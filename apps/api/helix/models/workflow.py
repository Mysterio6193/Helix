"""Workflow registry, runs, tasks, and asset outputs."""
from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from helix.models.base import Base, created_at_col, updated_at_col, uuid_pk


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[uuid_pk]
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    graph_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    definition: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]

    runs: Mapped[list["WorkflowRun"]] = relationship(
        back_populates="workflow_def", cascade="all, delete-orphan"
    )


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[uuid_pk]
    # Nullable (see migration 0006) — slices register in-memory and nothing
    # populates the `workflows` table. The `workflow` slug column below is the
    # actual source of truth for which slice produced this run.
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="RESTRICT"), nullable=True
    )
    # Denormalized slug (e.g. "brand_identity_foundation") populated by run_queue
    # so callers don't always need to join `workflows`. Backed by migration 0004.
    workflow: Mapped[str | None] = mapped_column(String(64), nullable=True)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL")
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    current_node: Mapped[str | None] = mapped_column(String(128))
    # DB column is still "input" (migration 0001) but exposed as `inputs` in Python.
    inputs: Mapped[dict] = mapped_column("input", JSONB, nullable=False, default=dict)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    # Reliability + cost tracking added in migration 0002.
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[created_at_col]
    started_at: Mapped[created_at_col | None] = mapped_column(nullable=True)
    finished_at: Mapped[created_at_col | None] = mapped_column(nullable=True)

    # Backwards-compat Python aliases for code/schemas that say `ended_at` / `completed_at`.
    ended_at = synonym("finished_at")
    completed_at = synonym("finished_at")

    workflow_def: Mapped[Workflow] = relationship(back_populates="runs")
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid_pk]
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False
    )
    node_name: Mapped[str] = mapped_column(String(128), nullable=False)
    agent: Mapped[str | None] = mapped_column(String(64))
    skill: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    langfuse_trace_id: Mapped[str | None] = mapped_column(String(128))
    started_at: Mapped[created_at_col]
    finished_at: Mapped[created_at_col | None] = mapped_column(nullable=True)

    # Python aliases for consumers that use the longer/plural names.
    workflow_run_id = synonym("run_id")
    name = synonym("node_name")
    inputs = synonym("input")
    outputs = synonym("output")

    run: Mapped[WorkflowRun] = relationship(back_populates="tasks")


class Asset(Base):
    """Generated creative outputs (packaging, site, social_post, ad, video, print)."""

    __tablename__ = "assets"

    id: Mapped[uuid_pk]
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE")
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True
    )
    workflow_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="SET NULL")
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    s3_key: Mapped[str | None] = mapped_column(Text)
    storage_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[created_at_col]

    # Python alias used by skill handlers / helpers.
    storage_key = synonym("s3_key")
