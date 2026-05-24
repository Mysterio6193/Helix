"""Intelligence API — revenue, customer, competitor, campaign insights."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.acl import list_user_workspace_ids
from helix.core.db import get_db
from helix.core.sessions import require_user
from helix.intelligence.actions import ActionExecutor, ApprovalQueue
from helix.intelligence.analysis import (
    calculate_rfm,
    detect_anomaly,
    simple_forecast,
)
from helix.intelligence.campaign import CampaignIntelligence, CreativeIntelligence
from helix.intelligence.experiments import ExperimentEngine
from helix.intelligence.rules_engine import RulesEngine
from helix.intelligence.suggestions import generate_suggestions
from helix.models.intelligence import (
    CompetitorSnapshot,
    CustomerSegment,
    Experiment,
    IntelligenceSignal,
    PerformanceSnapshot,
)
from helix.models.organization import User
from helix.services.ws_manager import manager as ws_manager

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


# ─── Schemas ──────────────────────────────────────────────────────────

class RevenueOverview(BaseModel):
    current_revenue: dict[str, Any]
    roas: dict[str, Any]
    cac: dict[str, Any]
    ltv: dict[str, Any]
    margin: dict[str, Any]
    anomalies: list[dict[str, Any]]
    predictions: dict[str, Any]
    by_channel: list[dict[str, Any]]


class MetricSeries(BaseModel):
    metric_type: str
    platform: str
    data: list[dict[str, Any]]


class CustomerSegmentsResponse(BaseModel):
    segments: list[dict[str, Any]]
    cohorts: dict[str, Any]
    rfm_distribution: dict[str, int]


class CompetitorListResponse(BaseModel):
    competitors: list[dict[str, Any]]
    alerts: list[dict[str, Any]]


class SignalListResponse(BaseModel):
    signals: list[dict[str, Any]]
    unread_count: int


# ─── Revenue Intelligence ─────────────────────────────────────────────

@router.get("/revenue/overview", response_model=RevenueOverview)
async def revenue_overview(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> RevenueOverview:
    """Return aggregated revenue metrics and predictions."""
    workspace_ids = await list_user_workspace_ids(db, user)

    if not workspace_ids:
        return RevenueOverview(
            current_revenue={"daily": 0, "weekly": 0, "monthly": 0, "yoy_change": 0},
            roas={"current": 0, "target": 2.5, "trend": "stable"},
            cac={"current": 0, "trend": "stable", "by_channel": []},
            ltv={"current": 0, "predicted_12m": 0},
            margin={"gross": 0, "net": 0},
            anomalies=[],
            predictions={"next_30_days": [], "confidence": 0},
            by_channel=[],
        )

    # Fetch last 90 days of revenue data
    cutoff = datetime.utcnow() - timedelta(days=90)

    result = await db.execute(
        select(PerformanceSnapshot)
        .where(
            PerformanceSnapshot.workspace_id.in_(workspace_ids),
            PerformanceSnapshot.metric_type.in_(["revenue", "roas", "ctr", "cac", "spend"]),
            PerformanceSnapshot.captured_at >= cutoff,
        )
        .order_by(PerformanceSnapshot.captured_at)
    )
    snapshots = result.scalars().all()

    # Aggregate by metric
    by_metric: dict[str, list[float]] = {}
    by_date: dict[str, dict[str, float]] = {}
    by_platform: dict[str, list[float]] = {}

    for snap in snapshots:
        key = snap.metric_type
        by_metric.setdefault(key, []).append(snap.value)

        date_key = snap.captured_at.strftime("%Y-%m-%d") if snap.captured_at else ""
        by_date.setdefault(date_key, {})[key] = snap.value

        plat_key = f"{snap.platform}_{key}"
        by_platform.setdefault(plat_key, []).append(snap.value)

    # Calculate aggregates
    daily = sum(v.get("revenue", 0) for v in by_date.values() if v.get("revenue")) / max(len(by_date), 1)
    weekly = daily * 7
    monthly = daily * 30

    roas_values = by_metric.get("roas", [])
    current_roas = roas_values[-1] if roas_values else 0

    # Detect anomalies
    revenue_values = [v.get("revenue", 0) for v in by_date.values() if v.get("revenue")]
    anomaly_indices = detect_anomaly(revenue_values) if len(revenue_values) > 7 else []
    anomalies = []
    dates = list(by_date.keys())
    for idx in anomaly_indices:
        if idx < len(dates):
            anomalies.append({
                "date": dates[idx],
                "metric": "revenue",
                "value": revenue_values[idx],
                "severity": "warning",
            })

    # Simple forecast
    forecast = simple_forecast(revenue_values, 30) if revenue_values else []

    # By channel
    channels = []
    for platform in ["meta_ads", "shopify", "stripe"]:
        spend = sum(by_platform.get(f"{platform}_spend", []))
        rev = sum(by_platform.get(f"{platform}_revenue", []))
        if spend > 0 or rev > 0:
            channels.append({
                "platform": platform,
                "spend": round(spend, 2),
                "revenue": round(rev, 2),
                "roas": round(rev / max(spend, 1), 2),
            })

    return RevenueOverview(
        current_revenue={"daily": round(daily, 2), "weekly": round(weekly, 2), "monthly": round(monthly, 2), "yoy_change": 0},
        roas={"current": round(current_roas, 2), "target": 2.5, "trend": "stable" if len(roas_values) < 7 else ("up" if roas_values[-1] > roas_values[-7] else "down")},
        cac={"current": 0, "trend": "stable", "by_channel": []},
        ltv={"current": 0, "predicted_12m": 0},
        margin={"gross": 0, "net": 0},
        anomalies=anomalies,
        predictions={"next_30_days": [round(v, 2) for v in forecast], "confidence": 0.7 if len(revenue_values) > 14 else 0.4},
        by_channel=channels,
    )


@router.get("/revenue/metrics")
async def revenue_metrics(
    platform: str | None = None,
    metric_type: str | None = None,
    days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return time-series metrics."""
    workspace_ids = await list_user_workspace_ids(db, user)
    if not workspace_ids:
        return []

    cutoff = datetime.utcnow() - timedelta(days=days)

    query = select(PerformanceSnapshot).where(
        PerformanceSnapshot.workspace_id.in_(workspace_ids),
        PerformanceSnapshot.captured_at >= cutoff,
    )

    if platform:
        query = query.where(PerformanceSnapshot.platform == platform)
    if metric_type:
        query = query.where(PerformanceSnapshot.metric_type == metric_type)

    query = query.order_by(PerformanceSnapshot.captured_at)
    result = await db.execute(query)

    return [
        {
            "platform": s.platform,
            "metric_type": s.metric_type,
            "value": s.value,
            "currency": s.currency,
            "captured_at": s.captured_at.isoformat() if s.captured_at else None,
        }
        for s in result.scalars().all()
    ]


# ─── Customer Intelligence ────────────────────────────────────────────

@router.get("/customers/segments", response_model=CustomerSegmentsResponse)
async def customer_segments(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> CustomerSegmentsResponse:
    """Return customer segments and cohort analysis."""
    workspace_ids = await list_user_workspace_ids(db, user)

    result = await db.execute(
        select(CustomerSegment)
        .where(CustomerSegment.workspace_id.in_(workspace_ids))
        .order_by(CustomerSegment.member_count.desc())
    )
    segments = result.scalars().all()

    segment_data = []
    rfm_dist: dict[str, int] = {}

    for seg in segments:
        segment_data.append({
            "id": str(seg.id),
            "key": seg.segment_key,
            "name": seg.name,
            "count": seg.member_count,
            "avg_ltv": seg.avg_ltv,
            "avg_order_value": seg.avg_order_value,
            "churn_rate": seg.churn_rate,
            "retention_curve": seg.retention_curve,
        })
        rfm_dist[seg.segment_key] = seg.member_count

    return CustomerSegmentsResponse(
        segments=segment_data,
        cohorts={},
        rfm_distribution=rfm_dist,
    )


@router.post("/customers/compute-segments")
async def compute_customer_segments(
    brand_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Compute customer segments from order data."""
    # Fetch performance snapshots as mock order data
    result = await db.execute(
        select(PerformanceSnapshot)
        .where(
            PerformanceSnapshot.brand_id == brand_id,
            PerformanceSnapshot.platform == "shopify",
            PerformanceSnapshot.metric_type == "orders",
        )
        .order_by(PerformanceSnapshot.captured_at)
    )
    snapshots = result.scalars().all()

    # Create mock orders from snapshot data for RFM calculation
    orders = []
    for snap in snapshots:
        orders.append({
            "customer_id": f"customer_{snap.workspace_id}",
            "total_price": snap.value * 50,  # Mock value
            "created_at": snap.captured_at.isoformat() if snap.captured_at else datetime.utcnow().isoformat(),
        })

    rfm = calculate_rfm(orders)

    # Aggregate into segments
    segment_counts: dict[str, int] = {}
    for customer in rfm.values():
        seg = customer["segment"]
        segment_counts[seg] = segment_counts.get(seg, 0) + 1

    return {
        "total_customers": len(rfm),
        "segments": segment_counts,
        "sample_customers": list(rfm.values())[:5],
    }


# ─── Competitor Intelligence ──────────────────────────────────────────

@router.get("/competitors", response_model=CompetitorListResponse)
async def list_competitors(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> CompetitorListResponse:
    """Return tracked competitors and recent alerts."""
    workspace_ids = await list_user_workspace_ids(db, user)

    # Get latest snapshot per competitor
    result = await db.execute(
        select(CompetitorSnapshot)
        .where(CompetitorSnapshot.workspace_id.in_(workspace_ids))
        .order_by(desc(CompetitorSnapshot.captured_at))
    )
    snapshots = result.scalars().all()

    seen = set()
    competitors = []
    alerts = []

    for snap in snapshots:
        key = f"{snap.workspace_id}:{snap.competitor_domain}"
        if key in seen:
            continue
        seen.add(key)

        competitors.append({
            "domain": snap.competitor_domain,
            "name": snap.competitor_name,
            "health_score": snap.health_score,
            "last_scraped": snap.captured_at.isoformat() if snap.captured_at else None,
            "snapshot_type": snap.snapshot_type,
            "data_summary": {k: str(v)[:100] for k, v in (snap.data or {}).items()},
        })

        if snap.change_detected:
            alerts.append({
                "competitor": snap.competitor_domain,
                "type": snap.snapshot_type,
                "captured_at": snap.captured_at.isoformat() if snap.captured_at else None,
            })

    return CompetitorListResponse(competitors=competitors, alerts=alerts)


@router.post("/competitors/track")
async def track_competitor(
    domain: str,
    name: str | None = None,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Start tracking a competitor."""
    workspace_ids = await list_user_workspace_ids(db, user)
    if not workspace_ids:
        return {"error": "No workspace available"}

    # Create initial snapshot placeholder
    snapshot = CompetitorSnapshot(
        workspace_id=workspace_ids[0],
        competitor_domain=domain,
        competitor_name=name or domain,
        snapshot_type="initial",
        data={},
        captured_at=datetime.utcnow(),
    )
    db.add(snapshot)
    await db.commit()

    return {"ok": True, "domain": domain, "workspace_id": str(workspace_ids[0])}


# ─── Signals ──────────────────────────────────────────────────────────

@router.get("/signals", response_model=SignalListResponse)
async def list_signals(
    layer: str | None = None,
    severity: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> SignalListResponse:
    """Return intelligence signals."""
    workspace_ids = await list_user_workspace_ids(db, user)

    query = select(IntelligenceSignal).where(
        IntelligenceSignal.workspace_id.in_(workspace_ids),
        IntelligenceSignal.dismissed_at.is_(None),
    )

    if layer:
        query = query.where(IntelligenceSignal.layer == layer)
    if severity:
        query = query.where(IntelligenceSignal.severity == severity)

    query = query.order_by(desc(IntelligenceSignal.created_at)).limit(limit)
    result = await db.execute(query)
    signals = result.scalars().all()

    unread = sum(1 for s in signals if not s.acknowledged_at)

    return SignalListResponse(
        signals=[
            {
                "id": str(s.id),
                "layer": s.layer,
                "type": s.signal_type,
                "severity": s.severity,
                "title": s.title,
                "description": s.description,
                "recommended_action": s.recommended_action,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in signals
        ],
        unread_count=unread,
    )


@router.post("/signals/{signal_id}/acknowledge")
async def acknowledge_signal(
    signal_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Acknowledge a signal."""
    result = await db.execute(
        select(IntelligenceSignal).where(IntelligenceSignal.id == signal_id)
    )
    signal = result.scalar_one_or_none()
    if not signal:
        return {"error": "Signal not found"}

    signal.acknowledged_at = datetime.utcnow()
    await db.commit()
    return {"ok": True}


@router.post("/signals/{signal_id}/dismiss")
async def dismiss_signal(
    signal_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Dismiss a signal."""
    result = await db.execute(
        select(IntelligenceSignal).where(IntelligenceSignal.id == signal_id)
    )
    signal = result.scalar_one_or_none()
    if not signal:
        return {"error": "Signal not found"}

    signal.dismissed_at = datetime.utcnow()
    await db.commit()
    return {"ok": True}


# ─── Experiments ──────────────────────────────────────────────────────

@router.get("/experiments")
async def list_experiments(
    status: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return A/B experiments."""
    workspace_ids = await list_user_workspace_ids(db, user)

    query = select(Experiment).where(Experiment.workspace_id.in_(workspace_ids))
    if status:
        query = query.where(Experiment.status == status)

    query = query.order_by(desc(Experiment.created_at)).limit(limit)
    result = await db.execute(query)

    return [
        {
            "id": str(e.id),
            "name": e.name,
            "hypothesis": e.hypothesis,
            "status": e.status,
            "experiment_type": e.experiment_type,
            "primary_metric": e.primary_metric,
            "traffic_allocation": e.traffic_allocation,
            "variants": e.variants,
            "control_variant_id": e.control_variant_id,
            "factors": e.factors,
            "winner": e.winner,
            "confidence": e.confidence,
            "uplift": e.uplift,
            "auto_stop": e.auto_stop,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "ended_at": e.ended_at.isoformat() if e.ended_at else None,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in result.scalars().all()
    ]


@router.post("/experiments")
async def create_experiment(
    payload: dict[str, Any],
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new experiment (A/B or multivariate)."""
    workspace_ids = await list_user_workspace_ids(db, user)
    if not workspace_ids:
        return {"error": "No workspace available"}

    experiment_type = payload.get("experiment_type", "ab")
    factors = payload.get("factors", {})

    variants = payload.get("variants", [])
    if not variants:
        if experiment_type == "mvt" and factors:
            variants = ExperimentEngine.generate_mvt_variants(factors)
        else:
            # Default A/B setup
            variants = [
                {"id": "control", "name": "Control", "traffic_pct": 50, "config": {}},
                {"id": "variant_b", "name": "Variant B", "traffic_pct": 50, "config": {}},
            ]

    exp = Experiment(
        workspace_id=workspace_ids[0],
        brand_id=payload.get("brand_id"),
        name=payload.get("name", "Untitled Experiment"),
        hypothesis=payload.get("hypothesis", ""),
        experiment_type=experiment_type,
        primary_metric=payload.get("primary_metric", "conversion_rate"),
        traffic_allocation=payload.get("traffic_allocation", 100),
        variants=variants,
        control_variant_id=payload.get("control_variant_id", variants[0]["id"]),
        factors=factors,
        min_confidence=payload.get("min_confidence", 0.95),
        min_sample_size=payload.get("min_sample_size", 100),
        auto_stop=payload.get("auto_stop", True),
        status="draft",
    )
    db.add(exp)
    await db.commit()
    await db.refresh(exp)

    try:
        await ws_manager.broadcast("experiments", "experiment.created", {
            "id": str(exp.id), "name": exp.name, "status": "draft",
            "experiment_type": experiment_type,
        })
    except Exception:
        pass

    exp_dict = {
        "id": str(exp.id), "ok": True, "experiment_type": experiment_type,
        "variants_count": len(variants),
    }
    if experiment_type == "mvt":
        exp_dict["factors"] = factors
    return exp_dict


@router.get("/experiments/{experiment_id}")
async def get_experiment(
    experiment_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get experiment details with current results."""
    engine = ExperimentEngine(db)
    results = await engine.get_experiment_results(experiment_id)
    return results


@router.post("/experiments/{experiment_id}/start")
async def start_experiment(
    experiment_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Start an experiment."""
    engine = ExperimentEngine(db)
    result = await engine.start_experiment(experiment_id)
    try:
        await ws_manager.broadcast("experiments", "experiment.started", result)
    except Exception:
        pass
    return result


@router.post("/experiments/{experiment_id}/stop")
async def stop_experiment(
    experiment_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Stop an experiment."""
    engine = ExperimentEngine(db)
    result = await engine.stop_experiment(experiment_id)
    try:
        await ws_manager.broadcast("experiments", "experiment.stopped", result)
    except Exception:
        pass
    return result


@router.post("/experiments/{experiment_id}/allocate")
async def allocate_variant(
    experiment_id: UUID,
    payload: dict[str, Any],
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Allocate a user to a variant."""
    engine = ExperimentEngine(db)
    return await engine.allocate_variant(
        experiment_id,
        session_id=payload.get("session_id"),
        user_id=payload.get("user_id"),
    )


@router.post("/experiments/{experiment_id}/events")
async def track_experiment_event(
    experiment_id: UUID,
    payload: dict[str, Any],
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Track an event for an experiment variant."""
    engine = ExperimentEngine(db)
    return await engine.track_event(
        experiment_id,
        variant_id=payload["variant_id"],
        event_type=payload["event_type"],
        value=payload.get("value"),
        session_id=payload.get("session_id"),
        user_id=payload.get("user_id"),
        source=payload.get("source"),
        metadata=payload.get("metadata"),
    )


# ─── AI Experiment Suggestions ─────────────────────────────────────────

@router.post("/experiments/suggest")
async def suggest_experiments(
    brand_id: UUID | None = None,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Generate AI experiment suggestions from intelligence signals and past experiments."""
    ws_ids = await list_user_workspace_ids(db, user)
    if not ws_ids:
        return []
    suggestions = await generate_suggestions(db, user, ws_ids[0], brand_id)
    return suggestions


# ─── Optimization Engine ──────────────────────────────────────────────

@router.get("/optimization/rules")
async def list_optimization_rules(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return all optimization rules with their current status."""
    engine = RulesEngine(db)
    rules = []
    for rule in engine.rules:
        rules.append({
            "rule_id": rule.rule_id,
            "name": rule.name,
            "description": rule.description,
            "severity": rule.severity,
            "cooldown_hours": rule.cooldown_hours,
            "approval_required": rule.approval_required,
            "conditions_count": len(rule.conditions),
            "actions_count": len(rule.actions),
        })
    return rules


@router.post("/optimization/evaluate")
async def evaluate_optimization_rules(
    brand_id: UUID | None = None,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Evaluate all optimization rules and return triggered actions."""
    workspace_ids = await list_user_workspace_ids(db, user)
    if not workspace_ids:
        return {"triggered": [], "executed": [], "pending_approval": []}

    engine = RulesEngine(db)
    triggered = await engine.evaluate_all_rules(workspace_ids[0], brand_id)

    executed = []
    pending_approval = []

    for trigger in triggered:
        if trigger["approval_required"]:
            # Create approval request
            queue = ApprovalQueue(db)
            approval = await queue.create_approval_request(
                workspace_ids[0],
                trigger["rule_id"],
                trigger["rule_name"],
                trigger["actions"],
                trigger["context"],
            )
            pending_approval.append(approval)
        else:
            # Execute immediately
            executor = ActionExecutor(db)
            results = await executor.execute_actions(
                trigger["actions"],
                workspace_ids[0],
                brand_id,
                trigger["context"],
            )
            executed.append({
                "rule_id": trigger["rule_id"],
                "rule_name": trigger["rule_name"],
                "results": results,
            })

    await db.commit()

    return {
        "triggered": len(triggered),
        "executed": executed,
        "pending_approval": pending_approval,
    }


@router.get("/optimization/approvals")
async def list_pending_approvals(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List pending approval requests."""
    workspace_ids = await list_user_workspace_ids(db, user)
    if not workspace_ids:
        return []

    queue = ApprovalQueue(db)
    return await queue.list_pending_approvals(workspace_ids[0])


@router.post("/optimization/approvals/{approval_id}/approve")
async def approve_optimization(
    approval_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Approve a pending optimization action."""
    queue = ApprovalQueue(db)
    result = await queue.approve_action(approval_id)
    return result


@router.post("/optimization/approvals/{approval_id}/reject")
async def reject_optimization(
    approval_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Reject a pending optimization action."""
    queue = ApprovalQueue(db)
    result = await queue.reject_action(approval_id)
    return result


@router.get("/optimization/history")
async def optimization_history(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return history of executed optimization actions."""
    workspace_ids = await list_user_workspace_ids(db, user)

    result = await db.execute(
        select(IntelligenceSignal)
        .where(
            IntelligenceSignal.workspace_id.in_(workspace_ids),
            IntelligenceSignal.signal_type == "auto_action",
        )
        .order_by(desc(IntelligenceSignal.created_at))
        .limit(limit)
    )
    signals = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "title": s.title,
            "description": s.description,
            "severity": s.severity,
            "layer": s.layer,
            "source_data": s.source_data,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in signals
    ]


# ─── Campaign Intelligence ────────────────────────────────────────────

@router.get("/campaigns/health")
async def campaign_health(
    brand_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return campaign health score and issues."""
    workspace_ids = await list_user_workspace_ids(db, user)
    if not workspace_ids:
        return {"score": 0, "issues": [], "status": "no_data"}

    intel = CampaignIntelligence(db)
    return await intel.analyze_campaign_health(workspace_ids[0], brand_id)


@router.get("/campaigns/fatigue")
async def creative_fatigue(
    brand_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return creative fatigue signals."""
    workspace_ids = await list_user_workspace_ids(db, user)
    if not workspace_ids:
        return []

    intel = CampaignIntelligence(db)
    return await intel.detect_creative_fatigue(workspace_ids[0], brand_id)


@router.get("/campaigns/optimize")
async def optimization_signals(
    brand_id: UUID,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return actionable optimization signals."""
    workspace_ids = await list_user_workspace_ids(db, user)
    if not workspace_ids:
        return []

    intel = CreativeIntelligence(db)
    signals = await intel.generate_optimization_signals(workspace_ids[0], brand_id)

    # Store signals in database
    for signal_data in signals:
        signal = IntelligenceSignal(
            workspace_id=workspace_ids[0],
            brand_id=brand_id,
            layer=signal_data["layer"],
            signal_type=signal_data["signal_type"],
            severity=signal_data["severity"],
            title=signal_data["title"],
            description=signal_data["description"],
            source_data={},
            recommended_action=signal_data.get("recommended_action"),
            auto_triggered=True,
        )
        db.add(signal)

    await db.commit()

    try:
        for signal_data in signals:
            await ws_manager.broadcast("intelligence", "signal.new", {
                "title": signal_data.get("title", ""),
                "severity": signal_data.get("severity", "info"),
                "layer": signal_data.get("layer", ""),
            })
    except Exception:
        pass

    return signals
