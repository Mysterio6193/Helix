---
name: kitchen_label_pack
version: 0.1.0
description: >
  Designs a printable kitchen-label set (prep date, allergen flag, station tag). Trigger phrases: "kitchen labels", "prep labels", "station labels".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [select_design_school]
tags: [ops, print]
trigger_phrases:
  - kitchen labels
  - prep labels
  - station labels
---

# Kitchen Label Pack

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.kitchen_label_pack` via the `@register_skill_handler("kitchen_label_pack")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
