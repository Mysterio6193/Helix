"use client";

import { useCallback, useState } from "react";
import useSWR from "swr";
import { Key, Check, Eye, EyeOff, Trash2, AlertCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

interface UserKey {
  provider: string;
  key_prefix: string;
  created_at: string | null;
}

const PROVIDERS = [
  { id: "openai", label: "OpenAI", url: "https://platform.openai.com/api-keys" },
  { id: "anthropic", label: "Anthropic", url: "https://console.anthropic.com/settings/keys" },
  { id: "gemini", label: "Google Gemini", url: "https://aistudio.google.com/apikey" },
  { id: "openrouter", label: "OpenRouter", url: "https://openrouter.ai/keys" },
  { id: "deepseek", label: "DeepSeek", url: "https://platform.deepseek.com/api-keys" },
  { id: "groq", label: "Groq", url: "https://console.groq.com/keys" },
  { id: "mistral", label: "Mistral", url: "https://console.mistral.ai/api-keys" },
  { id: "dashscope", label: "DashScope (Alibaba)", url: "https://bailian.console.aliyun.com/" },
] as const;

export default function ProviderKeysPage() {
  const { data: auth } = useSWR("auth-me", () => api.auth.me());
  const { data: keys, mutate: refreshKeys } = useSWR<UserKey[]>(
    auth?.authenticated ? "user-keys" : null,
    () => api.get("/api/v1/user-keys").then((r: any) => r.keys as UserKey[]),
  );

  const [addingFor, setAddingFor] = useState<string | null>(null);
  const [keyValue, setKeyValue] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const keyMap = new Map((keys ?? []).map((k) => [k.provider, k]));

  const handleSave = useCallback(async (provider: string) => {
    if (!keyValue.trim()) return;
    setSaving(true);
    setErrorMsg(null);
    try {
      await api.post("/api/v1/user-keys", { provider, raw_key: keyValue.trim() });
      setSuccessMsg(`${provider} key saved`);
      setKeyValue("");
      setAddingFor(null);
      refreshKeys();
    } catch (err: any) {
      setErrorMsg(err?.message || String(err));
    } finally {
      setSaving(false);
    }
  }, [keyValue, refreshKeys]);

  const handleDelete = useCallback(async (provider: string) => {
    if (!confirm(`Remove your ${provider} API key?`)) return;
    try {
      await api.delete(`/api/v1/user-keys/${provider}`);
      refreshKeys();
    } catch (err: any) {
      setErrorMsg(err?.message || String(err));
    }
  }, [refreshKeys]);

  if (!auth?.authenticated) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="mb-3 text-2xl font-semibold">Provider Keys</h1>
        <p className="text-muted-foreground">Please sign in to manage your API keys.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">Provider Keys</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Bring your own API key for any provider. Keys are encrypted at rest and used
          instead of the server&apos;s shared keys when making LLM calls.
        </p>
      </div>

      {errorMsg ? (
        <div className="mb-6 flex items-center gap-2 rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-700">
          <AlertCircle size={14} />
          {errorMsg}
        </div>
      ) : null}
      {successMsg ? (
        <div className="mb-6 rounded-md border border-green-500/40 bg-green-500/10 p-3 text-sm text-green-700">
          {successMsg}
        </div>
      ) : null}

      <Card className="p-4">
        <div className="space-y-4">
          {PROVIDERS.map((p) => {
            const existing = keyMap.get(p.id);
            const isAdding = addingFor === p.id;

            return (
              <div
                key={p.id}
                className="flex items-center justify-between rounded-lg border p-4"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Key size={14} className="text-muted-foreground" />
                    <span className="text-sm font-medium">{p.label}</span>
                    {existing ? (
                      <Badge tone="success">configured</Badge>
                    ) : (
                      <Badge tone="neutral">no key</Badge>
                    )}
                  </div>
                  {existing ? (
                    <div className="mt-1 text-xs text-muted-foreground">
                      {existing.key_prefix}
                    </div>
                  ) : (
                    <a
                      href={p.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-1 inline-block text-xs text-purple-400 hover:underline"
                    >
                      Get a key &rarr;
                    </a>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {isAdding ? (
                    <div className="flex items-center gap-2">
                      <div className="relative">
                        <Input
                          type={showKey ? "text" : "password"}
                          placeholder="sk-..."
                          value={keyValue}
                          onChange={(e) => setKeyValue(e.target.value)}
                          className="w-56 text-xs"
                          autoFocus
                        />
                        <button
                          type="button"
                          onClick={() => setShowKey(!showKey)}
                          className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        >
                          {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
                        </button>
                      </div>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleSave(p.id)}
                        disabled={saving || !keyValue.trim()}
                      >
                        {saving ? "Saving..." : "Save"}
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => { setAddingFor(null); setKeyValue(""); }}
                      >
                        Cancel
                      </Button>
                    </div>
                  ) : existing ? (
                    <>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => { setAddingFor(p.id); setKeyValue(""); }}
                      >
                        Update
                      </Button>
                      <button
                        onClick={() => handleDelete(p.id)}
                        className="rounded p-1.5 text-red-500 hover:bg-red-500/10"
                      >
                        <Trash2 size={14} />
                      </button>
                    </>
                  ) : (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => { setAddingFor(p.id); setKeyValue(""); }}
                    >
                      Add Key
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      <p className="mt-4 text-xs text-muted-foreground">
        Your keys are encrypted at rest using the server&apos;s encryption key and are never
        shared. When a provider key is configured, it takes priority over the server&apos;s
        shared key for LLM calls.
      </p>
    </div>
  );
}
