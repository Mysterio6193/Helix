---
name: podcast_cover_art
version: 0.1.0
description: >
  Designs a podcast cover (3000×3000) + episode card template. Trigger phrases: "podcast cover", "podcast art", "episode cover".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [select_design_school, design_logo]
tags: [social, podcast]
trigger_phrases:
  - podcast cover
  - podcast art
  - episode cover
---

# Podcast Cover Art

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.podcast_cover_art` via the `@register_skill_handler("podcast_cover_art")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
