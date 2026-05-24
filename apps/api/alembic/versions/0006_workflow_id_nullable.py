"""Make workflow_runs.workflow_id nullable.

The `workflow` slug column (added in 0004) is now the source of truth for
identifying which slice produced a run. The historic `workflow_id` FK to the
`workflows` table is unused because slices register in-memory only; nothing
ever inserts rows into `workflows`. Dropping the NOT NULL constraint lets
run_queue.enqueue_run() succeed without needing a Workflow DB row to point at.

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-22
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def get_is_sqlite() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "sqlite"


def uuid_type():
    return sa.String(36) if get_is_sqlite() else postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    with op.batch_alter_table("workflow_runs") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            existing_type=uuid_type(),
            nullable=True,
        )


def downgrade() -> None:
    # Note: downgrade may fail if existing rows have NULL workflow_id.
    with op.batch_alter_table("workflow_runs") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            existing_type=uuid_type(),
            nullable=False,
        )
