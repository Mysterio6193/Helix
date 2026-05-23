"""Brand memory entries with embeddings + FTS."""
from __future__ import annotations

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from helix.models.base import Base, created_at_col, uuid_pk


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id: Mapped[uuid_pk]
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE")
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE")
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    tsv: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', coalesce(content,'') || ' ' || coalesce(summary,''))", persisted=True),
    )
    created_at: Mapped[created_at_col]

    __table_args__ = (
        Index(
            "ix_memory_entries_embedding_cosine",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index(
            "ix_memory_entries_tsv",
            "tsv",
            postgresql_using="gin",
        ),
        Index("ix_memory_entries_brand_id", "brand_id"),
    )
