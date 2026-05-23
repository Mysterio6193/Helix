---
name: animated_logo_intro
version: 0.1.0
description: >
  Briefs a 3s animated logo intro / stinger for social and web headers. Trigger phrases: "logo animation", "logo intro", "sting".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  brief: object
required_tools: [openai_chat]
dependencies: [design_logo]
tags: [video, motion]
trigger_phrases:
  - logo animation
  - logo intro
  - sting
---

# Animated Logo Intro

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.animated_logo_intro` via the `@register_skill_handler("animated_logo_intro")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.brief` matching the
schema declared above.
