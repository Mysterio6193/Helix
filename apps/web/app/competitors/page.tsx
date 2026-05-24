"use client";

import { useState } from "react";
import useSWR from "swr";
import { motion } from "framer-motion";
import {
  Globe,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Target,
  Shield,
  Activity,
  Plus,
  Search,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

export default function CompetitorsPage() {
  const [newDomain, setNewDomain] = useState("");
  const { data, mutate, isLoading } = useSWR(
    "competitors",
    () => api.competitors.list(),
    { refreshInterval: 60000 }
  );

  async function trackCompetitor() {
    if (!newDomain) return;
    try {
      await api.competitors.track(newDomain);
      setNewDomain("");
      mutate();
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <div className="space-y-8 animate-fade-up">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">
          Intelligence
        </div>
        <h1 className="mt-2 text-display-lg font-bold leading-tight text-white">
          Competitor Intelligence
        </h1>
        <p className="mt-3 max-w-[72ch] text-body-md text-[color:var(--color-slate)]">
          Automated competitor monitoring, pricing tracking, campaign
          surveillance, and strategic battlecards.
        </p>
      </header>

      <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-[300px]">
            <label className="text-[10px] font-bold uppercase tracking-wider text-[color:var(--color-stone)]">
              Track New Competitor
            </label>
            <div className="mt-2 flex gap-2">
              <Input
                placeholder="competitor.com"
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && trackCompetitor()}
              />
              <button
                onClick={trackCompetitor}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-white px-4 text-xs font-bold text-black transition hover:bg-white/90"
              >
                <Plus className="size-4" />
                Track
              </button>
            </div>
          </div>
        </div>
      </Card>

      {data?.alerts && data.alerts.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-heading-md text-white flex items-center gap-2">
            <AlertTriangle className="size-5 text-amber-400" />
            Recent Alerts
          </h2>
          {data?.alerts?.map((alert: any, i: number) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Globe className="size-4 text-amber-400" />
                  <span className="text-sm font-bold text-amber-200">
                    {alert.competitor}
                  </span>
                  <Badge tone="warning">{alert.type}</Badge>
                </div>
                <span className="text-[10px] text-amber-200/50">
                  {alert.captured_at
                    ? new Date(alert.captured_at).toLocaleDateString()
                    : "Recently"}
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data?.competitors?.map((comp: any, i: number) => (
          <motion.div
            key={comp.domain}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl h-full">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex size-10 items-center justify-center rounded-lg bg-white/[0.06]">
                    <Globe className="size-5 text-[color:var(--color-slate)]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">
                      {comp.name || comp.domain}
                    </h3>
                    <p className="text-[10px] text-[color:var(--color-stone)]">
                      {comp.domain}
                    </p>
                  </div>
                </div>
                {comp.health_score && (
                  <Badge
                    tone={
                      comp.health_score > 70
                        ? "success"
                        : comp.health_score > 40
                        ? "warning"
                        : "error"
                    }
                  >
                    {comp.health_score}/100
                  </Badge>
                )}
              </div>

              <div className="mt-4 grid grid-cols-2 gap-2">
                <div className="rounded bg-black/20 p-2 text-center">
                  <Shield className="mx-auto size-4 text-[color:var(--color-slate)]" />
                  <p className="mt-1 text-[10px] text-[color:var(--color-stone)]">
                    Health
                  </p>
                </div>
                <div className="rounded bg-black/20 p-2 text-center">
                  <Target className="mx-auto size-4 text-[color:var(--color-slate)]" />
                  <p className="mt-1 text-[10px] text-[color:var(--color-stone)]">
                    Positioning
                  </p>
                </div>
              </div>

              <div className="mt-4 text-[10px] text-[color:var(--color-stone)]">
                Last scanned:{" "}
                {comp.last_scraped
                  ? new Date(comp.last_scraped).toLocaleDateString()
                  : "Never"}
              </div>
            </Card>
          </motion.div>
        ))}

        {isLoading && (
          <>
            {[1, 2, 3].map((i) => (
              <Card
                key={i}
                className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl animate-pulse"
              >
                <div className="h-20 bg-white/5 rounded" />
              </Card>
            ))}
          </>
        )}

        {!isLoading && !data?.competitors?.length && (
          <div className="col-span-full text-center py-12">
            <Search className="mx-auto size-8 text-[color:var(--color-stone)]" />
            <p className="mt-3 text-sm text-[color:var(--color-slate)]">
              No competitors tracked yet. Add domains above to start
              monitoring.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
