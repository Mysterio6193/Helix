---
name: sms_welcome_flow
version: 0.1.0
description: >
  Drafts a 3-message SMS welcome flow with TCPA / opt-in language. Trigger phrases: "sms welcome", "sms flow", "text welcome".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [lifecycle, sms]
trigger_phrases:
  - sms welcome
  - sms flow
  - text welcome
---

# Sms Welcome Flow

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.sms_welcome_flow` via the `@register_skill_handler("sms_welcome_flow")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
