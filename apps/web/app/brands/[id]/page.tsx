"use client";

import Link from "next/link";
import { use } from "react";
import useSWR from "swr";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardSubtitle,
  CardTitle,
  ProductCard,
} from "@/components/ui/card";
import { RunList } from "@/components/workflow/run-list";
import { api, type Brand } from "@/lib/api";

interface PageProps {
  params: Promise<{ id: string }>;
}

const SLICES: {
  workflow: string;
  title: string;
  blurb: string;
  gradient: "coral" | "magenta" | "blue" | "purple" | "amber";
}[] = [
  {
    workflow: "brand_identity_foundation",
    title: "Brand Identity",
    blurb: "Strategy, design school, taglines, logo variants.",
    gradient: "coral",
  },
  {
    workflow: "packaging_suite",
    title: "Packaging Suite",
    blurb: "Boxes, bowls, cups, bags, stickers — print-ready artwork.",
    gradient: "purple",
  },
  {
    workflow: "website_suite",
    title: "Website Suite",
    blurb: "Sections, copy, Next.js scaffold, Vercel deploy.",
    gradient: "blue",
  },
  {
    workflow: "social_pack",
    title: "Social Pack",
    blurb: "Captions, carousels, story templates, highlight covers.",
    gradient: "magenta",
  },
  {
    workflow: "menu_design",
    title: "Menu Design",
    blurb: "Digital, print, board menus, dish items, pricing psychology.",
    gradient: "amber",
  },
  {
    workflow: "launch_campaign",
    title: "Launch Campaign",
    blurb: "Press releases, email sequences, localized ad creatives.",
    gradient: "coral",
  },
];

export default function BrandDetail({ params }: PageProps) {
  const { id } = use(params);
  const { data: brand, error, isLoading } = useSWR<Brand>(
    ["brand", id],
    () => api.brands.get(id),
  );

  return (
    <div className="space-y-10">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">
          <Link href="/brands" className="hover:underline">
            Brands
          </Link>{" "}
          · detail
        </div>
        {isLoading && (
          <h1 className="text-display-lg text-[color:var(--color-muted)]">
            Loading…
          </h1>
        )}
        {error && (
          <h1 className="text-display-lg text-[color:var(--color-error-text)]">
            Not found
          </h1>
        )}
        {brand && (
          <>
            <h1 className="text-display-lg text-[color:var(--color-charcoal)]">
              {brand.name}
            </h1>
            <p className="mt-2 text-body-md text-[color:var(--color-slate)]">
              {brand.slug ?? "—"}
            </p>
          </>
        )}
      </header>

      {/* Workflow launchers — vibrant cards */}
      <section>
        <div className="mb-4 flex items-end justify-between">
          <div>
            <h2 className="text-heading-xl text-[color:var(--color-charcoal)]">
              Launch a workflow
            </h2>
            <p className="text-body-sm text-[color:var(--color-steel)]">
              Each workflow produces real strategy, creative, campaign, or commerce artifacts.
            </p>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {SLICES.map((s) => (
            <ProductCard
              key={s.workflow}
              gradient={s.gradient}
              className="flex flex-col gap-4"
            >
              <div className="text-eyebrow">{s.workflow}</div>
              <div className="text-heading-lg">{s.title}</div>
              <p className="text-body-sm">{s.blurb}</p>
              <div className="pt-2">
                <LaunchButton brand={brand} workflow={s.workflow} />
              </div>
            </ProductCard>
          ))}
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RunList brandId={id} limit={12} emptyHint="No runs for this brand yet." />
        </div>
        <Card feature>
          <CardTitle>Closed-loop memory</CardTitle>
          <CardSubtitle>
            Every successful skill extracts a learning that informs future runs
            for this brand.
          </CardSubtitle>
          <Link href={`/memory?brand=${id}`} className="mt-4 inline-block">
            <Button variant="secondary" size="sm">
              Inspect memory
            </Button>
          </Link>
        </Card>
      </section>
    </div>
  );
}

function LaunchButton({
  brand,
  workflow,
}: {
  brand?: Brand;
  workflow: string;
}) {
  async function launch() {
    if (!brand) return;
    try {
      const inputs = {
        category: brand.category || "restaurant",
        cuisine: brand.metadata?.cuisine || "",
        city: brand.metadata?.city || "",
        audience: brand.target_audience?.audience || "",
        vibe: brand.voice_attributes?.vibe || "",
      };
      const run = await api.runs.create({
        workflow,
        brand_id: brand.id,
        inputs,
      });
      window.location.href = `/workflows/${run.id}`;
    } catch (e) {
      console.error("run.create_failed", e);
      alert("Failed to launch run — check the API logs.");
    }
  }
  return (
    <Button variant="primary" size="md" onClick={launch} disabled={!brand}>
      Run →
    </Button>
  );
}
