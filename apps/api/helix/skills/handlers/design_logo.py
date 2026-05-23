"""Handler for skill: design_logo."""
from __future__ import annotations

import asyncio
from typing import Any

from helix.models.workflow import Asset
from helix.skills.base import SkillContext, SkillResult, register_skill_handler
from helix.tools.registry import get_tool


def _palette_words(design_system: dict) -> str:
    pal = design_system.get("palette") or {}
    primaries = []
    for key in ("ink", "accent", "brand_coral", "brand_blue"):
        v = pal.get(key)
        if isinstance(v, str):
            primaries.append(v)
        elif isinstance(v, list):
            primaries.extend(v[:1])
        if len(primaries) >= 3:
            break
    return ", ".join(primaries) if primaries else "monochrome"


def _typography_family(design_system: dict) -> str:
    typo = design_system.get("typography") or {}
    return typo.get("family_primary") or "geometric sans"


def _logo_prompt(*, strategy: dict, design_system: dict, school: str | None, variant_seed: int) -> str:
    name = strategy.get("name") or "the brand"
    mood = ", ".join(strategy.get("mood") or []) or "considered, contemporary"
    palette = _palette_words(design_system)
    family = _typography_family(design_system)
    school_descriptor = (design_system.get("name") or school or "modern").lower()

    return (
        f"Vector logo lockup for a restaurant called '{name}'. "
        f"Aesthetic: {school_descriptor} ({mood}). "
        f"Typography vibe: {family}. Palette: {palette}. "
        "Centered composition, white background, no extra text, no mockup, no realistic photography, "
        f"variation seed {variant_seed}. Print-ready, clean edges, balanced negative space."
    )


@register_skill_handler("design_logo")
async def handle(ctx: SkillContext) -> SkillResult:
    image_tool = get_tool("openai_image")
    if image_tool is None:
        return SkillResult(ok=False, error="openai_image tool not registered")

    inputs: dict[str, Any] = ctx.inputs or {}
    strategy = inputs.get("strategy", {})
    if ctx.brand_context.get("brand", {}).get("name"):
        strategy = {**strategy, "name": ctx.brand_context["brand"]["name"]}

    design_system = inputs.get("design_system") or {}
    school = inputs.get("design_school")
    variant_count = int(inputs.get("variant_count", 4))

    # Generate variants concurrently
    prompts = [_logo_prompt(strategy=strategy, design_system=design_system, school=school, variant_seed=i) for i in range(variant_count)]
    calls = [
        image_tool.call(prompt=p, size="1024x1024", quality="high", n=1)
        for p in prompts
    ]
    results = await asyncio.gather(*calls, return_exceptions=True)

    visuals: list[dict[str, Any]] = []
    asset_ids: list = []
    total_cost = 0.0
    for idx, res in enumerate(results):
        if isinstance(res, Exception):
            continue
        if not res.ok:
            continue
        total_cost += res.cost_usd or 0.0
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
            purpose="logo",
            kind="image",
            storage_key=s3_key,
            mime_type=data.get("mime_type", "image/png"),
            width=width,
            height=height,
            metadata_={
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
                "purpose": "logo",
                "storage_key": s3_key,
                "width": width,
                "height": height,
                "prompt": prompts[idx],
                "variant": idx,
            }
        )

    if not visuals:
        return SkillResult(ok=False, error="all logo variants failed", cost_usd=total_cost)

    await ctx.db.commit()
    return SkillResult(
        ok=True,
        outputs={"visuals": visuals, "count": len(visuals)},
        asset_ids=asset_ids,
        cost_usd=total_cost,
    )
