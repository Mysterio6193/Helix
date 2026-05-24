---
name: brand_positioning_matrix
version: 0.1.0
description: >
  Determine unique selling coordinates relative to four key competitors. Trigger phrases: 'positioning matrix', 'brand coordinates'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - brand
  - operations
trigger_phrases:
  - positioning matrix
  - brand coordinates
---

# Brand Positioning Matrix

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
