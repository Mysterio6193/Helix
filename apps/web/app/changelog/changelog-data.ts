/**
 * Source-of-truth changelog content.
 *
 * Each entry corresponds to a real surface or capability that exists in the
 * codebase today. Update this file when shipping new features so the
 * marketing changelog stays in sync with reality.
 */

export interface ChangelogEntry {
  version: string;
  date: string; // ISO date
  title: string;
  summary: string;
  tags: Array<"feature" | "improvement" | "infrastructure" | "fix">;
  highlights: string[];
}

export const CHANGELOG: ChangelogEntry[] = [
  {
    version: "1.0.0",
    date: "2026-05-15",
    title: "Helix OS — public release.",
    summary:
      "Brand, workflows, packaging, websites, social, studio, campaigns, chat, models, memory, assets, and integrations available on one workspace.",
    tags: ["feature", "infrastructure"],
    highlights: [
      "Full marketing surface: features, pricing, about, contact, changelog, security, and legal.",
      "Stripe billing scaffold with self-serve plan management.",
      "Auth-aware shells: guest landing for unauthenticated visitors, app shell for signed-in users.",
    ],
  },
  {
    version: "0.9.0",
    date: "2026-04-22",
    title: "Memory graph and run history.",
    summary:
      "Every brief, asset, and workflow run feeds a persistent memory graph scoped to your workspace.",
    tags: ["feature"],
    highlights: [
      "Live-streamed workflow runs with durable Postgres-backed history.",
      "Per-workspace memory graph with edges across brands, assets, and runs.",
      "Sidebar live activity for in-flight runs.",
    ],
  },
  {
    version: "0.8.0",
    date: "2026-03-18",
    title: "Composable creative workflows.",
    summary:
      "Packaging, websites, social calendars, and studio canvases now share one underlying skill graph.",
    tags: ["feature", "improvement"],
    highlights: [
      "Print-ready packaging artwork pipeline with critique passes.",
      "Generated marketing sites deployable to Vercel.",
      "Weekly social packs on a calendar with channel-aware copy.",
    ],
  },
  {
    version: "0.7.0",
    date: "2026-02-04",
    title: "Bring your own model.",
    summary:
      "Plug your own OpenAI, Anthropic, or open-source provider keys at the workspace level.",
    tags: ["feature", "infrastructure"],
    highlights: [
      "Per-workspace model registry with provider key vault.",
      "Direct chat surface for ad-hoc prompting against connected providers.",
      "Workflow runs honor the workspace's default model.",
    ],
  },
  {
    version: "0.6.0",
    date: "2026-01-10",
    title: "Brand canvases.",
    summary:
      "First-class brand profile with positioning, voice, mission, story, and visual identity.",
    tags: ["feature"],
    highlights: [
      "Brand library with structured fields and asset attachments.",
      "Voice + positioning carried into every downstream run.",
      "Workspace isolation enforced end-to-end.",
    ],
  },
];

export const TAG_STYLE: Record<
  ChangelogEntry["tags"][number],
  { label: string; color: string; bg: string }
> = {
  feature: { label: "Feature", color: "#00d4aa", bg: "rgba(0,212,170,0.12)" },
  improvement: {
    label: "Improvement",
    color: "#4d9fff",
    bg: "rgba(77,159,255,0.12)",
  },
  infrastructure: {
    label: "Infrastructure",
    color: "#a24bff",
    bg: "rgba(162,75,255,0.12)",
  },
  fix: { label: "Fix", color: "#ffb347", bg: "rgba(255,179,71,0.12)" },
};
