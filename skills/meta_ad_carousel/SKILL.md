---
name: meta_ad_carousel
version: 0.1.0
description: >
  Generates a 5-card Meta carousel ad with hook → benefit → benefit → proof → CTA. Trigger phrases: "meta carousel", "facebook carousel", "instagram carousel ad".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat, openai_image]
dependencies: [build_social_pack]
tags: [ads, meta]
trigger_phrases:
  - meta carousel
  - facebook carousel
  - instagram carousel ad
---

# Meta Ad Carousel

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.meta_ad_carousel` via the `@register_skill_handler("meta_ad_carousel")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
