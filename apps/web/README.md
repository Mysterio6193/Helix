# Helix — Web shell

Next.js 15 + React 19 + Tailwind v4 + Framer Motion + SWR.

Consumes the design language documented in [`DESIGN.md`](./DESIGN.md):
quiet monochrome canvas + vibrant brand-gradient product cards, DM Sans,
pill buttons, dual card families (`rounded-[16px]` quiet, `rounded-[32px]`
vibrant).

## Run

```bash
cp .env.example .env.local
pnpm install
pnpm dev          # http://localhost:3000
```

The API must be running on `http://localhost:8000` (FastAPI in `apps/api`).
WebSocket streaming hits `ws://localhost:8000/api/v1/runs/<id>/stream` directly
(no proxy — `lib/ws.ts`).

## Routes

| Path                           | Purpose                                   |
|--------------------------------|-------------------------------------------|
| `/`                            | Dashboard — hero, AI tile matrix, recent runs |
| `/brands`                      | Brand list                                 |
| `/brands/[id]`                 | Brand detail + workflow launchers         |
| `/workflows`                   | All runs across brands                     |
| `/workflows/[runId]`           | Run detail + live WS event stream         |
| `/studio`, `/packaging`, `/websites`, `/social`, `/campaigns`, `/assets`, `/skills`, `/memory`, `/integrations` | Placeholders for later phases |

## Phase wiring

| Concept                         | Source                                |
|---------------------------------|---------------------------------------|
| Design tokens                   | `app/globals.css` (CSS vars + `@theme inline`) |
| REST client                     | `lib/api.ts`                          |
| WS stream hook                  | `lib/ws.ts`                           |
| Pill button, cards, badge, input| `components/ui/*`                     |
| Workflow stream UI              | `components/workflow/run-stream.tsx`  |
| Run list                        | `components/workflow/run-list.tsx`    |
| Shell + nav                     | `components/layout/app-shell.tsx`     |
