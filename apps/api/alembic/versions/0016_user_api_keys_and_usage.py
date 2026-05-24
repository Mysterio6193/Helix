"""Add user_api_keys and usage_records tables.

Revision ID: 0016
Revises: 0015
Create Date: 2026-05-24 01:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    is_pg = dialect == "postgresql"

    uuid_type = postgresql.UUID(as_uuid=True) if is_pg else sa.String(36)

    # user_api_keys
    op.create_table(
        "user_api_keys",
        sa.Column("id", uuid_type, primary_key=True, default=None),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("key_prefix", sa.String(32), nullable=False),
        sa.Column("key_ciphertext", sa.String(512), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )

    # usage_records
    op.create_table(
        "usage_records",
        sa.Column("id", uuid_type, primary_key=True, default=None),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("model_id", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, default=0),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, default=0),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    if is_pg:
        op.create_index("ix_usage_org_created", "usage_records", ["organization_id", "created_at"])
        op.create_index("ix_usage_user_created", "usage_records", ["user_id", "created_at"])


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.drop_index("ix_usage_org_created", table_name="usage_records")
        op.drop_index("ix_usage_user_created", table_name="usage_records")
    op.drop_table("usage_records")
    op.drop_table("user_api_keys")
