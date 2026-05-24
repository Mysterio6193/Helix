"use client";

import Link from "next/link";
import {
  Activity,
  ArrowRight,
  Boxes,
  Brain,
  CheckCircle2,
  Cpu,
  Database,
  GitBranch,
  Image as ImageIcon,
  KeyRound,
  Layers,
  Megaphone,
  MessageSquare,
  Package,
  PaintBucket,
  Plug,
  Rocket,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { MarketingShell } from "@/components/layout/marketing-shell";
import {
  Reveal,
  RevealItem,
  RevealStagger,
} from "@/components/marketing/reveal";

interface FeatureSection {
  id: string;
  icon: React.ComponentType<{
    size?: number;
    className?: string;
    style?: React.CSSProperties;
  }>;
  accent: string;
  eyebrow: string;
  title: string;
  description: string;
  bullets: string[];
  href: string;
}

const SECTIONS: FeatureSection[] = [
  {
    id: "brand",
    icon: Sparkles,
    accent: "#ff3d7f",
    eyebrow: "Brands",
    title: "Brand identity, structured.",
    description:
      "Capture every brand as a record with positioning, archetype, voice attributes, palette, and references — the substrate every workflow reads from.",
    bullets: [
      "From-brief or from-URL extraction",
      "Voice attribute matrix + tone presets",
      "Palette, typography, and design school metadata",
      "Per-brand memory graph that grows with each run",
    ],
    href: "/sign-up",
  },
  {
    id: "workflows",
    icon: Workflow,
    accent: "#a24bff",
    eyebrow: "Workflows",
    title: "Composable workflow runs.",
    description:
      "Each capability is a graph of steps with typed inputs and outputs. Inspect any node, replay a run, fork a variant.",
    bullets: [
      "Live status streaming per run",
      "Full input / output history",
      "Re-run from any step",
      "Variants without losing history",
    ],
    href: "/sign-up",
  },
  {
    id: "packaging",
    icon: Package,
    accent: "#ff7a4d",
    eyebrow: "Packaging",
    title: "Print-ready packaging artwork.",
    description:
      "Generate labels, boxes, cups, bags, and stickers as SKU artwork with brand-locked composition.",
    bullets: [
      "Pizza boxes, pasta bowls, coffee cups, delivery bags",
      "Sticker and label artwork with bleed",
      "Brand tokens baked into every export",
      "Asset library, organized by SKU",
    ],
    href: "/sign-up",
  },
  {
    id: "websites",
    icon: Boxes,
    accent: "#4d7bff",
    eyebrow: "Websites",
    title: "Generate sites, deploy to Vercel.",
    description:
      "Spin up a Next.js marketing site from a brand record, push it to GitHub, and trigger a Vercel deploy — in one workflow.",
    bullets: [
      "Multi-page Next.js scaffolds",
      "Tailwind theming from brand tokens",
      "GitHub repo + Vercel project provisioning",
      "Re-run to regenerate without losing edits",
    ],
    href: "/sign-up",
  },
  {
    id: "social",
    icon: Megaphone,
    accent: "#ffb347",
    eyebrow: "Social",
    title: "Weekly social pack on a calendar.",
    description:
      "Feed tiles, stories, and ad creative classified by surface and laid out on an editable calendar.",
    bullets: [
      "Auto-classified by aspect ratio + purpose",
      "Filter by brand, run, or surface",
      "One-click handoff to the studio",
      "Asset versions tracked end-to-end",
    ],
    href: "/sign-up",
  },
  {
    id: "studio",
    icon: PaintBucket,
    accent: "#ff6a4d",
    eyebrow: "Studio",
    title: "Open canvas with critique loops.",
    description:
      "Drop any asset onto a canvas, request critiques, and iterate until it's ready to ship. Every step lands back in the asset library.",
    bullets: [
      "Critique presets per brand",
      "Layered versions with diff view",
      "Quick export to packaging / social",
      "Approve-and-publish handoff",
    ],
    href: "/sign-up",
  },
  {
    id: "campaigns",
    icon: Rocket,
    accent: "#00d4aa",
    eyebrow: "Campaigns",
    title: "Coordinate launches across channels.",
    description:
      "Plan email, social, ads, storefront, and packaging from a single launch timeline — with checklists you can actually run.",
    bullets: [
      "Calendar of moments across channels",
      "Asset roll-up by campaign",
      "Live status across every workstream",
      "Bring-your-own integration targets",
    ],
    href: "/sign-up",
  },
  {
    id: "chat",
    icon: MessageSquare,
    accent: "#4d9fff",
    eyebrow: "Chat",
    title: "Direct line to your models.",
    description:
      "Stream completions from any provider, with full cost accounting, history, and a per-workspace system prompt.",
    bullets: [
      "Streaming responses with token + cost tracking",
      "Switch providers mid-conversation",
      "Conversations saved locally and per-workspace",
      "Bring your own keys",
    ],
    href: "/sign-up",
  },
  {
    id: "models",
    icon: Cpu,
    accent: "#a24bff",
    eyebrow: "Models",
    title: "Bring your own provider.",
    description:
      "Route each capability — chat, image, video, embeddings — to the provider you prefer, per workspace.",
    bullets: [
      "OpenAI, Anthropic, Google, and OpenAI-compatible endpoints",
      "Per-capability default routing",
      "Live test playground",
      "Cost reports per provider",
    ],
    href: "/sign-up",
  },
  {
    id: "memory",
    icon: Brain,
    accent: "#00d4aa",
    eyebrow: "Memory",
    title: "A brain that compounds.",
    description:
      "Every run, asset, and decision writes into a per-brand memory graph that future runs can read — so the second campaign starts smarter than the first.",
    bullets: [
      "Per-brand context snapshot",
      "Timeline of every decision",
      "Memory graph queryable by depth",
      "References surface in chat + workflows",
    ],
    href: "/sign-up",
  },
  {
    id: "assets",
    icon: ImageIcon,
    accent: "#4d7bff",
    eyebrow: "Assets",
    title: "One library, every output.",
    description:
      "Every artifact a workflow produces flows into a single asset library, filterable by brand, kind, and run.",
    bullets: [
      "S3-backed storage with signed URLs",
      "Thumbnails + previews built in",
      "Linked back to the run that made them",
      "Search and filter by every dimension",
    ],
    href: "/sign-up",
  },
  {
    id: "integrations",
    icon: Plug,
    accent: "#ffb347",
    eyebrow: "Integrations",
    title: "Connect the rest of your stack.",
    description:
      "OAuth and token-based integrations for messaging, social, deploy targets, and storage providers.",
    bullets: [
      "OAuth and token auth flows",
      "Per-workspace connection state",
      "Live status indicators",
      "Easy disconnect + reconnect",
    ],
    href: "/sign-up",
  },
];

const PLATFORM_PROPS: {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  title: string;
  blurb: string;
}[] = [
  {
    icon: Database,
    title: "Postgres-backed",
    blurb:
      "Every brand, run, asset, and event lives in Postgres with Alembic migrations.",
  },
  {
    icon: GitBranch,
    title: "Run history is durable",
    blurb:
      "Replay any run, fork from any node, and audit decisions weeks later.",
  },
  {
    icon: Activity,
    title: "Live streaming",
    blurb:
      "Run status, chat completions, and workflow events all stream in real time.",
  },
  {
    icon: ShieldCheck,
    title: "Workspace isolation",
    blurb:
      "Workspaces own brands, integrations, and billing. Members never see each other's data.",
  },
  {
    icon: KeyRound,
    title: "Bring your own keys",
    blurb:
      "Model provider keys live per-workspace. You pay the provider, never us, for inference.",
  },
  {
    icon: Layers,
    title: "Composable from day one",
    blurb:
      "Every capability is a graph of steps you can rewire, replay, or fork.",
  },
];

export default function FeaturesPage() {
  return (
    <MarketingShell>
      <div className="absolute top-[10%] right-0 w-[600px] h-[600px] rounded-full bg-[rgba(162,75,255,0.012)] blur-[140px] pointer-events-none" />
      <div className="absolute top-[60%] -left-32 w-[500px] h-[500px] rounded-full bg-[rgba(255,106,77,0.008)] blur-[130px] pointer-events-none" />

      {/* ===== Hero ===== */}
      <Reveal>
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 pt-16 md:pt-24 pb-12 md:pb-16 text-center space-y-6">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[rgba(162,75,255,0.08)] border border-[rgba(162,75,255,0.18)] text-[10px] text-purple-300 font-bold uppercase tracking-widest">
          <Sparkles size={11} />
          <span>Features</span>
        </div>
        <h1 className="font-display text-4xl sm:text-6xl md:text-[80px] font-light tracking-[-0.025em] text-white leading-[1.02] max-w-3xl mx-auto text-balance">
          Everything Helix does — under the hood.
        </h1>
        <p className="text-[16px] sm:text-[17px] text-[var(--color-slate)] leading-relaxed max-w-2xl mx-auto">
          A tour of the surfaces, workflows, and platform primitives that make
          Helix more than a stitched-together pile of prompts.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <Link href="/sign-up">
            <Button
              variant="glow"
              size="lg"
              className="h-12 px-6 font-bold rounded-xl"
            >
              Start building free
            </Button>
          </Link>
          <Link href="/pricing">
            <Button
              variant="secondary"
              size="lg"
              className="h-12 px-6 font-bold rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-white"
            >
              See pricing
            </Button>
          </Link>
        </div>
      </section>
      </Reveal>

      {/* ===== Section directory ===== */}
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-8 border-t border-white/[0.04]">
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2.5">
          {SECTIONS.map((s) => {
            const Icon = s.icon;
            return (
              <a
                key={s.id}
                href={`#${s.id}`}
                className="group flex items-center gap-2 px-3 py-2 rounded-lg border border-white/[0.06] bg-[#13141a]/90 hover:border-purple-500/30 hover:bg-[#1a1c24] hover:scale-[1.03] hover:-translate-y-0.5 cursor-pointer shadow-[0_2px_8px_rgba(0,0,0,0.4)] hover:shadow-[0_6px_20px_rgba(162,75,255,0.06)] transition-all duration-300"
              >
                <span
                  className="size-6 rounded-md flex items-center justify-center"
                  style={{
                    background: `${s.accent}14`,
                    border: `1px solid ${s.accent}33`,
                    color: s.accent,
                  }}
                >
                  <Icon size={11} />
                </span>
                <span className="text-[11px] font-semibold text-white/80 group-hover:text-white">
                  {s.eyebrow}
                </span>
              </a>
            );
          })}
        </div>
      </section>

      {/* ===== Sections ===== */}
      {SECTIONS.map((s, idx) => {
        const Icon = s.icon;
        const flipped = idx % 2 === 1;
        return (
          <section
            key={s.id}
            id={s.id}
            className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-16 md:py-20 border-t border-white/[0.04]"
          >
            <div
              className={`grid grid-cols-1 lg:grid-cols-12 gap-10 items-center ${
                flipped ? "lg:flex-row-reverse" : ""
              }`}
            >
              <div
                className={`space-y-5 ${
                  flipped ? "lg:col-span-7 lg:order-2" : "lg:col-span-7"
                }`}
              >
                <div className="flex items-center gap-2">
                  <div
                    className="size-8 rounded-lg flex items-center justify-center"
                    style={{
                      background: `${s.accent}14`,
                      border: `1px solid ${s.accent}33`,
                      color: s.accent,
                    }}
                  >
                    <Icon size={15} />
                  </div>
                  <span
                    className="text-[11px] font-bold uppercase tracking-widest"
                    style={{ color: s.accent }}
                  >
                    {s.eyebrow}
                  </span>
                </div>
                <h2 className="font-display text-3xl sm:text-5xl font-light tracking-[-0.018em] text-white leading-[1.05] max-w-xl text-balance">
                  {s.title}
                </h2>
                <p className="text-[15px] text-[var(--color-slate)] leading-relaxed max-w-xl">
                  {s.description}
                </p>
                <ul className="space-y-2 pt-2">
                  {s.bullets.map((b) => (
                    <li
                      key={b}
                      className="flex items-start gap-2 text-[13px] text-white/85"
                    >
                      <CheckCircle2
                        size={14}
                        className="mt-0.5 shrink-0"
                        style={{ color: s.accent }}
                      />
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
                <div className="pt-2">
                  <Link href={s.href}>
                    <Button
                      variant="glow"
                      size="md"
                      className="group h-10 px-5 font-bold rounded-xl text-white flex items-center gap-1.5 cursor-pointer transition-all duration-300 hover:opacity-90"
                      style={{
                        background: `linear-gradient(135deg, ${s.accent} 0%, ${s.accent}bb 100%)`,
                        boxShadow: `0 0 15px ${s.accent}33`,
                      }}
                    >
                      Try it
                      <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
                    </Button>
                  </Link>
                </div>
              </div>

              <Link
                href={s.href}
                className={`group/card block ${
                  flipped ? "lg:col-span-5 lg:order-1" : "lg:col-span-5"
                }`}
              >
                <div
                  className="relative aspect-square rounded-2xl border border-white/[0.08] bg-[#13141a] overflow-hidden p-8 flex items-center justify-center transition-all duration-300 group-hover/card:border-white/[0.18] group-hover/card:scale-[1.015] group-hover/card:-translate-y-1 cursor-pointer"
                  style={{
                    background: `radial-gradient(circle at 30% 30%, ${s.accent}22, transparent 60%), #13141acc`,
                    boxShadow: `0 4px 20px rgba(0,0,0,0.5)`,
                  }}
                >
                  <div
                    className="absolute inset-0 opacity-30 pointer-events-none group-hover/card:opacity-40 transition-opacity duration-300"
                    style={{
                      background: `radial-gradient(circle at 70% 70%, ${s.accent}33, transparent 50%)`,
                    }}
                  />
                  <Icon
                    size={120}
                    className="relative transition-transform duration-500 group-hover/card:scale-110"
                    style={{ color: s.accent, opacity: 0.85 }}
                  />
                </div>
              </Link>
            </div>
          </section>
        );
      })}

      {/* ===== Platform props ===== */}
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-16 md:py-24 border-t border-white/[0.04]">
        <div className="text-center max-w-2xl mx-auto space-y-3 mb-12">
          <p className="text-[11px] font-bold uppercase tracking-widest text-purple-300">
            Platform
          </p>
          <h2 className="font-display text-3xl sm:text-5xl font-light tracking-[-0.018em] text-white text-balance">
            Built on durable primitives.
          </h2>
          <p className="text-[15px] text-[var(--color-slate)] leading-relaxed">
            The surfaces above ride on a small set of well-defined platform
            primitives. No magic, no lock-in.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {PLATFORM_PROPS.map((p) => {
            const Icon = p.icon;
            return (
              <div
                key={p.title}
                className="p-5 rounded-xl border border-white/[0.04] bg-[#13141a]/40 backdrop-blur-sm space-y-3 cursor-default transition-colors duration-300 hover:border-white/[0.08]"
              >
                <div className="size-9 rounded-lg flex items-center justify-center bg-white/[0.04] border border-white/[0.05] text-white/80">
                  <Icon size={16} />
                </div>
                <div className="text-[15px] font-semibold text-white">
                  {p.title}
                </div>
                <p className="text-[13px] leading-relaxed text-[var(--color-slate)]">
                  {p.blurb}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ===== Final CTA ===== */}
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-20 md:py-24">
        <div className="relative rounded-3xl border border-white/[0.06] bg-gradient-to-br from-[#13141a] via-[#0d0e12] to-[#0a0b0e] p-10 md:p-16 text-center">
          <div className="space-y-5 max-w-2xl mx-auto">
            <h2 className="font-display text-3xl sm:text-5xl md:text-6xl font-light tracking-[-0.022em] text-white leading-[1.05] text-balance">
              Ready to spin up your first brand?
            </h2>
            <p className="text-[15px] text-[var(--color-slate)] leading-relaxed">
              The free tier covers your first workspace, first brand, and first
              workflow runs. No card.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Link href="/sign-up">
                <Button
                  variant="glow"
                  size="lg"
                  className="h-12 px-6 font-bold rounded-xl"
                >
                  Get started free
                </Button>
              </Link>
              <Link href="/contact">
                <Button
                  variant="secondary"
                  size="lg"
                  className="h-12 px-6 font-bold rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-white"
                >
                  Talk to us
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </MarketingShell>
  );
}
