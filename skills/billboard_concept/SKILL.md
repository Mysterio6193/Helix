---
name: billboard_concept
version: 0.1.0
description: >
  Concepts a billboard / OOH (single-image hero + 7-word hook). Trigger phrases: "billboard", "ooh ad", "outdoor ad".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [brand_strategy_brief]
tags: [ads, ooh]
trigger_phrases:
  - billboard
  - ooh ad
  - outdoor ad
---

# Billboard Concept

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.billboard_concept` via the `@register_skill_handler("billboard_concept")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
