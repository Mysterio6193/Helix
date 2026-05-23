"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import useSWR from "swr";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { MarketingShell } from "@/components/layout/marketing-shell";
import { api, ApiError, type BillingPlan } from "@/lib/api";
import { cn } from "@/lib/utils";

function formatPrice(amount: number, currency: string): string {
  if (amount === 0) return "Free";
  const formatter = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency.toUpperCase(),
    maximumFractionDigits: 0,
  });
  return formatter.format(amount);
}

export default function PricingPage() {
  const router = useRouter();
  const { data: catalog, isLoading } = useSWR("billing-plans", () =>
    api.billing.plans(),
  );
  const { data: auth } = useSWR("auth-me", () => api.auth.me());
  const { data: sub } = useSWR(
    auth?.authenticated ? "billing-subscription" : null,
    () => api.billing.subscription(),
  );
  const [pendingPlan, setPendingPlan] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function startCheckout(plan: BillingPlan) {
    setErrorMsg(null);
    if (!auth?.authenticated) {
      router.push(`/sign-in?return_to=/pricing`);
      return;
    }
    if (plan.id === "free") {
      router.push("/");
      return;
    }
    if (!plan.available) {
      setErrorMsg(
        `${plan.name} isn't configured yet. Set STRIPE_PRICE_${plan.id.toUpperCase()} in the API env.`,
      );
      return;
    }
    setPendingPlan(plan.id);
    try {
      const { url } = await api.billing.checkout({ plan: plan.id });
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
      setPendingPlan(null);
    }
  }

  const plans: BillingPlan[] = catalog?.plans ?? [];
  const currentPlan = sub?.plan ?? "free";

  const isGuest = auth ? !auth.authenticated : false;

  const inner = (
    <div className="mx-auto max-w-6xl px-6 py-16">
      <div className="mb-12 text-center">
        <h1 className="font-display text-[clamp(2.2rem,4.5vw,3.6rem)] font-light leading-[1.04] tracking-[-0.025em] text-balance">
          Pricing built for{" "}
          <span className="font-display-italic text-gradient-signature font-normal">
            creative teams
          </span>
        </h1>
        <p className="mt-3 text-lg text-muted-foreground">
          Start free. Upgrade when your brand needs more horsepower.
        </p>
        {catalog && !catalog.stripe_configured ? (
          <p className="mt-4 inline-block rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1 text-xs text-amber-700">
            Stripe is not yet configured for this deployment. Set
            STRIPE_SECRET_KEY to enable paid checkout.
          </p>
        ) : null}
      </div>

      {errorMsg ? (
        <div className="mb-6 rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-700">
          {errorMsg}
        </div>
      ) : null}

      {isLoading ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Card key={i} className="h-96 animate-pulse bg-muted/50" />
          ))}
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {plans.map((plan) => {
            const isCurrent = currentPlan === plan.id;
            return (
              <Card
                key={plan.id}
                className={cn(
                  "flex flex-col p-6",
                  plan.highlight && "border-primary shadow-lg",
                )}
              >
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-xl font-semibold">{plan.name}</h3>
                  {plan.highlight ? <Badge>Popular</Badge> : null}
                  {isCurrent ? (
                    <Badge tone="info">Current</Badge>
                  ) : null}
                </div>

                <div className="mb-4">
                  <span className="text-4xl font-bold">
                    {formatPrice(plan.amount, plan.currency)}
                  </span>
                  {plan.amount > 0 ? (
                    <span className="text-muted-foreground">
                      {" "}
                      /{plan.interval}
                    </span>
                  ) : null}
                </div>

                <p className="mb-6 text-sm text-muted-foreground">
                  {plan.description}
                </p>

                <ul className="mb-8 flex-1 space-y-2 text-sm">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex gap-2">
                      <span className="text-primary">✓</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>

                <Button
                  onClick={() => startCheckout(plan)}
                  disabled={
                    isCurrent ||
                    pendingPlan === plan.id ||
                    (plan.id !== "free" && !plan.available)
                  }
                  variant={plan.highlight ? "primary" : "secondary"}
                  className="w-full"
                >
                  {pendingPlan === plan.id
                    ? "Loading…"
                    : isCurrent
                      ? "Current plan"
                      : plan.id === "free"
                        ? "Get started"
                        : !plan.available
                          ? "Not configured"
                          : `Upgrade to ${plan.name}`}
                </Button>
              </Card>
            );
          })}
        </div>
      )}

      <div className="mt-12 text-center text-sm text-muted-foreground">
        Already a customer?{" "}
        <Link href="/settings/billing" className="underline">
          Manage your subscription
        </Link>
        .
      </div>
    </div>
  );

  if (isGuest) {
    return <MarketingShell>{inner}</MarketingShell>;
  }
  return inner;
}
