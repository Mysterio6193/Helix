---
name: klaviyo_flow_segment
version: 0.1.0
description: >
  Construct segment rules for post-purchase winback flows in Klaviyo. Trigger phrases: 'klaviyo flow', 'klaviyo segment'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - marketing
  - ecommerce
trigger_phrases:
  - klaviyo flow
  - klaviyo segment
---

# Klaviyo Flow Segment

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
