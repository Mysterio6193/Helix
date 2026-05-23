"""Closed-loop skill learning (Hermes pattern).

After every successful run, OrchestratorAgent extracts a SkillLearning row from
the run trace, capturing the trigger context + prompt delta that worked. On
skill load, learnings are prepended to the handler system prompt.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.models.skill import SkillLearning, SkillRegistry


async def extract_learning(
    db: AsyncSession,
    *,
    skill_name: str,
    workflow_run_id: uuid.UUID,
    brand_id: uuid.UUID | None,
    trigger_context: str,
    prompt_delta: str,
    success_markers: dict[str, Any] | None = None,
    score: float | None = None,
    context_embedding: list[float] | None = None,
) -> SkillLearning | None:
    skill = (
        await db.execute(select(SkillRegistry).where(SkillRegistry.name == skill_name))
    ).scalar_one_or_none()
    if skill is None:
        return None

    learning = SkillLearning(
        skill_id=skill.id,
        workflow_run_id=workflow_run_id,
        brand_id=brand_id,
        trigger_context=trigger_context,
        prompt_delta=prompt_delta,
        success_markers=success_markers or {},
        score=score,
        context_embedding=context_embedding,
    )
    db.add(learning)
    await db.flush()
    await db.refresh(learning)
    return learning


async def load_learnings(
    db: AsyncSession,
    *,
    skill_name: str,
    brand_id: uuid.UUID | None = None,
    brand_context_embedding: list[float] | None = None,
    limit: int = 5,
) -> list[SkillLearning]:
    """Return enabled learnings, ranked semantically if brand_context_embedding is provided,
    otherwise by most recent.
    """
    stmt = (
        select(SkillLearning)
        .join(SkillRegistry, SkillRegistry.id == SkillLearning.skill_id)
        .where(SkillRegistry.name == skill_name, SkillLearning.enabled.is_(True))
    )
    
    if brand_context_embedding is not None:
        stmt = stmt.order_by(
            SkillLearning.context_embedding.cosine_distance(brand_context_embedding),
            desc(SkillLearning.score),
            desc(SkillLearning.created_at),
        )
    else:
        stmt = stmt.order_by(desc(SkillLearning.created_at))

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


def format_learnings_preamble(learnings: list[SkillLearning]) -> str:
    if not learnings:
        return ""
    lines = ["Lessons learned from past successful runs of this skill:"]
    for i, lrn in enumerate(learnings, 1):
        if lrn.prompt_delta:
            lines.append(f"  {i}. {lrn.prompt_delta.strip()}")
    return "\n".join(lines)
