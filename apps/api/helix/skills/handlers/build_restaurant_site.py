"""Handler for skill: build_restaurant_site.

Three sub-steps inside one skill so the WebBuilderAgent can stay simple:

  1. Generate section copy (openai_chat, json_mode).
  2. Render Next.js 15 + Tailwind TSX files from the brand's design system.
  3. (Optional) push to GitHub + trigger Vercel deployment.

The rendered file map is also returned in `outputs.files` so the UI can show a
preview tree even when deploy=False.
"""
from __future__ import annotations

import json
import re
from typing import Any

from helix.skills.base import SkillContext, SkillResult, register_skill_handler
from helix.tools.registry import get_tool


# ---------------------------------------------------------------------------
# 1. Section copy generation
# ---------------------------------------------------------------------------

_SECTIONS_SYSTEM = (
    "You are a senior restaurant copywriter and conversion-focused landing page "
    "designer. Given a brand strategy and voice, return ONLY a JSON object with "
    "these keys exactly:\n"
    "  hero: { eyebrow: string, headline: string, subhead: string, primary_cta: string, secondary_cta: string }\n"
    "  about: { eyebrow: string, headline: string, paragraphs: string[] }   // 2-3 paragraphs, 1-3 sentences each\n"
    "  menu_teaser: { eyebrow: string, headline: string, items: { name: string, blurb: string, price: string }[] }   // 3-5 signature items, price formatted with currency\n"
    "  visit: { eyebrow: string, headline: string, address_lines: string[], hours: { day: string, hours: string }[] }\n"
    "  contact: { eyebrow: string, headline: string, email: string, phone: string, instagram: string }\n"
    "  footer: { tagline: string, copyright_owner: string }\n"
    "Tone matches strategy.voice. No emojis. No marketing clichés (\"experience\", "
    "\"journey\", \"savor\", \"indulge\"). Concrete sensory nouns and verbs over abstractions."
)


def _compose_sections_user(strategy: dict, copy: dict | None, brand: dict) -> str:
    payload = {
        "brand_name": brand.get("name") or strategy.get("name"),
        "strategy": strategy,
        "preferred_tagline": _first_tagline(copy),
    }
    return json.dumps(payload, indent=2)


def _first_tagline(copy: dict | None) -> str | None:
    if not copy:
        return None
    options = (copy.get("taglines") or {}).get("options") or []
    if options and isinstance(options[0], dict):
        return options[0].get("text") or options[0].get("tagline")
    if options and isinstance(options[0], str):
        return options[0]
    return None


async def _generate_sections(
    ctx: SkillContext,
    strategy: dict,
    copy: dict | None,
    brand: dict,
) -> tuple[dict[str, Any] | None, float, str | None]:
    tool = get_tool("openai_chat")
    if tool is None:
        return None, 0.0, "openai_chat tool not registered"

    messages: list[dict[str, str]] = []
    for learn in ctx.learnings:
        if learn:
            messages.append({"role": "system", "content": learn})
    messages.append({"role": "system", "content": _SECTIONS_SYSTEM})
    messages.append(
        {"role": "user", "content": _compose_sections_user(strategy, copy, brand)}
    )

    result = await tool.call(
        messages=messages,
        model="gpt-4o-mini",
        temperature=0.7,
        json_mode=True,
    )
    if not result.ok:
        return None, result.cost_usd or 0.0, result.error

    text = (result.data or {}).get("content") if isinstance(result.data, dict) else str(result.data or "")
    try:
        sections = json.loads(text)
    except json.JSONDecodeError:
        return None, result.cost_usd or 0.0, "sections JSON parse failed"

    if not isinstance(sections, dict):
        return None, result.cost_usd or 0.0, "sections payload not an object"
    return sections, result.cost_usd or 0.0, None


# ---------------------------------------------------------------------------
# 2. File rendering — Next.js 15 + Tailwind v4
# ---------------------------------------------------------------------------

def _slug(s: str | None, fallback: str = "site") -> str:
    if not s:
        return fallback
    out = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return out or fallback


def _color(palette: dict, *keys: str, default: str) -> str:
    for k in keys:
        v = palette.get(k)
        if isinstance(v, str) and v.startswith("#"):
            return v
        if isinstance(v, list) and v and isinstance(v[0], str):
            return v[0]
    return default


def _tokens(design_system: dict) -> dict[str, str]:
    palette = design_system.get("palette") or {}
    typo = design_system.get("typography") or {}
    return {
        "canvas": _color(palette, "canvas", "background", "bg", default="#ffffff"),
        "ink": _color(palette, "ink", "text", "primary", default="#0a0a0a"),
        "accent": _color(palette, "accent", "brand_coral", "brand_blue", "primary", default="#ff6a4d"),
        "muted": _color(palette, "surface", "muted", default="#fafafa"),
        "hairline": _color(palette, "hairline", "border", default="#e6e6e6"),
        "font_family": typo.get("family_primary") or "DM Sans",
    }


def _render_package_json(slug: str) -> str:
    return json.dumps(
        {
            "name": slug,
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint",
            },
            "dependencies": {
                "next": "15.0.3",
                "react": "19.0.0",
                "react-dom": "19.0.0",
            },
            "devDependencies": {
                "@types/node": "^22.9.0",
                "@types/react": "^19.0.0",
                "@types/react-dom": "^19.0.0",
                "tailwindcss": "^4.0.0-beta.3",
                "@tailwindcss/postcss": "^4.0.0-beta.3",
                "autoprefixer": "^10.4.20",
                "postcss": "^8.4.49",
                "typescript": "^5.6.3",
            },
        },
        indent=2,
    )


def _render_tsconfig() -> str:
    return json.dumps(
        {
            "compilerOptions": {
                "target": "ES2022",
                "lib": ["dom", "dom.iterable", "esnext"],
                "skipLibCheck": True,
                "strict": True,
                "noEmit": True,
                "esModuleInterop": True,
                "module": "esnext",
                "moduleResolution": "bundler",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
                "plugins": [{"name": "next"}],
                "paths": {"@/*": ["./*"]},
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
            "exclude": ["node_modules"],
        },
        indent=2,
    )


_NEXT_CONFIG = """import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
"""

_POSTCSS = """export default {
  plugins: {
    "@tailwindcss/postcss": {},
    autoprefixer: {},
  },
};
"""

_NEXT_ENV = '/// <reference types="next" />\n/// <reference types="next/image-types/global" />\n'


def _render_globals_css(tokens: dict[str, str]) -> str:
    return f"""@import "tailwindcss";

:root {{
  --color-canvas: {tokens['canvas']};
  --color-ink: {tokens['ink']};
  --color-accent: {tokens['accent']};
  --color-muted: {tokens['muted']};
  --color-hairline: {tokens['hairline']};
  --font-sans: "{tokens['font_family']}", "DM Sans", "Inter", ui-sans-serif, system-ui, sans-serif;
}}

@theme inline {{
  --color-canvas: var(--color-canvas);
  --color-ink: var(--color-ink);
  --color-accent: var(--color-accent);
  --color-muted: var(--color-muted);
  --color-hairline: var(--color-hairline);
  --font-sans: var(--font-sans);
}}

html, body {{
  background: var(--color-canvas);
  color: var(--color-ink);
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
}}

* {{ box-sizing: border-box; }}
"""


def _render_layout_tsx(brand_name: str, tagline: str | None) -> str:
    desc = (tagline or brand_name).replace('"', '\\"')
    return f"""import type {{ Metadata }} from "next";
import {{ DM_Sans }} from "next/font/google";

import "./globals.css";

const dmSans = DM_Sans({{
  subsets: ["latin"],
  variable: "--font-dm-sans",
  display: "swap",
  weight: ["400", "500", "600", "700"],
}});

export const metadata: Metadata = {{
  title: "{brand_name}",
  description: "{desc}",
}};

export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
  return (
    <html lang="en" className={{dmSans.variable}}>
      <body>{{children}}</body>
    </html>
  );
}}
"""


_PAGE_TSX = """import About from "@/components/About";
import Contact from "@/components/Contact";
import Footer from "@/components/Footer";
import Hero from "@/components/Hero";
import MenuTeaser from "@/components/MenuTeaser";
import Visit from "@/components/Visit";

export default function Home() {
  return (
    <main>
      <Hero />
      <About />
      <MenuTeaser />
      <Visit />
      <Contact />
      <Footer />
    </main>
  );
}
"""


def _esc(value: Any) -> str:
    """Escape an arbitrary value for safe embedding inside a JSX string literal."""
    if value is None:
        return ""
    return str(value).replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", " ").strip()


def _render_hero_tsx(hero: dict) -> str:
    return f"""export default function Hero() {{
  return (
    <section className="px-6 py-24 sm:py-32 mx-auto max-w-[1200px]">
      <div className="text-xs uppercase tracking-[1.5px] text-[color:var(--color-accent)] font-semibold mb-4">
        {_esc(hero.get('eyebrow'))}
      </div>
      <h1 className="text-5xl sm:text-7xl font-bold leading-[1.05] tracking-tight max-w-[18ch]">
        {_esc(hero.get('headline'))}
      </h1>
      <p className="mt-6 text-lg sm:text-xl text-[color:var(--color-ink)]/70 max-w-[55ch] leading-relaxed">
        {_esc(hero.get('subhead'))}
      </p>
      <div className="mt-10 flex flex-wrap gap-3">
        <a href="#menu" className="inline-flex h-12 items-center rounded-full bg-[color:var(--color-ink)] px-6 text-sm font-medium text-[color:var(--color-canvas)] hover:opacity-95">
          {_esc(hero.get('primary_cta'))}
        </a>
        <a href="#visit" className="inline-flex h-12 items-center rounded-full border border-[color:var(--color-ink)] px-6 text-sm font-medium hover:bg-[color:var(--color-muted)]">
          {_esc(hero.get('secondary_cta'))}
        </a>
      </div>
    </section>
  );
}}
"""


def _render_about_tsx(about: dict) -> str:
    paras = about.get("paragraphs") or []
    paras_jsx = "\n".join(
        f'        <p className="text-lg leading-relaxed text-[color:var(--color-ink)]/80">{_esc(p)}</p>'
        for p in paras
    )
    return f"""export default function About() {{
  return (
    <section id="about" className="px-6 py-20 mx-auto max-w-[1200px] border-t border-[color:var(--color-hairline)]">
      <div className="text-xs uppercase tracking-[1.5px] text-[color:var(--color-accent)] font-semibold mb-4">
        {_esc(about.get('eyebrow'))}
      </div>
      <h2 className="text-4xl sm:text-5xl font-bold leading-tight max-w-[20ch] mb-8">
        {_esc(about.get('headline'))}
      </h2>
      <div className="space-y-6 max-w-[65ch]">
{paras_jsx}
      </div>
    </section>
  );
}}
"""


def _render_menu_tsx(menu: dict) -> str:
    items = menu.get("items") or []
    items_jsx = "\n".join(
        f"""        <div className="flex items-baseline justify-between gap-6 border-b border-[color:var(--color-hairline)] py-5">
          <div>
            <div className="text-lg font-semibold">{_esc(it.get('name'))}</div>
            <div className="text-sm text-[color:var(--color-ink)]/70 mt-1">{_esc(it.get('blurb'))}</div>
          </div>
          <div className="text-base font-medium tabular-nums">{_esc(it.get('price'))}</div>
        </div>"""
        for it in items
    )
    return f"""export default function MenuTeaser() {{
  return (
    <section id="menu" className="px-6 py-20 mx-auto max-w-[1200px] border-t border-[color:var(--color-hairline)]">
      <div className="text-xs uppercase tracking-[1.5px] text-[color:var(--color-accent)] font-semibold mb-4">
        {_esc(menu.get('eyebrow'))}
      </div>
      <h2 className="text-4xl sm:text-5xl font-bold leading-tight max-w-[20ch] mb-10">
        {_esc(menu.get('headline'))}
      </h2>
      <div className="max-w-[720px]">
{items_jsx}
      </div>
    </section>
  );
}}
"""


def _render_visit_tsx(visit: dict) -> str:
    addr = "\n".join(
        f'          <div className="text-base">{_esc(line)}</div>'
        for line in (visit.get("address_lines") or [])
    )
    hours = "\n".join(
        f"""          <div className="flex justify-between gap-6 py-1.5">
            <div className="text-base">{_esc(h.get('day'))}</div>
            <div className="text-base tabular-nums text-[color:var(--color-ink)]/70">{_esc(h.get('hours'))}</div>
          </div>"""
        for h in (visit.get("hours") or [])
    )
    return f"""export default function Visit() {{
  return (
    <section id="visit" className="px-6 py-20 mx-auto max-w-[1200px] border-t border-[color:var(--color-hairline)]">
      <div className="text-xs uppercase tracking-[1.5px] text-[color:var(--color-accent)] font-semibold mb-4">
        {_esc(visit.get('eyebrow'))}
      </div>
      <h2 className="text-4xl sm:text-5xl font-bold leading-tight max-w-[20ch] mb-10">
        {_esc(visit.get('headline'))}
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-10 max-w-[720px]">
        <div>
          <div className="text-xs uppercase tracking-[1.5px] text-[color:var(--color-ink)]/60 font-semibold mb-3">Address</div>
{addr}
        </div>
        <div>
          <div className="text-xs uppercase tracking-[1.5px] text-[color:var(--color-ink)]/60 font-semibold mb-3">Hours</div>
{hours}
        </div>
      </div>
    </section>
  );
}}
"""


def _render_contact_tsx(contact: dict) -> str:
    return f"""export default function Contact() {{
  return (
    <section id="contact" className="px-6 py-20 mx-auto max-w-[1200px] border-t border-[color:var(--color-hairline)]">
      <div className="text-xs uppercase tracking-[1.5px] text-[color:var(--color-accent)] font-semibold mb-4">
        {_esc(contact.get('eyebrow'))}
      </div>
      <h2 className="text-4xl sm:text-5xl font-bold leading-tight max-w-[20ch] mb-10">
        {_esc(contact.get('headline'))}
      </h2>
      <ul className="space-y-3 text-base">
        <li><a className="hover:underline" href="mailto:{_esc(contact.get('email'))}">{_esc(contact.get('email'))}</a></li>
        <li><a className="hover:underline" href="tel:{_esc(contact.get('phone'))}">{_esc(contact.get('phone'))}</a></li>
        <li><a className="hover:underline" href="https://instagram.com/{_esc(contact.get('instagram','')).lstrip('@')}" target="_blank" rel="noreferrer">@{_esc(contact.get('instagram','')).lstrip('@')}</a></li>
      </ul>
    </section>
  );
}}
"""


def _render_footer_tsx(footer: dict, brand_name: str) -> str:
    owner = footer.get("copyright_owner") or brand_name
    return f"""export default function Footer() {{
  const year = new Date().getFullYear();
  return (
    <footer className="px-6 py-10 mx-auto max-w-[1200px] border-t border-[color:var(--color-hairline)] flex flex-col sm:flex-row justify-between gap-4">
      <div className="text-sm text-[color:var(--color-ink)]/70">{_esc(footer.get('tagline'))}</div>
      <div className="text-sm text-[color:var(--color-ink)]/60 tabular-nums">© {{year}} {_esc(owner)}</div>
    </footer>
  );
}}
"""


def _render_readme(brand_name: str, slug: str) -> str:
    return f"""# {brand_name}

Generated by Helix — `build_restaurant_site` skill.

```bash
pnpm install
pnpm dev
```

Open http://localhost:3000.

## Deploy

This project is pre-configured for Vercel. If Helix triggered a deployment, the
URL was returned alongside this scaffold. Otherwise:

```bash
vercel --prod
```

Repo slug: `{slug}`.
"""


def _render_all_files(
    *,
    brand_name: str,
    slug: str,
    tagline: str | None,
    design_system: dict,
    sections: dict,
) -> dict[str, str]:
    tokens = _tokens(design_system)
    return {
        "package.json": _render_package_json(slug),
        "tsconfig.json": _render_tsconfig(),
        "next.config.ts": _NEXT_CONFIG,
        "postcss.config.mjs": _POSTCSS,
        "next-env.d.ts": _NEXT_ENV,
        "app/globals.css": _render_globals_css(tokens),
        "app/layout.tsx": _render_layout_tsx(brand_name, tagline),
        "app/page.tsx": _PAGE_TSX,
        "components/Hero.tsx": _render_hero_tsx(sections.get("hero") or {}),
        "components/About.tsx": _render_about_tsx(sections.get("about") or {}),
        "components/MenuTeaser.tsx": _render_menu_tsx(sections.get("menu_teaser") or {}),
        "components/Visit.tsx": _render_visit_tsx(sections.get("visit") or {}),
        "components/Contact.tsx": _render_contact_tsx(sections.get("contact") or {}),
        "components/Footer.tsx": _render_footer_tsx(sections.get("footer") or {}, brand_name),
        "README.md": _render_readme(brand_name, slug),
        ".gitignore": "node_modules\n.next\n.env*.local\ndist\nout\n.DS_Store\n",
    }


# ---------------------------------------------------------------------------
# 3. Handler
# ---------------------------------------------------------------------------

@register_skill_handler("build_restaurant_site")
async def handle(ctx: SkillContext) -> SkillResult:
    inputs: dict[str, Any] = ctx.inputs or {}
    strategy = inputs.get("strategy") or {}
    design_system = inputs.get("design_system") or {}
    copy = inputs.get("copy") or {}
    brand = ctx.brand_context.get("brand") or {}
    if brand.get("name"):
        strategy = {**strategy, "name": brand["name"]}

    brand_name = strategy.get("name") or brand.get("name") or "Restaurant"
    slug = inputs.get("repo_slug") or _slug(brand_name)

    sections, copy_cost, copy_err = await _generate_sections(ctx, strategy, copy, brand)
    if sections is None:
        return SkillResult(ok=False, error=f"sections: {copy_err}", cost_usd=copy_cost)

    tagline = _first_tagline(copy) or (sections.get("hero") or {}).get("subhead")
    files = _render_all_files(
        brand_name=brand_name,
        slug=slug,
        tagline=tagline,
        design_system=design_system,
        sections=sections,
    )

    outputs: dict[str, Any] = {
        "sections": sections,
        "slug": slug,
        "files": files,
        "file_count": len(files),
    }
    total_cost = copy_cost

    # Optional deploy step
    deploy = bool(inputs.get("deploy", False))
    if deploy:
        gh = get_tool("github_repo")
        vercel = get_tool("vercel_deploy")
        if gh is None or vercel is None:
            outputs["deploy_error"] = "github_repo or vercel_deploy tool not registered"
        else:
            gh_res = await gh.call(
                repo_name=slug,
                files=files,
                description=tagline or f"{brand_name} — generated by Helix",
                private=True,
            )
            if gh_res.ok:
                outputs["repo"] = gh_res.data
                repo_full = f"{gh_res.data['owner']}/{gh_res.data['repo']}"
                vercel_res = await vercel.call(
                    project_name=slug,
                    github_repo=repo_full,
                )
                if vercel_res.ok:
                    outputs["deployment"] = vercel_res.data
                else:
                    outputs["deploy_error"] = vercel_res.error
            else:
                outputs["deploy_error"] = gh_res.error

    await ctx.db.commit()
    return SkillResult(
        ok=True,
        outputs=outputs,
        cost_usd=total_cost,
    )
