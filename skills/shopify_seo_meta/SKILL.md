---
name: shopify_seo_meta
version: 0.1.0
description: >
  Generate optimized SEO title tags and meta descriptions for Shopify products. Trigger phrases: 'shopify seo', 'shopify meta'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - seo
  - ecommerce
trigger_phrases:
  - shopify seo
  - shopify meta
---

# Shopify Seo Meta

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
