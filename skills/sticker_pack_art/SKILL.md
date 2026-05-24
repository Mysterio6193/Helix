---
name: sticker_pack_art
version: 0.1.0
description: >
  Generate illustration assets for customer loyalty sticker packages. Trigger phrases: 'sticker art', 'sticker illustration'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat, flux_schnell]
dependencies: []
tags:
  - design
  - image
trigger_phrases:
  - sticker art
  - sticker illustration
---

# Sticker Pack Art

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
