---
name: about_page_copy
version: 0.1.0
description: >
  Writes a brand-voice about-page narrative including origin, mission, team, and values. Trigger phrases: "about page", "our story", "brand story".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [web, copy]
trigger_phrases:
  - about page
  - our story
  - brand story
---

# About Page Copy

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.about_page_copy` via the `@register_skill_handler("about_page_copy")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
