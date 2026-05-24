"""Performance indexes + reliability columns.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-22
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Performance indexes for hot query paths --

    # tasks: frequently queried by run_id (join from workflow_runs) and filtered by status
    op.create_index("ix_tasks_run_id", "tasks", ["run_id"])
    op.create_index("ix_tasks_status", "tasks", ["status"])

    # assets: queried by brand, by workflow_run, and by brand+kind (existing ix_assets_brand_kind covers latter)
    op.create_index("ix_assets_brand_id", "assets", ["brand_id"])
    op.create_index("ix_assets_workflow_run_id", "assets", ["workflow_run_id"])

    # skill_learnings: load_learnings queries by skill_id ordered by score; also filter by brand
    op.create_index("ix_skill_learnings_skill_id_score", "skill_learnings", ["skill_id", "score"])
    op.create_index("ix_skill_learnings_brand_id", "skill_learnings", ["brand_id"])

    # workflow_runs: dashboard queries filter by brand + status
    op.create_index("ix_workflow_runs_brand_id_status", "workflow_runs", ["brand_id", "status"])

    # -- Reliability columns --

    # Idempotency key for run_queue duplicate prevention
    op.add_column(
        "workflow_runs",
        sa.Column("idempotency_key", sa.String(255), nullable=True),
    )
    # Partial unique index: only enforce uniqueness on non-null values
    is_sqlite = op.get_bind().dialect.name == "sqlite"
    if is_sqlite:
        op.create_index(
            "ix_workflow_runs_idempotency_key",
            "workflow_runs",
            ["idempotency_key"],
            unique=True,
            sqlite_where=sa.text("idempotency_key IS NOT NULL"),
        )
    else:
        op.create_index(
            "ix_workflow_runs_idempotency_key",
            "workflow_runs",
            ["idempotency_key"],
            unique=True,
            postgresql_where=sa.text("idempotency_key IS NOT NULL"),
        )

    # Total cost tracking on the run itself
    op.add_column(
        "workflow_runs",
        sa.Column("total_cost_usd", sa.Float(), nullable=True),
    )

    # Duration in milliseconds
    op.add_column(
        "workflow_runs",
        sa.Column("duration_ms", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workflow_runs", "duration_ms")
    op.drop_column("workflow_runs", "total_cost_usd")
    op.drop_index("ix_workflow_runs_idempotency_key", table_name="workflow_runs")
    op.drop_column("workflow_runs", "idempotency_key")
    op.drop_index("ix_workflow_runs_brand_id_status", table_name="workflow_runs")
    op.drop_index("ix_skill_learnings_brand_id", table_name="skill_learnings")
    op.drop_index("ix_skill_learnings_skill_id_score", table_name="skill_learnings")
    op.drop_index("ix_assets_workflow_run_id", table_name="assets")
    op.drop_index("ix_assets_brand_id", table_name="assets")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_run_id", table_name="tasks")
