---
name: design_menu_pack
version: 1.0.0
description: >
  When the user wants a printable menu, menu layout, dish copy, or photography
  direction for a food/restaurant brand. Produces a structured menu (sections
  with items, descriptions, prices), a photography brief, and N mockup images
  rendered at print quality.
  Trigger phrases: "menu design", "menu layout", "printable menu", "menu PDF",
  "dish descriptions", "menu copy", "tasting menu", "menu mockup".
inputs:
  strategy: { type: object, required: true }
  design_system: { type: object, required: true }
  copy: { type: object, required: false }
  cuisine: { type: string, required: false, description: "Italian, Mexican, Japanese, etc. Pulled from strategy if omitted." }
  format: { type: string, required: false, default: "a4_portrait", description: "a4_portrait | a4_landscape | tabloid | tri_fold" }
  mockup_count: { type: integer, required: false, default: 3 }
outputs:
  menu: object   # sections[], items[], photography_brief, format
  visuals: array # mockup images
required_tools: [openai_chat, openai_image]
dependencies: [brand_strategy_brief, select_design_school, design_logo]
tags: [menu, print, restaurant, layout, dish-copy]
trigger_phrases:
  - menu design
  - menu layout
  - printable menu
  - menu PDF
  - dish descriptions
  - menu copy
  - tasting menu
  - menu mockup
---

# Design Menu Pack

1. Generate the *structured menu* via `openai_chat` (json_mode):
   - `sections`: ordered array of `{ slug, title, blurb, items[] }` where each
     item is `{ name, description, price, dietary_tags[] }`.
   - `format`: chosen layout (a4_portrait / a4_landscape / tabloid / tri_fold).
   - `photography_brief`: prose direction for any dish photography that would
     accompany the menu (mood, palette discipline, lighting, plating notes).
2. Render `mockup_count` menu mockups via `openai_image` (`1024x1536` for
   portrait, `1536x1024` for landscape). Prompts compose the design system
   palette + typography vibe + chosen format + a sample of the top section
   names. Each mockup becomes `Asset(purpose="menu:mockup", kind="image")`.
3. Return `outputs = { menu: {...}, visuals: [...], counts: { mockups } }`.
