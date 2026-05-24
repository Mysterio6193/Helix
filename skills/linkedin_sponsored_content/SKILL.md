---
name: linkedin_sponsored_content
version: 0.1.0
description: >
  Draft professional lead-gen posts for sponsored B2B campaigns. Trigger phrases: 'linkedin sponsor', 'sponsored content'.
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
  - linkedin sponsor
  - sponsored content
---

# Linkedin Sponsored Content

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
