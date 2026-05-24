---
name: press_release_pitch
version: 0.1.0
description: >
  Write a compelling press release highlighting a major brand milestone. Trigger phrases: 'press release', 'pr pitch'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - pr
  - copy
trigger_phrases:
  - press release
  - pr pitch
---

# Press Release Pitch

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
