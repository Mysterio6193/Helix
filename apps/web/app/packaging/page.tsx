"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { Boxes, Filter } from "lucide-react";

import { Badge, statusTone } from "@/components/ui/badge";
import { Card, CardSubtitle, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, type AssetItem, type Brand, type RunSummary } from "@/lib/api";
import { formatRelative, shortId } from "@/lib/utils";

const PACKAGING_PURPOSES = new Set([
  "packaging",
  "pizza_box",
  "pasta_bowl",
  "coffee_cup",
  "delivery_bag",
  "sticker",
  "label",
  "menu",
]);

export default function PackagingPage() {
  const [brandId, setBrandId] = useState("");
  const [query, setQuery] = useState("");

  const { data: brands } = useSWR<Brand[]>("brands", () => api.brands.list(), {
    revalidateOnFocus: false,
  });

  useEffect(() => {
    if (!brandId && brands && brands.length > 0) setBrandId(brands[0].id);
  }, [brandId, brands]);

  const { data: runs } = useSWR<RunSummary[]>(
    brandId ? ["packaging-runs", brandId] : null,
    () => api.runs.list({ brand_id: brandId, limit: 25 }),
    { revalidateOnFocus: false },
  );

  const packagingRuns = useMemo(
    () =>
      (runs ?? []).filter(
        (r) =>
          r.workflow === "packaging_suite" ||
          r.workflow === "menu_design" ||
          r.workflow.includes("packaging"),
      ),
    [runs],
  );

  const { data: assets, isLoading: assetsLoading } = useSWR<AssetItem[]>(
    brandId ? ["packaging-assets", brandId] : null,
    () => api.assets.list({ brand_id: brandId, kind: "image", limit: 200 }),
    { revalidateOnFocus: false },
  );

  const packagingAssets = useMemo(() => {
    const all = assets ?? [];
    const filtered = all.filter((a) => {
      const purpose = (a.metadata?.purpose as string | undefined) ?? "";
      return PACKAGING_PURPOSES.has(purpose) || purpose.includes("pack");
    });
    if (!query.trim()) return filtered;
    const q = query.trim().toLowerCase();
    return filtered.filter((a) =>
      JSON.stringify({ p: a.metadata, s: a.s3_key }).toLowerCase().includes(q),
    );
  }, [assets, query]);

  const purposeCounts = useMemo(() => {
    const map = new Map<string, number>();
    (assets ?? []).forEach((a) => {
      const p = (a.metadata?.purpose as string | undefined) ?? "other";
      if (PACKAGING_PURPOSES.has(p) || p.includes("pack")) {
        map.set(p, (map.get(p) ?? 0) + 1);
      }
    });
    return Array.from(map.entries()).sort((a, b) => b[1] - a[1]);
  }, [assets]);

  return (
    <div className="space-y-8">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">
          Deliver
        </div>
        <h1 className="text-display-lg text-[color:var(--color-charcoal)]">
          Packaging
        </h1>
        <p className="mt-2 max-w-[60ch] text-body-md text-[color:var(--color-slate)]">
          Per-SKU artwork — boxes, bowls, cups, sleeves, labels, sticker packs.
          Every artifact is traced back to the run that made it.
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
        <div className="flex min-w-[260px] flex-col gap-1.5">
          <label className="text-micro uppercase tracking-wider text-[color:var(--color-muted)]">
            Search
          </label>
          <Input
            placeholder="Filter by purpose, prompt, key…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <div className="ml-auto flex items-center gap-2 text-micro text-[color:var(--color-muted)]">
          <Filter className="size-3.5" />
          <span>{packagingAssets.length} packaging assets</span>
        </div>
      </Card>

      {purposeCounts.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {purposeCounts.map(([purpose, count]) => (
            <Badge key={purpose} tone="info">
              {purpose} · {count}
            </Badge>
          ))}
        </div>
      )}

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-[2fr_1fr]">
        <div>
          <h2 className="mb-4 text-heading-md">Artwork</h2>
          {!brandId && (
            <Card>
              <CardSubtitle>Pick a brand to see its packaging.</CardSubtitle>
            </Card>
          )}
          {brandId && assetsLoading && (
            <Card>
              <CardSubtitle>Loading packaging assets…</CardSubtitle>
            </Card>
          )}
          {brandId && !assetsLoading && packagingAssets.length === 0 && (
            <Card>
              <CardTitle>No artwork yet</CardTitle>
              <CardSubtitle>
                Launch a <code>packaging_suite</code> run from the brand page
                to generate per-SKU artwork.
              </CardSubtitle>
            </Card>
          )}
          {packagingAssets.length > 0 && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {packagingAssets.map((a) => (
                <PackagingTile key={a.id} asset={a} />
              ))}
            </div>
          )}
        </div>

        <aside>
          <h2 className="mb-4 text-heading-md">Recent runs</h2>
          <div className="space-y-3">
            {packagingRuns.length === 0 && brandId && (
              <Card>
                <CardSubtitle>
                  No packaging-related runs yet for this brand.
                </CardSubtitle>
              </Card>
            )}
            {packagingRuns.map((r) => (
              <Link key={r.id} href={`/workflows/${r.id}`}>
                <Card className="transition-shadow hover:shadow-[0_4px_12px_rgba(10,10,10,0.06)]">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-label-md font-medium">{r.workflow}</p>
                      <p className="text-micro mt-1 font-mono text-[color:var(--color-muted)]">
                        {shortId(r.id)}
                      </p>
                    </div>
                    <Badge tone={statusTone(r.status)}>{r.status}</Badge>
                  </div>
                  <p className="text-micro mt-3 text-[color:var(--color-muted)]">
                    {formatRelative(r.created_at)}
                  </p>
                </Card>
              </Link>
            ))}
          </div>
        </aside>
      </section>
    </div>
  );
}

function PackagingTile({ asset }: { asset: AssetItem }) {
  const meta = asset.metadata ?? {};
  const purpose = (meta.purpose as string | undefined) ?? asset.kind;
  const prompt = (meta.prompt as string | undefined) ?? "";

  return (
    <Card className="overflow-hidden p-0">
      <div className="flex aspect-[4/5] w-full items-center justify-center bg-[color:var(--color-surface)]">
        <Boxes className="size-10 text-[color:var(--color-muted)]" />
      </div>
      <div className="p-5">
        <div className="mb-2 flex flex-wrap items-center gap-1.5">
          <Badge tone="info">{purpose}</Badge>
          {asset.width && asset.height && (
            <Badge tone="neutral">
              {asset.width}×{asset.height}
            </Badge>
          )}
        </div>
        {prompt && (
          <p className="text-body-sm line-clamp-3 text-[color:var(--color-slate)]">
            {prompt}
          </p>
        )}
        <p className="text-micro mt-3 text-[color:var(--color-muted)]">
          {formatRelative(asset.created_at)}
          {asset.workflow_run_id && (
            <>
              {" · "}
              <Link
                href={`/workflows/${asset.workflow_run_id}`}
                className="underline-offset-2 hover:underline"
              >
                run {shortId(asset.workflow_run_id, 6)}
              </Link>
            </>
          )}
        </p>
      </div>
    </Card>
  );
}
