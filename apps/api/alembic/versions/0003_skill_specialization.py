"""Skill specialization + context embeddings.

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-22
"""
from __future__ import annotations

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None



def get_is_sqlite() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "sqlite"


def uuid_type():
    return sa.String(36) if get_is_sqlite() else postgresql.UUID(as_uuid=True)


def vector_type():
    return sa.JSON() if get_is_sqlite() else Vector(1536)


def upgrade() -> None:
    is_sqlite = get_is_sqlite()

    # Add columns and FK constraints to skills_registry in batch mode
    with op.batch_alter_table("skills_registry") as batch_op:
        batch_op.add_column(
            sa.Column("is_specialization", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
        batch_op.add_column(
            sa.Column("parent_skill", sa.String(128), nullable=True),
        )
        batch_op.add_column(
            sa.Column("brand_id", uuid_type(), nullable=True),
        )
        batch_op.create_foreign_key(
            "fk_skills_registry_parent_skill",
            "skills_registry",
            ["parent_skill"],
            ["name"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_skills_registry_brand_id",
            "brands",
            ["brand_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # Add context_embedding to skill_learnings
    op.add_column(
        "skill_learnings",
        sa.Column("context_embedding", vector_type(), nullable=True),
    )
    
    # Add index for cosine similarity queries
    if is_sqlite:
        op.create_index(
            "ix_skill_learnings_context_embedding_cosine",
            "skill_learnings",
            ["context_embedding"],
        )
    else:
        op.create_index(
            "ix_skill_learnings_context_embedding_cosine",
            "skill_learnings",
            ["context_embedding"],
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"context_embedding": "vector_cosine_ops"},
        )


def downgrade() -> None:
    op.drop_index("ix_skill_learnings_context_embedding_cosine", table_name="skill_learnings")
    op.drop_column("skill_learnings", "context_embedding")
    with op.batch_alter_table("skills_registry") as batch_op:
        batch_op.drop_constraint("fk_skills_registry_brand_id", type_="foreignkey")
        batch_op.drop_constraint("fk_skills_registry_parent_skill", type_="foreignkey")
        batch_op.drop_column("brand_id")
        batch_op.drop_column("parent_skill")
        batch_op.drop_column("is_specialization")
