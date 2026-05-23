"""Session + job runtime: agent_sessions, scheduled_jobs, triggers, run_checkpoints.

Phase 2.0 of the runtime layer. Adds four primitives that the existing
workflow runner does not have today:

- `agent_sessions` — long-lived agent processes (the "AI CMO" daemon)
  that wake on a heartbeat and react to events scoped to a workspace.
- `scheduled_jobs` — cron/interval triggers that enqueue workflow runs.
- `triggers` — declarative `event_kind → workflow` mapping fired by
  the event bus.
- `run_checkpoints` — per-step state snapshots so failed runs can resume
  from the last successful node instead of restarting.

All tables follow the patterns established by earlier migrations
(`uuid_type()` + `json_type()` helpers, SQLite-compatible defaults,
indexes on every FK).

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-24
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def get_is_sqlite() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "sqlite"


def uuid_type():
    return sa.String(36) if get_is_sqlite() else postgresql.UUID(as_uuid=True)


def json_type():
    return sa.JSON() if get_is_sqlite() else postgresql.JSONB()


def bool_default(value: bool) -> sa.text:
    if get_is_sqlite():
        return sa.text("1" if value else "0")
    return sa.text("true" if value else "false")


def upgrade() -> None:
    # ------------------------------------------------------------------
    # agent_sessions — long-running agent daemons scoped to a workspace.
    # ------------------------------------------------------------------
    op.create_table(
        "agent_sessions",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column(
            "workspace_id",
            uuid_type(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "brand_id",
            uuid_type(),
            sa.ForeignKey("brands.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            uuid_type(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("agent", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # lifecycle: idle | active | paused | stopped | errored
        sa.Column(
            "status", sa.String(32), nullable=False, server_default="idle"
        ),
        # autonomy: manual | assisted | semi | autonomous
        sa.Column(
            "mode", sa.String(32), nullable=False, server_default="assisted"
        ),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("config", json_type(), nullable=False, server_default="{}"),
        sa.Column("memory", json_type(), nullable=False, server_default="{}"),
        # Heartbeat — the sweeper marks sessions stale if last_heartbeat_at
        # is older than `heartbeat_interval_s * 3`.
        sa.Column("heartbeat_interval_s", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_agent_sessions_workspace_id", "agent_sessions", ["workspace_id"]
    )
    op.create_index(
        "ix_agent_sessions_brand_id", "agent_sessions", ["brand_id"]
    )
    op.create_index(
        "ix_agent_sessions_status", "agent_sessions", ["status"]
    )

    # ------------------------------------------------------------------
    # scheduled_jobs — cron / interval triggers that enqueue runs.
    # ------------------------------------------------------------------
    op.create_table(
        "scheduled_jobs",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column(
            "workspace_id",
            uuid_type(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "brand_id",
            uuid_type(),
            sa.ForeignKey("brands.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "session_id",
            uuid_type(),
            sa.ForeignKey("agent_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            uuid_type(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("workflow", sa.String(64), nullable=False),
        # schedule: either cron expression (5-field) or interval_s
        sa.Column("cron", sa.String(128), nullable=True),
        sa.Column("interval_s", sa.Integer(), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("inputs", json_type(), nullable=False, server_default="{}"),
        sa.Column("config", json_type(), nullable=False, server_default="{}"),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=bool_default(True),
        ),
        # Sweeper state.
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_id", uuid_type(), nullable=True),
        sa.Column("last_status", sa.String(32), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_scheduled_jobs_workspace_id", "scheduled_jobs", ["workspace_id"]
    )
    op.create_index(
        "ix_scheduled_jobs_next_run_at", "scheduled_jobs", ["next_run_at"]
    )
    op.create_index(
        "ix_scheduled_jobs_enabled", "scheduled_jobs", ["enabled"]
    )

    # ------------------------------------------------------------------
    # triggers — event_kind → workflow mapping. Fired by the event bus.
    # ------------------------------------------------------------------
    op.create_table(
        "triggers",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column(
            "workspace_id",
            uuid_type(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "brand_id",
            uuid_type(),
            sa.ForeignKey("brands.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "session_id",
            uuid_type(),
            sa.ForeignKey("agent_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            uuid_type(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        # source: event | webhook | manual | session_signal
        sa.Column("source", sa.String(32), nullable=False, server_default="event"),
        sa.Column("event_kind", sa.String(128), nullable=True),
        sa.Column("channel_pattern", sa.String(255), nullable=True),
        # JSONPath-ish payload filter (simple key=value AND match for now).
        sa.Column("filter", json_type(), nullable=False, server_default="{}"),
        sa.Column("workflow", sa.String(64), nullable=False),
        sa.Column("inputs_template", json_type(), nullable=False, server_default="{}"),
        sa.Column("config", json_type(), nullable=False, server_default="{}"),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=bool_default(True),
        ),
        # Anti-storm — minimum seconds between firings.
        sa.Column("debounce_s", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_fired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fire_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_triggers_workspace_id", "triggers", ["workspace_id"])
    op.create_index("ix_triggers_event_kind", "triggers", ["event_kind"])
    op.create_index("ix_triggers_enabled", "triggers", ["enabled"])

    # ------------------------------------------------------------------
    # run_checkpoints — per-node state snapshots for resumable execution.
    # ------------------------------------------------------------------
    op.create_table(
        "run_checkpoints",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column(
            "run_id",
            uuid_type(),
            sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("node", sa.String(128), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("state", json_type(), nullable=False, server_default="{}"),
        # status: snapshot | resumable | terminal
        sa.Column(
            "status", sa.String(32), nullable=False, server_default="snapshot"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_run_checkpoints_run_id", "run_checkpoints", ["run_id"]
    )
    op.create_index(
        "ix_run_checkpoints_run_seq", "run_checkpoints", ["run_id", "seq"]
    )


def downgrade() -> None:
    op.drop_index("ix_run_checkpoints_run_seq", table_name="run_checkpoints")
    op.drop_index("ix_run_checkpoints_run_id", table_name="run_checkpoints")
    op.drop_table("run_checkpoints")

    op.drop_index("ix_triggers_enabled", table_name="triggers")
    op.drop_index("ix_triggers_event_kind", table_name="triggers")
    op.drop_index("ix_triggers_workspace_id", table_name="triggers")
    op.drop_table("triggers")

    op.drop_index("ix_scheduled_jobs_enabled", table_name="scheduled_jobs")
    op.drop_index("ix_scheduled_jobs_next_run_at", table_name="scheduled_jobs")
    op.drop_index("ix_scheduled_jobs_workspace_id", table_name="scheduled_jobs")
    op.drop_table("scheduled_jobs")

    op.drop_index("ix_agent_sessions_status", table_name="agent_sessions")
    op.drop_index("ix_agent_sessions_brand_id", table_name="agent_sessions")
    op.drop_index("ix_agent_sessions_workspace_id", table_name="agent_sessions")
    op.drop_table("agent_sessions")
