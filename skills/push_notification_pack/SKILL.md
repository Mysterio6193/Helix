---
name: push_notification_pack
version: 0.1.0
description: >
  Drafts a pack of 10 push-notification copy variants by use case. Trigger phrases: "push notification", "push copy", "mobile push".
inputs:
  brand_id: { type: uuid, required: true }
  context_override: { type: object, required: false }
outputs:
  copy: object
required_tools: [openai_chat]
dependencies: [brand_strategy_brief]
tags: [lifecycle, push]
trigger_phrases:
  - push notification
  - push copy
  - mobile push
---

# Push Notification Pack

Stub manifest — no handler bound yet. The orchestrator will refuse to dispatch
this skill until a handler is registered under
`helix.skills.handlers.push_notification_pack` via the `@register_skill_handler("push_notification_pack")`
decorator.

When implemented, this skill should consume the brand foundation context
(via `load_brand_context`) and produce `outputs.copy` matching the
schema declared above.
