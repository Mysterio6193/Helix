# Helix — AI-Native Commerce Operating System

## Commands

```bash
# API (from apps/api)
source .venv/bin/activate
uvicorn helix.main:app --host 0.0.0.0 --port 8000 --reload

# Web (from apps/web)
pnpm dev

# Workers
source .venv/bin/activate && python -m apps.workers.run_worker

# Lint & Typecheck
ruff check apps/api    # Python lint
mypy apps/api          # Python types
npx tsc --noEmit --strict  # TS typecheck (from apps/web)
npx next lint           # Next lint (from apps/web)

# Migrations (from apps/api)
alembic upgrade head
alembic revision --autogenerate -m "description"

# Tests
pytest apps/api/tests
```
