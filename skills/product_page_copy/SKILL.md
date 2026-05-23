---
name: product_page_copy
version: 0.1.0
description: >
  Writes ecommerce product-page copy (hero, benefits, ingredients, FAQs). Trigger phrases: "product page copy", "pdp copy", "ecommerce description".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [ecommerce, copy]
trigger_phrases:
  - product page copy
  - pdp copy
  - ecommerce description
---

# Product Page Copy

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.product_page_copy` via the `@register_skill_handler("product_page_copy")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
