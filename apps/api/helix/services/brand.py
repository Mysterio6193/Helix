"""Brand service: create/read/update/list with auto-slug + workspace scoping.

The previous `get_or_create_default_workspace(db)` helper was removed —
it bypassed organization scoping and would silently return another org's
workspace in a multi-tenant deployment. All callers now resolve the
workspace through `helix.core.acl.get_default_workspace_for_user`, which
is always scoped to the caller's organization.
"""
from __future__ import annotations

import re
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.models.brand import Brand
from helix.schemas.brand import BrandCreate, BrandUpdate


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:128] or "brand"


async def _unique_slug(db: AsyncSession, workspace_id: uuid.UUID, base: str) -> str:
    slug = base
    suffix = 1
    while True:
        result = await db.execute(
            select(Brand.id).where(Brand.workspace_id == workspace_id, Brand.slug == slug)
        )
        if result.scalar_one_or_none() is None:
            return slug
        suffix += 1
        slug = f"{base}-{suffix}"


async def create_brand(
    db: AsyncSession,
    payload: BrandCreate,
    *,
    workspace_id: uuid.UUID | None = None,
) -> Brand:
    """Create a brand under the given workspace.

    `workspace_id` is required (either via the payload or the explicit
    argument). Callers are responsible for resolving the workspace through
    the org-scoped ACL helpers before invoking this function — the service
    layer no longer falls back to a global default workspace.
    """
    resolved = workspace_id or payload.workspace_id
    if resolved is None:
        raise ValueError("workspace_id is required to create a brand")

    slug = payload.slug or slugify(payload.name)
    slug = await _unique_slug(db, resolved, slug)

    brand = Brand(
        workspace_id=resolved,
        name=payload.name,
        slug=slug,
        category=payload.category,
        tagline=payload.tagline,
        mission=payload.mission,
        story=payload.story,
        target_audience=payload.target_audience,
        voice_attributes=payload.voice_attributes,
        positioning=payload.positioning,
        archetype=payload.archetype,
        design_school=payload.design_school,
        metadata_=payload.metadata_,
    )
    db.add(brand)
    await db.flush()
    await db.refresh(brand)
    return brand


async def get_brand(db: AsyncSession, brand_id: uuid.UUID) -> Brand | None:
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    return result.scalar_one_or_none()


async def list_brands(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Brand], int]:
    base = select(Brand)
    count_q = select(func.count()).select_from(Brand)
    if workspace_id is not None:
        base = base.where(Brand.workspace_id == workspace_id)
        count_q = count_q.where(Brand.workspace_id == workspace_id)

    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(
        base.order_by(Brand.created_at.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all()), total


async def list_brands_in_workspaces(
    db: AsyncSession,
    *,
    workspace_ids: list[uuid.UUID],
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Brand], int]:
    """List brands across multiple workspaces (e.g. all workspaces in caller's org)."""
    if not workspace_ids:
        return [], 0
    base = select(Brand).where(Brand.workspace_id.in_(workspace_ids))
    count_q = (
        select(func.count()).select_from(Brand).where(Brand.workspace_id.in_(workspace_ids))
    )
    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(
        base.order_by(Brand.created_at.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all()), total


async def update_brand(
    db: AsyncSession, brand: Brand, payload: BrandUpdate
) -> Brand:
    data = payload.model_dump(exclude_none=True, by_alias=False)
    # Pydantic with alias="metadata" -> field name remains metadata_; rename for ORM.
    for key, value in data.items():
        if hasattr(brand, key):
            setattr(brand, key, value)
    await db.flush()
    await db.refresh(brand)
    return brand


async def delete_brand(db: AsyncSession, brand: Brand) -> None:
    await db.delete(brand)
    await db.flush()
