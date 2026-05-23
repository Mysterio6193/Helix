---
name: nutrition_card
version: 0.1.0
description: >
  Produces a printable nutrition information card for a given dish or menu set. Trigger phrases: "nutrition card", "calorie label", "macros".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  card: object
required_tools: [openai_chat, openai_image]
dependencies: [design_menu_pack]
tags: [restaurant, print, compliance]
trigger_phrases:
  - nutrition card
  - calorie label
  - macros
---

# Nutrition Card

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.nutrition_card` via the `@register_skill_handler("nutrition_card")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.card` matching the
schema declared above.
