---
name: customer_survey_email
version: 0.1.0
description: >
  Craft email asking for reviews or customer feedback with incentive offers. Trigger phrases: 'feedback survey', 'review request email'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - email
  - marketing
trigger_phrases:
  - feedback survey
  - review request email
---

# Customer Survey Email

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
