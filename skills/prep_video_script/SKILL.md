---
name: prep_video_script
version: 0.1.0
description: >
  Writes a short prep / behind-the-pass video script for the chef. Trigger phrases: "prep video", "behind the pass", "kitchen video script".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  script: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [video, content]
trigger_phrases:
  - prep video
  - behind the pass
  - kitchen video script
---

# Prep Video Script

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.prep_video_script` via the `@register_skill_handler("prep_video_script")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.script` matching the
schema declared above.
