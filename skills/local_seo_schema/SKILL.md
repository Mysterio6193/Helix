---
name: local_seo_schema
version: 0.1.0
description: >
  Generate LocalBusiness schema markup for restaurant/retail sites. Trigger phrases: 'local schema', 'business schema'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - seo
  - schema
trigger_phrases:
  - local schema
  - business schema
---

# Local Seo Schema

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
