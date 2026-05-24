"""Access control helpers — workspace/brand membership checks.

All v1 endpoints that accept a `workspace_id` or `brand_id` should run
through one of these to prevent horizontal privilege escalation (one user
reading another org's data by guessing UUIDs).
"""
from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.db import get_db
from helix.core.sessions import require_user
from helix.models.brand import Brand
from helix.models.organization import User, Workspace


async def assert_workspace_access(
    db: AsyncSession,
    user: User,
    workspace_id: UUID,
) -> Workspace:
    """Raise 403 if the user's organization doesn't own the workspace."""
    ws = await db.get(Workspace, workspace_id)
    if ws is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="workspace not found")
    if ws.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="workspace access denied")
    return ws


async def assert_brand_access(
    db: AsyncSession,
    user: User,
    brand_id: UUID,
) -> Brand:
    """Raise 403 if the user's organization doesn't own the brand's workspace."""
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="brand not found")
    ws = await db.get(Workspace, brand.workspace_id)
    if ws is None or ws.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="brand access denied")
    return brand


async def list_user_workspace_ids(db: AsyncSession, user: User) -> list[UUID]:
    """All workspace IDs the user's organization owns."""
    rows = await db.execute(
        select(Workspace.id).where(Workspace.organization_id == user.organization_id)
    )
    return [r for (r,) in rows.all()]


async def get_default_workspace_for_user(db: AsyncSession, user: User) -> Workspace:
    """Return the first workspace in the user's org, creating one if none exist.

    Used by endpoints that don't take an explicit workspace_id (single-tenant
    convenience). Always scoped to the calling user's organization — never
    falls back to a global default.
    """
    result = await db.execute(
        select(Workspace)
        .where(Workspace.organization_id == user.organization_id)
        .order_by(Workspace.created_at)
        .limit(1)
    )
    ws = result.scalar_one_or_none()
    if ws is not None:
        return ws
    ws = Workspace(
        organization_id=user.organization_id,
        name="Default Workspace",
        slug="default",
        description="Auto-created default workspace.",
        settings={},
    )
    db.add(ws)
    await db.flush()
    await db.refresh(ws)
    return ws


# ---------------------------------------------------------------------------
# FastAPI dependency shorthands
# ---------------------------------------------------------------------------
async def workspace_dep(
    workspace_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    return await assert_workspace_access(db, user, workspace_id)


async def brand_dep(
    brand_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> Brand:
    return await assert_brand_access(db, user, brand_id)
