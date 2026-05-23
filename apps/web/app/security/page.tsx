import Link from "next/link";
import {
  ArrowRight,
  Database,
  Key,
  Lock,
  Mail,
  ShieldCheck,
  Workflow,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { MarketingShell } from "@/components/layout/marketing-shell";

/**
 * /security — describes the actual security posture of the running product.
 *
 * Content describes capabilities that exist in the codebase today
 * (workspace isolation, model-key vault, Postgres-backed state, etc.).
 */

export const metadata = {
  title: "Security · Helix",
  description: "How Helix protects your data, brand memory, and model credentials.",
};

const PILLARS: { icon: typeof Lock; title: string; body: string }[] = [
  {
    icon: Lock,
    title: "Workspace isolation.",
    body: "Every brand, run, asset, and memory edge is scoped to a workspace. Cross-workspace access is enforced at the data layer, not just the UI.",
  },
  {
    icon: Key,
    title: "Your model keys, your control.",
    body: "Provider credentials live in a workspace-scoped vault. Helix never persists raw model outputs or prompts to shared infrastructure.",
  },
  {
    icon: Database,
    title: "Durable, auditable state.",
    body: "Workflow runs, briefs, and memory edges land in Postgres. Every run carries an immutable history you can replay or export.",
  },
  {
    icon: Workflow,
    title: "Explicit skill graph.",
    body: "Workflows are composed from declared skills, not opaque chains. You can inspect every step, every input, and every output.",
  },
];

const CONTROLS: { area: string; items: string[] }[] = [
  {
    area: "Account & access",
    items: [
      "Session cookies are HTTP-only and scoped to the application origin.",
      "Sign-in and sign-out flows do not leak credentials into URL parameters.",
      "Auth state is verified server-side before sensitive operations.",
    ],
  },
  {
    area: "Data at rest",
    items: [
      "Application data is persisted in Postgres with per-workspace row scoping.",
      "Model credentials are stored as encrypted records and never returned to the client in plaintext.",
      "Uploaded assets are addressed by content hash and scoped to the owning workspace.",
    ],
  },
  {
    area: "Network",
    items: [
      "Outbound calls to model providers happen server-side; provider keys never leave the API process.",
      "Browser traffic is served over HTTPS in production.",
      "Webhooks (e.g. billing) verify signatures before mutating state.",
    ],
  },
  {
    area: "Operations",
    items: [
      "Workflow runs are durable: failures can be retried without re-uploading inputs.",
      "Logs are structured and scrubbed of credential material.",
      "Schema migrations are versioned and reversible.",
    ],
  },
];

export default function SecurityPage() {
  return (
    <MarketingShell>
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10 opacity-50">
          <div className="absolute top-[-15%] left-[15%] w-[480px] h-[480px] rounded-full blur-[140px] bg-[#4d7bff]/15" />
          <div className="absolute top-[25%] right-[10%] w-[480px] h-[480px] rounded-full blur-[140px] bg-[#00d4aa]/15" />
        </div>
        <div className="max-w-5xl mx-auto px-6 sm:px-8 pt-24 pb-12 text-center">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/[0.08] text-[10px] font-bold uppercase tracking-[0.18em] text-white/70 bg-white/[0.02]">
            <ShieldCheck size={11} />
            Security
          </span>
          <h1 className="font-display mt-7 text-[clamp(2.2rem,4.5vw,4rem)] font-light leading-[1.03] tracking-[-0.025em] text-balance">
            Your brand, your data, your{" "}
            <span className="font-display-italic text-gradient-signature font-normal">
              keys
            </span>
            .
          </h1>
          <p className="mt-6 mx-auto max-w-2xl text-[15px] leading-relaxed text-[var(--color-slate)]">
            Helix is built so that the people, models, and assets in your
            workspace stay separated from everyone else&apos;s. Here&apos;s how
            that works under the hood.
          </p>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {PILLARS.map((p) => {
            const Icon = p.icon;
            return (
              <div
                key={p.title}
                className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-7 hover:border-white/[0.12] hover:bg-white/[0.035] transition-all"
              >
                <div className="inline-flex w-11 h-11 rounded-xl items-center justify-center bg-white/[0.04] border border-white/[0.08]">
                  <Icon size={18} className="text-white" />
                </div>
                <h2 className="mt-5 text-lg font-semibold tracking-tight text-white">
                  {p.title}
                </h2>
                <p className="mt-2 text-[14px] leading-relaxed text-[var(--color-slate)]">
                  {p.body}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-8 py-12">
        <div className="max-w-2xl mb-10">
          <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--color-stone)]">
            Controls
          </span>
          <h2 className="mt-4 text-[clamp(1.8rem,3.5vw,2.4rem)] font-bold leading-tight tracking-tight">
            What we do in code.
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {CONTROLS.map((group) => (
            <div
              key={group.area}
              className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-7"
            >
              <h3 className="text-[11px] font-bold uppercase tracking-[0.18em] text-white/80">
                {group.area}
              </h3>
              <ul className="mt-4 space-y-2.5 text-[14px] text-[var(--color-slate)]">
                {group.items.map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <span className="mt-2 inline-block w-1.5 h-1.5 rounded-full bg-gradient-to-r from-[#ff6a4d] to-[#a24bff]" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-6 sm:px-8 py-16">
        <div className="rounded-3xl border border-white/[0.08] bg-gradient-to-br from-white/[0.04] to-white/[0.01] p-10 md:p-12">
          <div className="flex flex-col md:flex-row md:items-center gap-8">
            <div className="flex-1">
              <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--color-stone)]">
                Responsible disclosure
              </span>
              <h2 className="font-display mt-3 text-[clamp(1.6rem,3vw,2.2rem)] font-light tracking-[-0.018em] leading-[1.1] text-balance">
                Found something? Tell us.
              </h2>
              <p className="mt-4 text-[14px] text-[var(--color-slate)] max-w-xl">
                If you believe you&apos;ve identified a security issue,
                we&apos;d like to hear about it before it&apos;s public. We
                respond to every legitimate report and credit researchers when
                appropriate.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <Link href="/contact">
                <Button variant="secondary" size="md">
                  <Mail size={14} className="mr-2" />
                  Report an issue
                </Button>
              </Link>
              <Link href="/legal/privacy">
                <Button variant="tertiary" size="md">
                  Read privacy policy
                  <ArrowRight size={14} className="ml-2" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </MarketingShell>
  );
}
