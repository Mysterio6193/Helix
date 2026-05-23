---
name: google_search_ads
version: 0.1.0
description: >
  Writes Google search ad variants (RSA: 15 headlines + 4 descriptions). Trigger phrases: "google ads", "search ads", "rsa ads".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [ads, google, search]
trigger_phrases:
  - google ads
  - search ads
  - rsa ads
---

# Google Search Ads

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.google_search_ads` via the `@register_skill_handler("google_search_ads")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
