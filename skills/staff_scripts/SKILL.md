---
name: staff_scripts
version: 0.1.0
description: >
  Drafts greeter / server / phone scripts in brand voice (greet, upsell, recover, close). Trigger phrases: "staff scripts", "server script", "phone script".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  doc: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [ops, training]
trigger_phrases:
  - staff scripts
  - server script
  - phone script
---

# Staff Scripts

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.staff_scripts` via the `@register_skill_handler("staff_scripts")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.doc` matching the
schema declared above.
