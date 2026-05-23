"""Brand + brand asset models."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helix.models.base import Base, created_at_col, updated_at_col, uuid_pk

if TYPE_CHECKING:
    from helix.models.organization import Workspace


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[uuid_pk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str | None] = mapped_column(String(128))
    tagline: Mapped[str | None] = mapped_column(Text)
    mission: Mapped[str | None] = mapped_column(Text)
    story: Mapped[str | None] = mapped_column(Text)
    target_audience: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    voice_attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    positioning: Mapped[str | None] = mapped_column(Text)
    archetype: Mapped[str | None] = mapped_column(String(64))
    design_school: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]

    workspace: Mapped["Workspace"] = relationship(back_populates="brands")
    assets: Mapped[list["BrandAsset"]] = relationship(
        back_populates="brand", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_brand_workspace_slug"),
    )


class BrandAsset(Base):
    """Foundational brand assets: logo, palette, typography, pattern, mark."""

    __tablename__ = "brand_assets"

    id: Mapped[uuid_pk]
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    s3_key: Mapped[str | None] = mapped_column(Text)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]

    brand: Mapped[Brand] = relationship(back_populates="assets")
