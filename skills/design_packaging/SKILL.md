---
name: design_packaging
version: 1.0.0
description: >
  When the user wants packaging artwork for a food/restaurant brand — pizza box,
  pasta bowl, coffee cup, delivery bag, sticker pack, label, takeaway carton. Composes
  a SKU-specific prompt from brand strategy + selected design school tokens + (optional)
  approved logo asset, then renders a print-ready label/wrap artwork via the image tool
  and persists an Asset row. Trigger phrases: "packaging", "pizza box", "pasta bowl",
  "coffee cup", "delivery bag", "sticker pack", "label", "takeaway", "carton".
inputs:
  sku: { type: string, required: true, enum: [pizza_box_12in, pizza_box_14in, pasta_bowl_kraft, cup_8oz, cup_12oz, cup_16oz, delivery_bag, sticker_pack, label_jar, label_bottle, takeaway_carton] }
  strategy: { type: object, required: true }
  design_system: { type: object, required: true }
  copy: { type: object, required: false }
  logos: { type: array, required: false, description: "Approved logo asset records from a prior run." }
  variant_count: { type: integer, required: false, default: 2 }
outputs:
  visuals: array
required_tools: [openai_image, s3_storage]
dependencies: [select_design_school, brand_strategy_brief, design_logo]
tags: [packaging, print, food, restaurant]
trigger_phrases:
  - packaging
  - pizza box
  - pasta bowl
  - coffee cup
  - delivery bag
  - sticker pack
  - takeaway carton
  - label
  - jar label
  - bottle label
---

# Design Packaging

1. Resolve the SKU into a dieline spec (substrate, dimensions, key safe-area, dpi target).
2. Compose a prompt from `strategy.name`, `strategy.mood`, `design_system.palette`,
   `design_system.typography.family_primary`, plus the SKU-specific surface description
   ("flat unfolded pizza box top panel", "kraft pasta bowl wrap with bleed", …).
3. Generate `variant_count` images via `openai_image`. Each variant uses a distinct
   composition seed so the critic gets meaningful options.
4. Persist each as `Asset(kind="image", purpose="packaging:<sku>")` with metadata
   carrying the dieline spec + prompt + variant index.
5. Return `outputs.visuals = [{asset_id, purpose, sku, storage_key, width, height,
   prompt, dieline}]`.
