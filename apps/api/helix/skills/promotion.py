"""Skill specialization promotion (compounding/learning loop).

When a parent skill has been run for a specific brand and accumulated >= 5 successful
learnings (average critique score >= 8.0), we synthesize a brand-specialized skill
under `skills/_specializations/<skill>_<brand_slug>/SKILL.md` using LLM synthesis
(with a deterministic offline fallback).
"""
from __future__ import annotations

import os
import yaml
import json
import uuid
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix.core.config import get_settings
from helix.core.logging import get_logger
from helix.models.brand import Brand
from helix.models.skill import SkillLearning, SkillRegistry
from helix.skills.loader import sync_registry

log = get_logger("helix.skills.promotion")


async def promote_specialization(
    db: AsyncSession,
    skill_name: str,
    brand_id: uuid.UUID,
) -> SkillRegistry | None:
    """Consolidate brand-specific learnings into a brand-specialized SKILL.md.

    Checks if count >= 5 and average score >= 8.0.
    Returns the newly synced SkillRegistry row, or None if conditions not met.
    """
    settings = get_settings()

    # 1. Fetch the brand
    brand = (
        await db.execute(select(Brand).where(Brand.id == brand_id))
    ).scalar_one_or_none()
    if brand is None:
        log.warning("promote.brand_not_found", brand_id=str(brand_id))
        return None

    # 2. Fetch the parent skill
    parent_skill = (
        await db.execute(select(SkillRegistry).where(SkillRegistry.name == skill_name))
    ).scalar_one_or_none()
    if parent_skill is None:
        log.warning("promote.parent_skill_not_found", skill_name=skill_name)
        return None

    # 3. Query learnings count and average score
    learnings_res = await db.execute(
        select(SkillLearning)
        .where(
            SkillLearning.brand_id == brand_id,
            SkillLearning.skill_id == parent_skill.id,
            SkillLearning.enabled == True
        )
    )
    learnings = list(learnings_res.scalars().all())
    if not learnings:
        return None

    count = len(learnings)
    scores = [l.score for l in learnings if l.score is not None]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    log.info(
        "promote.check_eligibility",
        skill=skill_name,
        brand=brand.name,
        count=count,
        avg_score=avg_score,
    )

    if count < 5 or avg_score < 8.0:
        log.info("promote.not_eligible_yet", count=count, avg_score=avg_score)
        return None

    # 4. Generate specialized skill name
    spec_skill_name = f"{skill_name}_{brand.slug}"

    # 5. Synthesize frontmatter and content
    frontmatter_dict = {
        "name": spec_skill_name,
        "version": "1.0.0",
        "is_specialization": True,
        "parent_skill": skill_name,
        "brand_id": str(brand_id),
        "inputs": parent_skill.inputs,
        "outputs": parent_skill.outputs,
        "required_tools": parent_skill.required_tools,
        "dependencies": parent_skill.dependencies,
        "tags": list(set(parent_skill.tags + ["specialization", brand.slug])),
        "trigger_phrases": parent_skill.trigger_phrases,
    }

    # Extract prompt deltas to inject
    deltas = [l.prompt_delta for l in learnings if l.prompt_delta]
    deltas_str = "\n".join(f"- {d.strip()}" for d in deltas)

    # 6. Perform synthesis using LLM or offline fallback
    if settings.openai_api_key:
        log.info("promote.synthesis_via_openai", skill=spec_skill_name)
        description, instructions = await _synthesize_llm(
            parent_skill=parent_skill,
            brand=brand,
            deltas=deltas,
            settings=settings,
        )
    else:
        log.info("promote.synthesis_fallback_offline", skill=spec_skill_name)
        description = f"Specialized brand variant of {skill_name} tailored for {brand.name}."
        instructions = f"""# {parent_skill.name.replace('_', ' ').title()} - {brand.name}

This is a specialized version of the `{skill_name}` skill, dynamically tailored for the brand **{brand.name}** ({brand.category}).

## Consolidate Brand Guidelines

The system has automatically analyzed successful execution runs and consolidated the following instructions:

{deltas_str}

## Core Parent Guidelines

Please continue to adhere to the core parent instructions:
1. Parse input payload.
2. Adhere to brand strategy under design school: {brand.design_school or "default"}.
3. Produce specified outputs.
"""

    frontmatter_dict["description"] = description

    # 7. Write to skills/_specializations/<skill>_<brand_slug>/SKILL.md
    spec_dir = Path(settings.skills_dir) / "_specializations" / f"{skill_name}_{brand.slug}"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_file = spec_dir / "SKILL.md"

    # Dump as YAML + Markdown
    yaml_part = yaml.safe_dump(frontmatter_dict, sort_keys=False)
    content = f"---\n{yaml_part}---\n\n{instructions.strip()}\n"

    try:
        spec_file.write_text(content, encoding="utf-8")
        log.info("promote.file_written", path=str(spec_file))
    except Exception as exc:
        log.exception("promote.write_failed", path=str(spec_file), error=str(exc))
        return None

    # 8. Sync registry (this registers it in DB + memory and handles dynamic inheritance of handlers)
    await sync_registry(db, reload_handlers=True)

    # 9. Return the newly created registry row
    created_skill = (
        await db.execute(select(SkillRegistry).where(SkillRegistry.name == spec_skill_name))
    ).scalar_one_or_none()
    return created_skill


async def _synthesize_llm(
    parent_skill: SkillRegistry,
    brand: Brand,
    deltas: list[str],
    settings: Any,
) -> tuple[str, str]:
    """Call OpenAI to perform a high-fidelity synthesis of specialized instructions."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    prompt = f"""You are the Helix Creative OS Skill Promoter.
Your job is to synthesize a specialized version of a skill called "{parent_skill.name}" for the brand "{brand.name}" ({brand.category}).
We have accumulated a set of successful prompt deltas/learnings that represent fine-tuning lessons from previous executions of this skill for this brand.

Parent Description:
{parent_skill.description}

Brand Info:
- Name: {brand.name}
- Category: {brand.category}
- Positioning: {brand.positioning}
- Voice: {json.dumps(brand.voice_attributes)}
- Design School: {brand.design_school}

Learnings / Prompt Deltas:
{json.dumps(deltas, indent=2)}

You need to output a JSON object containing:
1. "description": A concise, 2-3 sentence description of the specialized skill tailored for this brand.
2. "instructions": A beautiful, complete, structured Markdown document that will be the body of the new SKILL.md file. This document must seamlessly combine the parent skill's core purposes with the new brand-specific lessons, rules, and style requirements. Be extremely specific, premium, and actionable.

Respond ONLY with valid JSON. Do not include markdown blocks like ```json or anything else.
"""
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional system promotion agent that outputs pure JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2000,
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        desc = data.get("description", f"Specialized brand variant of {parent_skill.name} tailored for {brand.name}.")
        instructions = data.get("instructions", "")
        if not instructions:
            raise ValueError("Empty instructions from LLM")
        return desc, instructions
    except Exception as exc:
        log.exception("promote.llm_synthesis_failed_falling_back_to_offline")
        # Deterministic fallback logic
        desc = f"Specialized brand variant of {parent_skill.name} tailored for {brand.name}."
        deltas_str = "\n".join(f"- {d.strip()}" for d in deltas)
        instructions = f"""# {parent_skill.name.replace('_', ' ').title()} - {brand.name}

This is a specialized version of the `{parent_skill.name}` skill, dynamically tailored for the brand **{brand.name}** ({brand.category}).

## Consolidate Brand Guidelines

The system has automatically analyzed successful execution runs and consolidated the following instructions:

{deltas_str}

## Core Parent Guidelines

Please continue to adhere to the core parent instructions:
1. Parse input payload.
2. Adhere to brand strategy under design school: {brand.design_school or "default"}.
3. Produce specified outputs.
"""
        return desc, instructions
