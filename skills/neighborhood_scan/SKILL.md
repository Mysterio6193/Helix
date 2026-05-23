---
name: neighborhood_scan
version: 0.1.0
description: >
  Profiles the brand's neighborhood (foot traffic, comparable concepts, anchors, gaps). Trigger phrases: "neighborhood scan", "location scan", "trade area".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  report: object
required_tools: [openai_chat]
dependencies: []
tags: [research, location]
trigger_phrases:
  - neighborhood scan
  - location scan
  - trade area
---

# Neighborhood Scan

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.neighborhood_scan` via the `@register_skill_handler("neighborhood_scan")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.report` matching the
schema declared above.
