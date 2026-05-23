---
name: competitor_positioning_map
version: 0.1.0
description: >
  Builds a 2-axis positioning map placing competitors and the brand. Trigger phrases: "positioning map", "competitor map", "perceptual map".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  report: object
required_tools: [openai_chat]
dependencies: []
tags: [research, strategy]
trigger_phrases:
  - positioning map
  - competitor map
  - perceptual map
---

# Competitor Positioning Map

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.competitor_positioning_map` via the `@register_skill_handler("competitor_positioning_map")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.report` matching the
schema declared above.
