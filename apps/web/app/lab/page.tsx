"use client";

import { useEffect, useState } from "react";
import useSWR from "swr";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity,
  Award,
  BarChart3,
  CheckCircle,
  HelpCircle,
  Play,
  RotateCw,
  Sparkles,
  TrendingDown,
  TrendingUp,
  AlertCircle
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardSubtitle, CardTitle } from "@/components/ui/card";
import { api, type Brand } from "@/lib/api";
import { shortId } from "@/lib/utils";

// Mock data representing dynamic live A/B test splits
const INITIAL_EXPERIMENTS = [
  {
    id: "exp-1",
    name: "Summer Refresh ad-set: Visual Style",
    hypothesis: "A Brutalist Bold visual layout will yield 25% higher CTR than the Editorial style for local organic diners.",
    metrics: {
      variant_a: { name: "Variant A (Editorial)", ctr: 1.15, conversion: 2.1, roas: 1.62, spend: 320, active: true },
      variant_b: { name: "Variant B (Brutalist)", ctr: 2.45, conversion: 4.8, roas: 3.12, spend: 450, active: true }
    },
    status: "running",
    winner: null,
    started_at: "2026-05-20T08:00:00Z"
  },
  {
    id: "exp-2",
    name: "Copy Hook: Numerical vs Story",
    hypothesis: "Positioning our ingredients with exact local mileage figures ('Made within 4 miles') beats story-centric taglines.",
    metrics: {
      variant_a: { name: "Variant A (Story Vibe)", ctr: 1.84, conversion: 3.4, roas: 2.25, spend: 600, active: false },
      variant_b: { name: "Variant B (Numerical)", ctr: 3.12, conversion: 5.6, roas: 3.84, spend: 850, active: false }
    },
    status: "completed",
    winner: "variant_b",
    started_at: "2026-05-15T12:00:00Z"
  }
];

export default function LabPage() {
  const [brandId, setBrandId] = useState("");
  const [selectedEvent, setSelectedEvent] = useState("campaign_fatigue_detected");
  const [loading, setLoading] = useState(false);
  const [simulatedResult, setSimulatedResult] = useState<{
    ok: boolean;
    event_kind: string;
    triggered_runs_count: number;
  } | null>(null);

  const { data: brands } = useSWR<Brand[]>("brands", () => api.brands.list(), {
    revalidateOnFocus: false,
  });

  const { data: experiments, mutate: mutateExperiments } = useSWR(
    "experiments",
    () => api.experiments.list(),
    { refreshInterval: 30000 }
  );

  useEffect(() => {
    if (!brandId && brands && brands.length > 0) setBrandId(brands[0].id);
  }, [brandId, brands]);

  async function triggerSimulation() {
    if (!brandId) return;
    setLoading(true);
    setSimulatedResult(null);

    // Mock realistic telemetry payload depending on selected event
    let payload: Record<string, any> = {};
    if (selectedEvent === "roas_dropped") {
      payload = { roas: 1.58, target_roas: 2.5, current_spend_daily: 120 };
    } else if (selectedEvent === "ctr_dropped") {
      payload = { ctr: 0.92, benchmark_ctr: 1.8 };
    } else {
      payload = { fatigue_score: 0.85, creative_lifetime_days: 14 };
    }

    try {
      // workspace_id is required. We fetch workspace_id from selected brand
      const selectedBrand = (brands ?? []).find(b => b.id === brandId);
      const workspaceId = selectedBrand?.workspace_id;

      if (!workspaceId) {
        throw new Error("No active workspace found for this brand");
      }

      const res = await api.events.publish({
        workspace_id: workspaceId,
        brand_id: brandId,
        event_kind: selectedEvent,
        payload
      });

      setSimulatedResult(res);
    } catch (err: any) {
      console.error(err);
      alert(err.message || "Failed to trigger event.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">
          Optimize
        </div>
        <h1 className="text-display-lg text-[color:var(--color-charcoal)]">
          Campaign Lab
        </h1>
        <p className="mt-2 max-w-[60ch] text-body-md text-[color:var(--color-slate)]">
          Simulate live performance fluctuations, track A/B test splits, and trigger autonomous recovery workflows.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Left 2 Cols: Experiments Dashboard */}
        <div className="space-y-6 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="text-heading-md flex items-center gap-2">
              <BarChart3 className="size-5 text-[color:var(--color-ink)]" />
              Active Splits & Experimentation
            </h2>
            <Badge tone="info">Continuous A/B Engine</Badge>
          </div>

          {(experiments || []).map((exp: any) => {
            const variants = exp.variants || [];
            const va = variants[0] || { name: "Variant A", ctr: 0, conversion: 0, roas: 0, spend: 0, active: false };
            const vb = variants[1] || { name: "Variant B", ctr: 0, conversion: 0, roas: 0, spend: 0, active: false };
            const winnerKey = exp.winner;
            
            return (
              <Card key={exp.id} className="relative overflow-hidden border border-[rgba(255,255,255,0.06)] bg-[#13141a]/40 backdrop-blur-md shadow-2xl p-6 rounded-2xl">
                {exp.status === "completed" && (
                  <div className="absolute top-4 right-4 flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold text-emerald-400">
                    <CheckCircle className="size-3.5" />
                    Completed
                  </div>
                )}
                
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-bold text-[color:var(--color-ink)]">{exp.name}</h3>
                    <p className="text-xs text-[color:var(--color-muted)] font-mono mt-1">Started: {new Date(exp.started_at).toLocaleDateString()}</p>
                  </div>

                  <div className="p-3 bg-neutral-900/30 border border-neutral-800/40 rounded-xl">
                    <span className="text-xs font-semibold text-accent uppercase tracking-wider block mb-1">Hypothesis</span>
                    <p className="text-body-sm text-[color:var(--color-slate)] italic">"{exp.hypothesis}"</p>
                  </div>

                  {/* Splits visual side-by-side */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                    {/* Variant A */}
                    <div className={`p-4 rounded-xl border relative ${winnerKey === "variant_a" ? "border-emerald-500/30 bg-emerald-500/5" : "border-neutral-800/50 bg-neutral-950/20"}`}>
                      {winnerKey === "variant_a" && (
                        <div className="absolute -top-2.5 -left-2.5 bg-emerald-500 text-white rounded-full p-1 shadow-lg">
                          <Award className="size-3.5" />
                        </div>
                      )}
                      <h4 className="text-sm font-semibold text-[color:var(--color-ink)] flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-neutral-600"></span>
                        {va.name}
                      </h4>
                      <div className="grid grid-cols-3 gap-2 mt-4 text-center">
                        <div>
                          <span className="text-xs text-[color:var(--color-muted)]">ROAS</span>
                          <span className={`block text-base font-bold mt-0.5 ${winnerKey === "variant_a" ? "text-emerald-400" : "text-[color:var(--color-ink)]"}`}>{va.roas}x</span>
                        </div>
                        <div>
                          <span className="text-xs text-[color:var(--color-muted)]">CTR</span>
                          <span className="block text-base font-bold text-[color:var(--color-ink)] mt-0.5">{va.ctr}%</span>
                        </div>
                        <div>
                          <span className="text-xs text-[color:var(--color-muted)]">Conv.</span>
                          <span className="block text-base font-bold text-[color:var(--color-ink)] mt-0.5">{va.conversion}%</span>
                        </div>
                      </div>
                    </div>

                    {/* Variant B */}
                    <div className={`p-4 rounded-xl border relative ${winnerKey === "variant_b" ? "border-emerald-500/30 bg-emerald-500/5" : "border-neutral-800/50 bg-neutral-950/20"}`}>
                      {winnerKey === "variant_b" && (
                        <div className="absolute -top-2.5 -left-2.5 bg-emerald-500 text-white rounded-full p-1 shadow-lg">
                          <Award className="size-3.5" />
                        </div>
                      )}
                      <h4 className="text-sm font-semibold text-[color:var(--color-ink)] flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-accent"></span>
                        {vb.name}
                      </h4>
                      <div className="grid grid-cols-3 gap-2 mt-4 text-center">
                        <div>
                          <span className="text-xs text-[color:var(--color-muted)]">ROAS</span>
                          <span className={`block text-base font-bold mt-0.5 ${winnerKey === "variant_b" ? "text-emerald-400" : "text-[color:var(--color-ink)]"}`}>{vb.roas}x</span>
                        </div>
                        <div>
                          <span className="text-xs text-[color:var(--color-muted)]">CTR</span>
                          <span className="block text-base font-bold text-[color:var(--color-ink)] mt-0.5">{vb.ctr}%</span>
                        </div>
                        <div>
                          <span className="text-xs text-[color:var(--color-muted)]">Conv.</span>
                          <span className="block text-base font-bold text-[color:var(--color-ink)] mt-0.5">{vb.conversion}%</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Summary / Outcome */}
                  {exp.status === "completed" && (
                    <div className="flex items-center gap-2 p-3 bg-emerald-500/5 border border-emerald-500/10 rounded-xl text-emerald-400 text-body-sm">
                      <Sparkles className="size-4 shrink-0" />
                      <span><strong>Experiment Resolved:</strong> Variant B yielded significantly higher CTR and Conversion Rates. Bidding budget was autonomously re-routed 100% to Variant B.</span>
                    </div>
                  )}
                </div>
              </Card>
            );
          })}
        </div>

        {/* Right Col: Interactive Simulation Console */}
        <aside className="space-y-6">
          <h2 className="text-heading-md flex items-center gap-2">
            <Activity className="size-5 text-[color:var(--color-ink)]" />
            Event Simulator
          </h2>

          <Card className="border border-[rgba(255,255,255,0.06)] bg-[#13141a]/60 backdrop-blur-md shadow-2xl p-6 rounded-2xl space-y-6">
            <div className="space-y-4">
              <div className="flex flex-col gap-2">
                <label className="text-xs uppercase font-bold tracking-wider text-[color:var(--color-stone)]">
                  Brand Scope
                </label>
                <select
                  value={brandId}
                  onChange={(e) => setBrandId(e.target.value)}
                  className="rounded-lg border border-neutral-800 bg-[#0d0e12] px-3 py-2 text-body-sm text-[color:var(--color-ink)] focus:outline-none focus:ring-1 focus:ring-accent"
                >
                  {!brandId && <option value="">— select a brand —</option>}
                  {(brands ?? []).map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-xs uppercase font-bold tracking-wider text-[color:var(--color-stone)]">
                  Simulate Event Type
                </label>
                <div className="space-y-2">
                  {[
                    { id: "campaign_fatigue_detected", label: "Campaign Fatigue (CTR/CAC shift)", icon: AlertCircle, color: "text-amber-500" },
                    { id: "roas_dropped", label: "ROAS Drop (ROAS < Target)", icon: TrendingDown, color: "text-red-500" },
                    { id: "ctr_dropped", label: "CTR Drop (High CPM, Low Clicks)", icon: TrendingDown, color: "text-orange-500" }
                  ].map((evt) => (
                    <button
                      key={evt.id}
                      onClick={() => setSelectedEvent(evt.id)}
                      className={`w-full flex items-center gap-3 p-3 rounded-xl border text-left text-body-sm transition-all ${
                        selectedEvent === evt.id
                          ? "border-accent bg-accent/5 font-semibold text-[color:var(--color-ink)]"
                          : "border-neutral-800 hover:border-neutral-700 bg-neutral-900/20 text-[color:var(--color-slate)]"
                      }`}
                    >
                      <evt.icon className={`size-4 shrink-0 ${evt.color}`} />
                      <span>{evt.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <Button
                variant="primary"
                size="md"
                onClick={triggerSimulation}
                disabled={!brandId || loading}
                className="w-full h-11 relative overflow-hidden group shadow-lg"
              >
                {loading ? (
                  <>
                    <RotateCw className="size-4 animate-spin mr-2" />
                    Publishing Event...
                  </>
                ) : (
                  <>
                    <Play className="size-4 mr-2 group-hover:scale-110 transition-transform" />
                    Publish Telemetry Event
                  </>
                )}
              </Button>
            </div>

            {/* Results Alert panel */}
            <AnimatePresence>
              {simulatedResult && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/10 text-emerald-400 space-y-3"
                >
                  <div className="flex items-center gap-2">
                    <Sparkles className="size-4 shrink-0 animate-pulse" />
                    <span className="font-bold text-sm">Autonomous Workflow Activated</span>
                  </div>
                  <p className="text-xs text-[color:var(--color-slate)] leading-relaxed">
                    Published event <code>{simulatedResult.event_kind}</code>. Helix triggered <strong>{simulatedResult.triggered_runs_count}</strong> executive review run(s) autonomously in response.
                  </p>
                  <div className="pt-1">
                    <Link
                      href="/workflows"
                      className="inline-flex items-center gap-1.5 text-xs uppercase font-bold text-emerald-400 hover:underline"
                    >
                      Open Live Actions Feed →
                    </Link>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </Card>
        </aside>
      </div>
    </div>
  );
}

// Quick tiny NextJS link inline stub
function Link({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) {
  return (
    <a href={href} className={className}>
      {children}
    </a>
  );
}
