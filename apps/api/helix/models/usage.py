"""Usage tracking and user API keys for BYOK + subscription billing."""
from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from helix.models.base import Base, created_at_col, uuid_pk


class UserApiKey(Base):
    """Per-user provider API keys (Bring Your Own Key). Encrypted at rest."""

    __tablename__ = "user_api_keys"

    id: Mapped[uuid_pk]
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(32), nullable=False)
    key_ciphertext: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[created_at_col]

    __table_args__ = (
        sa.UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )


class UsageRecord(Base):
    """Per-call token usage for subscription billing."""

    __tablename__ = "usage_records"

    id: Mapped[uuid_pk]
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[created_at_col]

    __table_args__ = (
        sa.Index("ix_usage_org_created", "organization_id", "created_at"),
        sa.Index("ix_usage_user_created", "user_id", "created_at"),
    )
