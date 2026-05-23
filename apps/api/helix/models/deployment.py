"""Tracks website / asset deployments to Vercel, GitHub Pages, etc."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from helix.models.base import Base, created_at_col, updated_at_col, uuid_pk


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[uuid_pk]
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    workflow_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="SET NULL")
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="vercel")
    repo_url: Mapped[str | None] = mapped_column(Text)
    deployment_url: Mapped[str | None] = mapped_column(Text)
    preview_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    commit_sha: Mapped[str | None] = mapped_column(String(64))
    error: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]
