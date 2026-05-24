---
name: press_kit_curation
version: 0.1.0
description: >
  Assemble media assets, high-res logo links, and brand brief copy for PR kits. Trigger phrases: 'press kit', 'media kit'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - brand
  - pr
trigger_phrases:
  - press kit
  - media kit
---

# Press Kit Curation

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
