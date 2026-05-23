---
name: vendor_outreach_email
version: 0.1.0
description: >
  Drafts an outreach email to a prospective vendor / supplier with brand context. Trigger phrases: "vendor outreach", "supplier email", "wholesale email".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [ops, email]
trigger_phrases:
  - vendor outreach
  - supplier email
  - wholesale email
---

# Vendor Outreach Email

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.vendor_outreach_email` via the `@register_skill_handler("vendor_outreach_email")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
