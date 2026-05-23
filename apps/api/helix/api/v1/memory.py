"""Memory API: brand context view + cross-brand stats.

All routes require authentication and enforce brand-level ACL — a user
can only read memory for brands owned by their organization's workspaces.
Pagination limits and graph caps are config-driven.
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.acl import assert_brand_access
from helix.core.config import settings
from helix.core.db import get_db
from helix.core.sessions import require_user
from helix.memory.brand_memory import load_brand_context
from helix.models.brand import Brand, BrandAsset
from helix.models.organization import User
from helix.models.skill import SkillLearning
from helix.models.workflow import Asset, WorkflowRun

router = APIRouter(prefix="/memory", tags=["memory"])


def _page_limit_query() -> Query:
    return Query(
        default=settings.page_default_limit,
        ge=1,
        le=settings.page_max_limit,
    )


@router.get("/brands/{brand_id}")
async def get_brand_memory(
    brand_id: uuid.UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Foundation context as every skill sees it, plus surrounding stats."""
    await assert_brand_access(db, user, brand_id)

    ctx = await load_brand_context(db, brand_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="brand not found")

    run_count = (
        await db.execute(
            select(func.count(WorkflowRun.id)).where(WorkflowRun.brand_id == brand_id)
        )
    ).scalar_one()
    asset_count = (
        await db.execute(
            select(func.count(Asset.id)).where(Asset.brand_id == brand_id)
        )
    ).scalar_one()
    learning_count = (
        await db.execute(
            select(func.count(SkillLearning.id)).where(SkillLearning.brand_id == brand_id)
        )
    ).scalar_one()
    brand_asset_count = (
        await db.execute(
            select(func.count(BrandAsset.id)).where(BrandAsset.brand_id == brand_id)
        )
    ).scalar_one()

    kind_rows = (
        await db.execute(
            select(Asset.kind, func.count(Asset.id))
            .where(Asset.brand_id == brand_id)
            .group_by(Asset.kind)
            .order_by(desc(func.count(Asset.id)))
        )
    ).all()
    kind_histogram = [{"kind": k or "unknown", "count": int(c)} for k, c in kind_rows]

    return {
        "context": ctx,
        "counts": {
            "runs": int(run_count or 0),
            "assets": int(asset_count or 0),
            "brand_assets": int(brand_asset_count or 0),
            "learnings": int(learning_count or 0),
        },
        "asset_kinds": kind_histogram,
    }


@router.get("/brands/{brand_id}/timeline")
async def get_brand_timeline(
    brand_id: uuid.UUID,
    limit: int = Query(
        default=settings.page_default_limit,
        ge=1,
        le=settings.page_max_limit,
    ),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Unified event timeline (runs + assets + learnings) — newest first."""
    await assert_brand_access(db, user, brand_id)

    timeline: list[dict[str, Any]] = []

    run_rows = (
        await db.execute(
            select(WorkflowRun)
            .where(WorkflowRun.brand_id == brand_id)
            .order_by(desc(WorkflowRun.started_at))
            .limit(limit)
        )
    ).scalars().all()
    for r in run_rows:
        timeline.append(
            {
                "type": "run",
                "id": str(r.id),
                "status": r.status,
                "title": f"Workflow run · {r.status}",
                "at": r.started_at.isoformat() if r.started_at else None,
            }
        )

    asset_rows = (
        await db.execute(
            select(Asset)
            .where(Asset.brand_id == brand_id)
            .order_by(desc(Asset.created_at))
            .limit(limit)
        )
    ).scalars().all()
    for a in asset_rows:
        timeline.append(
            {
                "type": "asset",
                "id": str(a.id),
                "kind": a.kind,
                "title": f"Asset · {a.kind}",
                "at": a.created_at.isoformat() if a.created_at else None,
            }
        )

    learning_rows = (
        await db.execute(
            select(SkillLearning)
            .where(SkillLearning.brand_id == brand_id)
            .order_by(desc(SkillLearning.created_at))
            .limit(limit)
        )
    ).scalars().all()
    for l in learning_rows:
        timeline.append(
            {
                "type": "learning",
                "id": str(l.id),
                "title": f"Learning · {(l.prompt_delta or l.trigger_context or '')[:80]}",
                "at": l.created_at.isoformat() if l.created_at else None,
            }
        )

    timeline.sort(key=lambda e: e.get("at") or "", reverse=True)
    return timeline[:limit]


@router.get("/brands/{brand_id}/graph")
async def get_brand_graph(
    brand_id: uuid.UUID,
    depth: int = Query(default=2, ge=1, le=5),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    """Force-directed graph of the brand's creative memory.

    Per-kind row caps scale with `depth` and the configured page limit so
    callers can dial detail without code changes.
    """
    brand = await assert_brand_access(db, user, brand_id)

    base_cap = max(5, settings.page_default_limit // 2)
    per_kind_cap = base_cap * depth

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    nodes.append({
        "id": f"brand:{brand.id}",
        "type": "brand",
        "label": brand.name,
        "val": 40,
    })

    try:
        run_rows = (
            await db.execute(
                select(WorkflowRun)
                .where(WorkflowRun.brand_id == brand_id)
                .order_by(desc(WorkflowRun.started_at))
                .limit(per_kind_cap)
            )
        ).scalars().all()

        run_ids: set[uuid.UUID] = set()
        for run in run_rows:
            run_id_str = str(run.id)
            run_ids.add(run.id)
            nodes.append({
                "id": f"run:{run_id_str}",
                "type": "run",
                "label": f"{run.workflow.replace('_', ' ').title()} ({run.status})",
                "val": 25,
            })
            edges.append({
                "id": f"brand->run:{run_id_str}",
                "source": f"brand:{brand.id}",
                "target": f"run:{run_id_str}",
                "label": "executed",
            })

        asset_rows = (
            await db.execute(
                select(Asset)
                .where(Asset.brand_id == brand_id)
                .order_by(desc(Asset.created_at))
                .limit(per_kind_cap * 2)
            )
        ).scalars().all()

        for asset in asset_rows:
            asset_id_str = str(asset.id)
            nodes.append({
                "id": f"asset:{asset_id_str}",
                "type": "asset",
                "label": asset.kind.replace("_", " ").title(),
                "val": 20,
            })
            if asset.workflow_run_id and asset.workflow_run_id in run_ids:
                edges.append({
                    "id": f"run->asset:{asset_id_str}",
                    "source": f"run:{asset.workflow_run_id}",
                    "target": f"asset:{asset_id_str}",
                    "label": "produced",
                })
            else:
                edges.append({
                    "id": f"brand->asset:{asset_id_str}",
                    "source": f"brand:{brand.id}",
                    "target": f"asset:{asset_id_str}",
                    "label": "owned",
                })

        learning_rows = (
            await db.execute(
                select(SkillLearning)
                .where(SkillLearning.brand_id == brand_id)
                .order_by(desc(SkillLearning.created_at))
                .limit(per_kind_cap)
            )
        ).scalars().all()

        for learning in learning_rows:
            lrn_id_str = str(learning.id)
            label = (learning.prompt_delta or learning.trigger_context or "Skill optimization")
            if len(label) > 35:
                label = label[:32] + "..."
            nodes.append({
                "id": f"learning:{lrn_id_str}",
                "type": "learning",
                "label": label,
                "val": 15,
            })
            edges.append({
                "id": f"brand->learning:{lrn_id_str}",
                "source": f"brand:{brand.id}",
                "target": f"learning:{lrn_id_str}",
                "label": "distilled",
            })

    except Exception:
        # Graceful: tables may not exist on a fresh DB; return what we have.
        pass

    return {"nodes": nodes, "edges": edges}
