"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { Calendar, Mail, Megaphone, Target } from "lucide-react";

import { Badge, statusTone } from "@/components/ui/badge";
import { Card, CardSubtitle, CardTitle, ProductCard } from "@/components/ui/card";
import { api, type Brand, type RunDetail, type RunSummary } from "@/lib/api";
import { formatRelative, shortId } from "@/lib/utils";

interface CampaignRow {
  run: RunSummary;
  detail: RunDetail | null;
}

const HERO_GRADIENTS = ["coral", "magenta", "blue", "purple", "amber"] as const;
type Gradient = (typeof HERO_GRADIENTS)[number];

export default function CampaignsPage() {
  const [brandId, setBrandId] = useState("");

  const { data: brands } = useSWR<Brand[]>("brands", () => api.brands.list(), {
    revalidateOnFocus: false,
  });

  useEffect(() => {
    if (!brandId && brands && brands.length > 0) setBrandId(brands[0].id);
  }, [brandId, brands]);

  const { data: runs, isLoading } = useSWR<RunSummary[]>(
    brandId ? ["campaign-runs", brandId] : null,
    () => api.runs.list({ brand_id: brandId, limit: 25 }),
    { revalidateOnFocus: false },
  );

  const campaignRuns = useMemo(
    () =>
      (runs ?? []).filter(
        (r) =>
          r.workflow === "launch_campaign" ||
          r.workflow.includes("campaign") ||
          r.workflow.includes("launch"),
      ),
    [runs],
  );

  const { data: rows } = useSWR<CampaignRow[]>(
    campaignRuns.length > 0
      ? ["campaign-details", campaignRuns.map((r) => r.id).join(",")]
      : null,
    async () => {
      const out: CampaignRow[] = [];
      for (const r of campaignRuns) {
        try {
          const detail = await api.runs.get(r.id);
          out.push({ run: r, detail });
        } catch {
          out.push({ run: r, detail: null });
        }
      }
      return out;
    },
    { revalidateOnFocus: false },
  );

  const display = rows ?? campaignRuns.map((r) => ({ run: r, detail: null }));

  return (
    <div className="space-y-8">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">
          Deliver
        </div>
        <h1 className="text-display-lg text-[color:var(--color-charcoal)]">
          Campaigns
        </h1>
        <p className="mt-2 max-w-[60ch] text-body-md text-[color:var(--color-slate)]">
          End-to-end launch campaigns — strategy, calendar, email drafts, paid
          creative, and a day-of-launch checklist, threaded through a single
          orchestrated run.
        </p>
      </header>

      <Card className="flex flex-wrap items-end gap-4">
        <div className="flex flex-col gap-1.5">
          <label className="text-micro uppercase tracking-wider text-[color:var(--color-muted)]">
            Brand
          </label>
          <select
            value={brandId}
            onChange={(e) => setBrandId(e.target.value)}
            className="rounded-[8px] border border-[color:var(--color-hairline)] bg-[color:var(--color-canvas)] px-3 py-1.5 text-body-sm"
          >
            {!brandId && <option value="">— select a brand —</option>}
            {(brands ?? []).map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </div>
        <div className="ml-auto text-micro text-[color:var(--color-muted)]">
          {display.length} campaign run{display.length === 1 ? "" : "s"}
        </div>
      </Card>

      {!brandId && (
        <Card>
          <CardSubtitle>Pick a brand to see its campaigns.</CardSubtitle>
        </Card>
      )}

      {brandId && isLoading && (
        <Card>
          <CardSubtitle>Loading campaign runs…</CardSubtitle>
        </Card>
      )}

      {brandId && !isLoading && display.length === 0 && (
        <Card>
          <CardTitle>No campaigns yet</CardTitle>
          <CardSubtitle>
            Launch an <code>orchestrate_launch_campaign</code> or{" "}
            <code>launch_campaign</code> run from the brand page to scaffold a
            full launch.
          </CardSubtitle>
        </Card>
      )}

      {display.length > 0 && (
        <div className="space-y-6">
          {display.map((row, idx) => (
            <CampaignCard
              key={row.run.id}
              row={row}
              gradient={HERO_GRADIENTS[idx % HERO_GRADIENTS.length]}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function CampaignCard({ row, gradient }: { row: CampaignRow; gradient: Gradient }) {
  const { run, detail } = row;
  const output = (detail?.output ?? {}) as Record<string, unknown>;
  const state = (detail?.state ?? {}) as Record<string, unknown>;

  const headline =
    ((output.headline as string | undefined) ??
      (state.headline as string | undefined) ??
      (detail?.inputs?.headline as string | undefined)) ||
    `${run.workflow} · ${shortId(run.id, 6)}`;

  const calendar =
    (output.calendar as Array<{ day?: string; theme?: string }> | undefined) ??
    (state.calendar as Array<{ day?: string; theme?: string }> | undefined) ??
    [];
  const emails =
    (output.emails as Array<{ step?: number; subject?: string }> | undefined) ??
    (state.emails as Array<{ step?: number; subject?: string }> | undefined) ??
    [];
  const ads =
    (output.ads as Array<{ surface?: string; headline?: string }> | undefined) ??
    (state.ads as Array<{ surface?: string; headline?: string }> | undefined) ??
    [];
  const checklist =
    (output.day_of_checklist as string[] | undefined) ??
    (state.day_of_checklist as string[] | undefined) ??
    [];

  return (
    <article className="space-y-4">
      <ProductCard gradient={gradient}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-eyebrow opacity-70">{run.workflow}</div>
            <h2 className="text-display-md mt-1">{headline}</h2>
            <p className="mt-2 text-body-md opacity-80">
              Started {formatRelative(run.created_at)} ·{" "}
              {run.completed_at
                ? `wrapped ${formatRelative(run.completed_at)}`
                : "in flight"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge tone={statusTone(run.status)}>{run.status}</Badge>
            <Link
              href={`/workflows/${run.id}`}
              className="rounded-full bg-[color:var(--color-ink)] px-4 py-1.5 text-label text-[color:var(--color-canvas)] hover:opacity-95"
            >
              Open run
            </Link>
          </div>
        </div>
      </ProductCard>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <CampaignPanel
          icon={<Calendar className="size-4" />}
          title="Calendar"
          count={calendar.length}
          empty="No calendar yet"
        >
          {calendar.slice(0, 5).map((c, i) => (
            <li key={i} className="text-body-sm text-[color:var(--color-slate)]">
              <span className="font-mono text-[color:var(--color-muted)]">
                {c.day ?? `D${i + 1}`}
              </span>{" "}
              {c.theme ?? "—"}
            </li>
          ))}
        </CampaignPanel>

        <CampaignPanel
          icon={<Mail className="size-4" />}
          title="Email drafts"
          count={emails.length}
          empty="No emails yet"
        >
          {emails.slice(0, 5).map((e, i) => (
            <li key={i} className="text-body-sm text-[color:var(--color-slate)]">
              <span className="font-mono text-[color:var(--color-muted)]">
                {e.step != null ? `#${e.step}` : `#${i + 1}`}
              </span>{" "}
              {e.subject ?? "—"}
            </li>
          ))}
        </CampaignPanel>

        <CampaignPanel
          icon={<Megaphone className="size-4" />}
          title="Paid creative"
          count={ads.length}
          empty="No ads yet"
        >
          {ads.slice(0, 5).map((a, i) => (
            <li key={i} className="text-body-sm text-[color:var(--color-slate)]">
              <span className="font-mono text-[color:var(--color-muted)]">
                {a.surface ?? `surface ${i + 1}`}
              </span>{" "}
              {a.headline ?? "—"}
            </li>
          ))}
        </CampaignPanel>

        <CampaignPanel
          icon={<Target className="size-4" />}
          title="Day-of checklist"
          count={checklist.length}
          empty="No checklist yet"
        >
          {checklist.slice(0, 5).map((c, i) => (
            <li key={i} className="text-body-sm text-[color:var(--color-slate)]">
              {c}
            </li>
          ))}
        </CampaignPanel>
      </div>

      {run.error && (
        <div className="rounded-[12px] bg-[color:var(--color-error-bg)] px-4 py-3 text-label text-[color:var(--color-error-text)]">
          {run.error}
        </div>
      )}
    </article>
  );
}

function CampaignPanel({
  icon,
  title,
  count,
  empty,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  count: number;
  empty: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <div className="mb-3 flex items-center gap-2 text-[color:var(--color-ink)]">
        {icon}
        <p className="text-label-md font-medium">{title}</p>
        <Badge tone="neutral" className="ml-auto">
          {count}
        </Badge>
      </div>
      {count === 0 ? (
        <p className="text-body-sm text-[color:var(--color-muted)]">{empty}</p>
      ) : (
        <ul className="space-y-1.5">{children}</ul>
      )}
    </Card>
  );
}
