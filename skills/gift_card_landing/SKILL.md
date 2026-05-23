---
name: gift_card_landing
version: 0.1.0
description: >
  Generates a landing page for selling digital gift cards. Trigger phrases: "gift card landing", "buy a gift card", "egift page".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  code: object
required_tools: [openai_chat]
dependencies: [build_restaurant_site]
tags: [web, commerce]
trigger_phrases:
  - gift card landing
  - buy a gift card
  - egift page
---

# Gift Card Landing

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.gift_card_landing` via the `@register_skill_handler("gift_card_landing")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.code` matching the
schema declared above.
