---
name: reservations_page
version: 0.1.0
description: >
  Generates a reservations page with OpenTable / Resy / Tock placeholders. Trigger phrases: "reservations page", "book a table", "reserve page".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  code: object
required_tools: [openai_chat]
dependencies: [build_restaurant_site]
tags: [web, ops]
trigger_phrases:
  - reservations page
  - book a table
  - reserve page
---

# Reservations Page

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.reservations_page` via the `@register_skill_handler("reservations_page")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.code` matching the
schema declared above.
