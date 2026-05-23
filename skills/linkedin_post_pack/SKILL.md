---
name: linkedin_post_pack
version: 0.1.0
description: >
  Writes a pack of 3 brand-voice LinkedIn posts targeting hospitality / industry audience. Trigger phrases: "linkedin post", "industry post", "b2b post".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [social, linkedin]
trigger_phrases:
  - linkedin post
  - industry post
  - b2b post
---

# Linkedin Post Pack

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.linkedin_post_pack` via the `@register_skill_handler("linkedin_post_pack")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
