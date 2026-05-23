/**
 * LLM gateway client — talks to /api/v1/llm/*.
 * Higgsfield-style: users pick a model from the catalog; API keys live
 * server-side and are never collected from the browser.
 */
import useSWR, { mutate } from "swr";

const API_BASE =
  typeof window === "undefined"
    ? (process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000") + "/api/v1"
    : "/api/proxy";

export type Capability = "chat" | "image" | "video" | "embedding";
export type Tier = "free" | "pro" | "team";

export interface ModelEntry {
  id: string;
  provider: string;
  model: string;
  display_name: string;
  capability: Capability;
  description: string;
  context_window: number | null;
  max_output_tokens: number | null;
  input_price_per_1k: number;
  output_price_per_1k: number;
  price_per_image: number | null;
  price_per_second: number | null;
  tier: Tier;
  is_default: boolean;
  supports_streaming: boolean;
  supports_json_mode: boolean;
  supports_vision: boolean;
  available: boolean;
  tags: string[];
}

export interface CatalogResponse {
  models: ModelEntry[];
  defaults: { chat: string | null; image: string | null; video: string | null };
}

export interface WorkspacePrefs {
  workspace_id: string;
  default_chat_model: string | null;
  default_image_model: string | null;
  default_video_model: string | null;
}

export interface CompleteResult {
  text: string;
  model: string;
  provider: string;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  cost_usd: number | null;
}

export interface ImageGenItem {
  s3_key: string;
  width: number;
  height: number;
  source_url?: string | null;
}

export interface ImageGenResult {
  images: ImageGenItem[];
  model: string;
  provider: string;
  cost_usd: number | null;
}

async function jsonFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const llmApi = {
  catalog: (params?: { capability?: Capability; availableOnly?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.capability) q.set("capability", params.capability);
    if (params?.availableOnly) q.set("available_only", "true");
    const qs = q.toString();
    return jsonFetch<CatalogResponse>(`/llm/models${qs ? `?${qs}` : ""}`);
  },
  preferences: () => jsonFetch<WorkspacePrefs>("/llm/preferences"),
  updatePreferences: (prefs: Partial<Omit<WorkspacePrefs, "workspace_id">>) =>
    jsonFetch<WorkspacePrefs>("/llm/preferences", {
      method: "PUT",
      body: JSON.stringify(prefs),
    }),
  complete: (payload: {
    model?: string | null;
    prompt?: string;
    messages?: Array<{ role: "system" | "user" | "assistant"; content: string }>;
    system?: string;
    temperature?: number;
    max_tokens?: number;
    json_mode?: boolean;
  }) =>
    jsonFetch<CompleteResult>("/llm/complete", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  images: (payload: {
    model?: string | null;
    prompt: string;
    size?: string;
    quality?: string;
    n?: number;
  }) =>
    jsonFetch<ImageGenResult>("/llm/images", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  /**
   * Stream a chat completion via SSE. Yields text deltas.
   * Aborts when the returned controller is aborted.
   */
  stream: async function* (
    payload: {
      model?: string | null;
      prompt?: string;
      messages?: Array<{ role: string; content: string }>;
      system?: string;
      temperature?: number;
      max_tokens?: number;
    },
    signal?: AbortSignal,
  ): AsyncGenerator<string, void, void> {
    const res = await fetch(`${API_BASE}/llm/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    });
    if (!res.ok || !res.body) {
      throw new Error(`stream failed: ${res.status} ${res.statusText}`);
    }
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop() ?? "";
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const data = line.slice(6);
        if (data === "[DONE]") return;
        try {
          const parsed = JSON.parse(data);
          if (parsed.delta) yield parsed.delta as string;
          if (parsed.error) throw new Error(parsed.error as string);
        } catch {
          // ignore malformed frame
        }
      }
    }
  },
};

/* ------------------ SWR hooks ------------------ */

export function useModelCatalog(capability?: Capability) {
  return useSWR<CatalogResponse>(
    ["llm/models", capability ?? "all"],
    () => llmApi.catalog({ capability }),
    { revalidateOnFocus: false },
  );
}

export function useWorkspacePrefs() {
  return useSWR<WorkspacePrefs>("llm/preferences", () => llmApi.preferences(), {
    revalidateOnFocus: false,
  });
}

export async function setDefaultModel(
  capability: Capability,
  modelId: string | null,
): Promise<WorkspacePrefs> {
  const payload: Partial<Omit<WorkspacePrefs, "workspace_id">> = {};
  if (capability === "chat") payload.default_chat_model = modelId;
  if (capability === "image") payload.default_image_model = modelId;
  if (capability === "video") payload.default_video_model = modelId;
  const next = await llmApi.updatePreferences(payload);
  await mutate("llm/preferences", next, { revalidate: false });
  return next;
}

/* ------------------ Formatting helpers ------------------ */

export function formatCost(usd: number | null | undefined): string {
  if (usd == null) return "—";
  if (usd < 0.01) return `$${usd.toFixed(4)}`;
  if (usd < 1) return `$${usd.toFixed(3)}`;
  return `$${usd.toFixed(2)}`;
}

export function modelPriceLabel(m: ModelEntry): string {
  if (m.capability === "chat") {
    return `$${m.input_price_per_1k.toFixed(4)} / $${m.output_price_per_1k.toFixed(4)} per 1k`;
  }
  if (m.capability === "image" && m.price_per_image != null) {
    return `${formatCost(m.price_per_image)} / image`;
  }
  if (m.capability === "video" && m.price_per_second != null) {
    return `${formatCost(m.price_per_second)} / sec`;
  }
  return "—";
}
