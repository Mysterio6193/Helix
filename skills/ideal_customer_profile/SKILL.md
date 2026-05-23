---
name: ideal_customer_profile
version: 0.1.0
description: >
  Drafts an ICP / persona deck for the brand's 3 highest-LTV segments. Trigger phrases: "icp", "persona", "customer profile".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  report: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [research, strategy]
trigger_phrases:
  - icp
  - persona
  - customer profile
---

# Ideal Customer Profile

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.ideal_customer_profile` via the `@register_skill_handler("ideal_customer_profile")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.report` matching the
schema declared above.
