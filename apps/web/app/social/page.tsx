"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { ImageIcon, Square, Smartphone } from "lucide-react";

import { Badge, statusTone } from "@/components/ui/badge";
import { Card, CardSubtitle, CardTitle } from "@/components/ui/card";
import { api, type AssetItem, type Brand, type RunSummary } from "@/lib/api";
import { formatRelative, shortId } from "@/lib/utils";

type SurfaceKey = "all" | "feed" | "story" | "ads";

const SURFACE_LABELS: Record<SurfaceKey, string> = {
  all: "All",
  feed: "Feed tiles",
  story: "Stories",
  ads: "Ads",
};

function classifySurface(asset: AssetItem): SurfaceKey {
  const purpose = ((asset.metadata?.purpose as string | undefined) ?? "").toLowerCase();
  if (purpose.includes("story")) return "story";
  if (purpose.includes("ad") || purpose.includes("carousel")) return "ads";
  if (
    purpose === "social" ||
    purpose === "feed" ||
    purpose.includes("instagram") ||
    purpose.includes("post")
  )
    return "feed";
  // Fallback by aspect ratio.
  if (asset.width && asset.height) {
    const ratio = asset.height / asset.width;
    if (ratio > 1.3) return "story";
    if (Math.abs(ratio - 1) < 0.1) return "feed";
  }
  return "feed";
}

export default function SocialPage() {
  const [brandId, setBrandId] = useState("");
  const [surface, setSurface] = useState<SurfaceKey>("all");

  const { data: brands } = useSWR<Brand[]>("brands", () => api.brands.list(), {
    revalidateOnFocus: false,
  });

  useEffect(() => {
    if (!brandId && brands && brands.length > 0) setBrandId(brands[0].id);
  }, [brandId, brands]);

  const { data: runs } = useSWR<RunSummary[]>(
    brandId ? ["social-runs", brandId] : null,
    () => api.runs.list({ brand_id: brandId, limit: 25 }),
    { revalidateOnFocus: false },
  );

  const socialRuns = useMemo(
    () =>
      (runs ?? []).filter(
        (r) =>
          r.workflow === "social_pack" ||
          r.workflow.includes("social") ||
          r.workflow.includes("instagram") ||
          r.workflow.includes("tiktok"),
      ),
    [runs],
  );

  const { data: assets } = useSWR<AssetItem[]>(
    brandId ? ["social-assets", brandId] : null,
    () => api.assets.list({ brand_id: brandId, kind: "image", limit: 200 }),
    { revalidateOnFocus: false },
  );

  const tagged = useMemo(
    () =>
      (assets ?? [])
        .map((a) => ({ ...a, _surface: classifySurface(a) }))
        .filter((a) => {
          const purpose = ((a.metadata?.purpose as string | undefined) ?? "").toLowerCase();
          return (
            purpose === "social" ||
            purpose === "feed" ||
            purpose === "story" ||
            purpose.includes("ad") ||
            purpose.includes("carousel") ||
            purpose.includes("instagram") ||
            purpose.includes("tiktok") ||
            purpose.includes("post")
          );
        }),
    [assets],
  );

  const filtered = useMemo(() => {
    if (surface === "all") return tagged;
    return tagged.filter((a) => a._surface === surface);
  }, [tagged, surface]);

  const surfaceCounts = useMemo(() => {
    const map: Record<SurfaceKey, number> = { all: tagged.length, feed: 0, story: 0, ads: 0 };
    tagged.forEach((a) => {
      map[a._surface] = (map[a._surface] ?? 0) + 1;
    });
    return map;
  }, [tagged]);

  return (
    <div className="space-y-8">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">Deliver</div>
        <h1 className="text-display-lg text-[color:var(--color-charcoal)]">Social</h1>
        <p className="mt-2 max-w-[60ch] text-body-md text-[color:var(--color-slate)]">
          Feed tiles, story templates, ad carousels, and captions — produced by{" "}
          <code>social_pack</code> and child skills, organized by surface area.
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

        <div className="flex flex-wrap gap-2">
          {(Object.keys(SURFACE_LABELS) as SurfaceKey[]).map((key) => (
            <button
              key={key}
              onClick={() => setSurface(key)}
              className={`rounded-full px-4 py-1.5 text-label transition-colors ${
                surface === key
                  ? "bg-[color:var(--color-ink)] text-[color:var(--color-canvas)]"
                  : "bg-[color:var(--color-surface)] text-[color:var(--color-ink)] hover:bg-[color:var(--color-surface-elev)]"
              }`}
            >
              {SURFACE_LABELS[key]} · {surfaceCounts[key] ?? 0}
            </button>
          ))}
        </div>
      </Card>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-[2fr_1fr]">
        <div>
          <h2 className="mb-4 text-heading-md">Social artifacts</h2>
          {!brandId && (
            <Card>
              <CardSubtitle>Pick a brand to see its social pack.</CardSubtitle>
            </Card>
          )}
          {brandId && filtered.length === 0 && (
            <Card>
              <CardTitle>No social assets yet</CardTitle>
              <CardSubtitle>
                Launch a <code>social_pack</code> run from the brand page to
                populate feed tiles, story templates, and ad creative.
              </CardSubtitle>
            </Card>
          )}
          {filtered.length > 0 && (
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4">
              {filtered.map((a) => (
                <SocialTile key={a.id} asset={a} surface={a._surface} />
              ))}
            </div>
          )}
        </div>

        <aside>
          <h2 className="mb-4 text-heading-md">Social runs</h2>
          <div className="space-y-3">
            {socialRuns.length === 0 && brandId && (
              <Card>
                <CardSubtitle>No social runs yet for this brand.</CardSubtitle>
              </Card>
            )}
            {socialRuns.map((r) => (
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

function SocialTile({
  asset,
  surface,
}: {
  asset: AssetItem;
  surface: SurfaceKey;
}) {
  const meta = asset.metadata ?? {};
  const variant = meta.variant as number | undefined;
  const Icon = surface === "story" ? Smartphone : surface === "ads" ? ImageIcon : Square;
  return (
    <Card className="overflow-hidden p-0">
      <div
        className={`flex w-full items-center justify-center bg-[color:var(--color-surface)] ${
          surface === "story" ? "aspect-[9/16]" : "aspect-square"
        }`}
      >
        <Icon className="size-8 text-[color:var(--color-muted)]" />
      </div>
      <div className="p-4">
        <div className="mb-2 flex items-center gap-1.5">
          <Badge tone="info">{surface}</Badge>
          {variant !== undefined && <Badge tone="neutral">v{variant}</Badge>}
        </div>
        <p className="text-micro text-[color:var(--color-muted)]">
          {formatRelative(asset.created_at)}
        </p>
      </div>
    </Card>
  );
}
