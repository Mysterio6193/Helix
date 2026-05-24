---
name: voice_search_optimization
version: 0.1.0
description: >
  Optimize copywriting for conversational voice assistant searches (Siri, Alexa). Trigger phrases: 'voice search seo', 'voice optimization'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - seo
  - copy
trigger_phrases:
  - voice search seo
  - voice optimization
---

# Voice Search Optimization

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
