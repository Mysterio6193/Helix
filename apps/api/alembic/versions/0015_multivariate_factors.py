"""Add multivariate factors support to experiments.

Revision ID: 0015
Revises: 0014
Create Date: 2026-05-24 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    is_pg = dialect == "postgresql"

    json_type = postgresql.JSONB() if is_pg else sa.JSON()
    json_empty = "{}" if is_pg else "'{}'"

    if is_pg:
        op.add_column("experiments", sa.Column("factors", json_type, nullable=False, server_default=sa.text(json_empty)))
        op.create_index("ix_experiments_type", "experiments", ["experiment_type"])
    else:
        op.add_column("experiments", sa.Column("factors", json_type, nullable=False, server_default=sa.text(json_empty)))


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.drop_index("ix_experiments_type", table_name="experiments")
    op.drop_column("experiments", "factors")
