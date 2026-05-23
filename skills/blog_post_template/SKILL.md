---
name: blog_post_template
version: 0.1.0
description: >
  Drafts an SEO-aware blog post template (story, recipe, behind-the-scenes). Trigger phrases: "blog post", "seo article", "content post".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [web, seo, content]
trigger_phrases:
  - blog post
  - seo article
  - content post
---

# Blog Post Template

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.blog_post_template` via the `@register_skill_handler("blog_post_template")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
