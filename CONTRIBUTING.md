# Contributing to Helix

## Development Setup

### Prerequisites
- Node.js 18+ and pnpm 9+
- Python 3.11+
- Docker and Docker Compose

### Quick Start

```bash
# 1. Install dependencies
pnpm install

# 2. Start infrastructure
cd infra && docker compose up -d && cd ..

# 3. Set up the API
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
# Start API:
uvicorn helix.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Start the web app (separate terminal)
cd apps/web
pnpm dev
```

### Environment

Copy `.env.example` to `.env` and configure the providers you need:

```bash
cp .env.example .env
```

At minimum, configure one LLM provider (e.g., `OPENAI_API_KEY`) to test
agent and workflow functionality.

## Codebase Conventions

### Python (`apps/api/`)

- **Formatting**: Ruff with line-length=100. Run before committing:
  ```bash
  cd apps/api && source .venv/bin/activate && ruff check . && ruff format --check .
  ```
- **Types**: Use modern Python type hints (`str | None`, `list[str]`, etc.)
- **Imports**: Group as: stdlib → third-party → helix modules. One blank line between groups.
- **Models**: SQLAlchemy `Mapped` style. All models extend `helix.models.base.Base`.
- **Routes**: FastAPI `APIRouter` in `helix.api.v1.*`. Each route has type-annotated dependencies.
- **Services**: Business logic lives in `helix.services.*`, not in route handlers.
- **Config**: New settings go in `helix.core.config.Settings` with pydantic Field descriptors.
- **Migrations**: `cd apps/api && alembic revision --autogenerate -m "description"`
- **Testing**: `pytest` with `asyncio_mode=auto`. Tests live in `apps/api/tests/`.

### TypeScript (`apps/web/`, `packages/types/`)

- **Formatting**: Prettier with default config
- **Types**: Strict mode. Avoid `any`. Use `@ts-expect-error` instead of `@ts-ignore`.
- **Components**: Prefer server components by default. Use `"use client"` only when needed.
- **API client**: Add new endpoints to `lib/api.ts` as typed methods on the `api` object.
- **Hooks**: Shared hooks in `hooks/`, scoped hooks next to their component.
- **Styling**: Tailwind CSS utility classes. shadcn-style primitives in `components/ui/`.

### Workflow Slices

Workflow slices (in `apps/api/helix/workflows/slices/`) are reusable workflow
components. Each slice:
1. Defines a `build_steps()` function that returns workflow steps
2. Accepts `inputs`, `started` timestamp, and optional `prior_run` context
3. Uses `_step()` helper for consistent step formatting
4. Includes lifecycle events (hydrate → check → generate → finalize)

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes following codebase conventions
3. Run lint and type checking:
   ```bash
   # Python
   cd apps/api && ruff check . && mypy helix/

   # TypeScript
   cd apps/web && npx tsc --noEmit --strict && npx next lint
   ```
4. Add or update tests as needed
5. Update relevant documentation (ARCHITECTURE.md, DEPLOY.md, etc.)
6. Create a PR with a clear description of changes

## Adding a New Integration

Integrations follow a strict real-API-only policy — no mocks, no synthetic data, no silent degradation.

1. **Add the provider** to `apps/api/helix/integrations/providers.py`:
   - Choose `TOKEN_PROVIDER` (API key) or `OAUTH_PROVIDER` (OAuth flow)
   - Set a unique `key`, `display_name`, `category`, and `description`
   - Include `token_help_url` pointing to real docs
2. **Create the tool adapter** in `tools/adapters/` following the consistent pattern:
   - `_resolve_creds(session, workspace_id, provider)` — resolve credentials from DB
   - Return `ToolResult(ok=False, error="X not connected.")` if creds are missing — no graceful degradation
   - Make real HTTP API calls only — no mock endpoints or hardcoded data
3. **Register the adapter** in `apps/api/helix/tools/bootstrap.py`:
   - Import the tool class
   - Add it to the `_BUILTINS` tuple
4. **Update the frontend** `TOOL_COUNTS` map in `apps/web/app/integrations/page.tsx`
5. **Add a health check** to `apps/api/helix/services/integration_health.py` if possible
6. **Verify**: `ruff check` and `tsc --noEmit --strict` must pass with 0 errors
7. **Update docs**: List the integration in README.md and CHANGELOG.md

## Adding a New Model

1. Add a `ModelSpec` entry to `apps/api/helix/llm/catalog.py`
2. If it needs a new provider API key, add it to `Settings` in `config.py`
3. Wire up the provider's chat/stream function in `gateway.py`
4. Add the provider mapping in `ModelSpec.settings_attr`
5. The model is now available in the playground and chat endpoints

## Adding a New Skill

Skills live in the root `skills/` directory. Each skill is a directory with a
`SKILL.md` file containing:
- Frontmatter (name, version, inputs, outputs, required_tools, tags)
- Description of what the skill does
- Trigger phrases and usage examples
- Handler logic (YAML-based or referencing a Python handler)

For skills that need Python handlers, add the handler to
`apps/api/helix/skills/handlers/` and register it in the skill registry.

## Adding a New API Endpoint

1. Add the route function to an existing or new router in `apps/api/helix/api/v1/`
2. Add Pydantic schemas in `apps/api/helix/schemas/` if needed
3. Add business logic as a service in `apps/api/helix/services/`
4. Add the frontend API client method in `apps/web/lib/api.ts`
5. Add the frontend page in `apps/web/app/`

## Architecture Decisions

See `ARCHITECTURE.md` for detailed design decisions and data flow documentation.

Key principles:
- **Server-holds-keys by default**, optional BYOK
- **Streaming via SSE** for all chat providers
- **Usage tracking fires async** after response
- **BYOK keys encrypted at rest** with Fernet
- **Playwright is optional** with simulated fallback
- **Workflows are durable** with checkpoint resumption
