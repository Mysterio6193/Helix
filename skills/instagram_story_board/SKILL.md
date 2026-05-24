---
name: instagram_story_board
version: 0.1.0
description: >
  Draw story board frames for daily brand Instagram highlights. Trigger phrases: 'story board', 'instagram story'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat, flux_schnell]
dependencies: []
tags:
  - design
  - image
trigger_phrases:
  - story board
  - instagram story
---

# Instagram Story Board

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
