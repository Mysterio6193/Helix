"""Shared DTOs."""
from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TimestampedDTO(ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None = None


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class HealthResponse(BaseModel):
    status: str = Field(default="ok")
    version: str
    environment: str
    services: dict[str, str] = Field(default_factory=dict)
