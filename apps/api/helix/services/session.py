from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.models.runtime import AgentSession, ScheduledJob, Trigger
from helix.schemas.session import (
    AgentSessionCreate,
    AgentSessionUpdate,
    ScheduledJobCreate,
    ScheduledJobUpdate,
    TriggerCreate,
    TriggerUpdate,
)


# ---------------------------------------------------------------------------
# Agent Sessions
# ---------------------------------------------------------------------------
async def create_agent_session(
    db: AsyncSession,
    payload: AgentSessionCreate,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> AgentSession:
    session = AgentSession(
        workspace_id=workspace_id,
        created_by=user_id,
        brand_id=payload.brand_id,
        agent=payload.agent,
        name=payload.name,
        description=payload.description,
        status=payload.status,
        mode=payload.mode,
        goal=payload.goal,
        config=payload.config,
        memory=payload.memory,
        heartbeat_interval_s=payload.heartbeat_interval_s,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def get_agent_session(db: AsyncSession, session_id: uuid.UUID) -> AgentSession | None:
    return await db.get(AgentSession, session_id)


async def list_agent_sessions_in_workspaces(
    db: AsyncSession,
    *,
    workspace_ids: list[uuid.UUID],
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AgentSession], int]:
    if not workspace_ids:
        return [], 0
    base = select(AgentSession).where(AgentSession.workspace_id.in_(workspace_ids))
    count_q = (
        select(func.count())
        .select_from(AgentSession)
        .where(AgentSession.workspace_id.in_(workspace_ids))
    )
    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(base.order_by(AgentSession.created_at.desc()).limit(limit).offset(offset))
    return list(result.scalars().all()), total


async def update_agent_session(
    db: AsyncSession, session: AgentSession, payload: AgentSessionUpdate
) -> AgentSession:
    for key, value in payload.model_dump(exclude_unset=True).items():
        if hasattr(session, key):
            setattr(session, key, value)
    await db.flush()
    await db.refresh(session)
    return session


async def delete_agent_session(db: AsyncSession, session: AgentSession) -> None:
    await db.delete(session)
    await db.flush()


# ---------------------------------------------------------------------------
# Scheduled Jobs
# ---------------------------------------------------------------------------
async def create_scheduled_job(
    db: AsyncSession,
    payload: ScheduledJobCreate,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> ScheduledJob:
    job = ScheduledJob(
        workspace_id=workspace_id,
        created_by=user_id,
        brand_id=payload.brand_id,
        session_id=payload.session_id,
        name=payload.name,
        workflow=payload.workflow,
        cron=payload.cron,
        interval_s=payload.interval_s,
        timezone=payload.timezone,
        inputs=payload.inputs,
        config=payload.config,
        enabled=payload.enabled,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


async def get_scheduled_job(db: AsyncSession, job_id: uuid.UUID) -> ScheduledJob | None:
    return await db.get(ScheduledJob, job_id)


async def list_scheduled_jobs_in_workspaces(
    db: AsyncSession,
    *,
    workspace_ids: list[uuid.UUID],
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ScheduledJob], int]:
    if not workspace_ids:
        return [], 0
    base = select(ScheduledJob).where(ScheduledJob.workspace_id.in_(workspace_ids))
    count_q = (
        select(func.count())
        .select_from(ScheduledJob)
        .where(ScheduledJob.workspace_id.in_(workspace_ids))
    )
    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(base.order_by(ScheduledJob.created_at.desc()).limit(limit).offset(offset))
    return list(result.scalars().all()), total


async def update_scheduled_job(
    db: AsyncSession, job: ScheduledJob, payload: ScheduledJobUpdate
) -> ScheduledJob:
    for key, value in payload.model_dump(exclude_unset=True).items():
        if hasattr(job, key):
            setattr(job, key, value)
    await db.flush()
    await db.refresh(job)
    return job


async def delete_scheduled_job(db: AsyncSession, job: ScheduledJob) -> None:
    await db.delete(job)
    await db.flush()


# ---------------------------------------------------------------------------
# Triggers
# ---------------------------------------------------------------------------
async def create_trigger(
    db: AsyncSession,
    payload: TriggerCreate,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> Trigger:
    trigger = Trigger(
        workspace_id=workspace_id,
        created_by=user_id,
        brand_id=payload.brand_id,
        session_id=payload.session_id,
        name=payload.name,
        source=payload.source,
        event_kind=payload.event_kind,
        channel_pattern=payload.channel_pattern,
        filter=payload.filter,
        workflow=payload.workflow,
        inputs_template=payload.inputs_template,
        config=payload.config,
        enabled=payload.enabled,
        debounce_s=payload.debounce_s,
    )
    db.add(trigger)
    await db.flush()
    await db.refresh(trigger)
    return trigger


async def get_trigger(db: AsyncSession, trigger_id: uuid.UUID) -> Trigger | None:
    return await db.get(Trigger, trigger_id)


async def list_triggers_in_workspaces(
    db: AsyncSession,
    *,
    workspace_ids: list[uuid.UUID],
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Trigger], int]:
    if not workspace_ids:
        return [], 0
    base = select(Trigger).where(Trigger.workspace_id.in_(workspace_ids))
    count_q = (
        select(func.count())
        .select_from(Trigger)
        .where(Trigger.workspace_id.in_(workspace_ids))
    )
    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(base.order_by(Trigger.created_at.desc()).limit(limit).offset(offset))
    return list(result.scalars().all()), total


async def update_trigger(
    db: AsyncSession, trigger: Trigger, payload: TriggerUpdate
) -> Trigger:
    for key, value in payload.model_dump(exclude_unset=True).items():
        if hasattr(trigger, key):
            setattr(trigger, key, value)
    await db.flush()
    await db.refresh(trigger)
    return trigger


async def delete_trigger(db: AsyncSession, trigger: Trigger) -> None:
    await db.delete(trigger)
    await db.flush()
