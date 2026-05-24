---
name: reddit_sponsored_posts
version: 0.1.0
description: >
  Draft conversational text and headlines for Reddit campaigns. Trigger phrases: 'reddit ads', 'reddit sponsored'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - social
  - ads
trigger_phrases:
  - reddit ads
  - reddit sponsored
---

# Reddit Sponsored Posts

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
