"""Session, ScheduledJob, and Trigger endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.acl import (
    assert_workspace_access,
    get_default_workspace_for_user,
    list_user_workspace_ids,
)
from helix.core.config import get_settings
from helix.core.db import get_db
from helix.core.sessions import require_user
from helix.models.organization import User
from helix.schemas.common import Page
from helix.schemas.session import (
    AgentSessionCreate,
    AgentSessionRead,
    AgentSessionUpdate,
    ScheduledJobCreate,
    ScheduledJobRead,
    ScheduledJobUpdate,
    TriggerCreate,
    TriggerRead,
    TriggerUpdate,
)
from helix.services import session as session_service

router = APIRouter(prefix="", tags=["runtime"])


# ---------------------------------------------------------------------------
# Agent Sessions
# ---------------------------------------------------------------------------
@router.post("/agent-sessions", response_model=AgentSessionRead, status_code=status.HTTP_201_CREATED)
async def create_agent_session(
    payload: AgentSessionCreate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> AgentSessionRead:
    if payload.workspace_id is not None:
        await assert_workspace_access(db, user, payload.workspace_id)
        workspace_id = payload.workspace_id
    else:
        ws = await get_default_workspace_for_user(db, user)
        workspace_id = ws.id

    session = await session_service.create_agent_session(
        db, payload, workspace_id=workspace_id, user_id=user.id
    )
    await db.commit()
    return AgentSessionRead.model_validate(session)


@router.get("/agent-sessions", response_model=Page[AgentSessionRead])
async def list_agent_sessions(
    workspace_id: UUID | None = None,
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> Page[AgentSessionRead]:
    settings = get_settings()
    eff_limit = min(limit or settings.page_default_limit, settings.page_max_limit)

    if workspace_id is not None:
        await assert_workspace_access(db, user, workspace_id)
        ws_ids = [workspace_id]
    else:
        ws_ids = await list_user_workspace_ids(db, user)

    items, total = await session_service.list_agent_sessions_in_workspaces(
        db, workspace_ids=ws_ids, limit=eff_limit, offset=offset
    )

    return Page[AgentSessionRead](
        items=[AgentSessionRead.model_validate(x) for x in items],
        total=total,
        limit=eff_limit,
        offset=offset,
    )


@router.get("/agent-sessions/{session_id}", response_model=AgentSessionRead)
async def get_agent_session(
    session_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> AgentSessionRead:
    session = await session_service.get_agent_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="agent session not found")
    await assert_workspace_access(db, user, session.workspace_id)
    return AgentSessionRead.model_validate(session)


@router.patch("/agent-sessions/{session_id}", response_model=AgentSessionRead)
async def update_agent_session(
    session_id: UUID,
    payload: AgentSessionUpdate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> AgentSessionRead:
    session = await session_service.get_agent_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="agent session not found")
    await assert_workspace_access(db, user, session.workspace_id)
    
    session = await session_service.update_agent_session(db, session, payload)
    await db.commit()
    return AgentSessionRead.model_validate(session)


@router.delete(
    "/agent-sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
async def delete_agent_session(
    session_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    session = await session_service.get_agent_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="agent session not found")
    await assert_workspace_access(db, user, session.workspace_id)

    await session_service.delete_agent_session(db, session)
    await db.commit()


# ---------------------------------------------------------------------------
# Scheduled Jobs
# ---------------------------------------------------------------------------
@router.post("/scheduled-jobs", response_model=ScheduledJobRead, status_code=status.HTTP_201_CREATED)
async def create_scheduled_job(
    payload: ScheduledJobCreate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> ScheduledJobRead:
    if payload.workspace_id is not None:
        await assert_workspace_access(db, user, payload.workspace_id)
        workspace_id = payload.workspace_id
    else:
        ws = await get_default_workspace_for_user(db, user)
        workspace_id = ws.id

    job = await session_service.create_scheduled_job(
        db, payload, workspace_id=workspace_id, user_id=user.id
    )
    await db.commit()
    return ScheduledJobRead.model_validate(job)


@router.get("/scheduled-jobs", response_model=Page[ScheduledJobRead])
async def list_scheduled_jobs(
    workspace_id: UUID | None = None,
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> Page[ScheduledJobRead]:
    settings = get_settings()
    eff_limit = min(limit or settings.page_default_limit, settings.page_max_limit)

    if workspace_id is not None:
        await assert_workspace_access(db, user, workspace_id)
        ws_ids = [workspace_id]
    else:
        ws_ids = await list_user_workspace_ids(db, user)

    items, total = await session_service.list_scheduled_jobs_in_workspaces(
        db, workspace_ids=ws_ids, limit=eff_limit, offset=offset
    )

    return Page[ScheduledJobRead](
        items=[ScheduledJobRead.model_validate(x) for x in items],
        total=total,
        limit=eff_limit,
        offset=offset,
    )


@router.get("/scheduled-jobs/{job_id}", response_model=ScheduledJobRead)
async def get_scheduled_job(
    job_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> ScheduledJobRead:
    job = await session_service.get_scheduled_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="scheduled job not found")
    await assert_workspace_access(db, user, job.workspace_id)
    return ScheduledJobRead.model_validate(job)


@router.patch("/scheduled-jobs/{job_id}", response_model=ScheduledJobRead)
async def update_scheduled_job(
    job_id: UUID,
    payload: ScheduledJobUpdate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> ScheduledJobRead:
    job = await session_service.get_scheduled_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="scheduled job not found")
    await assert_workspace_access(db, user, job.workspace_id)
    
    job = await session_service.update_scheduled_job(db, job, payload)
    await db.commit()
    return ScheduledJobRead.model_validate(job)


@router.delete(
    "/scheduled-jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
async def delete_scheduled_job(
    job_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    job = await session_service.get_scheduled_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="scheduled job not found")
    await assert_workspace_access(db, user, job.workspace_id)

    await session_service.delete_scheduled_job(db, job)
    await db.commit()


# ---------------------------------------------------------------------------
# Triggers
# ---------------------------------------------------------------------------
@router.post("/triggers", response_model=TriggerRead, status_code=status.HTTP_201_CREATED)
async def create_trigger(
    payload: TriggerCreate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> TriggerRead:
    if payload.workspace_id is not None:
        await assert_workspace_access(db, user, payload.workspace_id)
        workspace_id = payload.workspace_id
    else:
        ws = await get_default_workspace_for_user(db, user)
        workspace_id = ws.id

    trigger = await session_service.create_trigger(
        db, payload, workspace_id=workspace_id, user_id=user.id
    )
    await db.commit()
    return TriggerRead.model_validate(trigger)


@router.get("/triggers", response_model=Page[TriggerRead])
async def list_triggers(
    workspace_id: UUID | None = None,
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> Page[TriggerRead]:
    settings = get_settings()
    eff_limit = min(limit or settings.page_default_limit, settings.page_max_limit)

    if workspace_id is not None:
        await assert_workspace_access(db, user, workspace_id)
        ws_ids = [workspace_id]
    else:
        ws_ids = await list_user_workspace_ids(db, user)

    items, total = await session_service.list_triggers_in_workspaces(
        db, workspace_ids=ws_ids, limit=eff_limit, offset=offset
    )

    return Page[TriggerRead](
        items=[TriggerRead.model_validate(x) for x in items],
        total=total,
        limit=eff_limit,
        offset=offset,
    )


@router.get("/triggers/{trigger_id}", response_model=TriggerRead)
async def get_trigger(
    trigger_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> TriggerRead:
    trigger = await session_service.get_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="trigger not found")
    await assert_workspace_access(db, user, trigger.workspace_id)
    return TriggerRead.model_validate(trigger)


@router.patch("/triggers/{trigger_id}", response_model=TriggerRead)
async def update_trigger(
    trigger_id: UUID,
    payload: TriggerUpdate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> TriggerRead:
    trigger = await session_service.get_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="trigger not found")
    await assert_workspace_access(db, user, trigger.workspace_id)
    
    trigger = await session_service.update_trigger(db, trigger, payload)
    await db.commit()
    return TriggerRead.model_validate(trigger)


@router.delete(
    "/triggers/{trigger_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
async def delete_trigger(
    trigger_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    trigger = await session_service.get_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="trigger not found")
    await assert_workspace_access(db, user, trigger.workspace_id)

    await session_service.delete_trigger(db, trigger)
    await db.commit()
