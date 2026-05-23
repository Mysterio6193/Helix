---
name: supplier_brief
version: 0.1.0
description: >
  Drafts a supplier / co-packer outreach brief explaining the brand and required SKUs. Trigger phrases: "supplier brief", "co-packer brief", "vendor brief".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  doc: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [ops, supply]
trigger_phrases:
  - supplier brief
  - co-packer brief
  - vendor brief
---

# Supplier Brief

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.supplier_brief` via the `@register_skill_handler("supplier_brief")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.doc` matching the
schema declared above.
