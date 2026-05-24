---
name: competitor_pricing_scraping
version: 0.1.0
description: >
  Conduct scraping operations on competitive sites for price matching indexes. Trigger phrases: 'price matching', 'scrape prices'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - analytics
  - pricing
trigger_phrases:
  - price matching
  - scrape prices
---

# Competitor Pricing Scraping

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
