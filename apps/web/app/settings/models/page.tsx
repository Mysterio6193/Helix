"use client";

import { useState } from "react";

import { ModelPicker } from "@/components/model-picker";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  llmApi,
  setDefaultModel,
  useModelCatalog,
  useWorkspacePrefs,
  type Capability,
} from "@/lib/llm";

const CAPABILITY_META: Record<
  Capability,
  { label: string; description: string }
> = {
  chat: {
    label: "Chat & reasoning",
    description:
      "Used for copywriting, brand strategy, critique, and orchestrator reasoning.",
  },
  image: {
    label: "Image generation",
    description: "Used for logos, packaging mockups, social posts, menu art.",
  },
  video: {
    label: "Video generation",
    description: "Used for launch teasers and short-form campaign clips.",
  },
  embedding: { label: "Embeddings", description: "Memory + semantic search." },
};

export default function ModelSettingsPage() {
  const { data: prefs, isLoading: prefsLoading, mutate: refetchPrefs } =
    useWorkspacePrefs();
  const [savingCap, setSavingCap] = useState<Capability | null>(null);
  const [testPrompt, setTestPrompt] = useState(
    "Write a 6-word tagline for an artisan bakery in Brooklyn.",
  );
  const [testModel, setTestModel] = useState<string | null>(null);
  const [testOutput, setTestOutput] = useState<string>("");
  const [testMeta, setTestMeta] = useState<string>("");
  const [testing, setTesting] = useState(false);

  async function handleChange(cap: Capability, modelId: string) {
    setSavingCap(cap);
    try {
      const next = await setDefaultModel(cap, modelId);
      await refetchPrefs(next, { revalidate: false });
    } finally {
      setSavingCap(null);
    }
  }

  async function runTest() {
    setTesting(true);
    setTestOutput("");
    setTestMeta("");
    try {
      const r = await llmApi.complete({
        model: testModel ?? prefs?.default_chat_model ?? undefined,
        prompt: testPrompt,
        max_tokens: 80,
        temperature: 0.8,
      });
      setTestOutput(r.text);
      setTestMeta(
        `${r.provider} · ${r.model} · in:${r.prompt_tokens ?? "?"} / out:${r.completion_tokens ?? "?"} · ${
          r.cost_usd != null ? `$${r.cost_usd.toFixed(4)}` : "—"
        }`,
      );
    } catch (e) {
      setTestOutput(`Error: ${String(e)}`);
    } finally {
      setTesting(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-8 space-y-8">
      <header className="space-y-2">
        <h1 className="text-display-sm font-medium tracking-tight">
          Model preferences
        </h1>
        <p className="text-body-md text-[color:var(--color-muted)]">
          Pick which AI models Helix uses for your workspace. API keys are
          managed by Helix — you don't need your own.
        </p>
      </header>

      {(["chat", "image", "video"] as Capability[]).map((cap) => {
        const meta = CAPABILITY_META[cap];
        const currentId =
          cap === "chat"
            ? prefs?.default_chat_model
            : cap === "image"
              ? prefs?.default_image_model
              : prefs?.default_video_model;
        return (
          <CapabilityCard
            key={cap}
            capability={cap}
            label={meta.label}
            description={meta.description}
            currentId={currentId ?? null}
            disabled={prefsLoading}
            saving={savingCap === cap}
            onChange={(id) => handleChange(cap, id)}
          />
        );
      })}

      <Card className="p-6 space-y-4">
        <div>
          <h2 className="text-heading-md font-medium">Test playground</h2>
          <p className="text-body-sm text-[color:var(--color-muted)]">
            Quick smoke test against the gateway. Uses your default chat model
            unless overridden.
          </p>
        </div>
        <div className="flex flex-col gap-3">
          <ModelPicker
            capability="chat"
            value={testModel ?? prefs?.default_chat_model ?? null}
            onChange={setTestModel}
            label="Model override (optional)"
          />
          <textarea
            value={testPrompt}
            onChange={(e) => setTestPrompt(e.target.value)}
            className="min-h-[5rem] rounded-md border border-[color:var(--color-border)] bg-[color:var(--color-canvas)] p-3 text-body-sm focus:outline-none focus:ring-2 focus:ring-[color:var(--color-ink)]"
            placeholder="Prompt"
          />
          <div>
            <Button onClick={runTest} disabled={testing || !testPrompt.trim()}>
              {testing ? "Running…" : "Run test"}
            </Button>
          </div>
          {testOutput && (
            <div className="rounded-md bg-[color:var(--color-surface)] p-4 space-y-2">
              <pre className="whitespace-pre-wrap text-body-sm">{testOutput}</pre>
              {testMeta && (
                <div className="text-micro text-[color:var(--color-muted)]">
                  {testMeta}
                </div>
              )}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

function CapabilityCard({
  capability,
  label,
  description,
  currentId,
  disabled,
  saving,
  onChange,
}: {
  capability: Capability;
  label: string;
  description: string;
  currentId: string | null;
  disabled: boolean;
  saving: boolean;
  onChange: (id: string) => void;
}) {
  const { data } = useModelCatalog(capability);
  const current = data?.models.find((m) => m.id === currentId);
  return (
    <Card className="p-6 space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-heading-md font-medium">{label}</h2>
          <p className="text-body-sm text-[color:var(--color-muted)]">
            {description}
          </p>
        </div>
        {saving && (
          <Badge tone="info">Saving…</Badge>
        )}
      </div>
      <ModelPicker
        capability={capability}
        value={currentId}
        onChange={onChange}
      />
      {current && (
        <div className="text-micro text-[color:var(--color-muted)]">
          Selected · {current.provider} / {current.model}
          {!current.available && (
            <span className="ml-2 text-[color:var(--color-warning-text)]">
              (server has no key for this provider yet)
            </span>
          )}
        </div>
      )}
    </Card>
  );
}
