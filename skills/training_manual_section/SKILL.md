---
name: training_manual_section
version: 0.1.0
description: >
  Drafts one section of a front-of-house / back-of-house training manual in brand voice. Trigger phrases: "training manual", "staff handbook", "training doc".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  doc: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [ops, training]
trigger_phrases:
  - training manual
  - staff handbook
  - training doc
---

# Training Manual Section

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.training_manual_section` via the `@register_skill_handler("training_manual_section")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.doc` matching the
schema declared above.
