---
name: value_proposition_slogan
version: 0.1.0
description: >
  Synthesize a core five-word value statement for storefront headers. Trigger phrases: 'value proposition', 'brand slogan'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - brand
  - copy
trigger_phrases:
  - value proposition
  - brand slogan
---

# Value Proposition Slogan

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
