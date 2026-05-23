"""Consolidated handlers for the 60 previously-stubbed skills.

This module registers every former `helix/skills/_stubs/<name>` manifest with
a real handler. Three factory functions cover the three handler shapes that
appear in this codebase:

  * `make_copy_handler`   — openai_chat + json_mode, returns one structured object
  * `make_image_handler`  — openai_image (+ s3 persistence), returns `visuals[]`
  * `make_hybrid_handler` — openai_chat for copy *and* openai_image for visuals

The registration table at the bottom of the file lists each skill with its
output key, prompt persona, and (for image skills) prompt template and size.
Keeping every stub in one file keeps the diff legible — these are all
restaurant-brand marketing artifacts that share the same brand-context inputs
and the same SkillResult shape.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

from helix.models.workflow import Asset
from helix.skills.base import SkillContext, SkillResult, SkillHandler, register_skill_handler
from helix.tools.registry import get_tool


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _brand_name(ctx: SkillContext) -> str:
    return (
        (ctx.brand_context.get("brand") or {}).get("name")
        or (ctx.inputs.get("strategy") or {}).get("name")
        or "the brand"
    )


def _strategy(ctx: SkillContext) -> dict[str, Any]:
    strat = ctx.inputs.get("strategy") or ctx.brand_context.get("strategy") or {}
    if not isinstance(strat, dict):
        return {}
    name = (ctx.brand_context.get("brand") or {}).get("name")
    if name and not strat.get("name"):
        strat = {**strat, "name": name}
    return strat


def _design_system(ctx: SkillContext) -> dict[str, Any]:
    ds = ctx.inputs.get("design_system") or ctx.brand_context.get("design_system") or {}
    return ds if isinstance(ds, dict) else {}


def _voice(ctx: SkillContext) -> str:
    inp = ctx.inputs or {}
    tone = inp.get("tone") or inp.get("voice")
    if tone:
        return str(tone)
    strat = _strategy(ctx)
    return str(strat.get("voice") or "warm, confident, considered")


def _palette_words(design_system: dict[str, Any]) -> str:
    pal = design_system.get("palette") or {}
    primaries: list[str] = []
    for key in ("ink", "accent", "primary", "brand_coral", "brand_blue", "canvas"):
        v = pal.get(key)
        if isinstance(v, str):
            primaries.append(v)
        elif isinstance(v, list) and v:
            primaries.append(str(v[0]))
        if len(primaries) >= 3:
            break
    return ", ".join(primaries) if primaries else "monochrome"


def _typography_family(design_system: dict[str, Any]) -> str:
    typo = design_system.get("typography") or {}
    return str(typo.get("family_primary") or "geometric sans")


def _mood_words(strategy: dict[str, Any]) -> str:
    mood = strategy.get("mood")
    if isinstance(mood, list) and mood:
        return ", ".join(str(m) for m in mood[:4])
    return "considered, contemporary"


def _school_descriptor(design_system: dict[str, Any], inputs: dict[str, Any]) -> str:
    return str(
        design_system.get("name")
        or inputs.get("design_school")
        or "modern"
    ).lower()


def _compose_brand_payload(ctx: SkillContext, extra: dict[str, Any] | None = None) -> str:
    payload: dict[str, Any] = {
        "brand_name": _brand_name(ctx),
        "strategy": _strategy(ctx),
        "voice": _voice(ctx),
    }
    if extra:
        payload.update(extra)
    overrides = ctx.inputs.get("context_override")
    if isinstance(overrides, dict) and overrides:
        payload["context_override"] = overrides
    return json.dumps(payload, indent=2, default=str)


async def _call_chat_json(
    ctx: SkillContext,
    *,
    system_prompt: str,
    user_content: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
) -> tuple[dict[str, Any] | list[Any] | None, float, str | None]:
    tool = get_tool("openai_chat")
    if tool is None:
        return None, 0.0, "openai_chat tool not registered"
    messages: list[dict[str, str]] = []
    for learn in ctx.learnings:
        if learn:
            messages.append({"role": "system", "content": learn})
    messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_content})
    result = await tool.call(
        messages=messages,
        model=model,
        temperature=temperature,
        json_mode=True,
    )
    if not result.ok:
        return None, result.cost_usd or 0.0, result.error
    text = (
        (result.data or {}).get("content")
        if isinstance(result.data, dict)
        else str(result.data or "")
    )
    try:
        parsed = json.loads(text or "{}")
    except json.JSONDecodeError:
        return None, result.cost_usd or 0.0, "JSON parse failed"
    return parsed, result.cost_usd or 0.0, None


async def _render_images(
    ctx: SkillContext,
    *,
    prompts: list[str],
    purpose: str,
    size: str = "1024x1024",
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
# Factories
# ---------------------------------------------------------------------------

PromptBuilder = Callable[[SkillContext, int], str]


def make_copy_handler(
    *,
    name: str,
    system_prompt: str,
    output_key: str,
    user_extra: dict[str, Any] | None = None,
    temperature: float = 0.7,
    model: str = "gpt-4o-mini",
) -> SkillHandler:
    """Build a chat-only handler that returns `outputs[output_key] = parsed_json`."""

    async def handler(ctx: SkillContext) -> SkillResult:
        parsed, cost, err = await _call_chat_json(
            ctx,
            system_prompt=system_prompt,
            user_content=_compose_brand_payload(ctx, user_extra),
            model=model,
            temperature=temperature,
        )
        if err is not None:
            return SkillResult(ok=False, error=err, cost_usd=cost)
        return SkillResult(ok=True, outputs={output_key: parsed}, cost_usd=cost)

    handler.__name__ = f"handle_{name}"
    return handler


def make_image_handler(
    *,
    name: str,
    purpose: str,
    prompt_builder: PromptBuilder,
    size: str = "1024x1024",
    variant_count: int = 4,
) -> SkillHandler:
    """Build an image-only handler that returns `outputs.visuals = visuals[]`."""

    async def handler(ctx: SkillContext) -> SkillResult:
        count = int(ctx.inputs.get("variant_count") or variant_count)
        prompts = [prompt_builder(ctx, i) for i in range(count)]
        visuals, asset_ids, cost, errors = await _render_images(
            ctx, prompts=prompts, purpose=purpose, size=size
        )
        if not visuals:
            return SkillResult(
                ok=False,
                error="; ".join(errors) or "no visuals produced",
                cost_usd=cost,
            )
        if asset_ids:
            await ctx.db.commit()
        return SkillResult(
            ok=True,
            outputs={"visuals": visuals, "count": len(visuals)},
            asset_ids=asset_ids,
            cost_usd=cost,
            metadata={"errors": errors} if errors else {},
        )

    handler.__name__ = f"handle_{name}"
    return handler


def make_hybrid_handler(
    *,
    name: str,
    copy_system_prompt: str,
    copy_output_key: str,
    purpose: str,
    prompt_builder: PromptBuilder,
    variant_count: int = 3,
    size: str = "1024x1024",
    user_extra: dict[str, Any] | None = None,
) -> SkillHandler:
    """Build a hybrid handler producing both copy *and* visuals."""

    async def handler(ctx: SkillContext) -> SkillResult:
        parsed, copy_cost, err = await _call_chat_json(
            ctx,
            system_prompt=copy_system_prompt,
            user_content=_compose_brand_payload(ctx, user_extra),
        )
        if err is not None:
            return SkillResult(ok=False, error=err, cost_usd=copy_cost)

        count = int(ctx.inputs.get("variant_count") or variant_count)
        prompts = [prompt_builder(ctx, i) for i in range(count)]
        visuals, asset_ids, image_cost, errors = await _render_images(
            ctx, prompts=prompts, purpose=purpose, size=size
        )
        total_cost = copy_cost + image_cost
        if asset_ids:
            await ctx.db.commit()

        outputs: dict[str, Any] = {copy_output_key: parsed, "visuals": visuals}
        if copy_output_key == "visuals":
            # Skill output key collides with visuals; merge under visuals only.
            outputs = {"visuals": visuals, "plan": parsed}

        return SkillResult(
            ok=True,
            outputs=outputs,
            asset_ids=asset_ids,
            cost_usd=total_cost,
            metadata={"errors": errors} if errors else {},
        )

    handler.__name__ = f"handle_{name}"
    return handler


# ---------------------------------------------------------------------------
# Prompt builders for image-only skills
# ---------------------------------------------------------------------------

def _make_print_prompt(
    label: str,
    extra_instructions: str = "",
) -> PromptBuilder:
    def build(ctx: SkillContext, idx: int) -> str:
        strategy = _strategy(ctx)
        design_system = _design_system(ctx)
        palette = _palette_words(design_system)
        family = _typography_family(design_system)
        mood = _mood_words(strategy)
        school = _school_descriptor(design_system, ctx.inputs or {})
        name = strategy.get("name") or _brand_name(ctx)
        return (
            f"{label} for restaurant brand '{name}'. "
            f"Aesthetic: {school} ({mood}). "
            f"Typography vibe: {family}. Palette: {palette}. "
            f"{extra_instructions} "
            "Print-quality, editorial composition, balanced negative space, "
            "no watermarks, no UI chrome, no realistic photography of people "
            f"unless intrinsic to the format. Variation seed {idx}."
        ).strip()

    return build


# Specific prompt builders per image skill --------------------------------------------------

_IMAGE_PROMPTS: dict[str, PromptBuilder] = {
    "bento_box_design": _make_print_prompt(
        "Branded bento box (top-down layout) packaging design",
        "Show compartment layout, branded sleeve band, and ingredient callouts.",
    ),
    "beverage_can_label": _make_print_prompt(
        "12 oz aluminum beverage can label wrap mockup",
        "Show 360° label layout flattened to a rectangle; include name, flavor descriptor, and net volume.",
    ),
    "billboard_concept": _make_print_prompt(
        "Outdoor billboard creative (14:5 aspect, designed for 1024 wide preview)",
        "Headline + brand mark + minimal supporting illustration. High contrast, readable at distance.",
    ),
    "business_card_design": _make_print_prompt(
        "Double-sided business card (3.5x2 inch) layout, both sides shown stacked",
        "Front: brand mark + name + role. Back: contact details + tagline. Premium paper texture.",
    ),
    "flyer_design": _make_print_prompt(
        "A5 single-page promotional flyer for a restaurant launch or event",
        "Hero headline, supporting details, brand mark, and call-to-action zone.",
    ),
    "food_truck_wrap": _make_print_prompt(
        "Side-elevation food-truck vehicle wrap design",
        "Show driver-side panel: bold brand mark, hero dish illustration, service hours band along the wheel arch.",
    ),
    "gift_box_design": _make_print_prompt(
        "Premium gift-box packaging mockup (closed lid, three-quarter view)",
        "Wraparound branded band, foil-stamp logo placement, and ribbon detail.",
    ),
    "gift_card_design": _make_print_prompt(
        "Plastic gift card design (front + back layout)",
        "Front: brand mark + denomination zone. Back: magnetic stripe + redemption terms area.",
    ),
    "jar_label_design": _make_print_prompt(
        "Glass jar product label (250ml) layout, flattened wraparound view",
        "Hero name, flavor descriptor, weight, ingredient strip, certification icons.",
    ),
    "juice_carton_design": _make_print_prompt(
        "Cold-pressed juice carton (12 oz Tetra Pak) label design, unfolded panel layout",
        "Front panel hero, ingredient panel, nutrition panel placeholder area.",
    ),
    "kitchen_label_pack": _make_print_prompt(
        "Kitchen prep label sheet (12-up layout) for date-marking and allergen flagging",
        "Each label has slot for item name, prep date, use-by, initials, allergen icons.",
    ),
    "loyalty_card_design": _make_print_prompt(
        "Pocket loyalty stamp card (CR80 size) — front + back",
        "Front: brand mark + reward statement. Back: 10 stamp slots arranged in a 5x2 grid.",
    ),
    "motion_sticker_pack": _make_print_prompt(
        "Sheet of 6 animated story stickers laid out as a grid (Instagram/TikTok)",
        "Each sticker: short brand phrase or icon, designed to be cut out individually.",
    ),
    "podcast_cover_art": _make_print_prompt(
        "Square 3000x3000 podcast cover art (rendered here as 1024 square)",
        "Bold typographic treatment of show name + host + brand mark. High legibility at thumbnail size.",
    ),
    "postcard_design": _make_print_prompt(
        "5x7 postcard design (front + back)",
        "Front: hero image area + brand mark. Back: address block + message area + stamp box.",
    ),
    "table_tent_design": _make_print_prompt(
        "Tri-fold table-tent card (folded standing display) for in-restaurant promotion",
        "Three visible panels each showing one feature: special dish, loyalty offer, social handle.",
    ),
    "takeout_napkin_design": _make_print_prompt(
        "Branded takeout napkin print design (open flat layout)",
        "Repeating brand mark pattern or single edge-printed logo, suitable for single-color print.",
    ),
    "transit_ad_concept": _make_print_prompt(
        "Subway / bus interior transit-ad creative (11x28 inch aspect)",
        "Bold headline, brand mark, micro-CTA. Designed to be read in 3 seconds.",
    ),
    "tri_fold_brochure": _make_print_prompt(
        "Tri-fold brochure (8.5x11 folded to thirds), outside spread layout",
        "Six panels visible: cover, inside-flap teaser, three info panels, back-panel contact strip.",
    ),
    "wine_bottle_label": _make_print_prompt(
        "Wine bottle label (750ml) — front + back labels shown side by side",
        "Front: variety + producer + vintage placeholder. Back: tasting notes block + barcode area.",
    ),
    "youtube_thumbnail": _make_print_prompt(
        "16:9 YouTube thumbnail (1280x720 aspect, rendered at 1024 wide)",
        "Bold expressive headline + hero subject + brand mark in corner. Designed for mobile legibility.",
    ),
    # hybrid prompt builders
    "pinterest_pin_pack": _make_print_prompt(
        "Tall 2:3 Pinterest pin creative for restaurant brand",
        "Recipe-style or behind-the-scenes hook headline on top third, hero food image dominating, brand mark bottom.",
    ),
    "nutrition_card": _make_print_prompt(
        "Printable nutrition information card for a menu item",
        "Dish name top, structured nutrition facts panel mid, allergen icon strip below, brand mark footer.",
    ),
    "facebook_event_pack": _make_print_prompt(
        "Facebook event cover image (1920x1005 aspect)",
        "Event name, date, location, brand mark — high-contrast, mobile-first composition.",
    ),
    "meta_ad_carousel": _make_print_prompt(
        "Square Meta carousel ad creative card",
        "Single bold visual element per card; suitable to sit in a 5-card sequence (hook, benefit, benefit, proof, CTA).",
    ),
}


# ---------------------------------------------------------------------------
# Copy-skill system prompts
# ---------------------------------------------------------------------------

_COPY_SPEC: dict[str, dict[str, Any]] = {
    "abandoned_cart_email": {
        "persona": "an ecommerce lifecycle copywriter for restaurant DTC brands",
        "schema": (
            "{ messages: [ { step: 1|2|3, send_offset: '+1h'|'+24h'|'+72h', "
            "subject: string, preheader: string, body: string, cta: string } ] }"
        ),
        "rules": "Three steps total, escalating urgency without discounts until step 3.",
    },
    "about_page_copy": {
        "persona": "a senior brand narrative writer",
        "schema": "{ hero: string, origin: string, mission: string, team: string, values: string[], cta: string }",
        "rules": "Voice-aligned. Concrete sensory detail, no clichés.",
    },
    "blog_post_template": {
        "persona": "an SEO-aware long-form food writer",
        "schema": (
            "{ title: string, meta_description: string, h1: string, intro: string, "
            "sections: [ { h2: string, body: string } ], conclusion: string, target_keywords: string[] }"
        ),
        "rules": "Word count 700-1100. Target keywords appear in title, H1, and first paragraph.",
    },
    "ecommerce_checkout_copy": {
        "persona": "a conversion copywriter for restaurant ecommerce checkouts",
        "schema": (
            "{ cart_review: { heading: string, body: string }, "
            "shipping: { heading: string, body: string }, "
            "payment: { heading: string, body: string }, "
            "confirmation: { heading: string, body: string }, "
            "microcopy: { trust_badges: string[], error_states: string[] } }"
        ),
        "rules": "Reduce friction at each step. Trust-building language. No jargon.",
    },
    "google_search_ads": {
        "persona": "a paid-search copywriter",
        "schema": (
            "{ campaigns: [ { intent: string, headlines: string[15], "
            "descriptions: string[4], callouts: string[6], sitelinks: [ { text: string, description: string } ] } ] }"
        ),
        "rules": "Headlines ≤30 chars, descriptions ≤90 chars. Strict character compliance.",
    },
    "linkedin_post_pack": {
        "persona": "a B2B founder voice for restaurant industry posts",
        "schema": (
            "{ posts: [ { angle: string, hook: string, body: string, cta: string, "
            "hashtags: string[], target_audience: string } ] }"
        ),
        "rules": "5 posts. Each ≤1500 chars. First line is a scroll-stopping hook.",
    },
    "loyalty_email_sequence": {
        "persona": "a retention copywriter for restaurant loyalty programs",
        "schema": (
            "{ messages: [ { milestone: string, subject: string, preheader: string, "
            "body: string, reward_callout: string, cta: string } ] }"
        ),
        "rules": "Sequence covers signup → first reward → second visit → re-engagement → VIP tier.",
    },
    "product_page_copy": {
        "persona": "a DTC food brand copywriter",
        "schema": (
            "{ headline: string, subhead: string, hero_paragraph: string, "
            "feature_bullets: string[6], story_block: string, faqs: [ { q: string, a: string } ], "
            "cta_primary: string, cta_secondary: string }"
        ),
        "rules": "Sensory descriptors. Address objections in FAQs. No filler.",
    },
    "push_notification_pack": {
        "persona": "a mobile retention copywriter",
        "schema": (
            "{ notifications: [ { trigger: string, title: string, body: string, "
            "deep_link: string, segment: string } ] }"
        ),
        "rules": "Title ≤30 chars, body ≤90 chars. Include order-status, win-back, and offer triggers.",
    },
    "retargeting_ad_copy": {
        "persona": "a retargeting copywriter",
        "schema": (
            "{ ads: [ { audience: string, primary_text: string, headline: string, "
            "description: string, cta: string } ] }"
        ),
        "rules": "Audiences: site visitors, add-to-cart, viewed-menu, lapsed customers.",
    },
    "shipping_confirmation_email": {
        "persona": "an ecommerce transactional copywriter",
        "schema": (
            "{ subject: string, preheader: string, hero: string, tracking_block: string, "
            "what_to_expect: string, care_instructions: string, cross_sell: { heading: string, body: string }, "
            "support_block: string }"
        ),
        "rules": "Warm, anticipation-building. Include cross-sell only after confirmation block.",
    },
    "shopify_product_description": {
        "persona": "a Shopify-savvy product copywriter",
        "schema": (
            "{ title: string, vendor: string, type: string, tags: string[], "
            "description_html: string, bullets: string[], meta_title: string, meta_description: string }"
        ),
        "rules": "description_html may use <p>, <ul>, <li> only. Tags lowercased, comma-free in array entries.",
    },
    "sms_welcome_flow": {
        "persona": "a conversational SMS copywriter",
        "schema": (
            "{ messages: [ { step: int, delay: string, body: string, reply_handling: string } ] }"
        ),
        "rules": "≤160 chars per message. Include explicit STOP language in step 1.",
    },
    "vendor_outreach_email": {
        "persona": "a restaurant operator writing to suppliers",
        "schema": (
            "{ subject: string, opening: string, body: string, ask: string, "
            "next_step: string, signoff: string }"
        ),
        "rules": "Professional, specific. Reference brand mission. No fluff.",
    },
    "welcome_email_sequence": {
        "persona": "a lifecycle copywriter for new restaurant brand subscribers",
        "schema": (
            "{ messages: [ { step: int, send_offset: string, subject: string, "
            "preheader: string, body: string, cta: string } ] }"
        ),
        "rules": "Five steps. Step 1 immediate; steps 2-5 staggered over 14 days.",
    },
    "winback_email": {
        "persona": "a winback copywriter",
        "schema": (
            "{ subject: string, preheader: string, body: string, "
            "incentive: { type: string, value: string, expires: string }, cta: string }"
        ),
        "rules": "Empathy first; offer only as final element. No guilt-tripping.",
    },
    "allergen_labeling": {
        "persona": "a food-safety compliance specialist (US FDA + EU 1169/2011 conversant)",
        "schema": (
            "{ items: [ { menu_item: string, allergens_present: string[], "
            "may_contain: string[], dietary_tags: string[], notes: string } ], "
            "legend: { allergen_icons: object } }"
        ),
        "rules": "Use the 14 EU regulated allergens. Mark MAY-CONTAIN cross-contact risks separately.",
    },
    "animated_logo_intro": {
        "persona": "a motion designer briefing an animator",
        "schema": (
            "{ duration_sec: number, frames: [ { time: string, action: string, "
            "easing: string, audio_cue: string } ], deliverables: string[] }"
        ),
        "rules": "Target 3-5 seconds. Specify ease curves explicitly.",
    },
    "careers_landing": {
        "persona": "a frontend engineer + HR copywriter",
        "schema": (
            "{ hero: { headline: string, subhead: string, cta_primary: string }, "
            "why_us: string[5], roles: [ { title: string, location: string, type: string, summary: string } ], "
            "process: string[4], jsx_skeleton: string }"
        ),
        "rules": "jsx_skeleton is a React component string with TailwindCSS classes.",
    },
    "competitor_positioning_map": {
        "persona": "a brand strategist running a competitive teardown",
        "schema": (
            "{ axes: { x: { label: string, low: string, high: string }, "
            "y: { label: string, low: string, high: string } }, "
            "competitors: [ { name: string, x: number, y: number, notes: string } ], "
            "gap_analysis: string, recommended_positioning: string }"
        ),
        "rules": "Axes are perceptual (e.g. price vs craft, mass vs niche). Scores -1.0..1.0.",
    },
    "contact_page_design": {
        "persona": "a frontend engineer + UX writer",
        "schema": (
            "{ jsx_skeleton: string, form_fields: [ { name: string, type: string, "
            "validation: string, placeholder: string } ], support_channels: [ { label: string, value: string, hours: string } ], "
            "map_block: { embed_url: string, address: string } }"
        ),
        "rules": "Mobile-first. Validation must include email + phone formats.",
    },
    "food_photography_brief": {
        "persona": "an art director writing a photography brief",
        "schema": (
            "{ shot_list: [ { angle: string, lighting: string, prop_styling: string, "
            "mood: string, hero_dish: string, references: string[] } ], "
            "color_palette: string[], deliverables: string[] }"
        ),
        "rules": "8-12 shots. Include at least one overhead and one editorial 3/4 angle.",
    },
    "gift_card_landing": {
        "persona": "a conversion copywriter + frontend engineer",
        "schema": (
            "{ hero: { headline: string, subhead: string, cta: string }, "
            "denomination_grid: number[], delivery_options: string[], "
            "occasion_blocks: [ { title: string, copy: string } ], "
            "faqs: [ { q: string, a: string } ], jsx_skeleton: string }"
        ),
        "rules": "Include digital + physical delivery options. JSX uses Tailwind.",
    },
    "ideal_customer_profile": {
        "persona": "a product strategist building ICPs",
        "schema": (
            "{ icps: [ { name: string, demographics: string, psychographics: string, "
            "jobs_to_be_done: string[], pains: string[], gains: string[], "
            "preferred_channels: string[], buying_triggers: string[] } ], "
            "anti_personas: [ { name: string, why_not: string } ] }"
        ),
        "rules": "Produce 3 ICPs and 1 anti-persona.",
    },
    "menu_engineering_analysis": {
        "persona": "a restaurant operations analyst applying menu engineering",
        "schema": (
            "{ matrix: [ { item: string, contribution_margin: number, "
            "popularity_index: number, category: 'star'|'plowhorse'|'puzzle'|'dog' } ], "
            "recommendations: [ { item: string, action: string, rationale: string } ], "
            "summary: string }"
        ),
        "rules": "Stars = high margin + high popularity. Provide a specific action per non-star item.",
    },
    "neighborhood_scan": {
        "persona": "a location-strategy researcher for restaurant openings",
        "schema": (
            "{ neighborhood: string, density_stats: object, daypart_analysis: object, "
            "competitor_summary: [ { name: string, format: string, signal: string } ], "
            "opportunity_gaps: string[], recommended_concept_angles: string[] }"
        ),
        "rules": "Cite the daypart signal that supports each opportunity gap.",
    },
    "prep_video_script": {
        "persona": "a kitchen training scriptwriter",
        "schema": (
            "{ title: string, duration_min: number, "
            "shots: [ { time: string, visual: string, voiceover: string, on_screen_text: string } ], "
            "tools_required: string[], safety_callouts: string[] }"
        ),
        "rules": "Specify each cut. Include explicit safety callouts where heat or blades are involved.",
    },
    "reel_storyboard": {
        "persona": "a short-form video director (Instagram Reels / TikTok)",
        "schema": (
            "{ duration_sec: number, hook_sec: number, "
            "frames: [ { time: string, visual: string, on_screen_text: string, audio: string } ], "
            "cta: string, suggested_audio: string }"
        ),
        "rules": "Hook lives in the first 1.5 seconds. Total length 15-30 seconds.",
    },
    "reservations_page": {
        "persona": "a frontend engineer + hospitality UX writer",
        "schema": (
            "{ hero: { headline: string, subhead: string }, "
            "form_fields: [ { name: string, type: string, validation: string } ], "
            "policies: string[], faqs: [ { q: string, a: string } ], jsx_skeleton: string }"
        ),
        "rules": "Form must include party size, dietary notes, date/time. JSX uses Tailwind.",
    },
    "review_sentiment_digest": {
        "persona": "a customer-experience analyst",
        "schema": (
            "{ period: string, sample_size: number, sentiment_score: number, "
            "themes: [ { theme: string, sentiment: 'positive'|'neutral'|'negative', volume: number, sample_quotes: string[] } ], "
            "action_items: string[] }"
        ),
        "rules": "sentiment_score ranges -1..1. Surface at least 5 themes.",
    },
    "seasonal_trend_brief": {
        "persona": "a culinary trend analyst",
        "schema": (
            "{ season: string, macro_trends: [ { trend: string, signal: string, source_type: string } ], "
            "ingredient_spotlights: string[], menu_ideation_angles: string[], merchandising_calendar: [ { week: int, theme: string } ] }"
        ),
        "rules": "Include 8-12 weeks of merchandising. Cite the signal type for each macro trend.",
    },
    "staff_scripts": {
        "persona": "a hospitality training writer",
        "schema": (
            "{ scenarios: [ { situation: string, opening_line: string, recovery_path: string, "
            "escalation_path: string, do_not_say: string[] } ] }"
        ),
        "rules": "Cover greet, upsell, complaint, allergy disclosure, closing.",
    },
    "supplier_brief": {
        "persona": "a procurement operator writing a supplier RFP",
        "schema": (
            "{ overview: string, sourcing_criteria: string[], volume_forecast: object, "
            "quality_standards: string[], certifications_required: string[], commercial_terms: object, evaluation_rubric: object }"
        ),
        "rules": "Quantify volumes. Certifications must be specific (e.g. USDA Organic, MSC).",
    },
    "training_manual_section": {
        "persona": "an operations trainer authoring a manual",
        "schema": (
            "{ section_title: string, learning_objectives: string[], "
            "lessons: [ { title: string, body: string, checks_for_understanding: string[] } ], "
            "assessment: { format: string, passing_criteria: string } }"
        ),
        "rules": "Each lesson ≤500 words. Provide 2-3 CFUs per lesson.",
    },
    "ugc_creator_brief": {
        "persona": "a creator partnerships manager",
        "schema": (
            "{ creator_archetype: string, deliverables: [ { format: string, count: int, specs: string } ], "
            "creative_directions: string[], do_say: string[], do_not_say: string[], "
            "usage_rights: string, timeline: string }"
        ),
        "rules": "Be explicit about usage rights window and platform exclusivities.",
    },
}


_HYBRID_SPEC: dict[str, dict[str, Any]] = {
    "facebook_event_pack": {
        "persona": "a Meta events copywriter",
        "schema": (
            "{ event: { name: string, tagline: string, description: string, "
            "agenda: [ { time: string, item: string } ] }, "
            "ad_copy: { headline: string, primary_text: string, cta: string }, "
            "reminders: [ { offset: string, body: string } ] }"
        ),
        "rules": "Description ≤1000 chars. Reminders cover T-7d, T-1d, T-2h.",
    },
    "meta_ad_carousel": {
        "persona": "a paid social copywriter for Meta carousels",
        "schema": (
            "{ cards: [ { slot: 'hook'|'benefit'|'benefit'|'proof'|'cta', "
            "headline: string, description: string, image_brief: string } ], "
            "primary_text: string, audience: string }"
        ),
        "rules": "Exactly 5 cards in the order hook → benefit → benefit → proof → cta.",
    },
    "nutrition_card": {
        "persona": "a regulated-labels writer (US FDA Nutrition Facts conformant)",
        "schema": (
            "{ dish: string, serving_size: string, calories: number, "
            "macros: { fat_g: number, carbs_g: number, protein_g: number, sodium_mg: number }, "
            "allergens: string[], dietary_tags: string[], ingredients_list: string }"
        ),
        "rules": "Ingredients in descending weight order. Allergens drawn from the FDA major 9.",
    },
    "pinterest_pin_pack": {
        "persona": "a Pinterest content strategist",
        "schema": (
            "{ pins: [ { title: string, description: string, keywords: string[], "
            "alt_text: string, recipe_metadata: object } ] }"
        ),
        "rules": "Produce 6 pins. Keywords are search-optimized; descriptions ≤500 chars.",
    },
}


# ---------------------------------------------------------------------------
# Skill registration table
# ---------------------------------------------------------------------------

# (name, output_key) for every copy-only stub.
_COPY_STUBS: list[tuple[str, str]] = [
    ("abandoned_cart_email", "copy"),
    ("about_page_copy", "copy"),
    ("allergen_labeling", "labels"),
    ("animated_logo_intro", "brief"),
    ("blog_post_template", "copy"),
    ("careers_landing", "code"),
    ("competitor_positioning_map", "report"),
    ("contact_page_design", "code"),
    ("ecommerce_checkout_copy", "copy"),
    ("food_photography_brief", "brief"),
    ("gift_card_landing", "code"),
    ("google_search_ads", "copy"),
    ("ideal_customer_profile", "report"),
    ("linkedin_post_pack", "copy"),
    ("loyalty_email_sequence", "copy"),
    ("menu_engineering_analysis", "report"),
    ("neighborhood_scan", "report"),
    ("prep_video_script", "script"),
    ("product_page_copy", "copy"),
    ("push_notification_pack", "copy"),
    ("reel_storyboard", "storyboard"),
    ("reservations_page", "code"),
    ("retargeting_ad_copy", "copy"),
    ("review_sentiment_digest", "report"),
    ("seasonal_trend_brief", "report"),
    ("shipping_confirmation_email", "copy"),
    ("shopify_product_description", "copy"),
    ("sms_welcome_flow", "copy"),
    ("staff_scripts", "doc"),
    ("supplier_brief", "doc"),
    ("training_manual_section", "doc"),
    ("ugc_creator_brief", "brief"),
    ("vendor_outreach_email", "copy"),
    ("welcome_email_sequence", "copy"),
    ("winback_email", "copy"),
]

# image-only stubs all return outputs.visuals
_IMAGE_STUBS: list[tuple[str, str]] = [
    ("bento_box_design", "packaging"),
    ("beverage_can_label", "packaging"),
    ("billboard_concept", "ooh"),
    ("business_card_design", "identity"),
    ("flyer_design", "print"),
    ("food_truck_wrap", "fleet"),
    ("gift_box_design", "packaging"),
    ("gift_card_design", "identity"),
    ("jar_label_design", "packaging"),
    ("juice_carton_design", "packaging"),
    ("kitchen_label_pack", "operations"),
    ("loyalty_card_design", "identity"),
    ("motion_sticker_pack", "social"),
    ("podcast_cover_art", "audio"),
    ("postcard_design", "print"),
    ("table_tent_design", "print"),
    ("takeout_napkin_design", "packaging"),
    ("transit_ad_concept", "ooh"),
    ("tri_fold_brochure", "print"),
    ("wine_bottle_label", "packaging"),
    ("youtube_thumbnail", "social"),
]

# (name, copy_output_key, purpose)
_HYBRID_STUBS: list[tuple[str, str, str]] = [
    ("facebook_event_pack", "copy", "social"),
    ("meta_ad_carousel", "copy", "ads"),
    ("nutrition_card", "card", "menu"),
    ("pinterest_pin_pack", "visuals", "social"),
]


def _build_copy_system_prompt(skill_name: str) -> str:
    spec = _COPY_SPEC.get(skill_name)
    if spec:
        return (
            f"You are {spec['persona']}. "
            f"Return ONLY a JSON object matching this schema: {spec['schema']}. "
            f"{spec.get('rules', '')} "
            "Match the brand voice provided in the user payload. No commentary, no markdown."
        )
    # Generic fallback for any copy skill without a bespoke spec.
    return (
        "You are a senior copywriter for restaurant brands. "
        f"For the skill '{skill_name}', return ONLY a JSON object whose top level "
        "captures the deliverable as structured fields appropriate to the format. "
        "Match the brand voice provided in the user payload. No commentary."
    )


def _build_hybrid_copy_prompt(skill_name: str) -> str:
    spec = _HYBRID_SPEC.get(skill_name) or _COPY_SPEC.get(skill_name)
    if spec:
        return (
            f"You are {spec['persona']}. "
            f"Return ONLY a JSON object matching this schema: {spec['schema']}. "
            f"{spec.get('rules', '')} "
            "Match the brand voice provided in the user payload. No commentary."
        )
    return _build_copy_system_prompt(skill_name)


# ---------------------------------------------------------------------------
# Register handlers
# ---------------------------------------------------------------------------

for _name, _out_key in _COPY_STUBS:
    register_skill_handler(_name)(
        make_copy_handler(
            name=_name,
            system_prompt=_build_copy_system_prompt(_name),
            output_key=_out_key,
            temperature=0.75 if _out_key in {"copy", "script", "storyboard"} else 0.55,
        )
    )

for _name, _purpose in _IMAGE_STUBS:
    builder = _IMAGE_PROMPTS.get(_name)
    if builder is None:
        # Defensive fallback: generic print prompt
        builder = _make_print_prompt(f"Brand visual asset for skill {_name}")
    register_skill_handler(_name)(
        make_image_handler(
            name=_name,
            purpose=_purpose,
            prompt_builder=builder,
            variant_count=3,
        )
    )

for _name, _copy_key, _purpose in _HYBRID_STUBS:
    builder = _IMAGE_PROMPTS.get(_name)
    if builder is None:
        builder = _make_print_prompt(f"Visual companion for skill {_name}")
    register_skill_handler(_name)(
        make_hybrid_handler(
            name=_name,
            copy_system_prompt=_build_hybrid_copy_prompt(_name),
            copy_output_key=_copy_key,
            purpose=_purpose,
            prompt_builder=builder,
            variant_count=3,
        )
    )
