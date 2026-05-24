---
name: twilio_cart_recovery
version: 0.1.0
description: >
  Compose urgent and friendly SMS reminders for abandoned shopping carts. Trigger phrases: 'cart sms recovery', 'abandoned sms'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - sms
  - ecommerce
trigger_phrases:
  - cart sms recovery
  - abandoned sms
---

# Twilio Cart Recovery

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
