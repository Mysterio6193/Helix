"""Intelligence layer tables.

Revision ID: 0009
Revises: 0008
Create Date: 2025-05-24 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    is_pg = dialect == "postgresql"
    
    # Use appropriate types
    uuid_type = postgresql.UUID(as_uuid=True) if is_pg else sa.String(36)
    json_type = postgresql.JSONB() if is_pg else sa.JSON()
    uuid_default = sa.text("gen_random_uuid()") if is_pg else None
    now_default = sa.text("now()") if is_pg else sa.text("CURRENT_TIMESTAMP")
    json_empty = "{}" if is_pg else "'{}'"
    json_list = "[]" if is_pg else "'[]'"

    op.create_table(
        "performance_snapshots",
        sa.Column("id", uuid_type, server_default=uuid_default, nullable=False),
        sa.Column("workspace_id", uuid_type, nullable=False),
        sa.Column("brand_id", uuid_type, nullable=True),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("metric_type", sa.String(64), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("metadata", json_type, nullable=False, server_default=sa.text(json_empty)),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_perf_workspace_captured", "performance_snapshots", ["workspace_id", "captured_at"])
    op.create_index("ix_perf_platform_metric", "performance_snapshots", ["platform", "metric_type"])
    op.create_index("ix_perf_brand_captured", "performance_snapshots", ["brand_id", "captured_at"])

    op.create_table(
        "customer_segments",
        sa.Column("id", uuid_type, server_default=uuid_default, nullable=False),
        sa.Column("workspace_id", uuid_type, nullable=False),
        sa.Column("brand_id", uuid_type, nullable=True),
        sa.Column("segment_key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("definition_rules", json_type, nullable=False, server_default=sa.text(json_empty)),
        sa.Column("member_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("avg_ltv", sa.Float(), nullable=True),
        sa.Column("avg_order_value", sa.Float(), nullable=True),
        sa.Column("churn_rate", sa.Float(), nullable=True),
        sa.Column("retention_curve", json_type, nullable=False, server_default=sa.text(json_list)),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "segment_key", name="ix_segments_workspace_key"),
    )

    op.create_table(
        "competitor_snapshots",
        sa.Column("id", uuid_type, server_default=uuid_default, nullable=False),
        sa.Column("workspace_id", uuid_type, nullable=False),
        sa.Column("competitor_domain", sa.String(255), nullable=False),
        sa.Column("competitor_name", sa.String(255), nullable=True),
        sa.Column("snapshot_type", sa.String(32), nullable=False),
        sa.Column("data", json_type, nullable=False, server_default=sa.text(json_empty)),
        sa.Column("health_score", sa.Integer(), nullable=True),
        sa.Column("change_detected", sa.Boolean(), nullable=False, server_default=sa.text("false") if is_pg else sa.text("0")),
        sa.Column("diff_from_previous", json_type, nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_competitor_domain_captured", "competitor_snapshots", ["competitor_domain", "captured_at"])
    op.create_index("ix_competitor_workspace", "competitor_snapshots", ["workspace_id", "captured_at"])

    op.create_table(
        "intelligence_signals",
        sa.Column("id", uuid_type, server_default=uuid_default, nullable=False),
        sa.Column("workspace_id", uuid_type, nullable=False),
        sa.Column("brand_id", uuid_type, nullable=True),
        sa.Column("layer", sa.String(32), nullable=False),
        sa.Column("signal_type", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default=sa.text("'info'")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_data", json_type, nullable=False, server_default=sa.text(json_empty)),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("auto_triggered", sa.Boolean(), nullable=False, server_default=sa.text("false") if is_pg else sa.text("0")),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_signals_workspace_layer", "intelligence_signals", ["workspace_id", "layer", "created_at"])
    op.create_index("ix_signals_severity", "intelligence_signals", ["severity", "created_at"])

    op.create_table(
        "experiments",
        sa.Column("id", uuid_type, server_default=uuid_default, nullable=False),
        sa.Column("workspace_id", uuid_type, nullable=False),
        sa.Column("brand_id", uuid_type, nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("variants", json_type, nullable=False, server_default=sa.text(json_list)),
        sa.Column("metrics", json_type, nullable=False, server_default=sa.text(json_empty)),
        sa.Column("winner", sa.String(64), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("experiments")
    op.drop_table("intelligence_signals")
    op.drop_table("competitor_snapshots")
    op.drop_table("customer_segments")
    op.drop_table("performance_snapshots")
