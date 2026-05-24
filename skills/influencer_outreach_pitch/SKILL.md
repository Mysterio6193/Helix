---
name: influencer_outreach_pitch
version: 0.1.0
description: >
  Compose personalized collab offers for target nano-influencers. Trigger phrases: 'influencer outreach', 'collab pitch'.
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
  - influencer outreach
  - collab pitch
---

# Influencer Outreach Pitch

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
