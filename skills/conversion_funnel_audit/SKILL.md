---
name: conversion_funnel_audit
version: 0.1.0
description: >
  Audit shopping cart checkout funnels for user experience drop-offs. Trigger phrases: 'funnel audit', 'conversion audit'.
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  result: object
required_tools: [openai_chat]
dependencies: []
tags:
  - analytics
  - cro
trigger_phrases:
  - funnel audit
  - conversion audit
---

# Conversion Funnel Audit

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered.
