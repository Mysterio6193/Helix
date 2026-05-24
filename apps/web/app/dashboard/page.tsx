"use client";

import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { motion } from "framer-motion";
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

const SYSTEM_ICONS = [BrainCircuit, BadgeCheck, Activity, Play, WandSparkles, Network];
const METRIC_ICONS = [DollarSign, Cpu, Target, Network, Boxes, Activity];
const WORKSPACE_LINKS = [
  { href: "/campaigns", label: "Campaign Manager", icon: Megaphone },
  { href: "/studio", label: "Creative Studio", icon: WandSparkles },
  { href: "/websites", label: "Website Builder", icon: Boxes },
  { href: "/packaging", label: "Packaging Workspace", icon: Package },
  { href: "/lab", label: "Experimentation Lab", icon: BarChart3 },
  { href: "/integrations", label: "Integrations Center", icon: ShieldCheck },
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
  const overview = data ?? FALLBACK_OVERVIEW;
  const hasWorkforce = Number(overview.automation_coverage?.triggers ?? 0) > 0;

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
    <div className="space-y-8 animate-fade-up">
      <header className="grid gap-5 lg:grid-cols-[1fr_auto] lg:items-end">
        <div>
          <div className="flex items-center gap-3">
            <div className="text-eyebrow text-[color:var(--color-stone)]">
              AI Commerce Operating System
            </div>
            <span
              className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wider"
              style={{
                background: ws.status === "open" ? "rgba(0,212,170,0.15)" : "rgba(255,84,112,0.15)",
                color: ws.status === "open" ? "rgb(0,212,170)" : "rgb(255,84,112)",
              }}
            >
              <span
                className="inline-block w-1.5 h-1.5 rounded-full"
                style={{
                  background: ws.status === "open" ? "rgb(0,212,170)" : "rgb(255,84,112)",
                  boxShadow: ws.status === "open" ? "0 0 6px rgb(0,212,170)" : "none",
                  animation: ws.status === "open" ? "pulse-glow 2s ease-in-out infinite" : "none",
                }}
              />
              {ws.status === "open" ? "Live" : ws.status}
            </span>
          </div>
          <h1 className="mt-2 max-w-[920px] text-display-lg font-bold leading-tight text-white">
            Command growth, creative, revenue, and execution from one Helix workspace.
          </h1>
          <p className="mt-3 max-w-[72ch] text-body-md text-[color:var(--color-slate)]">
            Helix coordinates a persistent executive team, launches workflows, monitors KPI shifts,
            operates connected tools, and records every decision into a performance memory graph.
          </p>
          {ws.lastEvent && (
            <p className="mt-1 text-micro text-[color:var(--color-stone)] tabular">
              Latest event: {ws.lastEvent.type}
              {ws.lastEvent.data?.title ? ` — ${ws.lastEvent.data.title}` : ""}
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={bootstrapWorkspace}
            disabled={bootstrapState.loading}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-white px-4 text-xs font-bold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {bootstrapState.loading ? (
              <Activity className="size-4 animate-spin" />
            ) : (
              <TrendingUp className="size-4" />
            )}
            {hasWorkforce ? "Refresh Workforce" : "Initialize Workforce"}
          </button>
          <Link
            href="/brands/new"
            className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-4 text-xs font-bold text-white transition hover:bg-white/[0.08]"
          >
            <Sparkles className="size-4" />
            Initialize Brand
          </Link>
          <Link
            href="/lab"
            className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-4 text-xs font-bold text-white transition hover:bg-white/[0.08]"
          >
            <LineChart className="size-4" />
            Open Lab
          </Link>
        </div>
      </header>

      {error && (
        <Card className="rounded-lg border-amber-500/20 bg-amber-500/5 p-4">
          <p className="text-body-sm text-amber-200">
            Live operating data is unavailable, so Helix is showing a local readiness view.
          </p>
        </Card>
      )}

      {(bootstrapState.message || bootstrapState.error) && (
        <Card
          className={`rounded-lg p-4 ${
            bootstrapState.error
              ? "border-rose-500/20 bg-rose-500/5"
              : "border-emerald-500/20 bg-emerald-500/5"
          }`}
        >
          <p
            className={`text-body-sm ${
              bootstrapState.error ? "text-rose-200" : "text-emerald-200"
            }`}
          >
            {bootstrapState.error ?? bootstrapState.message}
          </p>
        </Card>
      )}

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-6">
        {overview.metrics.map((metric, index) => {
          const Icon = METRIC_ICONS[index % METRIC_ICONS.length];
          return (
            <Card
              key={metric.label}
              className="rounded-lg border-white/[0.06] bg-[#13141a]/70 p-4 shadow-xl"
            >
              <div className="flex items-center justify-between gap-3">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[color:var(--color-stone)]">
                  {metric.label}
                </span>
                <Icon className={`size-4 ${toneClass(metric.tone)}`} />
              </div>
              <div className="mt-3 text-2xl font-bold leading-none text-white">
                {isLoading ? "..." : metric.value}
              </div>
              <div className={`mt-2 text-[10px] font-semibold ${toneClass(metric.tone)}`}>
                {metric.delta}
              </div>
            </Card>
          );
        })}
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.35fr_0.65fr]">
        <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
          <div className="mb-5 flex items-center justify-between gap-3">
            <div>
              <div className="text-eyebrow text-[color:var(--color-stone)]">Runtime Layer</div>
              <h2 className="mt-1 text-heading-lg text-white">Core Systems</h2>
            </div>
            <Badge tone="success">Unified Helix Surface</Badge>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {overview.systems.map((system, index) => {
              const Icon = SYSTEM_ICONS[index % SYSTEM_ICONS.length];
              return (
                <motion.div
                  key={system.name}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.03 }}
                  className="rounded-lg border border-white/[0.06] bg-black/20 p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex size-8 items-center justify-center rounded-lg bg-white/[0.06] text-white">
                        <Icon className="size-4" />
                      </span>
                      <h3 className="text-sm font-bold text-white">{system.name}</h3>
                    </div>
                    <Badge tone={statusTone(system.status)}>{system.status}</Badge>
                  </div>
                  <p className="mt-3 text-xs leading-relaxed text-[color:var(--color-slate)]">
                    {system.description}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </Card>

        <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <div className="text-eyebrow text-[color:var(--color-stone)]">Actions Feed</div>
              <h2 className="mt-1 text-heading-lg text-white">Recent Decisions</h2>
            </div>
            <Link href="/workflows" className="text-xs font-bold text-[color:var(--color-slate)] hover:text-white">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {overview.action_feed.length > 0 ? (
              overview.action_feed.slice(0, 6).map((action) => (
                <Link
                  key={action.id}
                  href={`/workflows/${action.id}`}
                  className="block rounded-lg border border-white/[0.05] bg-black/20 p-3 transition hover:bg-white/[0.04]"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="truncate text-xs font-bold text-white">{action.title}</span>
                    <Badge tone={statusTone(action.status)}>{action.status}</Badge>
                  </div>
                  <p className="mt-2 truncate text-[10px] text-[color:var(--color-slate)]">
                    {action.detail}
                  </p>
                </Link>
              ))
            ) : (
              <div className="rounded-lg border border-dashed border-white/[0.08] p-5 text-center">
                <Activity className="mx-auto size-5 text-[color:var(--color-stone)]" />
                <p className="mt-3 text-xs text-[color:var(--color-slate)]">
                  Launch a workflow or publish a KPI event to populate the autonomous actions feed.
                </p>
              </div>
            )}
          </div>
        </Card>
      </section>

      {signalsData?.signals && signalsData.signals.length > 0 && (
        <section>
          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <div className="text-eyebrow text-[color:var(--color-stone)]">Live Intelligence</div>
                <h2 className="mt-1 text-heading-lg text-white">Active Signals</h2>
              </div>
              <Badge tone="warning">{signalsData?.unread_count ?? 0} unread</Badge>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
              {signalsData?.signals?.map((signal: any) => (
                <motion.div
                  key={signal.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className={`rounded-lg border p-3 ${
                    signal.severity === "critical"
                      ? "border-rose-500/20 bg-rose-500/5"
                      : signal.severity === "warning"
                      ? "border-amber-500/20 bg-amber-500/5"
                      : "border-emerald-500/20 bg-emerald-500/5"
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
                    >
                      {signal.layer}
                    </Badge>
                  </div>
                  <p className="mt-2 text-[10px] text-[color:var(--color-slate)]">
                    {signal.description}
                  </p>
                  {signal.recommended_action && (
                    <p className="mt-2 text-[10px] text-white/70">
                      Action: {signal.recommended_action}
                    </p>
                  )}
                </motion.div>
              ))}
            </div>
          </Card>
        </section>
      )}

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl xl:col-span-2">
          <div className="mb-5 flex items-center justify-between gap-3">
            <div>
              <div className="text-eyebrow text-[color:var(--color-stone)]">Executive Council</div>
              <h2 className="mt-1 text-heading-lg text-white">Persistent Specialist Agents</h2>
            </div>
            <Badge tone="info">{overview.council.length} roles</Badge>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
            {overview.council.map((agent) => (
              <div key={agent.name} className="rounded-lg border border-white/[0.05] bg-black/20 p-3">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="truncate text-xs font-bold text-white">{agent.name}</h3>
                  <span className="size-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.8)]" />
                </div>
                <p className="mt-2 line-clamp-2 text-[10px] leading-relaxed text-[color:var(--color-slate)]">
                  {agent.mandate}
                </p>
              </div>
            ))}
          </div>
        </Card>

        <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
          <div className="mb-5">
            <div className="text-eyebrow text-[color:var(--color-stone)]">Autonomy</div>
            <h2 className="mt-1 text-heading-lg text-white">Event Triggers</h2>
          </div>
          <div className="space-y-3">
            {overview.event_triggers.length > 0 ? (
              overview.event_triggers.map((trigger) => (
                <div key={trigger.id} className="rounded-lg border border-white/[0.05] bg-black/20 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-xs font-bold text-white">{trigger.name}</span>
                    <Badge tone={trigger.enabled ? "success" : "warning"}>
                      {trigger.enabled ? "enabled" : "paused"}
                    </Badge>
                  </div>
                  <p className="mt-2 truncate text-[10px] text-[color:var(--color-slate)]">
                    {trigger.event_kind ?? "any event"} → {trigger.workflow.replace(/_/g, " ")}
                  </p>
                  <p className="mt-1 text-[10px] text-[color:var(--color-stone)]">
                    Fired {trigger.fire_count} times
                  </p>
                </div>
              ))
            ) : (
              <div className="rounded-lg border border-dashed border-white/[0.08] p-5 text-center">
                <Target className="mx-auto size-5 text-[color:var(--color-stone)]" />
                <p className="mt-3 text-xs text-[color:var(--color-slate)]">
                  No triggers yet. Create autonomous reactions from the Campaign Lab.
                </p>
              </div>
            )}
          </div>
        </Card>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[0.75fr_1.25fr]">
        <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
          <div className="mb-5">
            <div className="text-eyebrow text-[color:var(--color-stone)]">Workspace OS</div>
            <h2 className="mt-1 text-heading-lg text-white">Operating Areas</h2>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-1">
            {WORKSPACE_LINKS.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center justify-between gap-3 rounded-lg border border-white/[0.05] bg-black/20 px-3 py-3 text-sm font-bold text-white transition hover:bg-white/[0.05]"
                >
                  <span className="flex items-center gap-2">
                    <Icon className="size-4 text-[color:var(--color-slate)]" />
                    {item.label}
                  </span>
                  <ArrowUpRight className="size-4 text-[color:var(--color-stone)]" />
                </Link>
              );
            })}
          </div>
        </Card>

        <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
          <div className="mb-5 flex items-center justify-between gap-3">
            <div>
              <div className="text-eyebrow text-[color:var(--color-stone)]">Intelligence Layer</div>
              <h2 className="mt-1 text-heading-lg text-white">Continuous Learning Systems</h2>
            </div>
            <Eye className="size-5 text-[color:var(--color-slate)]" />
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {overview.intelligence_layers.map((layer) => (
              <div key={layer.name} className="rounded-lg border border-white/[0.05] bg-black/20 p-4">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-xs font-bold text-white">{layer.name}</h3>
                  <Badge tone={statusTone(layer.status)}>{layer.status}</Badge>
                </div>
                <p className="mt-2 text-[10px] leading-relaxed text-[color:var(--color-slate)]">
                  {layer.description}
                </p>
              </div>
            ))}
          </div>
          <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {Object.entries(overview.automation_coverage).slice(0, 8).map(([key, value]) => (
              <div key={key} className="rounded-lg border border-white/[0.05] bg-black/20 p-3">
                <div className="text-lg font-bold text-white">{value}</div>
                <div className="mt-1 text-[10px] uppercase tracking-wider text-[color:var(--color-stone)]">
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
