---
name: loyalty_email_sequence
version: 0.1.0
description: >
  Drafts a 4-step loyalty / VIP email program (entry, milestone, anniversary, surprise). Trigger phrases: "loyalty email", "vip email", "milestone email".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [lifecycle, email, retention]
trigger_phrases:
  - loyalty email
  - vip email
  - milestone email
---

# Loyalty Email Sequence

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.loyalty_email_sequence` via the `@register_skill_handler("loyalty_email_sequence")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
