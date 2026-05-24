"""Initial schema: all 16 tables + pgvector + FTS indexes.

Revision ID: 0001
Revises:
Create Date: 2026-05-19
"""
from __future__ import annotations

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def get_is_sqlite() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "sqlite"


def uuid_type():
    return sa.String(36) if get_is_sqlite() else postgresql.UUID(as_uuid=True)


def server_default_uuid():
    return None if get_is_sqlite() else sa.text("uuid_generate_v4()")


def json_type():
    return sa.JSON() if get_is_sqlite() else postgresql.JSONB()


def vector_type():
    return sa.JSON() if get_is_sqlite() else Vector(1536)


def tsv_column_args():
    if get_is_sqlite():
        return [sa.String(), sa.Computed("coalesce(content, '') || ' ' || coalesce(summary, '')")]
    return [postgresql.TSVECTOR(), sa.Computed("to_tsvector('english', coalesce(content,'') || ' ' || coalesce(summary,''))", persisted=True)]


def upgrade() -> None:
    is_sqlite = get_is_sqlite()

    # Extensions are also installed via postgres/init.sql, but ensure idempotently.
    if not is_sqlite:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        op.execute("CREATE EXTENSION IF NOT EXISTS btree_gin")

    # organizations
    op.create_table(
        "organizations",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column("metadata", json_type(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # users
    op.create_table(
        "users",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("organization_id", uuid_type(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("role", sa.String(64), nullable=False, server_default="member"),
        sa.Column("metadata", json_type(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # workspaces
    op.create_table(
        "workspaces",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("organization_id", uuid_type(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("settings", json_type(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "slug", name="uq_workspace_org_slug"),
    )

    # brands
    op.create_table(
        "brands",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("workspace_id", uuid_type(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("tagline", sa.Text(), nullable=True),
        sa.Column("mission", sa.Text(), nullable=True),
        sa.Column("story", sa.Text(), nullable=True),
        sa.Column("target_audience", json_type(), nullable=False, server_default="{}"),
        sa.Column("voice_attributes", json_type(), nullable=False, server_default="{}"),
        sa.Column("positioning", sa.Text(), nullable=True),
        sa.Column("archetype", sa.String(64), nullable=True),
        sa.Column("design_school", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("metadata", json_type(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("workspace_id", "slug", name="uq_brand_workspace_slug"),
    )
    if not is_sqlite:
        op.create_index("ix_brands_name_trgm", "brands", ["name"], postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"})

    # brand_assets
    op.create_table(
        "brand_assets",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("brand_id", uuid_type(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("payload", json_type(), nullable=False, server_default="{}"),
        sa.Column("s3_key", sa.Text(), nullable=True),
        sa.Column("mime_type", sa.String(128), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_brand_assets_brand_kind", "brand_assets", ["brand_id", "kind"])

    # memory_entries (vector + FTS)
    op.create_table(
        "memory_entries",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("workspace_id", uuid_type(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True),
        sa.Column("brand_id", uuid_type(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=True),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("metadata", json_type(), nullable=False, server_default="{}"),
        sa.Column("embedding", vector_type(), nullable=True),
        sa.Column("tsv", *tsv_column_args(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    if not is_sqlite:
        op.execute(
            "CREATE INDEX ix_memory_entries_embedding_cosine ON memory_entries "
            "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
        )
        op.create_index("ix_memory_entries_tsv", "memory_entries", ["tsv"], postgresql_using="gin")
    op.create_index("ix_memory_entries_brand_id", "memory_entries", ["brand_id"])

    # workflows
    op.create_table(
        "workflows",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("graph_version", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("definition", json_type(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # workflow_runs
    op.create_table(
        "workflow_runs",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("workflow_id", uuid_type(), sa.ForeignKey("workflows.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("brand_id", uuid_type(), sa.ForeignKey("brands.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("current_node", sa.String(128), nullable=True),
        sa.Column("input", json_type(), nullable=False, server_default="{}"),
        sa.Column("output", json_type(), nullable=False, server_default="{}"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    if not is_sqlite:
        op.create_index("ix_workflow_runs_status", "workflow_runs", ["status"], postgresql_where=sa.text("status IN ('pending','running')"))
    else:
        op.create_index("ix_workflow_runs_status", "workflow_runs", ["status"])
    op.create_index("ix_workflow_runs_brand", "workflow_runs", ["brand_id"])

    # tasks
    op.create_table(
        "tasks",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("run_id", uuid_type(), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_name", sa.String(128), nullable=False),
        sa.Column("agent", sa.String(64), nullable=True),
        sa.Column("skill", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("retries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input", json_type(), nullable=False, server_default="{}"),
        sa.Column("output", json_type(), nullable=False, server_default="{}"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("langfuse_trace_id", sa.String(128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )

    # assets
    op.create_table(
        "assets",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("brand_id", uuid_type(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=True),
        sa.Column("workflow_run_id", uuid_type(), sa.ForeignKey("workflow_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=True),
        sa.Column("s3_key", sa.Text(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("metadata", json_type(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_assets_brand_kind", "assets", ["brand_id", "kind"])

    # creative_lineage
    op.create_table(
        "creative_lineage",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("parent_asset_id", uuid_type(), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=True),
        sa.Column("child_asset_id", uuid_type(), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workflow_run_id", uuid_type(), sa.ForeignKey("workflow_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("transform", sa.String(128), nullable=False),
        sa.Column("approved", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", json_type(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_lineage_child", "creative_lineage", ["child_asset_id"])

    # events
    op.create_table(
        "events",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("workspace_id", uuid_type(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True),
        sa.Column("brand_id", uuid_type(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=True),
        sa.Column("workflow_run_id", uuid_type(), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("channel", sa.String(128), nullable=True),
        sa.Column("payload", json_type(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_events_brand_created", "events", ["brand_id", "created_at"])
    op.create_index("ix_events_run_created", "events", ["workflow_run_id", "created_at"])

    # tool_connections
    op.create_table(
        "tool_connections",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("workspace_id", uuid_type(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("auth_kind", sa.String(32), nullable=False, server_default="api_key"),
        sa.Column("account_label", sa.String(255), nullable=True),
        sa.Column("credentials_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("scopes", json_type(), nullable=False, server_default="[]"),
        sa.Column("metadata", json_type(), nullable=False, server_default="{}"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("workspace_id", "provider", "account_label", name="uq_tool_conn_provider"),
    )

    # generations
    op.create_table(
        "generations",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("workflow_run_id", uuid_type(), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("task_id", uuid_type(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True),
        sa.Column("brand_id", uuid_type(), sa.ForeignKey("brands.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tool", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("kind", sa.String(32), nullable=False, server_default="text"),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="success"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("langfuse_trace_id", sa.String(128), nullable=True),
        sa.Column("metadata", json_type(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # skills_registry
    op.create_table(
        "skills_registry",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("version", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("manifest_path", sa.Text(), nullable=False),
        sa.Column("handler_path", sa.Text(), nullable=True),
        sa.Column("inputs", json_type(), nullable=False, server_default="{}"),
        sa.Column("outputs", json_type(), nullable=False, server_default="{}"),
        sa.Column("required_tools", json_type(), nullable=False, server_default="[]"),
        sa.Column("dependencies", json_type(), nullable=False, server_default="[]"),
        sa.Column("tags", json_type(), nullable=False, server_default="[]"),
        sa.Column("trigger_phrases", json_type(), nullable=False, server_default="[]"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_stub", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_rate", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # skill_learnings
    op.create_table(
        "skill_learnings",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("skill_id", uuid_type(), sa.ForeignKey("skills_registry.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workflow_run_id", uuid_type(), sa.ForeignKey("workflow_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("brand_id", uuid_type(), sa.ForeignKey("brands.id", ondelete="SET NULL"), nullable=True),
        sa.Column("trigger_context", sa.Text(), nullable=True),
        sa.Column("prompt_delta", sa.Text(), nullable=True),
        sa.Column("success_markers", json_type(), nullable=False, server_default="{}"),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("applied_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # design_systems
    op.create_table(
        "design_systems",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("school", sa.String(64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("palette", json_type(), nullable=False, server_default="{}"),
        sa.Column("typography", json_type(), nullable=False, server_default="{}"),
        sa.Column("spacing", json_type(), nullable=False, server_default="{}"),
        sa.Column("motion", json_type(), nullable=False, server_default="{}"),
        sa.Column("components", json_type(), nullable=False, server_default="{}"),
        sa.Column("tags", json_type(), nullable=False, server_default="[]"),
        sa.Column("is_school", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("source_path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # campaigns
    op.create_table(
        "campaigns",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("brand_id", uuid_type(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="planned"),
        sa.Column("schedule", json_type(), nullable=False, server_default="{}"),
        sa.Column("asset_ids", json_type(), nullable=False, server_default="[]"),
        sa.Column("workflow_run_ids", json_type(), nullable=False, server_default="[]"),
        sa.Column("metadata", json_type(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # deployments
    op.create_table(
        "deployments",
        sa.Column("id", uuid_type(), primary_key=True, server_default=server_default_uuid()),
        sa.Column("brand_id", uuid_type(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workflow_run_id", uuid_type(), sa.ForeignKey("workflow_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("provider", sa.String(64), nullable=False, server_default="vercel"),
        sa.Column("repo_url", sa.Text(), nullable=True),
        sa.Column("deployment_url", sa.Text(), nullable=True),
        sa.Column("preview_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("commit_sha", sa.String(64), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("metadata", json_type(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    is_sqlite = get_is_sqlite()

    op.drop_table("deployments")
    op.drop_table("campaigns")
    op.drop_table("design_systems")
    op.drop_table("skill_learnings")
    op.drop_table("skills_registry")
    op.drop_table("generations")
    op.drop_table("tool_connections")
    op.drop_table("events")
    op.drop_index("ix_lineage_child", table_name="creative_lineage")
    op.drop_table("creative_lineage")
    op.drop_index("ix_assets_brand_kind", table_name="assets")
    op.drop_table("assets")
    op.drop_table("tasks")
    op.drop_index("ix_workflow_runs_brand", table_name="workflow_runs")
    op.drop_index("ix_workflow_runs_status", table_name="workflow_runs")
    op.drop_table("workflow_runs")
    op.drop_table("workflows")
    op.drop_index("ix_memory_entries_brand_id", table_name="memory_entries")
    if not is_sqlite:
        op.drop_index("ix_memory_entries_tsv", table_name="memory_entries")
        op.execute("DROP INDEX IF EXISTS ix_memory_entries_embedding_cosine")
    op.drop_table("memory_entries")
    op.drop_index("ix_brand_assets_brand_kind", table_name="brand_assets")
    op.drop_table("brand_assets")
    if not is_sqlite:
        op.drop_index("ix_brands_name_trgm", table_name="brands")
    op.drop_table("brands")
    op.drop_table("workspaces")
    op.drop_table("users")
    op.drop_table("organizations")
