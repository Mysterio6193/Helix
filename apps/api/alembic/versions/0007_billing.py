"""Add Stripe billing tables: subscriptions, billing_events.

We mirror Stripe state locally so the API can answer "what tier is this org on?"
without a round-trip to Stripe. `billing_events` provides idempotency for
webhook processing — Stripe may retry delivery, so we dedupe on event id.

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-23
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def get_is_sqlite() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "sqlite"


def uuid_type():
    return sa.String(36) if get_is_sqlite() else postgresql.UUID(as_uuid=True)


def json_type():
    return sa.JSON() if get_is_sqlite() else postgresql.JSONB()


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column(
            "organization_id",
            uuid_type(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("stripe_customer_id", sa.String(128), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(128), nullable=True),
        sa.Column("stripe_price_id", sa.String(128), nullable=True),
        sa.Column(
            "plan", sa.String(32), nullable=False, server_default="free"
        ),
        sa.Column(
            "status", sa.String(32), nullable=False, server_default="active"
        ),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "cancel_at_period_end",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false") if not get_is_sqlite() else sa.text("0"),
        ),
        sa.Column("metadata", json_type(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_subscriptions_organization_id", "subscriptions", ["organization_id"]
    )
    op.create_index(
        "ix_subscriptions_stripe_customer_id",
        "subscriptions",
        ["stripe_customer_id"],
    )
    op.create_index(
        "ix_subscriptions_stripe_subscription_id",
        "subscriptions",
        ["stripe_subscription_id"],
    )

    op.create_table(
        "billing_events",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column(
            "stripe_event_id", sa.String(128), nullable=False, unique=True
        ),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column(
            "organization_id",
            uuid_type(),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("payload", json_type(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_billing_events_stripe_event_id",
        "billing_events",
        ["stripe_event_id"],
    )
    op.create_index(
        "ix_billing_events_organization_id",
        "billing_events",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_billing_events_organization_id", table_name="billing_events")
    op.drop_index("ix_billing_events_stripe_event_id", table_name="billing_events")
    op.drop_table("billing_events")
    op.drop_index(
        "ix_subscriptions_stripe_subscription_id", table_name="subscriptions"
    )
    op.drop_index(
        "ix_subscriptions_stripe_customer_id", table_name="subscriptions"
    )
    op.drop_index("ix_subscriptions_organization_id", table_name="subscriptions")
    op.drop_table("subscriptions")
