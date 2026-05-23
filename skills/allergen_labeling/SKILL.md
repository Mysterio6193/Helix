---
name: allergen_labeling
version: 0.1.0
description: >
  Generates allergen + dietary tag labels for every menu item against EU/US regulatory standards. Trigger phrases: "allergen labels", "dietary tags", "gluten free labels".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  labels: object
required_tools: [openai_chat]
dependencies: [design_menu_pack]
tags: [restaurant, compliance]
trigger_phrases:
  - allergen labels
  - dietary tags
  - gluten free labels
---

# Allergen Labeling

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.allergen_labeling` via the `@register_skill_handler("allergen_labeling")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.labels` matching the
schema declared above.
