---
name: pinterest_ads
version: 0.1.0
description: >
  Design Promoted Pins and write conversion-optimized copy. Trigger phrases: 'pinterest ads', 'promoted pin'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat, flux_schnell]
dependencies: []
tags:
  - social
  - ads
trigger_phrases:
  - pinterest ads
  - promoted pin
---

# Pinterest Ads

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
