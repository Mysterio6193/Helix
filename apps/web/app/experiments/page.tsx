"use client";

import { useState } from "react";
import useSWR from "swr";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart3,
  Beaker,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Copy,
  FlaskConical,
  Layers,
  Lightbulb,
  Pause,
  Play,
  Plus,
  RefreshCw,
  RotateCcw,
  Settings,
  StopCircle,
  Target,
  TrendingUp,
  Users,
  X,
  XCircle,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

const STATUS_COLORS: Record<string, any> = {
  draft: "neutral",
  running: "info",
  paused: "warning",
  completed: "success",
  stopped: "error",
};

function ConfidenceBadge({ confidence }: { confidence: number | null }) {
  if (!confidence) return null;
  const tone = confidence >= 95 ? "success" : confidence >= 90 ? "warning" : "neutral";
  return (
    <Badge tone={tone} className="text-[10px]">
      {confidence.toFixed(1)}% confidence
    </Badge>
  );
}

function UpliftBadge({ uplift }: { uplift: number | null }) {
  if (!uplift) return null;
  const isPositive = uplift > 0;
  return (
    <span className={`text-xs font-bold ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
      {isPositive ? "+" : ""}{uplift.toFixed(1)}%
    </span>
  );
}

function FactorLevelCard({ name, data }: { name: string; data: any }) {
  if (!data?.levels) return null;
  const levels = Object.entries(data.levels) as [string, any][];
  return (
    <div className="p-3 rounded-lg border border-white/[0.06] bg-black/20">
      <div className="flex items-center gap-2 mb-2">
        <Layers className="size-3.5 text-[var(--color-signature)]" />
        <span className="text-xs font-bold text-white uppercase tracking-wider">{name}</span>
      </div>
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[10px] text-[color:var(--color-stone)] pb-1 border-b border-white/[0.03]">
          <span>Level</span>
          <div className="flex gap-3">
            <span className="w-12 text-right">Conv.</span>
            <span className="w-14 text-right">Uplift</span>
            <span className="w-12 text-right">p-value</span>
          </div>
        </div>
        {levels.map(([levelName, levelData]: [string, any]) => {
          const isControl = levelName === data.control_level;
          const sig = levelData.significant;
          return (
            <div key={levelName} className="flex items-center justify-between text-[11px]">
              <span className="flex items-center gap-1.5">
                {isControl && <Badge tone="neutral" className="text-[8px]">Control</Badge>}
                <span className={sig ? "text-emerald-400 font-semibold" : "text-white"}>{levelName}</span>
              </span>
              <div className="flex gap-3">
                <span className="w-12 text-right text-white">{levelData.rate}%</span>
                <span className={`w-14 text-right ${levelData.uplift > 0 ? "text-emerald-400" : "text-[color:var(--color-stone)]"}`}>
                  {levelData.uplift > 0 ? "+" : ""}{levelData.uplift}%
                </span>
                <span className="w-12 text-right text-[color:var(--color-stone)]">{levelData.p_value}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function ExperimentsPage() {
  const [selectedExperiment, setSelectedExperiment] = useState<any>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newExpName, setNewExpName] = useState("");
  const [newExpHypothesis, setNewExpHypothesis] = useState("");
  const [expType, setExpType] = useState<"ab" | "mvt">("ab");
  const [mvtFactors, setMvtFactors] = useState<{name: string; levels: string}[]>([
    {name: "", levels: ""},
  ]);

  const { data: experiments, mutate: mutateExperiments } = useSWR(
    "experiments",
    () => api.experiments.experiments(),
    { refreshInterval: 10000 }
  );

  const { data: experimentDetail } = useSWR(
    selectedExperiment ? ["experiment", selectedExperiment.id] : null,
    () => api.experiments.experiment(selectedExperiment!.id),
    { refreshInterval: 5000 }
  );

  const { data: suggestions } = useSWR(
    "experiment-suggestions",
    () => api.post("/api/v1/intelligence/experiments/suggest", {}),
    { refreshInterval: 60000 }
  );

  function addFactor() {
    setMvtFactors([...mvtFactors, {name: "", levels: ""}]);
  }

  function updateFactor(index: number, field: "name" | "levels", value: string) {
    const updated = mvtFactors.map((f, i) => i === index ? {...f, [field]: value} : f);
    setMvtFactors(updated);
  }

  function removeFactor(index: number) {
    setMvtFactors(mvtFactors.filter((_, i) => i !== index));
  }

  async function createExperiment() {
    if (!newExpName.trim()) return;
    try {
      let payload: any = {
        name: newExpName,
        hypothesis: newExpHypothesis || "Test hypothesis",
        experiment_type: expType,
      };

      if (expType === "mvt") {
        const factors: Record<string, any> = {};
        for (const f of mvtFactors) {
          if (!f.name.trim()) continue;
          const levelValues = f.levels.split(",").map(s => s.trim()).filter(Boolean);
          factors[f.name.trim()] = {
            levels: levelValues.map((v: string) => ({value: v, config: {}})),
          };
        }
        payload.factors = factors;
        payload.min_sample_size = 50; // MVT needs smaller per-variant sample
      }

      await api.experiments.createExperiment(payload);
      setNewExpName("");
      setNewExpHypothesis("");
      setExpType("ab");
      setMvtFactors([{name: "", levels: ""}]);
      setShowCreate(false);
      mutateExperiments();
    } catch (e) {
      console.error(e);
    }
  }

  async function startExperiment(id: string) {
    try {
      await api.experiments.startExperiment(id);
      mutateExperiments();
    } catch (e) {
      console.error(e);
    }
  }

  async function stopExperiment(id: string) {
    try {
      await api.experiments.stopExperiment(id);
      mutateExperiments();
      if (selectedExperiment?.id === id) {
        setSelectedExperiment(null);
      }
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <div className="space-y-8 animate-fade-up">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">
          Testing
        </div>
        <h1 className="mt-2 text-display-lg font-bold leading-tight text-white">
          Experiments
        </h1>
        <p className="mt-3 max-w-[72ch] text-body-md text-[color:var(--color-slate)]">
          A/B and multivariate experiments with statistical significance.
          Auto-detect winners and roll out winning variants with confidence.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_0.4fr]">
        <div className="space-y-6">
          {/* Experiment List */}
          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <div className="text-eyebrow text-[color:var(--color-stone)]">Active Tests</div>
                <h2 className="mt-1 text-heading-lg text-white">Experiments</h2>
              </div>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setShowCreate(!showCreate)}
              >
                <Plus className="size-3.5" />
                New Experiment
              </Button>
            </div>

            {showCreate && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="mb-4 p-4 rounded-lg border border-white/[0.06] bg-black/20 space-y-3"
              >
                <Input
                  placeholder="Experiment name..."
                  value={newExpName}
                  onChange={(e) => setNewExpName(e.target.value)}
                />
                <textarea
                  placeholder="Hypothesis (e.g., 'Lifestyle images will increase CTR by 15%')..."
                  value={newExpHypothesis}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNewExpHypothesis(e.target.value)}
                  rows={2}
                  className="w-full rounded-lg border border-white/[0.06] bg-black/20 px-3 py-2 text-sm text-white placeholder:text-[color:var(--color-stone)] focus:outline-none focus:border-white/20 resize-y"
                />

                {/* Experiment Type Toggle */}
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setExpType("ab")}
                    className={`flex-1 px-3 py-2 rounded-lg text-xs font-bold transition-colors ${
                      expType === "ab"
                        ? "bg-[var(--color-signature)] text-black"
                        : "bg-black/20 text-[color:var(--color-stone)] border border-white/[0.06]"
                    }`}
                  >
                    A/B Test
                  </button>
                  <button
                    type="button"
                    onClick={() => setExpType("mvt")}
                    className={`flex-1 px-3 py-2 rounded-lg text-xs font-bold transition-colors ${
                      expType === "mvt"
                        ? "bg-[var(--color-signature)] text-black"
                        : "bg-black/20 text-[color:var(--color-stone)] border border-white/[0.06]"
                    }`}
                  >
                    <Layers className="inline size-3 mr-1" />
                    MVT
                  </button>
                </div>

                {/* MVT Factors Input */}
                {expType === "mvt" && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-[color:var(--color-stone)] uppercase tracking-wider">Factors</span>
                      <Button variant="secondary" size="sm" onClick={addFactor}>
                        <Plus className="size-3" />
                        Add Factor
                      </Button>
                    </div>
                    {mvtFactors.map((factor, idx) => (
                      <div key={idx} className="flex gap-2 items-start">
                        <div className="flex-1 space-y-1">
                          <input
                            placeholder="Factor name (e.g., headline)"
                            value={factor.name}
                            onChange={(e) => updateFactor(idx, "name", e.target.value)}
                            className="w-full rounded-lg border border-white/[0.06] bg-black/20 px-2.5 py-1.5 text-xs text-white placeholder:text-[color:var(--color-stone)] focus:outline-none focus:border-white/20"
                          />
                          <input
                            placeholder="Levels (comma-sep, e.g., Great Deals, Limited Time)"
                            value={factor.levels}
                            onChange={(e) => updateFactor(idx, "levels", e.target.value)}
                            className="w-full rounded-lg border border-white/[0.06] bg-black/20 px-2.5 py-1.5 text-xs text-white placeholder:text-[color:var(--color-stone)] focus:outline-none focus:border-white/20"
                          />
                        </div>
                        {mvtFactors.length > 1 && (
                          <button
                            onClick={() => removeFactor(idx)}
                            className="mt-1 p-1 rounded hover:bg-white/[0.06] text-[color:var(--color-stone)]"
                          >
                            <X className="size-3" />
                          </button>
                        )}
                      </div>
                    ))}
                    <p className="text-[9px] text-[color:var(--color-stone)]">
                      Variants generated:{" "}
                      {mvtFactors
                        .filter(f => f.name.trim() && f.levels.trim())
                        .reduce((acc, f) => acc * f.levels.split(",").filter(s => s.trim()).length, 1) || 1}
                    </p>
                  </div>
                )}

                <div className="flex gap-2">
                  <Button variant="primary" size="sm" onClick={createExperiment}>
                    Create
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => setShowCreate(false)}>
                    Cancel
                  </Button>
                </div>
              </motion.div>
            )}

            <div className="space-y-3">
              {experiments?.map((exp: any) => (
                <motion.div
                  key={exp.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className={`rounded-lg border p-4 cursor-pointer transition-colors ${
                    selectedExperiment?.id === exp.id
                      ? "border-white/20 bg-white/5"
                      : "border-white/[0.06] bg-black/20 hover:bg-white/[0.02]"
                  }`}
                  onClick={() => setSelectedExperiment(exp)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {exp.experiment_type === "mvt" ? (
                        <Layers className="size-5 text-[var(--color-signature)]" />
                      ) : (
                        <FlaskConical className="size-5 text-[color:var(--color-slate)]" />
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-bold text-white">{exp.name}</h3>
                          {exp.experiment_type === "mvt" && (
                            <Badge tone="info" className="text-[8px]">MVT</Badge>
                          )}
                        </div>
                        <p className="text-[10px] text-[color:var(--color-stone)] truncate max-w-[300px]">
                          {exp.hypothesis}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge tone={STATUS_COLORS[exp.status] || "neutral"}>
                        {exp.status}
                      </Badge>
                      {exp.status === "draft" && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            startExperiment(exp.id);
                          }}
                        >
                          <Play className="size-3" />
                        </Button>
                      )}
                      {exp.status === "running" && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            stopExperiment(exp.id);
                          }}
                        >
                          <StopCircle className="size-3" />
                        </Button>
                      )}
                    </div>
                  </div>

                  {exp.winner && (
                    <div className="mt-3 flex items-center gap-2">
                      <CheckCircle2 className="size-3.5 text-emerald-400" />
                      <span className="text-xs text-emerald-400">
                        Winner: {exp.winner} ({exp.confidence?.toFixed(1)}% confidence)
                      </span>
                    </div>
                  )}

                  {exp.experiment_type === "mvt" && exp.factors && (
                    <div className="mt-2 flex gap-1.5 flex-wrap">
                      {Object.keys(exp.factors).map((fn) => (
                        <Badge key={fn} tone="info" className="text-[8px]">
                          {fn}
                        </Badge>
                      ))}
                    </div>
                  )}
                </motion.div>
              ))}

              {!experiments?.length && (
                <div className="text-center py-8">
                  <Beaker className="mx-auto size-8 text-[color:var(--color-stone)]" />
                  <p className="mt-3 text-sm text-[color:var(--color-slate)]">
                    No experiments yet. Create one to start testing.
                  </p>
                </div>
              )}
            </div>
          </Card>

          {/* Experiment Detail */}
          <AnimatePresence>
            {selectedExperiment && experimentDetail && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
                  <div className="mb-5 flex items-center justify-between">
                    <div>
                      <div className="text-eyebrow text-[color:var(--color-stone)]">Results</div>
                      <div className="flex items-center gap-2">
                        <h2 className="mt-1 text-heading-lg text-white">{experimentDetail.experiment_name}</h2>
                        {experimentDetail.experiment_type === "mvt" && (
                          <Badge tone="info" className="text-[10px]">MVT</Badge>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setSelectedExperiment(null)}
                    >
                      <X className="size-4" />
                    </Button>
                  </div>

                  {/* Stats overview */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="p-3 rounded-lg border border-white/[0.06] bg-black/20">
                      <div className="text-[10px] text-[color:var(--color-stone)] uppercase tracking-wider">Status</div>
                      <Badge tone={STATUS_COLORS[experimentDetail.status] || "neutral"} className="mt-1">
                        {experimentDetail.status}
                      </Badge>
                    </div>
                    <div className="p-3 rounded-lg border border-white/[0.06] bg-black/20">
                      <div className="text-[10px] text-[color:var(--color-stone)] uppercase tracking-wider">Primary Metric</div>
                      <div className="mt-1 text-sm font-bold text-white capitalize">
                        {experimentDetail.primary_metric?.replace("_", " ")}
                      </div>
                    </div>
                    <div className="p-3 rounded-lg border border-white/[0.06] bg-black/20">
                      <div className="text-[10px] text-[color:var(--color-stone)] uppercase tracking-wider">Control</div>
                      <div className="mt-1 text-sm font-bold text-white">
                        {experimentDetail.control_variant}
                      </div>
                    </div>
                    <div className="p-3 rounded-lg border border-white/[0.06] bg-black/20">
                      <div className="text-[10px] text-[color:var(--color-stone)] uppercase tracking-wider">Winner</div>
                      <div className="mt-1 text-sm font-bold text-white">
                        {experimentDetail.winner ? (
                          <span className="text-emerald-400">{experimentDetail.winner}</span>
                        ) : (
                          <span className="text-[color:var(--color-stone)]">Undetermined</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Variant Results Table */}
                  {experimentDetail.results && (
                    <div className="overflow-x-auto mb-6">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-white/[0.06]">
                            <th className="text-left py-2 px-3 text-[color:var(--color-stone)]">Variant</th>
                            <th className="text-right py-2 px-3 text-[color:var(--color-stone)]">Impressions</th>
                            <th className="text-right py-2 px-3 text-[color:var(--color-stone)]">Conv.</th>
                            <th className="text-right py-2 px-3 text-[color:var(--color-stone)]">Conv. Rate</th>
                            <th className="text-right py-2 px-3 text-[color:var(--color-stone)]">CTR</th>
                            <th className="text-right py-2 px-3 text-[color:var(--color-stone)]">Revenue</th>
                            <th className="text-right py-2 px-3 text-[color:var(--color-stone)]">Significance</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.values(experimentDetail.results).map((variant: any) => {
                            const isControl = variant.variant_id === experimentDetail.control_variant;
                            const test = experimentDetail.statistical_tests?.[variant.variant_id];
                            const convTest = test?.conversion_rate;
                            const factorLevels = variant.factor_levels;

                            return (
                              <tr
                                key={variant.variant_id}
                                className={`border-b border-white/[0.03] ${
                                  isControl ? "bg-white/[0.02]" : ""
                                }`}
                              >
                                <td className="py-2.5 px-3">
                                  <div className="flex items-center gap-2">
                                    <span className="text-white font-semibold">{variant.variant_name}</span>
                                    {isControl && (
                                      <Badge tone="neutral" className="text-[8px]">Control</Badge>
                                    )}
                                    {experimentDetail.winner === variant.variant_id && (
                                      <Badge tone="success" className="text-[8px]">Winner</Badge>
                                    )}
                                  </div>
                                  {factorLevels && (
                                    <div className="flex gap-1 mt-1 flex-wrap">
                                      {Object.entries(factorLevels).map(([fn, fv]) => (
                                        <Badge key={fn} tone="info" className="text-[7px]">
                                          {fn}: {String(fv)}
                                        </Badge>
                                      ))}
                                    </div>
                                  )}
                                </td>
                                <td className="text-right py-2.5 px-3 text-white">{variant.impressions.toLocaleString()}</td>
                                <td className="text-right py-2.5 px-3 text-white">{variant.conversions.toLocaleString()}</td>
                                <td className="text-right py-2.5 px-3">
                                  <span className="text-white">{variant.conversion_rate}%</span>
                                  {convTest && <UpliftBadge uplift={convTest.uplift} />}
                                </td>
                                <td className="text-right py-2.5 px-3 text-white">{variant.ctr}%</td>
                                <td className="text-right py-2.5 px-3 text-white">${variant.revenue.toFixed(2)}</td>
                                <td className="text-right py-2.5 px-3">
                                  {convTest ? (
                                    <div className="flex flex-col items-end gap-0.5">
                                      <ConfidenceBadge confidence={convTest.confidence} />
                                      <span className="text-[10px] text-[color:var(--color-stone)]">
                                        p={convTest.p_value}
                                        {convTest.bonferroni_applied && (
                                          <span className="ml-1 text-[8px]" title="Bonferroni corrected">
                                            (adj.)
                                          </span>
                                        )}
                                      </span>
                                    </div>
                                  ) : (
                                    <span className="text-[10px] text-[color:var(--color-stone)]">
                                      Need {experimentDetail.min_sample_size}+ samples
                                    </span>
                                  )}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Factor Analysis (MVT only) */}
                  {experimentDetail.experiment_type === "mvt" && experimentDetail.factor_analysis && (
                    <div className="mb-6">
                      <div className="flex items-center gap-2 mb-3">
                        <Layers className="size-4 text-[var(--color-signature)]" />
                        <h3 className="text-sm font-bold text-white">Factor Analysis</h3>
                        <Badge tone="info" className="text-[8px]">Bonferroni corrected</Badge>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {Object.entries(experimentDetail.factor_analysis).map(([factorName, factorData]: [string, any]) => (
                          <FactorLevelCard key={factorName} name={factorName} data={factorData} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Winner banner */}
                  {experimentDetail.winner && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="mt-6 p-4 rounded-lg border border-emerald-500/20 bg-emerald-500/5"
                    >
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="size-6 text-emerald-400" />
                        <div>
                          <p className="text-sm font-bold text-white">
                            Winner detected: {experimentDetail.winner}
                          </p>
                          <p className="text-xs text-[var(--color-slate)]">
                            {experimentDetail.confidence?.toFixed(1)}% confidence ·{" "}
                            {experimentDetail.uplift > 0 ? "+" : ""}
                            {(experimentDetail.uplift * 100).toFixed(1)}% uplift over control
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="space-y-6">
          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-4">
              <div className="text-eyebrow text-[color:var(--color-stone)]">Methodology</div>
              <h2 className="mt-1 text-heading-lg text-white">Statistics</h2>
            </div>

            <div className="space-y-4">
              <div className="p-3 rounded-lg border border-white/[0.06] bg-black/20">
                <div className="flex items-center gap-2 mb-1">
                  <Target className="size-4 text-[var(--color-signature)]" />
                  <span className="text-xs font-bold text-white">Two-Proportion Z-Test</span>
                </div>
                <p className="text-[11px] text-[color:var(--color-slate)]">
                  For conversion rates and CTR. Tests if the difference between two proportions is statistically significant.
                </p>
              </div>

              <div className="p-3 rounded-lg border border-white/[0.06] bg-black/20">
                <div className="flex items-center gap-2 mb-1">
                  <Users className="size-4 text-[var(--color-signature)]" />
                  <span className="text-xs font-bold text-white">Min. Sample Size</span>
                </div>
                <p className="text-[11px] text-[color:var(--color-slate)]">
                  Default 100 impressions per variant before significance testing begins. Prevents false positives from small samples.
                </p>
              </div>

              <div className="p-3 rounded-lg border border-white/[0.06] bg-black/20">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="size-4 text-[var(--color-signature)]" />
                  <span className="text-xs font-bold text-white">Auto-Stop</span>
                </div>
                <p className="text-[11px] text-[color:var(--color-slate)]">
                  When a variant reaches 95% confidence with sufficient samples, the experiment automatically stops and declares a winner.
                </p>
              </div>

              <div className="p-3 rounded-lg border border-white/[0.06] bg-black/20">
                <div className="flex items-center gap-2 mb-1">
                  <BarChart3 className="size-4 text-[var(--color-signature)]" />
                  <span className="text-xs font-bold text-white">Bonferroni Correction</span>
                </div>
                <p className="text-[11px] text-[color:var(--color-slate)]">
                  For MVT experiments, adjusts significance thresholds to control the family-wise error rate from multiple comparisons.
                </p>
              </div>
            </div>
          </Card>

          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-4">
              <div className="flex items-center gap-2">
                <Lightbulb className="size-4 text-amber-400" />
                <span className="text-eyebrow text-[color:var(--color-stone)]">AI Suggestions</span>
              </div>
              <h2 className="mt-1 text-heading-lg text-white">What to Test</h2>
            </div>
            {suggestions && suggestions.length > 0 ? (
              <div className="space-y-3">
                {suggestions.map((s: any, i: number) => (
                  <div key={i} className="p-3 rounded-lg border border-white/[0.06] bg-black/20">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-white">{s.hypothesis}</span>
                      <Badge tone={s.type === "ab" ? "info" : "warning"} className="text-[8px] uppercase">
                        {s.type}
                      </Badge>
                    </div>
                    {s.variants && (
                      <p className="text-[10px] text-[color:var(--color-slate)] mb-2">
                        Variants: {s.variants.join(", ")}
                      </p>
                    )}
                    <div className="flex flex-wrap gap-1">
                      {s.metrics?.map((m: string) => (
                        <span key={m} className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400">
                          {m}
                        </span>
                      ))}
                    </div>
                    <div className="mt-2 flex items-center gap-2 text-[9px] text-[color:var(--color-stone)]">
                      <Users className="size-3" />
                      <span>n={s.suggested_sample_size || "?"}</span>
                      {s.suggested_duration && (
                        <>
                          <Clock className="size-3" />
                          <span>{s.suggested_duration}</span>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3 rounded-lg border border-white/[0.06] bg-black/20">
                <p className="text-[11px] text-[color:var(--color-slate)]">
                  Run more experiments to get AI-powered suggestions for what to test next.
                </p>
              </div>
            )}
          </Card>

          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-4">
              <div className="text-eyebrow text-[color:var(--color-stone)]">Status</div>
              <h2 className="mt-1 text-heading-lg text-white">Overview</h2>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[color:var(--color-slate)]">Total Experiments</span>
                <Badge tone="info">{experiments?.length || 0}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-[color:var(--color-slate)]">Running</span>
                <Badge tone="success">
                  {experiments?.filter((e: any) => e.status === "running").length || 0}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-[color:var(--color-slate)]">Completed</span>
                <Badge tone="neutral">
                  {experiments?.filter((e: any) => e.status === "completed").length || 0}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-[color:var(--color-slate)]">Winners Found</span>
                <Badge tone="success">
                  {experiments?.filter((e: any) => e.winner).length || 0}
                </Badge>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
