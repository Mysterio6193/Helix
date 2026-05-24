"""Helix operating-system overview API.

This endpoint intentionally exposes Helix-native product concepts only. The
underlying orchestration, rendering, workflow, and execution libraries remain
private implementation details.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.acl import (
    assert_workspace_access,
    get_default_workspace_for_user,
    list_user_workspace_ids,
)
from helix.core.db import get_db
from helix.core.sessions import require_user
from helix.models.brand import Brand
from helix.models.memory import MemoryEntry
from helix.models.organization import User
from helix.models.runtime import AgentSession, ScheduledJob, Trigger
from helix.models.skill import SkillRegistry
from helix.models.workflow import Asset, WorkflowRun

router = APIRouter(prefix="/operating-system", tags=["operating-system"])


class OperatingMetric(BaseModel):
    label: str
    value: str
    delta: str | None = None
    tone: str = "neutral"


class OperatingSystemOverview(BaseModel):
    metrics: list[OperatingMetric]
    systems: list[dict[str, Any]]
    council: list[dict[str, Any]]
    intelligence_layers: list[dict[str, Any]]
    action_feed: list[dict[str, Any]]
    event_triggers: list[dict[str, Any]]
    automation_coverage: dict[str, Any]


class OperatingSystemBootstrapRequest(BaseModel):
    workspace_id: UUID | None = Field(default=None, description="Workspace to initialize")


class OperatingSystemBootstrapResponse(BaseModel):
    ok: bool
    workspace_id: UUID
    created: dict[str, int]
    existing: dict[str, int]
    agents: list[str]
    triggers: list[str]
    schedules: list[str]


COUNCIL = [
    ("Chief Marketing Officer", "Revenue strategy, allocation, and executive decisions"),
    ("Creative Director", "Visual direction, brand consistency, and creative quality"),
    ("Brand Strategist", "Positioning, audience clarity, and market narrative"),
    ("Performance Marketer", "ROAS, CAC, bidding, and channel optimization"),
    ("Lifecycle Marketer", "Email, SMS, cohorts, and retention moments"),
    ("Retention Manager", "Churn signals, winback plays, and loyalty levers"),
    ("SEO Strategist", "Search demand, content clusters, and technical visibility"),
    ("Research Analyst", "Market, category, and competitor monitoring"),
    ("Revenue Analyst", "Margin, LTV, offer economics, and forecast deltas"),
    ("CRO Specialist", "Landing pages, checkout, and conversion experiments"),
    ("Customer Insights Analyst", "Reviews, surveys, cohorts, and behavior signals"),
    ("Competitor Analyst", "Pricing, messaging, launches, and offer tracking"),
    ("Campaign Operator", "Execution, QA, launch readiness, and channel operations"),
    ("Packaging Designer", "Packaging systems, dielines, inserts, and shelf impact"),
    ("UI/UX Designer", "Web experiences, product flows, and design systems"),
]

DEFAULT_TRIGGERS = [
    {
        "name": "ROAS Recovery",
        "event_kind": "roas_dropped",
        "workflow": "executive_council",
        "filter": {"roas": {"lt": 2.0}},
        "inputs_template": {"event": "roas_dropped", "priority": "high"},
        "debounce_s": 3600,
    },
    {
        "name": "CTR Recovery",
        "event_kind": "ctr_dropped",
        "workflow": "executive_council",
        "filter": {"ctr": {"lt": 1.2}},
        "inputs_template": {"event": "ctr_dropped", "priority": "high"},
        "debounce_s": 3600,
    },
    {
        "name": "Creative Fatigue Response",
        "event_kind": "campaign_fatigue_detected",
        "workflow": "executive_council",
        "filter": {"fatigue_score": {"gt": 0.7}},
        "inputs_template": {"event": "campaign_fatigue_detected", "priority": "high"},
        "debounce_s": 7200,
    },
    {
        "name": "Retention Decline Review",
        "event_kind": "retention_declined",
        "workflow": "executive_council",
        "filter": {"retention_delta": {"lt": -0.05}},
        "inputs_template": {"event": "retention_declined", "priority": "medium"},
        "debounce_s": 86400,
    },
    {
        "name": "Competitor Move Review",
        "event_kind": "competitor_campaign_detected",
        "workflow": "executive_council",
        "filter": {},
        "inputs_template": {"event": "competitor_campaign_detected", "priority": "medium"},
        "debounce_s": 21600,
    },
    {
        "name": "Revenue Spike Analysis",
        "event_kind": "revenue_spike_detected",
        "workflow": "executive_council",
        "filter": {"revenue_delta": {"gt": 0.2}},
        "inputs_template": {"event": "revenue_spike_detected", "priority": "medium"},
        "debounce_s": 21600,
    },
]

DEFAULT_SCHEDULES = [
    {
        "name": "Daily Growth Review",
        "workflow": "executive_council",
        "cron": "0 9 * * *",
        "inputs": {"event": "daily_growth_review", "priority": "medium"},
    },
    {
        "name": "Creative Fatigue Scan",
        "workflow": "executive_council",
        "cron": "0 */6 * * *",
        "inputs": {"event": "creative_fatigue_scan", "priority": "medium"},
    },
    {
        "name": "Weekly Executive Strategy",
        "workflow": "executive_council",
        "cron": "0 10 * * MON",
        "inputs": {"event": "weekly_executive_strategy", "priority": "high"},
    },
]

INTELLIGENCE_LAYERS = [
    ("Campaign Intelligence", "Campaign health, channel signals, and budget movement"),
    ("Creative Intelligence", "Taste scoring, fatigue detection, and visual memory"),
    ("Revenue Intelligence", "ROAS, CAC, LTV, margin, and offer performance"),
    ("Customer Intelligence", "Segments, retention, surveys, reviews, and purchase behavior"),
    ("Competitor Intelligence", "Competitor campaigns, pricing, messaging, and trend shifts"),
    ("Experimentation", "A/B tests, winner selection, confidence, and rollout control"),
    ("Memory Graph", "Persistent learning across campaigns, assets, offers, and audiences"),
    ("Tool Execution", "Browser operations, connected apps, retries, screenshots, and replay"),
]


async def _count(db: AsyncSession, model: Any, workspace_ids: list[Any]) -> int:
    if not workspace_ids:
        return 0
    column = getattr(model, "workspace_id", None)
    if column is None:
        return 0
    result = await db.execute(
        select(func.count()).select_from(model).where(column.in_(workspace_ids))
    )
    return int(result.scalar_one() or 0)


async def _recent_runs(db: AsyncSession, workspace_ids: list[Any]) -> list[WorkflowRun]:
    if not workspace_ids:
        return []
    result = await db.execute(
        select(WorkflowRun)
        .where(WorkflowRun.workspace_id.in_(workspace_ids))
        .order_by(WorkflowRun.created_at.desc())
        .limit(8)
    )
    return list(result.scalars().all())


async def _recent_triggers(db: AsyncSession, workspace_ids: list[Any]) -> list[Trigger]:
    if not workspace_ids:
        return []
    result = await db.execute(
        select(Trigger)
        .where(Trigger.workspace_id.in_(workspace_ids))
        .order_by(Trigger.updated_at.desc())
        .limit(6)
    )
    return list(result.scalars().all())


async def _ensure_agent(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    user_id: UUID | None,
    name: str,
    mandate: str,
) -> tuple[AgentSession, bool]:
    agent_key = name.lower().replace("/", "").replace(" ", "_")
    result = await db.execute(
        select(AgentSession).where(
            AgentSession.workspace_id == workspace_id,
            AgentSession.agent == agent_key,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing, False

    session = AgentSession(
        workspace_id=workspace_id,
        created_by=user_id,
        agent=agent_key,
        name=name,
        description=mandate,
        status="active",
        mode="autonomous",
        goal=f"Continuously monitor and improve {mandate.lower()}.",
        config={
            "autonomy": "supervised",
            "approval_required_for": ["budget_change", "external_publish", "destructive_action"],
            "operating_scope": ["strategy", "creative", "performance", "experimentation"],
        },
        memory={"mandate": mandate, "initialized_by": "helix"},
        heartbeat_interval_s=300,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session, True


async def _ensure_trigger(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    user_id: UUID | None,
    spec: dict[str, Any],
) -> tuple[Trigger, bool]:
    result = await db.execute(
        select(Trigger).where(
            Trigger.workspace_id == workspace_id,
            Trigger.name == spec["name"],
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing, False

    trigger = Trigger(
        workspace_id=workspace_id,
        created_by=user_id,
        name=spec["name"],
        source="event",
        event_kind=spec["event_kind"],
        filter=spec["filter"],
        workflow=spec["workflow"],
        inputs_template=spec["inputs_template"],
        config={"approval_mode": "supervised"},
        enabled=True,
        debounce_s=spec["debounce_s"],
    )
    db.add(trigger)
    await db.flush()
    await db.refresh(trigger)
    return trigger, True


async def _ensure_schedule(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    user_id: UUID | None,
    spec: dict[str, Any],
) -> tuple[ScheduledJob, bool]:
    result = await db.execute(
        select(ScheduledJob).where(
            ScheduledJob.workspace_id == workspace_id,
            ScheduledJob.name == spec["name"],
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing, False

    job = ScheduledJob(
        workspace_id=workspace_id,
        created_by=user_id,
        name=spec["name"],
        workflow=spec["workflow"],
        cron=spec["cron"],
        timezone="UTC",
        inputs=spec["inputs"],
        config={"approval_mode": "supervised"},
        enabled=True,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job, True


@router.get("/overview", response_model=OperatingSystemOverview)
async def overview(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> OperatingSystemOverview:
    """Return the unified Helix command-center state for the current user."""
    workspace_ids = await list_user_workspace_ids(db, user)

    active_agents = await _count(db, AgentSession, workspace_ids)
    schedules = await _count(db, ScheduledJob, workspace_ids)
    triggers = await _count(db, Trigger, workspace_ids)
    brands = await _count(db, Brand, workspace_ids)
    assets = await _count(db, Asset, workspace_ids)
    memories = await _count(db, MemoryEntry, workspace_ids)
    runs = await _count(db, WorkflowRun, workspace_ids)
    skills_result = await db.execute(select(func.count()).select_from(SkillRegistry))
    skills = int(skills_result.scalar_one() or 0)
    recent_runs = await _recent_runs(db, workspace_ids)
    recent_triggers = await _recent_triggers(db, workspace_ids)

    running = sum(1 for r in recent_runs if r.status in {"queued", "pending", "running"})
    succeeded = sum(1 for r in recent_runs if r.status in {"completed", "succeeded"})
    failed = sum(1 for r in recent_runs if r.status in {"failed", "error"})

    systems = [
        {
            "name": "AI CMO Brain",
            "status": "active" if active_agents else "ready",
            "description": "Coordinates goals, budgets, priorities, and executive decisions.",
        },
        {
            "name": "Executive Agent Council",
            "status": "active" if active_agents else "ready",
            "description": "Debates strategy, assigns work, votes on plans, and escalates risk.",
        },
        {
            "name": "Workflow Orchestration",
            "status": "active" if runs else "ready",
            "description": "Runs durable, resumable execution plans with checkpoints and retries.",
        },
        {
            "name": "Browser Automation",
            "status": "ready",
            "description": "Operates connected tools, captures evidence, and preserves execution replay.",
        },
        {
            "name": "Creative Intelligence",
            "status": "learning" if assets else "ready",
            "description": "Scores visual quality, detects fatigue, and remembers winning styles.",
        },
        {
            "name": "Performance Memory Graph",
            "status": "learning" if memories else "ready",
            "description": "Persists campaign, creative, customer, offer, and experiment learnings.",
        },
    ]

    action_feed = [
        {
            "id": str(run.id),
            "title": (run.workflow or "workflow").replace("_", " ").title(),
            "status": run.status,
            "timestamp": run.created_at.isoformat() if run.created_at else None,
            "detail": run.current_node or run.error or "Execution recorded",
        }
        for run in recent_runs
    ]

    event_triggers = [
        {
            "id": str(trigger.id),
            "name": trigger.name,
            "event_kind": trigger.event_kind,
            "workflow": trigger.workflow,
            "enabled": trigger.enabled,
            "fire_count": trigger.fire_count,
            "last_fired_at": trigger.last_fired_at.isoformat()
            if trigger.last_fired_at
            else None,
        }
        for trigger in recent_triggers
    ]

    return OperatingSystemOverview(
        metrics=[
            OperatingMetric(label="Revenue Control", value="Live", delta="Goal-aware", tone="success"),
            OperatingMetric(label="Active Agents", value=str(active_agents), delta="Persistent workforce", tone="info"),
            OperatingMetric(label="Autonomous Triggers", value=str(triggers), delta="Event-driven", tone="warning"),
            OperatingMetric(label="Memory Signals", value=str(memories), delta="Learning graph", tone="success"),
            OperatingMetric(label="Generated Assets", value=str(assets), delta="Creative library", tone="info"),
            OperatingMetric(label="Workflow Runs", value=str(runs), delta=f"{running} active · {succeeded} won · {failed} failed", tone="neutral"),
        ],
        systems=systems,
        council=[
            {
                "name": name,
                "mandate": mandate,
                "status": "active" if active_agents else "ready",
            }
            for name, mandate in COUNCIL
        ],
        intelligence_layers=[
            {
                "name": name,
                "description": description,
                "status": "learning" if memories or assets else "ready",
            }
            for name, description in INTELLIGENCE_LAYERS
        ],
        action_feed=action_feed,
        event_triggers=event_triggers,
        automation_coverage={
            "brands": brands,
            "skills": skills,
            "scheduled_jobs": schedules,
            "triggers": triggers,
            "workflows": runs,
            "assets": assets,
            "memory_entries": memories,
        },
    )


@router.post("/bootstrap", response_model=OperatingSystemBootstrapResponse)
async def bootstrap_operating_system(
    payload: OperatingSystemBootstrapRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> OperatingSystemBootstrapResponse:
    """Initialize the persistent Helix workforce and default autonomy rules."""
    if payload.workspace_id is not None:
        workspace = await assert_workspace_access(db, user, payload.workspace_id)
    else:
        workspace = await get_default_workspace_for_user(db, user)

    created = {"agents": 0, "triggers": 0, "schedules": 0}
    existing = {"agents": 0, "triggers": 0, "schedules": 0}
    agent_names: list[str] = []
    trigger_names: list[str] = []
    schedule_names: list[str] = []

    for name, mandate in COUNCIL:
        _, was_created = await _ensure_agent(
            db,
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            mandate=mandate,
        )
        if was_created:
            created["agents"] += 1
        else:
            existing["agents"] += 1
        agent_names.append(name)

    for spec in DEFAULT_TRIGGERS:
        _, was_created = await _ensure_trigger(
            db,
            workspace_id=workspace.id,
            user_id=user.id,
            spec=spec,
        )
        created["triggers"] += 1 if was_created else 0
        existing["triggers"] += 0 if was_created else 1
        trigger_names.append(spec["name"])

    for spec in DEFAULT_SCHEDULES:
        _, was_created = await _ensure_schedule(
            db,
            workspace_id=workspace.id,
            user_id=user.id,
            spec=spec,
        )
        created["schedules"] += 1 if was_created else 0
        existing["schedules"] += 0 if was_created else 1
        schedule_names.append(spec["name"])

    await db.commit()

    return OperatingSystemBootstrapResponse(
        ok=True,
        workspace_id=workspace.id,
        created=created,
        existing=existing,
        agents=agent_names,
        triggers=trigger_names,
        schedules=schedule_names,
    )
