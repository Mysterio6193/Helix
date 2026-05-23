---
name: careers_landing
version: 0.1.0
description: >
  Generates a careers / hiring landing page including open roles + culture section. Trigger phrases: "careers page", "hiring page", "join the team".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  code: object
required_tools: [openai_chat]
dependencies: [build_restaurant_site]
tags: [web, hr]
trigger_phrases:
  - careers page
  - hiring page
  - join the team
---

# Careers Landing

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.careers_landing` via the `@register_skill_handler("careers_landing")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.code` matching the
schema declared above.
