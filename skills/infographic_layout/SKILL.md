---
name: infographic_layout
version: 0.1.0
description: >
  Design layouts for structural data visualization infographics. Trigger phrases: 'infographic', 'data visualization'.
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
  - infographic
  - data visualization
---

# Infographic Layout

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
