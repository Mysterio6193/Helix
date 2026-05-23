"use client";

import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import {
  Activity,
  Image as ImageIcon,
  Palette,
  Sparkles,
  Type as TypeIcon,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ForceGraph } from "@/components/memory/force-graph";
import {
  api,
  type Brand,
  type BrandMemory,
  type TimelineEvent,
} from "@/lib/api";

export default function MemoryPage() {
  const [brandId, setBrandId] = useState<string>("");

  const { data: brands } = useSWR<Brand[]>("brands", () => api.brands.list(), {
    revalidateOnFocus: false,
  });

  // default to first brand once loaded
  useEffect(() => {
    if (!brandId && brands && brands.length > 0) setBrandId(brands[0].id);
  }, [brandId, brands]);

  const { data: memory, isLoading } = useSWR<BrandMemory>(
    brandId ? ["memory", brandId] : null,
    () => api.memory.brand(brandId),
    { revalidateOnFocus: false },
  );
  const { data: timeline } = useSWR<TimelineEvent[]>(
    brandId ? ["memory-timeline", brandId] : null,
    () => api.memory.timeline(brandId, 100),
    { revalidateOnFocus: false },
  );

  return (
    <div className="px-12 py-10">
      <header className="mb-8">
        <p className="text-micro uppercase tracking-wider text-muted">System</p>
        <h1 className="text-display-md mt-1">Memory</h1>
        <p className="text-body mt-3 max-w-2xl text-slate">
          Closed-loop brain — the foundation context every skill reads first,
          plus a unified timeline of runs, assets, and learnings scoped to one
          brand.
        </p>
      </header>

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <label className="text-label-md">Brand</label>
        <select
          value={brandId}
          onChange={(e) => setBrandId(e.target.value)}
          className="rounded-[8px] border border-hairline bg-canvas px-3 py-1.5 text-body-sm"
        >
          {!brandId && <option value="">— select a brand —</option>}
          {(brands ?? []).map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </select>
      </div>

      {!brandId && (
        <Card className="p-6">
          <p className="text-body-sm text-muted">
            Pick a brand to view its memory.
          </p>
        </Card>
      )}

      {isLoading && (
        <p className="text-body-sm text-muted">Loading brand memory…</p>
      )}

      {memory && (
        <div className="space-y-6">
          <ForceGraph brandId={brandId} className="w-full" />
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.4fr_1fr]">
            <div className="flex flex-col gap-5">
              <CountsCard memory={memory} />
              <ContextCard memory={memory} />
              <PaletteCard memory={memory} />
              <TypographyCard memory={memory} />
              <RecentAssetsCard memory={memory} />
            </div>
            <TimelineCard timeline={timeline ?? []} />
          </div>
        </div>
      )}
    </div>
  );
}

function CountsCard({ memory }: { memory: BrandMemory }) {
  const counts = memory.counts;
  return (
    <div className="grid grid-cols-4 gap-3">
      <Stat label="Runs" value={counts.runs} />
      <Stat label="Assets" value={counts.assets} />
      <Stat label="Brand assets" value={counts.brand_assets} />
      <Stat label="Learnings" value={counts.learnings} />
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <Card className="p-4">
      <p className="text-micro uppercase tracking-wider text-muted">{label}</p>
      <p className="text-display-sm mt-1">{value}</p>
    </Card>
  );
}

function ContextCard({ memory }: { memory: BrandMemory }) {
  const ctx = memory.context as Record<string, unknown>;
  const name = (ctx.name as string) ?? "Untitled brand";
  const tagline = (ctx.tagline as string) ?? null;
  const positioning = (ctx.positioning as string) ?? null;
  const archetype = (ctx.archetype as string) ?? null;
  const designSchool = (ctx.design_school as string) ?? null;
  const voice = (ctx.voice_attributes as string[] | undefined) ?? [];

  return (
    <Card className="p-6">
      <div className="mb-3 flex items-center gap-2">
        <Sparkles className="size-4 text-muted" />
        <p className="text-label-md">Foundation context</p>
      </div>
      <h2 className="text-heading-md">{name}</h2>
      {tagline && <p className="text-body mt-1 italic text-slate">"{tagline}"</p>}
      {positioning && (
        <p className="text-body-sm mt-3 text-slate">{positioning}</p>
      )}
      <div className="mt-4 flex flex-wrap gap-1.5">
        {archetype && <Badge tone="info">{archetype}</Badge>}
        {designSchool && <Badge tone="info">school · {designSchool}</Badge>}
        {voice.slice(0, 6).map((v) => (
          <Badge key={v} tone="neutral">
            {v}
          </Badge>
        ))}
      </div>
    </Card>
  );
}

function PaletteCard({ memory }: { memory: BrandMemory }) {
  const palette = memory.context.palette as Record<string, unknown> | undefined;
  if (!palette || Object.keys(palette).length === 0) return null;
  const swatches: Array<[string, string]> = [];
  for (const [k, v] of Object.entries(palette)) {
    if (typeof v === "string" && v.startsWith("#")) swatches.push([k, v]);
  }
  if (swatches.length === 0) return null;
  return (
    <Card className="p-6">
      <div className="mb-3 flex items-center gap-2">
        <Palette className="size-4 text-muted" />
        <p className="text-label-md">Palette</p>
      </div>
      <div className="grid grid-cols-3 gap-3 sm:grid-cols-5">
        {swatches.map(([name, hex]) => (
          <div key={name} className="flex flex-col gap-1">
            <div
              className="aspect-square rounded-[8px] border border-hairline"
              style={{ backgroundColor: hex }}
            />
            <p className="text-micro font-mono text-slate">{name}</p>
            <p className="text-micro font-mono text-muted">{hex}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function TypographyCard({ memory }: { memory: BrandMemory }) {
  const typo = memory.context.typography as Record<string, unknown> | undefined;
  if (!typo || Object.keys(typo).length === 0) return null;
  return (
    <Card className="p-6">
      <div className="mb-3 flex items-center gap-2">
        <TypeIcon className="size-4 text-muted" />
        <p className="text-label-md">Typography</p>
      </div>
      <dl className="grid grid-cols-2 gap-3">
        {Object.entries(typo).map(([k, v]) => (
          <div key={k}>
            <dt className="text-micro uppercase tracking-wider text-muted">
              {k}
            </dt>
            <dd className="text-body-sm font-mono">
              {typeof v === "string" ? v : JSON.stringify(v)}
            </dd>
          </div>
        ))}
      </dl>
    </Card>
  );
}

function RecentAssetsCard({ memory }: { memory: BrandMemory }) {
  const recent = (memory.context.recent_assets ??
    []) as Array<Record<string, unknown>>;
  if (recent.length === 0) return null;
  return (
    <Card className="p-6">
      <div className="mb-3 flex items-center gap-2">
        <ImageIcon className="size-4 text-muted" />
        <p className="text-label-md">Recent assets</p>
      </div>
      <ul className="flex flex-col gap-2">
        {recent.slice(0, 8).map((a) => (
          <li
            key={String(a.id)}
            className="flex items-center justify-between gap-3 text-body-sm"
          >
            <span className="font-mono text-charcoal">{String(a.kind)}</span>
            <span className="truncate text-muted">{String(a.s3_key)}</span>
          </li>
        ))}
      </ul>
      {memory.asset_kinds.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-1.5">
          {memory.asset_kinds.map((k) => (
            <Badge key={k.kind} tone="neutral">
              {k.kind} · {k.count}
            </Badge>
          ))}
        </div>
      )}
    </Card>
  );
}

function TimelineCard({ timeline }: { timeline: TimelineEvent[] }) {
  const [filter, setFilter] = useState<"all" | "run" | "asset" | "learning">(
    "all",
  );
  const filtered = useMemo(
    () => (filter === "all" ? timeline : timeline.filter((e) => e.type === filter)),
    [timeline, filter],
  );

  return (
    <Card className="sticky top-6 flex h-fit flex-col gap-3 p-6">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Activity className="size-4 text-muted" />
          <p className="text-label-md">Timeline</p>
        </div>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as typeof filter)}
          className="rounded-[6px] border border-hairline bg-canvas px-2 py-1 text-micro"
        >
          <option value="all">all events</option>
          <option value="run">runs</option>
          <option value="asset">assets</option>
          <option value="learning">learnings</option>
        </select>
      </div>
      {filtered.length === 0 ? (
        <p className="text-body-sm text-muted">No events yet.</p>
      ) : (
        <ol className="flex flex-col gap-0">
          {filtered.map((e, i) => (
            <li
              key={`${e.type}-${e.id}`}
              className={`flex items-start gap-3 py-2.5 ${
                i < filtered.length - 1 ? "border-b border-hairline" : ""
              }`}
            >
              <div className="mt-1 size-1.5 rounded-full bg-muted" />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <Badge tone={toneFor(e)}>{e.type}</Badge>
                  {e.status && (
                    <span className="text-micro text-muted">{e.status}</span>
                  )}
                  {e.kind && (
                    <span className="text-micro font-mono text-muted">
                      {e.kind}
                    </span>
                  )}
                </div>
                <p className="text-body-sm mt-1 line-clamp-2 text-charcoal">
                  {e.title}
                </p>
                <p className="text-micro mt-0.5 text-muted">
                  {e.at ? new Date(e.at).toLocaleString() : "—"}
                </p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </Card>
  );
}

function toneFor(e: TimelineEvent): "info" | "success" | "warning" | "neutral" | "error" {
  if (e.type === "run") {
    if (e.status === "completed") return "success";
    if (e.status === "failed") return "error";
    return "info";
  }
  if (e.type === "asset") return "neutral";
  return "info";
}
