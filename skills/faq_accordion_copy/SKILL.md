---
name: faq_accordion_copy
version: 0.1.0
description: >
  Write pre-emptive Q&As based on typical customer support checkout queries. Trigger phrases: 'faq copy', 'checkout faq'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - web
  - copy
trigger_phrases:
  - faq copy
  - checkout faq
---

# Faq Accordion Copy

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
