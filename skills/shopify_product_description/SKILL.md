---
name: shopify_product_description
version: 0.1.0
description: >
  Writes a Shopify-formatted product description with structured fields. Trigger phrases: "shopify description", "product description", "pdp shopify".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [ecommerce, shopify]
trigger_phrases:
  - shopify description
  - product description
  - pdp shopify
---

# Shopify Product Description

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.shopify_product_description` via the `@register_skill_handler("shopify_product_description")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
