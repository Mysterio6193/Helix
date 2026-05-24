"use client";

import { useState, useMemo, useEffect, useRef } from "react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  type Capability,
  type ModelEntry,
  modelPriceLabel,
  useModelCatalog,
} from "@/lib/llm";

const PROVIDER_LABELS: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  gemini: "Google Gemini",
  openrouter: "OpenRouter (multi-provider)",
  deepseek: "DeepSeek",
  groq: "Groq",
  mistral: "Mistral",
  dashscope: "Alibaba Qwen (DashScope)",
  replicate: "Replicate",
  runway: "Runway",
  veo: "Google Veo",
};

interface Props {
  capability: Capability;
  value: string | null;
  onChange: (modelId: string) => void;
  /** Hide unavailable models entirely (server has no key). */
  hideUnavailable?: boolean;
  /** Compact button form for inline use. */
  compact?: boolean;
  className?: string;
  label?: string;
}

export function ModelPicker({
  capability,
  value,
  onChange,
  hideUnavailable = false,
  compact = false,
  className,
  label,
}: Props) {
  const { data, isLoading, error } = useModelCatalog(capability);
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handle(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    window.addEventListener("mousedown", handle);
    return () => window.removeEventListener("mousedown", handle);
  }, [open]);

  const models = useMemo<ModelEntry[]>(() => {
    if (!data) return [];
    const list = data.models.filter((m) =>
      hideUnavailable ? m.available : true,
    );
    // Stable sort: available first, default first, then tier (free→pro→team), then alpha
    const tierRank: Record<string, number> = { free: 0, pro: 1, team: 2 };
    return [...list].sort((a, b) => {
      if (a.available !== b.available) return a.available ? -1 : 1;
      if (a.is_default !== b.is_default) return a.is_default ? -1 : 1;
      const t = (tierRank[a.tier] ?? 99) - (tierRank[b.tier] ?? 99);
      if (t !== 0) return t;
      return a.display_name.localeCompare(b.display_name);
    });
  }, [data, hideUnavailable]);

  const selected = useMemo(
    () => models.find((m) => m.id === value) ?? null,
    [models, value],
  );

  const grouped = useMemo(() => {
    const map = new Map<string, ModelEntry[]>();
    for (const m of models) {
      const k = m.provider;
      if (!map.has(k)) map.set(k, []);
      map.get(k)!.push(m);
    }
    return Array.from(map.entries());
  }, [models]);

  if (error) {
    return (
      <div className="text-micro text-[color:var(--color-error-text)]">
        Couldn't load models: {String(error)}
      </div>
    );
  }

  return (
    <div className={cn("relative inline-block", className)} ref={wrapRef}>
      {label && (
        <label className="block text-micro font-medium text-[color:var(--color-muted)] mb-1">
          {label}
        </label>
      )}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        disabled={isLoading}
        className={cn(
          "inline-flex items-center justify-between gap-2 rounded-md border border-[color:var(--color-border)] bg-[color:var(--color-canvas)] px-3 text-left transition-colors hover:bg-[color:var(--color-surface)]",
          "focus:outline-none focus:ring-2 focus:ring-[color:var(--color-ink)]",
          compact ? "h-8 text-label" : "h-10 text-body-sm",
          "min-w-[16rem]",
        )}
      >
        <span className="flex items-center gap-2 truncate">
          {selected ? (
            <>
              <span className="font-medium truncate">{selected.display_name}</span>
              {!selected.available && (
                <Badge tone="warning" className="shrink-0">
                  key missing
                </Badge>
              )}
            </>
          ) : (
            <span className="text-[color:var(--color-muted)]">
              {isLoading ? "Loading models…" : "Choose a model"}
            </span>
          )}
        </span>
        <ChevronIcon className={cn("h-4 w-4 transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div
          className="absolute z-50 mt-1 w-[28rem] max-h-[28rem] overflow-y-auto rounded-md border border-[color:var(--color-border)] bg-[color:var(--color-canvas)] shadow-lg"
          role="listbox"
        >
          {grouped.length === 0 && (
            <div className="px-3 py-4 text-body-sm text-[color:var(--color-muted)]">
              No models available. Configure provider keys server-side.
            </div>
          )}
          {grouped.map(([provider, items]) => (
            <div key={provider}>
              <div className="px-3 pt-2 pb-1 text-micro uppercase tracking-wide text-[color:var(--color-muted)]">
                {PROVIDER_LABELS[provider] ?? provider}
              </div>
              {items.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  role="option"
                  aria-selected={m.id === value}
                  onClick={() => {
                    onChange(m.id);
                    setOpen(false);
                  }}
                  className={cn(
                    "block w-full px-3 py-2 text-left transition-colors hover:bg-[color:var(--color-surface)]",
                    m.id === value && "bg-[color:var(--color-surface)]",
                    !m.available && "opacity-50",
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-body-sm truncate">
                      {m.display_name}
                    </span>
                    <div className="flex items-center gap-1 shrink-0">
                      {m.is_default && (
                        <Badge tone="info">default</Badge>
                      )}
                      <Badge
                        tone={
                          m.tier === "free"
                            ? "success"
                            : m.tier === "team"
                              ? "warning"
                              : "neutral"
                        }
                      >
                        {m.tier}
                      </Badge>
                      {!m.available && <Badge tone="warning">no key</Badge>}
                    </div>
                  </div>
                  <p className="mt-0.5 text-micro text-[color:var(--color-muted)] line-clamp-1">
                    {m.description}
                  </p>
                  <div className="mt-1 flex items-center gap-3 text-micro text-[color:var(--color-muted)]">
                    <span>{modelPriceLabel(m)}</span>
                    {m.context_window && (
                      <span>· {Math.round(m.context_window / 1000)}k ctx</span>
                    )}
                    {m.supports_streaming && <span>· streaming</span>}
                    {m.supports_vision && <span>· vision</span>}
                  </div>
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ChevronIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="m4 6 4 4 4-4" />
    </svg>
  );
}
