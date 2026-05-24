---
name: newsletter_weekly
version: 0.1.0
description: >
  Compose engaging weekly newsletters with custom product highlights. Trigger phrases: 'weekly newsletter', 'email newsletter'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - email
  - marketing
trigger_phrases:
  - weekly newsletter
  - email newsletter
---

# Newsletter Weekly

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
