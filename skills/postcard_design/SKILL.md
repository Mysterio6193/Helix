---
name: postcard_design
version: 0.1.0
description: >
  Designs a direct-mail postcard with offer + redemption code area. Trigger phrases: "postcard", "direct mail", "mailer".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [select_design_school]
tags: [print, direct mail]
trigger_phrases:
  - postcard
  - direct mail
  - mailer
---

# Postcard Design

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.postcard_design` via the `@register_skill_handler("postcard_design")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
