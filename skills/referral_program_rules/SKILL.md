---
name: referral_program_rules
version: 0.1.0
description: >
  Formulate optimized gamified parameters for brand loyalty share loops. Trigger phrases: 'referral program', 'referral rules'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - marketing
  - referrals
trigger_phrases:
  - referral program
  - referral rules
---

# Referral Program Rules

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
