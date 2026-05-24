---
name: sms_flash_sale
version: 0.1.0
description: >
  Craft copy and schedule parameters for high-urgency flash sale texts. Trigger phrases: 'flash sale sms', 'sms promo'.
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
  - flash sale sms
  - sms promo
---

# Sms Flash Sale

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
