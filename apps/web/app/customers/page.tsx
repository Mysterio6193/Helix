"use client";

import { useMemo } from "react";
import useSWR from "swr";
import { motion } from "framer-motion";
import {
  Crown,
  AlertTriangle,
  UserPlus,
  Heart,
  Users,
  TrendingUp,
  TrendingDown,
  Activity,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";

const SEGMENT_ICONS: Record<string, React.ComponentType<any>> = {
  champions: Crown,
  loyal: Heart,
  new: UserPlus,
  at_risk: AlertTriangle,
  hibernating: TrendingDown,
  needs_attention: Activity,
};

const SEGMENT_COLORS: Record<string, string> = {
  champions: "text-amber-400",
  loyal: "text-emerald-400",
  new: "text-sky-400",
  at_risk: "text-rose-400",
  hibernating: "text-[color:var(--color-stone)]",
  needs_attention: "text-amber-400",
};

export default function CustomersPage() {
  const { data: segments, isLoading } = useSWR(
    "customer-segments",
    () => api.customers.segments(),
    { refreshInterval: 60000 }
  );

  const totalCustomers = useMemo(() => {
    return (segments?.segments || []).reduce(
      (sum: number, s: any) => sum + (s.count || 0),
      0
    );
  }, [segments]);

  return (
    <div className="space-y-8 animate-fade-up">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">
          Intelligence
        </div>
        <h1 className="mt-2 text-display-lg font-bold leading-tight text-white">
          Customer Intelligence
        </h1>
        <p className="mt-3 max-w-[72ch] text-body-md text-[color:var(--color-slate)]">
          Segment analysis, cohort retention, churn prediction, and
          behavioral insights from all connected commerce platforms.
        </p>
      </header>

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/70 p-4 shadow-xl">
          <div className="flex items-center justify-between gap-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[color:var(--color-stone)]">
              Total Customers
            </span>
            <Users className="size-4 text-sky-400" />
          </div>
          <div className="mt-3 text-2xl font-bold leading-none text-white">
            {isLoading ? "..." : totalCustomers.toLocaleString()}
          </div>
        </Card>
        <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/70 p-4 shadow-xl">
          <div className="flex items-center justify-between gap-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[color:var(--color-stone)]">
              Avg LTV
            </span>
            <TrendingUp className="size-4 text-emerald-400" />
          </div>
          <div className="mt-3 text-2xl font-bold leading-none text-white">
            {isLoading
              ? "..."
              : `$${(
                  (segments?.segments || []).reduce(
                    (sum: number, s: any) =>
                      sum + (s.avg_ltv || 0) * (s.count || 0),
                    0
                  ) / Math.max(totalCustomers, 1)
                ).toFixed(2)}`}
          </div>
        </Card>
        <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/70 p-4 shadow-xl">
          <div className="flex items-center justify-between gap-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[color:var(--color-stone)]">
              At Risk
            </span>
            <AlertTriangle className="size-4 text-rose-400" />
          </div>
          <div className="mt-3 text-2xl font-bold leading-none text-white">
            {isLoading
              ? "..."
              : (
                  segments?.segments?.find((s: any) => s.key === "at_risk")
                    ?.count || 0
                ).toLocaleString()}
          </div>
        </Card>
        <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/70 p-4 shadow-xl">
          <div className="flex items-center justify-between gap-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[color:var(--color-stone)]">
              Churn Rate
            </span>
            <TrendingDown className="size-4 text-amber-400" />
          </div>
          <div className="mt-3 text-2xl font-bold leading-none text-white">
            {isLoading
              ? "..."
              : `${(
                  (segments?.segments || []).reduce(
                    (sum: number, s: any) =>
                      sum + (s.churn_rate || 0) * (s.count || 0),
                    0
                  ) / Math.max(totalCustomers, 1) *
                  100
                ).toFixed(1)}%`}
          </div>
        </Card>
      </section>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
          <div className="mb-5">
            <div className="text-eyebrow text-[color:var(--color-stone)]">
              Segments
            </div>
            <h2 className="mt-1 text-heading-lg text-white">
              Customer Segments
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {segments?.segments?.map((segment: any, i: number) => {
              const Icon = SEGMENT_ICONS[segment.key] || Users;
              const colorClass = SEGMENT_COLORS[segment.key] || "text-white";
              const percentage =
                totalCustomers > 0
                  ? ((segment.count || 0) / totalCustomers) * 100
                  : 0;

              return (
                <motion.div
                  key={segment.key}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="rounded-lg border border-white/[0.06] bg-black/20 p-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span
                        className={`inline-flex size-8 items-center justify-center rounded-lg bg-white/[0.06] ${colorClass}`}
                      >
                        <Icon className="size-4" />
                      </span>
                      <div>
                        <h3 className="text-sm font-bold text-white capitalize">
                          {segment.name}
                        </h3>
                        <p className="text-[10px] text-[color:var(--color-slate)]">
                          {segment.count?.toLocaleString()} customers
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-white">
                        {percentage.toFixed(1)}%
                      </div>
                      {segment.avg_ltv && (
                        <div className="text-[10px] text-[color:var(--color-stone)]">
                          LTV ${segment.avg_ltv}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="mt-3 h-1.5 rounded-full bg-white/5 overflow-hidden">
                    <motion.div
                      className={`h-full rounded-full ${
                        segment.key === "at_risk"
                          ? "bg-rose-500/60"
                          : segment.key === "champions"
                          ? "bg-amber-500/60"
                          : "bg-emerald-500/60"
                      }`}
                      initial={{ width: 0 }}
                      animate={{ width: `${percentage}%` }}
                      transition={{ delay: i * 0.05, duration: 0.5 }}
                    />
                  </div>
                </motion.div>
              );
            })}

            {!segments?.segments?.length && (
              <div className="text-center py-8">
                <Users className="mx-auto size-8 text-[color:var(--color-stone)]" />
                <p className="mt-3 text-sm text-[color:var(--color-slate)]">
                  No customer segments yet. Connect Shopify or Stripe to start
                  segmenting.
                </p>
              </div>
            )}
          </div>
        </Card>

        <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
          <div className="mb-5">
            <div className="text-eyebrow text-[color:var(--color-stone)]">
              Cohorts
            </div>
            <h2 className="mt-1 text-heading-lg text-white">
              Retention Analysis
            </h2>
          </div>

          {Object.keys(segments?.cohorts || {}).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(segments?.cohorts || {}).map(
                ([month, data]: [string, any]) => (
                  <div key={month}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-white">
                        {month}
                      </span>
                      <span className="text-[10px] text-[color:var(--color-stone)]">
                        {data.size} customers
                      </span>
                    </div>
                    <div className="flex gap-1">
                      {Object.entries(data.retention).map(
                        ([period, pct]: [string, any]) => (
                          <div
                            key={period}
                            className="flex-1 rounded bg-white/5 p-1 text-center"
                          >
                            <div
                              className="text-[10px] font-bold"
                              style={{
                                color:
                                  pct > 50
                                    ? "#34d399"
                                    : pct > 25
                                    ? "#fbbf24"
                                    : "#fb7185",
                              }}
                            >
                              {pct}%
                            </div>
                            <div className="text-[8px] text-[color:var(--color-stone)]">
                              {period}
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <Activity className="mx-auto size-8 text-[color:var(--color-stone)]" />
              <p className="mt-3 text-sm text-[color:var(--color-slate)]">
                No cohort data available. Requires order history from connected
                platforms.
              </p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
