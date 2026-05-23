---
name: wine_bottle_label
version: 0.1.0
description: >
  Designs a wine / spirits front + back bottle label including vintage block. Trigger phrases: "wine label", "bottle label", "spirits label".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [select_design_school, design_logo]
tags: [packaging, beverage, alcohol]
trigger_phrases:
  - wine label
  - bottle label
  - spirits label
---

# Wine Bottle Label

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.wine_bottle_label` via the `@register_skill_handler("wine_bottle_label")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
