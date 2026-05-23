"""OAuth + API-key tool connections per workspace; credentials encrypted at rest."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, LargeBinary, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from helix.models.base import Base, created_at_col, updated_at_col, uuid_pk


class ToolConnection(Base):
    __tablename__ = "tool_connections"

    id: Mapped[uuid_pk]
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    auth_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="api_key")
    account_label: Mapped[str | None] = mapped_column(String(255))
    credentials_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    scopes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[created_at_col | None] = mapped_column(nullable=True)
    created_at: Mapped[created_at_col]
    updated_at: Mapped[updated_at_col]

    __table_args__ = (
        UniqueConstraint("workspace_id", "provider", "account_label", name="uq_tool_conn_provider"),
    )
