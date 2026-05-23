---
name: facebook_event_pack
version: 0.1.0
description: >
  Builds a Facebook event listing (banner copy + visual brief + post variants). Trigger phrases: "facebook event", "event listing", "fb event".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat, openai_image]
dependencies: [build_social_pack]
tags: [social, facebook]
trigger_phrases:
  - facebook event
  - event listing
  - fb event
---

# Facebook Event Pack

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.facebook_event_pack` via the `@register_skill_handler("facebook_event_pack")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
