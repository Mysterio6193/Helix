---
name: contact_page_design
version: 0.1.0
description: >
  Designs a contact + locations page with hours, phone, embedded map placeholder. Trigger phrases: "contact page", "locations page", "find us page".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  code: object
required_tools: [openai_chat]
dependencies: [build_restaurant_site]
tags: [web, ux]
trigger_phrases:
  - contact page
  - locations page
  - find us page
---

# Contact Page Design

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.contact_page_design` via the `@register_skill_handler("contact_page_design")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.code` matching the
schema declared above.
