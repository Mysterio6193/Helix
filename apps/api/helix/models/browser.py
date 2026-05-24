"""Browser automation models — sessions, actions, and execution logs."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from helix.models.base import Base, created_at_col, updated_at_col, uuid_pk


class BrowserSession(Base):
    """A persistent browser session for automation."""

    __tablename__ = "browser_sessions"

    id: Mapped[uuid_pk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="local")  # local, browserbase, browser_use
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="idle")  # idle, running, paused, closed, error

    target_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_action_at: Mapped[datetime | None] = mapped_column(nullable=True)

    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]


class BrowserAction(Base):
    """Individual browser action log."""

    __tablename__ = "browser_actions"

    id: Mapped[uuid_pk]
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("browser_sessions.id", ondelete="CASCADE"), nullable=False
    )

    action_type: Mapped[str] = mapped_column(String(32), nullable=False)  # navigate, click, type, screenshot, scroll, execute
    selector: Mapped[str | None] = mapped_column(String(255), nullable=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")  # pending, success, failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    screenshot_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[created_at_col]


class BrowserAutomation(Base):
    """High-level browser automation workflow."""

    __tablename__ = "browser_automations"

    id: Mapped[uuid_pk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_site: Mapped[str] = mapped_column(String(32), nullable=False)  # meta_ads, shopify, canva, etc.
    action: Mapped[str] = mapped_column(String(64), nullable=False)  # login, create_campaign, edit_product, etc.

    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # credentials, selectors, etc.
    schedule: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # cron, interval, etc.
    enabled: Mapped[bool] = mapped_column(default=True)

    last_run_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]
