"""Add enterprise tables: api_keys, audit_logs, organization_invitations.

Revision ID: 0014
Revises: 0013
Create Date: 2026-05-24 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
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
    sa.text("false") if is_pg else sa.text("0")

    # -- api_keys --
    op.create_table(
        "api_keys",
        sa.Column("id", uuid_type, server_default=uuid_default, nullable=False),
        sa.Column("organization_id", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(16), nullable=False),
        sa.Column("key_hash", sa.String(128), nullable=False),
        sa.Column("scopes", json_type, nullable=False, server_default=sa.text(json_empty)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true") if is_pg else sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
    )
    if is_pg:
        op.create_index("ix_api_keys_org", "api_keys", ["organization_id", "enabled"])
        op.create_index("ix_api_keys_user", "api_keys", ["user_id", "enabled"])

    # -- audit_logs --
    op.create_table(
        "audit_logs",
        sa.Column("id", uuid_type, server_default=uuid_default, nullable=False),
        sa.Column("organization_id", uuid_type, nullable=False),
        sa.Column("actor_id", uuid_type, nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(128), nullable=True),
        sa.Column("details", json_type, nullable=False, server_default=sa.text(json_empty)),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    if is_pg:
        op.create_index("ix_audit_logs_org_created", "audit_logs", ["organization_id", "created_at"])
        op.create_index("ix_audit_logs_action", "audit_logs", ["action", "created_at"])
        op.create_index("ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])

    # -- organization_invitations --
    op.create_table(
        "organization_invitations",
        sa.Column("id", uuid_type, server_default=uuid_default, nullable=False),
        sa.Column("organization_id", uuid_type, nullable=False),
        sa.Column("invited_by", uuid_type, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(64), nullable=False, server_default=sa.text("'member'")),
        sa.Column("token", sa.String(128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=now_default, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    if is_pg:
        op.create_index("ix_org_invitations_org", "organization_invitations", ["organization_id", "accepted_at"])
        op.create_index("ix_org_invitations_email", "organization_invitations", ["email"])


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.drop_index("ix_org_invitations_email", table_name="organization_invitations")
        op.drop_index("ix_org_invitations_org", table_name="organization_invitations")
        op.drop_index("ix_audit_logs_resource", table_name="audit_logs")
        op.drop_index("ix_audit_logs_action", table_name="audit_logs")
        op.drop_index("ix_audit_logs_org_created", table_name="audit_logs")
        op.drop_index("ix_api_keys_user", table_name="api_keys")
        op.drop_index("ix_api_keys_org", table_name="api_keys")
    op.drop_table("organization_invitations")
    op.drop_table("audit_logs")
    op.drop_table("api_keys")
