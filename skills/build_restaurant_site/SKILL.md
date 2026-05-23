---
name: build_restaurant_site
version: 1.0.0
description: >
  When the user wants a restaurant landing site, marketing page, or microsite —
  builds a Next.js 15 + Tailwind v4 scaffold from the brand strategy + selected
  design school + approved logo. Generates section copy (hero, about, menu,
  visit, contact), renders TSX/CSS files using the design system tokens, and
  optionally pushes to GitHub + triggers a Vercel deployment.
  Trigger phrases: "website", "landing page", "microsite", "marketing site",
  "homepage", "Vercel deploy", "ship the site".
inputs:
  strategy: { type: object, required: true }
  design_system: { type: object, required: true }
  copy: { type: object, required: false }
  visuals: { type: array, required: false, description: "Asset records — uses first purpose=logo." }
  domain_hint: { type: string, required: false }
  deploy: { type: boolean, required: false, default: false }
  repo_slug: { type: string, required: false, description: "Override generated repo name." }
outputs:
  sections: object
  files: object
  repo: object
  deployment: object
required_tools: [openai_chat, github_repo, vercel_deploy]
dependencies: [brand_strategy_brief, select_design_school, design_logo, generate_taglines]
tags: [website, web, nextjs, vercel, deploy]
trigger_phrases:
  - website
  - landing page
  - homepage
  - microsite
  - marketing site
  - Vercel deploy
  - ship the site
---

# Build Restaurant Site

1. Generate section copy via `openai_chat` (json_mode). One JSON object with
   `hero`, `about`, `menu_teaser`, `visit`, `contact`, `footer`.
2. Render Next.js 15 App-Router TSX files using the `design_system` tokens for
   colors / radius / typography. Files:
   - `package.json`, `tsconfig.json`, `next.config.ts`
   - `tailwind.config.ts` (token-mirroring)
   - `app/layout.tsx`, `app/globals.css`, `app/page.tsx`
   - `components/{Hero,About,MenuTeaser,Visit,Contact,Footer}.tsx`
   - `public/logo.svg` (placeholder pointer — actual logo asset is uploaded separately)
   - `README.md`
3. If `deploy=true` and `GITHUB_TOKEN` + `VERCEL_TOKEN` are configured:
   - `github_repo` creates `repo_slug` (derived from strategy.name) and pushes
     every file.
   - `vercel_deploy` creates a project linked to the repo and triggers production.
4. Return `outputs = {sections, files: {<path>: <content>...}, repo: {...} | None,
   deployment: {url, status, ...} | None}`.
