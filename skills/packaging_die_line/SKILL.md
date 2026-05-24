---
name: packaging_die_line
version: 0.1.0
description: >
  Determine standard box dimensions and print lines for brand boxes. Trigger phrases: 'die line', 'packaging box'.
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
  - die line
  - packaging box
---

# Packaging Die Line

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
