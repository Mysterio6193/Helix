---
name: transit_ad_concept
version: 0.1.0
description: >
  Concepts a transit ad (subway car / bus side / bus shelter). Trigger phrases: "transit ad", "subway ad", "bus ad".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [brand_strategy_brief]
tags: [ads, ooh, transit]
trigger_phrases:
  - transit ad
  - subway ad
  - bus ad
---

# Transit Ad Concept

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.transit_ad_concept` via the `@register_skill_handler("transit_ad_concept")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
