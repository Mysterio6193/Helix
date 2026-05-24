"""Helpers used across LangGraph nodes."""
from __future__ import annotations

import time
from datetime import UTC
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.db import session_factory
from helix.events.bus import channel_for_run, publish
from helix.memory.brand_memory import load_brand_context
from helix.models.workflow import Asset, Task, WorkflowRun


async def emit_event(*, run_id: str | UUID, kind: str, payload: dict[str, Any]) -> None:
    """Publish a Redis event on the run channel + persist Event row."""
    run_uuid = UUID(str(run_id)) if isinstance(run_id, str) else run_id
    await publish(
        None,
        channel=channel_for_run(run_uuid),
        kind=kind,
        payload=payload,
        workflow_run_id=run_uuid,
        persist=False,
    )


async def load_initial_brand_context(state: dict[str, Any]) -> dict[str, Any]:
    """Load brand context from DB at the start of a run (runs once per workflow)."""
    async with session_factory() as session:
        ctx = await load_brand_context(session, brand_id=UUID(state["brand_id"]))
    
    # Compute and cache embedding for semantic learnings retrieval
    from helix.memory.embeddings import embed
    text_to_embed = f"{ctx.get('name', '')} {ctx.get('category', '')} {ctx.get('positioning', '')}"
    ctx["embedding"] = await embed(text_to_embed)
    return ctx


async def record_step(
    *,
    state: dict[str, Any],
    agent: str,
    skill: str | None,
    started_at: float,
    status: str,
    cost_usd: float = 0.0,
    tokens_in: int = 0,
    tokens_out: int = 0,
    output_summary: str | None = None,
    error: str | None = None,
    artifact_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Build a step record dict (for appending to state['steps'])."""
    return {
        "step": f"{agent}:{skill or '_'}",
        "agent": agent,
        "skill": skill,
        "started_at": started_at,
        "ended_at": time.time(),
        "status": status,
        "cost_usd": cost_usd,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "output_summary": output_summary,
        "error": error,
        "artifact_ids": artifact_ids or [],
    }


async def persist_asset(
    session: AsyncSession,
    *,
    run_id: UUID,
    brand_id: UUID,
    workspace_id: UUID,
    purpose: str,
    kind: str,
    storage_key: str | None = None,
    storage_url: str | None = None,
    mime_type: str | None = None,
    width: int | None = None,
    height: int | None = None,
    text_content: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Asset:
    """Insert an Asset row and return it."""
    asset = Asset(
        workflow_run_id=run_id,
        brand_id=brand_id,
        workspace_id=workspace_id,
        purpose=purpose,
        kind=kind,
        storage_key=storage_key,
        storage_url=storage_url,
        mime_type=mime_type,
        width=width,
        height=height,
        text_content=text_content,
        metadata_=metadata or {},
    )
    session.add(asset)
    await session.flush()
    return asset


async def persist_task(
    session: AsyncSession,
    *,
    run_id: UUID,
    name: str,
    agent: str,
    skill: str | None = None,
    status: str = "pending",
    inputs: dict | None = None,
    outputs: dict | None = None,
) -> Task:
    task = Task(
        workflow_run_id=run_id,
        name=name,
        agent=agent,
        skill=skill,
        status=status,
        inputs=inputs or {},
        outputs=outputs or {},
    )
    session.add(task)
    await session.flush()
    return task


async def mark_run_status(
    session: AsyncSession,
    *,
    run_id: UUID,
    status: str,
    error: str | None = None,
) -> None:
    run = await session.get(WorkflowRun, run_id)
    if run is None:
        return
    run.status = status
    if status == "running" and run.started_at is None:
        from datetime import datetime

        run.started_at = datetime.now(UTC)
    if status in ("succeeded", "failed", "canceled"):
        from datetime import datetime

        run.ended_at = datetime.now(UTC)
    if error:
        run.error = error
    await session.flush()
