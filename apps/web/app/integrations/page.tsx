"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Loader2,
  Plug,
  X,
  Zap,
  Info,
  Lock,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  api,
  type IntegrationConnection,
  type IntegrationProvider,
  type IntegrationsCatalog,
} from "@/lib/api";

const DEFAULT_WORKSPACE = process.env.NEXT_PUBLIC_DEFAULT_WORKSPACE_ID ?? "";

const CATEGORY_LABELS: Record<string, string> = {
  messaging: "Messaging & Chat",
  meta: "Meta Family",
  social: "Social Media",
  restaurant: "Restaurant & Hospitality",
  ecommerce: "E-commerce & Payments",
  marketing: "Marketing & CRM",
  crm: "CRM & Sales",
  support: "Customer Support",
  finance: "Finance & Accounting",
  productivity: "Productivity & Ops",
  analytics: "Analytics & Data",
  design: "Design & Content",
  infrastructure: "Infrastructure & Cloud",
  other: "Other",
};

const CATEGORY_ORDER = [
  "messaging",
  "meta",
  "social",
  "restaurant",
  "ecommerce",
  "marketing",
  "crm",
  "support",
  "finance",
  "productivity",
  "analytics",
  "design",
  "infrastructure",
  "other",
];

// Tool counts per provider (based on available tool adapters)
const TOOL_COUNTS: Record<string, number> = {
  telegram: 1,
  slack: 1,
  discord: 1,
  whatsapp_business: 1,
  meta_pages: 1,
  instagram_business: 1,
  meta_ads: 1,
  threads: 1,
  toast: 1,
  square: 1,
  resy: 1,
  opentable: 1,
  doordash: 1,
  ubereats: 1,
  yelp: 1,
  google_business: 1,
  shopify: 1,
  stripe: 1,
  twilio: 1,
  woocommerce: 1,
  mailchimp: 1,
  klaviyo: 1,
  hubspot: 1,
  sendgrid: 1,
  linkedin: 1,
  twitter: 1,
  tiktok_business: 1,
  youtube: 1,
  pinterest: 1,
  airtable: 1,
  linear: 1,
  asana: 1,
  calendly: 1,
  posthog: 1,
  mixpanel: 1,
  ga4: 1,
  salesforce: 1,
  zendesk: 1,
  intercom: 1,
  jira: 1,
  google_ads: 1,
  snapchat_ads: 1,
  reddit_ads: 1,
  semrush: 1,
  ahrefs: 1,
  paypal: 1,
  quickbooks: 1,
  squarespace: 1,
  wix: 1,
  bigcommerce: 1,
  microsoft_365: 1,
  typeform: 1,
  webflow: 1,
  framer: 1,
  loom: 1,
  segment: 1,
  amplitude: 1,
  google_calendar: 1,
  aws: 1,
  // OAuth providers
  canva: 1,
  figma: 1,
  notion: 1,
  google: 1,
  // POS Systems
  petpooja: 1,
  clover: 1,
  lightspeed: 1,
  revel: 1,
  chownow: 1,
  ordermark: 1,
  slice: 1,
  // Zoho Suite
  zoho_crm: 1,
  zoho_books: 1,
  zoho_campaigns: 1,
  zoho_desk: 1,
  zoho_inventory: 1,
  zoho_subscriptions: 1,
  zoho_projects: 1,
};

function fetcher(workspaceId: string) {
  return api.integrations.list(workspaceId);
}

/* ─── Telegram Webhook Panel ────────────────────────────────── */

function TelegramStatusPanel({ workspaceId }: { workspaceId: string }) {
  const { data, error, mutate, isLoading } = useSWR(
    workspaceId ? ["telegram-status", workspaceId] : null,
    () => api.telegram.status(workspaceId),
    { refreshInterval: 6000 }
  );

  const [activating, setActivating] = useState(false);
  const [msg, setMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  async function activateWebhook() {
    setActivating(true);
    setMsg(null);
    try {
      const res = await api.telegram.registerWebhook(workspaceId);
      if (res.ok) {
        setMsg({ type: "success", text: "Webhook listener activated successfully!" });
        mutate();
      } else {
        setMsg({ type: "error", text: "Failed to register webhook." });
      }
    } catch (e) {
      setMsg({ type: "error", text: e instanceof Error ? e.message : "Activation failed" });
    } finally {
      setActivating(false);
    }
  }

  if (isLoading) {
    return (
      <div className="mt-3 p-3 rounded-lg bg-[rgba(255,255,255,0.01)] border border-[rgba(255,255,255,0.04)] animate-pulse flex items-center justify-center py-4">
        <Loader2 className="size-3.5 animate-spin text-[var(--color-steel)]" />
        <span className="text-micro text-[var(--color-steel)] ml-2">Reading webhook status...</span>
      </div>
    );
  }

  if (error || !data || !data.connected) {
    return null;
  }

  const botName = data.bot?.username 
    ? `@${data.bot.username}` 
    : (data.bot?.first_name as string) || "Telegram Bot";
  const webhookUrl = typeof data.webhook?.url === "string" ? data.webhook.url : null;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-3 p-3.5 rounded-xl bg-[rgba(162,75,255,0.03)] border border-[rgba(162,75,255,0.12)] space-y-2.5 shadow-[0_4px_16px_rgba(0,0,0,0.2)]"
    >
      <div className="flex items-center justify-between gap-2 border-b border-[rgba(255,255,255,0.04)] pb-2">
        <div className="text-micro text-[var(--color-slate)] flex items-center gap-1">
          <Zap className="size-3 text-purple-400" />
          <span>Active Bot</span>
        </div>
        <div className="text-label text-purple-400 font-semibold">{botName}</div>
      </div>
      
      <div className="flex items-center justify-between gap-2">
        <div className="text-micro text-[var(--color-slate)]">Webhook State</div>
        {webhookUrl ? (
          <div className="flex items-center gap-1.5 text-[#00c896]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#00c896] animate-pulse-glow" style={{ boxShadow: "0 0 6px #00c896" }} />
            <span className="text-micro font-medium">Listening</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-amber-400">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            <span className="text-micro font-medium">Not Listening</span>
          </div>
        )}
      </div>

      {webhookUrl && (
        <div className="text-[10px] text-[var(--color-steel)] font-mono break-all bg-[#090a0d] p-2 rounded border border-white/5 select-all">
          {webhookUrl}
        </div>
      )}

      {msg && (
        <div className={`text-micro px-2 py-1.5 rounded border ${
          msg.type === "success" 
            ? "bg-[#00c896]/5 text-[#00c896] border-[#00c896]/20" 
            : "bg-[rgba(255,77,109,0.05)] text-[#ff4d6d] border-[rgba(255,77,109,0.2)]"
        }`}>
          {msg.text}
        </div>
      )}

      {!webhookUrl && (
        <Button 
          variant="glow" 
          size="sm" 
          className="w-full text-xs h-8 cursor-pointer mt-1 font-semibold" 
          disabled={activating}
          onClick={activateWebhook}
        >
          {activating ? "Activating..." : "Activate Webhook Listener"}
        </Button>
      )}
    </motion.div>
  );
}

/* ─── Main Integrations Catalog ─────────────────────────────── */

export default function IntegrationsPage() {
  const [workspaceId, setWorkspaceId] = useState<string>(DEFAULT_WORKSPACE);
  const [banner, setBanner] = useState<{ tone: "ok" | "warn"; text: string } | null>(null);
  const [tokenModal, setTokenModal] = useState<IntegrationProvider | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const qs = new URLSearchParams(window.location.search);
    const connected = qs.get("connected");
    const error = qs.get("error");
    if (connected) setBanner({ tone: "ok", text: `Connected ${connected} successfully.` });
    else if (error) setBanner({ tone: "warn", text: `OAuth error: ${error}` });
    if (connected || error) {
      const url = new URL(window.location.href);
      url.search = "";
      window.history.replaceState({}, "", url.toString());
    }
  }, []);

  useEffect(() => {
    if (workspaceId || typeof window === "undefined") return;
    const fromUrl = new URLSearchParams(window.location.search).get("workspace_id");
    const fromStorage = window.localStorage.getItem("helix.workspace_id");
    const id = fromUrl ?? fromStorage ?? "";
    if (id) setWorkspaceId(id);
  }, [workspaceId]);

  const { data, error, isLoading, mutate } = useSWR<IntegrationsCatalog>(
    workspaceId ? ["integrations", workspaceId] : null,
    () => fetcher(workspaceId),
    { revalidateOnFocus: false },
  );

  const { data: healthData, mutate: mutateHealth } = useSWR(
    workspaceId ? ["integrations-health", workspaceId] : null,
    () => api.integrations.health(workspaceId),
    { revalidateOnFocus: false },
  );

  const healthByProvider = useMemo(() => {
    const map = new Map<string, { status: string; message?: string | null }>();
    healthData?.results?.forEach((r) => map.set(r.provider, { status: r.status, message: r.message }));
    return map;
  }, [healthData]);

  const connectionsByProvider = useMemo(() => {
    const map = new Map<string, IntegrationConnection>();
    (data?.connections ?? []).forEach((c) => map.set(c.provider, c));
    return map;
  }, [data]);

  const grouped = useMemo(() => {
    const groups = new Map<string, IntegrationProvider[]>();
    (data?.providers ?? []).forEach((p) => {
      const cat = p.category ?? "other";
      const list = groups.get(cat) ?? [];
      list.push(p);
      groups.set(cat, list);
    });
    return CATEGORY_ORDER
      .map((cat) => ({ category: cat, items: groups.get(cat) ?? [] }))
      .filter((g) => g.items.length > 0);
  }, [data]);

  const onConnectOAuth = useCallback(
    async (provider: IntegrationProvider) => {
      if (!workspaceId) return;
      try {
        const returnTo =
          typeof window !== "undefined"
            ? `${window.location.origin}/integrations?connected=${provider.key}`
            : undefined;
        const res = await api.integrations.connect(provider.key, workspaceId, returnTo);
        window.location.href = res.authorize_url;
      } catch (e) {
        setBanner({
          tone: "warn",
          text: e instanceof Error ? e.message : "Connect failed",
        });
      }
    },
    [workspaceId],
  );

  const onDisconnect = useCallback(
    async (provider: string) => {
      if (!workspaceId) return;
      try {
        await api.integrations.disconnect(provider, workspaceId);
        setBanner({ tone: "ok", text: `Disconnected ${provider}.` });
        mutate();
      } catch (e) {
        setBanner({
          tone: "warn",
          text: e instanceof Error ? e.message : "Disconnect failed",
        });
      }
    },
    [workspaceId, mutate],
  );

  return (
    <div className="animate-fade-up space-y-8">
      {/* Background gradients */}
      <div className="absolute top-0 right-1/4 w-[500px] h-[500px] rounded-full bg-[rgba(162,75,255,0.03)] blur-[120px] pointer-events-none" />

      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <p className="text-eyebrow" style={{ color: "var(--color-stone)" }}>CREATIVE PIPELINES</p>
          <h1 className="text-display-lg mt-1 tracking-tight" style={{ color: "var(--color-ink)" }}>
            Integrations
          </h1>
          <p className="mt-2 text-body-md max-w-[65ch]" style={{ color: "var(--color-slate)" }}>
            Connect all the tools you use in your restaurant, meta campaigns, messaging clients, and e-commerce stores. Helix securely runs credentials in a sandbox and executes them during active workflows.
          </p>
        </div>
      </header>

      {/* Workspace Requirement Warn Banner */}
      {!workspaceId && (
        <Card className="flex items-start gap-3 p-5 border-[rgba(255,179,71,0.2)] bg-[rgba(255,179,71,0.05)]">
          <AlertTriangle className="mt-0.5 size-5 text-warning shrink-0" />
          <div>
            <h3 className="text-label text-[var(--color-ink)] font-semibold">Active Workspace Required</h3>
            <p className="text-body-sm mt-1 text-[var(--color-slate)]">
              Specify a default workspace or set <code className="rounded bg-[var(--color-muted)] px-1.5 py-0.5 font-mono text-xs">NEXT_PUBLIC_DEFAULT_WORKSPACE_ID</code> in the frontend environment.
            </p>
          </div>
        </Card>
      )}

      {/* Notification Banner */}
      {banner && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`flex items-center justify-between p-4 rounded-xl border ${
            banner.tone === "ok"
              ? "border-[#00c896]/20 bg-[#00c896]/5 text-[#00c896]"
              : "border-[rgba(255,179,71,0.2)] bg-[rgba(255,179,71,0.05)] text-[#ffb347]"
          }`}
        >
          <div className="flex items-center gap-2.5">
            {banner.tone === "ok" ? (
              <CheckCircle2 className="size-4 shrink-0 text-[#00c896]" />
            ) : (
              <AlertTriangle className="size-4 shrink-0 text-[#ffb347]" />
            )}
            <span className="text-body-sm font-medium">{banner.text}</span>
          </div>
          <button
            onClick={() => setBanner(null)}
            className="text-[var(--color-slate)] hover:text-[var(--color-ink)] transition-colors cursor-pointer"
            aria-label="Dismiss"
          >
            <X className="size-4" />
          </button>
        </motion.div>
      )}

      {error && (
        <Card className="border-[rgba(255,77,109,0.2)] bg-[rgba(255,77,109,0.05)] p-5">
          <p className="text-body-sm text-[#ff4d6d]">
            Failed to load integrations: {String((error as Error).message)}
          </p>
        </Card>
      )}

      {isLoading && (
        <div className="flex items-center gap-2 text-body-sm text-[var(--color-slate)] py-12">
          <Loader2 className="size-4 animate-spin text-purple-400" />
          <span>Loading integration catalog...</span>
        </div>
      )}

      {data && (
        <div className="space-y-10">
          {grouped.map(({ category, items }) => (
            <section key={category} className="animate-fade-up">
              <h2 className="text-label mb-4 flex items-center gap-2 font-semibold tracking-wider text-[var(--color-steel)] uppercase">
                <span>{CATEGORY_LABELS[category] ?? category}</span>
                <span className="text-micro font-medium rounded-full bg-[var(--color-muted)] px-2 py-0.5" style={{ color: "var(--color-slate)" }}>
                  {items.length}
                </span>
              </h2>
              
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                {items.map((p) => {
                  const conn = connectionsByProvider.get(p.key);
                  const isToken = p.auth_kind === "token";
                  
                  return (
                    <div 
                      key={p.key} 
                      className="group relative flex flex-col justify-between rounded-2xl border border-[rgba(255,255,255,0.06)] bg-[#13141a]/60 backdrop-blur-md p-5 hover:border-[rgba(255,255,255,0.12)] hover:bg-[#1a1c24]/50 transition-all duration-300 shadow-[0_4px_24px_rgba(0,0,0,0.15)]"
                    >
                      {/* Glow overlay on hover */}
                      <div className="absolute -inset-px rounded-2xl bg-gradient-to-br from-white/5 to-white/0 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

                      <div className="relative space-y-4">
                        {/* Provider details */}
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-start gap-3.5">
                            {p.icon ? (
                              <div
                                className="flex size-10 shrink-0 items-center justify-center rounded-xl text-lg shadow-[0_4px_12px_rgba(0,0,0,0.3)] border border-white/5 bg-zinc-900 group-hover:scale-105 transition-transform"
                                aria-hidden
                              >
                                {p.icon}
                              </div>
                            ) : (
                              <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-zinc-900 border border-white/5">
                                <Plug className="size-5 text-[var(--color-slate)]" />
                              </div>
                            )}
                            <div>
                              <h3 className="text-label text-[var(--color-ink)] font-semibold">{p.display_name}</h3>
                              <p className="text-micro mt-1 text-[var(--color-slate)] leading-relaxed line-clamp-2">
                                {p.description ?? "Compositional API tool."}
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* Status badges */}
                        <div className="flex flex-wrap items-center gap-1.5 pt-1">
                          {conn ? (
                            <span className="bg-[#00c896]/10 text-[#00c896] border border-[#00c896]/20 font-medium px-2.5 py-0.5 text-[10px] rounded-full inline-flex items-center gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-[#00c896] animate-pulse" />
                              Connected
                            </span>
                          ) : p.coming_soon ? (
                            <span className="bg-zinc-800 text-zinc-400 border border-zinc-700/50 font-medium px-2.5 py-0.5 text-[10px] rounded-full">
                              Coming soon
                            </span>
                          ) : isToken ? (
                            <span className="bg-purple-500/10 text-purple-400 border border-purple-500/20 font-medium px-2.5 py-0.5 text-[10px] rounded-full">
                              Token auth
                            </span>
                          ) : p.configured ? (
                            <span className="bg-[#4d7bff]/10 text-[#4d7bff] border border-[#4d7bff]/20 font-medium px-2.5 py-0.5 text-[10px] rounded-full">
                              OAuth Ready
                            </span>
                          ) : (
                            <span className="bg-[rgba(255,179,71,0.08)] text-[#ffb347] border border-[rgba(255,179,71,0.2)] font-medium px-2.5 py-0.5 text-[10px] rounded-full">
                              Not Configured
                            </span>
                          )}
                          {conn?.account_label && (
                            <span className="text-micro bg-zinc-800 text-[var(--color-charcoal)] border border-white/5 rounded-full px-2 py-0.5 text-[10px]">
                              {conn.account_label}
                            </span>
                          )}
                          {/* Tool count */}
                          {TOOL_COUNTS[p.key] && (
                            <span className="text-micro bg-zinc-800/50 text-[var(--color-steel)] border border-white/5 rounded-full px-2 py-0.5 text-[10px]">
                              {TOOL_COUNTS[p.key]} tool{TOOL_COUNTS[p.key] > 1 ? "s" : ""}
                            </span>
                          )}
                          {/* Health status */}
                          {conn && healthByProvider.has(p.key) && (
                            (() => {
                              const h = healthByProvider.get(p.key)!;
                              const isHealthy = h.status === "healthy";
                              return (
                                <span className={`text-micro rounded-full px-2 py-0.5 text-[10px] border inline-flex items-center gap-1 ${
                                  isHealthy
                                    ? "bg-[#00c896]/5 text-[#00c896] border-[#00c896]/15"
                                    : h.status === "expired"
                                    ? "bg-[rgba(255,179,71,0.05)] text-[#ffb347] border-[rgba(255,179,71,0.15)]"
                                    : "bg-[rgba(255,77,109,0.05)] text-[#ff4d6d] border-[rgba(255,77,109,0.15)]"
                                }`}>
                                  <span className={`w-1 h-1 rounded-full ${isHealthy ? "bg-[#00c896]" : h.status === "expired" ? "bg-[#ffb347]" : "bg-[#ff4d6d]"}`} />
                                  {h.status}
                                </span>
                              );
                            })()
                          )}
                        </div>

                        {/* Custom Telegram webhook details once connected */}
                        {p.key === "telegram" && conn && (
                          <TelegramStatusPanel workspaceId={workspaceId} />
                        )}
                      </div>

                      {/* Action buttons */}
                      <div className="relative mt-5 flex flex-wrap items-center gap-2.5 pt-2 border-t border-[rgba(255,255,255,0.04)]">
                        {conn ? (
                          <>
                            <Button
                              variant="secondary"
                              size="sm"
                              className="text-xs h-8 cursor-pointer rounded-lg hover:border-red-500/30 hover:text-red-400"
                              onClick={() => onDisconnect(p.key)}
                            >
                              Disconnect
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              className="text-xs h-8 cursor-pointer rounded-lg"
                              onClick={() => mutateHealth()}
                            >
                              Test Connection
                            </Button>
                          </>
                        ) : p.coming_soon ? (
                          <Button variant="secondary" size="sm" className="text-xs h-8 rounded-lg" disabled>
                            Disabled
                          </Button>
                        ) : isToken ? (
                          <Button
                            variant="primary"
                            size="sm"
                            className="text-xs h-8 cursor-pointer rounded-lg"
                            onClick={() => setTokenModal(p)}
                            disabled={!workspaceId}
                          >
                            Paste Token
                          </Button>
                        ) : (
                          <Button
                            variant="primary"
                            size="sm"
                            className="text-xs h-8 cursor-pointer rounded-lg"
                            onClick={() => onConnectOAuth(p)}
                            disabled={!p.configured || !workspaceId}
                          >
                            Connect Account
                          </Button>
                        )}
                        
                        {p.token_help_url && (
                          <a
                            href={p.token_help_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-micro inline-flex items-center gap-1 text-[var(--color-slate)] hover:text-white transition-colors ml-auto"
                          >
                            <span>Help</span>
                            <ExternalLink className="size-3" />
                          </a>
                        )}
                      </div>

                      {!isToken && !p.configured && !p.coming_soon && (
                        <div className="relative mt-2 flex items-center gap-1 text-[10px] text-[var(--color-stone)] bg-black/20 p-1.5 rounded border border-white/5">
                          <Lock className="size-3 text-[var(--color-stone)]" />
                          <span>Requires <code>{p.key.toUpperCase()}_CLIENT_ID</code> in environment.</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      )}

      {/* Paste Token Modal */}
      <AnimatePresence>
        {tokenModal && workspaceId && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4"
            onClick={() => setTokenModal(null)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[#0d0e12] p-6 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-label-lg text-white font-semibold flex items-center gap-2">
                    <span>Connect {tokenModal.display_name}</span>
                  </h3>
                  <p className="text-body-sm mt-1 text-[var(--color-slate)]">{tokenModal.description}</p>
                </div>
                <button
                  onClick={() => setTokenModal(null)}
                  className="text-[var(--color-slate)] hover:text-white transition-colors cursor-pointer"
                  aria-label="Close"
                >
                  <X className="size-5" />
                </button>
              </div>

              <TokenModalContent
                provider={tokenModal}
                workspaceId={workspaceId}
                onDone={(verified) => {
                  setBanner({
                    tone: verified ? "ok" : "warn",
                    text: verified
                      ? `Connected ${tokenModal.display_name} successfully.`
                      : `Connected ${tokenModal.display_name} (token saved, but validation failed).`,
                  });
                  setTokenModal(null);
                  mutate();
                }}
                onClose={() => setTokenModal(null)}
              />
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

function TokenModalContent({
  provider,
  workspaceId,
  onClose,
  onDone,
}: {
  provider: IntegrationProvider;
  workspaceId: string;
  onClose: () => void;
  onDone: (verified: boolean) => void;
}) {
  const [token, setToken] = useState("");
  const [accountLabel, setAccountLabel] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!token.trim()) {
      setErr("Token is required");
      return;
    }
    setSubmitting(true);
    setErr(null);
    try {
      const res = await api.integrations.connectToken(provider.key, workspaceId, {
        token: token.trim(),
        account_label: accountLabel.trim() || undefined,
      });
      onDone(res.verified);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Connect failed");
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="space-y-3">
        <label className="block">
          <span className="text-label text-[var(--color-slate)] font-medium">
            {provider.token_label ?? "API Token"}
          </span>
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Paste credentials here"
            autoComplete="off"
            spellCheck={false}
            className="mt-1.5 w-full rounded-lg border border-[rgba(255,255,255,0.07)] bg-[#07080a] px-3.5 py-2.5 text-sm font-mono text-white outline-none focus:border-purple-500/80 transition-all"
            required
          />
        </label>

        <label className="block">
          <span className="text-label text-[var(--color-slate)] font-medium">Account Label (optional)</span>
          <input
            type="text"
            value={accountLabel}
            onChange={(e) => setAccountLabel(e.target.value)}
            placeholder="e.g. Primary production bot"
            className="mt-1.5 w-full rounded-lg border border-[rgba(255,255,255,0.07)] bg-[#07080a] px-3.5 py-2.5 text-sm text-white outline-none focus:border-purple-500/80 transition-all"
          />
        </label>
      </div>

      {provider.token_help_url && (
        <a
          href={provider.token_help_url}
          target="_blank"
          rel="noreferrer"
          className="text-micro inline-flex items-center gap-1 text-[var(--color-slate)] hover:text-white transition-colors"
        >
          <Info className="size-3" />
          <span>Where do I find this?</span>
          <ExternalLink className="size-2.5" />
        </a>
      )}

      {err && (
        <div className="text-body-sm rounded-lg border border-[rgba(255,77,109,0.2)] bg-[rgba(255,77,109,0.05)] px-3 py-2 text-[#ff4d6d] flex items-center gap-2">
          <AlertTriangle className="size-4 shrink-0" />
          <span>{err}</span>
        </div>
      )}

      <div className="flex justify-end gap-2.5 pt-2 border-t border-[rgba(255,255,255,0.04)]">
        <Button variant="secondary" size="sm" type="button" onClick={onClose} disabled={submitting}>
          Cancel
        </Button>
        <Button variant="glow" size="sm" type="submit" disabled={submitting}>
          {submitting ? (
            <span className="inline-flex items-center gap-1.5">
              <Loader2 className="size-3.5 animate-spin" />
              Connecting…
            </span>
          ) : (
            "Connect Integration"
          )}
        </Button>
      </div>
    </form>
  );
}
