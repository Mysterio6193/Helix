"""DTOs for workflow runs."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RunCreate(BaseModel):
    workflow: str = Field(..., description="Slice name, e.g. 'brand_identity_foundation'")
    brand_id: UUID
    inputs: dict[str, Any] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID
    workspace_id: UUID
    workflow: str
    status: str
    inputs: dict[str, Any]
    config: dict[str, Any]
    error: str | None
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime


class RunSummary(BaseModel):
    """Lightweight list item — no large JSON payloads."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow: str
    brand_id: UUID
    status: str
    created_at: datetime
    started_at: datetime | None
    ended_at: datetime | None
