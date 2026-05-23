---
name: seasonal_trend_brief
version: 0.1.0
description: >
  Drafts a seasonal trend brief (cravings, dayparts, occasions) for menu / promo planning. Trigger phrases: "seasonal trends", "food trends", "menu trends".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  report: object
required_tools: [openai_chat]
dependencies: []
tags: [research, seasonal]
trigger_phrases:
  - seasonal trends
  - food trends
  - menu trends
---

# Seasonal Trend Brief

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.seasonal_trend_brief` via the `@register_skill_handler("seasonal_trend_brief")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.report` matching the
schema declared above.
