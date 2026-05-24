"""Browser automation API — sessions, actions, and automations."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.acl import list_user_workspace_ids
from helix.core.db import get_db
from helix.core.sessions import require_user
from helix.models.browser import BrowserAction, BrowserAutomation, BrowserSession
from helix.models.organization import User
from helix.services.ws_manager import manager as ws_manager
from helix.tools.registry import get_tool

router = APIRouter(prefix="/browser", tags=["browser"])


@router.get("/status")
async def browser_status() -> dict:
    """Check if the Playwright browser executor is available."""
    try:
        from helix.services.browser_executor import get_executor
        executor = await get_executor()
        connected = executor._browser is not None and executor._browser.is_connected()
        return {"available": True, "connected": connected}
    except Exception as exc:
        return {"available": False, "connected": False, "error": str(exc)}


# ─── Schemas ──────────────────────────────────────────────────────────

class BrowserSessionCreate(BaseModel):
    name: str
    target_url: str | None = None
    provider: str = "local"
    config: dict[str, Any] = Field(default_factory=dict)


class BrowserSessionResponse(BaseModel):
    id: str
    name: str
    status: str
    provider: str
    target_url: str | None
    current_url: str | None
    page_title: str | None
    created_at: str | None


class BrowserActionRequest(BaseModel):
    action_type: str  # navigate, click, type, screenshot, scroll, execute
    selector: str | None = None
    value: str | None = None
    url: str | None = None


class BrowserAutomationCreate(BaseModel):
    name: str
    description: str | None = None
    target_site: str
    action: str
    config: dict[str, Any] = Field(default_factory=dict)
    schedule: dict[str, Any] = Field(default_factory=dict)


# ─── Sessions ─────────────────────────────────────────────────────────

@router.get("/sessions", response_model=list[BrowserSessionResponse])
async def list_sessions(
    status: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[BrowserSessionResponse]:
    """Return browser sessions."""
    workspace_ids = await list_user_workspace_ids(db, user)

    query = select(BrowserSession).where(BrowserSession.workspace_id.in_(workspace_ids))
    if status:
        query = query.where(BrowserSession.status == status)

    query = query.order_by(desc(BrowserSession.updated_at)).limit(limit)
    result = await db.execute(query)

    return [
        BrowserSessionResponse(
            id=str(s.id),
            name=s.name,
            status=s.status,
            provider=s.provider,
            target_url=s.target_url,
            current_url=s.current_url,
            page_title=s.page_title,
            created_at=s.created_at.isoformat() if s.created_at else None,
        )
        for s in result.scalars().all()
    ]


@router.post("/sessions", response_model=BrowserSessionResponse)
async def create_session(
    payload: BrowserSessionCreate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> BrowserSessionResponse:
    """Create a new browser session."""
    workspace_ids = await list_user_workspace_ids(db, user)
    if not workspace_ids:
        raise ValueError("No workspace available")

    session = BrowserSession(
        workspace_id=workspace_ids[0],
        created_by=user.id,
        name=payload.name,
        provider=payload.provider,
        target_url=payload.target_url,
        status="idle",
        config=payload.config,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return BrowserSessionResponse(
        id=str(session.id),
        name=session.name,
        status=session.status,
        provider=session.provider,
        target_url=session.target_url,
        current_url=session.current_url,
        page_title=session.page_title,
        created_at=session.created_at.isoformat() if session.created_at else None,
    )


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return session details with recent actions."""
    result = await db.execute(
        select(BrowserSession).where(BrowserSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "Session not found"}

    # Get recent actions
    actions_result = await db.execute(
        select(BrowserAction)
        .where(BrowserAction.session_id == session_id)
        .order_by(desc(BrowserAction.created_at))
        .limit(50)
    )
    actions = actions_result.scalars().all()

    return {
        "id": str(session.id),
        "name": session.name,
        "status": session.status,
        "provider": session.provider,
        "target_url": session.target_url,
        "current_url": session.current_url,
        "page_title": session.page_title,
        "config": session.config,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "actions": [
            {
                "id": str(a.id),
                "action_type": a.action_type,
                "selector": a.selector,
                "value": a.value,
                "url": a.url,
                "status": a.status,
                "error": a.error,
                "result": a.result,
                "screenshot_url": a.screenshot_url,
                "execution_time_ms": a.execution_time_ms,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in actions
        ],
    }


@router.post("/sessions/{session_id}/actions")
async def execute_action(
    session_id: UUID,
    payload: BrowserActionRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Execute a browser action in a session."""
    result = await db.execute(
        select(BrowserSession).where(BrowserSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "Session not found"}

    # Create action log
    action = BrowserAction(
        session_id=session_id,
        action_type=payload.action_type,
        selector=payload.selector,
        value=payload.value,
        url=payload.url,
        status="pending",
    )
    db.add(action)
    await db.flush()

    start_time = datetime.utcnow()

    try:
        # Get the browser tool
        browser_tool = get_tool("helix_browser")
        if not browser_tool:
            raise RuntimeError("Browser tool not available")

        # Build instruction based on action type
        if payload.action_type == "navigate":
            instruction = f"Navigate to {payload.url}"
        elif payload.action_type == "click":
            instruction = f"Click on element matching selector: {payload.selector}"
        elif payload.action_type == "type":
            instruction = f"Type '{payload.value}' into element matching selector: {payload.selector}"
        elif payload.action_type == "screenshot":
            instruction = "Take a screenshot of the current page"
        elif payload.action_type == "scroll":
            instruction = "Scroll down the page"
        elif payload.action_type == "execute":
            instruction = payload.value or "No instruction provided"
        else:
            instruction = f"Perform {payload.action_type} action"

        # Execute via browser-use
        tool_result = await browser_tool.call(instruction=instruction)

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        if tool_result.ok:
            action.status = "success"
            action.result = tool_result.data or {}
            session.status = "running"
            session.last_action_at = datetime.utcnow()
        else:
            action.status = "failed"
            action.error = tool_result.error
            session.status = "error"

        action.execution_time_ms = execution_time

        await db.commit()

        return {
            "action_id": str(action.id),
            "status": action.status,
            "result": action.result,
            "error": action.error,
            "execution_time_ms": execution_time,
        }

    except Exception as e:
        action.status = "failed"
        action.error = str(e)
        await db.commit()

        return {
            "action_id": str(action.id),
            "status": "failed",
            "error": str(e),
        }


@router.post("/sessions/{session_id}/close")
async def close_session(
    session_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Close a browser session."""
    result = await db.execute(
        select(BrowserSession).where(BrowserSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "Session not found"}

    session.status = "closed"
    session.ended_at = datetime.utcnow()
    await db.commit()

    return {"ok": True, "session_id": str(session_id)}


# ─── Automations ──────────────────────────────────────────────────────

@router.get("/automations")
async def list_automations(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return browser automations."""
    workspace_ids = await list_user_workspace_ids(db, user)

    result = await db.execute(
        select(BrowserAutomation)
        .where(BrowserAutomation.workspace_id.in_(workspace_ids))
        .order_by(desc(BrowserAutomation.updated_at))
    )

    return [
        {
            "id": str(a.id),
            "name": a.name,
            "description": a.description,
            "target_site": a.target_site,
            "action": a.action,
            "enabled": a.enabled,
            "run_count": a.run_count,
            "success_count": a.success_count,
            "last_run_at": a.last_run_at.isoformat() if a.last_run_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in result.scalars().all()
    ]


@router.post("/automations")
async def create_automation(
    payload: BrowserAutomationCreate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a browser automation."""
    workspace_ids = await list_user_workspace_ids(db, user)
    if not workspace_ids:
        return {"error": "No workspace available"}

    automation = BrowserAutomation(
        workspace_id=workspace_ids[0],
        name=payload.name,
        description=payload.description,
        target_site=payload.target_site,
        action=payload.action,
        config=payload.config,
        schedule=payload.schedule,
    )
    db.add(automation)
    await db.commit()
    await db.refresh(automation)

    return {"id": str(automation.id), "ok": True}


@router.post("/automations/{automation_id}/run")
async def run_automation(
    automation_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Execute a browser automation with full action logging."""
    result = await db.execute(
        select(BrowserAutomation).where(BrowserAutomation.id == automation_id)
    )
    automation = result.scalar_one_or_none()
    if not automation:
        return {"error": "Automation not found"}

    # Get the page operator tool
    operator_tool = get_tool("helix_page_operator")
    if not operator_tool:
        return {"error": "Page operator tool not available"}

    # Create a session for this run
    session = BrowserSession(
        workspace_id=automation.workspace_id,
        brand_id=automation.brand_id,
        created_by=user.id,
        name=f"Auto-run: {automation.name}",
        provider="local",
        status="running",
        target_url=f"https://{automation.target_site}.com",
        metadata_={"automation_id": str(automation_id), "trigger": "manual"},
        started_at=datetime.utcnow(),
    )
    db.add(session)
    await db.flush()

    start_time = datetime.utcnow()
    actions_log = []

    try:
        # Step 1: Navigate to target site
        nav_action = BrowserAction(
            session_id=session.id,
            action_type="navigate",
            url=f"https://{automation.target_site}.com",
            status="pending",
        )
        db.add(nav_action)
        await db.flush()

        tool_result = await operator_tool.call(
            target_site=automation.target_site,
            action=automation.action,
            payload=automation.config,
        )

        nav_action.status = "success" if tool_result.ok else "failed"
        nav_action.error = tool_result.error if not tool_result.ok else None
        nav_action.result = tool_result.data or {}
        nav_action.execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        actions_log.append({
            "type": "navigate",
            "status": nav_action.status,
            "result": nav_action.result,
        })

        # Step 2: Execute main action
        main_start = datetime.utcnow()
        main_action = BrowserAction(
            session_id=session.id,
            action_type="execute",
            value=automation.action,
            status="pending",
        )
        db.add(main_action)
        await db.flush()

        main_action.status = "success" if tool_result.ok else "failed"
        main_action.error = tool_result.error if not tool_result.ok else None
        main_action.result = tool_result.data or {}
        main_action.execution_time_ms = int((datetime.utcnow() - main_start).total_seconds() * 1000)
        actions_log.append({
            "type": "execute",
            "status": main_action.status,
            "result": main_action.result,
        })

        # Update automation stats
        automation.run_count += 1
        automation.last_run_at = datetime.utcnow()
        automation.last_run_id = session.id

        if tool_result.ok:
            automation.success_count += 1
            session.status = "idle"
        else:
            session.status = "error"

        session.ended_at = datetime.utcnow()
        await db.commit()

        result = {
            "automation_id": str(automation_id),
            "session_id": str(session.id),
            "status": "success" if tool_result.ok else "failed",
            "execution_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000),
            "actions": actions_log,
            "result": tool_result.data if tool_result.ok else None,
            "error": tool_result.error if not tool_result.ok else None,
        }

        try:
            await ws_manager.broadcast("browser", "automation.completed", result)
        except Exception:
            pass

        return result

    except Exception as e:
        session.status = "error"
        session.ended_at = datetime.utcnow()
        automation.run_count += 1
        await db.commit()

        return {
            "automation_id": str(automation_id),
            "session_id": str(session.id),
            "status": "failed",
            "error": str(e),
        }


@router.get("/automations/{automation_id}/replay")
async def replay_automation(
    automation_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return execution replay for an automation's last run."""
    result = await db.execute(
        select(BrowserAutomation).where(BrowserAutomation.id == automation_id)
    )
    automation = result.scalar_one_or_none()
    if not automation:
        return {"error": "Automation not found"}

    if not automation.last_run_id:
        return {
            "automation_id": str(automation_id),
            "automation_name": automation.name,
            "status": "no_runs",
            "message": "This automation has not been run yet",
        }

    # Get the session
    session_result = await db.execute(
        select(BrowserSession).where(BrowserSession.id == automation.last_run_id)
    )
    session = session_result.scalar_one_or_none()

    # Get all actions for this session
    actions_result = await db.execute(
        select(BrowserAction)
        .where(BrowserAction.session_id == automation.last_run_id)
        .order_by(BrowserAction.created_at)
    )
    actions = actions_result.scalars().all()

    return {
        "automation_id": str(automation_id),
        "automation_name": automation.name,
        "session_id": str(automation.last_run_id),
        "status": session.status if session else "unknown",
        "started_at": session.started_at.isoformat() if session and session.started_at else None,
        "ended_at": session.ended_at.isoformat() if session and session.ended_at else None,
        "total_actions": len(actions),
        "success_count": sum(1 for a in actions if a.status == "success"),
        "failed_count": sum(1 for a in actions if a.status == "failed"),
        "actions": [
            {
                "id": str(a.id),
                "action_type": a.action_type,
                "selector": a.selector,
                "value": a.value,
                "url": a.url,
                "status": a.status,
                "error": a.error,
                "result": a.result,
                "execution_time_ms": a.execution_time_ms,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in actions
        ],
    }


@router.post("/automations/{automation_id}/toggle")
async def toggle_automation(
    automation_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Toggle automation enabled status."""
    result = await db.execute(
        select(BrowserAutomation).where(BrowserAutomation.id == automation_id)
    )
    automation = result.scalar_one_or_none()
    if not automation:
        return {"error": "Automation not found"}

    automation.enabled = not automation.enabled
    await db.commit()

    return {"id": str(automation_id), "enabled": automation.enabled}


# ─── Triggers ─────────────────────────────────────────────────────────

@router.post("/triggers/test")
async def test_trigger(
    signal_title: str,
    signal_description: str = "",
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Test the trigger system by simulating a signal."""
    from helix.intelligence.triggers import process_signal_triggers
    from helix.models.intelligence import IntelligenceSignal

    workspace_ids = await list_user_workspace_ids(db, user)
    if not workspace_ids:
        return {"error": "No workspace available"}

    # Create a test signal
    signal = IntelligenceSignal(
        workspace_id=workspace_ids[0],
        layer="campaign",
        signal_type="anomaly",
        severity="warning",
        title=signal_title,
        description=signal_description,
        source_data={"test": True},
        auto_triggered=True,
    )
    db.add(signal)
    await db.flush()

    # Process triggers
    triggered = await process_signal_triggers(db, signal)

    return {
        "signal_id": str(signal.id),
        "triggered": len(triggered),
        "executions": triggered,
    }


# ─── Templates ────────────────────────────────────────────────────────

@router.get("/templates")
async def list_templates() -> list[dict[str, Any]]:
    """Return available browser automation templates."""
    return [
        {
            "id": "meta_ads_login",
            "name": "Meta Ads Manager Login",
            "target_site": "meta_ads",
            "action": "login",
            "description": "Log into Meta Ads Manager",
        },
        {
            "id": "meta_ads_create_campaign",
            "name": "Create Meta Ads Campaign",
            "target_site": "meta_ads",
            "action": "create_campaign",
            "description": "Create a new campaign with specified budget and targeting",
        },
        {
            "id": "shopify_login",
            "name": "Shopify Admin Login",
            "target_site": "shopify",
            "action": "login",
            "description": "Log into Shopify admin panel",
        },
        {
            "id": "shopify_edit_product",
            "name": "Edit Shopify Product",
            "target_site": "shopify",
            "action": "edit_product",
            "description": "Edit product title, description, and pricing",
        },
        {
            "id": "canva_login",
            "name": "Canva Login",
            "target_site": "canva",
            "action": "login",
            "description": "Log into Canva",
        },
        {
            "id": "canva_create_design",
            "name": "Create Canva Design",
            "target_site": "canva",
            "action": "create_design",
            "description": "Create a new design from template",
        },
    ]
