"""Handler for skill: design_packaging.

Renders SKU-specific dieline / label artwork using the registered image tool and
persists each variant as an `Asset` row. Designed to be invoked once per SKU by
the packaging_suite workflow (which fans out across SKUs in parallel).
"""
from __future__ import annotations

import asyncio
from typing import Any

from helix.models.workflow import Asset
from helix.skills.base import SkillContext, SkillResult, register_skill_handler
from helix.tools.registry import get_tool

# ---------------------------------------------------------------------------
# SKU catalog — surface + dieline metadata fed into the prompt + Asset metadata.
# Sizes are nominal pixel sizes the image tool can return; print-fidelity dielines
# are produced by post-processing (Phase 11+) but we keep the dieline spec here so
# downstream tooling can lay artwork into print templates without guessing intent.
# ---------------------------------------------------------------------------
_SKU_CATALOG: dict[str, dict[str, Any]] = {
    "pizza_box_12in": {
        "surface": "flat unfolded pizza box top panel, 12 inch",
        "substrate": "B-flute corrugated kraft",
        "print_dims_mm": [305, 305],
        "image_size": "1024x1024",
        "treatment": "1- or 2-color flexographic print, generous negative space, strong centered mark, no photo realism",
    },
    "pizza_box_14in": {
        "surface": "flat unfolded pizza box top panel, 14 inch",
        "substrate": "B-flute corrugated kraft",
        "print_dims_mm": [356, 356],
        "image_size": "1024x1024",
        "treatment": "1- or 2-color flexographic print, generous negative space, strong centered mark, no photo realism",
    },
    "pasta_bowl_kraft": {
        "surface": "kraft pasta bowl wrap, unrolled, with bleed",
        "substrate": "natural kraft paperboard",
        "print_dims_mm": [330, 110],
        "image_size": "1536x1024",
        "treatment": "single accent color band + wordmark + ingredient typography ribbon, warm grain visible",
    },
    "cup_8oz": {
        "surface": "8oz hot coffee cup wrap, unrolled",
        "substrate": "double-wall paper cup stock",
        "print_dims_mm": [205, 80],
        "image_size": "1536x1024",
        "treatment": "compact wordmark + tagline + repeating motif row, designed for circumference seam",
    },
    "cup_12oz": {
        "surface": "12oz hot coffee cup wrap, unrolled",
        "substrate": "double-wall paper cup stock",
        "print_dims_mm": [240, 95],
        "image_size": "1536x1024",
        "treatment": "wordmark + tagline + texture wash, designed for circumference seam",
    },
    "cup_16oz": {
        "surface": "16oz cold drink cup wrap, unrolled, with frosted feel",
        "substrate": "single-wall PP cup",
        "print_dims_mm": [275, 110],
        "image_size": "1536x1024",
        "treatment": "high-contrast wordmark + tagline + iconography band",
    },
    "delivery_bag": {
        "surface": "kraft delivery bag front panel, gusseted",
        "substrate": "100% recycled kraft",
        "print_dims_mm": [280, 320],
        "image_size": "1024x1536",
        "treatment": "vertical lockup, thank-you note typography, gentle outline pattern at base",
    },
    "sticker_pack": {
        "surface": "die-cut sticker sheet, 6 stickers, varied shapes",
        "substrate": "vinyl with matte laminate",
        "print_dims_mm": [210, 297],
        "image_size": "1024x1536",
        "treatment": "playful set: wordmark sticker, mascot/glyph sticker, hot-take quote sticker, circle stamp, pill, square",
    },
    "label_jar": {
        "surface": "jar label, rectangular with rounded corners",
        "substrate": "matte white paper, water-resistant",
        "print_dims_mm": [120, 80],
        "image_size": "1024x1024",
        "treatment": "ingredient-forward editorial layout, hierarchy: brand · product · weight · usage",
    },
    "label_bottle": {
        "surface": "bottle wrap label",
        "substrate": "matte white paper, water-resistant",
        "print_dims_mm": [180, 110],
        "image_size": "1536x1024",
        "treatment": "wordmark left, descriptors right, narrow typographic spine, no ornament",
    },
    "takeaway_carton": {
        "surface": "takeaway noodle/rice carton, unfolded blank",
        "substrate": "white-back kraft, food-safe coating",
        "print_dims_mm": [220, 180],
        "image_size": "1024x1024",
        "treatment": "single-side artwork, large wordmark + light pattern fill, leaves window for instructions stamp",
    },
}


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

def _palette_words(design_system: dict) -> str:
    pal = design_system.get("palette") or {}
    primaries: list[str] = []
    for key in ("ink", "accent", "brand_coral", "brand_blue", "primary", "secondary"):
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
    return "confident, contemporary, grounded"


def _tagline_hint(copy: dict | None) -> str | None:
    if not copy:
        return None
    tags = copy.get("taglines") or {}
    options = tags.get("options") or []
    if isinstance(options, list) and options:
        first = options[0]
        if isinstance(first, dict):
            return first.get("text") or first.get("tagline")
        if isinstance(first, str):
            return first
    return None


def _packaging_prompt(
    *,
    sku: str,
    spec: dict[str, Any],
    strategy: dict,
    design_system: dict,
    school: str | None,
    tagline: str | None,
    variant_seed: int,
) -> str:
    name = strategy.get("name") or "the brand"
    palette = _palette_words(design_system)
    family = _typography_family(design_system)
    mood = _mood_words(strategy)
    school_descriptor = (design_system.get("name") or school or "modern").lower()
    tagline_line = f"Tagline candidate: \"{tagline}\". " if tagline else ""

    return (
        f"Print-ready packaging artwork for a restaurant brand called '{name}'. "
        f"Surface: {spec['surface']}. Substrate: {spec['substrate']}. "
        f"Treatment: {spec['treatment']}. "
        f"Aesthetic: {school_descriptor} ({mood}). "
        f"Typography vibe: {family}. Palette: {palette}. "
        f"{tagline_line}"
        "Composition is flat, top-down, no perspective mockup, no realistic photograph, "
        "no shadows, no model hands, no environmental setting, no extra captions or watermarks. "
        f"Treat the canvas as the unfolded print panel ready for placement on a dieline. "
        f"Variation seed {variant_seed}. Print-ready, crisp edges, balanced negative space."
    )


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

@register_skill_handler("design_packaging")
async def handle(ctx: SkillContext) -> SkillResult:
    image_tool = get_tool("openai_image")
    if image_tool is None:
        return SkillResult(ok=False, error="openai_image tool not registered")

    inputs: dict[str, Any] = ctx.inputs or {}
    sku = str(inputs.get("sku") or "").strip()
    if sku not in _SKU_CATALOG:
        return SkillResult(ok=False, error=f"unknown sku: {sku!r}")

    spec = _SKU_CATALOG[sku]

    strategy = inputs.get("strategy") or {}
    if ctx.brand_context.get("brand", {}).get("name"):
        strategy = {**strategy, "name": ctx.brand_context["brand"]["name"]}

    design_system = inputs.get("design_system") or {}
    school = inputs.get("design_school") or design_system.get("school")
    copy = inputs.get("copy") or {}
    tagline = _tagline_hint(copy)

    variant_count = max(1, min(4, int(inputs.get("variant_count", 2))))

    prompts = [
        _packaging_prompt(
            sku=sku,
            spec=spec,
            strategy=strategy,
            design_system=design_system,
            school=school,
            tagline=tagline,
            variant_seed=i,
        )
        for i in range(variant_count)
    ]
    calls = [
        image_tool.call(prompt=p, size=spec["image_size"], quality="high", n=1)
        for p in prompts
    ]
    results = await asyncio.gather(*calls, return_exceptions=True)

    visuals: list[dict[str, Any]] = []
    asset_ids: list = []
    total_cost = 0.0
    errors: list[str] = []

    for idx, res in enumerate(results):
        if isinstance(res, Exception):
            errors.append(f"variant {idx}: {res!s}")
            continue
        if not res.ok:
            errors.append(f"variant {idx}: {res.error}")
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
            purpose=f"packaging:{sku}",
            kind="image",
            storage_key=s3_key,
            mime_type=data.get("mime_type", "image/png"),
            width=width,
            height=height,
            metadata_={
                "prompt": prompts[idx],
                "model": res.model,
                "variant": idx,
                "sku": sku,
                "dieline": {
                    "substrate": spec["substrate"],
                    "print_dims_mm": spec["print_dims_mm"],
                    "surface": spec["surface"],
                },
            },
        )
        ctx.db.add(asset)
        await ctx.db.flush()
        asset_ids.append(asset.id)
        visuals.append(
            {
                "asset_id": str(asset.id),
                "purpose": f"packaging:{sku}",
                "sku": sku,
                "storage_key": s3_key,
                "width": width,
                "height": height,
                "prompt": prompts[idx],
                "variant": idx,
                "dieline": {
                    "substrate": spec["substrate"],
                    "print_dims_mm": spec["print_dims_mm"],
                    "surface": spec["surface"],
                },
            }
        )

    if not visuals:
        return SkillResult(
            ok=False,
            error=f"all packaging variants for sku={sku} failed: {'; '.join(errors)}",
            cost_usd=total_cost,
        )

    await ctx.db.commit()
    return SkillResult(
        ok=True,
        outputs={"visuals": visuals, "sku": sku, "count": len(visuals)},
        asset_ids=asset_ids,
        cost_usd=total_cost,
    )
