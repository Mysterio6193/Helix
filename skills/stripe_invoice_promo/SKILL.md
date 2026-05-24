---
name: stripe_invoice_promo
version: 0.1.0
description: >
  Inject promotional codes and coupons into customer invoice templates. Trigger phrases: 'invoice promo', 'stripe coupons'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - billing
  - ecommerce
trigger_phrases:
  - invoice promo
  - stripe coupons
---

# Stripe Invoice Promo

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
