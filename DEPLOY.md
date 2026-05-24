# Helix Deployment Guide

This is the end-to-end path from your laptop to a public SaaS at `https://app.yourdomain.com`.

## Architecture

```
                          ┌────────────────────┐
                 https    │  Next.js (web)     │
   users ────────────────▶│  port 3000         │
                          └─────────┬──────────┘
                                    │ /api/proxy/* rewrite
                                    ▼
                          ┌────────────────────┐
                          │  FastAPI (api)     │
                          │  port 8000         │
                          └─┬─────────┬──────┬─┘
                            │         │      │
                  ┌─────────┘     ┌───┘      └─────┐
                  ▼               ▼                ▼
         ┌─────────────┐  ┌─────────────┐  ┌──────────────┐
         │ Postgres    │  │ Redis       │  │ S3 / R2      │
         │ + pgvector  │  │ queue+cache │  │ asset store  │
         └─────────────┘  └─────────────┘  └──────────────┘
                                ▲
                                │ workers pop runs
                                │
                          ┌────────────────────┐
                          │ workers            │
                          │ multi-replica      │
                          └────────────────────┘
```

## Prerequisites

| Service | Purpose | Recommended provider |
|---|---|---|
| Postgres 16 + pgvector | Primary DB, embeddings | Supabase, Neon, Fly Postgres, Railway |
| Redis | Run queue + cache | Upstash, Redis Cloud, Fly Redis |
| S3-compatible object store | Generated assets | Cloudflare R2 (cheapest egress), AWS S3, Backblaze B2 |
| Domain + SSL | Production URLs | Cloudflare, namecheap; SSL via your host |
| Google Cloud project | OAuth sign-in | console.cloud.google.com |
| Stripe account | Billing | dashboard.stripe.com (start in Test mode) |

## Step 1 — Create the managed services

### Postgres with pgvector

```sql
-- After provisioning the DB, connect with psql and run:
CREATE EXTENSION IF NOT EXISTS vector;
```

Supabase / Neon: enable under **Database → Extensions**.
Fly Postgres: `fly pg connect -a <app>` then run the SQL above.

### Redis

Any managed Redis ≥6 works. Copy the `rediss://` URL.

### S3 bucket (Cloudflare R2 example)

1. Create R2 bucket `helix-assets`
2. Settings → CORS Policy:
   ```json
   [{"AllowedOrigins":["https://app.yourdomain.com"],"AllowedMethods":["GET","PUT","POST","HEAD"],"AllowedHeaders":["*"],"MaxAgeSeconds":3600}]
   ```
3. Generate an R2 API token, copy access key + secret

## Step 2 — Configure environment

```bash
cp .env.production.example .env.production
```

Open `.env.production` and replace every `__REPLACE__` placeholder. Critical:

- `SECRET_KEY` and `ENCRYPTION_KEY` — already pre-filled with fresh values, but regenerate per-environment:
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(48))"
  python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- `DATABASE_URL` — must be `postgresql+asyncpg://...` (note the `+asyncpg`)
- `WEB_PUBLIC_URL` and `API_PUBLIC_URL` — must be `https://` (the API refuses to boot otherwise when `HELIX_ENV=production`)
- `CORS_ORIGINS` — comma-separated list, NO wildcards

## Step 3 — Set up Google OAuth

1. console.cloud.google.com → APIs & Services → Credentials → Create OAuth 2.0 Client ID
2. Application type: Web application
3. Authorized JavaScript origins: `https://app.yourdomain.com`
4. Authorized redirect URIs: `https://app.yourdomain.com/api/proxy/auth/google/callback`
5. Copy Client ID + Client Secret into `.env.production`

## Step 4 — Set up Stripe

1. dashboard.stripe.com → Developers → API keys → copy publishable + secret
2. Products → New product → set up your tiers (matches `STRIPE_PRICE_STARTER`, `STRIPE_PRICE_PRO`, `STRIPE_PRICE_BUSINESS`)
3. Each product → "Add price" → recurring monthly → copy the `price_xxx` ID
4. Developers → Webhooks → Add endpoint:
   - URL: `https://api.yourdomain.com/api/v1/billing/webhook`
   - Events: `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.paid`, `invoice.payment_failed`, `checkout.session.completed`
   - Reveal & copy the signing secret → `STRIPE_WEBHOOK_SECRET`

## Step 5 — Run migrations

From a one-off container or the API container's shell:

```bash
cd apps/api
alembic upgrade head
```

This creates every table in your production Postgres.

## Step 6 — Deploy

### Option A — Fly.io (recommended for first launch)

```bash
# 1. Install flyctl, log in
flyctl auth login

# 2. Provision the api app
cd apps/api
flyctl launch --no-deploy
# Set every secret from .env.production:
flyctl secrets set $(grep -v '^#' ../../.env.production | grep '=' | xargs)
flyctl deploy

# 3. Provision the worker app (same repo, different start command)
# Edit fly.toml -> processes: worker = "python -m apps.workers.run_worker"
# Then: flyctl deploy

# 4. Provision the web app
cd ../web
flyctl launch --no-deploy
flyctl secrets set NEXT_PUBLIC_API_URL=https://api.yourdomain.com NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
flyctl deploy

# 5. Wire up DNS
# Cloudflare: CNAME app -> <web-app>.fly.dev
#             CNAME api -> <api-app>.fly.dev
# Fly will issue SSL certs automatically.
```

### Option B — Render

Create three Render services from the same repo:

| Service | Type | Start command |
|---|---|---|
| `helix-api` | Web | `uvicorn helix.main:app --host 0.0.0.0 --port $PORT` |
| `helix-worker` | Background Worker | `python -m apps.workers.run_worker` |
| `helix-web` | Web | `pnpm --filter web build && pnpm --filter web start` |

Attach a Render Postgres + Redis. Set env vars from `.env.production` on each service.

### Option C — Vercel (frontend) + Railway (backend)

- Vercel: import `apps/web`, set `NEXT_PUBLIC_*` env vars
- Railway: import `apps/api` and `apps/workers` as separate services, attach managed Postgres + Redis

## Step 7 — Post-deploy verification

```bash
# 1. Health check returns 200
curl https://api.yourdomain.com/health
# Expected: {"status":"ok","version":"0.1.0","environment":"production",...}

# 2. Auth providers endpoint shows Google enabled
curl https://api.yourdomain.com/api/v1/auth/providers
# Expected: {"google":{"enabled":true,"label":"Continue with Google"}}

# 3. Open https://app.yourdomain.com and complete a sign-in flow

# 4. Create a brand → should round-trip to the DB
```

## Step 8 — Stripe webhook smoke test

```bash
stripe trigger checkout.session.completed
# Then check API logs:
flyctl logs -a helix-api | grep billing
```

## Common failures

| Symptom | Fix |
|---|---|
| `Unsafe production config: SECRET_KEY is missing or weak` | Your `SECRET_KEY` is the dev default or < 32 chars. Regenerate. |
| `Unsafe production config: WEB_PUBLIC_URL is non-https` | Use `https://` URLs in production. |
| Sign-in shows `google_oauth_not_configured` | `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` missing. |
| CORS errors in browser | `CORS_ORIGINS` doesn't include your web URL exactly. |
| `pgvector type not found` | Postgres doesn't have the extension. Run `CREATE EXTENSION vector;` |
| Assets won't upload | S3 CORS policy missing — see Step 1. |
| Stripe webhook signature failures | `STRIPE_WEBHOOK_SECRET` is from a different endpoint than the one Stripe is posting to. |

## Scaling notes

- The API is stateless: scale horizontally behind a load balancer. Sessions live in cookies, not memory.
- Workers are the throughput bottleneck. Bump `WORKER_CONCURRENCY` per replica, then add replicas.
- Redis is used for the run queue and idempotency keys. A small managed plan (256MB) is plenty for the first few thousand customers.
- Postgres connection pool is 10/30 per API replica (see `apps/api/helix/core/db.py`). Use PgBouncer once you have >5 API replicas.

## Security checklist before launch

- [ ] `HELIX_ENV=production` so `assert_production_safe()` runs at boot
- [ ] `SECRET_KEY` and `ENCRYPTION_KEY` are unique per environment, never reused
- [ ] All URLs in `.env.production` are HTTPS
- [ ] `CORS_ORIGINS` contains only your own domains, no `*`
- [ ] OAuth redirect URIs in Google Cloud Console match `WEB_PUBLIC_URL` exactly
- [ ] Stripe is in **Live** mode (`sk_live_…` / `pk_live_…`)
- [ ] `/docs` is disabled (it is, when `HELIX_ENV=production`)
- [ ] S3 bucket is private (no public read), assets served via presigned URLs
- [ ] Postgres has automated daily backups enabled
- [ ] You've run through the sign-up → create brand → run workflow → see asset flow end-to-end on a fresh account
