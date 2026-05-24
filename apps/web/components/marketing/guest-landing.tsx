"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
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
  TrendingUp,
  Users,
  Workflow,
  Zap,
  Terminal,
  Palette,
  Play,
  RotateCcw,
  Activity,
  Layout
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { MarketingShell } from "@/components/layout/marketing-shell";
import {
  Reveal,
  RevealItem,
  RevealStagger,
} from "@/components/marketing/reveal";
import { TestimonialsSection } from "@/components/marketing/testimonials";

/* ─── MOCK BRIEF TEMPLATES ────────────────────────────────── */

interface SimulatorBrief {
  id: string;
  name: string;
  category: string;
  briefText: string;
  tagline: string;
  palette: { name: string; hex: string }[];
  logoStyle: string;
  menu: { name: string; price: string }[];
  packagingType: string;
  iconName: string;
}

const BRIEF_PRESETS: SimulatorBrief[] = [
  {
    id: "sizzle",
    name: "Sizzle & Bun",
    category: "Gourmet Burger Kitchen",
    briefText: "A gourmet street smash burger brand with a rustic, bold, fire-cooked aesthetic.",
    tagline: "Honest ingredients. Sizzled hot.",
    palette: [
      { name: "Charcoal Ink", hex: "#111215" },
      { name: "Smash Coral", hex: "#ff6a4d" },
      { name: "Toasted Cream", hex: "#f7f1e8" },
      { name: "Mustard Gold", hex: "#ffb347" },
    ],
    logoStyle: "sans-bold",
    menu: [
      { name: "Double Smash Burger", price: "$14.50" },
      { name: "Truffle Parm Fries", price: "$6.00" },
      { name: "Smoked Bourbon Shake", price: "$7.50" },
    ],
    packagingType: "Burger Box & Wax Wrap",
    iconName: "Flame",
  },
  {
    id: "matcha",
    name: "Matcha Garden",
    category: "Organic Tea Atelier",
    briefText: "A minimalist organic stone-ground matcha bar with a clean, calm, Zen forest aesthetic.",
    tagline: "Pure stone-ground shade-grown Uji tea.",
    palette: [
      { name: "Forest Moss", hex: "#1c3d27" },
      { name: "Ceremonial Teal", hex: "#00d4aa" },
      { name: "Soft Sand", hex: "#ebdcb9" },
      { name: "Clean Ivory", hex: "#fafafc" },
    ],
    logoStyle: "serif-elegant",
    menu: [
      { name: "Ceremonial Iced Latte", price: "$6.50" },
      { name: "Uji Matcha Soft Serve", price: "$5.00" },
      { name: "Black Sesame Cookie", price: "$3.75" },
    ],
    packagingType: "Brushed Tin & Paper Tube",
    iconName: "Leaf",
  },
  {
    id: "pizza",
    name: "Pizzeria Sol",
    category: "Neapolitan Wood-Fired Pizza",
    briefText: "Naturally leavened wood-fired pizzas in a cheerful, sunlit, retro Italian vibe.",
    tagline: "Naturally leavened wood-fired bliss.",
    palette: [
      { name: "Vibrant Yellow", hex: "#ffb347" },
      { name: "Tomato Red", hex: "#ff3d7f" },
      { name: "Burnt Olive", hex: "#4d6b53" },
      { name: "Warm Dough", hex: "#faf5ec" },
    ],
    logoStyle: "retro-script",
    menu: [
      { name: "Margherita D.O.C.", price: "$16.00" },
      { name: "Spicy Salami & Honey", price: "$18.50" },
      { name: "Burrata & Sol Salad", price: "$12.00" },
    ],
    packagingType: "Hexagonal Craft Pizza Box",
    iconName: "Pizza",
  },
];

/* ─── HELIX SPECIALIST AGENTS ────────────────────────────── */

interface Agent {
  name: string;
  role: string;
  color: string;
  status: "idle" | "thinking" | "reflecting" | "writing";
  actionText: string;
}

const AGENTS: Agent[] = [
  {
    name: "CMO Agent",
    role: "Brand Strategy & Positioning",
    color: "#ff6a4d",
    status: "reflecting",
    actionText: "Analyzing market sentiment and adjusting pricing benchmarks against local competitors.",
  },
  {
    name: "Creative Director",
    role: "Aesthetic Control & Style Guides",
    color: "#ff3d7f",
    status: "thinking",
    actionText: "Scoring layout composition and grading packaging design elements against brand presets.",
  },
  {
    name: "Web Engineer",
    role: "Next.js & Vercel Auto-Deployment",
    color: "#4d7bff",
    status: "writing",
    actionText: "Generating React layout files and staging deployment triggers to Vercel edge endpoints.",
  },
  {
    name: "Packaging Specialist",
    role: "Print-Ready SKU Artwork Systems",
    color: "#a24bff",
    status: "idle",
    actionText: "Compiling vector specifications and die line outlines for direct factory export.",
  },
  {
    name: "Memory Graph Coordinator",
    role: "Persistent Vector Context Sync",
    color: "#00d4aa",
    status: "reflecting",
    actionText: "Writing back campaign performance metrics and design preferences to local postgres vector store.",
  },
];

/* ─── STATS API CONFIG ───────────────────────────────────── */

interface PlatformStats {
  brands: number;
  workspaces: number;
  runs: { total: number; completed: number; success_rate: number };
  assets: { total: number; images: number; videos: number };
  intelligence: { total_signals: number; signals_24h: number };
}

function LiveStats() {
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/public/stats")
      .then((r) => r.json())
      .then((data) => {
        setStats(data);
        setLoading(false);
      })
      .catch(() => {
        // Fallback demo stats
        setStats({
          brands: 142,
          workspaces: 87,
          runs: { total: 10420, completed: 10398, success_rate: 99.8 },
          assets: { total: 4210, images: 3980, videos: 230 },
          intelligence: { total_signals: 24890, signals_24h: 340 }
        });
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 animate-pulse">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-16 rounded-xl bg-white/[0.04]" />
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const items = [
    { label: "Active Brands", value: stats.brands, icon: Boxes },
    { label: "Workspaces", value: stats.workspaces, icon: Users },
    { label: "Workflow Runs", value: stats.runs.total, icon: TrendingUp },
    { label: "Assets Spawned", value: stats.assets.total, icon: ImageIcon },
    { label: "Intel Signals", value: stats.intelligence.total_signals, icon: BarChart3 },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <motion.div
            key={item.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 rounded-xl border border-white/[0.05] bg-[#0d0e12]/50 backdrop-blur-md hover:border-white/10 transition-colors shadow-lg"
          >
            <div className="flex items-center gap-2 mb-2">
              <Icon size={13} className="text-[#f0734a]" />
              <span className="text-[10px] uppercase tracking-wider text-[var(--color-slate)] font-semibold">
                {item.label}
              </span>
            </div>
            <div className="text-2xl font-bold text-white tabular">
              {item.value.toLocaleString()}
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

/* ─── GUEST LANDING PAGE ────────────────────────────────── */

const CAPABILITIES = [
  {
    icon: Sparkles,
    title: "Brand identity",
    blurb: "Generate a complete brand system — voice, palette, typography, archetype — from a single brief.",
    href: "/features#brand",
    accent: "#ff3d7f",
    detailText: "Produces consistent vector color sheets, brand souls, and typography pairings."
  },
  {
    icon: Package,
    title: "Packaging artwork",
    blurb: "Print-ready labels, boxes, cups and bags. SKU artwork that stays on-brand at scale.",
    href: "/features#packaging",
    accent: "#a24bff",
    detailText: "Compiles exact SVG die layouts and material instructions ready for printers."
  },
  {
    icon: Boxes,
    title: "Websites on Vercel",
    blurb: "Spin up a Next.js marketing site for any brand and deploy it to Vercel in a single workflow.",
    href: "/features#websites",
    accent: "#4d7bff",
    detailText: "Generates semantic component files, installs assets, and deploys autonomously."
  },
  {
    icon: Megaphone,
    title: "Social pack",
    blurb: "A week of feed tiles, stories and ad creative — laid out on a calendar you can edit.",
    href: "/features#social",
    accent: "#ffb347",
    detailText: "Writes copy, designs image layouts, and tracks optimal conversion schedules."
  },
  {
    icon: PaintBucket,
    title: "Creative studio",
    blurb: "An open canvas with critique loops to iterate on visuals until they're ready to ship.",
    href: "/features#studio",
    accent: "#ff7a4d",
    detailText: "Real-time AI filters, style mixing templates, and high-fidelity upscalers."
  },
  {
    icon: Rocket,
    title: "Launch campaigns",
    blurb: "Coordinate launches across email, social, ads and storefront from one timeline.",
    href: "/features#campaigns",
    accent: "#00d4aa",
    detailText: "Wires Shopify events, hooks social schedules, and rolls out pricing rules."
  },
];

const PILLARS = [
  {
    icon: Brain,
    title: "Brand memory store",
    blurb: "Every workflow writes back into a per-brand memory graph — voice, palette, decisions — so the next run starts smarter than the last.",
    color: "#a24bff",
  },
  {
    icon: Workflow,
    title: "Composable execution",
    blurb: "Each capability is a graph of steps you can swap, branch and rerun. Inspect any node, replay a run, fork a variant.",
    color: "#4d7bff",
  },
  {
    icon: Network,
    title: "Bring your own model keys",
    blurb: "Plug in OpenAI, Anthropic, Google or your own endpoints. Route by capability — text, image, video, embeddings — per workspace.",
    color: "#00d4aa",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Define a brand concept",
    blurb: "Start from a single sentence brief or a competitor URL. Helix extracts voice, positioning and style guidelines into a structured record.",
  },
  {
    n: "02",
    title: "Run automated workflows",
    blurb: "Pick a capability — packaging, website, social calendar — and watch the executive agents execute step-by-step with live visual output.",
  },
  {
    n: "03",
    title: "Approve & deploy",
    blurb: "Review high-fidelity mockups, trigger one-click Vercel and Shopify deployments, and feed critiques back into the brand memory.",
  },
];

const SURFACES = [
  { icon: Sparkles, label: "Brand Kits", href: "/features#brand" },
  { icon: Workflow, label: "Workflows", href: "/features#workflows" },
  { icon: ImageIcon, label: "Creative Library", href: "/features#assets" },
  { icon: MessageSquare, label: "Agent Council Chat", href: "/features#chat" },
  { icon: Cpu, label: "Models Portal", href: "/features#models" },
  { icon: LineChart, label: "Performance Graph", href: "/features#memory" },
];

export function GuestLanding() {
  const [selectedBrief, setSelectedBrief] = useState<SimulatorBrief>(BRIEF_PRESETS[0]);
  const [customBriefText, setCustomBriefText] = useState("");
  const [simStep, setSimStep] = useState<"idle" | "cmo" | "palette" | "logo" | "packaging" | "web" | "complete">("idle");
  const [logs, setLogs] = useState<string[]>([]);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Immersive Mux HLS Video Background hook
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
        const win = window as any;
        if (win.Hls && win.Hls.isSupported()) {
          const hls = new win.Hls();
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

  // Auto-scroll logs terminal
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  // Brand Simulator Routine
  const runSimulation = (brief: SimulatorBrief) => {
    setSelectedBrief(brief);
    setSimStep("cmo");
    setLogs([]);

    const logSteps = [
      { text: "⚡ Initializing Helix Orchestration Gateway...", delay: 200 },
      { text: "🤖 Spawning Executive Agent Council (5 agents online)...", delay: 500 },
      { text: `📝 Brief received: "${customBriefText || brief.briefText}"`, delay: 900 },
      { text: "📊 CMO AGENT: Analyzing target demographics & brand positioning...", delay: 1400 },
      { text: `💡 CMO AGENT: Brand voice set to Elevated & Artisanal; Category: ${brief.category}`, delay: 2000 },
      { text: "🎨 CREATIVE DIRECTOR: Researching optimal brand color psychology...", delay: 2600 },
      { text: "🎨 CREATIVE DIRECTOR: Generated design tokens and palettes. Moving to asset rendering.", delay: 3500 },
      { text: "⚙️ ART DIRECTOR: Rendering vector typography logo system...", delay: 4200 },
      { text: `✨ ART DIRECTOR: Custom SVG typography generated (Style: ${brief.logoStyle})`, delay: 5000 },
      { text: "📦 PACKAGING SPECIALIST: Loading carton blueprints and die lines...", delay: 5600 },
      { text: `📦 PACKAGING SPECIALIST: Applied HSL styles onto ${brief.packagingType} template. Success.`, delay: 6500 },
      { text: "🌐 WEB ENGINEER: Scaffolding high-performance Next.js layout structure...", delay: 7200 },
      { text: "🌐 WEB ENGINEER: Committing components. Triggering auto-deploy serverless hook to Vercel...", delay: 8000 },
      { text: "🚀 CMO AGENT: Finalizing campaign rollout plan and syncing persistent vector memory...", delay: 8800 },
      { text: "✅ HELIX SYSTEM: Fully Autonomous Execution Complete. All systems synced.", delay: 9500 },
    ];

    logSteps.forEach((s) => {
      setTimeout(() => {
        setLogs((prev) => [...prev, s.text]);
      }, s.delay);
    });

    // Control steps visual transitions
    setTimeout(() => setSimStep("palette"), 2800);
    setTimeout(() => setSimStep("logo"), 4800);
    setTimeout(() => setSimStep("packaging"), 6200);
    setTimeout(() => setSimStep("web"), 7800);
    setTimeout(() => setSimStep("complete"), 9800);
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customBriefText.trim()) return;

    // Create a dynamic mockup brief matching user input
    const customBrief: SimulatorBrief = {
      id: "custom",
      name: customBriefText.split(" ").slice(0, 2).join(" ") || "Your Brand",
      category: "Bespoke Culinary Concept",
      briefText: customBriefText,
      tagline: "Uniquely crafted from your brief.",
      palette: [
        { name: "Primary Ink", hex: "#ff3d7f" },
        { name: "Core Accent", hex: "#a24bff" },
        { name: "Secondary Tint", hex: "#00d4aa" },
        { name: "Canvas Warmth", hex: "#faf5ec" },
      ],
      logoStyle: "sans-bold",
      menu: [
        { name: "Signature Dish", price: "$18.00" },
        { name: "Artisanal Starter", price: "$9.50" },
        { name: "Bespoke Nectar", price: "$6.00" },
      ],
      packagingType: "Custom Wrapped Bag & Label",
      iconName: "Sparkles",
    };

    runSimulation(customBrief);
  };

  const resetSimulator = () => {
    setSimStep("idle");
    setLogs([]);
    setCustomBriefText("");
  };

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
        style={{ filter: "brightness(0.5) contrast(1.1) saturate(1.15)" }}
      />

      {/* ===== Hero & Simulator Section ===== */}
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 pt-10 md:pt-16 pb-16 md:pb-24 grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-center">
        {/* Left Column - Headline & Controls */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
          className="lg:col-span-5 space-y-6"
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[rgba(240,115,74,0.06)] border border-[rgba(240,115,74,0.22)] text-[10px] text-[var(--color-signature)] font-semibold uppercase tracking-[0.18em] shadow-md">
            <Sparkles className="size-3 animate-pulse" />
            <span>The Creative OS for Food Brands & Restaurants</span>
          </div>

          <h1 className="font-display text-[44px] sm:text-[56px] lg:text-[64px] font-light tracking-[-0.02em] text-white leading-[1.04] text-balance">
            Run brand, creative, and{" "}
            <span className="font-display-italic text-gradient-signature font-normal">
              campaigns
            </span>{" "}
            from one OS.
          </h1>

          <div className="hairline-divider w-24" aria-hidden />

          <p className="text-[15px] leading-[1.6] text-[var(--color-slate)] max-w-[50ch] text-pretty">
            Helix turns a brief into a complete brand system, packaging
            artwork, a Next.js site on Vercel, and active campaign timelines —
            all synced through a persistent memory graph.
          </p>

          {/* Quick presets list */}
          <div className="space-y-3 pt-2">
            <label className="text-[10px] uppercase font-bold tracking-widest text-[var(--color-stone)]">
              Choose a concept brief to simulate
            </label>
            <div className="flex flex-wrap gap-2">
              {BRIEF_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => runSimulation(preset)}
                  disabled={simStep !== "idle" && simStep !== "complete"}
                  className={`px-3 py-1.5 rounded-full text-micro font-semibold transition-all border cursor-pointer ${
                    selectedBrief.id === preset.id && simStep !== "idle"
                      ? "bg-purple-500/20 border-purple-500/40 text-purple-300"
                      : "bg-white/[0.02] border-white/5 text-[var(--color-charcoal)] hover:border-white/10 hover:bg-white/[0.05]"
                  } disabled:opacity-50`}
                >
                  {preset.name}
                </button>
              ))}
            </div>
          </div>

          {/* Custom Prompt Input */}
          <form onSubmit={handleCustomSubmit} className="relative mt-2">
            <input
              type="text"
              placeholder="Or write custom brief (e.g. A retro Italian gelateria...)"
              value={customBriefText}
              onChange={(e) => setCustomBriefText(e.target.value)}
              disabled={simStep !== "idle" && simStep !== "complete"}
              className="w-full h-11 bg-zinc-950/60 border border-white/10 rounded-full px-5 pr-12 text-micro text-white placeholder-zinc-500 focus:outline-none focus:border-[var(--color-signature)] transition-colors shadow-inner"
            />
            <button
              type="submit"
              disabled={simStep !== "idle" && simStep !== "complete"}
              className="absolute right-1.5 top-1.5 size-8 rounded-full bg-[var(--color-signature)] hover:bg-[var(--color-signature-deep)] flex items-center justify-center text-white transition-colors cursor-pointer disabled:opacity-50"
            >
              <Play size={12} className="fill-current ml-0.5" />
            </button>
          </form>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link href="/sign-up">
              <Button
                variant="glow"
                size="lg"
                className="h-11 px-5 font-bold tracking-tight rounded-xl flex items-center gap-2 group cursor-pointer"
              >
                <span>Start building free</span>
                <ArrowRight
                  size={15}
                  className="transition-transform group-hover:translate-x-0.5"
                />
              </Button>
            </Link>
            <Link href="/pricing">
              <Button
                variant="secondary"
                size="lg"
                className="h-11 px-5 font-bold tracking-tight rounded-xl bg-white/[0.03] hover:bg-white/[0.07] text-white cursor-pointer"
              >
                See pricing
              </Button>
            </Link>
          </div>
        </motion.div>

        {/* Right Column - Brand Simulator Viewport */}
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.65, delay: 0.1 }}
          className="lg:col-span-7"
        >
          <div className="relative w-full max-w-[620px] mx-auto">
            {/* Visual Back glows */}
            <div className="absolute -inset-6 rounded-3xl bg-gradient-to-tr from-[#a24bff]/15 via-[#f0734a]/8 to-transparent blur-3xl opacity-50 pointer-events-none animate-pulse-glow" style={{ animationDuration: "8s" }} />

            {/* Core Simulator viewport container */}
            <div className="relative rounded-2xl border border-white/[0.07] bg-[#0d0e12]/85 shadow-[0_24px_80px_rgba(0,0,0,0.6)] overflow-hidden backdrop-blur-md">
              {/* Window Header */}
              <div className="flex items-center justify-between px-4 py-3 bg-zinc-950/80 border-b border-white/[0.04]">
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-rose-500/60" />
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-500/60" />
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/60" />
                  <div className="ml-3 text-[10px] font-mono text-[var(--color-stone)]">
                    helix.os — {simStep === "idle" ? "idle waiting" : `simulation: ${selectedBrief.name}`}
                  </div>
                </div>
                {simStep !== "idle" && (
                  <button
                    onClick={resetSimulator}
                    className="flex items-center gap-1 text-[9px] font-mono uppercase tracking-wider text-purple-400 hover:text-white transition-colors cursor-pointer"
                  >
                    <RotateCcw size={10} />
                    <span>Reset</span>
                  </button>
                )}
              </div>

              {/* Viewport content */}
              <div className="relative flex flex-col md:flex-row h-[380px] bg-[#07080a]/30">
                
                {/* Left Mini-Rail (Simulation Stages) */}
                <aside className="w-full md:w-36 shrink-0 bg-[#0a0b0e]/90 border-r md:border-b-0 border-b border-white/[0.04] p-3 flex md:flex-col gap-1.5 overflow-x-auto md:overflow-x-visible">
                  <div className="hidden md:block text-[9px] font-mono uppercase text-[var(--color-stone)] tracking-wider mb-2">
                    Execution DAG
                  </div>
                  {[
                    { key: "cmo", label: "Agent Council", color: "#ff6a4d" },
                    { key: "palette", label: "Brand Palette", color: "#ff3d7f" },
                    { key: "logo", label: "Creative SVG", color: "#a24bff" },
                    { key: "packaging", label: "SKU Package", color: "#00d4aa" },
                    { key: "web", label: "Vercel Deploy", color: "#4d7bff" },
                  ].map((stage) => {
                    const stepsMap = ["idle", "cmo", "palette", "logo", "packaging", "web", "complete"];
                    const stageIdx = stepsMap.indexOf(stage.key);
                    const currentIdx = stepsMap.indexOf(simStep);
                    const isActive = simStep === stage.key;
                    const isCompleted = currentIdx > stageIdx;

                    return (
                      <div
                        key={stage.key}
                        className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-[10px] font-semibold transition-all shrink-0 ${
                          isActive
                            ? "bg-purple-500/10 border border-purple-500/20 text-white"
                            : isCompleted
                            ? "text-[#00c896]"
                            : "text-[var(--color-stone)]"
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            isActive
                              ? "bg-purple-400 animate-ping"
                              : isCompleted
                              ? "bg-[#00c896]"
                              : "bg-zinc-800"
                          }`}
                          style={{
                            boxShadow: isActive ? "0 0 4px #a24bff" : undefined
                          }}
                        />
                        <span className="truncate">{stage.label}</span>
                      </div>
                    );
                  })}
                </aside>

                {/* Right Interactive View Pane */}
                <main className="flex-1 p-4 flex flex-col justify-between overflow-hidden bg-zinc-950/20">
                  <AnimatePresence mode="wait">
                    {/* IDLE state: Live video placeholder info */}
                    {simStep === "idle" && (
                      <motion.div
                        key="idle-pane"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4"
                      >
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[var(--color-signature)] to-[#a24bff] flex items-center justify-center shadow-lg shadow-purple-500/5 animate-pulse-glow">
                          <Cpu size={22} className="text-white" />
                        </div>
                        <div>
                          <h4 className="text-[13px] font-bold text-white tracking-tight">
                            Helix Autonomous Simulation Node
                          </h4>
                          <p className="text-[11px] text-[var(--color-slate)] max-w-[32ch] mx-auto mt-1 leading-relaxed">
                            Select a preset brand concept above or type a brief to watch the Executive Council construct a system.
                          </p>
                        </div>
                        <button
                          onClick={() => runSimulation(BRIEF_PRESETS[0])}
                          className="px-4 h-8 text-[10px] font-bold uppercase tracking-wider bg-white text-zinc-950 hover:bg-zinc-200 transition-colors rounded-full flex items-center gap-1.5 shadow-md cursor-pointer"
                        >
                          <Play size={8} className="fill-current" />
                          <span>Simulate &apos;Sizzle &amp; Bun&apos;</span>
                        </button>
                      </motion.div>
                    )}

                    {/* CMO Analysis Logs state */}
                    {simStep === "cmo" && (
                      <motion.div
                        key="cmo-pane"
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="h-full flex flex-col justify-between"
                      >
                        <div className="flex items-center gap-2 pb-2 border-b border-white/[0.04]">
                          <Terminal size={14} className="text-orange-400" />
                          <span className="text-[10px] font-mono uppercase tracking-widest text-orange-400 font-semibold">
                            Council Stream Logs
                          </span>
                        </div>
                        
                        <div
                          ref={logContainerRef}
                          className="flex-1 font-mono text-[9px] text-zinc-400 overflow-y-auto space-y-1.5 py-3 pr-1 leading-relaxed select-none"
                        >
                          {logs.map((log, i) => (
                            <div key={i} className="animate-fade-up">
                              {log}
                            </div>
                          ))}
                        </div>
                        
                        <div className="h-6 flex items-center gap-2 text-[10px] text-zinc-500 font-mono italic animate-pulse border-t border-white/[0.04] pt-2">
                          <Activity size={10} />
                          <span>Executive CMO compiling positioning analysis...</span>
                        </div>
                      </motion.div>
                    )}

                    {/* Palette Render State */}
                    {simStep === "palette" && (
                      <motion.div
                        key="palette-pane"
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="h-full flex flex-col justify-between"
                      >
                        <div className="space-y-1.5">
                          <div className="flex items-center gap-2 text-micro font-bold text-white">
                            <Palette size={13} className="text-pink-400" />
                            <span>Generated HSL Brand Color tokens</span>
                          </div>
                          <p className="text-[11px] text-[var(--color-slate)]">
                            Creative Director chose these brand tokens matching your brief&apos;s semantic tone:
                          </p>
                        </div>

                        <div className="grid grid-cols-2 gap-2 my-4">
                          {selectedBrief.palette.map((color, i) => (
                            <motion.div
                              key={color.hex}
                              initial={{ opacity: 0, scale: 0.95 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: i * 0.1 }}
                              className="p-2.5 rounded-xl border border-white/5 bg-zinc-900/50 flex items-center gap-3"
                            >
                              <div
                                className="w-7 h-7 rounded-lg border border-white/10 shrink-0"
                                style={{ backgroundColor: color.hex }}
                              />
                              <div className="overflow-hidden">
                                <div className="text-[10px] font-bold text-white truncate">
                                  {color.name}
                                </div>
                                <div className="text-[9px] font-mono text-zinc-500 uppercase">
                                  {color.hex}
                                </div>
                              </div>
                            </motion.div>
                          ))}
                        </div>

                        <div className="border-t border-white/[0.04] pt-2">
                          <div className="text-[10px] font-mono text-[var(--color-slate)]">
                            FONT PAIRING: <span className="text-white font-bold">{selectedBrief.logoStyle === "serif-elegant" ? "Fraunces Elegance" : "DM Sans Custom"}</span>
                          </div>
                        </div>
                      </motion.div>
                    )}

                    {/* SVG Typography Logo Design State */}
                    {simStep === "logo" && (
                      <motion.div
                        key="logo-pane"
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="h-full flex flex-col justify-between"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 text-micro font-bold text-white">
                            <ImageIcon size={13} className="text-purple-400" />
                            <span>Creative Studio — Custom Vector Asset</span>
                          </div>
                          <p className="text-[11px] text-[var(--color-slate)]">
                            Typographic dynamic vector mark generated autonomously:
                          </p>
                        </div>

                        <div
                          className="flex-1 my-4 border border-dashed border-white/10 rounded-xl bg-zinc-950/60 flex items-center justify-center p-6 relative overflow-hidden"
                          style={{ backgroundColor: selectedBrief.palette[0].hex + "10" }}
                        >
                          {/* Central Dynamic Brand Logo render */}
                          <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            className="text-center space-y-2 z-10"
                          >
                            <h3
                              className={`text-3xl tracking-tight leading-none ${
                                selectedBrief.logoStyle === "serif-elegant"
                                  ? "font-display font-light italic"
                                  : selectedBrief.logoStyle === "retro-script"
                                  ? "font-serif italic font-bold tracking-wide"
                                  : "font-sans font-black uppercase tracking-tighter"
                              }`}
                              style={{ color: selectedBrief.palette[1].hex }}
                            >
                              {selectedBrief.name}
                            </h3>
                            <div
                              className="text-[9px] uppercase tracking-[0.2em] font-mono"
                              style={{ color: selectedBrief.palette[2].hex }}
                            >
                              {selectedBrief.tagline}
                            </div>
                          </motion.div>

                          {/* Dynamic visual grid */}
                          <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: "radial-gradient(white 1px, transparent 1px)", backgroundSize: "16px 16px" }} />
                        </div>

                        <div className="text-[9px] font-mono text-[var(--color-stone)]">
                          Format: SVG vector scale-independent coordinates
                        </div>
                      </motion.div>
                    )}

                    {/* Packaging Mockup State */}
                    {simStep === "packaging" && (
                      <motion.div
                        key="packaging-pane"
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="h-full flex flex-col justify-between"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 text-micro font-bold text-white">
                            <Package size={13} className="text-teal-400" />
                            <span>Packaging Workspace Blueprint</span>
                          </div>
                          <p className="text-[11px] text-[var(--color-slate)]">
                            Die outline blueprint for <span className="text-white font-bold">{selectedBrief.packagingType}</span>:
                          </p>
                        </div>

                        <div className="flex-1 my-3 flex items-center justify-center gap-6">
                          {/* Simplified dynamic box drawing using Tailwind */}
                          <div className="relative w-28 h-28 border border-teal-500/20 bg-zinc-950/40 rounded-lg p-2.5 flex flex-col justify-between overflow-hidden shadow-inner">
                            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-teal-500 to-transparent opacity-40" />
                            
                            {/* Visual Packaging Content */}
                            <div className="w-full flex justify-between items-center text-[8px] font-mono text-zinc-500">
                              <span>SKU-1029</span>
                              <span>DIE LINE</span>
                            </div>

                            <div className="text-center space-y-1">
                              <span
                                className="block text-[11px] font-bold truncate tracking-tight"
                                style={{ color: selectedBrief.palette[1].hex }}
                              >
                                {selectedBrief.name}
                              </span>
                              <span className="block text-[6px] tracking-widest uppercase font-mono text-zinc-400">
                                {selectedBrief.category}
                              </span>
                            </div>

                            <div
                              className="w-full h-3.5 rounded flex items-center justify-center text-[7px] font-mono font-bold"
                              style={{
                                backgroundColor: selectedBrief.palette[1].hex,
                                color: selectedBrief.palette[0].hex,
                              }}
                            >
                              SEAL TAPE
                            </div>
                          </div>

                          {/* Features list */}
                          <div className="space-y-2">
                            <div className="flex items-center gap-1.5 text-[10px] text-zinc-300">
                              <CheckCircle2 size={11} className="text-teal-400" />
                              <span>Custom scale dimensions</span>
                            </div>
                            <div className="flex items-center gap-1.5 text-[10px] text-zinc-300">
                              <CheckCircle2 size={11} className="text-teal-400" />
                              <span>Aesthetic consistency grade: A</span>
                            </div>
                            <div className="flex items-center gap-1.5 text-[10px] text-zinc-300">
                              <CheckCircle2 size={11} className="text-teal-400" />
                              <span>Vector die-lines ready</span>
                            </div>
                          </div>
                        </div>

                        <div className="text-[9px] font-mono text-[var(--color-stone)] border-t border-white/[0.04] pt-1.5">
                          Blueprint ID: PKG-SOL-4019
                        </div>
                      </motion.div>
                    )}

                    {/* Vercel Web Deployment Mock State */}
                    {simStep === "web" && (
                      <motion.div
                        key="web-pane"
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="h-full flex flex-col justify-between"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 text-micro font-bold text-white">
                            <Layout size={13} className="text-blue-400" />
                            <span>Vercel Edge Next.js Live Viewport</span>
                          </div>
                        </div>

                        {/* Interactive mini Web Browser screen mockup */}
                        <div className="flex-1 my-3 border border-white/10 rounded-lg bg-zinc-950 overflow-hidden flex flex-col shadow-inner">
                          {/* Browser search address bar */}
                          <div className="h-6 bg-zinc-900 px-3 flex items-center justify-between text-[8px] border-b border-white/[0.04] text-zinc-500 font-mono">
                            <div className="flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-zinc-700" />
                              <span className="w-1.5 h-1.5 rounded-full bg-zinc-700" />
                            </div>
                            <span className="text-zinc-400 font-semibold select-all">https://{selectedBrief.id}-sol.vercel.app</span>
                            <span className="w-2" />
                          </div>

                          {/* Mini Website Screen content */}
                          <div className="flex-1 p-3 bg-zinc-950 flex flex-col justify-between text-left relative overflow-hidden">
                            <header className="flex justify-between items-center text-[8px] pb-1 border-b border-white/[0.02]">
                              <span className="font-bold text-white">{selectedBrief.name}</span>
                              <span className="text-zinc-500">MENU · INFO</span>
                            </header>

                            <div className="my-2 space-y-1">
                              <h5
                                className="text-[13px] leading-tight font-black tracking-tight"
                                style={{ color: selectedBrief.palette[1].hex }}
                              >
                                {selectedBrief.tagline}
                              </h5>
                              <p className="text-[7px] text-zinc-400 line-clamp-2 max-w-[35ch] leading-relaxed">
                                {selectedBrief.briefText}
                              </p>
                            </div>

                            <div className="grid grid-cols-3 gap-1 my-1.5">
                              {selectedBrief.menu.map((item) => (
                                <div key={item.name} className="p-1 rounded bg-zinc-900 border border-white/[0.02]">
                                  <div className="text-[6px] font-bold text-white truncate">{item.name}</div>
                                  <div className="text-[6px] font-mono text-zinc-500 mt-0.5">{item.price}</div>
                                </div>
                              ))}
                            </div>

                            <footer className="text-[6px] text-zinc-500 flex justify-between items-center pt-1 border-t border-white/[0.02]">
                              <span>© {selectedBrief.name} Kitchen</span>
                              <span className="text-emerald-400 flex items-center gap-0.5">
                                <span className="w-1 h-1 rounded-full bg-emerald-400 animate-ping" />
                                <span>Deployed Edge</span>
                              </span>
                            </footer>
                          </div>
                        </div>

                        <div className="flex items-center justify-between text-[9px] font-mono text-[var(--color-stone)]">
                          <span>Framework: Next.js 15 App Router</span>
                          <span>Hosting: Vercel Edge Serverless</span>
                        </div>
                      </motion.div>
                    )}

                    {/* Simulation COMPLETE State */}
                    {simStep === "complete" && (
                      <motion.div
                        key="complete-pane"
                        initial={{ opacity: 0, scale: 0.96 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0 }}
                        className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4"
                      >
                        <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center shadow-lg shadow-emerald-500/5 animate-pulse-glow">
                          <CheckCircle2 size={22} className="text-[#00c896]" />
                        </div>
                        <div>
                          <h4 className="text-[13px] font-bold text-white tracking-tight">
                            Autonomous Brand System Generation Complete!
                          </h4>
                          <p className="text-[11px] text-[var(--color-slate)] max-w-[34ch] mx-auto mt-1 leading-relaxed">
                            Every asset has been compiled, deployed to edge endpoints, and saved to Helix persistent memory.
                          </p>
                        </div>
                        
                        <div className="flex items-center gap-2.5">
                          <Link href="/sign-up">
                            <button className="px-4 h-8.5 text-[10px] font-bold uppercase tracking-wider bg-white text-zinc-950 hover:bg-zinc-200 transition-colors rounded-full flex items-center gap-1.5 shadow-md cursor-pointer">
                              <span>Initialize Free Workspace</span>
                              <ArrowRight size={10} />
                            </button>
                          </Link>
                          <button
                            onClick={resetSimulator}
                            className="px-4 h-8.5 text-[10px] font-bold uppercase tracking-wider bg-white/[0.04] border border-white/5 hover:bg-white/[0.08] text-white transition-colors rounded-full flex items-center gap-1.5 cursor-pointer"
                          >
                            <RotateCcw size={10} />
                            <span>Try another</span>
                          </button>
                        </div>
                      </motion.div>
                    )}

                  </AnimatePresence>
                </main>

              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* ===== Live Stats Region ===== */}
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-8 border-t border-white/[0.04] z-10">
        <Reveal>
          <div className="text-center mb-6">
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-signature)]">
              Helix Node Network Status
            </p>
          </div>
        </Reveal>
        <LiveStats />
      </section>

      {/* ===== Executive Agent Council Panel ===== */}
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-16 md:py-24 border-t border-white/[0.04] z-10">
        <Reveal>
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-14">
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-signature)]">
              Executive Agent Council
            </p>
            <h2 className="font-display text-3xl sm:text-5xl font-light tracking-[-0.015em] text-white text-balance">
              Five specialized minds, one operational core.
            </h2>
            <p className="text-[14px] text-[var(--color-slate)] leading-relaxed">
              Helix operates through a closed-loop multi-agent critique council. Agents communicate dynamically via the Agent Client Protocol to refine your assets autonomously.
            </p>
          </div>
        </Reveal>

        <RevealStagger className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {AGENTS.map((agent) => {
            return (
              <RevealItem key={agent.name}>
                <motion.div
                  whileHover={{ y: -3 }}
                  className="relative p-5 rounded-2xl border border-white/[0.05] bg-[#0d0e12]/60 overflow-hidden h-full flex flex-col justify-between shadow-lg"
                >
                  {/* Subtle corner light flare */}
                  <div
                    className="absolute -right-8 -top-8 w-20 h-20 rounded-full blur-xl opacity-[0.04] pointer-events-none"
                    style={{ backgroundColor: agent.color }}
                  />

                  <div>
                    <div className="flex items-center justify-between mb-3.5">
                      <span
                        className="text-[9px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-black/20 border border-white/5 font-semibold inline-flex items-center gap-1.5"
                        style={{ color: agent.color }}
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse-glow" />
                        {agent.status}
                      </span>
                    </div>

                    <h4 className="text-[14px] font-bold text-white">
                      {agent.name}
                    </h4>
                    <p className="text-[10px] text-[var(--color-stone)] mt-0.5 font-medium leading-tight">
                      {agent.role}
                    </p>

                    <p className="text-[12px] leading-relaxed text-[var(--color-slate)] mt-4 line-clamp-3 select-none">
                      &quot;{agent.actionText}&quot;
                    </p>
                  </div>

                  <div className="mt-5 pt-3.5 border-t border-white/[0.03] flex items-center justify-between">
                    <span className="text-[8px] font-mono text-[var(--color-stone)] uppercase">
                      READY STATE
                    </span>
                    <CheckCircle2 size={11} className="text-[#00c896]" />
                  </div>
                </motion.div>
              </RevealItem>
            );
          })}
        </RevealStagger>
      </section>

      {/* ===== Capabilities Matrix Overhaul ===== */}
      <section
        id="capabilities"
        className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-16 md:py-24 border-t border-white/[0.04] z-10"
      >
        <Reveal>
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-12">
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-signature)]">
              System Capabilities
            </p>
            <h2 className="font-display text-3xl sm:text-5xl font-light tracking-[-0.015em] text-white text-balance">
              Six workflows, one connected brain.
            </h2>
            <p className="text-[14px] text-[var(--color-slate)] leading-relaxed">
              Each capability runs as a modular, inspectable workflow. Outputs flow directly into a shared workspace asset library and write context back to your persistent memory graph.
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
                  className="group block p-6 rounded-2xl border border-white/[0.04] bg-[#0d0e12]/40 backdrop-blur-md transition-all duration-300 hover:scale-[1.01] hover:-translate-y-0.5"
                  style={{
                    boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
                  }}
                >
                  {/* Glowing background on hover */}
                  <div
                    className="size-10 rounded-xl flex items-center justify-center mb-4.5 transition-transform group-hover:scale-105"
                    style={{
                      background: `${c.accent}10`,
                      border: `1px solid ${c.accent}24`,
                      color: c.accent,
                    }}
                  >
                    <Icon size={18} />
                  </div>
                  
                  <h3 className="text-[15px] font-bold text-white mb-1.5 group-hover:text-purple-400 transition-colors">
                    {c.title}
                  </h3>
                  
                  <p className="text-[13px] leading-relaxed text-[var(--color-slate)] min-h-[54px] line-clamp-3">
                    {c.blurb}
                  </p>
                  
                  <p className="text-[11px] leading-relaxed text-[var(--color-stone)] mt-2 italic line-clamp-2">
                    {c.detailText}
                  </p>
                  
                  <div className="mt-4 pt-3 border-t border-white/[0.03] flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-purple-400 group-hover:text-white transition-colors">
                    <span>Initialize Workspace</span>
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
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-16 md:py-24 border-t border-white/[0.04] z-10">
        <Reveal>
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-14">
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-signature)]">
              Core Pillars
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
                <div className="relative p-6 rounded-2xl border border-white/[0.04] bg-[#0d0e12]/60 overflow-hidden h-full flex flex-col justify-between shadow-lg">
                  <div
                    className="absolute -right-8 -top-8 w-24 h-24 rounded-full blur-2xl opacity-20 pointer-events-none"
                    style={{ background: p.color }}
                  />
                  <div>
                    <div
                      className="size-9 rounded-xl flex items-center justify-center mb-4"
                      style={{
                        background: `${p.color}14`,
                        border: `1px solid ${p.color}24`,
                        color: p.color,
                      }}
                    >
                      <Icon size={16} />
                    </div>
                    <h3 className="text-[16px] font-bold text-white mb-2">
                      {p.title}
                    </h3>
                    <p className="text-[13px] leading-relaxed text-[var(--color-slate)]">
                      {p.blurb}
                    </p>
                  </div>
                </div>
              </RevealItem>
            );
          })}
        </RevealStagger>
      </section>

      {/* ===== Steps ===== */}
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-16 md:py-24 border-t border-white/[0.04] z-10">
        <Reveal>
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-14">
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-signature)]">
              Operational Flow
            </p>
            <h2 className="font-display text-3xl sm:text-5xl font-light tracking-[-0.015em] text-white text-balance">
              From brief to launch in three moves.
            </h2>
          </div>
        </Reveal>

        <RevealStagger className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {STEPS.map((s) => (
            <RevealItem key={s.n}>
              <div className="p-6 rounded-2xl border border-white/[0.04] bg-[#0d0e12]/40 backdrop-blur-md space-y-3 h-full shadow-lg">
                <div className="text-[10px] font-mono font-bold text-purple-400 tracking-widest">
                  STEP {s.n}
                </div>
                <h3 className="text-[17px] font-bold text-white">
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
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-16 md:py-24 border-t border-white/[0.04] z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <Reveal className="lg:col-span-5">
            <div className="space-y-5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-signature)]">
                Inside Helix
              </p>
              <h2 className="font-display text-3xl sm:text-5xl font-light tracking-[-0.015em] text-white leading-[1.05] text-balance">
                Every surface you need, in one workspace.
              </h2>
              <p className="text-[14px] text-[var(--color-slate)] leading-relaxed">
                Helix unites brand strategy, composable workflows, visual assets, model picks, and memory graphs under one single workspace namespace — featuring high-performance sub-second transitions and uniform credentials.
              </p>
              <div className="pt-2">
                <Link href="/features">
                  <Button
                    variant="secondary"
                    size="md"
                    className="bg-white/[0.03] hover:bg-white/[0.07] text-white border-white/[0.08] cursor-pointer"
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
                    className="group block p-4.5 rounded-xl border border-white/[0.04] bg-[#0d0e12]/60 hover:border-white/10 hover:bg-[#13141a]/95 transition-all shadow-md"
                  >
                    <div className="size-9 rounded-lg flex items-center justify-center mb-3 bg-white/[0.03] border border-white/[0.04] text-white/80 group-hover:scale-105 transition-transform">
                      <Icon size={15} className="text-[#f0734a]" />
                    </div>
                    <div className="text-[13px] font-bold text-white">
                      {s.label}
                    </div>
                  </Link>
                </RevealItem>
              );
            })}
          </RevealStagger>
        </div>
      </section>

      {/* ===== Testimonials ===== */}
      <TestimonialsSection />

      {/* ===== Final CTA ===== */}
      <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-20 md:py-28 z-10">
        <Reveal>
          <div className="relative overflow-hidden rounded-3xl border border-white/[0.06] bg-gradient-to-br from-[#13141a] via-[#0d0e12] to-[#0a0b0e] p-10 md:p-16 text-center shadow-[0_24px_80px_rgba(0,0,0,0.5)]">
            <div className="absolute -inset-1 bg-[radial-gradient(circle_at_30%_0%,rgba(255,106,77,0.08),transparent_40%),radial-gradient(circle_at_70%_100%,rgba(162,75,255,0.08),transparent_45%)] pointer-events-none" />

            <div className="relative space-y-6 max-w-2xl mx-auto">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/[0.03] border border-white/[0.07] text-[10px] text-white/70 font-semibold uppercase tracking-widest">
                <Zap size={11} className="text-[#ff6a4d]" />
                <span>Free tier — no card required</span>
              </div>
              <h2 className="font-display text-3xl sm:text-5xl md:text-6xl font-light tracking-[-0.02em] text-white leading-[1.04] text-balance">
                Spin up your first brand in a few minutes.
              </h2>
              <p className="text-[14px] text-[var(--color-slate)] leading-relaxed">
                Create an account, integrate a model API key, and run your first autonomous workflow today. Scale and upgrade only when you need to — free forever when starting.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
                <Link href="/sign-up">
                  <Button
                    variant="glow"
                    size="lg"
                    className="h-12 px-6 font-bold tracking-tight rounded-xl flex items-center gap-2 group cursor-pointer"
                  >
                    <span>Create your workspace</span>
                    <ArrowRight
                      size={15}
                      className="transition-transform group-hover:translate-x-0.5"
                    />
                  </Button>
                </Link>
                <Link href="/contact">
                  <Button
                    variant="secondary"
                    size="lg"
                    className="h-12 px-6 font-bold tracking-tight rounded-xl bg-white/[0.03] hover:bg-white/[0.07] text-white cursor-pointer"
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
