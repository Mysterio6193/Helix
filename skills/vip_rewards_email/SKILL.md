---
name: vip_rewards_email
version: 0.1.0
description: >
  Draft customized reward emails for high-tier loyal customers. Trigger phrases: 'vip email', 'loyalty reward email'.
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
  - vip email
  - loyalty reward email
---

# Vip Rewards Email

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
