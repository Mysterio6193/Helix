"use client";

import { motion } from "framer-motion";
function formatDistanceStrict(start: Date, end: Date): string {
  const diffMs = end.getTime() - start.getTime();
  const diffSecs = Math.max(0, Math.floor(diffMs / 1000));
  if (diffSecs < 60) return `${diffSecs}s`;
  const diffMins = Math.floor(diffSecs / 60);
  if (diffMins < 60) return `${diffMins}m ${diffSecs % 60}s`;
  const diffHours = Math.floor(diffMins / 60);
  return `${diffHours}h ${diffMins % 60}m`;
}

import { Badge, statusTone } from "@/components/ui/badge";
import { Card, CardSubtitle, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { RunDetail } from "@/lib/api";

interface StepRecord {
  step: string;
  agent: string;
  skill?: string | null;
  started_at: number;
  ended_at?: number | null;
  status: string;
  cost_usd?: number;
  tokens_in?: number;
  tokens_out?: number;
  output_summary?: string | null;
  error?: string | null;
  artifact_ids?: string[];
  metadata?: Record<string, unknown>;
}

interface Props {
  run: RunDetail;
  className?: string;
}

export function AgentTimeline({ run, className }: Props) {
  const steps = (run.state?.steps as StepRecord[]) ?? [];

  return (
    <Card className={cn("space-y-6", className)}>
      <div>
        <CardTitle>Agent Timeline</CardTitle>
        <CardSubtitle>
          Replay the thought process and execution trace for this run.
        </CardSubtitle>
      </div>

      {steps.length === 0 ? (
        <div className="py-12 text-center text-body-sm text-[color:var(--color-stone)]">
          No agent steps recorded yet.
        </div>
      ) : (
        <div className="relative border-l border-[color:var(--color-hairline)] ml-3 space-y-8 pb-4">
          {steps.map((step, idx) => {
            const isError = step.status === "error";
            const isRunning = step.status === "running";
            
            let durationStr = "";
            if (step.ended_at && step.started_at) {
              const start = new Date(step.started_at * 1000);
              const end = new Date(step.ended_at * 1000);
              durationStr = formatDistanceStrict(start, end);
            }

            return (
              <motion.div
                key={`${idx}-${step.step}`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: idx * 0.05 }}
                className="relative pl-6"
              >
                {/* Timeline Dot */}
                <div
                  className={cn(
                    "absolute -left-1.5 top-1 h-3 w-3 rounded-full border-2 border-[color:var(--color-surface)]",
                    isError
                      ? "bg-[color:var(--color-error-text)]"
                      : isRunning
                        ? "bg-[color:var(--color-info-text)] animate-pulse"
                        : "bg-[color:var(--color-success-text)]"
                  )}
                />

                <div className="flex flex-col gap-2">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h4 className="text-label text-[color:var(--color-ink)]">
                        {step.agent} <span className="text-[color:var(--color-stone)] font-normal px-1">via</span> {step.skill || step.step}
                      </h4>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge tone={isError ? "error" : isRunning ? "info" : "success"} className="text-micro">
                          {step.status}
                        </Badge>
                        {durationStr && (
                          <span className="text-micro text-[color:var(--color-stone)]">
                            {durationStr}
                          </span>
                        )}
                        {step.cost_usd && step.cost_usd > 0 && (
                          <span className="text-micro text-[color:var(--color-stone)]">
                            ${step.cost_usd.toFixed(4)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {step.output_summary && (
                    <div className="rounded-md bg-[color:var(--color-gray-1)] px-3 py-2 text-body-sm text-[color:var(--color-ink)] border border-[color:var(--color-hairline)]">
                      {step.output_summary}
                    </div>
                  )}

                  {step.error && (
                    <div className="rounded-md bg-[color:var(--color-error-bg)] px-3 py-2 text-body-sm text-[color:var(--color-error-text)]">
                      {step.error}
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
