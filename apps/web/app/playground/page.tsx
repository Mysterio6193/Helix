"use client";

import { useMemo, useState } from "react";
import { AlertCircle, Loader2, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ModelPicker } from "@/components/model-picker";
import { formatCost, llmApi, useModelCatalog, type ModelEntry } from "@/lib/llm";

interface PlaygroundResult {
  model: string;
  provider: string;
  display_name: string | null;
  text: string;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  cost_usd: number | null;
  latency_ms: number | null;
  error: string | null;
}

interface PlaygroundResponse {
  results: PlaygroundResult[];
}

const SAMPLE_PROMPTS = [
  "Write a 3-line tagline for a premium organic coffee brand targeting Gen Z.",
  "Compare and contrast React vs Vue. Be opinionated.",
  "Translate this to French: 'The early bird catches the worm.'",
  "Write a 4-line poem about artificial intelligence in the style of Shakespeare.",
  "Explain quantum computing to a 10-year-old.",
  "Summarize the key differences between SQL and NoSQL databases.",
];

export default function PlaygroundPage() {
  const { data: catalog } = useModelCatalog("chat");

  const [models, setModels] = useState<string[]>(["", ""]);
  const [prompt, setPrompt] = useState("");
  const [system, setSystem] = useState("You are Helix, the AI creative OS. Be concise and direct.");
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(1500);
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<PlaygroundResponse | null>(null);
  const [showSystem, setShowSystem] = useState(false);

  const availableModels = useMemo(
    () => (catalog?.models ?? []).filter((m) => m.capability === "chat" && m.available),
    [catalog],
  );

  const canRun = models.every(Boolean) && prompt.trim().length > 0 && !running;

  function addModel() {
    if (models.length < 6) setModels([...models, ""]);
  }

  function removeModel(idx: number) {
    if (models.length > 2) setModels(models.filter((_, i) => i !== idx));
  }

  function updateModel(idx: number, val: string) {
    const updated = [...models];
    updated[idx] = val;
    setModels(updated);
  }

  async function runComparison() {
    setRunning(true);
    setResults(null);
    try {
      const data = await llmApi.playground({
        models: models.filter(Boolean),
        prompt,
        system: system || undefined,
        temperature,
        max_tokens: maxTokens,
      });
      setResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-8 animate-fade-up">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">Testing</div>
        <h1 className="mt-2 text-display-lg font-bold leading-tight text-white">Playground</h1>
        <p className="mt-3 max-w-[72ch] text-body-md text-[color:var(--color-slate)]">
          Compare model outputs side by side. Select 2–6 chat models and enter a prompt to see how each responds.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_0.35fr]">
        {/* Input panel */}
        <div className="space-y-6">
          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-4">
              <div className="text-eyebrow text-[color:var(--color-stone)]">Configuration</div>
              <h2 className="mt-1 text-heading-lg text-white">Models</h2>
            </div>

            <div className="space-y-3">
              {models.map((m, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="w-5 text-xs text-[color:var(--color-stone)]">#{i + 1}</span>
                  <div className="flex-1">
                    <ModelPicker
                      capability="chat"
                      value={m || null}
                      onChange={(v) => updateModel(i, v)}
                      hideUnavailable
                    />
                  </div>
                  {models.length > 2 && (
                    <button
                      onClick={() => removeModel(i)}
                      className="text-[10px] text-red-400 hover:text-red-300 transition-colors"
                    >
                      Remove
                    </button>
                  )}
                </div>
              ))}
              {models.length < 6 && (
                <Button variant="secondary" size="sm" onClick={addModel}>
                  + Add model
                </Button>
              )}
            </div>
          </Card>

          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-4">
              <div className="text-eyebrow text-[color:var(--color-stone)]">Input</div>
              <h2 className="mt-1 text-heading-lg text-white">Prompt</h2>
            </div>

            <div className="space-y-4">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="min-h-[6rem] w-full rounded-lg border border-white/[0.08] bg-black/30 p-4 text-body-sm text-white placeholder:text-[color:var(--color-stone)] focus:outline-none focus:ring-2 focus:ring-white/20"
                placeholder="Enter your prompt here..."
              />

              <div className="flex flex-wrap gap-2">
                {SAMPLE_PROMPTS.map((sp) => (
                  <button
                    key={sp}
                    onClick={() => setPrompt(sp)}
                    className="rounded-full border border-white/[0.06] bg-white/[0.03] px-2.5 py-1 text-[10px] text-[color:var(--color-slate)] hover:bg-white/[0.06] transition-colors"
                  >
                    {sp.length > 40 ? sp.slice(0, 40) + "..." : sp}
                  </button>
                ))}
              </div>

              <div className="flex items-center justify-between">
                <button
                  onClick={() => setShowSystem(!showSystem)}
                  className="text-[10px] uppercase tracking-wider text-[color:var(--color-stone)] hover:text-white transition-colors"
                >
                  {showSystem ? "Hide" : "Show"} system prompt
                </button>

                <div className="flex items-center gap-4">
                  <label className="text-[10px] text-[color:var(--color-stone)]">
                    Temp: {temperature.toFixed(1)}
                    <input
                      type="range"
                      min="0"
                      max="2"
                      step="0.1"
                      value={temperature}
                      onChange={(e) => setTemperature(parseFloat(e.target.value))}
                      className="ml-2 w-20"
                    />
                  </label>
                  <label className="text-[10px] text-[color:var(--color-stone)]">
                    Max tokens: {maxTokens}
                    <input
                      type="range"
                      min="256"
                      max="8192"
                      step="256"
                      value={maxTokens}
                      onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                      className="ml-2 w-20"
                    />
                  </label>
                </div>
              </div>

              {showSystem && (
                <textarea
                  value={system}
                  onChange={(e) => setSystem(e.target.value)}
                  className="min-h-[3rem] w-full rounded-lg border border-white/[0.08] bg-black/30 p-3 text-body-sm text-white placeholder:text-[color:var(--color-stone)] focus:outline-none focus:ring-2 focus:ring-white/20"
                  placeholder="System prompt..."
                />
              )}
            </div>

            <div className="mt-4">
              <Button onClick={runComparison} disabled={!canRun} variant="primary">
                {running ? (
                  <>
                    <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                    Running…
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-1.5 size-3.5" />
                    Compare models
                  </>
                )}
              </Button>
            </div>
          </Card>
        </div>

        {/* Results panel */}
        <div className="space-y-6">
          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-4">
              <div className="text-eyebrow text-[color:var(--color-stone)]">Output</div>
              <h2 className="mt-1 text-heading-lg text-white">Results</h2>
            </div>

            {!results && !running && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="mb-3 rounded-full bg-white/[0.04] p-4">
                  <Sparkles className="size-8 text-[color:var(--color-stone)]" />
                </div>
                <p className="text-body-sm text-[color:var(--color-slate)]">
                  Select models, enter a prompt, and run a comparison.
                </p>
              </div>
            )}

            {running && !results && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Loader2 className="mb-3 size-8 animate-spin text-[var(--color-signature)]" />
                <p className="text-body-sm text-[color:var(--color-slate)]">
                  Querying {models.filter(Boolean).length} models…
                </p>
              </div>
            )}

            {results && (
              <div className="space-y-4">
                {results.results.map((r, i) => {
                  const modelEntry = availableModels.find((m) => m.id === r.model);
                  return (
                    <div
                      key={i}
                      className="rounded-lg border border-white/[0.06] bg-black/20 p-4"
                    >
                      <div className="mb-2 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-white">
                            {r.display_name || modelEntry?.display_name || r.model}
                          </span>
                          <Badge tone="neutral" className="text-[8px]">
                            {r.provider}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-[color:var(--color-stone)]">
                          {r.latency_ms != null && (
                            <span>{r.latency_ms.toFixed(0)}ms</span>
                          )}
                          {r.cost_usd != null && (
                            <span>{formatCost(r.cost_usd)}</span>
                          )}
                        </div>
                      </div>

                      {r.error ? (
                        <div className="flex items-center gap-2 text-xs text-red-400">
                          <AlertCircle className="size-3" />
                          {r.error}
                        </div>
                      ) : (
                        <pre className="whitespace-pre-wrap text-body-sm text-[color:var(--color-slate)]">
                          {r.text}
                        </pre>
                      )}

                      {(r.prompt_tokens != null || r.completion_tokens != null) && (
                        <div className="mt-2 flex gap-2 text-[9px] text-[color:var(--color-stone)]">
                          {r.prompt_tokens != null && <span>↑{r.prompt_tokens} tok</span>}
                          {r.completion_tokens != null && <span>↓{r.completion_tokens} tok</span>}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
