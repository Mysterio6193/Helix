---
name: brand_color_palette
version: 0.1.0
description: >
  Determine optimized brand palette values matching emotional target school. Trigger phrases: 'brand colors', 'palette creation'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - design
  - brand
trigger_phrases:
  - brand colors
  - palette creation
---

# Brand Color Palette

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
