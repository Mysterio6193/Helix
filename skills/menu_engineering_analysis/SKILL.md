---
name: menu_engineering_analysis
version: 0.1.0
description: >
  Analyzes a restaurant menu by margin × popularity quadrant (stars, plowhorses, puzzles, dogs) and proposes price / position / description tweaks. Trigger phrases: "menu engineering", "star items", "menu profitability".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  report: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [restaurant, strategy]
trigger_phrases:
  - menu engineering
  - star items
  - menu profitability
---

# Menu Engineering Analysis

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.menu_engineering_analysis` via the `@register_skill_handler("menu_engineering_analysis")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.report` matching the
schema declared above.
