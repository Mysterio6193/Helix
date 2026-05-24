"""Post-run reflection to extract closed-loop learnings (Hermes pattern)."""
from __future__ import annotations

import json
import uuid
from typing import Any

from helix.core.config import get_settings
from helix.core.logging import get_logger
from helix.workflows.state import HelixState

log = get_logger(__name__)


async def reflect_on_run(state: HelixState) -> list[dict[str, Any]]:
    """LLM-powered post-run reflection that extracts concrete learnings."""
    settings = get_settings()

    # Extract workflow metadata
    run_id_str = state.get("run_id")
    brand_id_str = state.get("brand_id")
    workflow = state.get("workflow", "unknown")

    try:
        run_id = uuid.UUID(run_id_str) if run_id_str else uuid.uuid4()
        brand_id = uuid.UUID(brand_id_str) if brand_id_str else None
    except ValueError:
        run_id = uuid.uuid4()
        brand_id = None

    steps = state.get("steps", [])
    critiques = state.get("critiques", [])
    brand_context = state.get("brand_context", {})

    # Offline/No-key fallback: extract simple recency/status-based learnings without LLM
    if not settings.openai_api_key:
        log.info("openai_api_key_not_found_skipping_llm_reflection")
        return _offline_fallback_reflection(state, run_id, brand_id)

    # Calculate average critic score or final score
    avg_critic_score = 0.0
    if critiques:
        scores = [c.get("score", 0.0) for c in critiques if c.get("score") is not None]
        if scores:
            avg_critic_score = sum(scores) / len(scores)

    # Prompt constructing brand profile, steps taken, and critique feedback
    brand_summary = {
        "name": brand_context.get("name"),
        "category": brand_context.get("category"),
        "positioning": brand_context.get("positioning"),
        "voice_attributes": brand_context.get("voice_attributes"),
        "palette": brand_context.get("palette"),
    }

    step_summaries = []
    for step in steps:
        if step.get("skill"):
            step_summaries.append({
                "skill": step.get("skill"),
                "agent": step.get("agent"),
                "status": step.get("status"),
                "output_summary": step.get("output_summary"),
                "cost_usd": step.get("cost_usd", 0.0),
            })

    critique_summaries = []
    for crit in critiques:
        critique_summaries.append({
            "verdict": crit.get("verdict"),
            "score": crit.get("score"),
            "dimension_scores": crit.get("dimension_scores"),
            "feedback": crit.get("feedback"),
        })

    prompt = f"""You are the Helix Creative OS Reflection Engine.
Your task is to analyze the history of a completed creative workflow run and extract concrete, actionable lessons ("prompt deltas") that can be prepended to the system prompt of skills in future runs to improve their quality.

Brand Profile:
{json.dumps(brand_summary, indent=2)}

Workflow Name: {workflow}
Run ID: {run_id}

Step History:
{json.dumps(step_summaries, indent=2)}

Critiques & Scores:
{json.dumps(critique_summaries, indent=2)}

For each successful skill invocation (status is "ok" and a skill was used), synthesize a concrete lesson learned.
A lesson should highlight:
1. What worked well (based on high critique scores).
2. What needs to be changed/refined (based on critic feedback and failing dimensions).

Each prompt delta must be highly specific, prescriptive, and practical. Avoid generic platitudes.
Format your output as a JSON object with a single key "learnings" containing a list of objects. Each object must have:
- "skill_name": The exact name of the skill.
- "trigger_context": A short description of the context/inputs that triggered this skill (e.g. "Restaurant design under Playful-Warm school").
- "prompt_delta": A highly specific, actionable styling or copywriting instruction (e.g., "When generating tagline copy for luxury fashion, use exactly 3-5 words, avoid exclamation marks, and emphasize heritage/exclusivity.").
- "score": A float score from 0.0 to 10.0 indicating how successful this skill output was based on critiques.
- "success_markers": A dict with keys like "critic_score", "iterations", "cost_usd", "errors".

Respond ONLY with valid JSON. Do not include markdown blocks like ```json or anything else.
"""

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional software reflection agent that outputs pure JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=1500,
        )

        content = resp.choices[0].message.content or ""
        data = json.loads(content)
        learnings_raw = data.get("learnings", [])

        output_learnings = []
        for item in learnings_raw:
            skill_name = item.get("skill_name")
            if not skill_name:
                continue

            output_learnings.append({
                "skill_name": skill_name,
                "workflow_run_id": run_id,
                "brand_id": brand_id,
                "trigger_context": item.get("trigger_context", f"Workflow {workflow}"),
                "prompt_delta": item.get("prompt_delta", ""),
                "score": item.get("score", avg_critic_score),
                "success_markers": item.get("success_markers", {"critic_score": avg_critic_score}),
            })
        return output_learnings

    except Exception:
        log.exception("llm_reflection_failed_falling_back")
        return _offline_fallback_reflection(state, run_id, brand_id)


def _offline_fallback_reflection(state: HelixState, run_id: uuid.UUID, brand_id: uuid.UUID | None) -> list[dict[str, Any]]:
    """Deterministic fallback for local/offline environments without LLM keys."""
    learnings = []
    steps = state.get("steps", [])
    critiques = state.get("critiques", [])
    brand_context = state.get("brand_context", {})
    workflow = state.get("workflow", "unknown")
    brand_category = brand_context.get("category", "unknown")
    design_school = state.get("design_school", "default")

    avg_critic_score = 8.0
    if critiques:
        scores = [c.get("score", 0.0) for c in critiques if c.get("score") is not None]
        if scores:
            avg_critic_score = sum(scores) / len(scores)

    for step in steps:
        skill_name = step.get("skill")
        if step.get("status") == "ok" and skill_name:
            trigger_context = f"{brand_category} brand under {design_school} school inside {workflow} workflow."

            # Simple deterministic prompt delta based on state
            prompt_delta = (
                f"For the {skill_name} skill, ensure output strictly conforms to "
                f"the {design_school} style school with color palette {brand_context.get('palette', [])}."
            )

            learnings.append({
                "skill_name": skill_name,
                "workflow_run_id": run_id,
                "brand_id": brand_id,
                "trigger_context": trigger_context,
                "prompt_delta": prompt_delta,
                "score": avg_critic_score,
                "success_markers": {
                    "critic_score": avg_critic_score,
                    "cost_usd": step.get("cost_usd", 0.0),
                    "duration_ms": int((step.get("ended_at", 0) - step.get("started_at", 0)) * 1000) if step.get("ended_at") else 0,
                }
            })
    return learnings
