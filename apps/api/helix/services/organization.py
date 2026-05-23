"""Organization and Workspace services."""
from __future__ import annotations

import re
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.models.organization import Organization, Workspace, User
from helix.schemas.organization import WorkspaceCreate, WorkspaceUpdate


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:128] or "slug"


async def _unique_workspace_slug(db: AsyncSession, organization_id: uuid.UUID, base: str) -> str:
    slug = base
    suffix = 1
    while True:
        result = await db.execute(
            select(Workspace.id).where(Workspace.organization_id == organization_id, Workspace.slug == slug)
        )
        if result.scalar_one_or_none() is None:
            return slug
        suffix += 1
        slug = f"{base}-{suffix}"

async def _unique_org_slug(db: AsyncSession, base: str) -> str:
    slug = base
    suffix = 1
    while True:
        result = await db.execute(
            select(Organization.id).where(Organization.slug == slug)
        )
        if result.scalar_one_or_none() is None:
            return slug
        suffix += 1
        slug = f"{base}-{suffix}"

async def create_organization(
    db: AsyncSession, name: str, slug: str | None = None, metadata_: dict | None = None
) -> Organization:
    """Create a new organization."""
    if not slug:
        slug = slugify(name)
    slug = await _unique_org_slug(db, slug)

    org = Organization(
        name=name,
        slug=slug,
        metadata_=metadata_ or {}
    )
    db.add(org)
    await db.flush()
    await db.refresh(org)
    return org

async def get_organization(db: AsyncSession, org_id: uuid.UUID) -> Organization | None:
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    return result.scalar_one_or_none()

async def list_organizations(
    db: AsyncSession, limit: int = 50, offset: int = 0
) -> tuple[list[Organization], int]:
    base = select(Organization)
    count_q = select(func.count()).select_from(Organization)

    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(
        base.order_by(Organization.created_at.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all()), total

async def update_organization(
    db: AsyncSession, org: Organization, name: str | None = None, metadata_: dict | None = None
) -> Organization:
    if name is not None:
        org.name = name
    if metadata_ is not None:
        org.metadata_ = metadata_
    await db.flush()
    await db.refresh(org)
    return org

async def create_workspace(
    db: AsyncSession, organization_id: uuid.UUID, payload: WorkspaceCreate
) -> Workspace:
    slug = payload.slug or slugify(payload.name)
    slug = await _unique_workspace_slug(db, organization_id, slug)

    workspace = Workspace(
        organization_id=organization_id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        settings=payload.settings,
    )
    db.add(workspace)
    await db.flush()
    await db.refresh(workspace)
    return workspace

async def get_workspace(db: AsyncSession, workspace_id: uuid.UUID) -> Workspace | None:
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    return result.scalar_one_or_none()

async def get_workspace_by_slug(db: AsyncSession, organization_id: uuid.UUID, slug: str) -> Workspace | None:
    result = await db.execute(
        select(Workspace).where(Workspace.organization_id == organization_id, Workspace.slug == slug)
    )
    return result.scalar_one_or_none()

async def list_workspaces(
    db: AsyncSession, organization_id: uuid.UUID, limit: int = 50, offset: int = 0
) -> tuple[list[Workspace], int]:
    base = select(Workspace).where(Workspace.organization_id == organization_id)
    count_q = select(func.count()).select_from(Workspace).where(Workspace.organization_id == organization_id)

    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(
        base.order_by(Workspace.created_at.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all()), total

async def list_workspaces_for_user(
    db: AsyncSession, user: User, limit: int = 50, offset: int = 0
) -> tuple[list[Workspace], int]:
    # Users only have access to workspaces in their own organization.
    return await list_workspaces(db, user.organization_id, limit, offset)

async def update_workspace(
    db: AsyncSession, workspace: Workspace, payload: WorkspaceUpdate
) -> Workspace:
    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        if hasattr(workspace, key):
            setattr(workspace, key, value)
    await db.flush()
    await db.refresh(workspace)
    return workspace

async def delete_workspace(db: AsyncSession, workspace: Workspace) -> None:
    await db.delete(workspace)
    await db.flush()
