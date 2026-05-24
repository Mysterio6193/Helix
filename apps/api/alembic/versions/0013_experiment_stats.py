"""Enhance experiments with statistical fields and add experiment events.

Revision ID: 0013
Revises: 0012
Create Date: 2025-05-24 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    is_pg = dialect == "postgresql"
    
    uuid_type = postgresql.UUID(as_uuid=True) if is_pg else sa.String(36)
    uuid_default = sa.text("gen_random_uuid()") if is_pg else None
    now_default = sa.text("now()") if is_pg else sa.text("CURRENT_TIMESTAMP")
    json_type = postgresql.JSONB() if is_pg else sa.JSON()
    json_empty = "{}" if is_pg else "'{}'"
    false_default = sa.text("false") if is_pg else sa.text("0")

    # Add new columns to experiments table
    op.add_column("experiments", sa.Column("experiment_type", sa.String(32), nullable=False, server_default=sa.text("'ab'") if is_pg else sa.text("'ab'")))
    op.add_column("experiments", sa.Column("primary_metric", sa.String(64), nullable=False, server_default=sa.text("'conversion_rate'") if is_pg else sa.text("'conversion_rate'")))
    op.add_column("experiments", sa.Column("traffic_allocation", sa.Integer(), nullable=False, server_default=sa.text("100")))
    op.add_column("experiments", sa.Column("control_variant_id", sa.String(64), nullable=True))
    op.add_column("experiments", sa.Column("min_confidence", sa.Float(), nullable=False, server_default=sa.text("0.95")))
    op.add_column("experiments", sa.Column("min_sample_size", sa.Integer(), nullable=False, server_default=sa.text("100")))
    op.add_column("experiments", sa.Column("auto_stop", sa.Boolean(), nullable=False, server_default=false_default))
    op.add_column("experiments", sa.Column("p_value", sa.Float(), nullable=True))
    op.add_column("experiments", sa.Column("uplift", sa.Float(), nullable=True))

    # Create experiment_events table
    op.create_table(
        "experiment_events",
        sa.Column("id", uuid_type, server_default=uuid_default, nullable=False),
        sa.Column("experiment_id", uuid_type, nullable=False),
        sa.Column("variant_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("session_id", sa.String(128), nullable=True),
        sa.Column("user_id", sa.String(128), nullable=True),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("metadata", json_type, nullable=False, server_default=sa.text(json_empty)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_exp_events_experiment", "experiment_events", ["experiment_id", "variant_id", "event_type", "created_at"])
    op.create_index("ix_experiments_workspace_status", "experiments", ["workspace_id", "status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_exp_events_experiment", table_name="experiment_events")
    op.drop_index("ix_experiments_workspace_status", table_name="experiments")
    op.drop_table("experiment_events")
    
    op.drop_column("experiments", "experiment_type")
    op.drop_column("experiments", "primary_metric")
    op.drop_column("experiments", "traffic_allocation")
    op.drop_column("experiments", "control_variant_id")
    op.drop_column("experiments", "min_confidence")
    op.drop_column("experiments", "min_sample_size")
    op.drop_column("experiments", "auto_stop")
    op.drop_column("experiments", "p_value")
    op.drop_column("experiments", "uplift")
