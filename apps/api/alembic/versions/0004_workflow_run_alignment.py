"""Align workflow_runs schema with consumers (schemas, runner, run_queue).

Adds the columns the rest of the codebase already references:
  - workspace_id (FK -> workspaces)
  - workflow (string slug, mirrors workflow_id row.slug for fast access)
  - config (JSON)
  - created_at (DateTime, server-default now())
  - created_by (FK -> users)

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-22
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def get_is_sqlite() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "sqlite"


def uuid_type():
    return sa.String(36) if get_is_sqlite() else postgresql.UUID(as_uuid=True)


def json_type():
    return sa.JSON() if get_is_sqlite() else postgresql.JSONB()


def upgrade() -> None:
    op.add_column(
        "workflow_runs",
        sa.Column("workspace_id", uuid_type(), nullable=True),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("workflow", sa.String(64), nullable=True),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("config", json_type(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "workflow_runs",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("created_by", uuid_type(), nullable=True),
    )

    # Foreign keys are added in batch mode to support SQLite.
    with op.batch_alter_table("workflow_runs") as batch_op:
        batch_op.create_foreign_key(
            "fk_workflow_runs_workspace_id",
            "workspaces",
            ["workspace_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_workflow_runs_created_by",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_index(
        "ix_workflow_runs_created_at", "workflow_runs", ["created_at"]
    )
    op.create_index(
        "ix_workflow_runs_workflow", "workflow_runs", ["workflow"]
    )


def downgrade() -> None:
    op.drop_index("ix_workflow_runs_workflow", table_name="workflow_runs")
    op.drop_index("ix_workflow_runs_created_at", table_name="workflow_runs")
    with op.batch_alter_table("workflow_runs") as batch_op:
        batch_op.drop_constraint("fk_workflow_runs_created_by", type_="foreignkey")
        batch_op.drop_constraint("fk_workflow_runs_workspace_id", type_="foreignkey")
    op.drop_column("workflow_runs", "created_by")
    op.drop_column("workflow_runs", "created_at")
    op.drop_column("workflow_runs", "config")
    op.drop_column("workflow_runs", "workflow")
    op.drop_column("workflow_runs", "workspace_id")
