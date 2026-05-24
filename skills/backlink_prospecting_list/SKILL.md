---
name: backlink_prospecting_list
version: 0.1.0
description: >
  Identify domain prospects and pitch angles for authority backlink building. Trigger phrases: 'backlink building', 'domain prospecting'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - seo
  - marketing
trigger_phrases:
  - backlink building
  - domain prospecting
---

# Backlink Prospecting List

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
