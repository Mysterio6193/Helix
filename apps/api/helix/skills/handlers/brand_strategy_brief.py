"""Handler for skill: brand_strategy_brief."""
from __future__ import annotations

import json
from typing import Any

from helix.skills.base import SkillContext, SkillResult, register_skill_handler
from helix.tools.registry import get_tool

SYSTEM_PROMPT = (
    "You are a brand strategist for restaurants and food brands. "
    "Return ONLY a JSON object with keys: positioning (string, ~25 words), "
    "audience (object with persona, age_range, psychographics array), "
    "voice (string, 3-5 adjectives joined by hyphens), "
    "mood (array of 5 evocative adjectives), "
    "no_go (array of 5 clichés/words to avoid), "
    "keywords (array of 8 brand-relevant keywords). "
    "Be specific, opinionated, and avoid generic restaurant language."
)


def _compose_user(inputs: dict[str, Any]) -> str:
    parts = [f"Brand name: {inputs.get('name','(unnamed)')}"]
    if inputs.get("category"):
        parts.append(f"Category: {inputs['category']}")
    if inputs.get("cuisine"):
        parts.append(f"Cuisine: {inputs['cuisine']}")
    if inputs.get("city"):
        parts.append(f"City: {inputs['city']}")
    if inputs.get("audience_hint"):
        parts.append(f"Audience hint: {inputs['audience_hint']}")
    if inputs.get("vibe"):
        parts.append(f"Vibe: {inputs['vibe']}")
    return "\n".join(parts)


@register_skill_handler("brand_strategy_brief")
async def handle(ctx: SkillContext) -> SkillResult:
    tool = get_tool("openai_chat")
    if tool is None:
        return SkillResult(ok=False, error="openai_chat tool not registered")

    messages = []
    for learn in ctx.learnings:
        if learn:
            messages.append({"role": "system", "content": learn})
    messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "user", "content": _compose_user(ctx.inputs)})

    result = await tool.call(
        messages=messages,
        model="gpt-4o-mini",
        temperature=0.7,
        json_mode=True,
    )
    if not result.ok:
        return SkillResult(ok=False, error=result.error, cost_usd=result.cost_usd or 0.0)

    text = (result.data or {}).get("content") if isinstance(result.data, dict) else None
    if not text:
        text = str(result.data or "")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return SkillResult(ok=False, error="strategy JSON parse failed", cost_usd=result.cost_usd or 0.0)

    return SkillResult(
        ok=True,
        outputs={
            "strategy": parsed,
            "brief": parsed,
            "positioning": parsed.get("positioning"),
            "voice": parsed.get("voice"),
            "mood": parsed.get("mood", []),
            "no_go": parsed.get("no_go", []),
            "keywords": parsed.get("keywords", []),
        },
        cost_usd=result.cost_usd or 0.0,
        metadata={"model": result.model, "tokens": result.metadata.get("tokens") if result.metadata else None},
    )
