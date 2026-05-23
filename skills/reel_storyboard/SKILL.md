---
name: reel_storyboard
version: 0.1.0
description: >
  Storyboards a 15-30s Instagram Reel / TikTok with shot-by-shot beats + on-screen text. Trigger phrases: "reel storyboard", "tiktok storyboard", "vertical video".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  storyboard: object
required_tools: [openai_chat]
dependencies: [build_social_pack]
tags: [video, social]
trigger_phrases:
  - reel storyboard
  - tiktok storyboard
  - vertical video
---

# Reel Storyboard

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.reel_storyboard` via the `@register_skill_handler("reel_storyboard")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.storyboard` matching the
schema declared above.
