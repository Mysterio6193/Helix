---
name: meta_ads_lookalike
version: 0.1.0
description: >
  Formulate custom and lookalike audience setups for Meta campaigns. Trigger phrases: 'lookalike audience', 'meta audience'.
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
  - lookalike audience
  - meta audience
---

# Meta Ads Lookalike

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
