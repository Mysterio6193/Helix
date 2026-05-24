"""Handler for skill: orchestrate_launch_campaign.

Single openai_chat (json_mode) producing the launch plan payload:
calendar / emails / press_kit / ads / rollout.
"""
from __future__ import annotations

import json
from typing import Any

from helix.skills.base import SkillContext, SkillResult, register_skill_handler
from helix.tools.registry import get_tool

_SYSTEM = (
    "You are a launch director for restaurant and food brands. Given a brand "
    "strategy and (optionally) a launch date, return ONLY a JSON object with "
    "these exact top-level keys:\n"
    "  calendar: array of { day_offset:int, channel:string, asset:string, owner:string, note:string }\n"
    "  emails:   array of { slot:string, subject:string, preheader:string, body:string, cta:string }\n"
    "  press_kit: { one_liner:string, short_bio:string, long_bio:string, quotes:string[], contact_placeholder:string }\n"
    "  ads: { meta: array of { headline:string, primary_text:string, cta:string }, google: array of { headline:string, description:string, path:string }, tiktok: array of { hook:string, script_beats:string[], cta:string } }\n"
    "  rollout: { phases: array of { name:string, days:string, focus:string }, success_metrics: string[] }\n"
    "Rules:\n"
    "- calendar: 16-24 entries spanning day_offset -14 to +14, weighted around "
    "T-0. Channels must be drawn from the supplied 'channels' list. Each entry "
    "names a concrete asset (e.g. 'IG carousel #2', 'launch email', 'press "
    "outreach batch').\n"
    "- emails: exactly 4 entries with slots ['teaser','announce','day_of','follow_up']. "
    "Subject lines <= 55 chars. Preheader <= 90 chars. Body 80-160 words, "
    "concrete sensory language, no clichés. CTA is the literal button label.\n"
    "- press_kit: one_liner <= 22 words. short_bio <= 60 words. long_bio "
    "120-180 words. quotes: exactly 3 quoted lines, each attributable to the "
    "founder / chef / brand voice. contact_placeholder is press@<slug>.com "
    "derived from the brand name.\n"
    "- ads.meta: 3 variants. ads.google: 3 variants. ads.tiktok: 3 variants. "
    "All within platform character limits: Meta headline <= 40, primary text "
    "<= 125. Google headline <= 30, description <= 90, path <= 15. TikTok hook "
    "<= 90.\n"
    "- rollout.phases: exactly 3 phases (Tease / Launch / Sustain). "
    "success_metrics: 3-5 measurable signals (e.g. 'IG followers +1k', "
    "'500 menu views', '50 first-week reservations').\n"
    "All copy in the brand voice. No emojis in email body or press_kit."
)


def _compose_user(
    strategy: dict,
    copy: dict,
    design_system: dict,
    channels: list[str],
    launch_date: str | None,
    notion_db: str | None,
) -> str:
    payload = {
        "brand_strategy": strategy,
        "voice": strategy.get("voice"),
        "design_system_summary": {
            "name": design_system.get("name"),
            "palette": design_system.get("palette"),
            "mood": design_system.get("mood"),
        },
        "channels": channels,
        "launch_date": launch_date,
        "notion_database_id": notion_db,
        "preferred_tagline": _first_tagline(copy),
    }
    return json.dumps(payload, indent=2)


def _first_tagline(copy: dict | None) -> str | None:
    if not copy:
        return None
    options = (copy.get("taglines") or {}).get("options") or []
    if options and isinstance(options[0], dict):
        return options[0].get("text") or options[0].get("tagline")
    if options and isinstance(options[0], str):
        return options[0]
    return None


@register_skill_handler("orchestrate_launch_campaign")
async def handle(ctx: SkillContext) -> SkillResult:
    tool = get_tool("openai_chat")
    if tool is None:
        return SkillResult(ok=False, error="openai_chat tool not registered")

    inputs: dict[str, Any] = ctx.inputs or {}
    strategy = inputs.get("strategy") or {}
    if ctx.brand_context.get("brand", {}).get("name"):
        strategy = {**strategy, "name": ctx.brand_context["brand"]["name"]}
    copy = inputs.get("copy") or {}
    design_system = inputs.get("design_system") or {}
    channels = inputs.get("channels") or ["email", "social", "press", "paid"]
    launch_date = inputs.get("launch_date")
    notion_db = inputs.get("notion_database_id")

    messages: list[dict[str, str]] = []
    for learn in ctx.learnings:
        if learn:
            messages.append({"role": "system", "content": learn})
    messages.append({"role": "system", "content": _SYSTEM})
    messages.append(
        {
            "role": "user",
            "content": _compose_user(strategy, copy, design_system, channels, launch_date, notion_db),
        }
    )

    result = await tool.call(
        messages=messages,
        model="gpt-4o-mini",
        temperature=0.8,
        json_mode=True,
    )
    if not result.ok:
        return SkillResult(ok=False, error=result.error, cost_usd=result.cost_usd or 0.0)

    text = (result.data or {}).get("content") if isinstance(result.data, dict) else str(result.data or "")
    try:
        plan = json.loads(text)
    except json.JSONDecodeError:
        return SkillResult(
            ok=False,
            error="launch plan JSON parse failed",
            cost_usd=result.cost_usd or 0.0,
        )
    if not isinstance(plan, dict):
        return SkillResult(
            ok=False,
            error="launch plan payload not an object",
            cost_usd=result.cost_usd or 0.0,
        )

    # Surface counts for the slice's critic + summary nodes.
    counts = {
        "calendar": len(plan.get("calendar") or []),
        "emails": len(plan.get("emails") or []),
        "quotes": len((plan.get("press_kit") or {}).get("quotes") or []),
        "meta_ads": len((plan.get("ads") or {}).get("meta") or []),
        "google_ads": len((plan.get("ads") or {}).get("google") or []),
        "tiktok_ads": len((plan.get("ads") or {}).get("tiktok") or []),
        "rollout_phases": len((plan.get("rollout") or {}).get("phases") or []),
    }

    return SkillResult(
        ok=True,
        outputs={
            "calendar": plan.get("calendar", []),
            "emails": plan.get("emails", []),
            "press_kit": plan.get("press_kit", {}),
            "ads": plan.get("ads", {}),
            "rollout": plan.get("rollout", {}),
            "counts": counts,
            "channels": channels,
            "launch_date": launch_date,
        },
        cost_usd=result.cost_usd or 0.0,
    )
