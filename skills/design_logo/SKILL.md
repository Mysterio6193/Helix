---
name: design_logo
version: 1.0.0
description: >
  Generates N logo variants for the brand using a text-to-image model with a prompt
  composed from the strategy + selected design school tokens. Uploads each variant
  to S3 and registers an Asset row.
inputs:
  strategy: { type: object, required: true }
  design_system: { type: object, required: true }
  design_school: { type: string, required: false }
  variant_count: { type: integer, required: false, default: 4 }
outputs:
  visuals: array
required_tools: [openai_image, s3_storage]
dependencies: [select_design_school, brand_strategy_brief]
tags: [visual, logo]
trigger_phrases:
  - logo
  - identity mark
  - wordmark
---

# Design Logo

1. Compose a logo brief from `strategy` (name, positioning, mood) + design tokens
   (palette, typography family).
2. Generate `variant_count` images via `openai_image` (gpt-image-1).
3. Persist each via `s3_storage` and create an `Asset(kind="image", purpose="logo")` row.
4. Return `outputs.visuals = [{asset_id, purpose, storage_key, width, height, prompt}]`.
