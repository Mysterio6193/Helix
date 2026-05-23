---
name: gift_box_design
version: 0.1.0
description: >
  Designs a holiday / launch gift-box wrap and insert card set. Trigger phrases: "gift box", "unboxing", "launch box".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [select_design_school]
tags: [packaging, retail]
trigger_phrases:
  - gift box
  - unboxing
  - launch box
---

# Gift Box Design

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.gift_box_design` via the `@register_skill_handler("gift_box_design")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
