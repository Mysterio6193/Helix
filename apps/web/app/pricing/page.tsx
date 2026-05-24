"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import useSWR from "swr";
import { motion } from "framer-motion";
import { Check, HelpCircle, X, Zap } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { MarketingShell } from "@/components/layout/marketing-shell";
import { TestimonialsSection } from "@/components/marketing/testimonials";
import { Reveal } from "@/components/marketing/reveal";
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

const FEATURE_COMPARISON = [
  {
    category: "Brands & Workspaces",
    features: [
      { name: "Brands", free: "1", starter: "5", pro: "25", business: "Unlimited" },
      { name: "Team members", free: "1", starter: "3", pro: "10", business: "Unlimited" },
      { name: "Workspaces", free: "1", starter: "3", pro: "10", business: "Unlimited" },
    ],
  },
  {
    category: "Workflows & Runs",
    features: [
      { name: "Runs per month", free: "10", starter: "200", pro: "1,500", business: "10,000" },
      { name: "Concurrent runs", free: "1", starter: "3", pro: "8", business: "20" },
      { name: "Custom workflows", free: false, starter: true, pro: true, business: true },
      { name: "Workflow scheduling", free: false, starter: true, pro: true, business: true },
    ],
  },
  {
    category: "AI & Generation",
    features: [
      { name: "Image generation", free: "20/mo", starter: "200/mo", pro: "1,000/mo", business: "5,000/mo" },
      { name: "Video generation", free: false, starter: "10/mo", pro: "100/mo", business: "500/mo" },
      { name: "Bring your own model", free: true, starter: true, pro: true, business: true },
      { name: "Priority model access", free: false, starter: false, pro: true, business: true },
    ],
  },
  {
    category: "Intelligence & Automation",
    features: [
      { name: "Revenue analytics", free: true, starter: true, pro: true, business: true },
      { name: "Customer segmentation", free: false, starter: true, pro: true, business: true },
      { name: "Competitor tracking", free: false, starter: true, pro: true, business: true },
      { name: "Auto-optimization rules", free: "1", starter: "3", pro: "10", business: "Unlimited" },
      { name: "Browser automation", free: false, starter: false, pro: true, business: true },
    ],
  },
  {
    category: "Support & Security",
    features: [
      { name: "Community support", free: true, starter: true, pro: true, business: true },
      { name: "Email support", free: false, starter: true, pro: true, business: true },
      { name: "Priority support", free: false, starter: false, pro: true, business: true },
      { name: "SLA guarantee", free: false, starter: false, pro: false, business: true },
      { name: "SSO / SAML", free: false, starter: false, pro: false, business: true },
      { name: "Audit logs", free: false, starter: false, pro: false, business: true },
    ],
  },
];

const FAQS = [
  {
    q: "What happens when I hit my run limit?",
    a: "You'll get a heads-up at 80% usage. Once you hit the limit, new runs are queued until your next billing cycle or until you upgrade. No surprise charges.",
  },
  {
    q: "Can I bring my own AI model keys?",
    a: "Yes — Helix is model-agnostic. Connect your own OpenAI, Anthropic, Google, or Replicate keys and pay us only for the platform. Or use our hosted models for simplicity.",
  },
  {
    q: "Is there a free trial for paid plans?",
    a: "The Free tier is your trial — no time limit, no credit card. When you're ready for more brands, runs, or team members, upgrade instantly.",
  },
  {
    q: "Can I cancel anytime?",
    a: "Absolutely. Cancel from your billing settings and you'll keep access until the end of your current period. No lock-in, no exit fees.",
  },
  {
    q: "What does 'brand memory' mean?",
    a: "Every workflow writes decisions, outputs, and feedback into a per-brand knowledge graph. The next time you run a workflow for that brand, it starts with full context — voice, palette, past assets, what worked, what didn't.",
  },
];

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
  const [showComparison, setShowComparison] = useState(false);

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

  return (
    <MarketingShell>
      <div className="mx-auto max-w-7xl px-6 py-16">
        {/* Header */}
        <div className="mb-16 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[rgba(240,115,74,0.06)] border border-[rgba(240,115,74,0.22)] text-[10px] text-[var(--color-signature)] font-semibold uppercase tracking-[0.18em]">
              <Zap className="size-3" />
              <span>Simple, transparent pricing</span>
            </div>
            
            <h1 className="font-display text-[clamp(2.2rem,4.5vw,3.6rem)] font-light leading-[1.04] tracking-[-0.025em] text-balance text-white">
              Pricing built for{" "}
              <span className="font-display-italic text-gradient-signature font-normal">
                creative teams
              </span>
            </h1>
            <p className="mt-3 text-lg text-[var(--color-slate)] max-w-2xl mx-auto">
              Start free. Upgrade when your brand needs more horsepower. No hidden fees, no surprises.
            </p>
            
            {catalog && !catalog.stripe_configured ? (
              <p className="mt-4 inline-block rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1 text-xs text-amber-400">
                Stripe is not yet configured for this deployment.
              </p>
            ) : null}
          </motion.div>
        </div>

        {errorMsg ? (
          <div className="mb-6 rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-400">
            {errorMsg}
          </div>
        ) : null}

        {/* Plans Grid */}
        {isLoading ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <Card key={i} className="h-96 animate-pulse bg-white/[0.04]" />
            ))}
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {plans.map((plan, i) => {
              const isCurrent = currentPlan === plan.id;
              return (
                <motion.div
                  key={plan.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <Card
                    className={cn(
                      "flex flex-col p-6 h-full relative",
                      plan.highlight && "border-[var(--color-signature)]/30 shadow-[0_0_40px_rgba(240,115,74,0.08)]",
                    )}
                  >
                    {plan.highlight && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                        <Badge tone="success" className="text-[10px]">Most Popular</Badge>
                      </div>
                    )}
                    
                    <div className="mb-4 flex items-center justify-between">
                      <h3 className="text-xl font-semibold text-white">{plan.name}</h3>
                      {isCurrent ? (
                        <Badge tone="info">Current</Badge>
                      ) : null}
                    </div>

                    <div className="mb-4">
                      <span className="text-4xl font-bold text-white">
                        {formatPrice(plan.amount, plan.currency)}
                      </span>
                      {plan.amount > 0 ? (
                        <span className="text-[var(--color-slate)]">
                          {" "}
                          /{plan.interval}
                        </span>
                      ) : null}
                    </div>

                    <p className="mb-6 text-sm text-[var(--color-slate)]">
                      {plan.description}
                    </p>

                    <ul className="mb-8 flex-1 space-y-2 text-sm">
                      {plan.features.map((feature) => (
                        <li key={feature} className="flex gap-2 text-[var(--color-slate)]">
                          <Check size={16} className="text-emerald-400 shrink-0 mt-0.5" />
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
                            ? "Get started free"
                            : !plan.available
                              ? "Coming soon"
                              : `Upgrade to ${plan.name}`}
                    </Button>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        )}

        {/* Feature Comparison */}
        <div className="mt-16">
          <button
            onClick={() => setShowComparison(!showComparison)}
            className="flex items-center gap-2 mx-auto text-sm text-[var(--color-slate)] hover:text-white transition-colors"
          >
            <HelpCircle size={16} />
            {showComparison ? "Hide" : "Show"} full feature comparison
          </button>

          {showComparison && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mt-8 overflow-x-auto"
            >
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/[0.06]">
                    <th className="text-left py-3 px-4 text-[var(--color-stone)] font-medium">Feature</th>
                    <th className="text-center py-3 px-4 text-white font-semibold">Free</th>
                    <th className="text-center py-3 px-4 text-white font-semibold">Starter</th>
                    <th className="text-center py-3 px-4 text-[var(--color-signature)] font-semibold">Pro</th>
                    <th className="text-center py-3 px-4 text-white font-semibold">Business</th>
                  </tr>
                </thead>
                <tbody>
                  {FEATURE_COMPARISON.map((category) => (
                    <>
                      <tr className="bg-white/[0.02]">
                        <td colSpan={5} className="py-2 px-4 text-xs font-bold text-[var(--color-signature)] uppercase tracking-wider">
                          {category.category}
                        </td>
                      </tr>
                      {category.features.map((feature) => (
                        <tr key={feature.name} className="border-b border-white/[0.03] hover:bg-white/[0.01]">
                          <td className="py-2.5 px-4 text-[var(--color-slate)]">{feature.name}</td>
                          {["free", "starter", "pro", "business"].map((plan) => {
                            const value = feature[plan as keyof typeof feature];
                            return (
                              <td key={plan} className="text-center py-2.5 px-4">
                                {typeof value === "boolean" ? (
                                  value ? (
                                    <Check size={16} className="text-emerald-400 mx-auto" />
                                  ) : (
                                    <X size={16} className="text-white/20 mx-auto" />
                                  )
                                ) : (
                                  <span className="text-white">{value}</span>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </>
                  ))}
                </tbody>
              </table>
            </motion.div>
          )}
        </div>

        {/* FAQ */}
        <Reveal>
          <div className="mt-24 max-w-3xl mx-auto">
            <div className="text-center mb-10">
              <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-signature)] mb-3">
                FAQ
              </p>
              <h2 className="font-display text-3xl sm:text-4xl font-light tracking-[-0.015em] text-white">
                Questions? Answered.
              </h2>
            </div>

            <div className="space-y-4">
              {FAQS.map((faq, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-white/[0.05] bg-[#0d0e12]/50 p-5"
                >
                  <h3 className="text-[15px] font-semibold text-white mb-2">{faq.q}</h3>
                  <p className="text-[13px] leading-relaxed text-[var(--color-slate)]">{faq.a}</p>
                </div>
              ))}
            </div>
          </div>
        </Reveal>

        {/* CTA */}
        <Reveal>
          <div className="mt-24 text-center">
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] text-[10px] text-white/70 font-semibold uppercase tracking-widest mb-4">
              <Zap size={11} className="text-[#ff6a4d]" />
              <span>Still deciding?</span>
            </div>
            <h2 className="font-display text-3xl sm:text-4xl font-light tracking-[-0.015em] text-white mb-4">
              Start free, upgrade when you're ready.
            </h2>
            <p className="text-[var(--color-slate)] mb-6">
              No credit card required. No time limits. Full access to core features.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3">
              <Link href="/sign-up">
                <Button variant="glow" size="lg" className="h-12 px-6 font-bold rounded-xl">
                  Create free account
                </Button>
              </Link>
              <Link href="/contact">
                <Button variant="secondary" size="lg" className="h-12 px-6 font-bold rounded-xl bg-white/[0.04] hover:bg-white/[0.08]">
                  Talk to sales
                </Button>
              </Link>
            </div>
          </div>
        </Reveal>
      </div>

      <TestimonialsSection />
    </MarketingShell>
  );
}
