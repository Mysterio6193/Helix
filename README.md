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

## Tech Stack

- Web: Next.js 15, TypeScript, Tailwind CSS, shadcn-style primitives, Framer Motion
- API: FastAPI, Python, async SQLAlchemy
- Database: PostgreSQL with vector search
- Workers: Redis-backed background execution
- Storage: S3-compatible object storage
- Observability: structured logs, traces, metrics, and audit history
- Deployment: Docker and Kubernetes-ready manifests

## Local Development

Prerequisites:

- Node.js 18+ and pnpm 9+
- Python 3.10+
- Docker and Docker Compose

Install dependencies:

```bash
pnpm install
```

Start infrastructure:

```bash
cd infra
docker compose up -d postgres redis minio
cd ..
```

Start the API:

```bash
cd apps/api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn helix.main:app --host 0.0.0.0 --port 8000 --reload
```

Start workers:

```bash
cd apps/api
source venv/bin/activate
python -m apps.workers.run_worker
```

Start the web app:

```bash
cd apps/web
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment

Copy the example environment file and configure the providers you need:

```bash
cp .env.example .env
```

Common variables:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/helix
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GEMINI_API_KEY=...
GITHUB_TOKEN=...
VERCEL_TOKEN=...
TELEGRAM_BOT_TOKEN=...
```

## Product Rule

All implementation foundations are private Helix infrastructure. Product UI,
API descriptions, logs, customer docs, and workflow language should expose only
Helix-native concepts.
