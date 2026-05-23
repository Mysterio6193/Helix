---
name: select_design_school
version: 1.0.0
description: >
  Selects one of the 5 (now 6) visual schools that best fits the brand strategy.
  Returns the chosen school slug + the resolved design-system tokens (palette,
  typography, spacing, radius, motion, components).
inputs:
  strategy: { type: object, required: true }
  brief: { type: object, required: false }
  user_pref_school: { type: string, required: false }
outputs:
  school: string
  design_system: object
  rationale: string
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [art-direction, design-system]
trigger_phrases:
  - pick a design style
  - what visual school
  - art direction
---

# Select Design School

If `user_pref_school` is provided, return it directly. Otherwise:
1. Load all `is_school=True` `DesignSystem` rows from the DB.
2. Compose a prompt with the strategy + each school's `description` + `tags`.
3. Ask the model to choose one slug + give a short rationale.
4. Return the school slug + full tokens dict.
