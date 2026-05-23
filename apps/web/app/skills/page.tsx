"use client";

import { useMemo, useState } from "react";
import useSWR from "swr";
import { Brain, ChevronRight, Sparkles, Tag } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  api,
  type SkillDetail,
  type SkillLearning,
  type SkillSummary,
  type SkillsCatalog,
} from "@/lib/api";

export default function SkillsPage() {
  const [query, setQuery] = useState("");
  const [tagFilter, setTagFilter] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const { data: catalog, isLoading, mutate } = useSWR<SkillsCatalog>(
    ["skills", tagFilter ?? ""],
    () => api.skills.list({ tag: tagFilter ?? undefined }),
    { revalidateOnFocus: false },
  );

  const { data: detail, mutate: mutateDetail } = useSWR<SkillDetail>(
    selected ? ["skill", selected] : null,
    () => api.skills.get(selected!),
    { revalidateOnFocus: false },
  );

  const allTags = useMemo(() => {
    const set = new Set<string>();
    (catalog?.items ?? []).forEach((s) => s.tags.forEach((t) => set.add(t)));
    return Array.from(set).sort();
  }, [catalog]);

  const filtered = useMemo(() => {
    const items = catalog?.items ?? [];
    if (!query.trim()) return items;
    const q = query.trim().toLowerCase();
    return items.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        (s.description ?? "").toLowerCase().includes(q) ||
        s.tags.some((t) => t.toLowerCase().includes(q)),
    );
  }, [catalog, query]);

  const onToggle = async (s: SkillSummary) => {
    try {
      await api.skills.toggle(s.name, !s.enabled);
      mutate();
      if (selected === s.name) mutateDetail();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="px-12 py-10">
      <header className="mb-8">
        <p className="text-micro uppercase tracking-wider text-muted">System</p>
        <h1 className="text-display-md mt-1">Skills</h1>
        <p className="text-body mt-3 max-w-2xl text-slate">
          Read-only registry of every SKILL.md manifest. Each row shows what
          triggers it, what outputs it produces, and the live learnings it has
          accumulated across runs.
        </p>
      </header>

      {catalog && (
        <div className="mb-6 grid grid-cols-3 gap-4">
          <Card className="p-5">
            <p className="text-micro uppercase tracking-wider text-muted">
              Total
            </p>
            <p className="text-display-sm mt-1">{catalog.summary.total}</p>
          </Card>
          <Card className="p-5">
            <p className="text-micro uppercase tracking-wider text-muted">
              Active handlers
            </p>
            <p className="text-display-sm mt-1">{catalog.summary.active}</p>
          </Card>
          <Card className="p-5">
            <p className="text-micro uppercase tracking-wider text-muted">
              Stub manifests
            </p>
            <p className="text-display-sm mt-1">{catalog.summary.stubs}</p>
          </Card>
        </div>
      )}

      <div className="mb-5 flex flex-wrap items-center gap-3">
        <Input
          placeholder="Filter skills by name, description, or tag…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="max-w-md"
        />
        {allTags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            <button
              onClick={() => setTagFilter(null)}
              className={`rounded-[4px] px-2 py-1 text-micro transition ${
                tagFilter === null
                  ? "bg-charcoal text-canvas"
                  : "border border-hairline text-slate hover:border-charcoal"
              }`}
            >
              all
            </button>
            {allTags.map((t) => (
              <button
                key={t}
                onClick={() => setTagFilter(t === tagFilter ? null : t)}
                className={`rounded-[4px] px-2 py-1 text-micro transition ${
                  tagFilter === t
                    ? "bg-charcoal text-canvas"
                    : "border border-hairline text-slate hover:border-charcoal"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        )}
      </div>

      {isLoading && <p className="text-body-sm text-muted">Loading skills…</p>}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_360px]">
        <div className="flex flex-col gap-3">
          {filtered.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelected(s.name)}
              className={`text-left transition ${
                selected === s.name ? "ring-1 ring-charcoal" : ""
              }`}
            >
              <Card className="flex items-start justify-between gap-4 p-5 hover:border-charcoal">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-label-lg truncate font-mono">
                      {s.name}
                    </h3>
                    <span className="text-micro text-muted">v{s.version}</span>
                    {s.is_stub ? (
                      <Badge tone="warning">stub</Badge>
                    ) : s.enabled ? (
                      <Badge tone="success">active</Badge>
                    ) : (
                      <Badge tone="neutral">disabled</Badge>
                    )}
                  </div>
                  {s.description && (
                    <p className="text-body-sm mt-1.5 line-clamp-2 text-slate">
                      {s.description}
                    </p>
                  )}
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {s.tags.slice(0, 6).map((t) => (
                      <Badge key={t} tone="info">
                        <Tag className="size-3" />
                        {t}
                      </Badge>
                    ))}
                  </div>
                  <div className="text-micro mt-2 flex flex-wrap gap-4 text-muted">
                    <span>used {s.usage_count}×</span>
                    <span>success {s.success_count}×</span>
                    {s.success_rate !== null &&
                      s.success_rate !== undefined && (
                        <span>rate {(s.success_rate * 100).toFixed(0)}%</span>
                      )}
                  </div>
                </div>
                <ChevronRight className="mt-1 size-4 text-muted" />
              </Card>
            </button>
          ))}
          {filtered.length === 0 && !isLoading && (
            <Card className="p-8 text-center">
              <p className="text-body-sm text-muted">No skills match the filter.</p>
            </Card>
          )}
        </div>

        <SkillDetailPanel
          detail={detail}
          onToggle={onToggle}
          onToggleLearning={async (lid, enabled) => {
            await api.skills.toggleLearning(lid, enabled);
            mutateDetail();
          }}
        />
      </div>
    </div>
  );
}

function SkillDetailPanel({
  detail,
  onToggle,
  onToggleLearning,
}: {
  detail: SkillDetail | undefined;
  onToggle: (s: SkillSummary) => void;
  onToggleLearning: (id: string, enabled: boolean) => void;
}) {
  if (!detail) {
    return (
      <Card className="sticky top-6 hidden h-fit p-6 xl:block">
        <div className="flex flex-col items-center gap-2 py-6 text-center">
          <Brain className="size-5 text-muted" />
          <p className="text-body-sm text-muted">
            Select a skill to see its manifest, dependencies, and the learnings
            it has accumulated from past runs.
          </p>
        </div>
      </Card>
    );
  }
  const s = detail.skill;
  return (
    <Card className="sticky top-6 hidden h-fit flex-col gap-4 p-6 xl:flex">
      <div>
        <p className="text-micro uppercase tracking-wider text-muted">
          Skill manifest
        </p>
        <h2 className="text-heading-md mt-1 font-mono">{s.name}</h2>
        <p className="text-body-sm mt-1 text-slate">
          {s.description ?? "No description"}
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {s.is_stub ? (
          <Badge tone="warning">stub manifest</Badge>
        ) : s.enabled ? (
          <Badge tone="success">enabled</Badge>
        ) : (
          <Badge tone="neutral">disabled</Badge>
        )}
        <Badge tone="info">v{s.version}</Badge>
      </div>

      <DetailRow label="Trigger phrases" items={s.trigger_phrases} />
      <DetailRow label="Required tools" items={s.required_tools} mono />
      <DetailRow label="Dependencies" items={s.dependencies} mono />
      <DetailRow label="Tags" items={s.tags} />

      <Button
        variant="secondary"
        size="sm"
        onClick={() => onToggle(s)}
        disabled={s.is_stub}
      >
        {s.enabled ? "Disable" : "Enable"} skill
      </Button>

      <div className="border-t border-hairline pt-4">
        <div className="mb-3 flex items-center gap-2">
          <Sparkles className="size-4 text-muted" />
          <p className="text-label-md">
            Learnings ({detail.learnings.length})
          </p>
        </div>
        {detail.learnings.length === 0 ? (
          <p className="text-body-sm text-muted">
            No learnings extracted yet. They accumulate after each successful
            run.
          </p>
        ) : (
          <ul className="flex flex-col gap-3">
            {detail.learnings.slice(0, 10).map((l) => (
              <LearningCard
                key={l.id}
                l={l}
                onToggle={(e) => onToggleLearning(l.id, e)}
              />
            ))}
          </ul>
        )}
      </div>
    </Card>
  );
}

function DetailRow({
  label,
  items,
  mono,
}: {
  label: string;
  items: string[];
  mono?: boolean;
}) {
  if (!items || items.length === 0) return null;
  return (
    <div>
      <p className="text-micro uppercase tracking-wider text-muted">{label}</p>
      <div className="mt-1.5 flex flex-wrap gap-1.5">
        {items.map((i) => (
          <span
            key={i}
            className={`rounded-[4px] border border-hairline px-2 py-0.5 text-micro text-slate ${
              mono ? "font-mono" : ""
            }`}
          >
            {i}
          </span>
        ))}
      </div>
    </div>
  );
}

function LearningCard({
  l,
  onToggle,
}: {
  l: SkillLearning;
  onToggle: (enabled: boolean) => void;
}) {
  return (
    <li className="rounded-[8px] border border-hairline p-3">
      <div className="mb-1 flex items-center justify-between">
        <span className="text-micro text-muted">
          {l.created_at
            ? new Date(l.created_at).toLocaleDateString()
            : "—"}
          {" · applied "}
          {l.applied_count}×
        </span>
        <button
          onClick={() => onToggle(!l.enabled)}
          className="text-micro text-muted hover:text-charcoal"
        >
          {l.enabled ? "disable" : "enable"}
        </button>
      </div>
      {l.trigger_context && (
        <p className="text-body-sm line-clamp-2 text-slate">
          <span className="text-muted">trigger:</span> {l.trigger_context}
        </p>
      )}
      {l.prompt_delta && (
        <p className="text-body-sm mt-1 line-clamp-3 text-charcoal">
          {l.prompt_delta}
        </p>
      )}
    </li>
  );
}
