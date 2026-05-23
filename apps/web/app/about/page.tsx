"use client";

import Link from "next/link";
import { ArrowRight, Compass, Hexagon, Layers, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MarketingShell } from "@/components/layout/marketing-shell";

/**
 * /about — company / product story page.
 *
 * All content describes the actual product and the principles behind it.
 * No fake teams, fake investors, fake offices, or fictitious milestones.
 */

const PRINCIPLES: { icon: typeof Sparkles; title: string; body: string }[] = [
  {
    icon: Layers,
    title: "One operating system, not ten dashboards.",
    body: "Brand, packaging, websites, social, studio, and campaigns live on the same data layer. Move from one to the next without copy-pasting context.",
  },
  {
    icon: Hexagon,
    title: "Memory compounds.",
    body: "Every brief, asset, and run feeds a persistent memory graph. The system gets sharper on your brand the more you use it.",
  },
  {
    icon: Compass,
    title: "Bring your own model.",
    body: "Plug your own keys for OpenAI, Anthropic, or open-source providers. Helix is the surface, you stay in control of the substrate.",
  },
  {
    icon: Sparkles,
    title: "Composable from day one.",
    body: "Every workflow is a directed graph of skills. Fork it, edit it, version it. There is no magic black box you have to live with.",
  },
];

const TIMELINE: { phase: string; title: string; body: string }[] = [
  {
    phase: "Origin",
    title: "Built inside a working studio.",
    body: "Helix started as the internal tool we used to run brand and creative work for food and consumer brands. We needed something that respected the actual workflow, not a glorified prompt box.",
  },
  {
    phase: "Today",
    title: "An operating system for creative teams.",
    body: "Brands, workflows, packaging, websites, social, studio, campaigns, chat, models, memory, assets, and integrations are all first-class. The whole stack is open to inspection and extension.",
  },
  {
    phase: "Tomorrow",
    title: "Open to the rest of your stack.",
    body: "We are extending integrations into the channels your team already lives in — review queues, project management, content scheduling, and analytics — so Helix becomes the connective tissue rather than another silo.",
  },
];

export default function AboutPage() {
  return (
    <MarketingShell>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10 opacity-60">
          <div className="absolute top-[-15%] left-[15%] w-[520px] h-[520px] rounded-full blur-[140px] bg-[#ff6a4d]/15" />
          <div className="absolute top-[20%] right-[5%] w-[480px] h-[480px] rounded-full blur-[140px] bg-[#a24bff]/15" />
        </div>
        <div className="max-w-5xl mx-auto px-6 sm:px-8 pt-28 pb-20 text-center">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/[0.08] text-[10px] font-bold uppercase tracking-[0.18em] text-white/70 bg-white/[0.02]">
            <Sparkles size={11} />
            About Helix
          </span>
          <h1 className="mt-7 text-[clamp(2.4rem,5vw,4.2rem)] font-bold leading-[1.04] tracking-tight">
            We are building the{" "}
            <span className="bg-gradient-to-r from-[#ff6a4d] via-[#ff3d7f] to-[#a24bff] bg-clip-text text-transparent">
              creative operating system
            </span>{" "}
            for the next era of brands.
          </h1>
          <p className="mt-7 mx-auto max-w-2xl text-[16px] leading-relaxed text-[var(--color-slate)]">
            Helix is for the teams who ship brand and creative work end-to-end —
            from positioning to packaging to launch — and want the whole stack
            on one surface, with their own models, their own memory, and their
            own data.
          </p>
        </div>
      </section>

      {/* Principles */}
      <section className="max-w-7xl mx-auto px-6 sm:px-8 py-16">
        <div className="max-w-2xl">
          <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--color-stone)]">
            Principles
          </span>
          <h2 className="mt-4 text-[clamp(1.8rem,3.5vw,2.6rem)] font-bold leading-tight tracking-tight">
            What we believe creative software should be.
          </h2>
        </div>
        <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-5">
          {PRINCIPLES.map((p) => {
            const Icon = p.icon;
            return (
              <div
                key={p.title}
                className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-7 hover:border-white/[0.12] hover:bg-white/[0.035] transition-all"
              >
                <div className="inline-flex w-11 h-11 rounded-xl items-center justify-center bg-white/[0.04] border border-white/[0.08]">
                  <Icon size={18} className="text-white" />
                </div>
                <h3 className="mt-5 text-lg font-semibold tracking-tight text-white">
                  {p.title}
                </h3>
                <p className="mt-2 text-[14px] leading-relaxed text-[var(--color-slate)]">
                  {p.body}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Story / timeline */}
      <section className="max-w-7xl mx-auto px-6 sm:px-8 py-16">
        <div className="max-w-2xl">
          <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--color-stone)]">
            Story
          </span>
          <h2 className="mt-4 text-[clamp(1.8rem,3.5vw,2.6rem)] font-bold leading-tight tracking-tight">
            From studio tool to operating system.
          </h2>
        </div>
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-5">
          {TIMELINE.map((t, i) => (
            <div
              key={t.phase}
              className="relative rounded-2xl border border-white/[0.06] bg-white/[0.02] p-7"
            >
              <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[var(--color-stone)]">
                {String(i + 1).padStart(2, "0")} · {t.phase}
              </div>
              <h3 className="mt-3 text-lg font-semibold tracking-tight text-white">
                {t.title}
              </h3>
              <p className="mt-2 text-[14px] leading-relaxed text-[var(--color-slate)]">
                {t.body}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* What we ship */}
      <section className="max-w-7xl mx-auto px-6 sm:px-8 py-16">
        <div className="rounded-3xl border border-white/[0.08] bg-gradient-to-br from-white/[0.04] to-white/[0.01] p-10 md:p-14">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-start">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--color-stone)]">
                What we ship
              </span>
              <h2 className="mt-4 text-[clamp(1.8rem,3.5vw,2.4rem)] font-bold leading-tight tracking-tight">
                Real surfaces, not screenshots.
              </h2>
              <p className="mt-4 text-[15px] leading-relaxed text-[var(--color-slate)]">
                Helix is shipped as a working product, not a deck. Every section
                of this site links into a surface you can use today.
              </p>
              <div className="mt-7 flex flex-wrap gap-3">
                <Link href="/features">
                  <Button variant="secondary" size="md">
                    Browse features
                  </Button>
                </Link>
                <Link href="/sign-up">
                  <Button
                    variant="glow"
                    size="md"
                    className="font-bold uppercase tracking-wider"
                  >
                    Get started
                    <ArrowRight size={14} className="ml-2" />
                  </Button>
                </Link>
              </div>
            </div>
            <ul className="space-y-3 text-[14px] text-[var(--color-slate)]">
              {[
                "Brand canvases with positioning, voice, mission, and visual identity.",
                "Composable workflow runs with live streaming and durable history.",
                "Packaging, websites, social, studio, and campaigns on one data layer.",
                "Direct chat with whichever models you connect.",
                "A workspace-isolated memory graph that compounds over time.",
              ].map((line) => (
                <li key={line} className="flex items-start gap-3">
                  <span className="mt-2 inline-block w-1.5 h-1.5 rounded-full bg-gradient-to-r from-[#ff6a4d] to-[#a24bff]" />
                  <span>{line}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="max-w-5xl mx-auto px-6 sm:px-8 py-24 text-center">
        <h2 className="text-[clamp(2rem,4vw,3.2rem)] font-bold tracking-tight leading-[1.05]">
          Run brand and creative on one operating system.
        </h2>
        <p className="mt-5 mx-auto max-w-xl text-[15px] leading-relaxed text-[var(--color-slate)]">
          Spin up a workspace, connect your model keys, define a brand, and ship
          your first asset.
        </p>
        <div className="mt-9 flex flex-wrap justify-center gap-3">
          <Link href="/sign-up">
            <Button
              variant="glow"
              size="lg"
              className="font-bold uppercase tracking-wider"
            >
              Get started
              <ArrowRight size={14} className="ml-2" />
            </Button>
          </Link>
          <Link href="/contact">
            <Button variant="secondary" size="lg">
              Talk to us
            </Button>
          </Link>
        </div>
      </section>
    </MarketingShell>
  );
}
