---
name: ugc_creator_brief
version: 0.1.0
description: >
  Writes a UGC creator brief (do / don't, hooks, deliverables, talking points). Trigger phrases: "ugc brief", "creator brief", "influencer brief".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  brief: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [video, ugc, influencer]
trigger_phrases:
  - ugc brief
  - creator brief
  - influencer brief
---

# Ugc Creator Brief

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.ugc_creator_brief` via the `@register_skill_handler("ugc_creator_brief")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.brief` matching the
schema declared above.
