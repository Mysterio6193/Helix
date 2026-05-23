"use client";

import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { FileText, Filter, Image as ImageIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { AssetThumb } from "@/components/asset-thumb";
import { api, type AssetItem, type Brand } from "@/lib/api";

export default function AssetsPage() {
  const [brandId, setBrandId] = useState<string>("");
  const [kind, setKind] = useState<string>("");
  const [query, setQuery] = useState("");

  const { data: brands } = useSWR<Brand[]>("brands", () => api.brands.list(), {
    revalidateOnFocus: false,
  });

  useEffect(() => {
    if (!brandId && brands && brands.length > 0) setBrandId(brands[0].id);
  }, [brandId, brands]);

  const { data: assets, isLoading } = useSWR<AssetItem[]>(
    brandId ? ["assets", brandId, kind] : null,
    () =>
      api.assets.list({
        brand_id: brandId,
        kind: kind || undefined,
        limit: 200,
      }),
    { revalidateOnFocus: false },
  );

  const kinds = useMemo(() => {
    const set = new Set<string>();
    (assets ?? []).forEach((a) => set.add(a.kind));
    return Array.from(set).sort();
  }, [assets]);

  const filtered = useMemo(() => {
    const items = assets ?? [];
    if (!query.trim()) return items;
    const q = query.trim().toLowerCase();
    return items.filter(
      (a) =>
        a.kind.toLowerCase().includes(q) ||
        (a.s3_key ?? "").toLowerCase().includes(q) ||
        JSON.stringify(a.metadata).toLowerCase().includes(q),
    );
  }, [assets, query]);

  return (
    <div className="px-12 py-10">
      <header className="mb-8">
        <p className="text-micro uppercase tracking-wider text-muted">Deliver</p>
        <h1 className="text-display-md mt-1">Assets</h1>
        <p className="text-body mt-3 max-w-2xl text-slate">
          Searchable library of every artifact every run has produced — logos,
          packaging panels, website sections, social tiles — with provenance
          back to the run that made them.
        </p>
      </header>

      <Card className="mb-6 p-5">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-micro uppercase tracking-wider text-muted">
              Brand
            </label>
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

          <div className="flex flex-col gap-1.5">
            <label className="text-micro uppercase tracking-wider text-muted">
              Kind
            </label>
            <select
              value={kind}
              onChange={(e) => setKind(e.target.value)}
              className="rounded-[8px] border border-hairline bg-canvas px-3 py-1.5 text-body-sm"
            >
              <option value="">all kinds</option>
              {kinds.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
          </div>

          <div className="flex min-w-[280px] flex-col gap-1.5">
            <label className="text-micro uppercase tracking-wider text-muted">
              Search
            </label>
            <Input
              placeholder="Search kind, s3 key, metadata…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          <div className="ml-auto flex items-center gap-2 text-micro text-muted">
            <Filter className="size-3.5" />
            <span>{filtered.length} assets</span>
          </div>
        </div>
      </Card>

      {!brandId && (
        <Card className="p-6">
          <p className="text-body-sm text-muted">
            Pick a brand to see its assets.
          </p>
        </Card>
      )}

      {isLoading && (
        <p className="text-body-sm text-muted">Loading assets…</p>
      )}

      {brandId && filtered.length === 0 && !isLoading && (
        <Card className="p-8 text-center">
          <p className="text-body-sm text-muted">
            No assets yet for this filter. Kick off a workflow run to populate
            the library.
          </p>
        </Card>
      )}

      {filtered.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((a) => (
            <AssetTile key={a.id} asset={a} />
          ))}
        </div>
      )}
    </div>
  );
}

function AssetTile({ asset }: { asset: AssetItem }) {
  const isImage = (asset.mime_type ?? "").startsWith("image/");
  const meta = asset.metadata ?? {};
  const label =
    (meta.purpose as string | undefined) ??
    (meta.label as string | undefined) ??
    asset.kind;
  return (
    <Card className="flex flex-col gap-3 overflow-hidden p-0">
      <div className="aspect-square w-full">
        <AssetThumb
          assetId={asset.id}
          kind={asset.kind}
          mimeType={asset.mime_type}
          className="w-full h-full rounded-b-none"
        />
      </div>
      <div className="px-5 pb-5">
        <div className="mb-2 flex flex-wrap items-center gap-1.5">
          <Badge tone="info">{asset.kind}</Badge>
          {asset.mime_type && (
            <Badge tone="neutral">{asset.mime_type}</Badge>
          )}
        </div>
        <p className="text-label-md line-clamp-1">{label}</p>
        {asset.width && asset.height && (
          <p className="text-micro mt-1 font-mono text-muted">
            {asset.width} × {asset.height}
          </p>
        )}
        {asset.s3_key && (
          <p className="text-micro mt-1 truncate font-mono text-muted">
            {asset.s3_key}
          </p>
        )}
        <p className="text-micro mt-2 text-muted">
          {asset.created_at
            ? new Date(asset.created_at).toLocaleString()
            : "—"}
        </p>
      </div>
    </Card>
  );
}
