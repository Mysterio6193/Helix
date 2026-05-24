/**
 * Helix REST API client.
 *
 * In the browser we go through Next.js rewrites (`/api/proxy/...`) so that
 * CORS is transparent. On the server (RSC / route handlers) we hit the API
 * directly via NEXT_PUBLIC_API_BASE.
 */
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

export interface Organization {
  id: string;
  name: string;
  slug: string;
  metadata?: Record<string, any>;
  created_at?: string;
}

export interface Workspace {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description?: string | null;
  settings?: Record<string, any>;
  created_at?: string;
}

export interface AgentSession {
  id: string;
  workspace_id: string;
  brand_id?: string | null;
  agent: string;
  name: string;
  description?: string | null;
  status: string;
  mode: string;
  goal?: string | null;
  config?: Record<string, any>;
  memory?: Record<string, any>;
  heartbeat_interval_s: number;
  last_heartbeat_at?: string | null;
  last_active_at?: string | null;
  error?: string | null;
  created_at?: string;
}

export interface ScheduledJob {
  id: string;
  workspace_id: string;
  session_id?: string | null;
  name: string;
  workflow: string;
  cron?: string | null;
  interval_s?: number | null;
  enabled: boolean;
  next_run_at?: string | null;
  created_at?: string;
}

export interface Trigger {
  id: string;
  workspace_id: string;
  session_id?: string | null;
  name: string;
  source: string;
  event_kind?: string | null;
  workflow: string;
  enabled: boolean;
  created_at?: string;
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
  purpose?: string | null;
  mime_type?: string | null;
  s3_key?: string | null;
  storage_url?: string | null;
  text_content?: string | null;
  width?: number | null;
  height?: number | null;
  metadata: Record<string, unknown>;
  created_at?: string | null;
}

export interface OperatingMetric {
  label: string;
  value: string;
  delta?: string | null;
  tone: "neutral" | "success" | "warning" | "error" | "info" | string;
}

export interface OperatingSystemOverview {
  metrics: OperatingMetric[];
  systems: Array<{
    name: string;
    status: string;
    description: string;
  }>;
  council: Array<{
    name: string;
    mandate: string;
    status: string;
  }>;
  intelligence_layers: Array<{
    name: string;
    description: string;
    status: string;
  }>;
  action_feed: Array<{
    id: string;
    title: string;
    status: string;
    timestamp?: string | null;
    detail?: string | null;
  }>;
  event_triggers: Array<{
    id: string;
    name: string;
    event_kind?: string | null;
    workflow: string;
    enabled: boolean;
    fire_count: number;
    last_fired_at?: string | null;
  }>;
  automation_coverage: Record<string, number>;
}

export interface OperatingSystemBootstrapResult {
  ok: boolean;
  workspace_id: string;
  created: Record<"agents" | "triggers" | "schedules", number>;
  existing: Record<"agents" | "triggers" | "schedules", number>;
  agents: string[];
  triggers: string[];
  schedules: string[];
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
const isSandbox = () => typeof window !== "undefined" && localStorage.getItem("helix_sandbox_session") === "true";

const MOCK_WORKSPACE = [
  {
    id: "sandbox-workspace",
    organization_id: "sandbox-org",
    name: "Sandbox Workspace",
    slug: "sandbox-workspace",
    description: "Explore Helix without backend constraints"
  }
];

const MOCK_BRANDS = [
  {
    id: "mock-brand-1",
    name: "Slice & Dice Co.",
    slug: "slice-dice",
    category: "Pizza & Pasta",
    tagline: "Crafted pizzas, composed precisely.",
    status: "active"
  },
  {
    id: "mock-brand-2",
    name: "Bento Junction",
    slug: "bento-junction",
    category: "Japanese Fast-Casual",
    tagline: "Traditional boxes, modern speeds.",
    status: "active"
  }
];

const MOCK_RUNS = [
  {
    id: "mock-run-1",
    workflow: "Brand Identity Generation",
    brand_id: "mock-brand-1",
    status: "completed",
    created_at: "2026-05-24T10:00:00Z",
    completed_at: "2026-05-24T10:02:15Z"
  },
  {
    id: "mock-run-2",
    workflow: "Packaging Artwork Generator",
    brand_id: "mock-brand-1",
    status: "completed",
    created_at: "2026-05-24T11:30:00Z",
    completed_at: "2026-05-24T11:31:45Z"
  },
  {
    id: "mock-run-3",
    workflow: "Next.js Site & Deploy",
    brand_id: "mock-brand-2",
    status: "completed",
    created_at: "2026-05-24T12:00:00Z",
    completed_at: "2026-05-24T12:05:12Z"
  }
];

const MOCK_ASSETS = [
  {
    id: "mock-asset-1",
    brand_id: "mock-brand-1",
    kind: "logo",
    purpose: "Primary Brand Logo",
    mime_type: "image/png",
    storage_url: "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&q=80",
    metadata: { width: 512, height: 512 },
    created_at: "2026-05-24T10:01:00Z"
  },
  {
    id: "mock-asset-2",
    brand_id: "mock-brand-1",
    kind: "packaging",
    purpose: "Pizza Box Lid Label",
    mime_type: "image/png",
    storage_url: "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&q=80",
    metadata: { width: 1024, height: 1024 },
    created_at: "2026-05-24T11:31:00Z"
  },
  {
    id: "mock-asset-3",
    brand_id: "mock-brand-2",
    kind: "website",
    purpose: "Next.js Scaffold Preview",
    mime_type: "image/png",
    storage_url: "https://images.unsplash.com/photo-1531403009284-440f080d1e12?w=400&q=80",
    metadata: { width: 1280, height: 800 },
    created_at: "2026-05-24T12:04:00Z"
  }
];

const MOCK_OPERATING_SYSTEM_OVERVIEW = {
  metrics: [
    { label: "Active Brands", value: "2", delta: "+1 this week", tone: "success" },
    { label: "Workflow Success", value: "98.4%", delta: "+2.1%", tone: "success" },
    { label: "Total Generation Cost", value: "$12.45", delta: null, tone: "neutral" }
  ],
  systems: [
    { name: "Celery Workflows", status: "online", description: "Durable task runner for multi-step jobs." },
    { name: "Postgres SQL", status: "online", description: "Relational storage for brands, runs, and memories." },
    { name: "Redis Memory", status: "online", description: "Key-value broker for live pub/sub sync." }
  ],
  council: [
    { name: "Design Critic Agent", mandate: "Visual quality control & contrast assurance.", status: "active" },
    { name: "Copy Alignment Agent", mandate: "Brand voice consistency & vocabulary control.", status: "active" },
    { name: "SEO Placement Agent", mandate: "Metadata correctness & viewport performance.", status: "active" }
  ],
  intelligence_layers: [
    { name: "Brand Memory Store", description: "Compound vector store that stores past iterations.", status: "active" },
    { name: "LLM Router Hub", description: "Low-latency streaming switchboard for provider APIs.", status: "active" }
  ],
  action_feed: [
    { id: "mock-act-1", title: "Bento Junction site deployed to Vercel production alias", status: "success", detail: "Deployed in 54s with 0 errors" },
    { id: "mock-act-2", title: "Slice & Dice Co. pizza box artwork finalized", status: "success", detail: "Exported print-ready bleed PDF" }
  ],
  event_triggers: [],
  automation_coverage: {}
};

export const api = {
  get: <T = any>(path: string) => request<T>(path),
  post: <T = any>(path: string, body?: any) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  delete: <T = any>(path: string) =>
    request<T>(path, { method: "DELETE" }),
  operatingSystem: {
    overview: () =>
      request<OperatingSystemOverview>("/operating-system/overview").catch((err) => {
        if (isSandbox()) return MOCK_OPERATING_SYSTEM_OVERVIEW as any;
        throw err;
      }),
    bootstrap: (payload: { workspace_id?: string | null } = {}) =>
      request<OperatingSystemBootstrapResult>("/operating-system/bootstrap", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },
  auth: {
    me: () => request<AuthStatus>("/auth/me").catch((err) => {
      if (isSandbox()) {
        return {
          authenticated: true,
          provider: "dev-bypass",
          user: {
            id: "sandbox-user",
            email: (typeof window !== "undefined" && localStorage.getItem("helix_sandbox_email")) || "sandbox@helix.app",
            name: (typeof window !== "undefined" && localStorage.getItem("helix_sandbox_name")) || "Sandbox Explorer",
            role: "owner",
            picture: null,
            organization_id: "sandbox-org",
          },
        };
      }
      throw err;
    }),
    providers: () =>
      request<{ google: { enabled: boolean; label: string } }>(
        "/auth/providers",
      ),
    googleStart: (returnTo: string = "/") =>
      request<{ url: string }>(
        `/auth/google/start?return_to=${encodeURIComponent(returnTo)}`,
      ),
    logout: () => request<{ ok: boolean }>("/auth/logout", { method: "POST" })
      .then((res) => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("helix_sandbox_session");
          localStorage.removeItem("helix_sandbox_email");
          localStorage.removeItem("helix_sandbox_name");
        }
        return res;
      })
      .catch((err) => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("helix_sandbox_session");
          localStorage.removeItem("helix_sandbox_email");
          localStorage.removeItem("helix_sandbox_name");
          return { ok: true };
        }
        throw err;
      }),
    devBypass: (email: string, name: string) =>
      request<{ ok: boolean; user_id: string }>("/auth/dev-bypass", {
        method: "POST",
        body: JSON.stringify({ email, name }),
      }).then((res) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("helix_sandbox_session", "true");
          localStorage.setItem("helix_sandbox_email", email);
          localStorage.setItem("helix_sandbox_name", name);
        }
        return res;
      }).catch((err) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("helix_sandbox_session", "true");
          localStorage.setItem("helix_sandbox_email", email);
          localStorage.setItem("helix_sandbox_name", name);
          return { ok: true, user_id: "sandbox-user" };
        }
        throw err;
      }),
  },
  organizations: {
    me: () => request<Organization>("/organizations/me"),
    get: (id: string) => request<Organization>(`/organizations/${id}`),
  },
  workspaces: {
    list: () =>
      request<Page<Workspace>>("/workspaces").then((p) => p.items).catch((err) => {
        if (isSandbox()) return MOCK_WORKSPACE as any;
        throw err;
      }),
    get: (id: string) => request<Workspace>(`/workspaces/${id}`),
    create: (w: Partial<Workspace>) =>
      request<Workspace>("/workspaces", { method: "POST", body: JSON.stringify(w) }),
    update: (id: string, w: Partial<Workspace>) =>
      request<Workspace>(`/workspaces/${id}`, { method: "PATCH", body: JSON.stringify(w) }),
    delete: (id: string) => request<void>(`/workspaces/${id}`, { method: "DELETE" }),
  },
  sessions: {
    list: (params?: { workspace_id?: string; limit?: number }) => {
      const q = new URLSearchParams();
      if (params?.workspace_id) q.set("workspace_id", params.workspace_id);
      if (params?.limit) q.set("limit", String(params.limit));
      const qs = q.toString();
      return request<Page<AgentSession>>(`/agent-sessions${qs ? `?${qs}` : ""}`).then(p => p.items);
    },
    get: (id: string) => request<AgentSession>(`/agent-sessions/${id}`),
    create: (payload: Partial<AgentSession>) =>
      request<AgentSession>("/agent-sessions", { method: "POST", body: JSON.stringify(payload) }),
    update: (id: string, payload: Partial<AgentSession>) =>
      request<AgentSession>(`/agent-sessions/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
    delete: (id: string) => request<void>(`/agent-sessions/${id}`, { method: "DELETE" }),
  },
  brands: {
    list: () =>
      request<Page<Brand>>("/brands").then((p) => p.items).catch((err) => {
        if (isSandbox()) return MOCK_BRANDS as any;
        throw err;
      }),
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
      ).catch((err) => {
        if (isSandbox()) return MOCK_RUNS as any;
        throw err;
      });
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
    health: (workspaceId: string) =>
      request<{
        checked: number;
        healthy: number;
        expired: number;
        error: number;
        results: Array<{
          provider: string;
          account_label?: string | null;
          status: string;
          message?: string | null;
        }>;
        checked_at: string;
      }>(`/integrations/health?workspace_id=${encodeURIComponent(workspaceId)}`),
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
  events: {
    publish: (payload: {
      workspace_id: string;
      brand_id?: string | null;
      event_kind: string;
      payload: Record<string, any>;
    }) =>
      request<{ ok: boolean; event_kind: string; triggered_runs_count: number }>("/events", {
        method: "POST",
        body: JSON.stringify(payload),
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
      return request<AssetItem[]>(`/assets${qs ? `?${qs}` : ""}`).catch((err) => {
        if (isSandbox()) return MOCK_ASSETS as any;
        throw err;
      });
    },
    get: (id: string) => request<AssetItem>(`/assets/${id}`),
    url: (id: string) => request<{ url: string }>(`/assets/${id}/url`),
    thumbnail: (id: string) => request<{ url: string }>(`/assets/${id}/thumbnail`),
  },
  workflows: {
    graph: (workflowName: string) =>
      request<{ nodes: any[]; edges: any[] }>(`/workflows/${workflowName}/graph`),
  },
  revenue: {
    overview: () =>
      request<{
        current_revenue: { daily: number; weekly: number; monthly: number; yoy_change: number };
        roas: { current: number; target: number; trend: string };
        cac: { current: number; trend: string; by_channel: any[] };
        ltv: { current: number; predicted_12m: number };
        margin: { gross: number; net: number };
        anomalies: any[];
        predictions: { next_30_days: number[]; confidence: number };
        by_channel: any[];
      }>("/intelligence/revenue/overview"),
    metrics: (params?: { platform?: string; metric_type?: string; days?: number }) => {
      const q = new URLSearchParams();
      if (params?.platform) q.set("platform", params.platform);
      if (params?.metric_type) q.set("metric_type", params.metric_type);
      if (params?.days) q.set("days", String(params.days));
      const qs = q.toString();
      return request<any[]>(`/intelligence/revenue/metrics${qs ? `?${qs}` : ""}`);
    },
  },
  customers: {
    segments: () =>
      request<{
        segments: any[];
        cohorts: Record<string, any>;
        rfm_distribution: Record<string, number>;
      }>("/intelligence/customers/segments"),
    compute: (brandId: string) =>
      request<any>("/intelligence/customers/compute-segments", {
        method: "POST",
        body: JSON.stringify({ brand_id: brandId }),
      }),
  },
  competitors: {
    list: () =>
      request<{ competitors: any[]; alerts: any[] }>("/intelligence/competitors"),
    track: (domain: string, name?: string) =>
      request<any>(`/intelligence/competitors/track?domain=${encodeURIComponent(domain)}${name ? `&name=${encodeURIComponent(name)}` : ""}`, { method: "POST" }),
  },
  signals: {
    list: (params?: { layer?: string; severity?: string; limit?: number }) => {
      const q = new URLSearchParams();
      if (params?.layer) q.set("layer", params.layer);
      if (params?.severity) q.set("severity", params.severity);
      if (params?.limit) q.set("limit", String(params.limit));
      const qs = q.toString();
      return request<{ signals: any[]; unread_count: number }>(`/intelligence/signals${qs ? `?${qs}` : ""}`);
    },
    acknowledge: (id: string) =>
      request<any>(`/intelligence/signals/${id}/acknowledge`, { method: "POST" }),
    dismiss: (id: string) =>
      request<any>(`/intelligence/signals/${id}/dismiss`, { method: "POST" }),
  },
  experiments: {
    list: (params?: { status?: string; limit?: number }) => {
      const q = new URLSearchParams();
      if (params?.status) q.set("status", params.status);
      if (params?.limit) q.set("limit", String(params.limit));
      const qs = q.toString();
      return request<any[]>(`/intelligence/experiments${qs ? `?${qs}` : ""}`);
    },
    experiments: () =>
      request<any[]>("/intelligence/experiments"),
    experiment: (id: string) =>
      request<any>(`/intelligence/experiments/${id}`),
    createExperiment: (payload: any) =>
      request<any>("/intelligence/experiments", { method: "POST", body: JSON.stringify(payload) }),
    startExperiment: (id: string) =>
      request<any>(`/intelligence/experiments/${id}/start`, { method: "POST" }),
    stopExperiment: (id: string) =>
      request<any>(`/intelligence/experiments/${id}/stop`, { method: "POST" }),
  },
  optimization: {
    rules: () =>
      request<any[]>("/intelligence/optimization/rules"),
    evaluate: (brandId?: string) =>
      request<any>(`/intelligence/optimization/evaluate${brandId ? `?brand_id=${encodeURIComponent(brandId)}` : ""}`, { method: "POST" }),
    approvals: () =>
      request<any[]>("/intelligence/optimization/approvals"),
    approve: (id: string) =>
      request<any>(`/intelligence/optimization/approvals/${id}/approve`, { method: "POST" }),
    reject: (id: string) =>
      request<any>(`/intelligence/optimization/approvals/${id}/reject`, { method: "POST" }),
    history: (limit?: number) =>
      request<any[]>(`/intelligence/optimization/history${limit ? `?limit=${limit}` : ""}`),
  },
  campaigns: {
    health: (brandId: string) =>
      request<any>(`/intelligence/campaigns/health?brand_id=${encodeURIComponent(brandId)}`),
    fatigue: (brandId: string) =>
      request<any[]>(`/intelligence/campaigns/fatigue?brand_id=${encodeURIComponent(brandId)}`),
    optimize: (brandId: string) =>
      request<any[]>(`/intelligence/campaigns/optimize?brand_id=${encodeURIComponent(brandId)}`),
  },
  browser: {
    sessions: () =>
      request<any[]>("/browser/sessions"),
    createSession: (payload: any) =>
      request<any>("/browser/sessions", { method: "POST", body: JSON.stringify(payload) }),
    session: (id: string) =>
      request<any>(`/browser/sessions/${id}`),
    executeAction: (sessionId: string, payload: any) =>
      request<any>(`/browser/sessions/${sessionId}/actions`, { method: "POST", body: JSON.stringify(payload) }),
    closeSession: (id: string) =>
      request<any>(`/browser/sessions/${id}/close`, { method: "POST" }),
    automations: () =>
      request<any[]>("/browser/automations"),
    runAutomation: (id: string) =>
      request<any>(`/browser/automations/${id}/run`, { method: "POST" }),
    replay: (id: string) =>
      request<any>(`/browser/automations/${id}/replay`),
    testTrigger: (title: string, description: string) =>
      request<any>(`/browser/triggers/test?signal_title=${encodeURIComponent(title)}&signal_description=${encodeURIComponent(description)}`, { method: "POST" }),
    templates: () =>
      request<any[]>("/browser/templates"),
  },
  media: {
    jobs: () =>
      request<any[]>("/media/jobs"),
    createJob: (payload: any) =>
      request<any>("/media/jobs", { method: "POST", body: JSON.stringify(payload) }),
    runJob: (id: string) =>
      request<any>(`/media/jobs/${id}/run`, { method: "POST" }),
    cancelJob: (id: string) =>
      request<any>(`/media/jobs/${id}/cancel`, { method: "POST" }),
    templates: () =>
      request<any[]>("/media/templates"),
  },
  llm: {
    catalog: () =>
      request<any>("/llm/models"),
    images: (payload: any) =>
      request<any>("/llm/images", { method: "POST", body: JSON.stringify(payload) }),
    videos: (payload: any) =>
      request<any>("/llm/videos", { method: "POST", body: JSON.stringify(payload) }),
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
    usage: () => request<BillingUsage>("/billing/usage"),
  },
  enterprise: {
    apiKeys: () =>
      request<ApiKeyItem[]>("/api-keys"),
    createApiKey: (payload: { name: string; scopes?: Record<string, any> }) =>
      request<ApiKeyCreated>("/api-keys", { method: "POST", body: JSON.stringify(payload) }),
    deleteApiKey: (id: string) =>
      request<void>(`/api-keys/${id}`, { method: "DELETE" }),
    auditLogs: (params?: { action?: string; resource_type?: string; resource_id?: string; offset?: number; limit?: number }) => {
      const q = new URLSearchParams();
      if (params?.action) q.set("action", params.action);
      if (params?.resource_type) q.set("resource_type", params.resource_type);
      if (params?.resource_id) q.set("resource_id", params.resource_id);
      if (params?.offset) q.set("offset", String(params.offset));
      if (params?.limit) q.set("limit", String(params.limit));
      const qs = q.toString();
      return request<Page<AuditLogEntry>>(`/audit-logs${qs ? `?${qs}` : ""}`);
    },
    members: () =>
      request<OrgMember[]>("/organizations/me/members"),
    updateMemberRole: (memberId: string, payload: { role: string }) =>
      request<OrgMember>(`/organizations/me/members/${memberId}`, { method: "PATCH", body: JSON.stringify(payload) }),
    removeMember: (memberId: string) =>
      request<void>(`/organizations/me/members/${memberId}`, { method: "DELETE" }),
    invitations: () =>
      request<OrgInvitation[]>("/organizations/me/invitations"),
    createInvitation: (payload: { email: string; role?: string }) =>
      request<OrgInvitation>("/organizations/me/invitations", { method: "POST", body: JSON.stringify(payload) }),
    revokeInvitation: (id: string) =>
      request<void>(`/organizations/me/invitations/${id}`, { method: "DELETE" }),
    acceptInvitation: (token: string) =>
      request<{ ok: boolean; organization_id: string }>("/invitations/accept", { method: "POST", body: JSON.stringify({ token }) }),
    usage: () =>
      request<OrgUsage>("/usage"),
    rateLimit: () =>
      request<{ plan: string; requests_per_minute: number }>("/rate-limit"),
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

export interface BillingUsage {
  plan: string;
  period_start: string;
  period_end: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  calls: number;
  call_limit: number | null;
  models: { model_id: string; prompt_tokens: number; completion_tokens: number; cost_usd: number; calls: number }[];
}

/* ---------- Enterprise ---------- */

export interface ApiKeyItem {
  id: string;
  organization_id: string;
  user_id: string;
  name: string;
  key_prefix: string;
  scopes: Record<string, any>;
  enabled: boolean;
  created_at?: string;
  last_used_at?: string;
}

export interface ApiKeyCreated extends ApiKeyItem {
  raw_key: string;
}

export interface AuditLogEntry {
  id: string;
  actor_id?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

export interface OrgMember {
  id: string;
  email: string;
  name?: string;
  role: string;
  created_at: string;
}

export interface OrgInvitation {
  id: string;
  organization_id: string;
  invited_by: string;
  email: string;
  role: string;
  token: string;
  expires_at: string;
  accepted_at?: string;
  revoked_at?: string;
  created_at: string;
}

export interface OrgUsage {
  brands: number;
  brand_limit: number | null;
  runs_this_month: number;
  run_limit: number | null;
  members: number;
  member_limit: number | null;
  api_keys: number;
  api_key_limit: number;
}

export const WS_BASE =
  process.env.NEXT_PUBLIC_WS_BASE ?? "ws://localhost:8000";

export function runStreamUrl(runId: string): string {
  return `${WS_BASE}/api/v1/runs/${runId}/stream`;
}
