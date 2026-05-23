---
name: brand_strategy_brief
version: 1.0.0
description: >
  Produces a brand strategy brief — positioning statement, audience archetype,
  brand voice, mood adjectives, no-go list — from minimal restaurant inputs
  (name, category, cuisine, city, vibe hint).
inputs:
  name: { type: string, required: true }
  category: { type: string, required: false, default: "restaurant" }
  cuisine: { type: string, required: false }
  city: { type: string, required: false }
  audience_hint: { type: string, required: false }
  vibe: { type: string, required: false }
outputs:
  strategy:
    positioning: string
    audience: object
    voice: string
    mood: array
    no_go: array
    keywords: array
  brief: object
required_tools: [openai_chat]
dependencies: []
tags: [strategy, foundation, brand]
trigger_phrases:
  - brand strategy
  - positioning brief
  - who is our brand
---

# Brand Strategy Brief

This skill is the first step in every brand workflow. It establishes positioning,
audience, voice, and mood — the foundation every downstream skill reads from
`SkillContext.brand_context`.

## Prompt approach
1. Read `inputs` (name, category, cuisine, city, audience_hint, vibe).
2. Compose a `system` prompt that asks for a JSON object with keys
   `positioning, audience, voice, mood, no_go, keywords`.
3. Apply any `learnings` prepended as a system preamble.
4. Call `openai_chat` in JSON mode.
5. Return `outputs.strategy = parsed` and `outputs.brief = parsed`.
