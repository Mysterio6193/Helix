---
name: abandoned_cart_email
version: 0.1.0
description: >
  Drafts a 3-step abandoned-cart email sequence (T+1h, T+24h, T+72h). Trigger phrases: "abandoned cart", "cart recovery", "cart email".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [ecommerce, email, lifecycle]
trigger_phrases:
  - abandoned cart
  - cart recovery
  - cart email
---

# Abandoned Cart Email

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.abandoned_cart_email` via the `@register_skill_handler("abandoned_cart_email")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
