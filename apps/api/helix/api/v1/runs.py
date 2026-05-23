"""Workflow run endpoints — auth-gated, brand- and workspace-scoped."""
from __future__ import annotations

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.acl import (
    assert_brand_access,
    list_user_workspace_ids,
)
from helix.core.config import get_settings
from helix.core.db import get_session
from helix.core.logging import get_logger
from helix.core.sessions import require_user, verify_session
from helix.events.bus import channel_for_run, subscribe
from helix.models.organization import User, Workspace
from helix.models.workflow import WorkflowRun
from helix.schemas.common import Page
from helix.schemas.run import RunCreate, RunRead, RunSummary
from helix.services.run_queue import enqueue_run
from helix.workflows.runner import list_workflows

router = APIRouter(prefix="/runs", tags=["runs"])
log = get_logger(__name__)


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
async def create_run(
    payload: RunCreate,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> RunRead:
    if payload.workflow not in list_workflows():
        raise HTTPException(
            status_code=400,
            detail=f"unknown workflow '{payload.workflow}'. Known: {list_workflows()}",
        )
    brand = await assert_brand_access(session, user, payload.brand_id)

    run = await enqueue_run(
        brand_id=brand.id,
        workspace_id=brand.workspace_id,
        workflow=payload.workflow,
        inputs=payload.inputs,
        config=payload.config,
        user_id=user.id,
    )
    return RunRead.model_validate(run)


@router.get("", response_model=Page[RunSummary])
async def list_runs(
    brand_id: UUID | None = None,
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> Page[RunSummary]:
    settings = get_settings()
    eff_limit = min(limit or settings.page_default_limit, settings.page_max_limit)

    ws_ids = await list_user_workspace_ids(session, user)
    stmt = (
        select(WorkflowRun)
        .where(WorkflowRun.workspace_id.in_(ws_ids))
        .order_by(desc(WorkflowRun.created_at))
        .limit(eff_limit)
        .offset(offset)
    )
    count_q = select(func.count(WorkflowRun.id)).where(WorkflowRun.workspace_id.in_(ws_ids))
    if brand_id:
        await assert_brand_access(session, user, brand_id)
        stmt = stmt.where(WorkflowRun.brand_id == brand_id)
        count_q = count_q.where(WorkflowRun.brand_id == brand_id)

    rows = (await session.scalars(stmt)).all()
    total = (await session.execute(count_q)).scalar_one()
    return Page[RunSummary](
        items=[RunSummary.model_validate(r) for r in rows],
        total=int(total or 0),
        limit=eff_limit,
        offset=offset,
    )


async def _assert_run_access(
    session: AsyncSession, user: User, run_id: UUID
) -> WorkflowRun:
    run = await session.get(WorkflowRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    if run.workspace_id is not None:
        ws = await session.get(Workspace, run.workspace_id)
        if ws is None or ws.organization_id != user.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="run access denied")
    return run


@router.get("/{run_id}", response_model=RunRead)
async def get_run(
    run_id: UUID,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> RunRead:
    run = await _assert_run_access(session, user, run_id)
    return RunRead.model_validate(run)


@router.websocket("/{run_id}/stream")
async def stream_run(ws: WebSocket, run_id: UUID) -> None:
    """Stream Redis pubsub events. Requires a valid session cookie."""
    await ws.accept()

    settings = get_settings()
    cookie = ws.cookies.get(settings.session_cookie_name)
    token = cookie
    if not token:
        auth = ws.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
    payload = verify_session(token) if token else None
    if not payload:
        await ws.close(code=4401)
        return

    from helix.core.db import session_factory

    async with session_factory() as session:
        user = await session.get(User, UUID(payload["uid"]))
        if user is None:
            await ws.close(code=4401)
            return
        try:
            await _assert_run_access(session, user, run_id)
        except HTTPException:
            await ws.close(code=4403)
            return

    channel = channel_for_run(str(run_id))
    log.info("ws.run_stream_connected", run_id=str(run_id), channel=channel)
    try:
        async for event in subscribe(channel):
            try:
                await ws.send_text(json.dumps(event))
            except RuntimeError:
                break
    except WebSocketDisconnect:
        log.info("ws.run_stream_disconnected", run_id=str(run_id))
    except asyncio.CancelledError:
        raise
    except Exception:
        log.exception("ws.run_stream_failed", run_id=str(run_id))
    finally:
        try:
            await ws.close()
        except Exception:
            pass
