---
name: holiday_campaign_calendar
version: 0.1.0
description: >
  Plan key ad set, email copy, and discount dates across major holidays. Trigger phrases: 'campaign calendar', 'holiday planning'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - marketing
  - operations
trigger_phrases:
  - campaign calendar
  - holiday planning
---

# Holiday Campaign Calendar

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
