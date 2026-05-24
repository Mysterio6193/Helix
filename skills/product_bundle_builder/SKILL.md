---
name: product_bundle_builder
version: 0.1.0
description: >
  Group menu or merchandise inventory items into attractive discounted combos. Trigger phrases: 'product bundle', 'discount combos'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - pricing
  - ecommerce
trigger_phrases:
  - product bundle
  - discount combos
---

# Product Bundle Builder

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
