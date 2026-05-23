/**
 * Helix REST API client.
 *
 * In the browser we go through Next.js rewrites (`/api/proxy/...`) so that
 * CORS is transparent. On the server (RSC / route handlers) we hit the API
 * directly via NEXT_PUBLIC_API_BASE.
 */
import type { paths } from "@helix/types";

const API_BASE =
  typeof window === "undefined"
    ? (process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000") + "/api/v1"
    : "/api/proxy";

export class ApiError extends Error {
  constructor(public status: number, message: string, public body?: unknown) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    cache: "no-store",
    credentials: "include",
  });
  if (!res.ok) {
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      body = await res.text();
    }
    throw new ApiError(res.status, `${res.status} ${res.statusText}`, body);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

/* ---------- Types ---------- */

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Brand {
  id: string;
  name: string;
  slug?: string | null;
  workspace_id?: string | null;
  created_at?: string;
  category?: string | null;
  tagline?: string | null;
  mission?: string | null;
  story?: string | null;
  target_audience?: Record<string, any>;
  voice_attributes?: Record<string, any>;
  positioning?: string | null;
  archetype?: string | null;
  design_school?: string | null;
  status?: string;
  metadata?: Record<string, any>;
}

export interface RunCreate {
  workflow: string;
  brand_id: string;
  inputs?: Record<string, unknown>;
  config?: Record<string, unknown>;
}

export interface RunSummary {
  id: string;
  workflow: string;
  brand_id: string;
  status: string;
  created_at: string;
  completed_at?: string | null;
  error?: string | null;
}

export interface RunDetail extends RunSummary {
  state?: Record<string, unknown>;
  inputs?: Record<string, unknown>;
  config?: Record<string, unknown>;
  output?: Record<string, unknown>;
}

export interface IntegrationProvider {
  key: string;
  display_name: string;
  scopes: string[];
  auth_kind: string;
  configured: boolean;
  connected: boolean;
  category?: string;
  icon?: string;
  description?: string;
  token_label?: string | null;
  token_help_url?: string | null;
  coming_soon?: boolean;
}

export interface IntegrationConnection {
  id: string;
  workspace_id: string;
  provider: string;
  auth_kind: string;
  account_label?: string | null;
  scopes: string[];
  enabled: boolean;
  expires_at?: string | null;
  created_at?: string | null;
}

export interface IntegrationsCatalog {
  providers: IntegrationProvider[];
  connections: IntegrationConnection[];
}

export interface SkillSummary {
  id: string;
  name: string;
  version: string;
  description?: string | null;
  tags: string[];
  trigger_phrases: string[];
  required_tools: string[];
  dependencies: string[];
  enabled: boolean;
  is_stub: boolean;
  usage_count: number;
  success_count: number;
  success_rate?: number | null;
  created_at?: string | null;
}

export interface SkillLearning {
  id: string;
  skill_id: string;
  workflow_run_id?: string | null;
  brand_id?: string | null;
  trigger_context?: string | null;
  prompt_delta?: string | null;
  success_markers: Record<string, unknown>;
  score?: number | null;
  applied_count: number;
  enabled: boolean;
  created_at?: string | null;
  skill_name?: string;
}

export interface SkillsCatalog {
  summary: { total: number; active: number; stubs: number };
  items: SkillSummary[];
}

export interface SkillDetail {
  skill: SkillSummary;
  learnings: SkillLearning[];
}

export interface BrandMemory {
  context: Record<string, unknown> & {
    name?: string;
    palette?: Record<string, unknown>;
    typography?: Record<string, unknown>;
    logos?: Array<Record<string, unknown>>;
    recent_assets?: Array<Record<string, unknown>>;
  };
  counts: {
    runs: number;
    assets: number;
    brand_assets: number;
    learnings: number;
  };
  asset_kinds: Array<{ kind: string; count: number }>;
}

export interface TimelineEvent {
  type: "run" | "asset" | "learning";
  id: string;
  title: string;
  at?: string | null;
  status?: string;
  kind?: string;
}

export interface AssetItem {
  id: string;
  brand_id?: string | null;
  workflow_run_id?: string | null;
  kind: string;
  mime_type?: string | null;
  s3_key?: string | null;
  width?: number | null;
  height?: number | null;
  metadata: Record<string, unknown>;
  created_at?: string | null;
}

/* ---------- Endpoints ---------- */

export interface AuthUser {
  id: string;
  email: string;
  name?: string | null;
  role: string;
  picture?: string | null;
  organization_id: string;
}

export interface AuthStatus {
  authenticated: boolean;
  provider?: string | null;
  user?: AuthUser | null;
}

export const api = {
  auth: {
    me: () => request<AuthStatus>("/auth/me"),
    providers: () =>
      request<{ google: { enabled: boolean; label: string } }>(
        "/auth/providers",
      ),
    googleStart: (returnTo: string = "/") =>
      request<{ url: string }>(
        `/auth/google/start?return_to=${encodeURIComponent(returnTo)}`,
      ),
    logout: () => request<{ ok: boolean }>("/auth/logout", { method: "POST" }),
    devBypass: (email: string, name: string) =>
      request<{ ok: boolean; user_id: string }>("/auth/dev-bypass", {
        method: "POST",
        body: JSON.stringify({ email, name }),
      }),
  },
  brands: {
    list: () =>
      request<Page<Brand>>("/brands").then((p) => p.items),
    get: (id: string) => request<Brand>(`/brands/${id}`),
    create: (b: Partial<Brand>) =>
      request<Brand>("/brands", { method: "POST", body: JSON.stringify(b) }),
  },
  runs: {
    list: (params?: { brand_id?: string; limit?: number }) => {
      const q = new URLSearchParams();
      if (params?.brand_id) q.set("brand_id", params.brand_id);
      if (params?.limit) q.set("limit", String(params.limit));
      const qs = q.toString();
      return request<Page<RunSummary>>(`/runs${qs ? `?${qs}` : ""}`).then(
        (p) => p.items,
      );
    },
    get: (id: string) => request<RunDetail>(`/runs/${id}`),
    create: (payload: RunCreate) =>
      request<RunDetail>("/runs", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },
  integrations: {
    list: (workspaceId: string) =>
      request<IntegrationsCatalog>(
        `/integrations?workspace_id=${encodeURIComponent(workspaceId)}`,
      ),
    connect: (provider: string, workspaceId: string, returnTo?: string) => {
      const q = new URLSearchParams({ workspace_id: workspaceId });
      if (returnTo) q.set("return_to", returnTo);
      return request<{ authorize_url: string; state: string; redirect_uri: string }>(
        `/integrations/${provider}/connect?${q.toString()}`,
      );
    },
    connectToken: (
      provider: string,
      workspaceId: string,
      payload: { token: string; account_label?: string; extra?: Record<string, unknown> },
    ) =>
      request<{
        ok: boolean;
        verified: boolean;
        verify_error?: string | null;
        connection: IntegrationConnection;
      }>(
        `/integrations/${provider}/connect/token?workspace_id=${encodeURIComponent(workspaceId)}`,
        { method: "POST", body: JSON.stringify(payload) },
      ),
    disconnect: (provider: string, workspaceId: string) =>
      request<void>(
        `/integrations/${provider}?workspace_id=${encodeURIComponent(workspaceId)}`,
        { method: "DELETE" },
      ),
  },
  telegram: {
    status: (workspaceId: string) =>
      request<{
        connected: boolean;
        bot?: Record<string, unknown> | null;
        webhook?: Record<string, unknown> | null;
      }>(`/telegram/status?workspace_id=${encodeURIComponent(workspaceId)}`),
    registerWebhook: (workspaceId: string, url?: string) =>
      request<{ ok: boolean; webhook_url: string; response: unknown }>(
        "/telegram/register-webhook",
        {
          method: "POST",
          body: JSON.stringify({ workspace_id: workspaceId, url }),
        },
      ),
    send: (workspaceId: string, chatId: number, text: string) =>
      request<{ ok: boolean; response: unknown }>("/telegram/send", {
        method: "POST",
        body: JSON.stringify({ workspace_id: workspaceId, chat_id: chatId, text }),
      }),
  },
  skills: {
    list: (params?: { includeStubs?: boolean; tag?: string }) => {
      const q = new URLSearchParams();
      if (params?.includeStubs === false) q.set("include_stubs", "false");
      if (params?.tag) q.set("tag", params.tag);
      const qs = q.toString();
      return request<SkillsCatalog>(`/skills${qs ? `?${qs}` : ""}`);
    },
    get: (name: string) =>
      request<SkillDetail>(`/skills/${encodeURIComponent(name)}`),
    toggle: (name: string, enabled: boolean) =>
      request<SkillSummary>(
        `/skills/${encodeURIComponent(name)}?enabled=${enabled}`,
        { method: "PATCH" },
      ),
    toggleLearning: (id: string, enabled: boolean) =>
      request<SkillLearning>(
        `/skills/learnings/${id}?enabled=${enabled}`,
        { method: "PATCH" },
      ),
    deleteLearning: (id: string) =>
      request<void>(`/skills/learnings/${id}`, { method: "DELETE" }),
    recentLearnings: (params?: { limit?: number; brand_id?: string }) => {
      const q = new URLSearchParams();
      if (params?.limit) q.set("limit", String(params.limit));
      if (params?.brand_id) q.set("brand_id", params.brand_id);
      const qs = q.toString();
      return request<SkillLearning[]>(
        `/skills/learnings/recent${qs ? `?${qs}` : ""}`,
      );
    },
  },
  memory: {
    brand: (brandId: string) =>
      request<BrandMemory>(`/memory/brands/${brandId}`),
    timeline: (brandId: string, limit = 100) =>
      request<TimelineEvent[]>(
        `/memory/brands/${brandId}/timeline?limit=${limit}`,
      ),
    graph: (brandId: string, depth = 2) =>
      request<{ nodes: any[]; edges: any[] }>(`/memory/brands/${brandId}/graph?depth=${depth}`),
  },
  assets: {
    list: (params?: {
      brand_id?: string;
      workflow_run_id?: string;
      kind?: string;
      limit?: number;
      offset?: number;
    }) => {
      const q = new URLSearchParams();
      if (params?.brand_id) q.set("brand_id", params.brand_id);
      if (params?.workflow_run_id) q.set("workflow_run_id", params.workflow_run_id);
      if (params?.kind) q.set("kind", params.kind);
      if (params?.limit) q.set("limit", String(params.limit));
      if (params?.offset) q.set("offset", String(params.offset));
      const qs = q.toString();
      return request<AssetItem[]>(`/assets${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => request<AssetItem>(`/assets/${id}`),
    url: (id: string) => request<{ url: string }>(`/assets/${id}/url`),
    thumbnail: (id: string) => request<{ url: string }>(`/assets/${id}/thumbnail`),
  },
  workflows: {
    graph: (sliceName: string) =>
      request<{ nodes: any[]; edges: any[] }>(`/workflows/${sliceName}/graph`),
  },
  billing: {
    plans: () =>
      request<{
        plans: BillingPlan[];
        stripe_configured: boolean;
        publishable_key: string | null;
      }>("/billing/plans"),
    subscription: () => request<SubscriptionStatus>("/billing/subscription"),
    checkout: (payload: {
      plan: string;
      success_url?: string;
      cancel_url?: string;
    }) =>
      request<{ url: string }>("/billing/checkout", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    portal: () =>
      request<{ url: string }>("/billing/portal", { method: "POST" }),
  },
};

export interface BillingPlan {
  id: string;
  name: string;
  description: string;
  amount: number;
  currency: string;
  interval: string;
  features: string[];
  limits: Record<string, number | string>;
  highlight: boolean;
  price_id: string | null;
  available: boolean;
}

export interface SubscriptionStatus {
  plan: string;
  status: string;
  cancel_at_period_end: boolean;
  current_period_end?: string | null;
  stripe_customer_id?: string | null;
  has_active_subscription: boolean;
  publishable_key?: string | null;
}

export const WS_BASE =
  process.env.NEXT_PUBLIC_WS_BASE ?? "ws://localhost:8000";

export function runStreamUrl(runId: string): string {
  return `${WS_BASE}/api/v1/runs/${runId}/stream`;
}
