---
name: alt_text_generator
version: 0.1.0
description: >
  Auto-generate descriptive alt text for product images to improve search SEO. Trigger phrases: 'image alt text', 'alt description'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - seo
  - image
trigger_phrases:
  - image alt text
  - alt description
---

# Alt Text Generator

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
