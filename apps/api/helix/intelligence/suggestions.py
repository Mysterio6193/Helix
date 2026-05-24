"""AI Experiment Suggestion Engine — generates experiment hypotheses from intelligence signals."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.logging import get_logger
from helix.llm import complete
from helix.models.intelligence import Experiment, IntelligenceSignal
from helix.models.organization import User

log = get_logger("helix.intelligence.suggestions")

SUGGESTION_SYSTEM_PROMPT = """You are Helix's experiment strategist. You analyze business signals, past experiment results, and performance data to generate high-impact experiment suggestions.

For each suggestion, output a JSON object with these fields:
- name: short experiment name
- hypothesis: what you believe will happen and why
- experiment_type: "ab" or "multivariate"
- primary_metric: "conversion_rate" | "ctr" | "revenue_per_session"
- variants: array of variant objects with "name" and "config" (key-value pairs describing the change)
- estimated_sample_size: minimum sample size needed (100-5000)
- estimated_duration_days: how many days to run (3-30)
- rationale: why this experiment matters now, referencing signals

Output ONLY a JSON array of suggestions (1-3 suggestions). No markdown, no code fences."""


async def generate_suggestions(
    db: AsyncSession,
    user: User,
    workspace_id: UUID,
    brand_id: UUID | None = None,
) -> list[dict]:
    """Generate experiment suggestions from intelligence signals and performance data."""
    now = datetime.utcnow()

    # Gather recent unacknowledged signals (last 30 days)
    signals_q = await db.execute(
        select(IntelligenceSignal)
        .where(
            IntelligenceSignal.workspace_id == workspace_id,
            IntelligenceSignal.created_at >= now - timedelta(days=30),
            IntelligenceSignal.dismissed_at.is_(None),
        )
        .order_by(desc(IntelligenceSignal.severity), desc(IntelligenceSignal.created_at))
        .limit(20)
    )
    signals = signals_q.scalars().all()

    # Gather recent experiments (last 90 days)
    expts_q = await db.execute(
        select(Experiment)
        .where(
            Experiment.workspace_id == workspace_id,
            Experiment.created_at >= now - timedelta(days=90),
        )
        .order_by(desc(Experiment.created_at))
        .limit(10)
    )
    past_experiments = expts_q.scalars().all()

    # Build context for the LLM
    signal_summary = []
    for s in signals:
        signal_summary.append({
            "layer": s.layer,
            "signal_type": s.signal_type,
            "severity": s.severity,
            "title": s.title,
            "description": s.description[:300] if s.description else "",
            "recommended_action": s.recommended_action,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    experiment_summary = []
    for e in past_experiments:
        experiment_summary.append({
            "name": e.name,
            "hypothesis": e.hypothesis,
            "status": e.status,
            "experiment_type": e.experiment_type,
            "primary_metric": e.primary_metric,
            "winner": e.winner,
            "confidence": e.confidence,
            "uplift": e.uplift,
            "started_at": e.started_at.isoformat() if e.started_at else None,
        })

    brand_context = f" for brand {brand_id}" if brand_id else ""

    user_prompt = f"""Generate experiment suggestions based on the following intelligence data for workspace {workspace_id}{brand_context}.

Recent intelligence signals:
{json.dumps(signal_summary, indent=2, default=str) if signal_summary else "No recent signals."}

Recent experiments:
{json.dumps(experiment_summary, indent=2, default=str) if experiment_summary else "No past experiments."}

Analyze patterns, identify gaps, and suggest 1-3 experiments that would drive the most impact."""

    try:
        result = await complete(
            system=SUGGESTION_SYSTEM_PROMPT,
            prompt=user_prompt,
            temperature=0.7,
            max_tokens=3000,
            json_mode=True,
        )
        suggestions = json.loads(result.text)
        if isinstance(suggestions, dict):
            suggestions = suggestions.get("suggestions", [suggestions])
        for s in suggestions:
            s.setdefault("estimated_sample_size", 500)
            s.setdefault("estimated_duration_days", 7)
        return suggestions[:3]
    except Exception as exc:
        log.warning("suggestion_gen_failed", error=str(exc))
        return []
