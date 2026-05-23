"""Handler for skill: critique_output."""
from __future__ import annotations

import json
from typing import Any

from helix.skills.base import SkillContext, SkillResult, register_skill_handler
from helix.tools.registry import get_tool


SYSTEM_PROMPT = (
    "You are a senior creative director and brand critic. "
    "Critique the candidate output against the brand strategy + design school. "
    "Return ONLY a JSON object: "
    "{verdict: 'accept'|'revise', score: 0-10, "
    "findings: [{dimension: string, score: 0-10, note: string}], "
    "target_branch: 'copy'|'visuals'|null, "
    "summary: string}. "
    "Acceptance bar: every finding >= 7. If any < 7, verdict='revise' and "
    "target_branch identifies the worst dimension's owner."
)


def _compose_user(inputs: dict[str, Any]) -> str:
    return (
        f"TARGET: {inputs.get('target','unknown')}\n\n"
        f"BRAND STRATEGY:\n{json.dumps(inputs.get('strategy',{}), indent=2)}\n\n"
        f"DESIGN SYSTEM:\n{json.dumps({k: v for k, v in (inputs.get('design_system') or {}).items() if k in ('slug','name','palette','typography','tags')}, indent=2)}\n\n"
        f"CANDIDATE:\n{json.dumps(inputs.get('candidate',{}), indent=2, default=str)}"
    )


@register_skill_handler("critique_output")
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
        temperature=0.2,
        json_mode=True,
    )
    if not result.ok:
        return SkillResult(ok=False, error=result.error, cost_usd=result.cost_usd or 0.0)

    text = (result.data or {}).get("content") if isinstance(result.data, dict) else str(result.data or "")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return SkillResult(ok=False, error="critique JSON parse failed", cost_usd=result.cost_usd or 0.0)

    verdict = parsed.get("verdict", "accept")
    score = parsed.get("score", 0)
    findings = parsed.get("findings", []) or []
    target_branch = parsed.get("target_branch")
    summary = parsed.get("summary", "")

    return SkillResult(
        ok=True,
        outputs={
            "verdict": verdict,
            "score": score,
            "findings": findings,
            "target_branch": target_branch,
            "summary": summary,
        },
        cost_usd=result.cost_usd or 0.0,
    )
