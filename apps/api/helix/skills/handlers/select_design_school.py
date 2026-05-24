"""Handler for skill: select_design_school."""
from __future__ import annotations

import json

from sqlalchemy import select

from helix.models.design_system import DesignSystem
from helix.skills.base import SkillContext, SkillResult, register_skill_handler
from helix.tools.registry import get_tool

SYSTEM_PROMPT = (
    "You are an art director choosing one of several pre-built visual schools "
    "to match a brand strategy. Return ONLY a JSON object: "
    "{\"slug\": <chosen-school-slug>, \"rationale\": <2-sentence reasoning>}."
)


def _school_summary(row: DesignSystem) -> str:
    tags = ", ".join(row.tags or [])
    return f"- {row.slug}: {row.name} — {row.description or ''} [tags: {tags}]"


@register_skill_handler("select_design_school")
async def handle(ctx: SkillContext) -> SkillResult:
    user_pref = (ctx.inputs or {}).get("user_pref_school")

    schools = (
        await ctx.db.scalars(
            select(DesignSystem).where(DesignSystem.is_school.is_(True), DesignSystem.enabled.is_(True))
        )
    ).all()
    if not schools:
        return SkillResult(ok=False, error="no design schools loaded — run sync_design_systems")

    by_slug = {s.slug: s for s in schools}

    if user_pref and user_pref in by_slug:
        chosen = by_slug[user_pref]
        return SkillResult(
            ok=True,
            outputs={
                "school": chosen.slug,
                "design_system": _serialize_school(chosen),
                "rationale": "User-selected preference.",
            },
        )

    tool = get_tool("openai_chat")
    if tool is None:
        return SkillResult(ok=False, error="openai_chat tool not registered")

    strategy = (ctx.inputs or {}).get("strategy", {})
    user_msg = (
        "BRAND STRATEGY:\n"
        f"{json.dumps(strategy, indent=2)}\n\n"
        "AVAILABLE SCHOOLS:\n"
        + "\n".join(_school_summary(s) for s in schools)
        + "\n\nPick exactly one slug from the list above."
    )

    messages = []
    for learn in ctx.learnings:
        if learn:
            messages.append({"role": "system", "content": learn})
    messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "user", "content": user_msg})

    result = await tool.call(messages=messages, model="gpt-4o-mini", temperature=0.3, json_mode=True)
    if not result.ok:
        return SkillResult(ok=False, error=result.error, cost_usd=result.cost_usd or 0.0)

    text = (result.data or {}).get("content") if isinstance(result.data, dict) else str(result.data or "")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return SkillResult(ok=False, error="school selection JSON parse failed")

    slug = parsed.get("slug")
    if slug not in by_slug:
        # Fallback: pick the first school
        slug = schools[0].slug
    chosen = by_slug[slug]
    return SkillResult(
        ok=True,
        outputs={
            "school": chosen.slug,
            "design_system": _serialize_school(chosen),
            "rationale": parsed.get("rationale", ""),
        },
        cost_usd=result.cost_usd or 0.0,
    )


def _serialize_school(row: DesignSystem) -> dict:
    return {
        "slug": row.slug,
        "name": row.name,
        "palette": row.palette,
        "typography": row.typography,
        "spacing": row.spacing,
        "motion": row.motion,
        "components": row.components,
        "tags": row.tags,
    }
