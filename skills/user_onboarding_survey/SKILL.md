---
name: user_onboarding_survey
version: 0.1.0
description: >
  Draft interactive post-sign-up customer segmentation surveys. Trigger phrases: 'onboarding survey', 'user segmentation survey'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - onboarding
  - copy
trigger_phrases:
  - onboarding survey
  - user segmentation survey
---

# User Onboarding Survey

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
