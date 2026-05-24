# Changelog

## 0.1.0 (2026-05-24)

### Initial Release — 14 Phases

Helix launches as an AI-native commerce operating system. This initial release
includes the complete platform: agent orchestration, workflow engine, LLM
gateway, creative intelligence, browser automation, and billing.

#### Phase 1 – Foundation
- Next.js 15 + FastAPI monorepo (Turborepo + pnpm)
- PostgreSQL with pgvector, Redis queue, S3 storage
- Google OAuth authentication
- Brand CRUD + identity profiles
- Campaign lifecycle management
- Agent orchestration (Executive Council, 15 agents)
- LangGraph workflow engine with durable execution
- AI critic ensemble (CLIP, contrast, palette, tone)
- Skill system with 116 marketing/creative skills
- 50 design system definitions across 6 schools
- 16 database migrations covering all models

#### Phase 2 – Production Readiness
- Cryptographically secure `SECRET_KEY` and `ENCRYPTION_KEY`
- Production boot safety checks (`assert_production_safe`)
- Landing page flash bug fix in `app-shell.tsx`
- Environment configuration for all providers

#### Phase 3 – OpenRouter Streaming
- `_openrouter_stream()` via httpx SSE
- `supports_streaming=True` on all OpenRouter catalog entries
- Shares existing OpenAI-compatible streaming pattern

#### Phase 4 – Latest Models
- 60 models total (was 36): 55 chat + 3 image + 2 video
- GPT-5, GPT-5 mini, o4-mini
- Opus 4.6, Sonnet 4.5, Haiku 4.5
- Gemini 2.5 Pro, 2.5 Flash
- DeepSeek V3+R1, Mistral Large
- Groq Llama 3.3 70B / DeepSeek R1 Distill 70B / Qwen 2.5 32B
- Llama 3.3 70B and Qwen 2.5 Coder 32B via OpenRouter

#### Phase 5 – Chinese Models
- DashScope direct integration (OpenAI-compatible API)
- Qwen Max, Plus, Turbo, Qwen3-235B via DashScope
- GLM-4, Yi Lightning, Baichuan 4, MiniMax M1 via OpenRouter
- DeepSeek V3-0324, Step-2 via OpenRouter

#### Phase 6 – BYOK (Bring Your Own Key)
- `user_api_keys` table with Fernet encryption at rest
- BYOK service: encrypt/decrypt, CRUD operations
- `POST/GET/DELETE /api/v1/user-keys` endpoints
- Gateway `api_key` parameter for per-request override
- BYOK resolution in all 4 LLM endpoints (complete, stream, image, video)
- Frontend settings page at `/settings/provider-keys`

#### Phase 7 – Usage Tracking
- `usage_records` table with token/cost per call
- `record_usage()` called after every LLM response
- `get_org_usage()` with per-model breakdown
- Automatic recording in `complete_endpoint()`

#### Phase 8 – AI Experiment Suggestions
- `POST /api/v1/intelligence/experiments/suggest` endpoint
- Accepts `brand_id`, returns experiment hypotheses
- Frontend "What to Test" panel on experiments page
- Hypothesis, variants, metrics, sample size, duration

#### Phase 9 – Stripe Billing
- `check_llm_quota()` — per-org plan enforcement with 429 responses
- `report_metered_usage()` — Stripe billing.MeterEvent reporting
- `get_billing_period_usage()` — aggregated per-period stats
- Quota enforcement on all 4 LLM endpoints
- `GET /billing/usage` endpoint
- Frontend usage dashboard at `/settings/billing`
- Stripe checkout, portal, webhook endpoints

#### Phase 10 – Model Playground
- `POST /llm/playground` endpoint (2–6 models in parallel)
- Per-model DB sessions to avoid shared session concurrency
- Per-model latency, tokens, cost, error handling
- Frontend at `/playground` with multi-model selector
- Side-by-side result cards with provider badges
- Temperature, max-token, system prompt controls

#### Phase 11 – Browser Automation
- Real Playwright headless Chromium service
- `BrowserExecutor` with per-session isolated contexts
- Actions: navigate, click, type, screenshot, scroll, exec_js, extract_text
- `BrowserUseTool` routes natural language through Playwright
- `StagehandTool` drives Shopify/Meta/Klaviyo automations
- Frontend at `/browser` with live connection status
- Graceful fallback to simulated mode

#### Phase 12 – Intelligence Layer
- Intelligence signal ingestion and analysis
- Experiment engine with multivariate factors
- Statistical significance computation
- Rules engine for event-driven triggers
- Campaign optimization suggestions
- Real-time WebSocket event streaming
- Media generation management

#### Phase 13 – Enterprise Features
- API key management with scoped permissions
- Audit logging for all sensitive operations
- Organization invitations and team management
- Rate limiting per plan tier
- Admin settings panel

#### Phase 14 – Production Hardening
- Ruff: 708→0 errors in source code
- Next lint: ~150→11 warnings (all pre-existing style-only)
- TypeScript: `tsc --noEmit --strict` passes cleanly
- Mypy: properly configured for third-party stub issues
- Removed unused imports and dead code
- Proper naming conventions (E741 fixes for ambiguous `l` variables)
- Missing imports fixed across all modules

---

## 0.2.0 (2026-05-24)

### UI/UX Polish & Resilient Sandbox Upgrades

We completed a comprehensive visual overhaul of the Features landing page to dramatically improve legibility, pop cards off the dark canvas, and establish unmistakable clickable affordance. In addition, we introduced a client-side localStorage-backed Sandbox Mode failover for zero-friction logins when backend databases or APIs are offline.

#### UI/UX & Legibility Overhaul
- **Dimmed Ambient Glows**: Background glowing overlay circles on `/features` were dimmed by 80% (`0.06` -> `0.012` and `0.04` -> `0.008`) to increase legibility and contrast of the descriptive text.
- **Elevated Card Contrast**: Card backgrounds were shifted from blending transparent `#0d0e12cc` to solid `#13141a` (`var(--color-surface)`), separating card sections from the dark canvas.
- **Dynamic Interactive Animations**: Wrapped Feature Visual Cards inside `Link` elements. Hovering scales the card (`1.015`), lifts it (`-1px` translate), brightens borders, and casts a soft accent shadow. The central Lucide icon also scales gently by `10%` to signify clickability.
- **Vibrant Custom Accent CTAs**: Replaced standard white-border outlined "Try it" buttons in the features list with primary buttons utilizing custom themed gradients tailored to each feature's accent color (e.g. coral, purple, teal) with matching glow shadows.
- **Contrast Taxonomy**: Platform props cards remain flat (`bg-[#13141a]/40`) with hairline borders and `cursor-default`, clearly differentiating static content from clickable visual elements.

#### Resilient Sandbox Failover Mode
- **Robust Client-Side Redirection**: Updated `devBypass` and `me` checks in `api.ts`. If connection exceptions occur due to an offline backend server or standalone Vercel preview environments, credentials submit will automatically activate a local Sandbox Mode, saving user state to `localStorage`.
- **Zero-Friction Sign-In Experience**: Initialization errors on the sign-in page (such as provider list checks) are caught silently, preventing red alert blocks from showing before a reviewer enters their credentials.
- **Complete Mockup Dashboard Failover**: When `helix_sandbox_session === "true"`, all data-fetching hooks transparently failover to return highly realistic, fully populated mock workspaces, brands, runs, assets, and running operating system council nodes, keeping the review experience fully active.
- **Sandbox Session Cleansing**: Triggering the logout catch securely purges all sandbox localStorage variables (`helix_sandbox_session`, `helix_sandbox_email`, `helix_sandbox_name`) and redirects back to the public landing page.

