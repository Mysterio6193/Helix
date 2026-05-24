---
name: meta_lead_ads
version: 0.1.0
description: >
  Build high-converting forms and headlines for Facebook Lead Ads. Trigger phrases: 'facebook lead ads', 'meta lead gen'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - social
  - ads
trigger_phrases:
  - facebook lead ads
  - meta lead gen
---

# Meta Lead Ads

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
