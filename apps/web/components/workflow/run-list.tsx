"use client";

import Link from "next/link";
import useSWR from "swr";

import { Badge, statusTone } from "@/components/ui/badge";
import { Card, CardSubtitle, CardTitle } from "@/components/ui/card";
import { api, type RunSummary } from "@/lib/api";
import { formatRelative, shortId } from "@/lib/utils";

const fetcher = (params?: { brand_id?: string; limit?: number }) => api.runs.list(params);

export function RunList({
  brandId,
  limit,
  emptyHint,
}: {
  brandId?: string;
  limit?: number;
  emptyHint?: string;
}) {
  const { data, error, isLoading } = useSWR<RunSummary[]>(
    brandId ? ["runs", brandId] : ["runs"],
    () => fetcher(brandId ? { brand_id: brandId, limit } : { limit }),
    { refreshInterval: 4000 },
  );

  return (
    <Card>
      <div className="mb-4 flex items-end justify-between">
        <div>
          <CardTitle>Recent runs</CardTitle>
          <CardSubtitle>
            {brandId ? "Runs for this brand" : "Latest activity across all brands"}
          </CardSubtitle>
        </div>
      </div>

      {isLoading && (
        <div className="py-10 text-center text-body-sm text-[color:var(--color-stone)]">
          Loading…
        </div>
      )}
      {error && (
        <div className="rounded-[12px] bg-[color:var(--color-error-bg)] px-4 py-3 text-label text-[color:var(--color-error-text)]">
          Failed to load runs.
        </div>
      )}
      {!isLoading && !error && (!data || data.length === 0) && (
        <div className="py-10 text-center text-body-sm text-[color:var(--color-stone)]">
          {emptyHint ?? "No runs yet."}
        </div>
      )}
      {data && data.length > 0 && (
        <ul className="divide-y divide-[color:var(--color-hairline)]">
          {data.map((r) => (
            <li key={r.id}>
              <Link
                href={`/workflows/${r.id}`}
                className="flex items-center justify-between gap-3 py-3 hover:bg-[color:var(--color-surface)] rounded-[8px] px-2 -mx-2 transition-colors"
              >
                <div>
                  <div className="text-label text-[color:var(--color-ink)]">
                    {r.workflow}
                  </div>
                  <div className="text-micro text-[color:var(--color-stone)] tabular">
                    {shortId(r.id)} · {formatRelative(r.created_at)}
                  </div>
                </div>
                <Badge tone={statusTone(r.status)}>{r.status}</Badge>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
