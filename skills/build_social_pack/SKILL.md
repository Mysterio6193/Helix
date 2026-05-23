---
name: build_social_pack
version: 1.0.0
description: >
  When the user wants social content for a food/restaurant brand — Instagram
  feed grid, launch carousel, story templates, highlight covers, hashtags, or
  posting calendar. Builds a publishable social pack: per-platform caption set,
  N feed tiles + 3 story templates rendered via image tool, hashtag families,
  and a 14-day posting cadence.
  Trigger phrases: "social pack", "instagram", "IG", "tiktok", "carousel",
  "story template", "feed tiles", "captions", "hashtag", "launch posts".
inputs:
  strategy: { type: object, required: true }
  design_system: { type: object, required: true }
  copy: { type: object, required: false, description: "Tagline options carry into captions." }
  platforms: { type: array, required: false, default: ["instagram", "tiktok"] }
  post_count: { type: integer, required: false, default: 9, description: "Number of feed tiles to render." }
  story_count: { type: integer, required: false, default: 3 }
outputs:
  plan: object
  visuals: array
required_tools: [openai_chat, openai_image]
dependencies: [brand_strategy_brief, select_design_school, design_logo, generate_taglines]
tags: [social, instagram, tiktok, captions, marketing]
trigger_phrases:
  - social pack
  - instagram
  - IG
  - tiktok
  - carousel
  - story template
  - feed tiles
  - launch posts
  - captions
  - hashtag
---

# Build Social Pack

1. Generate the *plan* via `openai_chat` (json_mode):
   - `captions`: array of `{ slot, hook, body, cta, hashtags[] }` — one per
     feed tile.
   - `hashtags`: `{ core[], local[], occasion[] }` — pre-segmented hashtag
     families the brand can mix.
   - `bio`: `{ instagram, tiktok }` — 150-char bio strings per platform.
   - `cadence`: 14-day posting plan — `[{ day, slot, post_idx, note }]`.
2. Render `post_count` feed tile images via `openai_image` (1024×1024) using
   prompts composed from the design system palette + strategy mood + caption
   hook. Each tile becomes an `Asset(purpose="social:feed", kind="image")`.
3. Render `story_count` story-template images (1024×1536, 9:16) for reusable
   announcement / quote / countdown frames. Each becomes
   `Asset(purpose="social:story", kind="image")`.
4. Return `outputs = { plan: {...}, visuals: [...], counts: { feed, story } }`.
