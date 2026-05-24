---
name: brand_voice_benchmark
version: 0.1.0
description: >
  Score brand copy variations against established tone of voice guides. Trigger phrases: 'voice score', 'tone benchmark'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - brand
  - copy
trigger_phrases:
  - voice score
  - tone benchmark
---

# Brand Voice Benchmark

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
