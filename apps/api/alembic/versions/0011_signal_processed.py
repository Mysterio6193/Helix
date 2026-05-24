"""Add processed flag to intelligence signals.

Revision ID: 0011
Revises: 0010
Create Date: 2025-05-24 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    is_pg = dialect == "postgresql"
    
    op.add_column(
        "intelligence_signals",
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.text("false") if is_pg else sa.text("0")),
    )

    op.create_index("ix_signals_processed", "intelligence_signals", ["workspace_id", "processed", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_signals_processed", table_name="intelligence_signals")
    op.drop_column("intelligence_signals", "processed")
