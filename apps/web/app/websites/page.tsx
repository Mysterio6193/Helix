"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { ExternalLink, Github, Globe, Rocket } from "lucide-react";

import { Badge, statusTone } from "@/components/ui/badge";
import { Card, CardSubtitle, CardTitle } from "@/components/ui/card";
import { api, type Brand, type RunSummary, type RunDetail } from "@/lib/api";
import { formatRelative, shortId } from "@/lib/utils";

interface SiteRow {
  run: RunSummary;
  detail: RunDetail | null;
}

export default function WebsitesPage() {
  const [brandId, setBrandId] = useState("");

  const { data: brands } = useSWR<Brand[]>("brands", () => api.brands.list(), {
    revalidateOnFocus: false,
  });

  useEffect(() => {
    if (!brandId && brands && brands.length > 0) setBrandId(brands[0].id);
  }, [brandId, brands]);

  const { data: runs, isLoading } = useSWR<RunSummary[]>(
    brandId ? ["site-runs", brandId] : null,
    () => api.runs.list({ brand_id: brandId, limit: 25 }),
    { revalidateOnFocus: false },
  );

  const siteRuns = useMemo(
    () =>
      (runs ?? []).filter(
        (r) =>
          r.workflow === "website_suite" ||
          r.workflow.includes("site") ||
          r.workflow.includes("website") ||
          r.workflow.includes("landing"),
      ),
    [runs],
  );

  const { data: details } = useSWR<SiteRow[]>(
    siteRuns.length > 0 ? ["site-details", siteRuns.map((r) => r.id).join(",")] : null,
    async () => {
      const out: SiteRow[] = [];
      for (const r of siteRuns) {
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

  const rows = details ?? siteRuns.map((r) => ({ run: r, detail: null }));

  return (
    <div className="space-y-8">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">Deliver</div>
        <h1 className="text-display-lg text-[color:var(--color-charcoal)]">
          Websites
        </h1>
        <p className="mt-2 max-w-[60ch] text-body-md text-[color:var(--color-slate)]">
          Generated landing-page scaffolds — section structure, copy
          frameworks, GitHub repos, and Vercel deploys. Each row is a single
          published site or in-flight build.
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
          {rows.length} site{rows.length === 1 ? "" : "s"}
        </div>
      </Card>

      {!brandId && (
        <Card>
          <CardSubtitle>Pick a brand to see its sites.</CardSubtitle>
        </Card>
      )}

      {brandId && isLoading && (
        <Card>
          <CardSubtitle>Loading site runs…</CardSubtitle>
        </Card>
      )}

      {brandId && !isLoading && rows.length === 0 && (
        <Card>
          <CardTitle>No sites yet</CardTitle>
          <CardSubtitle>
            Launch a <code>website_suite</code> run from the brand page to
            scaffold a landing page, push it to GitHub, and deploy to Vercel.
          </CardSubtitle>
        </Card>
      )}

      {rows.length > 0 && (
        <div className="space-y-4">
          {rows.map(({ run, detail }) => (
            <SiteCard key={run.id} run={run} detail={detail} />
          ))}
        </div>
      )}
    </div>
  );
}

function SiteCard({ run, detail }: { run: RunSummary; detail: RunDetail | null }) {
  const output = (detail?.output ?? {}) as Record<string, unknown>;
  const state = (detail?.state ?? {}) as Record<string, unknown>;
  const repo =
    (output.github_repo as { html_url?: string; name?: string } | undefined) ??
    (state.github_repo as { html_url?: string; name?: string } | undefined);
  const deploy =
    (output.deploy as { url?: string; status?: string } | undefined) ??
    (state.deploy as { url?: string; status?: string } | undefined);
  const sections =
    (output.sections as Array<{ slug?: string; framework?: string }> | undefined) ??
    (state.sections as Array<{ slug?: string; framework?: string }> | undefined) ??
    [];

  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <Badge tone={statusTone(run.status)}>{run.status}</Badge>
            <span className="text-micro font-mono text-[color:var(--color-muted)]">
              {shortId(run.id)}
            </span>
          </div>
          <CardTitle>{run.workflow}</CardTitle>
          <CardSubtitle>
            Started {formatRelative(run.created_at)}
            {run.completed_at &&
              ` · completed ${formatRelative(run.completed_at)}`}
          </CardSubtitle>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {repo?.html_url && (
            <a
              href={repo.html_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 rounded-full bg-[color:var(--color-surface)] px-3 py-1.5 text-label text-[color:var(--color-ink)] hover:bg-[color:var(--color-surface-elev)]"
            >
              <Github className="size-3.5" />
              <span>{repo.name ?? "repo"}</span>
              <ExternalLink className="size-3" />
            </a>
          )}
          {deploy?.url && (
            <a
              href={deploy.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 rounded-full bg-[color:var(--color-ink)] px-3 py-1.5 text-label text-[color:var(--color-canvas)] hover:opacity-95"
            >
              <Globe className="size-3.5" />
              <span>Visit site</span>
              <ExternalLink className="size-3" />
            </a>
          )}
          <Link
            href={`/workflows/${run.id}`}
            className="inline-flex items-center gap-1.5 rounded-full border border-[color:var(--color-ink)] px-3 py-1.5 text-label text-[color:var(--color-ink)] hover:bg-[color:var(--color-surface)]"
          >
            <Rocket className="size-3.5" />
            <span>Run detail</span>
          </Link>
        </div>
      </div>

      {sections.length > 0 && (
        <div className="mt-5 border-t border-[color:var(--color-hairline)] pt-4">
          <p className="text-micro mb-2 uppercase tracking-wider text-[color:var(--color-muted)]">
            Sections
          </p>
          <div className="flex flex-wrap gap-1.5">
            {sections.map((s, i) => (
              <Badge key={i} tone="neutral">
                {s.slug ?? `section ${i + 1}`}
                {s.framework ? ` · ${s.framework}` : ""}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {run.error && (
        <div className="mt-4 rounded-[12px] bg-[color:var(--color-error-bg)] px-4 py-3 text-label text-[color:var(--color-error-text)]">
          {run.error}
        </div>
      )}
    </Card>
  );
}
