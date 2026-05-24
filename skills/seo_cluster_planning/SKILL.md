---
name: seo_cluster_planning
version: 0.1.0
description: >
  Organize blog posts into structured parent-child topical authority clusters. Trigger phrases: 'seo clusters', 'topical clusters'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - seo
  - copy
trigger_phrases:
  - seo clusters
  - topical clusters
---

# Seo Cluster Planning

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
