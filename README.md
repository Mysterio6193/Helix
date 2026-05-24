<p align="center">
  <img src="assets/banner.png" alt="Helix OS" width="100%">
</p>

# Helix 🧬

<p align="center">
  <a href="https://github.com/Mysterio6193/Helix"><img src="https://img.shields.io/badge/Docs-helix--os.app-F0734A?style=for-the-badge" alt="Documentation"></a>
  <a href="https://github.com/Mysterio6193/Helix/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-purple?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://github.com/Mysterio6193/Helix"><img src="https://img.shields.io/badge/Release-v0.1.0--Alpha-blue?style=for-the-badge" alt="Release"></a>
  <a href="https://github.com/Mysterio6193/Helix"><img src="https://img.shields.io/badge/Architecture-Composed-emerald?style=for-the-badge" alt="Architecture"></a>
</p>

**Helix is an AI-native commerce operating system: an autonomous CMO, creative agency, growth team, and operator behind a unified product surface.**

Unlike traditional prompt playgrounds or generic chatbots, Helix is fully goal-oriented and event-driven. Users define brand identities, API integrations, constraints, and key performance indicators (KPIs). Helix then autonomously plans, renders creative assets, deploys websites, executes marketing campaigns, monitors performance, and continuously optimizes operations using closed-loop learning.

---

## 🎨 Product Surfaces

<table>
<tr>
  <td width="30%"><b>Command Center</b></td>
  <td>Unified AI CMO dashboard to launch workflows, check health, and track brand growth.</td>
</tr>
<tr>
  <td><b>Executive Council</b></td>
  <td>An ensemble of specialized agents collaborating dynamically to review and critique campaigns.</td>
</tr>
<tr>
  <td><b>Campaign Manager</b></td>
  <td>Omnichannel coordinator orchestrating launches across Email, Social, and Storefronts.</td>
</tr>
<tr>
  <td><b>Creative Studio</b></td>
  <td>A live-preview collaborative canvas to critique and refine visual design assets.</td>
</tr>
<tr>
  <td><b>Website Builder</b></td>
  <td>Instant Generation of restaurant and food brand sites deployed directly to <b>Vercel</b>.</td>
</tr>
<tr>
  <td><b>Packaging Workspace</b></td>
  <td>SKU and packaging suite generator creating print-ready label specifications.</td>
</tr>
<tr>
  <td><b>Performance Memory</b></td>
  <td>An evolving vector memory graph storing style presets, past outcomes, and learnings.</td>
</tr>
<tr>
  <td><b>Automations Console</b></td>
  <td>Event-driven timeline triggered by ROAS drops, CTR fatigue, or competitor price changes.</td>
</tr>
</table>

---

## 🚀 Core Capabilities

*   **Persistent Specialist Agents** — Specialized agents for creative design, copywriting, SEO, CRO, research, and web engineering.
*   **Event-Driven Autonomy** — Proactive responses to real-world triggers like declining conversion rates, visual fatigue, and competitor moves.
*   **Durable Workflow Execution** — Composed execution graphs with checkpoints, retries, replayable action logs, and step-by-step inspections.
*   **Creative Intelligence** — Automated aesthetic scoring, visual fatigue detection, layout quality assessments, and style guide consistency.
*   **Closed-Loop Experimentation** — Built-in A/B matrix testing, automated confidence scoring, and smart winner selection rollouts.

---

## ⚙️ Architecture

Helix is organized as a layered, modular system separating user interaction, agent cognition, durable workflows, and third-party integrations:

```text
       ┌─────────────────────────────────────────────────────────┐
       │                 Frontend (Next.js 15)                   │
       └────────────────────────────┬────────────────────────────┘
                                    │ HTTP / SSE
       ┌────────────────────────────▼────────────────────────────┐
       │             Helix API Gateway (FastAPI)                 │
       └────────────────────────────┬────────────────────────────┘
                                    │ Redis Job Queue
       ┌────────────────────────────▼────────────────────────────┐
       │            Helix Distributed Runtime Layer              │
       └────────────────────────────┬────────────────────────────┘
                                    │ Agent Invocation
       ┌────────────────────────────▼────────────────────────────┐
       │        Agent Orchestration Layer (LangGraph)            │
       └────────────────────────────┬────────────────────────────┘
                                    │ Execution Nodes
       ┌────────────────────────────▼────────────────────────────┐
       │            Durable Workflow & Tool Layer                │
       └───────┬────────────────────┬────────────────────┬───────┘
               │                    │                    │
 ┌─────────────▼─────────────┐┌─────▼─────────────┐┌─────▼─────────────┐
 │ Memory & Vector Graph     ││ Media Rendering   ││ External Services │
 │ (PostgreSQL + pgvector)   ││ (Canvas / SVGs)   ││ (Shopify / Stripe)│
 └───────────────────────────┘└───────────────────┘└───────────────────┘
```

### Workspace Model
Organization assets and execution context are nested clean under a single namespace:

```text
Organization
  └── Workspaces
      ├── Brands (Style rules, assets, settings)
      ├── Campaigns (Timelines, active pipelines)
      ├── Assets (Media, generated components)
      ├── Agents (Custom models, instructions)
      ├── Experiments (A/B testing, rollout status)
      ├── Integrations (Shopify, Stripe, Vercel)
      ├── Workflows (Execution DAGs)
      └── Automations (Event triggers)
```

---

## 🤖 Supported Models

Helix features an advanced LLM Gateway supporting **60+ models across 11 major providers**. Users can bring their own API keys via `/settings/provider-keys` for local execution or cloud dispatch.

| Provider | Supported Models |
|----------|------------------|
| **OpenAI** | GPT-5, GPT-5 mini, o4-mini, o3, o3-mini, GPT-4o, o1, DALL-E 3 |
| **Anthropic** | Opus 4.6, Sonnet 4.5, Haiku 4.5 |
| **Google** | Gemini 2.5 Pro, 2.5 Flash, 2.0 Flash, Imagen 3, Veo 2 |
| **DeepSeek** | DeepSeek V3, DeepSeek R1 |
| **OpenRouter** | DeepSeek R1/V3, Llama 3.3 70B, Qwen 2.5 Coder, Mistral Large, etc. |
| **DashScope** | Qwen Max/Plus/Turbo, Qwen3-235B |
| **Groq** | Llama 3.3 70B, DeepSeek R1 Distill 70B, Qwen 2.5 32B |
| **Runway / Replicate** | Gen-3 video generation, custom AI image filters |

---

## 🛠️ Local Development

### Prerequisites
*   Node.js 18+ & `pnpm` 9+
*   Python 3.11+
*   Docker & Docker Compose

### Step 1: Install Dependencies
```bash
pnpm install
```

### Step 2: Spin Up Infrastructure
```bash
cd infra
docker compose up -d postgres redis minio
cd ..
```

### Step 3: Set Up and Run the API
```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp ../../.env.example .env   # Configure with your keys
alembic upgrade head
uvicorn helix.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Run Background Workers
In a separate terminal tab:
```bash
cd apps/api
source .venv/bin/activate
python -m apps.workers.run_worker
```

### Step 5: Start the Web Dashboard
In a separate terminal tab:
```bash
cd apps/web
pnpm dev
```

The system will be accessible locally at **[http://localhost:3000](http://localhost:3000)**.

---

## 📖 Project Documentation

*   **[ARCHITECTURE.md](ARCHITECTURE.md)** — Architectural layout, runtime loops, and design decisions.
*   **[DEPLOY.md](DEPLOY.md)** — Complete production deployment guide (Fly.io, Render, Vercel).
*   **[CONTRIBUTING.md](CONTRIBUTING.md)** — Contribution pathways, PR criteria, and conventions.
*   **[CHANGELOG.md](CHANGELOG.md)** — Core development phases and features history.

---

<p align="center">
  <sub>Built with ❤️ for brands that move at light speed. Licensed under the MIT License.</sub>
</p>
