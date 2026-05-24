"use client";

import { useState } from "react";
import useSWR from "swr";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  Bot,
  CheckCircle,
  Clock,
  Cpu,
  Play,
  RotateCw,
  Shield,
  TrendingUp,
  XCircle,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";

const RULE_ICONS: Record<string, React.ComponentType<any>> = {
  roas_recovery: TrendingUp,
  ctr_fatigue: AlertTriangle,
  budget_rebalance: Activity,
  winning_variant_scale: CheckCircle,
  churn_rescue: Shield,
};

export default function OptimizationPage() {
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState<any>(null);

  const { data: rules, isLoading: rulesLoading } = useSWR(
    "optimization-rules",
    () => api.optimization.rules(),
    { refreshInterval: 30000 }
  );

  const { data: approvals, mutate: mutateApprovals } = useSWR(
    "optimization-approvals",
    () => api.optimization.approvals(),
    { refreshInterval: 5000 }
  );

  const { data: history } = useSWR(
    "optimization-history",
    () => api.optimization.history(),
    { refreshInterval: 10000 }
  );

  async function evaluateRules() {
    setEvaluating(true);
    setEvalResult(null);
    try {
      const result = await api.optimization.evaluate();
      setEvalResult(result);
      mutateApprovals();
    } catch (e) {
      console.error(e);
    } finally {
      setEvaluating(false);
    }
  }

  async function handleApproval(approvalId: string, action: "approve" | "reject") {
    try {
      if (action === "approve") {
        await api.optimization.approve(approvalId);
      } else {
        await api.optimization.reject(approvalId);
      }
      mutateApprovals();
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <div className="space-y-8 animate-fade-up">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">
          Autonomous Engine
        </div>
        <h1 className="mt-2 text-display-lg font-bold leading-tight text-white">
          Optimization Console
        </h1>
        <p className="mt-3 max-w-[72ch] text-body-md text-[color:var(--color-slate)]">
          Helix continuously evaluates optimization rules, detects anomalies,
          and executes autonomous actions. Review pending approvals and
          execution history.
        </p>
      </header>

      <div className="flex items-center gap-4">
        <Button
          variant="primary"
          size="md"
          onClick={evaluateRules}
          disabled={evaluating}
          className="relative overflow-hidden"
        >
          {evaluating ? (
            <>
              <RotateCw className="size-4 animate-spin" />
              Evaluating...
            </>
          ) : (
            <>
              <Play className="size-4" />
              Evaluate Rules Now
            </>
          )}
        </Button>
        <span className="text-sm text-[color:var(--color-stone)]">
          Auto-evaluates every 5 minutes
        </span>
      </div>

      <AnimatePresence>
        {evalResult && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-4"
          >
            <div className="flex items-center gap-2">
              <CheckCircle className="size-5 text-emerald-400" />
              <span className="text-sm font-bold text-emerald-200">
                Evaluation Complete
              </span>
            </div>
            <p className="mt-2 text-xs text-emerald-200/70">
              {evalResult.triggered} rules triggered,{" "}
              {evalResult.executed?.length} actions executed,{" "}
              {evalResult.pending_approval?.length} pending approval.
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_0.4fr]">
        <div className="space-y-6">
          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <div className="text-eyebrow text-[color:var(--color-stone)]">
                  Rules
                </div>
                <h2 className="mt-1 text-heading-lg text-white">
                  Active Optimization Rules
                </h2>
              </div>
              <Badge tone="info">{rules?.length ?? 0} rules</Badge>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {rules?.map((rule: any, i: number) => {
                const Icon = RULE_ICONS[rule.rule_id] || Bot;
                return (
                  <motion.div
                    key={rule.rule_id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="rounded-lg border border-white/[0.06] bg-black/20 p-4"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <span className="inline-flex size-8 items-center justify-center rounded-lg bg-white/[0.06]"
                        >
                          <Icon className="size-4 text-[color:var(--color-slate)]" />
                        </span>
                        <div>
                          <h3 className="text-sm font-bold text-white">
                            {rule.name}
                          </h3>
                          <p className="mt-1 text-[10px] text-[color:var(--color-slate)]">
                            {rule.description}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          tone={
                            rule.severity === "critical"
                              ? "error"
                              : rule.severity === "high"
                              ? "warning"
                              : "info"
                          }
                        >
                          {rule.severity}
                        </Badge>
                        {rule.approval_required && (
                          <Badge tone="warning">Approval</Badge>
                        )}
                      </div>
                    </div>
                    <div className="mt-3 flex items-center gap-4 text-[10px] text-[color:var(--color-stone)]">
                      <span>{rule.conditions_count} conditions</span>
                      <span>{rule.actions_count} actions</span>
                      <span className="flex items-center gap-1">
                        <Clock className="size-3" />
                        {rule.cooldown_hours}h cooldown
                      </span>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </Card>

          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-5">
              <div className="text-eyebrow text-[color:var(--color-stone)]">
                History
              </div>
              <h2 className="mt-1 text-heading-lg text-white">
                Execution Log
              </h2>
            </div>

            <div className="space-y-3">
              {history?.map((item: any, i: number) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.03 }}
                  className="flex items-center gap-3 rounded-lg border border-white/[0.05] bg-black/20 p-3"
                >
                  <div
                    className={`size-2 rounded-full ${
                      item.severity === "critical"
                        ? "bg-rose-400"
                        : item.severity === "warning"
                        ? "bg-amber-400"
                        : "bg-emerald-400"
                    }`}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-white truncate">
                      {item.title}
                    </p>
                    <p className="text-[10px] text-[color:var(--color-stone)]">
                      {item.description}
                    </p>
                  </div>
                  <span className="text-[10px] text-[color:var(--color-stone)]">
                    {item.created_at
                      ? new Date(item.created_at).toLocaleTimeString()
                      : ""}
                  </span>
                </motion.div>
              ))}

              {!history?.length && (
                <p className="text-center text-sm text-[color:var(--color-slate)] py-8">
                  No optimization actions executed yet.
                </p>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-4">
              <div className="text-eyebrow text-[color:var(--color-stone)]">
                Approvals
              </div>
              <h2 className="mt-1 text-heading-lg text-white">
                Pending
              </h2>
            </div>

            <div className="space-y-3">
              {approvals && approvals.length > 0 ? (
                approvals.map((approval: any) => (
                  <div
                    key={approval.id}
                    className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-4"
                  >
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="size-4 text-amber-400" />
                      <span className="text-xs font-bold text-amber-200">
                        {approval.rule_name}
                      </span>
                    </div>
                    <p className="mt-2 text-[10px] text-amber-200/70">
                      {approval.description}
                    </p>
                    <div className="mt-3 flex gap-2">
                      <button
                        onClick={() => handleApproval(approval.id, "approve")}
                        className="flex-1 rounded bg-emerald-500/20 px-3 py-1.5 text-[10px] font-bold text-emerald-300 hover:bg-emerald-500/30"
                      >
                        <CheckCircle className="inline size-3 mr-1" />
                        Approve
                      </button>
                      <button
                        onClick={() => handleApproval(approval.id, "reject")}
                        className="flex-1 rounded bg-rose-500/20 px-3 py-1.5 text-[10px] font-bold text-rose-300 hover:bg-rose-500/30"
                      >
                        <XCircle className="inline size-3 mr-1" />
                        Reject
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8">
                  <Shield className="mx-auto size-8 text-[color:var(--color-stone)]" />
                  <p className="mt-3 text-sm text-[color:var(--color-slate)]">
                    No pending approvals. All optimization rules are running
                    autonomously.
                  </p>
                </div>
              )}
            </div>
          </Card>

          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-4">
              <div className="text-eyebrow text-[color:var(--color-stone)]">
                Status
              </div>
              <h2 className="mt-1 text-heading-lg text-white">
                Engine Health
              </h2>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[color:var(--color-slate)]">
                  Rules Engine
                </span>
                <div className="flex items-center gap-1.5">
                  <div className="size-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-xs text-emerald-400">Active</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-[color:var(--color-slate)]">
                  Auto-Actions
                </span>
                <div className="flex items-center gap-1.5">
                  <div className="size-2 rounded-full bg-emerald-400" />
                  <span className="text-xs text-emerald-400">Running</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-[color:var(--color-slate)]">
                  Approval Queue
                </span>
                <Badge tone="info">
                  {approvals?.length ?? 0} pending
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-[color:var(--color-slate)]">
                  Eval Frequency
                </span>
                <span className="text-xs text-white">Every 5 min</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
