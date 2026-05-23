import Link from "next/link";
import { MarketingShell } from "@/components/layout/marketing-shell";

/**
 * Shared shell for legal documents (/legal/privacy, /legal/terms).
 */

export function LegalShell(props: {
  eyebrow: string;
  title: string;
  updated: string;
  children: React.ReactNode;
}) {
  return (
    <MarketingShell>
      <article className="max-w-3xl mx-auto px-6 sm:px-8 pt-20 pb-24">
        <header className="border-b border-white/[0.06] pb-8 mb-10">
          <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--color-stone)]">
            {props.eyebrow}
          </span>
          <h1 className="mt-4 text-[clamp(2rem,4vw,3rem)] font-bold tracking-tight leading-[1.1]">
            {props.title}
          </h1>
          <p className="mt-4 text-[13px] text-[var(--color-slate)]">
            Last updated: {props.updated}
          </p>
        </header>

        <div className="prose-legal space-y-7 text-[15px] leading-[1.7] text-[var(--color-slate)]">
          {props.children}
        </div>

        <footer className="mt-16 pt-8 border-t border-white/[0.06] flex flex-wrap items-center justify-between gap-3 text-[13px] text-[var(--color-stone)]">
          <span>
            Questions? Reach us at{" "}
            <Link href="/contact" className="underline hover:text-white">
              /contact
            </Link>
            .
          </span>
          <div className="flex gap-4">
            <Link
              href="/legal/privacy"
              className="hover:text-white transition"
            >
              Privacy
            </Link>
            <Link href="/legal/terms" className="hover:text-white transition">
              Terms
            </Link>
            <Link href="/security" className="hover:text-white transition">
              Security
            </Link>
          </div>
        </footer>
      </article>
    </MarketingShell>
  );
}

export function H2({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-[20px] font-semibold tracking-tight text-white mt-10 mb-3">
      {children}
    </h2>
  );
}

export function P({ children }: { children: React.ReactNode }) {
  return <p>{children}</p>;
}

export function UL({ children }: { children: React.ReactNode }) {
  return (
    <ul className="list-disc pl-6 space-y-2 marker:text-[var(--color-stone)]">
      {children}
    </ul>
  );
}
