---
name: loyalty_card_design
version: 0.1.0
description: >
  Designs a punch-card / loyalty-stamp card for repeat customer rewards. Trigger phrases: "loyalty card", "punch card", "rewards card".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [design_logo]
tags: [print, retention]
trigger_phrases:
  - loyalty card
  - punch card
  - rewards card
---

# Loyalty Card Design

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.loyalty_card_design` via the `@register_skill_handler("loyalty_card_design")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
