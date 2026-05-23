---
name: beverage_can_label
version: 0.1.0
description: >
  Designs a slim or sleek beverage can wrap (355ml / 250ml) with regulatory panel. Trigger phrases: "can label", "beverage can", "seltzer can".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [design_logo]
tags: [packaging, beverage]
trigger_phrases:
  - can label
  - beverage can
  - seltzer can
---

# Beverage Can Label

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.beverage_can_label` via the `@register_skill_handler("beverage_can_label")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
