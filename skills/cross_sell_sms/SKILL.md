---
name: cross_sell_sms
version: 0.1.0
description: >
  Draft short, impactful cross-sell SMS messages based on purchase history. Trigger phrases: 'cross sell sms', 'text promo'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - sms
  - marketing
trigger_phrases:
  - cross sell sms
  - text promo
---

# Cross Sell Sms

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
