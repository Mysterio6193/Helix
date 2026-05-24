"use client";

import { useMemo } from "react";
import useSWR from "swr";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  DollarSign,
  Target,
  Users,
  BarChart3,
  Activity,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";

function MetricCard({
  label,
  value,
  delta,
  tone,
  icon: Icon,
}: {
  label: string;
  value: string;
  delta?: string;
  tone: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  const toneClass =
    tone === "success"
      ? "text-emerald-400"
      : tone === "warning"
      ? "text-amber-400"
      : tone === "error"
      ? "text-rose-400"
      : "text-sky-400";

  return (
    <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/70 p-4 shadow-xl">
      <div className="flex items-center justify-between gap-3">
        <span className="text-[10px] font-bold uppercase tracking-wider text-[color:var(--color-stone)]">
          {label}
        </span>
        <Icon className={`size-4 ${toneClass}`} />
      </div>
      <div className="mt-3 text-2xl font-bold leading-none text-white">{value}</div>
      {delta && (
        <div className={`mt-2 text-[10px] font-semibold ${toneClass}`}>{delta}</div>
      )}
    </Card>
  );
}

export default function RevenuePage() {
  const { data: overview, isLoading } = useSWR(
    "revenue-overview",
    () => api.revenue.overview(),
    { refreshInterval: 30000 }
  );

  const { data: metrics } = useSWR(
    "revenue-metrics",
    () => api.revenue.metrics({ days: 30 }),
    { refreshInterval: 30000 }
  );

  const revenueData = useMemo(() => {
    if (!metrics) return [];
    return metrics
      .filter((m: any) => m.metric_type === "revenue")
      .sort((a: any, b: any) =>
        new Date(a.captured_at).getTime() - new Date(b.captured_at).getTime()
      );
  }, [metrics]);

  return (
    <div className="space-y-8 animate-fade-up">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">
          Intelligence
        </div>
        <h1 className="mt-2 text-display-lg font-bold leading-tight text-white">
          Revenue Intelligence
        </h1>
        <p className="mt-3 max-w-[72ch] text-body-md text-[color:var(--color-slate)]">
          Real-time revenue analytics, anomaly detection, and AI-powered
          optimization recommendations across all connected platforms.
        </p>
      </header>

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Daily Revenue"
          value={isLoading ? "..." : `$${overview?.current_revenue?.daily?.toFixed(2) ?? "0.00"}`}
          delta={overview?.current_revenue?.yoy_change ? `${overview.current_revenue.yoy_change}% YoY` : undefined}
          tone="success"
          icon={DollarSign}
        />
        <MetricCard
          label="ROAS"
          value={isLoading ? "..." : `${overview?.roas?.current?.toFixed(2) ?? "0.00"}x`}
          delta={`Target: ${overview?.roas?.target ?? 2.5}x`}
          tone={(overview?.roas?.current ?? 0) >= 2.5 ? "success" : "warning"}
          icon={Target}
        />
        <MetricCard
          label="CAC"
          value={isLoading ? "..." : `$${overview?.cac?.current?.toFixed(2) ?? "0.00"}`}
          delta={overview?.cac?.trend}
          tone="info"
          icon={Users}
        />
        <MetricCard
          label="LTV"
          value={isLoading ? "..." : `$${overview?.ltv?.current?.toFixed(2) ?? "0.00"}`}
          delta={`12m pred: $${overview?.ltv?.predicted_12m?.toFixed(2) ?? "0.00"}`}
          tone="success"
          icon={BarChart3}
        />
      </section>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_0.4fr]">
        <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <div className="text-eyebrow text-[color:var(--color-stone)]">
                Time Series
              </div>
              <h2 className="mt-1 text-heading-lg text-white">Revenue Trend</h2>
            </div>
            <Badge tone="info">30 days</Badge>
          </div>

          {revenueData.length > 0 ? (
            <div className="space-y-2">
              {revenueData.slice(-10).map((point: any, i: number) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-center gap-3"
                >
                  <span className="text-[10px] text-[color:var(--color-stone)] w-20">
                    {new Date(point.captured_at).toLocaleDateString()}
                  </span>
                  <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                    <motion.div
                      className="h-full bg-emerald-500/60 rounded-full"
                      initial={{ width: 0 }}
                      animate={{
                        width: `${Math.min(100, (point.value / Math.max(...revenueData.map((d: any) => d.value))) * 100)}%`,
                      }}
                      transition={{ delay: i * 0.05, duration: 0.5 }}
                    />
                  </div>
                  <span className="text-xs text-white w-16 text-right">
                    ${point.value.toFixed(0)}
                  </span>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Activity className="mx-auto size-8 text-[color:var(--color-stone)]" />
              <p className="mt-3 text-sm text-[color:var(--color-slate)]">
                No revenue data yet. Connect Shopify, Stripe, or Meta Ads to
                start tracking.
              </p>
            </div>
          )}
        </Card>

        <div className="space-y-4">
          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-4">
              <div className="text-eyebrow text-[color:var(--color-stone)]">
                Alerts
              </div>
              <h2 className="mt-1 text-heading-lg text-white">Anomalies</h2>
            </div>
            <div className="space-y-3">
              {overview?.anomalies && overview.anomalies.length > 0 ? (
                overview.anomalies.map((anomaly: any, i: number) => (
                  <div
                    key={i}
                    className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3"
                  >
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="size-4 text-amber-400" />
                      <span className="text-xs font-bold text-amber-200">
                        {anomaly.metric} anomaly
                      </span>
                    </div>
                    <p className="mt-1 text-[10px] text-amber-200/70">
                      {anomaly.date} — Value: {anomaly.value}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-[color:var(--color-slate)]">
                  No anomalies detected. Helix monitors all metrics
                  continuously.
                </p>
              )}
            </div>
          </Card>

          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-4">
              <div className="text-eyebrow text-[color:var(--color-stone)]">
                Forecast
              </div>
              <h2 className="mt-1 text-heading-lg text-white">Prediction</h2>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-[color:var(--color-slate)]">
                  Next 30 days
                </span>
                <Badge tone="info">
                  {Math.round((overview?.predictions?.confidence ?? 0) * 100)}%
                  confidence
                </Badge>
              </div>
              {overview?.predictions?.next_30_days && overview.predictions.next_30_days.length > 0 ? (
                <div className="text-2xl font-bold text-white">
                  $
                  {overview?.predictions?.next_30_days
                    .reduce((a: number, b: number) => a + b, 0)
                    .toFixed(2)}
                </div>
              ) : (
                <p className="text-sm text-[color:var(--color-slate)]">
                  Insufficient data for prediction.
                </p>
              )}
            </div>
          </Card>
        </div>
      </div>

      <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
        <div className="mb-5">
          <div className="text-eyebrow text-[color:var(--color-stone)]">
            Breakdown
          </div>
          <h2 className="mt-1 text-heading-lg text-white">By Channel</h2>
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {overview?.by_channel?.map((channel: any) => (
            <div
              key={channel.platform}
              className="rounded-lg border border-white/[0.06] bg-black/20 p-4"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white capitalize">
                  {channel.platform.replace("_", " ")}
                </h3>
                <Badge
                  tone={channel.roas >= 2.5 ? "success" : "warning"}
                >
                  {channel.roas}x ROAS
                </Badge>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-center">
                <div>
                  <div className="text-lg font-bold text-white">
                    ${channel.spend}
                  </div>
                  <div className="text-[10px] text-[color:var(--color-stone)]">
                    Spend
                  </div>
                </div>
                <div>
                  <div className="text-lg font-bold text-emerald-400">
                    ${channel.revenue}
                  </div>
                  <div className="text-[10px] text-[color:var(--color-stone)]">
                    Revenue
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
