"""Curated design systems loaded from design-systems/library/*.yaml (open-design pattern)."""
from __future__ import annotations

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from helix.models.base import Base, created_at_col, updated_at_col, uuid_pk


class DesignSystem(Base):
    __tablename__ = "design_systems"

    id: Mapped[uuid_pk]
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    school: Mapped[str | None] = mapped_column(String(64))  # one of 5 visual schools
    description: Mapped[str | None] = mapped_column(Text)
    palette: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    typography: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    spacing: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    motion: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    components: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_school: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]
