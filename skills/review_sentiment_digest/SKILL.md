---
name: review_sentiment_digest
version: 0.1.0
description: >
  Summarizes recent Google / Yelp / TripAdvisor reviews into theme buckets + action items. Trigger phrases: "review digest", "review sentiment", "yelp summary".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  report: object
required_tools: [openai_chat]
dependencies: []
tags: [research, reviews]
trigger_phrases:
  - review digest
  - review sentiment
  - yelp summary
---

# Review Sentiment Digest

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.review_sentiment_digest` via the `@register_skill_handler("review_sentiment_digest")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.report` matching the
schema declared above.
