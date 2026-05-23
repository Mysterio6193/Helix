from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentSessionCreate(BaseModel):
    agent: str
    name: str
    workspace_id: uuid.UUID | None = None
    description: str | None = None
    brand_id: uuid.UUID | None = None
    status: str = "idle"
    mode: str = "assisted"
    goal: str | None = None
    config: dict = Field(default_factory=dict)
    memory: dict = Field(default_factory=dict)
    heartbeat_interval_s: int = 60


class AgentSessionUpdate(BaseModel):
    agent: str | None = None
    name: str | None = None
    description: str | None = None
    brand_id: uuid.UUID | None = None
    status: str | None = None
    mode: str | None = None
    goal: str | None = None
    config: dict | None = None
    memory: dict | None = None
    heartbeat_interval_s: int | None = None


class AgentSessionRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    brand_id: uuid.UUID | None
    created_by: uuid.UUID | None
    agent: str
    name: str
    description: str | None
    status: str
    mode: str
    goal: str | None
    config: dict
    memory: dict
    heartbeat_interval_s: int
    last_heartbeat_at: datetime | None
    last_active_at: datetime | None
    error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScheduledJobCreate(BaseModel):
    name: str
    workflow: str
    workspace_id: uuid.UUID | None = None
    cron: str | None = None
    interval_s: int | None = None
    timezone: str = "UTC"
    inputs: dict = Field(default_factory=dict)
    config: dict = Field(default_factory=dict)
    enabled: bool = True
    session_id: uuid.UUID | None = None
    brand_id: uuid.UUID | None = None


class ScheduledJobUpdate(BaseModel):
    name: str | None = None
    workflow: str | None = None
    cron: str | None = None
    interval_s: int | None = None
    timezone: str | None = None
    inputs: dict | None = None
    config: dict | None = None
    enabled: bool | None = None
    session_id: uuid.UUID | None = None
    brand_id: uuid.UUID | None = None


class ScheduledJobRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    brand_id: uuid.UUID | None
    session_id: uuid.UUID | None
    created_by: uuid.UUID | None
    name: str
    workflow: str
    cron: str | None
    interval_s: int | None
    timezone: str
    inputs: dict
    config: dict
    enabled: bool
    next_run_at: datetime | None
    last_run_at: datetime | None
    last_run_id: uuid.UUID | None
    last_status: str | None
    consecutive_failures: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TriggerCreate(BaseModel):
    name: str
    workflow: str
    workspace_id: uuid.UUID | None = None
    source: str = "event"
    event_kind: str | None = None
    channel_pattern: str | None = None
    filter: dict = Field(default_factory=dict)
    inputs_template: dict = Field(default_factory=dict)
    config: dict = Field(default_factory=dict)
    enabled: bool = True
    debounce_s: int = 0
    session_id: uuid.UUID | None = None
    brand_id: uuid.UUID | None = None


class TriggerUpdate(BaseModel):
    name: str | None = None
    workflow: str | None = None
    source: str | None = None
    event_kind: str | None = None
    channel_pattern: str | None = None
    filter: dict | None = None
    inputs_template: dict | None = None
    config: dict | None = None
    enabled: bool | None = None
    debounce_s: int | None = None
    session_id: uuid.UUID | None = None
    brand_id: uuid.UUID | None = None


class TriggerRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    brand_id: uuid.UUID | None
    session_id: uuid.UUID | None
    created_by: uuid.UUID | None
    name: str
    source: str
    event_kind: str | None
    channel_pattern: str | None
    filter: dict
    workflow: str
    inputs_template: dict
    config: dict
    enabled: bool
    debounce_s: int
    last_fired_at: datetime | None
    fire_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
