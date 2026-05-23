"""Skill contract — manifest + handler + closed-loop learning interface."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class SkillManifest:
    """Parsed YAML frontmatter from SKILL.md (marketingskills + skillkit pattern)."""

    name: str
    description: str
    version: str = "1.0.0"
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    required_tools: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    trigger_phrases: list[str] = field(default_factory=list)
    manifest_path: str = ""
    is_stub: bool = False
    is_specialization: bool = False
    parent_skill: str | None = None
    brand_id: str | None = None


@dataclass
class SkillContext:
    """Foundation context passed to every skill handler."""

    db: AsyncSession
    brand_id: uuid.UUID | None
    workflow_run_id: uuid.UUID | None
    task_id: uuid.UUID | None
    workspace_id: uuid.UUID | None
    brand_context: dict[str, Any] = field(default_factory=dict)
    inputs: dict[str, Any] = field(default_factory=dict)
    learnings: list[str] = field(default_factory=list)


@dataclass
class SkillResult:
    ok: bool
    outputs: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    asset_ids: list[uuid.UUID] = field(default_factory=list)
    cost_usd: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# Handler signature: `async def handler(ctx: SkillContext) -> SkillResult`
SkillHandler = Callable[[SkillContext], Awaitable[SkillResult]]


@dataclass
class Skill:
    """Pair of manifest + handler, registered into the in-memory registry."""

    manifest: SkillManifest
    handler: SkillHandler | None = None


# Decorator used by handler modules to declare the binding to a manifest name.
_PENDING_HANDLERS: dict[str, SkillHandler] = {}


def register_skill_handler(name: str) -> Callable[[SkillHandler], SkillHandler]:
    def decorator(fn: SkillHandler) -> SkillHandler:
        _PENDING_HANDLERS[name] = fn
        return fn

    return decorator


def drain_pending_handlers() -> dict[str, SkillHandler]:
    snapshot = dict(_PENDING_HANDLERS)
    _PENDING_HANDLERS.clear()
    return snapshot
