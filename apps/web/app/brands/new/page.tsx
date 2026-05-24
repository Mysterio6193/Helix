"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSWRConfig } from "swr";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

export default function NewBrandPage() {
  const router = useRouter();
  const { mutate } = useSWRConfig();

  // Form State
  const [name, setName] = useState("");
  const [category, setCategory] = useState("restaurant");
  const [cuisine, setCuisine] = useState("");
  const [city, setCity] = useState("");
  const [audience, setAudience] = useState("");
  const [vibe, setVibe] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Brand name is required.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const payload = {
        name,
        category,
        target_audience: { audience },
        voice_attributes: { vibe },
        metadata: { cuisine, city },
      };

      const newBrand = await api.brands.create(payload);
      
      // Invalidate brands list cache so the new brand shows up in list instantly
      await mutate("brands");

      // Redirect user to the detail page of newly created brand
      router.push(`/brands/${newBrand.id}`);
    } catch (err: any) {
      console.error("brand.create_failed", err);
      setError(err?.message || "Failed to create brand canvas. Please check API connection.");
      setIsSubmitting(false);
    }
  }

  return (
    <div className="space-y-8 max-w-3xl mx-auto py-4">
      <header className="space-y-2">
        <div className="text-eyebrow text-[color:var(--color-stone)]">
          <Link href="/brands" className="hover:underline">
            Brands
          </Link>{" "}
          · new
        </div>
        <h1 className="text-display-lg text-[color:var(--color-charcoal)]">
          Create brand canvas
        </h1>
        <p className="text-body-md text-[color:var(--color-slate)]">
          Establish the foundational brand identity. This becomes the root context and seed memory for downstream Helix workflows.
        </p>
      </header>

      {error && (
        <div className="rounded-[8px] bg-[color:var(--color-error-bg)] px-4 py-3 text-label text-[color:var(--color-error-text)] border border-[color:var(--color-error-text)]/10">
          {error}
        </div>
      )}

      <Card className="p-8 shadow-[0_8px_30px_rgb(0,0,0,0.02)] border border-[color:var(--color-hairline)] bg-[color:var(--color-canvas)]">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Brand Name */}
            <div className="space-y-2 md:col-span-2">
              <label htmlFor="brand-name" className="text-label text-[color:var(--color-slate)] font-medium">
                Brand Name *
              </label>
              <Input
                id="brand-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Noodle Craft"
                disabled={isSubmitting}
                required
                autoFocus
              />
            </div>

            {/* Category Select */}
            <div className="space-y-2">
              <label htmlFor="brand-category" className="text-label text-[color:var(--color-slate)] font-medium">
                Category
              </label>
              <div className="relative">
                <select
                  id="brand-category"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  disabled={isSubmitting}
                  className="h-10 w-full rounded-[8px] border border-[color:var(--color-hairline)] bg-[color:var(--color-canvas)] px-3 text-body-md text-[color:var(--color-ink)] focus-visible:outline-none focus-visible:border-[color:var(--color-ink)] focus-visible:ring-2 focus-visible:ring-[color:var(--color-ink)] disabled:bg-[color:var(--color-surface)] disabled:text-[color:var(--color-muted)]"
                >
                  <option value="restaurant">Restaurant</option>
                  <option value="cafe">Cafe</option>
                  <option value="quick_service">Quick Service</option>
                  <option value="food_truck">Food Truck</option>
                </select>
              </div>
            </div>

            {/* Cuisine */}
            <div className="space-y-2">
              <label htmlFor="brand-cuisine" className="text-label text-[color:var(--color-slate)] font-medium">
                Cuisine / Product Type
              </label>
              <Input
                id="brand-cuisine"
                value={cuisine}
                onChange={(e) => setCuisine(e.target.value)}
                placeholder="e.g. Japanese Ramen, Artisanal Bakery"
                disabled={isSubmitting}
              />
            </div>

            {/* City */}
            <div className="space-y-2">
              <label htmlFor="brand-city" className="text-label text-[color:var(--color-slate)] font-medium">
                City / Location
              </label>
              <Input
                id="brand-city"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="e.g. Tokyo, New York"
                disabled={isSubmitting}
              />
            </div>

            {/* Vibe */}
            <div className="space-y-2">
              <label htmlFor="brand-vibe" className="text-label text-[color:var(--color-slate)] font-medium">
                Brand Vibe
              </label>
              <Input
                id="brand-vibe"
                value={vibe}
                onChange={(e) => setVibe(e.target.value)}
                placeholder="e.g. Refined Minimalist, Cyberpunk Cozy"
                disabled={isSubmitting}
              />
            </div>

            {/* Target Audience Description */}
            <div className="space-y-2 md:col-span-2">
              <label htmlFor="brand-audience" className="text-label text-[color:var(--color-slate)] font-medium">
                Target Audience Description
              </label>
              <textarea
                id="brand-audience"
                value={audience}
                onChange={(e) => setAudience(e.target.value)}
                placeholder="Describe your ideal customers, their preferences, and demographic (e.g. Busy urban professionals seeking quick, high-fidelity nourishing meals)."
                disabled={isSubmitting}
                rows={4}
                className="min-h-[100px] w-full rounded-[8px] border border-[color:var(--color-hairline)] bg-[color:var(--color-canvas)] p-3 text-body-md text-[color:var(--color-ink)] placeholder:text-[color:var(--color-stone)] focus-visible:outline-none focus-visible:border-[color:var(--color-ink)] focus-visible:ring-2 focus-visible:ring-[color:var(--color-ink)] disabled:bg-[color:var(--color-surface)] disabled:text-[color:var(--color-muted)] resize-y"
              />
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-4 pt-4 border-t border-[color:var(--color-hairline)]">
            <Link href="/brands">
              <Button
                type="button"
                variant="secondary"
                size="md"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            </Link>
            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Orchestrating..." : "Create Brand Canvas →"}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
