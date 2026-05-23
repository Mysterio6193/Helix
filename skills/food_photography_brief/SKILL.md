---
name: food_photography_brief
version: 0.1.0
description: >
  Produces a shot list for food photography including dish-level lighting, props, angles, and brand mood references. Trigger phrases: "photo brief", "food photography", "shot list".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  brief: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief, select_design_school]
tags: [restaurant, photography]
trigger_phrases:
  - photo brief
  - food photography
  - shot list
---

# Food Photography Brief

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.food_photography_brief` via the `@register_skill_handler("food_photography_brief")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.brief` matching the
schema declared above.
