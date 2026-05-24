# Helix Architecture

Helix is an AI-native commerce operating system. This document describes the
system architecture, data flow, and design decisions.

## System Overview

```
                         ┌─────────────────────────────────────┐
                         │         End Users (Browser)         │
                         └────────────────┬────────────────────┘
                                          │ HTTPS
                         ┌────────────────▼────────────────────┐
                         │        Next.js 15 (apps/web)        │
                         │  - App Router pages (22+ routes)    │
                         │  - Server Components + Client       │
                         │  - Tailwind CSS + Framer Motion     │
                         │  - /api/proxy/* rewrites to API     │
                         └────────────────┬────────────────────┘
                                          │
                         ┌────────────────▼────────────────────┐
                         │   FastAPI Gateway (apps/api)        │
                         │   port 8000                         │
                         │   26 route modules under /v1        │
                         └─┬────────┬────────┬────────┬───────┘
                           │        │        │        │
              ┌────────────┘   ┌────┘   ────┘   ─────┘
              ▼                ▼                ▼
   ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
   │ Agent Orchestra  │ │ LLM Gateway  │ │ Billing      │
   │ - LangGraph      │ │ - 60 models  │ │ - Stripe     │
   │ - 15 agents      │ │ - BYOK       │ │ - Quota      │
   │ - Critic system  │ │ - Streaming  │ │ - Metering   │
   └────────┬─────────┘ └──────┬───────┘ └──────────────┘
            │                  │
   ┌────────▼─────────┐ ┌──────▼───────┐
   │ Workflow Engine  │ │ Intelligence │
   │ - Durable exec   │ │ - Analysis   │
   │ - Slices         │ │ - Experiments│
   │ - Retries        │ │ - Triggers   │
   │ - Audit trail    │ │ - Suggestions│
   └────────┬─────────┘ └──────┬───────┘
            │                  │
            ▼                  ▼
   ┌─────────────────────────────────────────────────┐
   │              Persistence Layer                  │
   │  ┌──────────────┐ ┌──────────┐ ┌─────────────┐  │
   │  │ PostgreSQL   │ │  Redis   │ │  S3/MinIO   │  │
   │  │ + pgvector   │ │ queue    │ │ asset store │  │
   │  │ + asyncpg    │ │ cache    │ │ presigned   │  │
   │  └──────────────┘ └──────────┘ └─────────────┘  │
   └─────────────────────────────────────────────────┘
```

## Layer Breakdown

### 1. Frontend (`apps/web/`)

Next.js 15 App Router with 22+ pages organized by domain:

| Path | Page | Purpose |
|------|------|---------|
| `/` | Landing | Marketing homepage |
| `/dashboard` | Dashboard | Main workspace dashboard |
| `/brands` | Brands | Brand management |
| `/campaigns` | Campaigns | Campaign orchestration |
| `/studio` | Creative Studio | Visual content creation |
| `/playground` | Model Playground | Multi-model LLM comparison |
| `/experiments` | Experiments | A/B experiment management |
| `/browser` | Browser Automation | Playwright console |
| `/memory` | Memory Graph | Performance memory visualization |
| `/settings` | Settings | User/org/admin/settings |
| `/workflows` | Workflows | Workflow run history |
| `/websites` | Websites | Website builder |
| `/packaging` | Packaging | Packaging design workspace |
| `/integrations` | Integrations | Third-party connections |

Key patterns:
- Server components for data fetching, client components for interactivity
- `lib/api.ts` — typed API client with method-per-endpoint
- `lib/llm.ts` — LLM-specific client (playground, streaming)
- `lib/live.ts` — WebSocket client for real-time updates
- `components/layout/app-shell.tsx` — Authenticated app shell with sidebar
- `components/layout/marketing-shell.tsx` — Marketing site shell

### 2. API Gateway (`apps/api/helix/api/v1/`)

27 route modules, each a FastAPI `APIRouter`:

| Module | Prefix | Purpose |
|--------|--------|---------|
| `auth.py` | `/v1/auth` | Google OAuth, session management |
| `brands.py` | `/v1/brands` | Brand CRUD, brand profiles |
| `campaigns.py` | `/v1/campaigns` | Campaign lifecycle |
| `workflows.py` | `/v1/workflows` | Workflow execution, history |
| `llm.py` | `/v1/llm` | Chat complete/stream, image/video gen, playground |
| `billing.py` | `/v1/billing` | Stripe checkout, usage, webhooks |
| `intelligence.py` | `/v1/intelligence` | Signals, analysis, experiments, suggestions |
| `browser.py` | `/v1/browser` | Playwright sessions and actions |
| `memory.py` | `/v1/memory` | Brand memory, lineage, timeline |
| `assets.py` | `/v1/assets` | Asset CRUD, upload, presigned URLs |
| `integrations.py` | `/v1/integrations` | OAuth flows, connection status |
| `enterprise.py` | `/v1/enterprise` | API keys, audit logs, teams |
| `user_keys.py` | `/v1/user-keys` | BYOK provider key management |
| `skills.py` | `/v1/skills` | Skill registry, execution |
| `media.py` | `/v1/media` | Image/video generation and management |
| `events.py` | `/v1/events` | Event bus, webhook delivery |
| `mcp.py` | `/v1/mcp` | MCP tool protocol support |
| `public.py` | `/public` | Unauthenticated platform stats |
| `websocket.py` | `/v1/ws` | WebSocket connections |
| `sessions.py` | `/v1/sessions` | User session management |
| `organizations.py` | `/v1/orgs` | Organization CRUD |
| `workspaces.py` | `/v1/workspaces` | Workspace management |
| `runs.py` | `/v1/runs` | Workflow run detail |
| `telegram.py` | `/v1/telegram` | Telegram bot integration |
| `operating_system.py` | `/v1/os` | System-level operations |
| `design_systems.py` | `/v1/design-systems` | Design system management |

### 3. Agent Orchestration (`apps/api/helix/agents/`)

LangGraph-based agent system with 15 specialized agents:

```
Executive Council (coordinator)
├── Creative Director
├── Copywriter
├── Visual Designer
├── Brand Strategist
├── Menu Designer
├── Packaging Designer
├── Social Producer
├── Web Builder
├── Launch Manager
└── Critic (quality gate)
```

Each agent has:
- A system prompt defining its role and constraints
- Access to specialized tools
- Memory of brand context and past decisions
- Ability to delegate to sub-agents via the council

The critic ensemble (`apps/api/helix/critics/`) provides automated quality scoring:
- **CLIP scorer** — visual aesthetic quality
- **Contrast/a11y** — accessibility compliance
- **Palette scorer** — color harmony and brand consistency
- **Tone classifier** — copy voice consistency
- **Ensemble** — aggregates all scores into a quality metric

### 4. Workflow Engine (`apps/api/helix/workflows/`)

Durable workflow execution with:

- **State machine**: Each run progresses through defined states with checkpoints
- **Retry policy**: Configurable retries with exponential backoff
- **Audit trail**: Every action logged with timestamps
- **Event-driven triggers**: Workflows can start from events (ROAS drop, CTR decline, etc.)
- **Slices**: Reusable workflow components (brand identity, launch campaign, menu design, packaging suite, social pack, website suite, boardroom suite)

### 5. LLM Gateway (`apps/api/helix/llm/`)

Multi-provider abstraction layer:

```
gateway.py
├── _openai_chat() / _openai_stream()
├── _anthropic_chat() / _anthropic_stream()
├── _gemini_chat() / _gemini_stream()
├── _openrouter_chat() / _openrouter_stream()
├── _deepseek_chat() / _deepseek_stream()
├── _groq_chat()
├── _mistral_chat()
├── _dashscope_chat() / _dashscope_stream()
├── _replicate_image()
└── complete_endpoint()  # orchestrates the above
```

**60 models** across 11 providers:
- OpenAI: GPT-5, GPT-5 mini, o4-mini, o3, o3-mini, GPT-4o, GPT-4o-mini, o1, DALL-E 3
- Anthropic: Opus 4.6, Sonnet 4.5, Haiku 4.5
- Google: Gemini 2.5 Pro, 2.5 Flash, 2.0 Flash, Imagen 3
- OpenRouter: DeepSeek V3/R1, Llama 3.3 70B, Qwen 2.5 Coder 32B, Mistral Large
- DashScope: Qwen Max, Plus, Turbo, Qwen3-235B
- DeepSeek: V3, R1
- Groq: Llama 3.3 70B, DeepSeek R1 Distill, Qwen 2.5 32B
- Plus Chinese models: GLM-4, Yi Lightning, Baichuan 4, MiniMax M1, Step-2
- Image: DALL-E 3, Imagen 3, Replicate
- Video: Runway Gen-3, Google Veo 2

BYOK (Bring Your Own Key) allows users to use their own provider API keys instead of the server's.

### 6. Intelligence Layer (`apps/api/helix/intelligence/`)

Autonomous analysis and optimization:

- **Analysis**: Tracks brand performance, campaign metrics, creative fatigue
- **Experiments**: Full A/B testing with multivariate factor analysis, confidence scoring, and automated winner selection
- **Triggers**: Event-driven rules (revenue spike, competitor move, seasonal trend)
- **Suggestions**: AI-generated experiment suggestions based on brand context
- **Stats**: Statistical computation for experiment significance

### 7. Browser Automation (`apps/api/helix/services/browser_executor.py`)

Real Playwright integration:

- Headless Chromium with per-session isolated contexts
- Actions: navigate, click, type, screenshot, scroll, exec_js, extract_text
- `BrowserUseTool` — routes natural language instructions through Playwright
- `StagehandTool` — drives Shopify/Meta/Klaviyo page automation
- Graceful fallback to simulated mode when Playwright/Chromium unavailable

### 8. Tool Adapter System (`apps/api/helix/tools/`)

A scalable tool adapter architecture powering **76+ real API integrations**:

```
tools/
├── adapters/
│   ├── messaging.py         # Slack, Discord, WhatsApp, Meta Pages, Instagram
│   ├── restaurant.py        # Toast, Square, DoorDash, UberEats, Yelp
│   ├── marketing.py         # Mailchimp, HubSpot, SendGrid, Google Business
│   ├── social.py            # Twitter/X, PostHog, Threads, TikTok, Pinterest
│   ├── productivity_extra.py # Airtable, Linear, Asana, Calendly
│   ├── analytics_extra.py   # Mixpanel, Resy, OpenTable
│   ├── new_integrations.py  # 25 adapters: Salesforce, Zendesk, Google Ads, etc.
│   ├── pos_systems.py      # Petpooja, Clover, Lightspeed, Revel, ChowNow, Ordermark, Slice
│   ├── zoho.py             # Zoho CRM, Books, Campaigns, Desk, Inventory, Subscriptions, Projects
│   ├── mcp_server.py       # JSON-RPC 2.0 MCP server (SSE + stdio transports)
│   ├── saas.py             # Shopify, Stripe, Klaviyo, Meta Ads, LinkedIn, etc.
│   ├── image.py            # Flux, SDXL, OpenAI image generation
│   ├── llm.py              # OpenAI, Anthropic, Gemini, OpenRouter chat
│   ├── productivity.py     # Notion, Figma, Gmail, Canva, Web search
│   └── deploy.py           # GitHub, Vercel deployment tools
├── registry.py             # Tool registration and discovery
└── bootstrap.py            # Startup registration of all built-in tools
```

**Consistent Adapter Pattern** — every tool follows:
1. `_resolve_creds(session, workspace_id, provider)` — resolve credentials from DB
2. Validate credentials exist (return clear "not connected" error if missing)
3. Make real HTTP API call to the provider
4. Return `ToolResult` with `ok=True/False` and data or error message

**No mocks, no synthetic data** — every adapter either makes a real API call or fails with a clear "X not connected" error. Zero silent degradation.

### 9. Integration Health Monitoring (`apps/api/helix/services/integration_health.py`)

Health check service that verifies every connected integration with real API probes:
- Per-provider health check definitions (lightweight API calls)
- `GET /integrations/health` endpoint returns per-provider status (healthy/expired/error)
- `last_health_check` and `health_status` stored on connection metadata
- Frontend shows health badges: green (healthy), yellow (expired), red (error)

### 10. MCP Protocol Server (`apps/api/helix/tools/adapters/mcp_server.py`)

Model Context Protocol implementation for AI client tool access:
- **JSON-RPC 2.0** protocol compliance
- **SSE transport** (`SseMcpTransport`) — server-sent events for remote clients (e.g., IDEs)
- **Stdio transport** (`StdioMcpTransport`) — stdin/stdout for local clients (e.g., Claude Desktop)
- Tool listing + calling via the tool registry
- Singleton `get_mcp_server()` factory — transport is a lifecycle choice

### 11. Database Model (`apps/api/helix/models/`)

21 SQLAlchemy models across 16 migrations:

| Model Group | Tables | Purpose |
|-------------|--------|---------|
| Organization | `User`, `Organization`, `Workspace` | Multi-tenant structure |
| Brand | `Brand`, `BrandMemory`, `BrandProfile`, `BrandAssets` | Brand identity |
| Campaign | `Campaign`, `CampaignVersion`, `CampaignResult` | Campaigns |
| Workflow | `WorkflowRun`, `WorkflowStep`, `WorkflowState` | Execution |
| Asset | `Asset`, `AssetVersion`, `Generation` | Media assets |
| Billing | `Subscription`, `Invoice`, `Plan` | Stripe billing |
| Intelligence | `IntelligenceSignal`, `Experiment`, `ExperimentVariant`, `Factor` | AI analysis |
| Enterprise | `ApiKey`, `AuditLog`, `OrganizationInvitation` | Enterprise features |
| Browser | `BrowserSession`, `BrowserAction` | Automation |
| Usage | `UsageRecord`, `UserApiKey` | Tracking + BYOK |

### 9. Workers (`apps/workers/`)

Background task execution via Redis queue:

- `run_worker.py` — Main worker (runs workflows)
- `intelligence_worker.py` — Processes intelligence signals
- `optimization_worker.py` — Runs optimization jobs
- `sweeper.py` — Cleans up stale sessions/data
- `health.py` — Worker health checks

## Data Flow: End-to-End Request

```
1. Browser → Next.js server component renders page
2. Client component → api.ts client → /api/proxy/... → FastAPI
3. FastAPI router → dependency injection (auth, DB session, rate limit)
4. Route handler → service layer → LLM gateway / workflow engine / DB
5. LLM gateway → provider API → usage tracking → response
6. Response → serialization → HTTP response → browser
```

## Key Design Decisions

- **Server-holds-keys by default**: The server is pre-configured with provider API keys. Users can optionally BYOK to use their own keys.
- **Streaming via SSE**: All chat providers stream via Server-Sent Events. Images/video return URLs.
- **Usage tracking fires async**: `record_usage()` runs after the response is sent, never blocking.
- **BYOK keys encrypted at rest**: Fernet symmetric encryption using the server's `ENCRYPTION_KEY`.
- **Critic scores run offline**: Brand creation triggers async critic scoring — results are stored and surfaced later.
- **Workflows are durable**: Each step persists state. Crashes resume from last checkpoint.
- **Playwright is optional**: Falls back to simulated mode if Chromium isn't installed.
- **B008 in FastAPI**: `Depends()` in default arguments is the correct FastAPI pattern, intentionally allowed.

## Authentication Flow

```
1. User clicks "Sign in with Google"
2. Redirect to Google OAuth → callback → exchange code for tokens
3. Upsert user in DB → create session cookie (signed with SECRET_KEY)
4. `require_user` dependency extracts user from cookie on every request
5. ACL checks: user → org → workspace → resource permissions
```

## Monorepo Structure

```
helix/
├── apps/
│   ├── api/          # Python FastAPI backend (helix/)
│   │   ├── helix/
│   │   │   ├── api/          # 27 route modules under /v1
│   │   │   ├── tools/        # Tool adapter system (76+ adapters)
│   │   │   ├── agents/       # LangGraph agent orchestration (15 agents)
│   │   │   ├── llm/          # LLM gateway (60+ models, 11 providers)
│   │   │   ├── services/     # Business logic + health checks
│   │   │   └── models/       # 21 SQLAlchemy models
│   ├── web/          # Next.js 15 frontend
│   └── workers/      # Background workers
├── packages/
│   ├── types/        # Shared TypeScript types
│   └── vendor/       # Vendored third-party packages
├── skills/           # 116 marketing/creative skills (SKILL.md each)
├── design-systems/   # 50 design system definitions
├── infra/            # Docker, Kubernetes, Postgres configs
└── deploy-gcp.sh     # GCP deployment script
```
