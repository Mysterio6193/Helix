"""Session + job runtime models — Phase 2.0.

Adds the four primitives that turn Helix from a request/response app into
an operating system:

- AgentSession  — long-running agent process scoped to a workspace
- ScheduledJob  — cron / interval triggers
- Trigger       — declarative event_kind → workflow mapping
- RunCheckpoint — per-node state snapshot for resumable execution

The data layer purposefully stays close to the existing patterns in
`helix.models.workflow`: UUID PKs, JSONB payloads, server-default
timestamps, FK indexes via the migration (not here).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helix.models.base import Base, created_at_col, updated_at_col, uuid_pk


class AgentSession(Base):
    """A long-running agent daemon scoped to a workspace.

    Unlike a `WorkflowRun` (which executes once and terminates), an
    `AgentSession` is a process the user creates that stays alive across
    many runs. The sweeper pings it on `heartbeat_interval_s` and the
    agent reacts to triggers/schedules within its scope.

    Status transitions:
        idle -> active -> (idle|paused|stopped|errored)
    """

    __tablename__ = "agent_sessions"

    id: Mapped[uuid_pk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    agent: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="idle")
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="assisted")

    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    memory: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    heartbeat_interval_s: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_active_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]

    schedules: Mapped[list["ScheduledJob"]] = relationship(
        back_populates="session", cascade="save-update, merge"
    )
    triggers: Mapped[list["Trigger"]] = relationship(
        back_populates="session", cascade="save-update, merge"
    )


class ScheduledJob(Base):
    """Cron or interval-based workflow trigger.

    Exactly one of `cron` or `interval_s` must be set. The scheduler
    sweeper reads `next_run_at` (recomputed after each fire) and enqueues
    a `WorkflowRun` via the existing run queue when it's due.
    """

    __tablename__ = "scheduled_jobs"

    id: Mapped[uuid_pk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="SET NULL"),
        nullable=True,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    workflow: Mapped[str] = mapped_column(String(64), nullable=False)

    cron: Mapped[str | None] = mapped_column(String(128), nullable=True)
    interval_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")

    inputs: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    next_run_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    last_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]

    session: Mapped[AgentSession | None] = relationship(back_populates="schedules")


class Trigger(Base):
    """Declarative event_kind → workflow mapping.

    When the event bus publishes an event whose `kind` matches `event_kind`
    (and whose channel matches `channel_pattern` if set, and whose payload
    satisfies the `filter` predicates), the dispatcher enqueues a run with
    `inputs_template` merged with the event payload.

    `debounce_s` is the minimum seconds between firings of the same
    trigger — a simple anti-storm guard. The dispatcher checks
    `last_fired_at` before enqueuing.
    """

    __tablename__ = "triggers"

    id: Mapped[uuid_pk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="SET NULL"),
        nullable=True,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="event")
    event_kind: Mapped[str | None] = mapped_column(String(128), nullable=True)
    channel_pattern: Mapped[str | None] = mapped_column(String(255), nullable=True)
    filter: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    workflow: Mapped[str] = mapped_column(String(64), nullable=False)
    inputs_template: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    debounce_s: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_fired_at: Mapped[datetime | None] = mapped_column(nullable=True)
    fire_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]

    session: Mapped[AgentSession | None] = relationship(back_populates="triggers")


class RunCheckpoint(Base):
    """Per-node state snapshot for resumable workflow execution.

    The runner writes a checkpoint after each successful node so a
    failed run can be resumed from the last `seq` instead of restarting
    from zero. `seq` is monotonic per run; the highest `seq` with
    `status='resumable'` is the resume point.
    """

    __tablename__ = "run_checkpoints"

    id: Mapped[uuid_pk]
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    node: Mapped[str] = mapped_column(String(128), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    state: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="snapshot")
    created_at: Mapped[created_at_col]
