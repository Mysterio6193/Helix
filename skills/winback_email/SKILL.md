---
name: winback_email
version: 0.1.0
description: >
  Drafts a 3-step churn / win-back email sequence for lapsed customers. Trigger phrases: "win-back email", "reactivation email", "churn email".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [lifecycle, email, retention]
trigger_phrases:
  - win-back email
  - reactivation email
  - churn email
---

# Winback Email

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.winback_email` via the `@register_skill_handler("winback_email")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
