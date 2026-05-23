# Helix Creative OS — AI-Native Creative Operating System

<div align="center">
  <img src="apps/web/public/logo.svg" alt="Helix Logo" width="80" height="80" style="margin-bottom: 20px;" />
  <p><strong>The Autonomous AI CMO for Restaurants & Food Brands</strong></p>
  
  <p>
    <a href="https://nextjs.org"><img src="https://img.shields.io/badge/Next.js-15.0.3-black?logo=next.js" alt="Next.js" /></a>
    <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.115-teal?logo=fastapi" alt="FastAPI" /></a>
    <a href="https://langchain-ai.github.io/langgraph/"><img src="https://img.shields.io/badge/LangGraph-Durable_Agents-blue" alt="LangGraph" /></a>
    <a href="https://tailwindui.com"><img src="https://img.shields.io/badge/Tailwind_CSS-v4-38bdf8?logo=tailwind-css" alt="Tailwind" /></a>
  </p>
</div>

---

Helix is not a chatbot. It is a highly composable **AI-Native Creative Operating System** that functions as an autonomous **AI CMO** for restaurants, cafes, and food brands. It maps complex creative and campaign strategies into durable, deterministic **LangGraph workflow slices** operated by a cooperative network of 9 specialized agents. 

Every workflow slice—from packaging SKU design to website generation and live Vercel deployments—is guided by a **persistent, compounding brand memory graph** that grows smarter with each run.

---

## 🌌 Inspired Aesthetics (Higgsfield Redesign)
Helix's unauthenticated surface experience has been completely overhauled to match the high-fidelity visual signature of **Higgsfield** and **OpenAI**:
* **Cinematic Mux HLS Looping Background**: The homepage features a gorgeous full-screen looping Mux streaming video background (`https://stream.mux.com/8wrHPCX2dC3msyYU9ObwqNdm00u3ViXvOSHUMRYSEe5Q.m3u8`). It runs under a CSS backdrop blur at `opacity-[0.25]` with saturation and brightness filters to achieve a premium deep-space aesthetic. It utilizes a **dynamic cross-browser script loader** that automatically attaches the `Hls.js` client on non-Safari browsers (Chrome, Firefox, Edge).
* **High-Fidelity Solar Eclipse Backdrops**: The `/sign-in` and `/sign-up` portals are framed by a high-end glowing crescent moon eclipse backdrop, dynamic starry skies, and custom geometric mountain ridge SVGs.
* **Credentials Developer Bypass Portal**: Rapid developer sandbox testing is enabled via a smooth glassmorphic credential accordion. Clicking it lets anybody instantly generate mock accounts and bypass OAuth logins in local non-production environments.
* **Password Validation Checklist**: The sign-up portal provides a dynamic, real-time checklist that reactive-checks input criteria (numbers, length, cases) and animates successful green check states in real-time as you type.

---

## 🏗 System Architecture

Helix is built as a highly robust, multi-tier system designed to orchestrate cooperative agents and durable workflows:

```
                  ┌─────────────────────────────────────────┐
                  │          Next.js 15 Frontend            │
                  │   TypeScript, Tailwind v4, shadcn/ui    │
                  └────────────────────┬────────────────────┘
                                       │ WebSocket / REST HTTP
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │       FastAPI API Gateway (Async)       │
                  │   Alembic, SQLAlchemy 2.0, PostgreSQL    │
                  └────────────┬───────────────────┬────────┘
                               │                   │
                     Run Queue │                   │ Event Streams
                               ▼                   ▼
                  ┌──────────────────────┐   ┌──────────────────────┐
                  │  Celery Worker Node  │   │  Langfuse Analytics  │
                  │ (LangGraph Executor) │   │ (Observability Spans)│
                  └────────────┬─────────┘   └──────────────────────┘
                               │
                               ▼
            ┌──────────────────────────────────────┐
            │   9 Specialized Cooperative Agents   │
            │   (Orchestrator, Designer, Critic...)│
            └────────────┬────────────────────┬────┘
                         │                    │
                         ▼                    ▼
            ┌────────────────────────┐   ┌────────────────────────┐
            │      Memory Layer      │   │    Tools & Adapters    │
            │ pgvector Semantic FTS  │   │ OpenAI, Gemini, Vercel │
            └────────────────────────┘   └────────────────────────┘
```

### Reference Foundations & Design Patterns
* **[Hermes Agent](https://github.com/NousResearch/hermes-agent)** — Architected the agent runtime loop, in-memory tool registries, and sync-to-async thread-safe loop bridges.
* **[MarketingSkills](https://github.com/coreyhaines31/marketingskills)** — Inspired the SKILL.md YAML-frontmatter manifest contract, permitting developers to declare inputs, outputs, and trigger phrases in structured markdown.
* **[open-design](https://github.com/nexu-io/open-design)** — Governs the 5 visual schools and 50 pre-curated restaurant brand tokens (typography, color palettes, spacing rhythm) to enforce design-system alignment.

---

## 👥 The 9 Specialized Agents

Inside the **Agent Runtime**, nine autonomous agents coordinate using LangGraph to execute workflows:
1. **Orchestrator Agent** — Analyzes the active slice context, maps task dependencies, and coordinates execution.
2. **Visual Designer Agent** — Builds visual assets, defines typography scales, and generates color palettes.
3. **Copywriter Agent** — Drafts high-converting, brand-voice-compliant menus, descriptions, emails, and ads.
4. **Copy Editor Agent** — Proofreads and refines text assets to strip AI signatures and enforce tone guides.
5. **Creative Director Agent** — Reviews composition, audits color harmony, and ensures layout consistency.
6. **Web Builder Agent** — Scaffolds multi-page Next.js components, designs layouts, and structures HTML5 sections.
7. **Critic / Reviewer Agent** — Runs closed-loop evaluation, critiquing drafts against brand strategy briefs.
8. **Memory Retriever Agent** — Semantic-queries historical workflow runs to inject contextual learning into the graph.
9. **Observer / Observability Agent** — Autonomously measures span costs, latency, and tokens via Langfuse.

---

## ⚡ The 6 Workflow Slices

Every slice executes a full-stack, durable creative loop backed by structured input/output schemas:

| Workflow Slice | Key Capabilities | Output Artifacts |
|---|---|---|
| **Brand Identity** | URL parsing, positioning briefs, voice matrices, and color preset tokens. | Structured Brand Profile, Palette, Font scales |
| **Packaging Suite** | SKU layout generation with bleed, margin, and typography constraints. | Pizza boxes, cups, takeaway bags, jar labels |
| **Next.js Websites**| Page generation, Tailwind theme baking, GitHub commits, Vercel deployments. | Live website project URLs, GitHub repos |
| **Social Media Pack**| Aspect-ratio assets generation (1:1, 9:16), aspect filtering, and calendars. | Instagram tiles, reels storyboards, ad carousels |
| **Creative Studio** | Interactive canvas edits, layered diffing, critique overlays, and feedback loops. | Studio canvas designs, critique reports |
| **Launch Campaigns** | Cross-channel timeline structuring, sequential email drafts, and ad campaigns. | Email automation plans, meta ads, timelines |

---

## 🛠 Developer Setup & Installation

Follow these instructions to boot Helix locally on your machine.

### Prerequisites
* **Node.js** ≥ 18.x and **npm** or **pnpm** ≥ 9
* **Python** ≥ 3.10 and **pip**
* **Docker** and **Docker Compose**

### Step 1: Clone the Repository & Setup Files
```bash
git clone https://github.com/Mysterio6193/Helix.git
cd Helix
```

### Step 2: Configure Environment Variables
Copy the example environment files at the root directory:
```bash
cp .env.example .env
```
Fill out the API credentials. Key variables include:
```env
# Infrastructure & Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/helix
REDIS_URL=redis://localhost:6379/0

# Model Providers
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-claude-key
GEMINI_API_KEY=your-gemini-key

# Deployment & Integrations
GITHUB_TOKEN=your-github-personal-token
VERCEL_TOKEN=your-vercel-token
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

### Step 3: Run Infrastructure Services
Fire up local Postgres, Redis, MinIO (asset store), and Langfuse (observability) using Docker Compose:
```bash
cd infra
docker compose up -d postgres redis minio langfuse
cd ..
```

### Step 4: Setup Backend API (FastAPI)
Initialize Python virtual environment, install dependencies, run database migrations, and seed all bootstrap loaders:
```bash
cd apps/api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run Database Migrations
alembic upgrade head

# Load Skills, Tools Registry, and Design Systems Seeding
python -m helix.skills.loader
python -m helix.tools.bootstrap
python -m helix.design_systems.loader

# Start Backend API Dev Server
uvicorn helix.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 5: Setup Worker Nodes (Celery)
In a separate terminal, activate the virtual environment and start the LangGraph background worker:
```bash
cd apps/api
source venv/bin/activate
python -m apps.workers.run_worker
```

### Step 6: Setup Frontend (Next.js 15)
Open a new terminal window, navigate to the web directory, clear any build caches, and start the development server:
```bash
cd apps/web
npm install

# Clear Next.js dev server cache (highly recommended after asset changes)
rm -rf .next

# Start Dev Server
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser!

---

## 🍽 Customer & User Guide

For restaurant owners, food brands, and marketing teams using Helix to drive their brand growth:

### 1. Build a Brand Profile
Go to the **New Brand** portal. You can copy-paste your restaurant's website URL (e.g. `https://urbangrill.com`) or submit a descriptive prompt (e.g., *"A sustainable wood-fired pizzeria in downtown Chicago targeting health-conscious millennials with a minimalist, rustic aesthetic"*). Helix will autonomously:
* Synthesize a complete corporate identity brief.
* Formulate tone guidelines and brand voice matrices.
* Draft curated geometric palettes matching the selected design system.

### 2. Orchestrate Creative Workflows
Select one of the 6 creative workflow slices:
* **Digital Menu & Packaging**: Enter target menu item keywords (e.g. "Truffle Mushroom Pizza"), and Helix generates a design card with print-ready margins and margins-bleed packaging layout files.
* **Vercel Deployments**: Trigger the website slice. Helix generates a complete, multi-page Next.js web application incorporating your brand palettes and typography, commits the code to GitHub, and instantly deploys it to a live production Vercel URL.
* **Marketing Campaigns**: Schedule campaigns. View your email automation plans, visual ad tiles, and calendar moment timelines completely mapped out and ready to go.

### 3. Connect Integrations
Go to the **Integrations** console to connect third-party platforms:
* **Telegram Bot Integration**: Enter a Telegram Bot Token. The console dynamically starts a status checker, maps the bot handle (e.g., `@UrbanPizzaBot`), and displays webhook register statuses. Click the glowing **Activate Webhook Listener** button to immediately route conversation streams to your backend orchestrator.
* **Vercel & GitHub**: Connect tokens to enable automated repository creation and instant hosting deployments.
