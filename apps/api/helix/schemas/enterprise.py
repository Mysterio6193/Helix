"""Enterprise DTOs: API keys, audit logs, organization invitations, members."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from helix.schemas.common import ORMBase, TimestampedDTO

# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------

class ApiKeyCreate(ORMBase):
    name: str = Field(min_length=1, max_length=255)
    scopes: dict = Field(default_factory=lambda: {"all": True})


class ApiKeyRead(TimestampedDTO):
    organization_id: UUID
    user_id: UUID
    name: str
    key_prefix: str
    scopes: dict
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    enabled: bool


class ApiKeyCreated(ApiKeyRead):
    raw_key: str


# ---------------------------------------------------------------------------
# Audit Logs
# ---------------------------------------------------------------------------

class AuditLogRead(ORMBase):
    id: UUID
    organization_id: UUID
    actor_id: UUID | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    details: dict = Field(default_factory=dict)
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Organization Invitations
# ---------------------------------------------------------------------------

class InvitationCreate(ORMBase):
    email: str = Field(min_length=1, max_length=255)
    role: str = Field(default="member", max_length=64)


class InvitationRead(TimestampedDTO):
    organization_id: UUID
    invited_by: UUID
    email: str
    role: str
    token: str
    expires_at: datetime
    accepted_at: datetime | None = None
    revoked_at: datetime | None = None


class InvitationAccept(ORMBase):
    token: str


# ---------------------------------------------------------------------------
# Organization Members
# ---------------------------------------------------------------------------

class MemberRead(ORMBase):
    id: UUID
    email: str
    name: str | None = None
    role: str
    created_at: datetime


class MemberRoleUpdate(ORMBase):
    role: str = Field(min_length=1, max_length=64)


# ---------------------------------------------------------------------------
# Usage / Rate Limits
# ---------------------------------------------------------------------------

class UsageRead(ORMBase):
    brands: int = 0
    brand_limit: int = 1
    runs_this_month: int = 0
    run_limit: int = 50
    members: int = 0
    member_limit: int = 1
    api_keys: int = 0
    api_key_limit: int = 5
