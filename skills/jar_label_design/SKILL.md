---
name: jar_label_design
version: 0.1.0
description: >
  Designs a jar wrap label (sauces / preserves / pickles) with neckband. Trigger phrases: "jar label", "sauce label", "pickle jar label".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [design_logo]
tags: [packaging, retail]
trigger_phrases:
  - jar label
  - sauce label
  - pickle jar label
---

# Jar Label Design

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.jar_label_design` via the `@register_skill_handler("jar_label_design")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
