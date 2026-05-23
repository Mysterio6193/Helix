"""Vector retrieval over memory_entries via pgvector cosine."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.memory.embeddings import embed
from helix.models.memory import MemoryEntry


async def write_memory(
    db: AsyncSession,
    *,
    brand_id: uuid.UUID | None,
    workspace_id: uuid.UUID | None,
    kind: str,
    content: str,
    summary: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> MemoryEntry:
    vec = await embed(f"{summary or ''}\n{content}")
    entry = MemoryEntry(
        brand_id=brand_id,
        workspace_id=workspace_id,
        kind=kind,
        content=content,
        summary=summary,
        metadata_=metadata or {},
        embedding=vec,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def topk(
    db: AsyncSession,
    *,
    query: str,
    brand_id: uuid.UUID | None = None,
    k: int = 8,
) -> list[MemoryEntry]:
    vec = await embed(query)
    stmt = select(MemoryEntry).order_by(MemoryEntry.embedding.cosine_distance(vec))
    if brand_id is not None:
        stmt = stmt.where(MemoryEntry.brand_id == brand_id)
    stmt = stmt.limit(k)
    result = await db.execute(stmt)
    return list(result.scalars().all())
