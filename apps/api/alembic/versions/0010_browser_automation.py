"""Browser automation tables.

Revision ID: 0010
Revises: 0009
Create Date: 2025-05-24 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: str | None = "0009"
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

    op.create_table(
        "browser_sessions",
        sa.Column("id", uuid_type, server_default=uuid_default, nullable=False),
        sa.Column("workspace_id", uuid_type, nullable=False),
        sa.Column("brand_id", uuid_type, nullable=True),
        sa.Column("created_by", uuid_type, nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False, server_default=sa.text("'local'")),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'idle'")),
        sa.Column("target_url", sa.Text(), nullable=True),
        sa.Column("current_url", sa.Text(), nullable=True),
        sa.Column("page_title", sa.String(255), nullable=True),
        sa.Column("config", json_type, nullable=False, server_default=sa.text(json_empty)),
        sa.Column("metadata", json_type, nullable=False, server_default=sa.text(json_empty)),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_browser_sessions_workspace", "browser_sessions", ["workspace_id", "status"])
    op.create_index("ix_browser_sessions_status", "browser_sessions", ["status", "updated_at"])

    op.create_table(
        "browser_actions",
        sa.Column("id", uuid_type, server_default=uuid_default, nullable=False),
        sa.Column("session_id", uuid_type, nullable=False),
        sa.Column("action_type", sa.String(32), nullable=False),
        sa.Column("selector", sa.String(255), nullable=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("result", json_type, nullable=False, server_default=sa.text(json_empty)),
        sa.Column("screenshot_url", sa.Text(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_browser_actions_session", "browser_actions", ["session_id", "created_at"])

    op.create_table(
        "browser_automations",
        sa.Column("id", uuid_type, server_default=uuid_default, nullable=False),
        sa.Column("workspace_id", uuid_type, nullable=False),
        sa.Column("brand_id", uuid_type, nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_site", sa.String(32), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("config", json_type, nullable=False, server_default=sa.text(json_empty)),
        sa.Column("schedule", json_type, nullable=False, server_default=sa.text(json_empty)),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true") if is_pg else sa.text("1")),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_id", uuid_type, nullable=True),
        sa.Column("run_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_browser_automations_workspace", "browser_automations", ["workspace_id", "enabled"])


def downgrade() -> None:
    op.drop_table("browser_automations")
    op.drop_table("browser_actions")
    op.drop_table("browser_sessions")
