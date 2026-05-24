---
name: tiktok_spark_ads
version: 0.1.0
description: >
  Generate hook script and target profile for Spark Ads. Trigger phrases: 'spark ads', 'tiktok hook'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - social
  - ads
trigger_phrases:
  - spark ads
  - tiktok hook
---

# Tiktok Spark Ads

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
