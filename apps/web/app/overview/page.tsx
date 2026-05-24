"use client";

import Link from "next/link";
import useSWR from "swr";
import { motion } from "framer-motion";
import {
  ArrowUpRight,
  Boxes,
  Image as ImageIcon,
  Megaphone,
  Package,
  PaintBucket,
  Rocket,
  Sparkles,
  Activity,
  FolderOpen,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardSubtitle, CardTitle } from "@/components/ui/card";
import {
  api,
  type AssetItem,
  type AuthStatus,
  type Brand,
  type RunSummary,
} from "@/lib/api";
import { formatRelative } from "@/lib/utils";

/* ─── Stat tile ──────────────────────────────────────────── */

function StatTile({
  label,
  value,
  hint,
  href,
  color = "#a24bff",
}: {
  label: string;
  value: number | string;
  hint?: string;
  href?: string;
  color?: string;
}) {
  const inner = (
    <div
      className="group relative rounded-2xl p-5 border border-[rgba(255,255,255,0.06)] bg-[#13141a]/60 backdrop-blur-md shadow-[0_4px_24px_rgba(0,0,0,0.15)] hover:border-[rgba(255,255,255,0.12)] hover:bg-[#1a1c24]/50 transition-all duration-300 hover:-translate-y-0.5 overflow-hidden"
    >
      <div 
        className="absolute -right-4 -bottom-4 w-16 h-16 rounded-full opacity-[0.03] group-hover:scale-150 group-hover:opacity-[0.05] transition-all duration-500 blur-xl pointer-events-none"
        style={{ backgroundColor: color }}
      />
      
      <div
        className="text-eyebrow font-semibold tracking-wider"
        style={{ color: "var(--color-stone)" }}
      >
        {label}
      </div>
      <div
        className="text-display-lg mt-1.5 font-bold tracking-tight"
        style={{ color: "var(--color-ink)", lineHeight: 1 }}
      >
        {value}
      </div>
      {hint && (
        <div
          className="text-micro mt-2 text-[var(--color-slate)]"
        >
          {hint}
        </div>
      )}
    </div>
  );
  return href ? <Link href={href}>{inner}</Link> : inner;
}

/* ─── QUICK-START ACTIONS ────────────────────────────────── */

const QUICK_ACTIONS = [
  {
    label: "Brand Identity",
    href: "/brands/new",
    icon: Sparkles,
    color: "#ff3d7f",
    description: "Generate a complete brand from a single brief.",
  },
  {
    label: "Packaging Suite",
    href: "/packaging",
    icon: Package,
    color: "#a24bff",
    description: "Labels, boxes, and print-ready specs.",
  },
  {
    label: "Website",
    href: "/websites",
    icon: Boxes,
    color: "#4d7bff",
    description: "Launch a Next.js site on Vercel.",
  },
  {
    label: "Social Pack",
    href: "/social",
    icon: Megaphone,
    color: "#ffb347",
    description: "Weekly content calendar with assets.",
  },
  {
    label: "Studio",
    href: "/studio",
    icon: PaintBucket,
    color: "#ff7a4d",
    description: "Iterate on visuals with live preview.",
  },
  {
    label: "Launch Campaign",
    href: "/campaigns",
    icon: Rocket,
    color: "#00d4aa",
    description: "Coordinate launch across every channel.",
  },
];

/* ─── LOGGED-IN COMMAND CENTER ───────────────────────────── */

function CommandCenterDashboard({
  firstName,
  brandCount,
  runCount,
  recentBrands,
  recentRuns,
  recentAssets,
  hasAnyContent
}: {
  firstName: string;
  brandCount: number;
  runCount: number;
  recentBrands: Brand[];
  recentRuns: RunSummary[];
  recentAssets: AssetItem[];
  hasAnyContent: boolean;
}) {
  return (
    <div className="animate-fade-up space-y-8">
      {/* Shifting background neon details */}
      <div className="absolute top-0 right-1/4 w-[600px] h-[600px] rounded-full bg-[rgba(162,75,255,0.02)] blur-[140px] pointer-events-none" />

      {/* Higgsfield Glowing Hero Welcome Card */}
      <motion.div 
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative overflow-hidden rounded-[24px] border border-[rgba(255,255,255,0.06)] bg-gradient-to-br from-[#13141a]/95 via-[#0e0f12]/98 to-[#171821]/95 p-8 sm:p-10 shadow-[0_24px_80px_rgba(0,0,0,0.5)]"
      >
        {/* Shifting background neon details */}
        <div className="absolute top-0 right-0 w-[350px] h-[350px] rounded-full bg-[rgba(162,75,255,0.04)] blur-[90px] pointer-events-none animate-pulse-glow" style={{ animationDuration: "8s" }} />
        <div className="absolute bottom-0 left-1/3 w-[250px] h-[250px] rounded-full bg-[rgba(0,212,170,0.03)] blur-[80px] pointer-events-none animate-pulse-glow" style={{ animationDuration: "12s" }} />

        <div className="relative flex flex-col lg:flex-row lg:items-center justify-between gap-6 z-10">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[rgba(255,106,77,0.08)] border border-[rgba(255,106,77,0.18)] text-[10px] text-[#ff6a4d] uppercase font-semibold tracking-wider">
              <Sparkles className="size-3 animate-pulse-glow" />
              <span>Helix Command Center</span>
            </div>
            
            <h1 className="text-display-lg font-bold tracking-tight text-white leading-tight">
              Welcome back, <span className="bg-gradient-to-r from-[#ff6a4d] via-[#a24bff] to-[#00d4aa] bg-clip-text text-transparent">{firstName}</span>
            </h1>
            
            <p className="text-body-md max-w-[62ch] text-[var(--color-slate)] leading-relaxed">
              Design complete brand systems, run composable workflows, deploy restaurant websites on Vercel, and coordinate active marketing campaigns — all from a single screen.
            </p>
          </div>
          
          <div className="flex flex-wrap gap-3 shrink-0">
            <Link href="/brands/new">
              <Button variant="glow" size="md" className="cursor-pointer">
                New Brand
              </Button>
            </Link>
            <Link href="/brands">
              <Button variant="secondary" size="md" className="backdrop-blur-md bg-white/5 border-white/10 hover:bg-white/10 cursor-pointer">
                All Brands
              </Button>
            </Link>
          </div>
        </div>
      </motion.div>

      {/* Stats Cards Row */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
        className="grid grid-cols-2 lg:grid-cols-4 gap-3.5"
      >
        <StatTile
          label="Brands"
          value={brandCount}
          hint={brandCount === 0 ? "Create your first brand" : "Active projects"}
          href="/brands"
          color="#ff3d7f"
        />
        <StatTile
          label="Recent runs"
          value={runCount}
          hint={runCount === 0 ? "No active jobs" : "Last 5 executions"}
          href="/workflows"
          color="#a24bff"
        />
        <StatTile
          label="Library Assets"
          value={recentAssets?.length ?? 0}
          hint="Total outputs generated"
          href="/assets"
          color="#4d7bff"
        />
        <StatTile
          label="OS Status"
          value={hasAnyContent ? "Active" : "Pending"}
          hint={hasAnyContent ? "All systems healthy" : "Complete setup below"}
          color="#00d4aa"
        />
      </motion.div>

      {/* Empty State for Fresh Users */}
      {brandCount === 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Card feature className="text-center py-16 border border-[rgba(255,255,255,0.06)] bg-[#13141a]/40 backdrop-blur-md shadow-xl rounded-2xl relative overflow-hidden">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 rounded-full bg-purple-500/5 blur-[80px] pointer-events-none" />
            
            <div
              className="inline-flex w-14 h-14 rounded-2xl items-center justify-center mb-5 animate-pulse-glow shadow-lg shadow-purple-500/5"
              style={{
                background:
                  "linear-gradient(135deg,#ff6a4d 0%,#a24bff 50%,#4d7bff 100%)",
              }}
            >
              <Sparkles size={24} color="white" />
            </div>
            
            <CardTitle className="text-2xl font-bold text-white tracking-tight">Create your first brand kit</CardTitle>
            <CardSubtitle className="max-w-[45ch] mx-auto mt-2.5 text-[var(--color-slate)] leading-relaxed text-body-sm">
              Helix groups campaigns, packaging briefs, websites, and social packs around single brands. Create a brand kit to initialize memory and sync tools.
            </CardSubtitle>
            
            <div className="mt-8">
              <Link href="/brands/new">
                <Button variant="glow" size="md" className="cursor-pointer font-semibold px-6 h-11">
                  Create Brand Identity
                </Button>
              </Link>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Grid of Main Content Areas */}
      {brandCount > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_400px] gap-4">
          
          {/* Your Brands Section */}
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="rounded-[20px] overflow-hidden border border-[rgba(255,255,255,0.06)] bg-[#13141a]/60 backdrop-blur-md shadow-lg flex flex-col"
          >
            <div
              className="flex items-center justify-between px-6 py-4.5 border-b border-[rgba(255,255,255,0.05)] bg-white/[0.01]"
            >
              <div>
                <div
                  className="text-label font-semibold text-white flex items-center gap-2"
                >
                  <FolderOpen className="size-4 text-purple-400" />
                  <span>Your active brands</span>
                </div>
                <div
                  className="text-micro mt-0.5"
                  style={{ color: "var(--color-stone)" }}
                >
                  {brandCount} total projects
                </div>
              </div>
              <Link
                href="/brands"
                className="text-micro flex items-center gap-1.5 hover:opacity-100 opacity-60 transition-opacity font-semibold"
                style={{ color: "var(--color-slate)" }}
              >
                See all <ArrowUpRight size={13} />
              </Link>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-px bg-[rgba(255,255,255,0.04)]">
              {recentBrands.map((b) => (
                <Link
                  key={b.id}
                  href={`/brands/${b.id}`}
                  className="group relative p-5 transition-all bg-[#13141a]/85 hover:bg-[#1a1c24]/90"
                >
                  <div className="absolute -inset-px rounded-sm bg-gradient-to-r from-purple-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                  
                  <div className="relative">
                    <div
                      className="text-label font-bold text-white group-hover:text-purple-400 transition-colors"
                    >
                      {b.name}
                    </div>
                    <div
                      className="text-micro mt-1 font-medium"
                      style={{ color: "var(--color-slate)" }}
                    >
                      {b.category ?? "F&B Brand"} · Created {formatRelative(b.created_at)}
                    </div>
                    {b.tagline && (
                      <div
                        className="text-micro mt-3 line-clamp-2 leading-relaxed"
                        style={{ color: "var(--color-stone)" }}
                      >
                        {b.tagline}
                      </div>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </motion.div>

          {/* Recent Workflows Rail */}
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.25, duration: 0.5 }}
            className="rounded-[20px] overflow-hidden border border-[rgba(255,255,255,0.06)] bg-[#13141a]/60 backdrop-blur-md shadow-lg flex flex-col"
          >
            <div
              className="flex items-center justify-between px-6 py-4.5 border-b border-[rgba(255,255,255,0.05)] bg-white/[0.01]"
            >
              <div
                className="text-label font-semibold text-white flex items-center gap-2"
              >
                <Activity className="size-4 text-purple-400" />
                <span>Recent workflows</span>
              </div>
              <Link
                href="/workflows"
                className="text-micro flex items-center gap-1.5 hover:opacity-100 opacity-60 transition-opacity font-semibold"
                style={{ color: "var(--color-slate)" }}
              >
                All <ArrowUpRight size={13} />
              </Link>
            </div>
            
            <div className="p-3.5 space-y-1.5 flex-1">
              {recentRuns.length === 0 ? (
                <div
                  className="text-micro p-6 text-center border border-dashed border-white/5 rounded-xl"
                  style={{ color: "var(--color-stone)" }}
                >
                  No active workflows yet. Launch one from your project dashboard.
                </div>
              ) : (
                recentRuns.map((r) => {
                  const isRunning = r.status === "running" || r.status === "queued" || r.status === "pending";
                  const statusColor =
                    r.status === "succeeded"
                      ? "#00c896"
                      : r.status === "failed"
                      ? "#ff4d6d"
                      : r.status === "running"
                      ? "#4d9fff"
                      : "#ffb347";
                  return (
                    <Link
                      key={r.id}
                      href={`/workflows/${r.id}`}
                      className="group block px-4 py-3 rounded-xl border border-white/[0.02] bg-white/[0.01] hover:bg-white/[0.03] hover:border-white/5 transition-all duration-200"
                    >
                      <div className="flex items-center justify-between gap-2.5">
                        <div
                          className="text-label font-medium text-[var(--color-charcoal)] group-hover:text-white transition-colors truncate"
                        >
                          {r.workflow.replace(/_/g, " ")}
                        </div>
                        <span
                          className="text-micro font-semibold uppercase tracking-wider scale-95 shrink-0 px-2 py-0.5 rounded bg-black/20 border border-white/5 inline-flex items-center gap-1.5"
                          style={{ color: statusColor }}
                        >
                          {isRunning && <span className="w-1.5 h-1.5 rounded-full bg-[#4d9fff] animate-pulse-glow" style={{ boxShadow: "0 0 4px #4d9fff" }} />}
                          {r.status}
                        </span>
                      </div>
                      <div
                        className="text-[10px] mt-1 text-[var(--color-stone)]"
                      >
                        Started {formatRelative(r.created_at)}
                      </div>
                    </Link>
                  );
                })
              )}
            </div>
          </motion.div>
        </div>
      )}

      {/* Latest Generated Assets Strip */}
      {recentAssets.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="rounded-[20px] p-5 border border-[rgba(255,255,255,0.06)] bg-[#13141a]/60 backdrop-blur-md shadow-lg"
        >
          <div className="flex items-center justify-between mb-4.5 px-1">
            <div
              className="text-label font-semibold text-white flex items-center gap-2"
            >
              <ImageIcon className="size-4 text-purple-400" />
              <span>Latest creative outputs</span>
            </div>
            
            <Link
              href="/assets"
              className="text-micro flex items-center gap-1.5 hover:opacity-100 opacity-60 transition-opacity font-semibold"
              style={{ color: "var(--color-slate)" }}
            >
              Library <ArrowUpRight size={13} />
            </Link>
          </div>
          
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
            {recentAssets.map((a) => (
              <Link
                key={a.id}
                href={`/assets/${a.id}`}
                className="group relative aspect-square rounded-xl overflow-hidden flex items-center justify-center border border-white/[0.04] bg-zinc-950 transition-all duration-300 hover:scale-[1.03] hover:border-purple-500/20"
              >
                <div className="absolute -inset-px rounded-xl bg-gradient-to-br from-purple-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

                <ImageIcon
                  size={22}
                  className="text-[var(--color-stone)] group-hover:text-purple-400 group-hover:scale-105 transition-all duration-300"
                />
              </Link>
            ))}
          </div>
        </motion.div>
      )}

      {/* Quick Actions Matrix Grid */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35, duration: 0.5 }}
      >
        <div className="flex items-center justify-between mb-4.5 px-1">
          <div>
            <div
              className="text-eyebrow font-semibold tracking-wider text-[var(--color-stone)]"
            >
              LAUNCH TOOLS
            </div>
            <h2
              className="text-heading-xl font-bold tracking-tight text-white mt-1"
            >
              What would you like to build?
            </h2>
          </div>
        </div>
        
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
          {QUICK_ACTIONS.map((action) => {
            const Icon = action.icon;
            return (
              <Link key={action.label} href={action.href}>
                <div
                  className="group relative rounded-2xl p-5 h-full cursor-pointer border border-white/[0.03] bg-zinc-950/40 hover:bg-[#1a1c24]/50 transition-all duration-300 hover:scale-[1.03] hover:-translate-y-0.5 flex flex-col justify-between overflow-hidden"
                  style={{
                    boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
                  }}
                >
                  <div 
                    className="absolute -right-5 -bottom-5 w-16 h-16 rounded-full opacity-[0.02] group-hover:scale-150 group-hover:opacity-[0.05] transition-all duration-500 blur-xl pointer-events-none"
                    style={{ backgroundColor: action.color }}
                  />

                  <div>
                    <div 
                      className="inline-flex size-9 items-center justify-center rounded-xl border border-white/5 bg-zinc-900 shadow-md group-hover:scale-105 transition-transform"
                      style={{ color: action.color }}
                    >
                      <Icon size={18} />
                    </div>
                    <div
                      className="text-label mt-4 font-bold text-white group-hover:text-purple-400 transition-colors"
                    >
                      {action.label}
                    </div>
                    <div
                      className="text-micro mt-1.5 text-[var(--color-slate)] leading-relaxed line-clamp-3"
                    >
                      {action.description}
                    </div>
                  </div>

                  <div className="mt-4 pt-2 flex items-center text-[10px] text-purple-400 font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                    <span>Initialize</span>
                    <ArrowUpRight size={10} className="ml-1" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}

export default function OverviewPage() {
  const { data: auth, isLoading: authLoading } = useSWR<AuthStatus>(
    "auth-me",
    () => api.auth.me(),
  );

  const authed = auth?.authenticated === true;

  // SWR fetches for logged-in command center
  const { data: brands } = useSWR<Brand[]>(
    authed ? "home-brands" : null,
    () => api.brands.list(),
  );
  const { data: runs } = useSWR<RunSummary[]>(
    authed ? "home-runs" : null,
    () => api.runs.list({ limit: 5 }),
    { refreshInterval: 6000 },
  );
  const { data: assets } = useSWR<AssetItem[]>(
    authed ? "home-assets" : null,
    () => api.assets.list({ limit: 6 }),
  );

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] bg-[#07080a]">
        <div className="flex flex-col items-center gap-3">
          <svg className="animate-spin h-6 w-6 text-purple-500" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <div
            className="text-body-sm"
            style={{ color: "var(--color-stone)" }}
          >
            Accessing command center…
          </div>
        </div>
      </div>
    );
  }

  // Logged-in user variables
  const firstName =
    auth?.user?.name?.split(" ")[0] ??
    auth?.user?.email?.split("@")[0] ??
    "there";

  const brandCount = brands?.length ?? 0;
  const runCount = runs?.length ?? 0;
  const recentBrands = (brands ?? []).slice(0, 6);
  const recentRuns = (runs ?? []).slice(0, 5);
  const recentAssets = (assets ?? []).slice(0, 6);
  const hasAnyContent = brandCount > 0 || runCount > 0;

  return (
    <CommandCenterDashboard
      firstName={firstName}
      brandCount={brandCount}
      runCount={runCount}
      recentBrands={recentBrands}
      recentRuns={recentRuns}
      recentAssets={recentAssets}
      hasAnyContent={hasAnyContent}
    />
  );
}
