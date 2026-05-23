---
name: generate_taglines
version: 1.0.0
description: Generate tagline options that fit brand strategy + voice.
inputs:
  strategy: { type: object, required: true }
  brief: { type: object, required: false }
  count: { type: integer, required: false, default: 6 }
  tone: { type: string, required: false, default: "warm-confident" }
outputs:
  options: array
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [copy, taglines]
trigger_phrases:
  - taglines
  - slogans
  - hooks
---

# Generate Taglines

Produce N tagline options (default 6). Each option is `{text, length_words, angle}`.
Avoid clichés enumerated in `strategy.no_go`. Match the brand `voice`.
