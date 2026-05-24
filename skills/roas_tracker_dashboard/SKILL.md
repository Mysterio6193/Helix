---
name: roas_tracker_dashboard
version: 0.1.0
description: >
  Extract campaign performance and summarize Return on Ad Spend. Trigger phrases: 'roas tracking', 'roas dashboard'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - analytics
  - ads
trigger_phrases:
  - roas tracking
  - roas dashboard
---

# Roas Tracker Dashboard

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
