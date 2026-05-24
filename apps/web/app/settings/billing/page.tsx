"use client";

import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api, ApiError } from "@/lib/api";

function formatDate(iso?: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

function statusBadgeTone(status: string): "success" | "warning" | "error" | "neutral" {
  switch (status) {
    case "active":
    case "trialing":
      return "success";
    case "past_due":
    case "incomplete":
      return "warning";
    case "canceled":
    case "unpaid":
    case "incomplete_expired":
      return "error";
    default:
      return "neutral";
  }
}

function UsageBar({ used, limit, label }: { used: number; limit: number | null; label: string }) {
  const pct = limit && limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  const tone = pct >= 90 ? "bg-red-500" : pct >= 70 ? "bg-amber-500" : "bg-emerald-500";
  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span>
          {used.toLocaleString()}{limit ? ` / ${limit.toLocaleString()}` : ""}
        </span>
      </div>
      {limit && (
        <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-white/10">
          <div className={`h-full rounded-full transition-all ${tone}`} style={{ width: `${pct}%` }} />
        </div>
      )}
    </div>
  );
}

export default function BillingSettingsPage() {
  const { data: auth } = useSWR("auth-me", () => api.auth.me());
  const { data: sub, isLoading, mutate } = useSWR(
    auth?.authenticated ? "billing-subscription" : null,
    () => api.billing.subscription(),
  );
  const { data: usage } = useSWR(
    auth?.authenticated ? "billing-usage" : null,
    () => api.billing.usage(),
    { refreshInterval: 30000 },
  );
  const [openingPortal, setOpeningPortal] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function openPortal() {
    setErrorMsg(null);
    setOpeningPortal(true);
    try {
      const { url } = await api.billing.portal();
      window.location.href = url;
    } catch (err) {
      if (err instanceof ApiError) {
        const detail =
          typeof err.body === "object" && err.body && "detail" in err.body
            ? String((err.body as { detail: unknown }).detail)
            : err.message;
        setErrorMsg(detail);
      } else {
        setErrorMsg(String(err));
      }
      setOpeningPortal(false);
    }
  }

  if (!auth) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <p className="text-muted-foreground">Loading…</p>
      </div>
    );
  }

  if (!auth.authenticated) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="mb-3 text-2xl font-semibold">Billing</h1>
        <p className="text-muted-foreground">
          Please{" "}
          <Link
            href="/sign-in?return_to=/settings/billing"
            className="underline"
          >
            sign in
          </Link>{" "}
          to manage your subscription.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">Billing</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your Helix subscription and payment method.
        </p>
      </div>

      {errorMsg ? (
        <div className="mb-6 rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-700">
          {errorMsg}
        </div>
      ) : null}

      {isLoading ? (
        <Card className="h-48 animate-pulse" />
      ) : sub ? (
        <div className="space-y-6">
          <Card className="p-6">
          <div className="mb-6 flex items-start justify-between">
            <div>
              <div className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">
                Current plan
              </div>
              <div className="flex items-center gap-3">
                <span className="text-2xl font-semibold capitalize">
                  {sub.plan}
                </span>
                <Badge tone={statusBadgeTone(sub.status)}>{sub.status}</Badge>
              </div>
            </div>
            <Link
              href="/pricing"
              className="text-sm underline text-muted-foreground hover:text-foreground"
            >
              Change plan
            </Link>
          </div>

          <dl className="grid grid-cols-1 gap-4 border-t pt-4 sm:grid-cols-2">
            <div>
              <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                Renews
              </dt>
              <dd className="mt-1 text-sm">
                {sub.cancel_at_period_end ? (
                  <>
                    Cancels on {formatDate(sub.current_period_end)}
                  </>
                ) : sub.current_period_end ? (
                  <>Next charge on {formatDate(sub.current_period_end)}</>
                ) : (
                  "—"
                )}
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                Customer ID
              </dt>
              <dd className="mt-1 font-mono text-xs">
                {sub.stripe_customer_id ?? "Not provisioned yet"}
              </dd>
            </div>
          </dl>

          <div className="mt-6 flex flex-wrap gap-3 border-t pt-4">
            {sub.has_active_subscription ? (
              <Button
                onClick={openPortal}
                disabled={openingPortal}
                variant="primary"
              >
                {openingPortal ? "Opening…" : "Manage in Stripe portal"}
              </Button>
            ) : (
              <Link href="/pricing">
                <Button variant="primary">Choose a plan</Button>
              </Link>
            )}
            <Button onClick={() => mutate()} variant="secondary">
              Refresh
            </Button>
          </div>

          {!sub.publishable_key ? (
            <p className="mt-6 rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-xs text-amber-700">
              Stripe is not configured on this deployment. To enable paid
              subscriptions, set STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, and
              STRIPE_WEBHOOK_SECRET in the API environment.
            </p>
           ) : null}
          </Card>

        {usage ? (
          <Card className="p-6">
            <div className="mb-5">
              <div className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">
                Usage
              </div>
              <h2 className="text-xl font-semibold">Current Billing Period</h2>
              <p className="mt-1 text-xs text-muted-foreground">
                {new Date(usage.period_start).toLocaleDateString()} –{" "}
                {usage.period_end
                  ? new Date(usage.period_end).toLocaleDateString()
                  : "Ongoing"}
              </p>
            </div>

            <div className="space-y-4">
              <UsageBar used={usage.calls} limit={usage.call_limit} label="LLM Calls" />
              <UsageBar used={usage.prompt_tokens} limit={null} label="Prompt Tokens" />
              <UsageBar used={usage.completion_tokens} limit={null} label="Completion Tokens" />
            </div>

            <div className="mt-4 flex items-center justify-between border-t pt-4">
              <span className="text-xs text-muted-foreground">Total cost this period</span>
              <span className="text-sm font-semibold">${usage.cost_usd.toFixed(4)}</span>
            </div>

            {usage.models.length > 0 && (
              <div className="mt-4 border-t pt-4">
                <div className="mb-2 text-xs font-semibold text-muted-foreground">Per Model</div>
                <div className="space-y-2">
                  {usage.models.map((m: any) => (
                    <div key={m.model_id} className="flex items-center justify-between text-xs">
                      <span className="font-mono text-muted-foreground">{m.model_id.split(":").pop()}</span>
                      <span className="text-muted-foreground">{m.calls} calls · ${Number(m.cost_usd || 0).toFixed(4)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        ) : null}
        </div>
      ) : (
        <Card className="p-6">
          <p className="text-sm text-muted-foreground">
            No subscription record yet.{" "}
            <Link href="/pricing" className="underline">
              View plans
            </Link>{" "}
            to get started.
          </p>
        </Card>
      )}
    </div>
  );
}
