---
name: food_truck_wrap
version: 0.1.0
description: >
  Designs a full food-truck wrap (driver side, passenger side, rear, hood). Trigger phrases: "food truck wrap", "truck graphics", "vehicle wrap".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  visuals: object
required_tools: [openai_image, s3_storage]
dependencies: [select_design_school, design_logo]
tags: [packaging, vehicle, environmental]
trigger_phrases:
  - food truck wrap
  - truck graphics
  - vehicle wrap
---

# Food Truck Wrap

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.food_truck_wrap` via the `@register_skill_handler("food_truck_wrap")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.visuals` matching the
schema declared above.
