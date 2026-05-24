"""Optimization rules engine — defines when and how Helix takes autonomous action."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.logging import get_logger
from helix.models.intelligence import (
    IntelligenceSignal,
    PerformanceSnapshot,
)

log = get_logger(__name__)


class OptimizationRule:
    """A single optimization rule with conditions and actions."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        conditions: list[dict[str, Any]],
        actions: list[dict[str, Any]],
        severity: str = "medium",
        cooldown_hours: int = 24,
        approval_required: bool = False,
    ):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.conditions = conditions
        self.actions = actions
        self.severity = severity
        self.cooldown_hours = cooldown_hours
        self.approval_required = approval_required


# Default optimization rules
DEFAULT_RULES = [
    OptimizationRule(
        rule_id="roas_recovery",
        name="ROAS Recovery",
        description="When ROAS drops below target, reduce spend on underperformers",
        conditions=[
            {"metric": "roas", "operator": "lt", "value": 2.0, "platform": "meta_ads", "window_hours": 24},
        ],
        actions=[
            {"type": "reduce_budget", "target": "worst_performing_adset", "amount": 0.3},
            {"type": "generate_signal", "layer": "campaign", "severity": "critical", "title": "Auto-reduced budget on low ROAS ad set"},
        ],
        severity="critical",
        cooldown_hours=12,
        approval_required=False,
    ),
    OptimizationRule(
        rule_id="ctr_fatigue",
        name="CTR Fatigue Response",
        description="When CTR drops significantly, pause and refresh creative",
        conditions=[
            {"metric": "ctr", "operator": "decline_pct", "value": 25, "platform": "meta_ads", "window_hours": 168},
        ],
        actions=[
            {"type": "pause_adset", "target": "fatigued_adset"},
            {"type": "generate_variants", "count": 3, "style": "auto"},
            {"type": "generate_signal", "layer": "creative", "severity": "warning", "title": "Auto-paused fatigued ad set and queued new variants"},
        ],
        severity="high",
        cooldown_hours=24,
        approval_required=True,
    ),
    OptimizationRule(
        rule_id="budget_rebalance",
        name="Budget Rebalancing",
        description="Shift budget from low-ROAS to high-ROAS channels",
        conditions=[
            {"metric": "roas_variance", "operator": "gt", "value": 1.0, "window_hours": 72},
        ],
        actions=[
            {"type": "reallocate_budget", "from": "lowest_roas", "to": "highest_roas", "amount": 0.2},
            {"type": "generate_signal", "layer": "revenue", "severity": "info", "title": "Auto-reallocated budget to higher-performing channel"},
        ],
        severity="medium",
        cooldown_hours=48,
        approval_required=False,
    ),
    OptimizationRule(
        rule_id="winning_variant_scale",
        name="Scale Winning Variant",
        description="When an experiment variant wins with 95% confidence, scale it",
        conditions=[
            {"metric": "experiment_confidence", "operator": "gt", "value": 0.95, "window_hours": 0},
        ],
        actions=[
            {"type": "scale_variant", "target": "winner", "amount": 2.0},
            {"type": "generate_signal", "layer": "experimentation", "severity": "success", "title": "Auto-scaled winning experiment variant"},
        ],
        severity="info",
        cooldown_hours=72,
        approval_required=False,
    ),
    OptimizationRule(
        rule_id="churn_rescue",
        name="Churn Rescue",
        description="When at-risk customer segment grows, trigger winback campaign",
        conditions=[
            {"metric": "churn_rate", "operator": "gt", "value": 0.5, "segment": "at_risk", "window_hours": 168},
        ],
        actions=[
            {"type": "launch_workflow", "workflow": "winback_campaign", "target": "at_risk_segment"},
            {"type": "generate_signal", "layer": "customer", "severity": "warning", "title": "Auto-launched winback campaign for at-risk segment"},
        ],
        severity="high",
        cooldown_hours=168,
        approval_required=True,
    ),
    OptimizationRule(
        rule_id="meta_ads_refresh",
        name="Meta Ads Creative Refresh",
        description="When creative fatigue is detected, auto-refresh Meta Ads",
        conditions=[
            {"metric": "ctr", "operator": "decline_pct", "value": 30, "platform": "meta_ads", "window_hours": 72},
        ],
        actions=[
            {"type": "browser_automation", "target_site": "meta_ads", "action": "pause_adset", "config": {"target": "fatigued_adset"}},
            {"type": "generate_variants", "count": 3, "style": "auto"},
            {"type": "browser_automation", "target_site": "meta_ads", "action": "create_campaign", "config": {"budget": 50}},
            {"type": "generate_signal", "layer": "campaign", "severity": "warning", "title": "Auto-refreshed Meta Ads creative and launched new campaign"},
        ],
        severity="high",
        cooldown_hours=48,
        approval_required=True,
    ),
    OptimizationRule(
        rule_id="shopify_price_update",
        name="Shopify Price Optimization",
        description="When competitor price drops, update Shopify pricing",
        conditions=[
            {"metric": "competitor_price_change", "operator": "detected", "value": 1, "window_hours": 24},
        ],
        actions=[
            {"type": "browser_automation", "target_site": "shopify", "action": "edit_product", "config": {"price_adjustment": -0.05}},
            {"type": "generate_signal", "layer": "competitor", "severity": "info", "title": "Auto-adjusted Shopify pricing based on competitor change"},
        ],
        severity="medium",
        cooldown_hours=72,
        approval_required=True,
    ),
]


class RulesEngine:
    """Evaluate optimization rules against current data."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rules = DEFAULT_RULES

    async def evaluate_all_rules(
        self,
        workspace_id: UUID,
        brand_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        """Evaluate all rules and return triggered actions."""
        triggered = []

        for rule in self.rules:
            try:
                result = await self._evaluate_rule(rule, workspace_id, brand_id)
                if result["triggered"]:
                    triggered.append({
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "severity": rule.severity,
                        "approval_required": rule.approval_required,
                        "actions": rule.actions,
                        "context": result.get("context", {}),
                    })
            except Exception as e:
                log.error("rule_evaluation_failed", rule=rule.rule_id, error=str(e))

        return triggered

    async def _evaluate_rule(
        self,
        rule: OptimizationRule,
        workspace_id: UUID,
        brand_id: UUID | None,
    ) -> dict[str, Any]:
        """Evaluate a single rule's conditions."""
        all_conditions_met = True
        context = {}

        for condition in rule.conditions:
            met, ctx = await self._evaluate_condition(condition, workspace_id, brand_id)
            if not met:
                all_conditions_met = False
                break
            context.update(ctx)

        # Check cooldown
        if all_conditions_met:
            last_triggered = await self._get_last_trigger(rule.rule_id, workspace_id)
            if last_triggered:
                cooldown = timedelta(hours=rule.cooldown_hours)
                if datetime.utcnow() - last_triggered < cooldown:
                    all_conditions_met = False
                    context["cooldown_active"] = True

        return {"triggered": all_conditions_met, "context": context}

    async def _evaluate_condition(
        self,
        condition: dict[str, Any],
        workspace_id: UUID,
        brand_id: UUID | None,
    ) -> tuple[bool, dict[str, Any]]:
        """Evaluate a single condition."""
        metric = condition["metric"]
        operator = condition["operator"]
        value = condition["value"]
        window_hours = condition.get("window_hours", 24)
        platform = condition.get("platform")
        condition.get("segment")

        cutoff = datetime.utcnow() - timedelta(hours=window_hours)

        if metric == "experiment_confidence":
            # Check experiments
            from helix.models.intelligence import Experiment
            result = await self.db.execute(
                select(Experiment)
                .where(
                    Experiment.workspace_id == workspace_id,
                    Experiment.status == "running",
                    Experiment.confidence >= value,
                )
                .order_by(desc(Experiment.updated_at))
                .limit(1)
            )
            exp = result.scalar_one_or_none()
            if exp:
                return True, {"experiment_id": str(exp.id), "confidence": exp.confidence}
            return False, {}

        # Fetch performance data
        query = select(PerformanceSnapshot).where(
            PerformanceSnapshot.workspace_id == workspace_id,
            PerformanceSnapshot.metric_type == metric,
            PerformanceSnapshot.captured_at >= cutoff,
        )

        if platform:
            query = query.where(PerformanceSnapshot.platform == platform)
        if brand_id:
            query = query.where(PerformanceSnapshot.brand_id == brand_id)

        query = query.order_by(PerformanceSnapshot.captured_at)
        result = await self.db.execute(query)
        snapshots = result.scalars().all()

        if not snapshots:
            return False, {}

        values = [s.value for s in snapshots]
        current = values[-1]

        if operator == "lt":
            return current < value, {"current": current, "threshold": value}
        elif operator == "gt":
            return current > value, {"current": current, "threshold": value}
        elif operator == "decline_pct":
            if len(values) < 2:
                return False, {}
            previous = values[0]
            if previous <= 0:
                return False, {}
            decline = ((previous - current) / previous) * 100
            return decline >= value, {"decline_pct": decline, "current": current, "previous": previous}
        elif operator == "increase_pct":
            if len(values) < 2:
                return False, {}
            previous = values[0]
            if previous <= 0:
                return False, {}
            increase = ((current - previous) / previous) * 100
            return increase >= value, {"increase_pct": increase, "current": current, "previous": previous}

        return False, {}

    async def _get_last_trigger(
        self,
        rule_id: str,
        workspace_id: UUID,
    ) -> datetime | None:
        """Get the last time this rule triggered."""
        result = await self.db.execute(
            select(IntelligenceSignal)
            .where(
                IntelligenceSignal.workspace_id == workspace_id,
                IntelligenceSignal.title.like(f"%{rule_id}%"),
                IntelligenceSignal.auto_triggered.is_(True),
            )
            .order_by(desc(IntelligenceSignal.created_at))
            .limit(1)
        )
        signal = result.scalar_one_or_none()
        return signal.created_at if signal else None
