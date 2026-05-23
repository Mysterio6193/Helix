"""Extend assets table with columns the rest of the codebase already references.

Adds:
  - workspace_id (FK -> workspaces)
  - purpose (String, e.g. "logo", "menu:mockup", "social_post")
  - storage_url (Text, optional public URL alongside s3_key)
  - text_content (Text, for copy/text assets)

Task table mismatches are handled by SQLAlchemy synonyms in the model
(workflow_run_id <-> run_id, name <-> node_name, inputs <-> input,
outputs <-> output) so no DB rename is required.

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-22
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def get_is_sqlite() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "sqlite"


def uuid_type():
    return sa.String(36) if get_is_sqlite() else postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.add_column(
        "assets",
        sa.Column("workspace_id", uuid_type(), nullable=True),
    )
    op.add_column(
        "assets",
        sa.Column("purpose", sa.String(128), nullable=True),
    )
    op.add_column(
        "assets",
        sa.Column("storage_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "assets",
        sa.Column("text_content", sa.Text(), nullable=True),
    )

    with op.batch_alter_table("assets") as batch_op:
        batch_op.create_foreign_key(
            "fk_assets_workspace_id",
            "workspaces",
            ["workspace_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_index("ix_assets_workspace_id", "assets", ["workspace_id"])
    op.create_index("ix_assets_purpose", "assets", ["purpose"])


def downgrade() -> None:
    op.drop_index("ix_assets_purpose", table_name="assets")
    op.drop_index("ix_assets_workspace_id", table_name="assets")
    with op.batch_alter_table("assets") as batch_op:
        batch_op.drop_constraint("fk_assets_workspace_id", type_="foreignkey")
    op.drop_column("assets", "text_content")
    op.drop_column("assets", "storage_url")
    op.drop_column("assets", "purpose")
    op.drop_column("assets", "workspace_id")
