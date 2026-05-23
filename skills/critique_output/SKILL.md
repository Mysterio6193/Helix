---
name: critique_output
version: 1.0.0
description: >
  Critiques a candidate output (copy, visuals, site, social) against the brand
  strategy + design school. Returns a verdict ("accept"|"revise"), a 0-10 score,
  per-dimension findings, and (if revise) `target_branch` so the workflow knows
  which subgraph to re-run.
inputs:
  target: { type: string, required: true }
  strategy: { type: object, required: true }
  design_system: { type: object, required: true }
  candidate: { type: object, required: true }
  max_score: { type: integer, required: false, default: 10 }
outputs:
  verdict: string
  score: number
  findings: array
  target_branch: string
required_tools: [openai_chat]
dependencies: []
tags: [critic, quality-gate]
trigger_phrases:
  - critique
  - quality check
  - review my output
---

# Critique Output

Produce a structured critique. Acceptance bar: score >= 7 across all dimensions
(brand-fit, craft, originality, on-school).
