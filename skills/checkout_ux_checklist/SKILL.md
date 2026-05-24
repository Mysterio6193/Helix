---
name: checkout_ux_checklist
version: 0.1.0
description: >
  Review storefront checkouts against visual hierarchy heuristics. Trigger phrases: 'checkout ux', 'checkout checklist'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - cro
  - design
trigger_phrases:
  - checkout ux
  - checkout checklist
---

# Checkout Ux Checklist

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
