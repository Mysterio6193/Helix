"""Organization and Workspace DTOs."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from helix.schemas.common import ORMBase, TimestampedDTO


class OrganizationRead(TimestampedDTO):
    name: str
    slug: str
    metadata_: dict[str, Any] = Field(alias="metadata")


class WorkspaceCreate(ORMBase):
    name: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=128)
    description: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)


class WorkspaceUpdate(ORMBase):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    settings: dict[str, Any] | None = None


class WorkspaceRead(TimestampedDTO):
    organization_id: UUID
    name: str
    slug: str
    description: str | None
    settings: dict[str, Any]
