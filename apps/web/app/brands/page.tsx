"use client";

import Link from "next/link";
import useSWR from "swr";

import { Button } from "@/components/ui/button";
import { Card, CardSubtitle, CardTitle } from "@/components/ui/card";
import { SearchPill } from "@/components/ui/input";
import { api, type Brand } from "@/lib/api";
import { formatRelative } from "@/lib/utils";

export default function BrandsPage() {
  const { data, error, isLoading } = useSWR<Brand[]>("brands", () =>
    api.brands.list(),
  );

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between gap-6">
        <div>
          <div className="text-eyebrow text-[color:var(--color-stone)]">Workspace</div>
          <h1 className="text-display-lg text-[color:var(--color-charcoal)]">
            Brands
          </h1>
          <p className="mt-2 text-body-md text-[color:var(--color-slate)] max-w-[60ch]">
            Each brand is its own canvas — strategy, identity, packaging, web,
            social, and campaigns share one closed-loop memory.
          </p>
        </div>
        <Link href="/brands/new">
          <Button variant="primary" size="md">
            New brand
          </Button>
        </Link>
      </header>

      <SearchPill placeholder="Search brands…" />

      {isLoading && (
        <Card>
          <div className="py-10 text-center text-body-sm text-[color:var(--color-stone)]">
            Loading…
          </div>
        </Card>
      )}
      {error && (
        <Card>
          <div className="rounded-[12px] bg-[color:var(--color-error-bg)] px-4 py-3 text-label text-[color:var(--color-error-text)]">
            Failed to load brands. Is the API running on port 8000?
          </div>
        </Card>
      )}

      {data && data.length === 0 && (
        <Card>
          <CardTitle>No brands yet</CardTitle>
          <CardSubtitle>
            Create your first brand to start orchestrating identity, packaging,
            web, and social.
          </CardSubtitle>
        </Card>
      )}

      {data && data.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.map((b) => (
            <Link key={b.id} href={`/brands/${b.id}`}>
              <Card className="hover:shadow-[0_4px_12px_rgba(10,10,10,0.06)] transition-shadow h-full">
                <CardTitle>{b.name}</CardTitle>
                <CardSubtitle>
                  {b.slug ?? "—"} · created {formatRelative(b.created_at)}
                </CardSubtitle>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
