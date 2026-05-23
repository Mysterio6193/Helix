---
name: table_tent_design
version: 0.1.0
description: >
  Designs a printable table tent advertising a happy hour / special / event. Trigger phrases: "table tent", "tabletop card", "happy hour signage".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [select_design_school]
tags: [restaurant, print]
trigger_phrases:
  - table tent
  - tabletop card
  - happy hour signage
---

# Table Tent Design

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.table_tent_design` via the `@register_skill_handler("table_tent_design")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
