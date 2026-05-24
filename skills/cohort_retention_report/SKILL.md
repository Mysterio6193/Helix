---
name: cohort_retention_report
version: 0.1.0
description: >
  Analyze and build structured reports on customer retention cohorts. Trigger phrases: 'cohort analysis', 'retention report'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - analytics
  - operations
trigger_phrases:
  - cohort analysis
  - retention report
---

# Cohort Retention Report

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
