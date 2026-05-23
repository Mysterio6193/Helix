---
name: shipping_confirmation_email
version: 0.1.0
description: >
  Drafts a brand-voice shipping confirmation + tracking email. Trigger phrases: "shipping confirmation", "order shipped email", "tracking email".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [ecommerce, email]
trigger_phrases:
  - shipping confirmation
  - order shipped email
  - tracking email
---

# Shipping Confirmation Email

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.shipping_confirmation_email` via the `@register_skill_handler("shipping_confirmation_email")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
