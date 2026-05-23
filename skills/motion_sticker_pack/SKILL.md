---
name: motion_sticker_pack
version: 0.1.0
description: >
  Designs an Instagram Story / Reels animated sticker pack (5 stickers). Trigger phrases: "sticker pack", "ig stickers", "animated stickers".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [select_design_school, design_logo]
tags: [video, social, motion]
trigger_phrases:
  - sticker pack
  - ig stickers
  - animated stickers
---

# Motion Sticker Pack

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.motion_sticker_pack` via the `@register_skill_handler("motion_sticker_pack")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
