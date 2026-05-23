"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";

import { Badge, statusTone } from "@/components/ui/badge";
import { Card, CardSubtitle, CardTitle } from "@/components/ui/card";
import { useRunStream, type StreamEvent } from "@/lib/ws";
import { cn } from "@/lib/utils";

interface Props {
  runId: string;
  className?: string;
}

function eventLabel(e: StreamEvent): { headline: string; sub?: string } {
  const t = e.type ?? "event";
  const p = (e.payload ?? {}) as Record<string, unknown>;
  switch (t) {
    case "run.started":
      return { headline: "Run started", sub: String(p.workflow ?? "") };
    case "run.completed":
      return { headline: "Run completed", sub: `status=${String(p.status ?? "ok")}` };
    case "skill.started":
      return { headline: `Skill: ${String(p.skill ?? "?")}`, sub: String(p.agent ?? "") };
    case "skill.completed":
      return {
        headline: `Skill ok: ${String(p.skill ?? "?")}`,
        sub: typeof p.cost_usd === "number" ? `$${(p.cost_usd as number).toFixed(4)}` : undefined,
      };
    case "skill.failed":
      return { headline: `Skill failed: ${String(p.skill ?? "?")}`, sub: String(p.error ?? "") };
    case "asset.created":
      return { headline: "Asset", sub: String(p.purpose ?? p.kind ?? "") };
    default:
      return { headline: t };
  }
}

function eventTone(e: StreamEvent) {
  const t = e.type ?? "";
  if (t.endsWith(".failed")) return statusTone("failed");
  if (t.endsWith(".completed")) return statusTone("completed");
  if (t === "run.started" || t.endsWith(".started")) return statusTone("running");
  return statusTone("neutral");
}

export function RunStream({ runId, className }: Props) {
  const { events, status } = useRunStream(runId);

  const last = events[events.length - 1];
  const counts = useMemo(() => {
    const out = { total: events.length, ok: 0, fail: 0 };
    for (const e of events) {
      if ((e.type ?? "").endsWith(".completed")) out.ok += 1;
      if ((e.type ?? "").endsWith(".failed")) out.fail += 1;
    }
    return out;
  }, [events]);

  return (
    <Card className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <div>
          <CardTitle>Live stream</CardTitle>
          <CardSubtitle>
            Real-time events for this run.
          </CardSubtitle>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone={status === "open" ? "success" : status === "error" ? "error" : "info"}>
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                status === "open"
                  ? "bg-[color:var(--color-success-text)]"
                  : status === "error"
                    ? "bg-[color:var(--color-error-text)]"
                    : "bg-[color:var(--color-info-text)]",
              )}
            />
            {status}
          </Badge>
          <Badge tone="neutral" className="tabular">
            {counts.total} events
          </Badge>
          {counts.fail > 0 && (
            <Badge tone="error" className="tabular">
              {counts.fail} failed
            </Badge>
          )}
        </div>
      </div>

      <div className="max-h-[480px] overflow-y-auto rounded-[12px] border border-[color:var(--color-hairline)] bg-[color:var(--color-surface)]">
        {events.length === 0 ? (
          <div className="px-4 py-12 text-center text-body-sm text-[color:var(--color-stone)]">
            {status === "open" ? "Waiting for events…" : "Not connected yet."}
          </div>
        ) : (
          <ul className="divide-y divide-[color:var(--color-hairline)]">
            {events.map((e, idx) => {
              const label = eventLabel(e);
              const tone = eventTone(e);
              return (
                <motion.li
                  key={`${idx}-${e.type}-${e.ts ?? ""}`}
                  initial={{ opacity: 0, x: -4 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.18 }}
                  className="flex items-start justify-between gap-3 px-4 py-3"
                >
                  <div>
                    <div className="text-label text-[color:var(--color-ink)]">
                      {label.headline}
                    </div>
                    {label.sub && (
                      <div className="text-micro text-[color:var(--color-stone)]">
                        {label.sub}
                      </div>
                    )}
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Badge tone={tone} className="text-micro">
                      {(e.type ?? "").split(".").pop()}
                    </Badge>
                    {e.ts && (
                      <span className="text-micro text-[color:var(--color-stone)] tabular">
                        {new Date(e.ts).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                </motion.li>
              );
            })}
          </ul>
        )}
      </div>

      {last && last.type === "run.completed" && (
        <div className="rounded-[12px] bg-[color:var(--color-success-bg)] px-4 py-3 text-label text-[color:var(--color-success-text)]">
          Run completed. Outputs available below.
        </div>
      )}
    </Card>
  );
}
