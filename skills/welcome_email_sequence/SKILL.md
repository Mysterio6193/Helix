---
name: welcome_email_sequence
version: 0.1.0
description: >
  Drafts a 5-step welcome email sequence for new subscribers. Trigger phrases: "welcome series", "welcome flow", "onboarding email".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [lifecycle, email]
trigger_phrases:
  - welcome series
  - welcome flow
  - onboarding email
---

# Welcome Email Sequence

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.welcome_email_sequence` via the `@register_skill_handler("welcome_email_sequence")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
