"""Media generation jobs table.

Revision ID: 0012
Revises: 0011
Create Date: 2025-05-24 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012"
down_revision: str | None = "0011"
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
    json_array = "[]" if is_pg else "'[]'"
    sa.text("false") if is_pg else sa.text("0")

    op.create_table(
        "media_generation_jobs",
        sa.Column("id", uuid_type, server_default=uuid_default, nullable=False),
        sa.Column("workspace_id", uuid_type, nullable=False),
        sa.Column("brand_id", uuid_type, nullable=True),
        sa.Column("created_by", uuid_type, nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("job_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("prompts", json_type, nullable=False, server_default=sa.text(json_array)),
        sa.Column("config", json_type, nullable=False, server_default=sa.text(json_empty)),
        sa.Column("results", json_type, nullable=False, server_default=sa.text(json_array)),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("completed_items", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("failed_items", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_cost_usd", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("metadata", json_type, nullable=False, server_default=sa.text(json_empty)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_media_jobs_workspace", "media_generation_jobs", ["workspace_id", "status", "created_at"])
    op.create_index("ix_media_jobs_status", "media_generation_jobs", ["status", "updated_at"])


def downgrade() -> None:
    op.drop_index("ix_media_jobs_status", table_name="media_generation_jobs")
    op.drop_index("ix_media_jobs_workspace", table_name="media_generation_jobs")
    op.drop_table("media_generation_jobs")
