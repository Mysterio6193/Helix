"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  Boxes,
  ChevronLeft,
  CreditCard,
  Cpu,
  Image as ImageIcon,
  LayoutDashboard,
  LogOut,
  Megaphone,
  MessageSquare,
  Network,
  Package,
  PaintBucket,
  Rocket,
  Settings,
  Sparkles,
  UtensilsCrossed,
} from "lucide-react";

import useSWR from "swr";

import { api, type AuthUser, type RunSummary } from "@/lib/api";
import { cn } from "@/lib/utils";
import { WorkspaceSwitcher } from "./workspace-switcher";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  group: "core" | "deliver" | "infra";
}

const NAV: NavItem[] = [
  { href: "/", label: "Overview", icon: LayoutDashboard, group: "core" },
  { href: "/chat", label: "Chat", icon: MessageSquare, group: "core" },
  { href: "/brands", label: "Projects", icon: Sparkles, group: "core" },
  { href: "/workflows", label: "Workflows", icon: Activity, group: "core" },
  { href: "/assets", label: "Library", icon: ImageIcon, group: "core" },
  { href: "/memory", label: "Network", icon: Network, group: "core" },
  { href: "/studio", label: "Studio", icon: PaintBucket, group: "deliver" },
  { href: "/packaging", label: "Packaging", icon: Package, group: "deliver" },
  { href: "/websites", label: "Websites", icon: Boxes, group: "deliver" },
  { href: "/social", label: "Social", icon: Megaphone, group: "deliver" },
  { href: "/campaigns", label: "Campaigns", icon: Rocket, group: "deliver" },
  { href: "/skills", label: "Skills", icon: UtensilsCrossed, group: "infra" },
  { href: "/settings/models", label: "Models", icon: Cpu, group: "infra" },
  { href: "/integrations", label: "Integrations", icon: Settings, group: "infra" },
  { href: "/settings/billing", label: "Billing", icon: CreditCard, group: "infra" },
];

const STATUS_STYLE: Record<string, { color: string; label: string }> = {
  running: { color: "#4d9fff", label: "Running" },
  queued: { color: "#ffb347", label: "Queued" },
  pending: { color: "#ffb347", label: "Pending" },
  succeeded: { color: "#00d4aa", label: "Succeeded" },
  failed: { color: "#ff5470", label: "Failed" },
};

function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loaded, setLoaded] = useState(false);
  const refresh = useCallback(async () => {
    try {
      const r = await api.auth.me();
      setUser(r.authenticated && r.user ? r.user : null);
    } catch {
      setUser(null);
    } finally {
      setLoaded(true);
    }
  }, []);
  useEffect(() => {
    void refresh();
  }, [refresh]);
  return { user, loaded, refresh };
}

function UserFooter() {
  const { user, loaded } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  async function signOut() {
    try {
      await api.auth.logout();
    } catch {
      /* ignore */
    }
    router.push("/sign-in");
    router.refresh();
  }

  if (!loaded) {
    return (
      <div
        className="mx-2 mb-2 rounded-[12px] p-3 animate-pulse"
        style={{ border: "1px solid var(--color-hairline)" }}
      >
        <div className="h-3 w-24 rounded bg-[var(--color-muted)] opacity-50" />
      </div>
    );
  }

  if (!user) {
    const returnTo = pathname && pathname !== "/sign-in" ? pathname : "/";
    return (
      <Link
        href={`/sign-in?return_to=${encodeURIComponent(returnTo)}`}
        className="mx-2 mb-2 rounded-[12px] p-3 flex items-center gap-2 hover:bg-[rgba(255,255,255,0.05)] transition"
        style={{ border: "1px solid var(--color-hairline)" }}
      >
        <span
          className="inline-flex w-7 h-7 rounded-full items-center justify-center text-xs font-semibold"
          style={{ background: "var(--color-muted)", color: "var(--color-slate)" }}
        >
          ?
        </span>
        <span className="text-label" style={{ color: "var(--color-ink)" }}>
          Sign in
        </span>
      </Link>
    );
  }

  const initial = (user.name || user.email).slice(0, 1).toUpperCase();
  return (
    <div
      className="mx-2 mb-2 rounded-[12px] p-3 flex items-center gap-2"
      style={{ border: "1px solid var(--color-hairline)" }}
    >
      {user.picture ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={user.picture}
          alt={user.name ?? user.email}
          className="w-7 h-7 rounded-full object-cover"
          referrerPolicy="no-referrer"
        />
      ) : (
        <span
          className="inline-flex w-7 h-7 rounded-full items-center justify-center text-xs font-semibold text-white"
          style={{ background: "linear-gradient(135deg,#6366f1,#a855f7)" }}
        >
          {initial}
        </span>
      )}
      <div className="flex-1 min-w-0">
        <div
          className="text-label truncate"
          style={{ color: "var(--color-ink)" }}
        >
          {user.name || user.email.split("@")[0]}
        </div>
        <div
          className="text-micro truncate"
          style={{ color: "var(--color-slate)" }}
        >
          {user.email}
        </div>
      </div>
      <button
        onClick={signOut}
        aria-label="Sign out"
        title="Sign out"
        className="opacity-60 hover:opacity-100 transition-opacity"
        style={{ color: "var(--color-slate)" }}
      >
        <LogOut size={14} />
      </button>
    </div>
  );
}

function LiveActivity() {
  const { data } = useSWR<RunSummary[]>(
    "sidebar-recent-runs",
    () => api.runs.list({ limit: 5 }),
    { refreshInterval: 4000, revalidateOnFocus: true },
  );

  const runs = (data ?? []).slice(0, 3);

  return (
    <div
      className="mx-2 mb-2 rounded-[12px] p-3"
      style={{ border: "1px solid var(--color-hairline)" }}
    >
      <div
        className="text-eyebrow mb-3 flex items-center justify-between"
        style={{ color: "var(--color-stone)" }}
      >
        <span>Live activity</span>
        <Link
          href="/workflows"
          className="text-micro opacity-60 hover:opacity-100 transition-opacity"
          style={{ color: "var(--color-slate)" }}
        >
          All
        </Link>
      </div>
      {runs.length === 0 ? (
        <p
          className="text-micro"
          style={{ color: "var(--color-slate)" }}
        >
          No runs yet — start one from Projects.
        </p>
      ) : (
        <div className="space-y-2.5">
          {runs.map((run) => {
            const meta = STATUS_STYLE[run.status] ?? {
              color: "#6b6e7a",
              label: run.status,
            };
            const active = run.status === "running" || run.status === "queued" || run.status === "pending";
            return (
              <Link
                key={run.id}
                href={`/workflows/${run.id}`}
                className="block"
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className="inline-block w-2 h-2 rounded-full shrink-0"
                      style={{
                        background: meta.color,
                        boxShadow: active ? `0 0 6px ${meta.color}` : undefined,
                        animation: active ? "pulse-glow 2s ease-in-out infinite" : undefined,
                      }}
                    />
                    <span
                      className="text-label truncate"
                      style={{ color: "var(--color-charcoal)" }}
                      title={run.workflow}
                    >
                      {run.workflow.replace(/_/g, " ")}
                    </span>
                  </div>
                  <span
                    className="text-micro tabular shrink-0"
                    style={{ color: meta.color }}
                  >
                    {meta.label}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, loaded } = useAuth();

  // Public marketing routes always render outside the app sidebar — they
  // bring their own MarketingShell with nav + footer.
  const MARKETING_PREFIXES = [
    "/features",
    "/about",
    "/contact",
    "/changelog",
    "/security",
    "/legal",
  ];
  const isMarketingRoute =
    !!pathname &&
    MARKETING_PREFIXES.some(
      (p) => pathname === p || pathname.startsWith(p + "/"),
    );

  const isBypassRoute =
    pathname === "/sign-in" ||
    pathname === "/sign-up" ||
    isMarketingRoute ||
    (pathname === "/pricing" && loaded && !user) ||
    (pathname === "/" && loaded && !user);

  if (isBypassRoute) {
    return (
      <div className="min-h-screen w-full" style={{ background: "var(--color-canvas)" }}>
        {children}
      </div>
    );
  }

  return (
    <div className="flex min-h-screen" style={{ background: "var(--color-canvas)" }}>
      {/* Sidebar */}
      <aside
        className="hidden md:flex w-60 shrink-0 flex-col"
        style={{
          background: "var(--color-surface)",
          borderRight: "1px solid var(--color-hairline)",
        }}
      >
        {/* Logo */}
        <div className="flex h-14 items-center justify-between px-5">
          <Link
            href="/"
            className="flex items-center gap-2.5"
            style={{ color: "var(--color-ink)" }}
          >
            {/* Helix glyph — double helix icon */}
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
              <path
                d="M5 4C5 4 8 6 11 6C14 6 17 4 17 4"
                stroke="url(#g1)"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
              <path
                d="M5 8C5 8 8 10 11 10C14 10 17 8 17 8"
                stroke="url(#g2)"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
              <path
                d="M5 12C5 12 8 14 11 14C14 14 17 12 17 12"
                stroke="url(#g1)"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
              <path
                d="M5 16C5 16 8 18 11 18C14 18 17 16 17 16"
                stroke="url(#g2)"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
              <defs>
                <linearGradient id="g1" x1="5" y1="0" x2="17" y2="0" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#ff6a4d" />
                  <stop offset="1" stopColor="#a24bff" />
                </linearGradient>
                <linearGradient id="g2" x1="5" y1="0" x2="17" y2="0" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#4d7bff" />
                  <stop offset="1" stopColor="#00d4aa" />
                </linearGradient>
              </defs>
            </svg>
            <span
              className="text-heading-sm tracking-tight"
              style={{ color: "var(--color-ink)" }}
            >
              Helix OS
            </span>
          </Link>
          <button
            aria-label="Collapse sidebar"
            className="opacity-30 hover:opacity-70 transition-opacity"
            style={{ color: "var(--color-slate)" }}
          >
            <ChevronLeft size={14} />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-2 py-2">
          {NAV.map((item) => {
            const active =
              pathname === item.href ||
              (item.href !== "/" && pathname?.startsWith(item.href));
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-[10px] px-3 py-2 mb-0.5 text-label transition-all duration-150",
                  active
                    ? "text-ink"
                    : "hover:bg-[rgba(255,255,255,0.05)]"
                )}
                style={
                  active
                    ? {
                        background: "rgba(255,255,255,0.08)",
                        color: "var(--color-ink)",
                      }
                    : { color: "var(--color-slate)" }
                }
              >
                <Icon
                  size={15}
                  className={active ? "text-[#f0f0f5]" : "text-[#6b6e7a]"}
                />
                <span>{item.label}</span>
                {active && (
                  <span
                    className="ml-auto text-micro rounded-full px-2 py-0.5"
                    style={{
                      background: "rgba(255,255,255,0.12)",
                      color: "var(--color-ink)",
                    }}
                  >
                    Active
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Live activity */}
        <LiveActivity />

        {/* Workspace Switcher */}
        <WorkspaceSwitcher />

        {/* User footer */}
        <UserFooter />

        {/* Version */}
        <div
          className="px-4 py-3 text-micro"
          style={{
            borderTop: "1px solid var(--color-hairline)",
            color: "var(--color-stone)",
          }}
        >
          Helix OS v1.0.0
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 min-w-0 overflow-hidden">
        <div className="mx-auto w-full max-w-[1400px] px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </div>
      </main>
    </div>
  );
}
