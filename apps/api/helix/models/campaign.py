"""Campaign aggregates multiple workflow outputs (launch campaign, seasonal, etc.)."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from helix.models.base import Base, created_at_col, updated_at_col, uuid_pk


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid_pk]
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned")
    schedule: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    asset_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    workflow_run_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]
