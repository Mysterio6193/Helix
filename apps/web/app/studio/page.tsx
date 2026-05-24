"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { ImageIcon, MessageSquarePlus, Wand2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardSubtitle, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, type AssetItem, type Brand } from "@/lib/api";
import { formatRelative, shortId } from "@/lib/utils";
import { SandboxedPreview } from "@/components/preview/sandboxed-preview";

const CRITIQUE_PRESETS = [
  "Tighten the typography hierarchy",
  "Make the brand mark more prominent",
  "Lift contrast for outdoor visibility",
  "Reduce visual noise — simplify the composition",
  "Adjust the palette toward the brand accent",
];

export default function StudioPage() {
  const [brandId, setBrandId] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [critique, setCritique] = useState("");
  const [history, setHistory] = useState<
    Array<{ at: string; text: string; asset_id: string }>
  >([]);

  const { data: brands } = useSWR<Brand[]>("brands", () => api.brands.list(), {
    revalidateOnFocus: false,
  });

  useEffect(() => {
    if (!brandId && brands && brands.length > 0) setBrandId(brands[0].id);
  }, [brandId, brands]);

  const { data: assets } = useSWR<AssetItem[]>(
    brandId ? ["studio-assets", brandId] : null,
    () => api.assets.list({ brand_id: brandId, limit: 100 }),
    { revalidateOnFocus: false },
  );

  useEffect(() => {
    setSelectedId(null);
  }, [brandId]);

  const selected = useMemo(
    () => (assets ?? []).find((a) => a.id === selectedId) ?? null,
    [assets, selectedId],
  );

  function submitCritique() {
    const text = critique.trim();
    if (!text || !selected) return;
    setHistory((h) => [
      { at: new Date().toISOString(), text, asset_id: selected.id },
      ...h,
    ]);
    setCritique("");
  }

  return (
    <div className="space-y-8">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">
          Deliver
        </div>
        <h1 className="text-display-lg text-[color:var(--color-charcoal)]">
          Studio
        </h1>
        <p className="mt-2 max-w-[60ch] text-body-md text-[color:var(--color-slate)]">
          Open canvas — pick a single artifact and collaborate with agents on
          revisions. Critiques queue here and route into a{" "}
          <code>critique_output</code> loop when a brand run is in flight.
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
          {(assets ?? []).length} artifacts available
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_2fr_1fr]">
        <aside className="space-y-3">
          <h2 className="text-heading-md">Pick an artifact</h2>
          {!brandId && (
            <Card>
              <CardSubtitle>Pick a brand first.</CardSubtitle>
            </Card>
          )}
          {brandId && (assets ?? []).length === 0 && (
            <Card>
              <CardSubtitle>
                No artifacts yet — generate some via a brand run.
              </CardSubtitle>
            </Card>
          )}
          <div className="grid max-h-[600px] grid-cols-2 gap-2 overflow-y-auto pr-1">
            {(assets ?? []).map((a) => (
              <button
                key={a.id}
                onClick={() => setSelectedId(a.id)}
                className={`aspect-square overflow-hidden rounded-[12px] border transition-colors ${
                  selectedId === a.id
                    ? "border-[color:var(--color-ink)] ring-2 ring-[color:var(--color-ink)]"
                    : "border-[color:var(--color-hairline)] hover:border-[color:var(--color-stone)]"
                }`}
              >
                <div className="flex h-full w-full items-center justify-center bg-[color:var(--color-surface)] relative">
                  {a.storage_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={a.storage_url}
                      alt={a.purpose || a.kind}
                      className="absolute inset-0 h-full w-full object-cover"
                    />
                  ) : a.kind === "website" ? (
                    <div className="flex flex-col items-center gap-1.5 p-2 text-center text-xs font-medium text-[color:var(--color-ink)]">
                      <span className="text-[10px] uppercase font-bold text-violet-500 dark:text-violet-400">Site</span>
                      <span className="opacity-60 overflow-hidden text-ellipsis whitespace-nowrap w-full max-w-[65px]">{a.purpose || "Preview"}</span>
                    </div>
                  ) : (
                    <ImageIcon className="size-6 text-[color:var(--color-muted)]" />
                  )}
                </div>
              </button>
            ))}
          </div>
        </aside>

        <section>
          <h2 className="mb-3 text-heading-md">Canvas</h2>
          {!selected ? (
            <Card className="flex aspect-square w-full items-center justify-center">
              <p className="text-body-sm text-[color:var(--color-muted)]">
                Select an artifact to open it in the canvas.
              </p>
            </Card>
          ) : (
            <Card className="overflow-hidden p-0 h-[600px] flex flex-col">
              <div className="flex-1 w-full relative bg-[color:var(--color-surface)] overflow-hidden">
                {selected.kind === "website" && selected.text_content ? (
                  <SandboxedPreview
                    html={selected.text_content}
                    title={(selected.metadata?.brand_name as string) || "Website Preview"}
                  />
                ) : selected.storage_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={selected.storage_url}
                    alt={selected.purpose || selected.kind}
                    className="absolute inset-0 h-full w-full object-contain"
                  />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <ImageIcon className="size-16 text-[color:var(--color-muted)]" />
                  </div>
                )}
              </div>
              <div className="space-y-2 p-5">
                <div className="flex flex-wrap items-center gap-1.5">
                  <Badge tone="info">
                    {(selected.metadata?.purpose as string | undefined) ??
                      selected.kind}
                  </Badge>
                  {selected.width && selected.height && (
                    <Badge tone="neutral">
                      {selected.width}×{selected.height}
                    </Badge>
                  )}
                  <span className="text-micro ml-auto font-mono text-[color:var(--color-muted)]">
                    {shortId(selected.id, 8)}
                  </span>
                </div>
                {!!selected.metadata?.prompt && (
                  <p className="text-body-sm text-[color:var(--color-slate)]">
                    <span className="font-medium">Prompt: </span>
                    {String(selected.metadata.prompt)}
                  </p>
                )}
                {selected.workflow_run_id && (
                  <p className="text-micro text-[color:var(--color-muted)]">
                    From{" "}
                    <Link
                      href={`/workflows/${selected.workflow_run_id}`}
                      className="underline-offset-2 hover:underline"
                    >
                      run {shortId(selected.workflow_run_id, 6)}
                    </Link>
                    {" · "}
                    {formatRelative(selected.created_at)}
                  </p>
                )}
              </div>
            </Card>
          )}
        </section>

        <aside className="space-y-4">
          <h2 className="text-heading-md">Critique</h2>
          <Card>
            <div className="space-y-3">
              <p className="text-body-sm text-[color:var(--color-slate)]">
                Add a critique. When the source run is still in flight, this
                queues into <code>critique_output</code> and triggers a revised
                generation.
              </p>
              <Input
                placeholder="What should the next variant change?"
                value={critique}
                onChange={(e) => setCritique(e.target.value)}
                disabled={!selected}
              />
              <div className="flex flex-wrap gap-1.5">
                {CRITIQUE_PRESETS.map((p) => (
                  <button
                    key={p}
                    onClick={() => setCritique(p)}
                    disabled={!selected}
                    className="text-micro rounded-full bg-[color:var(--color-surface)] px-3 py-1 text-[color:var(--color-ink)] hover:bg-[color:var(--color-surface-elev)] disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {p}
                  </button>
                ))}
              </div>
              <Button
                variant="primary"
                size="md"
                onClick={submitCritique}
                disabled={!selected || !critique.trim()}
                className="w-full"
              >
                <MessageSquarePlus className="size-4" />
                Queue critique
              </Button>
            </div>
          </Card>

          <Card>
            <div className="mb-3 flex items-center gap-2">
              <Wand2 className="size-4 text-[color:var(--color-ink)]" />
              <p className="text-label-md font-medium">Queue</p>
              <Badge tone="neutral" className="ml-auto">
                {history.length}
              </Badge>
            </div>
            {history.length === 0 ? (
              <CardSubtitle>No critiques queued yet.</CardSubtitle>
            ) : (
              <ul className="space-y-3">
                {history.map((h, i) => (
                  <li
                    key={i}
                    className="border-b border-[color:var(--color-hairline)] pb-2 last:border-b-0"
                  >
                    <p className="text-body-sm text-[color:var(--color-ink)]">
                      {h.text}
                    </p>
                    <p className="text-micro mt-1 text-[color:var(--color-muted)]">
                      asset {shortId(h.asset_id, 6)} ·{" "}
                      {formatRelative(h.at)}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </aside>
      </div>

      {selected && (
        <Card feature>
          <CardTitle>Next step</CardTitle>
          <CardSubtitle>
            Open the source run to see all sibling variants and submit your
            critique queue as a structured revision request.
          </CardSubtitle>
          {selected.workflow_run_id && (
            <div className="mt-4">
              <Link
                href={`/workflows/${selected.workflow_run_id}`}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-full bg-[color:var(--color-ink)] px-5 text-label font-medium text-[color:var(--color-canvas)] hover:opacity-95"
              >
                Open source run
              </Link>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
