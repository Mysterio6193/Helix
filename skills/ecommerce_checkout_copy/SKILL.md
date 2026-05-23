---
name: ecommerce_checkout_copy
version: 0.1.0
description: >
  Writes microcopy for the full ecommerce checkout flow (cart, address, payment, thank-you). Trigger phrases: "checkout copy", "microcopy", "cart copy".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [ecommerce, ux, copy]
trigger_phrases:
  - checkout copy
  - microcopy
  - cart copy
---

# Ecommerce Checkout Copy

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.ecommerce_checkout_copy` via the `@register_skill_handler("ecommerce_checkout_copy")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
