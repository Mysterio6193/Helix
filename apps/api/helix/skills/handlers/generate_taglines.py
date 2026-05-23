"""Handler for skill: generate_taglines."""
from __future__ import annotations

import json
from typing import Any

from helix.skills.base import SkillContext, SkillResult, register_skill_handler
from helix.tools.registry import get_tool


SYSTEM_PROMPT = (
    "You are a senior copywriter for restaurants. "
    "Return ONLY a JSON object with key 'options' = array of items "
    "{text: string, length_words: int, angle: string}. "
    "Each tagline must respect the no_go list and match the requested voice."
)


def _compose_user(inputs: dict[str, Any]) -> str:
    strategy = inputs.get("strategy", {})
    return (
        f"BRAND STRATEGY:\n{json.dumps(strategy, indent=2)}\n\n"
        f"Voice: {inputs.get('tone') or strategy.get('voice') or 'warm-confident'}\n"
        f"Count: {inputs.get('count', 6)}"
    )


@register_skill_handler("generate_taglines")
async def handle(ctx: SkillContext) -> SkillResult:
    tool = get_tool("openai_chat")
    if tool is None:
        return SkillResult(ok=False, error="openai_chat tool not registered")

    messages = []
    for learn in ctx.learnings:
        if learn:
            messages.append({"role": "system", "content": learn})
    messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "user", "content": _compose_user(ctx.inputs or {})})

    result = await tool.call(
        messages=messages,
        model="gpt-4o-mini",
        temperature=0.85,
        json_mode=True,
    )
    if not result.ok:
        return SkillResult(ok=False, error=result.error, cost_usd=result.cost_usd or 0.0)

    text = (result.data or {}).get("content") if isinstance(result.data, dict) else str(result.data or "")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return SkillResult(ok=False, error="taglines JSON parse failed", cost_usd=result.cost_usd or 0.0)

    options = parsed.get("options") if isinstance(parsed, dict) else parsed
    if not isinstance(options, list):
        options = []
    return SkillResult(
        ok=True,
        outputs={"options": options, "count": len(options)},
        cost_usd=result.cost_usd or 0.0,
    )
