---
name: packaging_box_insert
version: 0.1.0
description: >
  Draft thank-you inserts with loyalty coupon codes for delivery boxes. Trigger phrases: 'box insert', 'thank you card'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - design
  - packaging
trigger_phrases:
  - box insert
  - thank you card
---

# Packaging Box Insert

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
