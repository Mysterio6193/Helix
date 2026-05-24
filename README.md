# Helix

Helix is an AI-native commerce operating system: an AI CMO, creative agency,
growth team, and autonomous operator behind one product surface.

Helix is not a chatbot or prompt playground. Users define goals, brands,
integrations, constraints, and KPIs. Helix plans, creates, launches, monitors,
optimizes, and records what it learns.

## Product Surface

- AI CMO command center
- Executive agent council
- Campaign manager
- Creative studio
- Website builder
- Packaging workspace
- Experimentation lab
- Performance memory graph
- Integrations center
- Browser automation console
- AI actions timeline
- Deployment center

## Core Capabilities

- Persistent specialist agents for marketing, creative, revenue, customer,
  lifecycle, SEO, CRO, research, packaging, and web design
- Event-driven autonomy for ROAS drops, CTR decline, fatigue, churn, competitor
  moves, seasonal trends, revenue spikes, and retention changes
- Durable workflow execution with retries, checkpoints, audit history, and
  replayable action logs
- Tool execution across commerce, advertising, productivity, deployment, and
  analytics systems
- Creative intelligence for aesthetic scoring, brand consistency, style memory,
  visual fatigue detection, layout quality, and packaging intelligence
- Performance memory for campaigns, creatives, audiences, offers, experiments,
  customer behavior, competitor actions, hooks, headlines, and outcomes
- Experimentation with A/B matrices, confidence scoring, automated winner
  selection, and rollout control

## Architecture

```text
Frontend
  ↓
Helix API Gateway
  ↓
Helix Runtime Layer
  ↓
Agent Orchestration Layer
  ↓
Workflow Engine
  ↓
Tool Execution Layer
  ↓
Memory + Intelligence Layer
  ↓
Rendering + Media Layer
  ↓
External Tools + APIs
```

## Workspace Model

```text
Organization
  └── Workspaces
      ├── Brands
      ├── Campaigns
      ├── Assets
      ├── Agents
      ├── Experiments
      ├── Integrations
      ├── Workflows
      └── Automations
```

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — System architecture, data flow, layer breakdown, design decisions
- **[DEPLOY.md](DEPLOY.md)** — End-to-end deployment guide (Fly.io, Render, Vercel)
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — Development setup, conventions, PR process
- **[CHANGELOG.md](CHANGELOG.md)** — Release history (14 phases)

## Tech Stack

- **Web**: Next.js 15, TypeScript, Tailwind CSS, shadcn-style primitives, Framer Motion
- **API**: FastAPI, Python 3.11+, async SQLAlchemy, Pydantic
- **Database**: PostgreSQL 16+ with pgvector (vector search)
- **LLM Gateway**: 60 models across 11 providers (OpenAI, Anthropic, Google, OpenRouter, DeepSeek, Groq, Mistral, DashScope, Replicate, Runway, Veo)
- **Workers**: Redis-backed background execution (APScheduler + Redis queue)
- **Storage**: S3-compatible object storage (MinIO local, Cloudflare R2/S3 prod)
- **Agent Framework**: LangGraph with 15 specialized agents and critic ensemble
- **Observability**: Structured logs (structlog), traces (Langfuse), Prometheus metrics, audit history
- **Automation**: Playwright headless Chromium with simulated fallback
- **Billing**: Stripe subscription management with usage-based metering
- **Deployment**: Docker, Kubernetes manifests, Fly.io, Render, Vercel, Railway

## Models

60 models across 11 providers. See `apps/api/helix/llm/catalog.py` for the full catalog.

| Provider | Models |
|----------|--------|
| OpenAI | GPT-5, GPT-5 mini, o4-mini, o3, o3-mini, GPT-4o, o1, DALL-E 3 |
| Anthropic | Opus 4.6, Sonnet 4.5, Haiku 4.5 |
| Google | Gemini 2.5 Pro, 2.5 Flash, 2.0 Flash, Imagen 3, Veo 2 |
| OpenRouter | DeepSeek V3/R1, Llama 3.3 70B, Qwen 2.5 Coder, Mistral Large, Chinese models |
| DashScope | Qwen Max/Plus/Turbo, Qwen3-235B |
| DeepSeek | V3, R1 |
| Groq | Llama 3.3 70B, DeepSeek R1 Distill 70B, Qwen 2.5 32B |
| Replicate | Image generation |
| Runway | Gen-3 video generation |

BYOK: Users can bring their own API keys via `/settings/provider-keys`.

## Local Development

Prerequisites: Node.js 18+, pnpm 9+, Python 3.11+, Docker + Compose

```bash
# 1. Install dependencies
pnpm install

# 2. Start infrastructure
cd infra && docker compose up -d postgres redis minio && cd ..

# 3. Set up the API
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp ../../.env.example .env   # edit with your keys
alembic upgrade head
uvicorn helix.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Start workers (separate terminal)
cd apps/api
source .venv/bin/activate
python -m apps.workers.run_worker

# 5. Start the web app (separate terminal)
cd apps/web
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

## Product Rule

All implementation foundations are private Helix infrastructure. Product UI,
API descriptions, logs, customer docs, and workflow language should expose only
Helix-native concepts.
