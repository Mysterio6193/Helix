---
name: pinterest_pin_pack
version: 0.1.0
description: >
  Designs a 5-pin Pinterest pack with vertical 2:3 visuals and SEO captions. Trigger phrases: "pinterest pin", "pinterest design", "vertical pin".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, openai_chat, s3_storage]
dependencies: [select_design_school]
tags: [social, pinterest]
trigger_phrases:
  - pinterest pin
  - pinterest design
  - vertical pin
---

# Pinterest Pin Pack

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.pinterest_pin_pack` via the `@register_skill_handler("pinterest_pin_pack")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
