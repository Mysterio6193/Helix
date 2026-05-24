"""Skill registry + closed-loop learning (Hermes pattern)."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helix.models.base import Base, created_at_col, updated_at_col, uuid_pk


class SkillRegistry(Base):
    __tablename__ = "skills_registry"

    id: Mapped[uuid_pk]
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    description: Mapped[str | None] = mapped_column(Text)
    manifest_path: Mapped[str] = mapped_column(Text, nullable=False)
    handler_path: Mapped[str | None] = mapped_column(Text)
    inputs: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    outputs: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    required_tools: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    dependencies: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    trigger_phrases: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_stub: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_rate: Mapped[float | None] = mapped_column(Float)
    
    # Pillar 3 Specialization columns
    is_specialization: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    parent_skill: Mapped[str | None] = mapped_column(
        String(128), ForeignKey("skills_registry.name", ondelete="SET NULL"), nullable=True
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]

    learnings: Mapped[list[SkillLearning]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )


class SkillLearning(Base):
    """Extracted lesson from a successful run; prepended to handler prompt on load."""

    __tablename__ = "skill_learnings"

    id: Mapped[uuid_pk]
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills_registry.id", ondelete="CASCADE"), nullable=False
    )
    workflow_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="SET NULL")
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL")
    )
    trigger_context: Mapped[str | None] = mapped_column(Text)
    prompt_delta: Mapped[str | None] = mapped_column(Text)
    success_markers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    score: Mapped[float | None] = mapped_column(Float)
    applied_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # pgvector embedding for semantic retrieval
    from pgvector.sqlalchemy import Vector
    context_embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))

    created_at: Mapped[created_at_col]

    skill: Mapped[SkillRegistry] = relationship(back_populates="learnings")
