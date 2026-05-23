---
name: flyer_design
version: 0.1.0
description: >
  Designs a single-page promotional flyer for an event or grand opening. Trigger phrases: "flyer", "event flyer", "grand opening flyer".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [select_design_school]
tags: [print, marketing]
trigger_phrases:
  - flyer
  - event flyer
  - grand opening flyer
---

# Flyer Design

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.flyer_design` via the `@register_skill_handler("flyer_design")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
