"""Billing models — Stripe subscription state mirrored locally.

We treat Stripe as the source of truth for billing state, but keep a local
mirror so the API can answer "what tier is this org on?" without a round-trip
to Stripe on every request. Updated via webhook events.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helix.models.base import Base, created_at_col, updated_at_col, uuid_pk

if TYPE_CHECKING:
    from helix.models.organization import Organization


# Plan tier identifiers used internally. Map to Stripe price IDs via settings.
PLAN_FREE = "free"
PLAN_STARTER = "starter"
PLAN_PRO = "pro"
PLAN_BUSINESS = "business"

# Subscription status values mirror Stripe's vocabulary.
SUB_STATUS_ACTIVE = "active"
SUB_STATUS_TRIALING = "trialing"
SUB_STATUS_PAST_DUE = "past_due"
SUB_STATUS_CANCELED = "canceled"
SUB_STATUS_UNPAID = "unpaid"
SUB_STATUS_INCOMPLETE = "incomplete"


class Subscription(Base):
    """One row per organization. NULL means the org is on the free tier."""

    __tablename__ = "subscriptions"

    id: Mapped[uuid_pk]

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Stripe identifiers
    stripe_customer_id: Mapped[str | None] = mapped_column(String(128), index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(128), index=True)
    stripe_price_id: Mapped[str | None] = mapped_column(String(128))

    # Local denormalization for fast lookup
    plan: Mapped[str] = mapped_column(String(32), nullable=False, default=PLAN_FREE)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=SUB_STATUS_ACTIVE
    )

    # When the current paid period ends. NULL on free tier.
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default="false"
    )

    # Raw Stripe payload of the most recent sub event, for audit/debug
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )

    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]

    organization: Mapped["Organization"] = relationship(
        "Organization",
        primaryjoin="Subscription.organization_id == Organization.id",
        foreign_keys=[organization_id],
    )


class BillingEvent(Base):
    """Audit log of processed Stripe webhook events for idempotency."""

    __tablename__ = "billing_events"

    id: Mapped[uuid_pk]
    stripe_event_id: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        index=True,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[created_at_col]
