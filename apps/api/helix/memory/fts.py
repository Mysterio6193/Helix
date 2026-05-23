"""Postgres FTS over memory_entries (Hermes FTS5 analog)."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.models.memory import MemoryEntry


async def fts_search(
    db: AsyncSession,
    *,
    query: str,
    brand_id: uuid.UUID | None = None,
    limit: int = 20,
) -> list[MemoryEntry]:
    tsq = func.plainto_tsquery("english", query)
    stmt = (
        select(MemoryEntry)
        .where(MemoryEntry.tsv.op("@@")(tsq))
        .order_by(func.ts_rank(MemoryEntry.tsv, tsq).desc())
        .limit(limit)
    )
    if brand_id is not None:
        stmt = stmt.where(MemoryEntry.brand_id == brand_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
