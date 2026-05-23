import Link from "next/link";
import { ArrowRight, GitCommit } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MarketingShell } from "@/components/layout/marketing-shell";
import { CHANGELOG, TAG_STYLE } from "./changelog-data";

/**
 * /changelog — release history driven by ./changelog-data.ts.
 *
 * Static export. Render at build time from the structured source-of-truth
 * file; no fake "you have unread updates" widgets or mocked data.
 */

export const metadata = {
  title: "Changelog · Helix",
  description: "Release notes and recent updates to the Helix operating system.",
};

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default function ChangelogPage() {
  return (
    <MarketingShell>
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10 opacity-50">
          <div className="absolute top-[-15%] left-[20%] w-[480px] h-[480px] rounded-full blur-[140px] bg-[#00d4aa]/15" />
          <div className="absolute top-[25%] right-[10%] w-[480px] h-[480px] rounded-full blur-[140px] bg-[#a24bff]/15" />
        </div>
        <div className="max-w-4xl mx-auto px-6 sm:px-8 pt-24 pb-12 text-center">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/[0.08] text-[10px] font-bold uppercase tracking-[0.18em] text-white/70 bg-white/[0.02]">
            <GitCommit size={11} />
            Changelog
          </span>
          <h1 className="font-display mt-7 text-[clamp(2.2rem,4.5vw,3.8rem)] font-light leading-[1.04] tracking-[-0.025em] text-balance">
            What we&apos;ve{" "}
            <span className="font-display-italic text-gradient-signature font-normal">
              shipped
            </span>
            .
          </h1>
          <p className="mt-6 mx-auto max-w-xl text-[15px] leading-relaxed text-[var(--color-slate)]">
            Real releases, not coming-soon promises. Each entry corresponds to
            a surface or capability you can use right now.
          </p>
        </div>
      </section>

      <section className="max-w-4xl mx-auto px-6 sm:px-8 py-12">
        <ol className="relative border-l border-white/[0.06] space-y-12 pl-8">
          {CHANGELOG.map((entry) => (
            <li key={entry.version} className="relative">
              <span
                aria-hidden
                className="absolute -left-[37px] top-1 inline-flex w-4 h-4 rounded-full bg-gradient-to-br from-[#ff6a4d] to-[#a24bff] ring-4 ring-[#07080a]"
              />
              <div className="flex flex-wrap items-baseline gap-3 mb-3">
                <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--color-stone)] tabular-nums">
                  v{entry.version}
                </span>
                <span className="text-[12px] text-[var(--color-slate)]">
                  {formatDate(entry.date)}
                </span>
                <div className="flex flex-wrap gap-1.5 ml-auto">
                  {entry.tags.map((tag) => {
                    const meta = TAG_STYLE[tag];
                    return (
                      <span
                        key={tag}
                        className="text-[10px] font-bold uppercase tracking-[0.14em] px-2 py-1 rounded-full"
                        style={{
                          color: meta.color,
                          background: meta.bg,
                          border: `1px solid ${meta.color}33`,
                        }}
                      >
                        {meta.label}
                      </span>
                    );
                  })}
                </div>
              </div>
              <h2 className="text-xl md:text-2xl font-bold tracking-tight text-white">
                {entry.title}
              </h2>
              <p className="mt-3 text-[14px] leading-relaxed text-[var(--color-slate)]">
                {entry.summary}
              </p>
              <ul className="mt-5 space-y-2.5 text-[14px] text-[var(--color-slate)]">
                {entry.highlights.map((h) => (
                  <li key={h} className="flex items-start gap-3">
                    <span className="mt-2 inline-block w-1.5 h-1.5 rounded-full bg-gradient-to-r from-[#ff6a4d] to-[#a24bff]" />
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ol>
      </section>

      <section className="max-w-4xl mx-auto px-6 sm:px-8 py-20 text-center">
        <h2 className="font-display text-[clamp(1.8rem,3.5vw,2.6rem)] font-light tracking-[-0.022em] leading-[1.08] text-balance">
          See what&apos;s next on the roadmap.
        </h2>
        <p className="mt-4 mx-auto max-w-md text-[14px] text-[var(--color-slate)]">
          Want a feature flagged early? Tell us what you&apos;re building.
        </p>
        <div className="mt-7 flex flex-wrap justify-center gap-3">
          <Link href="/contact">
            <Button variant="secondary" size="md">
              Talk to us
            </Button>
          </Link>
          <Link href="/sign-up">
            <Button
              variant="glow"
              size="md"
              className="font-bold uppercase tracking-wider"
            >
              Get started
              <ArrowRight size={14} className="ml-2" />
            </Button>
          </Link>
        </div>
      </section>
    </MarketingShell>
  );
}
