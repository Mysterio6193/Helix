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

export default function BillingSettingsPage() {
  const { data: auth } = useSWR("auth-me", () => api.auth.me());
  const { data: sub, isLoading, mutate } = useSWR(
    auth?.authenticated ? "billing-subscription" : null,
    () => api.billing.subscription(),
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
