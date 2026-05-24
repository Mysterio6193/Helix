"""Handler for skill: design_menu_pack.

Three-stage pipeline:
  1. Menu structure — sections / items / photography brief via openai_chat json_mode.
  2. Mockup renders — N print-quality menu mockup images.
  3. Persist mockups as `Asset(purpose="menu:mockup")` and return both the
     structured menu and the visuals.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from helix.models.workflow import Asset
from helix.skills.base import SkillContext, SkillResult, register_skill_handler
from helix.tools.registry import get_tool

_FORMAT_DIMS: dict[str, tuple[str, str]] = {
    # format key -> (image size, orientation descriptor)
    "a4_portrait": ("1024x1536", "A4 portrait (210x297mm), single page"),
    "a4_landscape": ("1536x1024", "A4 landscape (297x210mm), single page"),
    "tabloid": ("1024x1536", "Tabloid portrait (11x17in), single page"),
    "tri_fold": ("1536x1024", "Tri-fold (three vertical panels on a landscape sheet)"),
}


# ---------------------------------------------------------------------------
# 1. Menu structure
# ---------------------------------------------------------------------------

_MENU_SYSTEM = (
    "You are a restaurant menu copywriter and food stylist. Given a brand "
    "strategy, design system, cuisine, and format, return ONLY a JSON object "
    "with:\n"
    "  format: string  // one of a4_portrait, a4_landscape, tabloid, tri_fold\n"
    "  sections: array of { slug:string, title:string, blurb:string, items: array of { name:string, description:string, price:string, dietary_tags:string[] } }\n"
    "  photography_brief: string  // 90-180 words describing dish photography direction\n"
    "Rules:\n"
    "- 4-6 sections covering the cuisine (e.g. Starters, Pasta, Mains, Sides, "
    "Desserts, Drinks). Each section: 3-6 items.\n"
    "- Item descriptions: 12-22 words, concrete sensory language, no clichés "
    "('mouthwatering', 'crispy goodness', etc.).\n"
    "- Prices: realistic for the brand positioning, in the strategy currency or "
    "USD if unknown. Format like '$14' or '£12.50'.\n"
    "- Dietary tags: subset of [V, VG, GF, DF, N, S]  (vegetarian, vegan, gluten-free, "
    "dairy-free, contains nuts, spicy).\n"
    "- The photography_brief speaks in the brand voice and references the design "
    "system palette + mood. No mention of stock photo aesthetics."
)


def _compose_menu_user(strategy: dict, design_system: dict, copy: dict, cuisine: str | None, fmt: str) -> str:
    payload = {
        "brand_strategy": strategy,
        "design_system_summary": {
            "name": design_system.get("name"),
            "palette": design_system.get("palette"),
            "typography": design_system.get("typography"),
            "mood": design_system.get("mood"),
        },
        "cuisine": cuisine,
        "format": fmt,
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


async def _generate_menu(
    ctx: SkillContext,
    strategy: dict,
    design_system: dict,
    copy: dict,
    cuisine: str | None,
    fmt: str,
) -> tuple[dict[str, Any] | None, float, str | None]:
    tool = get_tool("openai_chat")
    if tool is None:
        return None, 0.0, "openai_chat tool not registered"

    messages: list[dict[str, str]] = []
    for learn in ctx.learnings:
        if learn:
            messages.append({"role": "system", "content": learn})
    messages.append({"role": "system", "content": _MENU_SYSTEM})
    messages.append({"role": "user", "content": _compose_menu_user(strategy, design_system, copy, cuisine, fmt)})

    result = await tool.call(
        messages=messages,
        model="gpt-4o-mini",
        temperature=0.8,
        json_mode=True,
    )
    if not result.ok:
        return None, result.cost_usd or 0.0, result.error

    text = (result.data or {}).get("content") if isinstance(result.data, dict) else str(result.data or "")
    try:
        menu = json.loads(text)
    except json.JSONDecodeError:
        return None, result.cost_usd or 0.0, "menu JSON parse failed"

    if not isinstance(menu, dict):
        return None, result.cost_usd or 0.0, "menu payload not an object"
    return menu, result.cost_usd or 0.0, None


# ---------------------------------------------------------------------------
# 2. Mockup rendering
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
    return "considered, contemporary"


def _mockup_prompt(
    *,
    idx: int,
    strategy: dict,
    design_system: dict,
    fmt: str,
    section_names: list[str],
    school: str | None,
) -> str:
    name = strategy.get("name") or "the brand"
    palette = _palette_words(design_system)
    family = _typography_family(design_system)
    mood = _mood_words(strategy)
    school_descriptor = (design_system.get("name") or school or "modern").lower()
    layout_descriptor = _FORMAT_DIMS.get(fmt, _FORMAT_DIMS["a4_portrait"])[1]
    section_hint = ", ".join(section_names[:4]) if section_names else "core menu sections"

    variation = (
        "hero opening page" if idx == 0
        else "middle section spread with item list visible" if idx == 1
        else "back page with brand mark + footer"
    )
    return (
        f"Print-quality restaurant menu mockup for brand '{name}'. "
        f"Layout: {layout_descriptor}. "
        f"Aesthetic: {school_descriptor} ({mood}). "
        f"Typography vibe: {family}. Palette: {palette}. "
        f"Composition emphasis: {variation}. "
        f"Section headings visible: {section_hint}. "
        "Editorial typesetting, generous margins, real menu structure (section heading + "
        "item rows with names + descriptions + prices). No watermarks, no UI chrome, no "
        f"placeholder lorem ipsum — use plausible item names. Variation seed {idx}."
    )


async def _render_mockups(
    *,
    ctx: SkillContext,
    prompts: list[str],
    size: str,
    fmt: str,
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
            errors.append(f"mockup {idx}: {res!s}")
            continue
        if not res.ok:
            errors.append(f"mockup {idx}: {res.error}")
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
            purpose="menu:mockup",
            kind="image",
            storage_key=s3_key,
            mime_type=data.get("mime_type", "image/png"),
            width=width,
            height=height,
            metadata_={
                "format": fmt,
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
                "purpose": "menu:mockup",
                "storage_key": s3_key,
                "width": width,
                "height": height,
                "prompt": prompts[idx],
                "variant": idx,
                "format": fmt,
            }
        )
    return visuals, asset_ids, cost, errors


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

@register_skill_handler("design_menu_pack")
async def handle(ctx: SkillContext) -> SkillResult:
    inputs: dict[str, Any] = ctx.inputs or {}
    strategy = inputs.get("strategy") or {}
    if ctx.brand_context.get("brand", {}).get("name"):
        strategy = {**strategy, "name": ctx.brand_context["brand"]["name"]}

    design_system = inputs.get("design_system") or {}
    school = inputs.get("design_school") or design_system.get("school")
    copy = inputs.get("copy") or {}
    cuisine = inputs.get("cuisine") or strategy.get("cuisine") or strategy.get("category")
    fmt = inputs.get("format") or "a4_portrait"
    if fmt not in _FORMAT_DIMS:
        fmt = "a4_portrait"
    mockup_count = max(1, min(5, int(inputs.get("mockup_count", 3))))

    # ---- Step 1: menu structure ----
    menu, menu_cost, menu_err = await _generate_menu(
        ctx, strategy, design_system, copy, cuisine, fmt
    )
    if menu is None:
        return SkillResult(ok=False, error=f"menu: {menu_err}", cost_usd=menu_cost)

    sections = menu.get("sections") or []
    if not isinstance(sections, list):
        sections = []
    section_names = [
        s.get("title") for s in sections
        if isinstance(s, dict) and isinstance(s.get("title"), str)
    ]
    resolved_fmt = menu.get("format") if menu.get("format") in _FORMAT_DIMS else fmt
    size, _ = _FORMAT_DIMS[resolved_fmt]

    total_cost = menu_cost

    # ---- Step 2: mockup renders ----
    prompts = [
        _mockup_prompt(
            idx=i,
            strategy=strategy,
            design_system=design_system,
            fmt=resolved_fmt,
            section_names=section_names,
            school=school,
        )
        for i in range(mockup_count)
    ]
    visuals, asset_ids, render_cost, errors = await _render_mockups(
        ctx=ctx,
        prompts=prompts,
        size=size,
        fmt=resolved_fmt,
    )
    total_cost += render_cost

    if not visuals:
        return SkillResult(
            ok=False,
            error=f"menu mockups failed: {'; '.join(errors)}",
            cost_usd=total_cost,
        )

    await ctx.db.commit()
    return SkillResult(
        ok=True,
        outputs={
            "menu": menu,
            "visuals": visuals,
            "counts": {"mockups": len(visuals), "sections": len(sections)},
            "errors": errors,
        },
        asset_ids=asset_ids,
        cost_usd=total_cost,
    )
