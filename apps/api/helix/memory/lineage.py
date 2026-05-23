"""Creative lineage graph (open-design pattern)."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.models.lineage import CreativeLineage


async def add_lineage_edge(
    db: AsyncSession,
    *,
    child_asset_id: uuid.UUID,
    parent_asset_id: uuid.UUID | None,
    transform: str,
    workflow_run_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> CreativeLineage:
    edge = CreativeLineage(
        parent_asset_id=parent_asset_id,
        child_asset_id=child_asset_id,
        workflow_run_id=workflow_run_id,
        transform=transform,
        metadata_=metadata or {},
    )
    db.add(edge)
    await db.flush()
    await db.refresh(edge)
    return edge


async def lineage_for_asset(
    db: AsyncSession, asset_id: uuid.UUID
) -> list[CreativeLineage]:
    stmt = select(CreativeLineage).where(
        or_(
            CreativeLineage.child_asset_id == asset_id,
            CreativeLineage.parent_asset_id == asset_id,
        )
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
