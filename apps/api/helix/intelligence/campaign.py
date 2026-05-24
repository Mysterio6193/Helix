"""Campaign intelligence engine — fatigue detection, health scoring, optimization."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.logging import get_logger
from helix.intelligence.analysis import detect_anomaly
from helix.models.intelligence import (
    PerformanceSnapshot,
)
from helix.models.workflow import Asset

log = get_logger(__name__)


class CampaignIntelligence:
    """Analyze campaign performance and generate optimization signals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_campaign_health(
        self,
        workspace_id: Any,
        brand_id: Any,
        days: int = 14,
    ) -> dict[str, Any]:
        """Analyze overall campaign health and return score + issues."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Fetch performance metrics
        result = await self.db.execute(
            select(PerformanceSnapshot)
            .where(
                PerformanceSnapshot.workspace_id == workspace_id,
                PerformanceSnapshot.brand_id == brand_id,
                PerformanceSnapshot.platform == "meta_ads",
                PerformanceSnapshot.metric_type.in_(["ctr", "roas", "spend", "impressions"]),
                PerformanceSnapshot.captured_at >= cutoff,
            )
            .order_by(PerformanceSnapshot.captured_at)
        )
        snapshots = result.scalars().all()

        if not snapshots:
            return {"score": 50, "issues": [], "status": "no_data"}

        # Group by metric
        by_metric: dict[str, list[float]] = {}
        for snap in snapshots:
            by_metric.setdefault(snap.metric_type, []).append(snap.value)

        issues = []
        score = 100

        # Check CTR decline
        ctr_values = by_metric.get("ctr", [])
        if len(ctr_values) >= 7:
            recent_avg = sum(ctr_values[-7:]) / 7
            previous_avg = sum(ctr_values[-14:-7]) / 7 if len(ctr_values) >= 14 else recent_avg
            if previous_avg > 0 and recent_avg < previous_avg * 0.8:
                decline = ((previous_avg - recent_avg) / previous_avg) * 100
                issues.append({
                    "type": "fatigue",
                    "severity": "high" if decline > 40 else "medium",
                    "description": f"CTR declined {decline:.1f}% over last 7 days",
                    "metric": "ctr",
                    "recommendation": "Generate new creative variants and refresh ad copy",
                })
                score -= 20 if decline > 40 else 10

        # Check ROAS
        roas_values = by_metric.get("roas", [])
        if roas_values:
            current_roas = roas_values[-1]
            if current_roas < 2.0:
                issues.append({
                    "type": "roas",
                    "severity": "critical" if current_roas < 1.5 else "high",
                    "description": f"ROAS at {current_roas:.2f}x, below 2.0x target",
                    "metric": "roas",
                    "recommendation": "Review audience targeting and pause underperforming ad sets",
                })
                score -= 30 if current_roas < 1.5 else 15

        # Check spend efficiency
        spend_values = by_metric.get("spend", [])
        if len(spend_values) >= 7:
            daily_spend = sum(spend_values[-7:]) / 7
            if daily_spend > 500 and current_roas < 2.0:
                issues.append({
                    "type": "budget",
                    "severity": "medium",
                    "description": f"High spend (${daily_spend:.0f}/day) with low ROAS",
                    "metric": "spend",
                    "recommendation": "Reduce daily budget and reallocate to higher-performing campaigns",
                })
                score -= 10

        return {
            "score": max(0, min(100, score)),
            "issues": issues,
            "status": "healthy" if score >= 80 else "needs_attention" if score >= 60 else "critical",
            "metrics": {
                "ctr": ctr_values[-1] if ctr_values else 0,
                "roas": roas_values[-1] if roas_values else 0,
                "avg_spend": sum(spend_values[-7:]) / 7 if spend_values else 0,
            }
        }

    async def detect_creative_fatigue(
        self,
        workspace_id: Any,
        brand_id: Any,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """Detect ad creative fatigue based on performance decline."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(PerformanceSnapshot)
            .where(
                PerformanceSnapshot.workspace_id == workspace_id,
                PerformanceSnapshot.brand_id == brand_id,
                PerformanceSnapshot.metric_type == "ctr",
                PerformanceSnapshot.captured_at >= cutoff,
            )
            .order_by(PerformanceSnapshot.captured_at)
        )
        snapshots = result.scalars().all()

        if len(snapshots) < 14:
            return []

        ctr_values = [s.value for s in snapshots]

        # Detect anomaly in CTR (creative fatigue indicator)
        anomaly_indices = detect_anomaly(ctr_values, threshold=2.5)

        fatigue_signals = []
        for idx in anomaly_indices:
            if idx >= len(snapshots):
                continue
            snap = snapshots[idx]
            # Check if it's a decline (not a spike)
            if idx > 0 and ctr_values[idx] < ctr_values[idx - 1]:
                decline = ((ctr_values[idx - 1] - ctr_values[idx]) / max(ctr_values[idx - 1], 0.001)) * 100
                fatigue_signals.append({
                    "date": snap.captured_at.isoformat() if snap.captured_at else None,
                    "ctr": ctr_values[idx],
                    "decline_percent": round(decline, 1),
                    "severity": "high" if decline > 30 else "medium",
                    "recommendation": "Generate 3 new creative variants and A/B test",
                })

        return fatigue_signals


class CreativeIntelligence:
    """Analyze creative assets for quality, fatigue, and brand compliance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def score_creative_fatigue(
        self,
        brand_id: Any,
        asset_id: Any,
    ) -> dict[str, Any]:
        """Score an asset for fatigue based on similarity to recent winners."""
        # Fetch recent assets for comparison
        result = await self.db.execute(
            select(Asset)
            .where(
                Asset.brand_id == brand_id,
                Asset.kind == "image",
            )
            .order_by(desc(Asset.created_at))
            .limit(20)
        )
        recent_assets = result.scalars().all()

        if len(recent_assets) < 5:
            return {"fatigue_score": 0, "status": "fresh", "similarity": 0}

        # Simple heuristic: if asset is very similar to many recent ones, it's fatigued
        # In production, this would use CLIP embeddings
        asset_ids = [str(a.id) for a in recent_assets]
        similarity = asset_ids.count(str(asset_id)) / len(asset_ids)
        fatigue_score = min(1.0, similarity * 10)  # Scale up

        return {
            "fatigue_score": round(fatigue_score, 2),
            "status": "fatigued" if fatigue_score > 0.7 else "tired" if fatigue_score > 0.4 else "fresh",
            "similarity": round(similarity, 3),
            "recent_assets_count": len(recent_assets),
        }

    async def generate_optimization_signals(
        self,
        workspace_id: Any,
        brand_id: Any,
    ) -> list[dict[str, Any]]:
        """Generate actionable optimization signals."""
        campaign_intel = CampaignIntelligence(self.db)
        health = await campaign_intel.analyze_campaign_health(workspace_id, brand_id)
        fatigue = await campaign_intel.detect_creative_fatigue(workspace_id, brand_id)

        signals = []

        # Health-based signals
        for issue in health.get("issues", []):
            signals.append({
                "layer": "campaign",
                "signal_type": "anomaly",
                "severity": issue["severity"],
                "title": f"Campaign {issue['type'].title()} Detected",
                "description": issue["description"],
                "recommended_action": issue["recommendation"],
            })

        # Fatigue signals
        for fat in fatigue:
            signals.append({
                "layer": "creative",
                "signal_type": "trend",
                "severity": fat["severity"],
                "title": f"Creative Fatigue: CTR dropped {fat['decline_percent']}%",
                "description": f"CTR declined to {fat['ctr']:.2f}% on {fat['date']}",
                "recommended_action": fat["recommendation"],
            })

        return signals
