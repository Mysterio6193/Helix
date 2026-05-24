---
name: product_launch_email
version: 0.1.0
description: >
  Write persuasive product launch sequences to generate early sales. Trigger phrases: 'launch email', 'new product email'.
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
  - launch email
  - new product email
---

# Product Launch Email

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
