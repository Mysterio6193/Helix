---
name: takeout_napkin_design
version: 0.1.0
description: >
  Designs a custom-printed napkin or coaster set. Trigger phrases: "napkin print", "coaster design", "branded napkin".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [select_design_school]
tags: [packaging, print]
trigger_phrases:
  - napkin print
  - coaster design
  - branded napkin
---

# Takeout Napkin Design

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.takeout_napkin_design` via the `@register_skill_handler("takeout_napkin_design")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
