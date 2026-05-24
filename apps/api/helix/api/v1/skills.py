"""Skills + learnings API: registry list, detail, learning rollups, toggles.

The skill registry is a shared catalog (visible to any authenticated user
in the organization), but brand-specific learnings and specializations are
filtered to the caller's organization via brand ACL. Mutating endpoints
require auth; brand-scoped learnings additionally enforce brand access.
Pagination is config-driven.
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.acl import assert_brand_access, list_user_workspace_ids
from helix.core.config import settings
from helix.core.db import get_db
from helix.core.sessions import require_user
from helix.models.brand import Brand
from helix.models.organization import User
from helix.models.skill import SkillLearning, SkillRegistry

router = APIRouter(prefix="/skills", tags=["skills"])


def _skill_to_public(row: SkillRegistry, specialization_count: int = 0) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "name": row.name,
        "version": row.version,
        "description": row.description,
        "tags": list(row.tags or []),
        "trigger_phrases": list(row.trigger_phrases or []),
        "required_tools": list(row.required_tools or []),
        "dependencies": list(row.dependencies or []),
        "enabled": row.enabled,
        "is_stub": row.is_stub,
        "usage_count": row.usage_count,
        "success_count": row.success_count,
        "success_rate": row.success_rate,
        "is_specialization": row.is_specialization,
        "parent_skill": row.parent_skill,
        "brand_id": str(row.brand_id) if row.brand_id else None,
        "specialization_count": specialization_count,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _learning_to_public(row: SkillLearning) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "skill_id": str(row.skill_id),
        "workflow_run_id": str(row.workflow_run_id) if row.workflow_run_id else None,
        "brand_id": str(row.brand_id) if row.brand_id else None,
        "trigger_context": row.trigger_context,
        "prompt_delta": row.prompt_delta,
        "success_markers": row.success_markers or {},
        "score": row.score,
        "applied_count": row.applied_count,
        "enabled": row.enabled,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


async def _user_brand_ids(db: AsyncSession, user: User) -> set[uuid.UUID]:
    """All brand IDs in the user's organization."""
    workspace_ids = await list_user_workspace_ids(db, user)
    if not workspace_ids:
        return set()
    rows = await db.execute(
        select(Brand.id).where(Brand.workspace_id.in_(workspace_ids))
    )
    return {b for (b,) in rows.all()}


async def _assert_learning_access(
    db: AsyncSession, user: User, learning: SkillLearning
) -> None:
    """Brand-scoped learnings must belong to the caller's org. Global
    learnings (brand_id is None) are visible to any authenticated user."""
    if learning.brand_id is None:
        return
    await assert_brand_access(db, user, learning.brand_id)


@router.get("")
async def list_skills(
    include_stubs: bool = Query(default=True),
    tag: str | None = Query(default=None),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    stmt = select(SkillRegistry).order_by(
        SkillRegistry.is_stub.asc(), SkillRegistry.name.asc()
    )
    if not include_stubs:
        stmt = stmt.where(SkillRegistry.is_stub.is_(False))
    rows = list((await db.execute(stmt)).scalars().all())

    if tag:
        rows = [r for r in rows if tag in (r.tags or [])]

    # Hide brand-scoped specializations that belong to other orgs.
    org_brand_ids = await _user_brand_ids(db, user)
    rows = [r for r in rows if r.brand_id is None or r.brand_id in org_brand_ids]

    counts_stmt = (
        select(SkillRegistry.parent_skill, func.count(SkillRegistry.id))
        .where(SkillRegistry.parent_skill.is_not(None))
        .group_by(SkillRegistry.parent_skill)
    )
    counts_res = await db.execute(counts_stmt)
    specialization_counts = dict(counts_res.all())

    total = len(rows)
    active = sum(1 for r in rows if not r.is_stub)
    stubs = sum(1 for r in rows if r.is_stub)

    items = [_skill_to_public(r, specialization_counts.get(r.name, 0)) for r in rows]

    return {
        "summary": {"total": total, "active": active, "stubs": stubs},
        "items": items,
    }


@router.get("/learnings/recent")
async def recent_learnings(
    limit: int = Query(
        default=settings.page_default_limit,
        ge=1,
        le=settings.page_max_limit,
    ),
    brand_id: uuid.UUID | None = Query(default=None),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Recent learnings. When no brand_id is given, scoped to the caller's
    organization's brands (plus global / non-brand learnings)."""
    stmt = (
        select(SkillLearning, SkillRegistry.name)
        .join(SkillRegistry, SkillRegistry.id == SkillLearning.skill_id)
        .order_by(desc(SkillLearning.created_at))
        .limit(limit)
    )
    if brand_id is not None:
        await assert_brand_access(db, user, brand_id)
        stmt = stmt.where(SkillLearning.brand_id == brand_id)
    else:
        org_brand_ids = await _user_brand_ids(db, user)
        if org_brand_ids:
            stmt = stmt.where(
                (SkillLearning.brand_id.is_(None))
                | (SkillLearning.brand_id.in_(org_brand_ids))
            )
        else:
            stmt = stmt.where(SkillLearning.brand_id.is_(None))

    rows = (await db.execute(stmt)).all()
    out: list[dict[str, Any]] = []
    for lrn, skill_name in rows:
        item = _learning_to_public(lrn)
        item["skill_name"] = skill_name
        out.append(item)
    return out


@router.get("/{name}")
async def get_skill(
    name: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    stmt = select(SkillRegistry).where(SkillRegistry.name == name)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=f"skill not found: {name}")

    # If the skill is a brand specialization, enforce ACL.
    if row.brand_id is not None:
        await assert_brand_access(db, user, row.brand_id)

    cnt_stmt = select(func.count(SkillRegistry.id)).where(SkillRegistry.parent_skill == row.name)
    sc = (await db.execute(cnt_stmt)).scalar() or 0

    org_brand_ids = await _user_brand_ids(db, user)
    lrn_stmt = (
        select(SkillLearning)
        .where(SkillLearning.skill_id == row.id)
        .order_by(desc(SkillLearning.created_at))
        .limit(settings.page_default_limit)
    )
    if org_brand_ids:
        lrn_stmt = lrn_stmt.where(
            (SkillLearning.brand_id.is_(None))
            | (SkillLearning.brand_id.in_(org_brand_ids))
        )
    else:
        lrn_stmt = lrn_stmt.where(SkillLearning.brand_id.is_(None))

    learnings = list((await db.execute(lrn_stmt)).scalars().all())
    return {
        "skill": _skill_to_public(row, sc),
        "learnings": [_learning_to_public(item) for item in learnings],
    }


@router.patch("/{name}")
async def toggle_skill(
    name: str,
    enabled: bool,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    stmt = select(SkillRegistry).where(SkillRegistry.name == name)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=f"skill not found: {name}")
    if row.brand_id is not None:
        await assert_brand_access(db, user, row.brand_id)
    row.enabled = enabled
    await db.commit()

    cnt_stmt = select(func.count(SkillRegistry.id)).where(SkillRegistry.parent_skill == row.name)
    sc = (await db.execute(cnt_stmt)).scalar() or 0
    return _skill_to_public(row, sc)


@router.patch("/learnings/{learning_id}")
async def toggle_learning(
    learning_id: uuid.UUID,
    enabled: bool,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    stmt = select(SkillLearning).where(SkillLearning.id == learning_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="learning not found")
    await _assert_learning_access(db, user, row)
    row.enabled = enabled
    await db.commit()
    return _learning_to_public(row)


@router.delete(
    "/learnings/{learning_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
async def delete_learning(
    learning_id: uuid.UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    stmt = select(SkillLearning).where(SkillLearning.id == learning_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="learning not found")
    await _assert_learning_access(db, user, row)
    await db.delete(row)
    await db.commit()
