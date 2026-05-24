---
name: facebook_group_welcome
version: 0.1.0
description: >
  Draft warm welcoming templates for new brand community joins. Trigger phrases: 'facebook welcome', 'community welcome'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - social
  - copy
trigger_phrases:
  - facebook welcome
  - community welcome
---

# Facebook Group Welcome

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
