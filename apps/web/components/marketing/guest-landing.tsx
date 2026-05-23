"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Boxes,
  Brain,
  CheckCircle2,
  Cpu,
  Image as ImageIcon,
  LineChart,
  Megaphone,
  MessageSquare,
  Network,
  Package,
  PaintBucket,
  Rocket,
  Sparkles,
  Workflow,
  Zap,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { MarketingShell } from "@/components/layout/marketing-shell";
import {
  Reveal,
  RevealItem,
  RevealStagger,
} from "@/components/marketing/reveal";

/**
 * Public guest landing page. Rendered for unauthenticated visitors on `/`.
 *
 * No mock testimonials, fabricated user counts, or placeholder brand logos —
 * every section describes a real capability that's wired up in the product.
 */

interface Capability {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  title: string;
  blurb: string;
  href: string;
  accent: string;
}

const CAPABILITIES: Capability[] = [
  {
    icon: Sparkles,
    title: "Brand identity",
    blurb:
      "Generate a complete brand system — voice, palette, typography, archetype — from a single brief.",
    href: "/features#brand",
    accent: "#ff3d7f",
  },
  {
    icon: Package,
    title: "Packaging artwork",
    blurb:
      "Print-ready labels, boxes, cups and bags. SKU artwork that stays on-brand at scale.",
    href: "/features#packaging",
    accent: "#a24bff",
  },
  {
    icon: Boxes,
    title: "Websites on Vercel",
    blurb:
      "Spin up a Next.js marketing site for any brand and deploy it to Vercel in a single workflow.",
    href: "/features#websites",
    accent: "#4d7bff",
  },
  {
    icon: Megaphone,
    title: "Social pack",
    blurb:
      "A week of feed tiles, stories and ad creative — laid out on a calendar you can edit.",
    href: "/features#social",
    accent: "#ffb347",
  },
  {
    icon: PaintBucket,
    title: "Creative studio",
    blurb:
      "An open canvas with critique loops to iterate on visuals until they're ready to ship.",
    href: "/features#studio",
    accent: "#ff7a4d",
  },
  {
    icon: Rocket,
    title: "Launch campaigns",
    blurb:
      "Coordinate launches across email, social, ads and storefront from one timeline.",
    href: "/features#campaigns",
    accent: "#00d4aa",
  },
];

interface Pillar {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  title: string;
  blurb: string;
  color: string;
}

const PILLARS: Pillar[] = [
  {
    icon: Brain,
    title: "Brand memory",
    blurb:
      "Every workflow writes back into a per-brand memory graph — voice, palette, references, decisions — so the next run starts smarter than the last.",
    color: "#a24bff",
  },
  {
    icon: Workflow,
    title: "Composable workflows",
    blurb:
      "Each capability is a graph of steps you can swap, branch and rerun. Inspect any node, replay a run, fork a variant.",
    color: "#4d7bff",
  },
  {
    icon: Network,
    title: "Bring your own model",
    blurb:
      "Plug in OpenAI, Anthropic, Google or your own endpoints. Route by capability — text, image, video, embeddings — per workspace.",
    color: "#00d4aa",
  },
];

interface Step {
  n: string;
  title: string;
  blurb: string;
}

const STEPS: Step[] = [
  {
    n: "01",
    title: "Define a brand",
    blurb:
      "Start from a brief or a URL. Helix extracts voice, audience and positioning into a structured brand record.",
  },
  {
    n: "02",
    title: "Run a workflow",
    blurb:
      "Pick a slice — packaging, website, social, campaign — and watch it execute step by step with live output.",
  },
  {
    n: "03",
    title: "Ship & iterate",
    blurb:
      "Approve outputs, push to channels, then loop critiques back into the brand memory for the next run.",
  },
];

interface Surface {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  label: string;
  href: string;
}

const SURFACES: Surface[] = [
  { icon: Sparkles, label: "Brands", href: "/features#brand" },
  { icon: Workflow, label: "Workflows", href: "/features#workflows" },
  { icon: ImageIcon, label: "Asset library", href: "/features#assets" },
  { icon: MessageSquare, label: "Chat", href: "/features#chat" },
  { icon: Cpu, label: "Models", href: "/features#models" },
  { icon: LineChart, label: "Memory graph", href: "/features#memory" },
];

const HERO_VIDEO_SRC =
  "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260418_115655_b4d9cd77-feed-43cd-a198-af78ebdf1f7a.mp4";

function HeroPreview() {
  return (
    <div className="relative w-full max-w-[560px] mx-auto">
      <div className="absolute -inset-6 rounded-3xl bg-gradient-to-tr from-[#a24bff]/15 via-[#ff6a4d]/8 to-transparent blur-3xl opacity-60 pointer-events-none" />

      <div className="relative rounded-2xl border border-white/[0.07] bg-[#0d0e12]/85 shadow-[0_24px_80px_rgba(0,0,0,0.6)] overflow-hidden backdrop-blur-md">
        <div className="flex items-center gap-1.5 px-4 py-2.5 bg-zinc-950/80 border-b border-white/[0.04]">
          <div className="w-2.5 h-2.5 rounded-full bg-rose-500/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-amber-500/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/60" />
          <div className="ml-3 text-[10px] font-mono text-[var(--color-stone)]">
            helix.app — live preview
          </div>
        </div>

        <div className="relative aspect-video bg-black overflow-hidden">
          <video
            src={HERO_VIDEO_SRC}
            autoPlay
            loop
            muted
            playsInline
            preload="metadata"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-tr from-[#a24bff]/0 via-transparent to-[#ff6a4d]/10 pointer-events-none" />
        </div>
      </div>
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function HeroPreviewMock() {
  return (
    <div className="relative w-full max-w-[560px] mx-auto">
      <div className="absolute -inset-6 rounded-3xl bg-gradient-to-tr from-[#a24bff]/15 via-[#ff6a4d]/8 to-transparent blur-3xl opacity-60 pointer-events-none" />

      <div className="relative rounded-2xl border border-white/[0.07] bg-[#0d0e12]/85 shadow-[0_24px_80px_rgba(0,0,0,0.6)] overflow-hidden backdrop-blur-md">
        <div className="flex items-center gap-1.5 px-4 py-2.5 bg-zinc-950/80 border-b border-white/[0.04]">
          <div className="w-2.5 h-2.5 rounded-full bg-rose-500/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-amber-500/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/60" />
          <div className="ml-3 text-[10px] font-mono text-[var(--color-stone)]">
            helix.app — command center
          </div>
        </div>

        <div className="flex h-[320px]">
          <aside className="hidden sm:flex w-32 shrink-0 bg-[#0a0b0e]/80 border-r border-white/[0.04] p-2.5 flex-col gap-1.5">
            <div className="h-5 rounded bg-white/[0.08]" />
            {[60, 75, 50, 80, 65, 70].map((w, i) => (
              <div
                key={i}
                className={`h-4 rounded ${
                  i === 2
                    ? "bg-purple-500/15 border border-purple-500/25"
                    : "bg-white/[0.04]"
                }`}
                style={{ width: `${w}%` }}
              />
            ))}
          </aside>

          <div className="flex-1 p-4 space-y-3 bg-[#07080a]/40 overflow-hidden">
            <div className="flex justify-between items-center">
              <div className="h-4 rounded bg-white/[0.08] w-28" />
              <div className="h-4 rounded bg-purple-500/20 w-16" />
            </div>

            <div className="grid grid-cols-3 gap-2">
              {["coral", "purple", "teal"].map((c, i) => (
                <div
                  key={i}
                  className="p-2.5 rounded-md border border-white/[0.04] bg-white/[0.015] space-y-1.5"
                >
                  <div className="h-2 rounded bg-white/[0.06] w-2/3" />
                  <div
                    className="h-4 rounded"
                    style={{
                      background:
                        c === "coral"
                          ? "rgba(255,106,77,0.45)"
                          : c === "purple"
                            ? "rgba(162,75,255,0.45)"
                            : "rgba(0,212,170,0.45)",
                      width: "85%",
                    }}
                  />
                </div>
              ))}
            </div>

            <div className="relative h-28 rounded-lg border border-white/[0.04] bg-[#0d0e12]/80 overflow-hidden p-2">
              <div className="text-[9px] font-mono text-white/40 uppercase tracking-wider">
                runs / last 24h
              </div>
              <svg
                className="absolute inset-x-0 bottom-0 w-full h-20"
                viewBox="0 0 200 60"
                preserveAspectRatio="none"
              >
                <defs>
                  <linearGradient id="lp1" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#a24bff" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="#a24bff" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <path
                  d="M 0 50 L 25 38 L 50 42 L 75 28 L 100 30 L 125 18 L 150 22 L 175 10 L 200 14 L 200 60 L 0 60 Z"
                  fill="url(#lp1)"
                />
                <path
                  d="M 0 50 L 25 38 L 50 42 L 75 28 L 100 30 L 125 18 L 150 22 L 175 10 L 200 14"
                  fill="none"
                  stroke="#a24bff"
                  strokeWidth="1.5"
                />
              </svg>
            </div>

            <div className="space-y-1.5">
              {[
                { label: "brand_identity", status: "succeeded", color: "#00d4aa" },
                { label: "packaging_suite", status: "running", color: "#4d9fff" },
                { label: "social_pack", status: "queued", color: "#ffb347" },
              ].map((r, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded border border-white/[0.04] bg-white/[0.01] px-2.5 py-1.5"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className="w-1.5 h-1.5 rounded-full"
                      style={{
                        background: r.color,
                        boxShadow:
                          r.status === "running"
                            ? `0 0 6px ${r.color}`
                            : undefined,
                      }}
                    />
                    <span className="text-[10px] font-mono text-white/70">
                      {r.label}
                    </span>
                  </div>
                  <span
                    className="text-[9px] uppercase tracking-wider font-semibold"
                    style={{ color: r.color }}
                  >
                    {r.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function GuestLanding() {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const streamUrl = "https://stream.mux.com/8wrHPCX2dC3msyYU9ObwqNdm00u3ViXvOSHUMRYSEe5Q.m3u8";

    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = streamUrl;
    } else {
      let active = true;
      const script = document.createElement("script");
      script.src = "https://cdn.jsdelivr.net/npm/hls.js@1.5.8/dist/hls.min.js";
      script.async = true;
      script.onload = () => {
        if (!active) return;
        // @ts-ignore
        if (window.Hls && window.Hls.isSupported()) {
          // @ts-ignore
          const hls = new window.Hls();
          hls.loadSource(streamUrl);
          hls.attachMedia(video);
        }
      };
      document.head.appendChild(script);
      return () => {
        active = false;
        script.remove();
      };
    }
  }, []);

  return (
    <MarketingShell>
      {/* Immersive Looping Mux HLS Video Background */}
      <video
        ref={videoRef}
        autoPlay
        loop
        muted
        playsInline
        className="pointer-events-none fixed inset-0 w-full h-full object-cover -z-20 opacity-[0.25]"
        style={{ filter: "brightness(0.6) contrast(1.15) saturate(1.15)" }}
      />
      {/* ===== Hero ===== */}
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 pt-12 md:pt-20 pb-16 md:pb-24 grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-center">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
          className="lg:col-span-6 space-y-7"
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[rgba(240,115,74,0.06)] border border-[rgba(240,115,74,0.22)] text-[10px] text-[var(--color-signature)] font-semibold uppercase tracking-[0.18em]">
            <Sparkles className="size-3" />
            <span>The creative OS for restaurants & food brands</span>
          </div>

          <h1 className="font-display text-[44px] sm:text-[60px] lg:text-[72px] font-light tracking-[-0.02em] text-white leading-[1.02] text-balance">
            Run brand, creative, and{" "}
            <span className="font-display-italic text-gradient-signature font-normal">
              campaigns
            </span>{" "}
            from one OS.
          </h1>

          <div className="hairline-divider w-24" aria-hidden />

          <p className="text-[17px] leading-[1.7] text-[var(--color-slate)] max-w-[52ch] text-pretty">
            Helix turns a brief into a complete brand system, packaging
            artwork, a website on Vercel, social content, and a launch
            campaign — all wired together with a per-brand memory.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Link href="/sign-up">
              <Button
                variant="glow"
                size="lg"
                className="h-12 px-6 font-bold tracking-tight rounded-xl flex items-center gap-2 group"
              >
                <span>Start building free</span>
                <ArrowRight
                  size={16}
                  className="transition-transform group-hover:translate-x-0.5"
                />
              </Button>
            </Link>
            <Link href="/pricing">
              <Button
                variant="secondary"
                size="lg"
                className="h-12 px-6 font-bold tracking-tight rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-white"
              >
                See pricing
              </Button>
            </Link>
          </div>

          <ul className="flex flex-wrap gap-x-6 gap-y-2 pt-2 text-[12px] text-[var(--color-slate)]">
            {[
              "No credit card required",
              "Bring your own model keys",
              "Free tier included",
            ].map((t) => (
              <li key={t} className="flex items-center gap-1.5">
                <CheckCircle2 size={13} className="text-[#00d4aa]" />
                <span>{t}</span>
              </li>
            ))}
          </ul>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.65, delay: 0.1 }}
          className="lg:col-span-6"
        >
          <HeroPreview />
        </motion.div>
      </section>

      {/* ===== Capability grid ===== */}
      <section
        id="capabilities"
        className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-16 md:py-24 border-t border-white/[0.04]"
      >
        <Reveal>
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-12">
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-signature)]">
              Capabilities
            </p>
            <h2 className="font-display text-3xl sm:text-5xl font-light tracking-[-0.015em] text-white text-balance">
              Six workflows, one connected brain.
            </h2>
            <p className="text-[15px] text-[var(--color-slate)] leading-relaxed">
              Each capability is a composable workflow you can run, inspect,
              replay, and remix. Outputs flow into a shared asset library and a
              per-brand memory graph.
            </p>
          </div>
        </Reveal>

        <RevealStagger className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {CAPABILITIES.map((c) => {
            const Icon = c.icon;
            return (
              <RevealItem key={c.title}>
                <Link
                  href={c.href}
                  className="group block p-5 rounded-2xl border border-white/[0.05] bg-[#0d0e12]/50 backdrop-blur-md hover:border-white/[0.12] hover:bg-[#13141a]/80 transition-all hover:-translate-y-0.5"
                >
                  <div
                    className="size-10 rounded-xl flex items-center justify-center mb-4"
                    style={{
                      background: `${c.accent}14`,
                      border: `1px solid ${c.accent}33`,
                      color: c.accent,
                    }}
                  >
                    <Icon size={18} />
                  </div>
                  <h3 className="text-[15px] font-semibold text-white mb-1.5">
                    {c.title}
                  </h3>
                  <p className="text-[13px] leading-relaxed text-[var(--color-slate)]">
                    {c.blurb}
                  </p>
                  <div className="mt-4 inline-flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wider text-white/40 group-hover:text-white transition-colors">
                    Learn more
                    <ArrowRight
                      size={11}
                      className="transition-transform group-hover:translate-x-0.5"
                    />
                  </div>
                </Link>
              </RevealItem>
            );
          })}
        </RevealStagger>
      </section>

      {/* ===== Pillars ===== */}
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-16 md:py-24 border-t border-white/[0.04]">
        <Reveal>
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-14">
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-signature)]">
              How it&apos;s different
            </p>
            <h2 className="font-display text-3xl sm:text-5xl font-light tracking-[-0.015em] text-white text-balance">
              Built like an operating system, not a tool.
            </h2>
          </div>
        </Reveal>

        <RevealStagger className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {PILLARS.map((p) => {
            const Icon = p.icon;
            return (
              <RevealItem key={p.title}>
                <div className="relative p-6 rounded-2xl border border-white/[0.05] bg-[#0d0e12]/50 overflow-hidden h-full">
                  <div
                    className="absolute -right-6 -top-6 w-24 h-24 rounded-full blur-2xl opacity-25 pointer-events-none"
                    style={{ background: p.color }}
                  />
                  <div
                    className="relative size-10 rounded-xl flex items-center justify-center mb-4"
                    style={{
                      background: `${p.color}14`,
                      border: `1px solid ${p.color}33`,
                      color: p.color,
                    }}
                  >
                    <Icon size={18} />
                  </div>
                  <h3 className="relative text-[18px] font-semibold text-white mb-2">
                    {p.title}
                  </h3>
                  <p className="relative text-[13px] leading-relaxed text-[var(--color-slate)]">
                    {p.blurb}
                  </p>
                </div>
              </RevealItem>
            );
          })}
        </RevealStagger>
      </section>

      {/* ===== Steps ===== */}
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-16 md:py-24 border-t border-white/[0.04]">
        <Reveal>
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-14">
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-signature)]">
              How it works
            </p>
            <h2 className="font-display text-3xl sm:text-5xl font-light tracking-[-0.015em] text-white text-balance">
              From brief to launch in three moves.
            </h2>
          </div>
        </Reveal>

        <RevealStagger className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {STEPS.map((s) => (
            <RevealItem key={s.n}>
              <div className="p-6 rounded-2xl border border-white/[0.05] bg-[#0d0e12]/50 space-y-3 h-full">
                <div className="text-[11px] font-mono font-bold text-purple-300 tracking-widest">
                  STEP {s.n}
                </div>
                <h3 className="text-[18px] font-semibold text-white">
                  {s.title}
                </h3>
                <p className="text-[13px] leading-relaxed text-[var(--color-slate)]">
                  {s.blurb}
                </p>
              </div>
            </RevealItem>
          ))}
        </RevealStagger>
      </section>

      {/* ===== Surfaces tour ===== */}
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-16 md:py-24 border-t border-white/[0.04]">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <Reveal className="lg:col-span-5">
            <div className="space-y-5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-signature)]">
                Inside Helix
              </p>
              <h2 className="font-display text-3xl sm:text-5xl font-light tracking-[-0.015em] text-white leading-[1.05] text-balance">
                Every surface you need, in one workspace.
              </h2>
              <p className="text-[15px] text-[var(--color-slate)] leading-relaxed">
                No more stitching together a dozen tabs. Brand, workflows,
                assets, chat, models, and memory live inside the same OS — with
                the same keyboard shortcuts and the same permissions.
              </p>
              <div className="pt-2">
                <Link href="/features">
                  <Button
                    variant="secondary"
                    size="md"
                    className="bg-white/[0.04] hover:bg-white/[0.08] text-white border-white/[0.08]"
                  >
                    Tour every surface
                  </Button>
                </Link>
              </div>
            </div>
          </Reveal>

          <RevealStagger className="lg:col-span-7 grid grid-cols-2 sm:grid-cols-3 gap-3">
            {SURFACES.map((s) => {
              const Icon = s.icon;
              return (
                <RevealItem key={s.label}>
                  <Link
                    href={s.href}
                    className="group block p-4 rounded-xl border border-white/[0.05] bg-[#0d0e12]/50 hover:border-white/[0.12] hover:bg-[#13141a]/80 transition-all"
                  >
                    <div className="size-9 rounded-lg flex items-center justify-center mb-3 bg-white/[0.04] border border-white/[0.05] text-white/80">
                      <Icon size={16} />
                    </div>
                    <div className="text-[13px] font-semibold text-white">
                      {s.label}
                    </div>
                  </Link>
                </RevealItem>
              );
            })}
          </RevealStagger>
        </div>
      </section>

      {/* ===== Final CTA ===== */}
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-20 md:py-28">
        <Reveal>
          <div className="relative overflow-hidden rounded-3xl border border-white/[0.06] bg-gradient-to-br from-[#13141a] via-[#0d0e12] to-[#0a0b0e] p-10 md:p-16 text-center">
          <div className="absolute -inset-1 bg-[radial-gradient(circle_at_30%_0%,rgba(255,106,77,0.10),transparent_40%),radial-gradient(circle_at_70%_100%,rgba(162,75,255,0.10),transparent_45%)] pointer-events-none" />

          <div className="relative space-y-6 max-w-2xl mx-auto">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] text-[10px] text-white/70 font-semibold uppercase tracking-widest">
              <Zap size={11} className="text-[#ff6a4d]" />
              <span>Free tier — no card required</span>
            </div>
            <h2 className="font-display text-3xl sm:text-5xl md:text-6xl font-light tracking-[-0.02em] text-white leading-[1.04] text-balance">
              Spin up your first brand in a few minutes.
            </h2>
            <p className="text-[15px] text-[var(--color-slate)] leading-relaxed">
              Create an account, connect a model provider, and run your first
              workflow today. Upgrade when you outgrow the free tier — never
              before.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Link href="/sign-up">
                <Button
                  variant="glow"
                  size="lg"
                  className="h-12 px-6 font-bold tracking-tight rounded-xl flex items-center gap-2 group"
                >
                  <span>Create your workspace</span>
                  <ArrowRight
                    size={16}
                    className="transition-transform group-hover:translate-x-0.5"
                  />
                </Button>
              </Link>
              <Link href="/contact">
                <Button
                  variant="secondary"
                  size="lg"
                  className="h-12 px-6 font-bold tracking-tight rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-white"
                >
                  Talk to us
                </Button>
              </Link>
            </div>
          </div>
          </div>
        </Reveal>
      </section>
    </MarketingShell>
  );
}

/** Re-export under the legacy name used by app/page.tsx. */
export { GuestLanding as GuestLandingPage };
