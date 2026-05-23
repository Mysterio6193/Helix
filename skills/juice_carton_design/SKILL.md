---
name: juice_carton_design
version: 0.1.0
description: >
  Designs a printable juice / cold-press carton wrap with front, back, and side panels. Trigger phrases: "juice carton", "cold press", "carton design".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [select_design_school, design_logo]
tags: [packaging, beverage]
trigger_phrases:
  - juice carton
  - cold press
  - carton design
---

# Juice Carton Design

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.juice_carton_design` via the `@register_skill_handler("juice_carton_design")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
