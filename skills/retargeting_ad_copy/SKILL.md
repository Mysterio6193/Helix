---
name: retargeting_ad_copy
version: 0.1.0
description: >
  Writes a retargeting ad copy set with abandoned-flow context awareness. Trigger phrases: "retargeting ad", "remarketing copy", "abandoned ad".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [ads, retargeting]
trigger_phrases:
  - retargeting ad
  - remarketing copy
  - abandoned ad
---

# Retargeting Ad Copy

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.retargeting_ad_copy` via the `@register_skill_handler("retargeting_ad_copy")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
