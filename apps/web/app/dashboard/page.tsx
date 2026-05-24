"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import useSWR from "swr";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  BadgeCheck,
  BarChart3,
  Boxes,
  BrainCircuit,
  Cpu,
  DollarSign,
  Eye,
  LineChart,
  Megaphone,
  Network,
  Package,
  Play,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  WandSparkles,
  Terminal as TerminalIcon,
  Zap,
  CheckCircle2,
  Users,
  Compass,
  Database,
  Layers,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { api, type OperatingSystemOverview } from "@/lib/api";
import { useLiveRoom } from "@/lib/live";

const FALLBACK_OVERVIEW: OperatingSystemOverview = {
  metrics: [
    { label: "Revenue Control", value: "Live", delta: "Goal-aware", tone: "success" },
    { label: "Active Agents", value: "15", delta: "Persistent workforce", tone: "info" },
    { label: "Autonomous Triggers", value: "8", delta: "Event-driven", tone: "warning" },
    { label: "Memory Signals", value: "Ready", delta: "Learning graph", tone: "success" },
    { label: "Generated Assets", value: "0", delta: "Creative library", tone: "info" },
    { label: "Workflow Runs", value: "0", delta: "0 active · 0 won · 0 failed", tone: "neutral" },
  ],
  systems: [
    {
      name: "AI CMO Brain",
      status: "ready",
      description: "Coordinates goals, budgets, priorities, and executive decisions.",
    },
    {
      name: "Executive Agent Council",
      status: "ready",
      description: "Debates strategy, assigns work, votes on plans, and escalates risk.",
    },
    {
      name: "Workflow Orchestration",
      status: "ready",
      description: "Runs durable, resumable execution plans with checkpoints and retries.",
    },
    {
      name: "Browser Automation",
      status: "ready",
      description: "Operates connected tools, captures evidence, and preserves execution replay.",
    },
    {
      name: "Creative Intelligence",
      status: "ready",
      description: "Scores visual quality, detects fatigue, and remembers winning styles.",
    },
    {
      name: "Performance Memory Graph",
      status: "ready",
      description: "Persists campaign, creative, customer, offer, and experiment learnings.",
    },
  ],
  council: [
    { name: "Chief Marketing Officer", mandate: "Revenue strategy, allocation, and executive decisions", status: "ready" },
    { name: "Creative Director", mandate: "Visual direction, brand consistency, and creative quality", status: "ready" },
    { name: "Brand Strategist", mandate: "Positioning, audience clarity, and market narrative", status: "ready" },
    { name: "Performance Marketer", mandate: "ROAS, CAC, bidding, and channel optimization", status: "ready" },
    { name: "Lifecycle Marketer", mandate: "Email, SMS, cohorts, and retention moments", status: "ready" },
    { name: "CRO Specialist", mandate: "Landing pages, checkout, and conversion experiments", status: "ready" },
  ],
  intelligence_layers: [
    { name: "Campaign Intelligence", description: "Campaign health, channel signals, and budget movement", status: "ready" },
    { name: "Creative Intelligence", description: "Taste scoring, fatigue detection, and visual memory", status: "ready" },
    { name: "Revenue Intelligence", description: "ROAS, CAC, LTV, margin, and offer performance", status: "ready" },
    { name: "Customer Intelligence", description: "Segments, retention, surveys, reviews, and purchase behavior", status: "ready" },
    { name: "Competitor Intelligence", description: "Competitor campaigns, pricing, messaging, and trend shifts", status: "ready" },
    { name: "Experimentation", description: "A/B tests, winner selection, confidence, and rollout control", status: "ready" },
  ],
  action_feed: [],
  event_triggers: [],
  automation_coverage: {
    brands: 0,
    skills: 0,
    scheduled_jobs: 0,
    triggers: 0,
    workflows: 0,
    assets: 0,
    memory_entries: 0,
  },
};

const SYSTEM_ICONS = [BrainCircuit, Users, Activity, Play, WandSparkles, Database];
const METRIC_ICONS = [DollarSign, Cpu, Target, Layers, Boxes, Activity];
const WORKSPACE_LINKS = [
  { href: "/campaigns", label: "Campaign Manager", icon: Megaphone, gradient: "bg-brand-coral" },
  { href: "/studio", label: "Creative Studio", icon: WandSparkles, gradient: "bg-brand-magenta" },
  { href: "/websites", label: "Website Builder", icon: Boxes, gradient: "bg-brand-blue" },
  { href: "/packaging", label: "Packaging Workspace", icon: Package, gradient: "bg-brand-purple" },
  { href: "/lab", label: "Experimentation Lab", icon: BarChart3, gradient: "bg-brand-amber" },
  { href: "/integrations", label: "Integrations Center", icon: ShieldCheck, gradient: "bg-brand-teal" },
];

// Color mapping for council agents in interactive map
const AGENT_COLORS = [
  { text: "text-amber-400", border: "border-amber-400/30", bg: "bg-amber-400/10", glow: "rgba(251, 191, 36, 0.4)" },
  { text: "text-rose-400", border: "border-rose-400/30", bg: "bg-rose-400/10", glow: "rgba(251, 113, 133, 0.4)" },
  { text: "text-purple-400", border: "border-purple-400/30", bg: "bg-purple-400/10", glow: "rgba(192, 132, 252, 0.4)" },
  { text: "text-blue-400", border: "border-blue-400/30", bg: "bg-blue-400/10", glow: "rgba(96, 165, 250, 0.4)" },
  { text: "text-emerald-400", border: "border-emerald-400/30", bg: "bg-emerald-400/10", glow: "rgba(52, 211, 153, 0.4)" },
  { text: "text-teal-400", border: "border-teal-400/30", bg: "bg-teal-400/10", glow: "rgba(45, 212, 191, 0.4)" },
];

function toneClass(tone: string) {
  switch (tone) {
    case "success":
      return "text-emerald-400";
    case "warning":
      return "text-amber-400";
    case "error":
      return "text-rose-400";
    case "info":
      return "text-sky-400";
    default:
      return "text-[color:var(--color-charcoal)]";
  }
}

function toneBorderClass(tone: string) {
  switch (tone) {
    case "success":
      return "border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.05)]";
    case "warning":
      return "border-amber-500/20 shadow-[0_0_15px_rgba(245,158,11,0.05)]";
    case "error":
      return "border-rose-500/20 shadow-[0_0_15px_rgba(239,68,68,0.05)]";
    case "info":
      return "border-sky-500/20 shadow-[0_0_15px_rgba(14,165,233,0.05)]";
    default:
      return "border-white/[0.06]";
  }
}

function statusTone(status: string): "neutral" | "success" | "warning" | "error" | "info" {
  if (["active", "learning", "completed", "succeeded"].includes(status)) return "success";
  if (["running", "queued", "pending", "ready"].includes(status)) return "info";
  if (["paused", "warning"].includes(status)) return "warning";
  if (["failed", "error"].includes(status)) return "error";
  return "neutral";
}

export default function DashboardPage() {
  const [bootstrapState, setBootstrapState] = useState<{
    loading: boolean;
    message?: string;
    error?: string;
  }>({ loading: false });

  const [activeCouncilAgent, setActiveCouncilAgent] = useState<number | null>(null);
  const [terminalLogs, setTerminalLogs] = useState<Array<{ time: string; msg: string; type: "info" | "action" | "success" }>>([]);

  const { data, error, isLoading, mutate } = useSWR<OperatingSystemOverview>(
    "operating-system-overview",
    () => api.operatingSystem.overview(),
    { refreshInterval: 10_000, revalidateOnFocus: true },
  );

  const { data: signalsData } = useSWR(
    "intelligence-signals",
    () => api.signals.list({ limit: 5 }),
    { refreshInterval: 15000 }
  );

  const ws = useLiveRoom("dashboard");
  const lastEvent = ws.lastEvent as any;
  const overview = data ?? FALLBACK_OVERVIEW;
  const hasWorkforce = Number(overview.automation_coverage?.triggers ?? 0) > 0;

  // Simulate dynamic intelligence streaming logs inside our premium terminal
  useEffect(() => {
    const defaultMissions: Array<{ msg: string; type: "info" | "action" | "success" }> = [
      { msg: "Executive CMO Brain aligned top campaigns with growth targets.", type: "success" },
      { msg: "CRO Specialist starting conversion optimization on main landing page.", type: "action" },
      { msg: "Creative Director detected high aesthetic score on winter catalogs.", type: "info" },
      { msg: "Performance Marketer adjusted bidding rules based on ROAS shifts.", type: "action" },
      { msg: "Autonomy triggers scanning live event streams.", type: "info" },
      { msg: "Lifecycle Marketer enqueued dynamic cart-abandonment flows.", type: "success" },
    ];

    const formatTime = () => {
      const now = new Date();
      return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    };

    // Load initial logs
    setTerminalLogs(
      defaultMissions.map((mission) => ({
        time: formatTime(),
        ...mission,
      }))
    );

    const interval = setInterval(() => {
      const logTemplates: Array<{ msg: string; type: "info" | "action" | "success" }> = [
        { msg: "CMO Council synchronized persistent context variables.", type: "info" },
        { msg: "Performance Marketer evaluating channel CAC shift.", type: "action" },
        { msg: "Browser Automation scanned inventory listings for competitor pricing updates.", type: "action" },
        { msg: "Creative Director committed dynamic assets to storage catalog.", type: "success" },
        { msg: "Signals engine triggered learning vector generation in graph database.", type: "info" },
        { msg: "CRO Specialist validated A/B experiment hypothesis with 98% confidence.", type: "success" },
        { msg: "Automated workflow enqueued with persistent memory context.", type: "info" },
      ];

      const chosen = logTemplates[Math.floor(Math.random() * logTemplates.length)];
      setTerminalLogs((prev) => [
        { time: formatTime(), ...chosen },
        ...prev.slice(0, 15),
      ]);
    }, 6000);

    return () => clearInterval(interval);
  }, []);

  async function bootstrapWorkspace() {
    setBootstrapState({ loading: true });
    try {
      const result = await api.operatingSystem.bootstrap();
      await mutate();
      setBootstrapState({
        loading: false,
        message: `Initialized ${result.created.agents} agents, ${result.created.triggers} triggers, and ${result.created.schedules} schedules.`,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to initialize autonomy.";
      setBootstrapState({ loading: false, error: message });
    }
  }

  return (
    <div className="space-y-8 animate-fade-up max-w-[1280px] mx-auto px-4 md:px-6 py-6 pb-20 relative">
      {/* Premium Decorative Ambient Glow background */}
      <div className="absolute top-[-20%] left-[20%] w-[500px] h-[500px] bg-gradient-to-tr from-brand-coral/10 to-brand-magenta/5 rounded-full blur-[120px] pointer-events-none -z-10 animate-pulse-glow" />
      <div className="absolute bottom-[10%] right-[10%] w-[400px] h-[400px] bg-gradient-to-br from-brand-blue/5 to-brand-purple/10 rounded-full blur-[100px] pointer-events-none -z-10" />

      {/* Header section with rich dark aesthetics */}
      <header className="grid gap-6 lg:grid-cols-[1fr_auto] lg:items-end border-b border-white/[0.04] pb-8">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="text-eyebrow text-slate font-bold tracking-[0.15em] flex items-center gap-2">
              <Compass className="size-3 text-signature" />
              AI Commerce Operating System
            </div>
            <span
              className="inline-flex items-center gap-1.5 rounded-full px-3 py-0.5 text-[10px] font-bold uppercase tracking-wider glass"
              style={{
                background: ws.status === "open" ? "rgba(0,212,170,0.08)" : "rgba(255,84,112,0.08)",
                color: ws.status === "open" ? "rgb(0,212,170)" : "rgb(255,84,112)",
                borderColor: ws.status === "open" ? "rgba(0,212,170,0.2)" : "rgba(255,84,112,0.2)",
              }}
            >
              <span
                className="inline-block w-1.5 h-1.5 rounded-full"
                style={{
                  background: ws.status === "open" ? "rgb(0,212,170)" : "rgb(255,84,112)",
                  boxShadow: ws.status === "open" ? "0 0 10px rgb(0,212,170)" : "none",
                  animation: ws.status === "open" ? "pulse-glow 2s ease-in-out infinite" : "none",
                }}
              />
              {ws.status === "open" ? "Live Gateway Active" : ws.status}
            </span>
          </div>
          <h1 className="mt-3 text-display-lg font-bold leading-[1.1] text-white tracking-tight">
            Command growth, creative, and execution from one <span className="text-gradient-signature">Helix Workspace</span>.
          </h1>
          <p className="mt-4 max-w-[76ch] text-body-md text-slate leading-relaxed">
            Helix coordinates a persistent executive council of specialized agents, orchestrates event-driven workflows,
            automates browser actions, and maps every operational decision into a high-fidelity learning graph.
          </p>
          {lastEvent && (
            <div className="mt-3 flex items-center gap-2 text-micro text-stone tabular border border-white/[0.04] bg-white/[0.01] w-fit px-3 py-1 rounded-md">
              <Activity className="size-3 text-signature animate-pulse" />
              <span className="font-semibold text-slate">Latest System Signal:</span>
              <span className="text-white font-medium">{lastEvent.type}</span>
              {lastEvent.data?.title && (
                <span className="text-stone-400">({lastEvent.data.title})</span>
              )}
            </div>
          )}
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={bootstrapWorkspace}
            disabled={bootstrapState.loading}
            className="inline-flex h-11 items-center justify-center gap-2.5 rounded-full bg-white px-6 text-xs font-bold text-black transition-all hover:bg-white/95 active:scale-95 disabled:cursor-not-allowed disabled:opacity-60 shadow-[0_4px_16px_rgba(255,255,255,0.1)]"
          >
            {bootstrapState.loading ? (
              <Activity className="size-4 animate-spin" />
            ) : (
              <TrendingUp className="size-4 text-signature" />
            )}
            {hasWorkforce ? "Refresh Council Workers" : "Initialize Executive Workforce"}
          </button>
          <Link
            href="/brands/new"
            className="inline-flex h-11 items-center justify-center gap-2.5 rounded-full border border-white/10 bg-white/[0.03] px-6 text-xs font-bold text-white transition-all hover:bg-white/[0.07] hover:border-white/20 active:scale-95"
          >
            <Sparkles className="size-4 text-brand-coral" />
            Initialize Brand
          </Link>
          <Link
            href="/lab"
            className="inline-flex h-11 items-center justify-center gap-2.5 rounded-full border border-white/10 bg-white/[0.03] px-6 text-xs font-bold text-white transition-all hover:bg-white/[0.07] hover:border-white/20 active:scale-95"
          >
            <LineChart className="size-4 text-brand-blue" />
            Open Lab
          </Link>
        </div>
      </header>

      {error && (
        <Card className="rounded-xl border-amber-500/20 bg-amber-500/5 p-4 flex items-start gap-3">
          <AlertTriangle className="size-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-bold text-amber-200">Readiness Mode Active</h4>
            <p className="text-xs text-amber-300/80 mt-1">
              Live operating data is loading, displaying local fallback Council profiles for sandbox evaluation.
            </p>
          </div>
        </Card>
      )}

      {(bootstrapState.message || bootstrapState.error) && (
        <Card
          className={`rounded-xl p-4 border flex items-center gap-3 ${
            bootstrapState.error
              ? "border-rose-500/20 bg-rose-500/5"
              : "border-emerald-500/20 bg-emerald-500/5"
          }`}
        >
          <CheckCircle2 className={`size-5 shrink-0 ${bootstrapState.error ? "text-rose-400" : "text-emerald-400"}`} />
          <p
            className={`text-xs font-semibold ${
              bootstrapState.error ? "text-rose-200" : "text-emerald-200"
            }`}
          >
            {bootstrapState.error ?? bootstrapState.message}
          </p>
        </Card>
      )}

      {/* Grid of Key Metrics with beautiful glassmorphism and tone indicators */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-6">
        {overview.metrics.map((metric, index) => {
          const Icon = METRIC_ICONS[index % METRIC_ICONS.length];
          return (
            <Card
              key={metric.label}
              className={`rounded-xl border bg-[#13141a]/40 p-5 shadow-xl glass transition-all duration-300 hover:-translate-y-1 hover:bg-[#1a1c24]/50 ${toneBorderClass(
                metric.tone
              )}`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate">
                  {metric.label}
                </span>
                <span className={`inline-flex p-1.5 rounded-lg bg-white/[0.02] border border-white/[0.04]`}>
                  <Icon className={`size-3.5 ${toneClass(metric.tone)}`} />
                </span>
              </div>
              <div className="mt-4 text-3xl font-bold leading-none text-white tracking-tight tabular">
                {isLoading ? (
                  <span className="inline-block h-6 w-12 bg-white/5 rounded animate-pulse" />
                ) : (
                  metric.value
                )}
              </div>
              <div className={`mt-2.5 text-[10px] font-bold tracking-wide flex items-center gap-1.5 ${toneClass(metric.tone)}`}>
                <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />
                {metric.delta}
              </div>
            </Card>
          );
        })}
      </section>

      {/* Interactive Boardroom & Autonomy Map Central Area */}
      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        
        {/* Interactive Boardroom Orbit Visual Panel */}
        <Card className="rounded-xl border border-white/[0.06] bg-[#13141a]/45 p-6 shadow-2xl glass relative overflow-hidden flex flex-col justify-between min-h-[480px]">
          <div className="absolute top-0 right-0 w-[200px] h-[200px] bg-brand-coral/5 rounded-full blur-[60px] pointer-events-none" />
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4 z-10">
            <div>
              <div className="text-eyebrow text-slate">Operational Blueprint</div>
              <h2 className="mt-1 text-heading-lg text-white font-bold tracking-tight">Executive Council Workspace</h2>
            </div>
            <div className="flex items-center gap-2 glass px-3 py-1.5 rounded-full border border-white/[0.06] text-xs text-slate">
              <Users className="size-3.5 text-brand-coral" />
              <span>Hover nodes to analyze specialist logic</span>
            </div>
          </div>

          {/* Interactive Agent Orbit Workspace Map */}
          <div className="relative w-full h-[320px] flex items-center justify-center border border-white/[0.03] bg-black/10 rounded-2xl p-4 overflow-hidden">
            
            {/* Background target grids */}
            <div className="absolute inset-0 border border-dashed border-white/[0.02] rounded-full scale-75 animate-pulse-glow" style={{ animationDuration: "6s" }} />
            <div className="absolute inset-0 border border-dashed border-white/[0.01] rounded-full scale-50" />
            
            {/* SVG Connecting Light Channels */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              <defs>
                <linearGradient id="coralGlow" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#ff6a4d" stopOpacity="0.2" />
                  <stop offset="100%" stopColor="#ff3d7f" stopOpacity="0.1" />
                </linearGradient>
              </defs>
              {overview.council.map((_, index) => {
                const angle = (index * 2 * Math.PI) / overview.council.length;
                const r = 110;
                const x2 = 50 + Math.cos(angle) * 35; // Target percentages for coordinates
                const y2 = 50 + Math.sin(angle) * 35;
                return (
                  <g key={index}>
                    <line
                      x1="50%"
                      y1="50%"
                      x2={`${x2}%`}
                      y2={`${y2}%`}
                      stroke="url(#coralGlow)"
                      strokeWidth="1.5"
                    />
                    {activeCouncilAgent === index && (
                      <line
                        x1="50%"
                        y1="50%"
                        x2={`${x2}%`}
                        y2={`${y2}%`}
                        stroke="#f0734a"
                        strokeWidth="2.5"
                        strokeDasharray="8 8"
                        style={{ animation: "line-flow 1.5s linear infinite" }}
                      />
                    )}
                  </g>
                );
              })}
            </svg>

            {/* Central Master Brain Node */}
            <div 
              className="absolute z-10 w-20 h-20 rounded-full flex flex-col items-center justify-center bg-black/80 border border-signature/30 shadow-[0_0_35px_rgba(240,115,74,0.25)] text-center cursor-pointer"
              onMouseEnter={() => setActiveCouncilAgent(null)}
            >
              <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-brand-coral/20 to-brand-magenta/10 animate-pulse" />
              <BrainCircuit className="size-7 text-signature animate-pulse" />
              <span className="text-[9px] uppercase tracking-wider font-bold text-white mt-1">CMO CORE</span>
            </div>

            {/* Specialist Nodes orbiting the Core */}
            {overview.council.map((agent, index) => {
              const angle = (index * 2 * Math.PI) / overview.council.length;
              // Circular coordinates
              const r = 115; // Radius of orbit
              const style = {
                transform: `translate(${Math.cos(angle) * r}px, ${Math.sin(angle) * r}px)`,
              };
              const colorInfo = AGENT_COLORS[index % AGENT_COLORS.length];
              const isHovered = activeCouncilAgent === index;

              return (
                <div
                  key={agent.name}
                  style={style}
                  className="absolute z-20"
                  onMouseEnter={() => setActiveCouncilAgent(index)}
                >
                  <motion.div
                    whileHover={{ scale: 1.15 }}
                    className={`w-11 h-11 rounded-full flex items-center justify-center cursor-pointer transition-all duration-300 border bg-black/80 ${
                      isHovered ? `${colorInfo.border} ${colorInfo.text}` : "border-white/10 text-slate"
                    }`}
                    style={{
                      boxShadow: isHovered ? `0 0 18px ${colorInfo.glow}` : "none",
                    }}
                  >
                    <Cpu className="size-4" />
                  </motion.div>
                </div>
              );
            })}
          </div>

          {/* Floating Context Details Plate */}
          <div className="z-10 mt-4 border border-white/[0.04] bg-white/[0.01] rounded-xl p-4 relative min-h-[90px] flex items-center">
            <AnimatePresence mode="wait">
              {activeCouncilAgent !== null ? (
                <motion.div
                  key={activeCouncilAgent}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="w-full flex items-start gap-4"
                >
                  <div className={`p-2 rounded-xl shrink-0 ${AGENT_COLORS[activeCouncilAgent].bg} ${AGENT_COLORS[activeCouncilAgent].text} border ${AGENT_COLORS[activeCouncilAgent].border}`}>
                    <Cpu className="size-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white">
                      {overview.council[activeCouncilAgent].name}
                    </h4>
                    <p className="text-xs text-slate mt-1 leading-relaxed">
                      <span className="font-semibold text-stone-400">Operational Mandate: </span>
                      {overview.council[activeCouncilAgent].mandate}
                    </p>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="cmo-core-overview"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="w-full flex items-start gap-4"
                >
                  <div className="p-2 rounded-xl shrink-0 bg-signature/10 text-signature border border-signature/20">
                    <BrainCircuit className="size-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white">Executive Strategy Engine</h4>
                    <p className="text-xs text-slate mt-1 leading-relaxed">
                      Coordinates specialized intelligence agents to drive ROI metrics. Set autonomous guidelines inside brand workspaces.
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </Card>

        {/* Live Commands Autonomy Terminal Stream */}
        <Card className="rounded-xl border border-white/[0.06] bg-black/80 p-5 shadow-2xl flex flex-col justify-between h-full min-h-[480px]">
          <div className="flex items-center justify-between border-b border-white/[0.05] pb-4 mb-4">
            <div className="flex items-center gap-2">
              <span className="size-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse" />
              <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <TerminalIcon className="size-3.5 text-signature" />
                Helix OS Autonomy Stream
              </span>
            </div>
            <div className="text-[10px] text-stone font-mono tracking-wider">
              PORT 3001 // BYOK_SECURE
            </div>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 font-mono text-xs pr-2 select-text h-[330px] scrollbar-thin">
            {terminalLogs.map((logItem, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-start gap-2 leading-relaxed"
              >
                <span className="text-stone select-none shrink-0 font-medium">{logItem.time}</span>
                <span className="text-signature select-none shrink-0">&gt;</span>
                <span className={
                  logItem.type === "success" 
                    ? "text-emerald-400 font-medium" 
                    : logItem.type === "action" 
                    ? "text-sky-400" 
                    : "text-slate"
                }>
                  {logItem.msg}
                </span>
              </motion.div>
            ))}
          </div>

          <div className="mt-4 pt-3 border-t border-white/[0.05] text-[10px] text-stone font-mono flex items-center justify-between">
            <span>Continuous streaming connection</span>
            <span className="animate-pulse">●</span>
          </div>
        </Card>
      </section>

      {/* Core Systems & Live active signals panels */}
      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        
        {/* Core system layers */}
        <Card className="rounded-xl border border-white/[0.06] bg-[#13141a]/45 p-6 shadow-2xl glass">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-eyebrow text-stone">Runtime Layer</div>
              <h2 className="mt-1 text-heading-lg text-white font-bold tracking-tight">Core Systems</h2>
            </div>
            <Badge tone="success" className="rounded-md px-2.5 py-1">Unified Helix Surface</Badge>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {overview.systems.map((system, index) => {
              const Icon = SYSTEM_ICONS[index % SYSTEM_ICONS.length];
              return (
                <motion.div
                  key={system.name}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.03 }}
                  className="rounded-xl border border-white/[0.04] bg-white/[0.01] p-5 transition-all duration-300 hover:bg-white/[0.03] hover:border-white/10 group"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <span className="inline-flex size-9 items-center justify-center rounded-xl bg-white/[0.03] border border-white/[0.06] text-slate group-hover:text-white group-hover:border-signature/20 group-hover:bg-signature/5 transition-all duration-300">
                        <Icon className="size-4.5" />
                      </span>
                      <h3 className="text-sm font-bold text-white tracking-wide">{system.name}</h3>
                    </div>
                    <Badge tone={statusTone(system.status)} className="px-2 py-0.5 text-[10px] font-semibold">{system.status}</Badge>
                  </div>
                  <p className="mt-3 text-xs leading-relaxed text-slate">
                    {system.description}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </Card>

        {/* Live Active Intelligence signals */}
        <Card className="rounded-xl border border-white/[0.06] bg-[#13141a]/45 p-6 shadow-2xl glass flex flex-col justify-between">
          <div>
            <div className="mb-6 flex items-center justify-between">
              <div>
                <div className="text-eyebrow text-stone">Live Intelligence</div>
                <h2 className="mt-1 text-heading-lg text-white font-bold tracking-tight">Active Signals</h2>
              </div>
              <Badge tone="warning" className="rounded-md font-semibold">{signalsData?.unread_count ?? 0} unread</Badge>
            </div>
            
            <div className="space-y-3">
              {signalsData?.signals && signalsData.signals.length > 0 ? (
                signalsData.signals.slice(0, 3).map((signal: any) => (
                  <motion.div
                    key={signal.id}
                    initial={{ opacity: 0, scale: 0.97 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className={`rounded-xl border p-4 transition-all duration-300 ${
                      signal.severity === "critical"
                        ? "border-rose-500/25 bg-rose-500/5 hover:bg-rose-500/10"
                        : signal.severity === "warning"
                        ? "border-amber-500/25 bg-amber-500/5 hover:bg-amber-500/10"
                        : "border-emerald-500/25 bg-emerald-500/5 hover:bg-emerald-500/10"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-bold text-white">{signal.title}</span>
                      <Badge
                        tone={
                          signal.severity === "critical"
                            ? "error"
                            : signal.severity === "warning"
                            ? "warning"
                            : "success"
                        }
                        className="text-[9px] px-2 py-0.5 rounded-sm"
                      >
                        {signal.layer}
                      </Badge>
                    </div>
                    <p className="mt-2 text-xs leading-relaxed text-slate">
                      {signal.description}
                    </p>
                    {signal.recommended_action && (
                      <div className="mt-3 text-[10px] text-white/70 font-semibold border-t border-white/[0.04] pt-2 flex items-center gap-1.5">
                        <Zap className="size-3 text-signature shrink-0" />
                        <span>Recommendation: {signal.recommended_action}</span>
                      </div>
                    )}
                  </motion.div>
                ))
              ) : (
                <div className="rounded-xl border border-dashed border-white/[0.08] p-8 text-center bg-black/10">
                  <Activity className="mx-auto size-6 text-stone animate-pulse" />
                  <p className="mt-3.5 text-xs text-slate font-medium max-w-[28ch] mx-auto leading-relaxed">
                    Event triggers scanning the commerce stack. Signals will register here.
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-white/[0.04] text-center">
            <Link href="/workflows" className="text-xs font-bold text-slate hover:text-white transition flex items-center justify-center gap-1">
              Analyze complete signal history
              <ArrowUpRight className="size-3.5 text-signature" />
            </Link>
          </div>
        </Card>
      </section>

      {/* Operating Area Quick Links designed with signature brand gradients */}
      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[0.4fr_0.6fr]">
        
        {/* Operating Areas Grid */}
        <Card className="rounded-xl border border-white/[0.06] bg-[#13141a]/45 p-6 shadow-2xl glass">
          <div className="mb-6">
            <div className="text-eyebrow text-stone">Workspace OS</div>
            <h2 className="mt-1 text-heading-lg text-white font-bold tracking-tight">Operating Areas</h2>
          </div>
          <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 xl:grid-cols-1">
            {WORKSPACE_LINKS.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center justify-between gap-3 rounded-xl border border-white/[0.04] bg-white/[0.01] px-4 py-3 text-sm font-bold text-white transition-all duration-300 hover:bg-white/[0.04] hover:border-signature/20 hover:pl-5 group"
                >
                  <span className="flex items-center gap-3">
                    <span className={`p-1.5 rounded-lg bg-white/[0.03] border border-white/[0.04] group-hover:bg-signature/5 group-hover:text-signature transition-all duration-300`}>
                      <Icon className="size-4" />
                    </span>
                    {item.label}
                  </span>
                  <ArrowUpRight className="size-4 text-stone group-hover:text-white group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all duration-300" />
                </Link>
              );
            })}
          </div>
        </Card>

        {/* Continuous Learning and stats mapping */}
        <Card className="rounded-xl border border-white/[0.06] bg-[#13141a]/45 p-6 shadow-2xl glass flex flex-col justify-between">
          <div>
            <div className="mb-6 flex items-center justify-between gap-3">
              <div>
                <div className="text-eyebrow text-stone">Intelligence Layer</div>
                <h2 className="mt-1 text-heading-lg text-white font-bold tracking-tight">Continuous Learning Systems</h2>
              </div>
              <Eye className="size-5 text-slate" />
            </div>
            
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {overview.intelligence_layers.map((layer) => (
                <div key={layer.name} className="rounded-xl border border-white/[0.04] bg-white/[0.01] p-4 transition hover:bg-white/[0.02]">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-xs font-bold text-white tracking-wide">{layer.name}</h3>
                    <Badge tone={statusTone(layer.status)} className="text-[9px] px-2 py-0.5">{layer.status}</Badge>
                  </div>
                  <p className="mt-2 text-xs leading-relaxed text-slate">
                    {layer.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 pt-5 border-t border-white/[0.04] grid grid-cols-2 gap-3 sm:grid-cols-4">
            {Object.entries(overview.automation_coverage).slice(0, 8).map(([key, value]) => (
              <div key={key} className="rounded-xl border border-white/[0.04] bg-white/[0.01] p-3.5 shadow-sm">
                <div className="text-2xl font-bold text-white tracking-tight tabular">{value}</div>
                <div className="mt-1 text-[9px] uppercase tracking-wider text-stone font-semibold">
                  {key.replace(/_/g, " ")}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </section>
    </div>
  );
}
