---
name: tri_fold_brochure
version: 0.1.0
description: >
  Designs a tri-fold brochure with about / menu / contact panels. Trigger phrases: "tri-fold brochure", "brochure", "pamphlet".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [select_design_school]
tags: [print, collateral]
trigger_phrases:
  - tri-fold brochure
  - brochure
  - pamphlet
---

# Tri Fold Brochure

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.tri_fold_brochure` via the `@register_skill_handler("tri_fold_brochure")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
