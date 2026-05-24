"use client";

import { useCallback, useRef, useState } from "react";
import useSWR from "swr";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";

export default function ApiKeysPage() {
  const { data: auth } = useSWR("auth-me", () => api.auth.me());
  const { data: keys, mutate: refreshKeys } = useSWR(
    auth?.authenticated ? "api-keys" : null,
    () => api.enterprise.apiKeys(),
  );

  const [keyName, setKeyName] = useState("");
  const [creating, setCreating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [newKey, setNewKey] = useState<string | null>(null);
  const newKeyRef = useRef<HTMLTextAreaElement>(null);

  const handleCreate = useCallback(async () => {
    if (!keyName) return;
    setErrorMsg(null);
    setNewKey(null);
    setCreating(true);
    try {
      const key = await api.enterprise.createApiKey({ name: keyName });
      setNewKey(key.raw_key);
      setKeyName("");
      refreshKeys();
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.message : String(err));
    } finally {
      setCreating(false);
    }
  }, [keyName, refreshKeys]);

  const handleDelete = useCallback(async (id: string) => {
    if (!confirm("Revoke this API key? This cannot be undone.")) return;
    try {
      await api.enterprise.deleteApiKey(id);
      refreshKeys();
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.message : String(err));
    }
  }, [refreshKeys]);

  const copyKey = useCallback(() => {
    if (newKey && newKeyRef.current) {
      navigator.clipboard.writeText(newKey);
      newKeyRef.current.select();
    }
  }, [newKey]);

  if (!auth?.authenticated) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="mb-3 text-2xl font-semibold">API Keys</h1>
        <p className="text-muted-foreground">Please sign in to manage API keys.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">API Keys</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage API keys for programmatic access to the Helix API.
        </p>
      </div>

      {errorMsg ? (
        <div className="mb-6 rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-700">{errorMsg}</div>
      ) : null}

      {/* New key banner */}
      {newKey ? (
        <Card className="mb-6 border-green-500/40 bg-green-500/10 p-4">
          <h3 className="mb-2 text-sm font-semibold text-green-700">API Key Created</h3>
          <p className="mb-2 text-xs text-green-600">
            Copy this key now. You will not be able to see it again.
          </p>
          <textarea
            ref={newKeyRef}
            readOnly
            value={newKey}
            className="mb-2 w-full rounded border border-green-500/30 bg-black/10 p-2 font-mono text-xs"
            rows={2}
          />
          <Button onClick={copyKey} variant="primary" size="sm">Copy to Clipboard</Button>
        </Card>
      ) : null}

      {/* Create */}
      <Card className="mb-6 p-4">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">Create API Key</h2>
        <div className="flex gap-2">
          <Input
            placeholder="e.g., CI Pipeline Key"
            value={keyName}
            onChange={(e) => setKeyName(e.target.value)}
            className="flex-1"
          />
          <Button onClick={handleCreate} disabled={creating || !keyName} variant="primary">
            {creating ? "Creating…" : "Create"}
          </Button>
        </div>
      </Card>

      {/* Existing keys */}
      <Card className="p-4">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">Active Keys</h2>
        {!keys || keys.length === 0 ? (
          <p className="text-sm text-muted-foreground">No API keys created yet.</p>
        ) : (
          <div className="space-y-2">
            {keys.map((k) => (
              <div key={k.id} className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{k.name}</span>
                    <span className="font-mono text-xs text-muted-foreground">{k.key_prefix}...</span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Created {new Date(k.created_at!).toLocaleDateString()}
                    {k.last_used_at ? ` · Last used ${new Date(k.last_used_at).toLocaleDateString()}` : " · Never used"}
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(k.id)}
                  className="rounded px-2 py-1 text-xs text-red-500 hover:bg-red-500/10"
                >
                  Revoke
                </button>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
