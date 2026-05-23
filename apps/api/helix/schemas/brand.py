"""Brand DTOs."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from helix.schemas.common import ORMBase, TimestampedDTO


class BrandCreate(ORMBase):
    workspace_id: UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=128)
    category: str | None = Field(default=None, max_length=128)
    tagline: str | None = None
    mission: str | None = None
    story: str | None = None
    target_audience: dict[str, Any] = Field(default_factory=dict)
    voice_attributes: dict[str, Any] = Field(default_factory=dict)
    positioning: str | None = None
    archetype: str | None = None
    design_school: str | None = None
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")


class BrandUpdate(ORMBase):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = None
    tagline: str | None = None
    mission: str | None = None
    story: str | None = None
    target_audience: dict[str, Any] | None = None
    voice_attributes: dict[str, Any] | None = None
    positioning: str | None = None
    archetype: str | None = None
    design_school: str | None = None
    status: str | None = None
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")


class BrandRead(TimestampedDTO):
    workspace_id: UUID
    name: str
    slug: str
    category: str | None
    tagline: str | None
    mission: str | None
    story: str | None
    target_audience: dict[str, Any]
    voice_attributes: dict[str, Any]
    positioning: str | None
    archetype: str | None
    design_school: str | None
    status: str
    metadata_: dict[str, Any] = Field(alias="metadata")


class BrandAssetRead(ORMBase):
    id: UUID
    brand_id: UUID
    kind: str
    payload: dict[str, Any]
    s3_key: str | None
    mime_type: str | None
    version: int
    is_primary: bool
    created_at: datetime
