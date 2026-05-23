"""Handler for skill: build_social_pack.

Three-stage pipeline:
  1. Plan generation — captions per slot, hashtag families, bios, 14-day cadence
     (openai_chat, json_mode).
  2. Feed tiles — N square images (1024x1024) rendered concurrently.
  3. Story templates — story_count 9:16 frames (1024x1536) rendered concurrently.

Returns `outputs.plan` and `outputs.visuals` so the SocialProducerAgent can
splat them into state.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from helix.models.workflow import Asset
from helix.skills.base import SkillContext, SkillResult, register_skill_handler
from helix.tools.registry import get_tool


# ---------------------------------------------------------------------------
# 1. Plan
# ---------------------------------------------------------------------------

_PLAN_SYSTEM = (
    "You are a social media director for restaurant brands. Given a brand "
    "strategy and the number of feed posts, return ONLY a JSON object with:\n"
    "  captions: array of {slot:int, hook:string, body:string, cta:string, hashtags:string[]}  // length == post_count\n"
    "  hashtags: { core: string[], local: string[], occasion: string[] }  // 6-10 each, no '#' prefix\n"
    "  bios: { instagram: string, tiktok: string }  // each <= 150 chars\n"
    "  cadence: array of { day:int, slot:string, post_idx:int, note:string }  // 14 entries covering a 14-day launch window\n"
    "Tone matches strategy.voice. Concrete sensory language. No emojis in body. "
    "Hashtags must be specific (not 'food', 'yummy'). Captions must be platform-agnostic."
)


def _compose_plan_user(strategy: dict, copy: dict, platforms: list[str], post_count: int) -> str:
    payload = {
        "brand_strategy": strategy,
        "platforms": platforms,
        "post_count": post_count,
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


async def _generate_plan(
    ctx: SkillContext,
    strategy: dict,
    copy: dict,
    platforms: list[str],
    post_count: int,
) -> tuple[dict[str, Any] | None, float, str | None]:
    tool = get_tool("openai_chat")
    if tool is None:
        return None, 0.0, "openai_chat tool not registered"

    messages: list[dict[str, str]] = []
    for learn in ctx.learnings:
        if learn:
            messages.append({"role": "system", "content": learn})
    messages.append({"role": "system", "content": _PLAN_SYSTEM})
    messages.append(
        {"role": "user", "content": _compose_plan_user(strategy, copy, platforms, post_count)}
    )

    result = await tool.call(
        messages=messages,
        model="gpt-4o-mini",
        temperature=0.85,
        json_mode=True,
    )
    if not result.ok:
        return None, result.cost_usd or 0.0, result.error

    text = (result.data or {}).get("content") if isinstance(result.data, dict) else str(result.data or "")
    try:
        plan = json.loads(text)
    except json.JSONDecodeError:
        return None, result.cost_usd or 0.0, "plan JSON parse failed"

    if not isinstance(plan, dict):
        return None, result.cost_usd or 0.0, "plan payload not an object"
    return plan, result.cost_usd or 0.0, None


# ---------------------------------------------------------------------------
# 2. + 3. Visuals (feed tiles + story templates)
# ---------------------------------------------------------------------------

def _palette_words(design_system: dict) -> str:
    pal = design_system.get("palette") or {}
    primaries: list[str] = []
    for key in ("ink", "accent", "brand_coral", "brand_blue", "primary"):
        v = pal.get(key)
        if isinstance(v, str):
            primaries.append(v)
        elif isinstance(v, list) and v:
            primaries.append(str(v[0]))
        if len(primaries) >= 3:
            break
    return ", ".join(primaries) if primaries else "monochrome"


def _typography_family(design_system: dict) -> str:
    typo = design_system.get("typography") or {}
    return typo.get("family_primary") or "geometric sans"


def _mood_words(strategy: dict) -> str:
    mood = strategy.get("mood")
    if isinstance(mood, list) and mood:
        return ", ".join(str(m) for m in mood[:4])
    return "confident, contemporary"


_FEED_TEMPLATES = (
    "hero shot — product centered, soft texture background, no text",
    "ingredient still life — flat-lay top down, geometric composition",
    "typography poster — large quote in brand voice, bold layout",
    "behind-the-scenes — hands at work, candid, warm light",
    "menu spotlight — single dish with brand-color frame",
    "venue or vibe shot — interior detail, mood-forward",
    "team or founder portrait — editorial, environmental",
    "promo tile — bold offer text on brand-color background",
    "story stamp — circular mark, repeating motif",
)


def _feed_prompt(
    *,
    slot: int,
    strategy: dict,
    design_system: dict,
    caption_hook: str | None,
    school: str | None,
) -> str:
    name = strategy.get("name") or "the brand"
    palette = _palette_words(design_system)
    family = _typography_family(design_system)
    mood = _mood_words(strategy)
    school_descriptor = (design_system.get("name") or school or "modern").lower()
    template = _FEED_TEMPLATES[slot % len(_FEED_TEMPLATES)]
    hook_line = f"Caption hook: \"{caption_hook}\". " if caption_hook else ""

    return (
        f"Square (1:1) Instagram feed tile for restaurant brand '{name}'. "
        f"Composition direction: {template}. "
        f"Aesthetic: {school_descriptor} ({mood}). "
        f"Typography vibe: {family}. Palette: {palette}. "
        f"{hook_line}"
        "Clean, editorial, print-quality. No watermarks, no UI chrome, no model "
        f"hands obstructing product. Variation seed {slot}."
    )


_STORY_TEMPLATES = (
    "announcement template — large headline + small subtitle, vertical layout, 9:16",
    "quote template — pull-quote in brand voice, ink-on-canvas, generous margins, 9:16",
    "countdown template — date stamp + headline + brand color band at base, 9:16",
    "menu drop template — dish callout + price + tagline, 9:16",
    "thank-you template — gratitude statement + brand mark, 9:16",
)


def _story_prompt(
    *,
    idx: int,
    strategy: dict,
    design_system: dict,
    school: str | None,
) -> str:
    name = strategy.get("name") or "the brand"
    palette = _palette_words(design_system)
    family = _typography_family(design_system)
    mood = _mood_words(strategy)
    school_descriptor = (design_system.get("name") or school or "modern").lower()
    template = _STORY_TEMPLATES[idx % len(_STORY_TEMPLATES)]
    return (
        f"Instagram story template (9:16 vertical) for restaurant brand '{name}'. "
        f"Layout: {template}. "
        f"Aesthetic: {school_descriptor} ({mood}). "
        f"Typography vibe: {family}. Palette: {palette}. "
        "Safe area respected (top 14% / bottom 14% reserved for UI). Editorial "
        f"composition, generous negative space. Variation seed {idx}."
    )


async def _render_visuals(
    *,
    ctx: SkillContext,
    purpose: str,
    prompts: list[str],
    size: str,
    meta_base: dict[str, Any],
) -> tuple[list[dict[str, Any]], list, float, list[str]]:
    image_tool = get_tool("openai_image")
    if image_tool is None:
        return [], [], 0.0, ["openai_image tool not registered"]

    calls = [image_tool.call(prompt=p, size=size, quality="high", n=1) for p in prompts]
    results = await asyncio.gather(*calls, return_exceptions=True)

    visuals: list[dict[str, Any]] = []
    asset_ids: list = []
    cost = 0.0
    errors: list[str] = []

    for idx, res in enumerate(results):
        if isinstance(res, Exception):
            errors.append(f"{purpose} variant {idx}: {res!s}")
            continue
        if not res.ok:
            errors.append(f"{purpose} variant {idx}: {res.error}")
            continue
        cost += res.cost_usd or 0.0
        raw = res.data
        if isinstance(raw, list):
            data = raw[0] if raw else {}
        elif isinstance(raw, dict):
            data = raw
        else:
            data = {}
        s3_key = data.get("s3_key") or data.get("storage_key")
        width = data.get("width")
        height = data.get("height")
        asset = Asset(
            workflow_run_id=ctx.workflow_run_id,
            brand_id=ctx.brand_id,
            workspace_id=ctx.workspace_id,
            purpose=purpose,
            kind="image",
            storage_key=s3_key,
            mime_type=data.get("mime_type", "image/png"),
            width=width,
            height=height,
            metadata_={
                **meta_base,
                "prompt": prompts[idx],
                "model": res.model,
                "variant": idx,
            },
        )
        ctx.db.add(asset)
        await ctx.db.flush()
        asset_ids.append(asset.id)
        visuals.append(
            {
                "asset_id": str(asset.id),
                "purpose": purpose,
                "storage_key": s3_key,
                "width": width,
                "height": height,
                "prompt": prompts[idx],
                "variant": idx,
            }
        )

    return visuals, asset_ids, cost, errors


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

@register_skill_handler("build_social_pack")
async def handle(ctx: SkillContext) -> SkillResult:
    inputs: dict[str, Any] = ctx.inputs or {}
    strategy = inputs.get("strategy") or {}
    if ctx.brand_context.get("brand", {}).get("name"):
        strategy = {**strategy, "name": ctx.brand_context["brand"]["name"]}

    design_system = inputs.get("design_system") or {}
    school = inputs.get("design_school") or design_system.get("school")
    copy = inputs.get("copy") or {}
    platforms = inputs.get("platforms") or ["instagram", "tiktok"]
    post_count = max(1, min(12, int(inputs.get("post_count", 9))))
    story_count = max(0, min(6, int(inputs.get("story_count", 3))))

    # ---- Step 1: plan ----
    plan, plan_cost, plan_err = await _generate_plan(
        ctx, strategy, copy, platforms, post_count
    )
    if plan is None:
        return SkillResult(ok=False, error=f"plan: {plan_err}", cost_usd=plan_cost)

    captions = plan.get("captions") or []
    if not isinstance(captions, list):
        captions = []

    total_cost = plan_cost
    all_visuals: list[dict[str, Any]] = []
    all_asset_ids: list = []
    all_errors: list[str] = []

    # ---- Step 2: feed tiles ----
    feed_prompts = [
        _feed_prompt(
            slot=i,
            strategy=strategy,
            design_system=design_system,
            caption_hook=(captions[i].get("hook") if i < len(captions) and isinstance(captions[i], dict) else None),
            school=school,
        )
        for i in range(post_count)
    ]
    feed_visuals, feed_ids, feed_cost, feed_errs = await _render_visuals(
        ctx=ctx,
        purpose="social:feed",
        prompts=feed_prompts,
        size="1024x1024",
        meta_base={"platforms": platforms, "kind": "feed"},
    )
    total_cost += feed_cost
    all_visuals.extend(feed_visuals)
    all_asset_ids.extend(feed_ids)
    all_errors.extend(feed_errs)

    # ---- Step 3: story templates ----
    if story_count > 0:
        story_prompts = [
            _story_prompt(idx=i, strategy=strategy, design_system=design_system, school=school)
            for i in range(story_count)
        ]
        story_visuals, story_ids, story_cost, story_errs = await _render_visuals(
            ctx=ctx,
            purpose="social:story",
            prompts=story_prompts,
            size="1024x1536",
            meta_base={"platforms": platforms, "kind": "story"},
        )
        total_cost += story_cost
        all_visuals.extend(story_visuals)
        all_asset_ids.extend(story_ids)
        all_errors.extend(story_errs)

    if not all_visuals:
        return SkillResult(
            ok=False,
            error=f"all social visuals failed: {'; '.join(all_errors)}",
            cost_usd=total_cost,
        )

    await ctx.db.commit()
    return SkillResult(
        ok=True,
        outputs={
            "plan": plan,
            "visuals": all_visuals,
            "counts": {
                "feed": len([v for v in all_visuals if v["purpose"] == "social:feed"]),
                "story": len([v for v in all_visuals if v["purpose"] == "social:story"]),
            },
            "errors": all_errors,
        },
        asset_ids=all_asset_ids,
        cost_usd=total_cost,
    )
