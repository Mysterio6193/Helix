"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MotionBackground } from "@/components/marketing/motion-background";
import { api, type AuthStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

/**
 * Shared shell for all public (unauthenticated) marketing pages.
 *
 * Renders top navigation + footer around children. Auth state is checked
 * client-side so the CTA can switch between "Sign in / Get started" and
 * "Open dashboard" for already-authenticated visitors.
 */

const NAV_LINKS: { href: string; label: string }[] = [
  { href: "/features", label: "Features" },
  { href: "/pricing", label: "Pricing" },
  { href: "/about", label: "About" },
  { href: "/changelog", label: "Changelog" },
  { href: "/security", label: "Security" },
  { href: "/contact", label: "Contact" },
];

function HelixMark() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden>
      <path
        d="M5 4C5 4 8 6 11 6C14 6 17 4 17 4"
        stroke="url(#mg1)"
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      <path
        d="M5 12C5 12 8 14 11 14C14 14 17 12 17 12"
        stroke="url(#mg1)"
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      <defs>
        <linearGradient
          id="mg1"
          x1="5"
          y1="0"
          x2="17"
          y2="0"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#ff6a4d" />
          <stop offset="1" stopColor="#a24bff" />
        </linearGradient>
      </defs>
    </svg>
  );
}

export function MarketingNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [auth, setAuth] = useState<AuthStatus | null>(null);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    let alive = true;
    api.auth
      .me()
      .then((r) => {
        if (alive) setAuth(r);
      })
      .catch(() => {
        if (alive) setAuth({ authenticated: false });
      });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 8);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  const isAuthed = auth?.authenticated === true;

  return (
    <header
      className={cn(
        "sticky top-0 z-50 w-full transition-all duration-200",
        scrolled
          ? "bg-[#07080a]/85 backdrop-blur-xl border-b border-white/[0.05]"
          : "bg-transparent border-b border-transparent",
      )}
    >
      <div className="max-w-7xl mx-auto flex h-16 items-center justify-between px-6 sm:px-8">
        <Link href="/" className="flex items-center gap-2.5">
          <HelixMark />
          <span className="text-lg font-bold tracking-tight text-white">
            Helix
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-7 text-[12px] font-semibold text-[var(--color-slate)] tracking-wide">
          {NAV_LINKS.map((l) => {
            const active =
              pathname === l.href ||
              (l.href !== "/" && pathname?.startsWith(l.href));
            return (
              <Link
                key={l.href}
                href={l.href}
                className={cn(
                  "hover:text-white transition-colors",
                  active && "text-white",
                )}
              >
                {l.label}
              </Link>
            );
          })}
        </nav>

        <div className="hidden md:flex items-center gap-3">
          {isAuthed ? (
            <Link href="/overview">
              <Button
                variant="glow"
                size="sm"
                className="h-9 px-4 text-[11px] font-bold uppercase tracking-wider rounded-xl"
              >
                Open dashboard
              </Button>
            </Link>
          ) : (
            <>
              <Link
                href="/sign-in"
                className="text-[12px] font-semibold text-[var(--color-slate)] hover:text-white transition-colors"
              >
                Sign in
              </Link>
              <Link href="/sign-up">
                <Button
                  variant="glow"
                  size="sm"
                  className="h-9 px-4 text-[11px] font-bold uppercase tracking-wider rounded-xl"
                >
                  Get started
                </Button>
              </Link>
            </>
          )}
        </div>

        {/* Mobile toggle */}
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="md:hidden inline-flex items-center justify-center w-9 h-9 rounded-lg border border-white/[0.08] text-white/80"
          aria-label="Toggle menu"
        >
          {open ? <X size={16} /> : <Menu size={16} />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden border-t border-white/[0.05] bg-[#07080a]/95 backdrop-blur-xl">
          <div className="px-6 py-4 flex flex-col gap-1">
            {NAV_LINKS.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="py-2 text-sm font-semibold text-white/70 hover:text-white"
              >
                {l.label}
              </Link>
            ))}
            <div className="pt-3 mt-2 border-t border-white/[0.05] flex flex-col gap-2">
              {isAuthed ? (
                <Link href="/overview">
                  <Button
                    variant="glow"
                    className="w-full h-10 text-[11px] font-bold uppercase tracking-wider"
                  >
                    Open dashboard
                  </Button>
                </Link>
              ) : (
                <>
                  <Link href="/sign-in">
                    <Button
                      variant="secondary"
                      className="w-full h-10 text-[12px] font-semibold"
                    >
                      Sign in
                    </Button>
                  </Link>
                  <Link href="/sign-up">
                    <Button
                      variant="glow"
                      className="w-full h-10 text-[11px] font-bold uppercase tracking-wider"
                    >
                      Get started
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

export function MarketingFooter() {
  const year = new Date().getFullYear();
  return (
    <footer className="relative w-full border-t border-white/[0.04] bg-[#08090d]/60 py-14 z-10">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 grid grid-cols-2 md:grid-cols-5 gap-8">
        <div className="col-span-2 md:col-span-2 space-y-4">
          <Link href="/" className="flex items-center gap-2.5">
            <HelixMark />
            <span className="text-lg font-bold tracking-tight text-white">
              Helix
            </span>
          </Link>
          <p className="text-[13px] leading-relaxed text-[var(--color-slate)] max-w-sm">
            The AI-native creative operating system for restaurants and food
            brands. Strategy, creative, and campaigns — running together.
          </p>
        </div>

        <div className="space-y-3">
          <h4 className="text-[11px] font-bold uppercase tracking-widest text-white/80">
            Product
          </h4>
          <ul className="space-y-2 text-[13px] text-[var(--color-slate)]">
            <li>
              <Link href="/features" className="hover:text-white transition">
                Features
              </Link>
            </li>
            <li>
              <Link href="/pricing" className="hover:text-white transition">
                Pricing
              </Link>
            </li>
            <li>
              <Link href="/changelog" className="hover:text-white transition">
                Changelog
              </Link>
            </li>
            <li>
              <Link href="/security" className="hover:text-white transition">
                Security
              </Link>
            </li>
          </ul>
        </div>

        <div className="space-y-3">
          <h4 className="text-[11px] font-bold uppercase tracking-widest text-white/80">
            Company
          </h4>
          <ul className="space-y-2 text-[13px] text-[var(--color-slate)]">
            <li>
              <Link href="/about" className="hover:text-white transition">
                About
              </Link>
            </li>
            <li>
              <Link href="/contact" className="hover:text-white transition">
                Contact
              </Link>
            </li>
            <li>
              <Link href="/sign-in" className="hover:text-white transition">
                Sign in
              </Link>
            </li>
            <li>
              <Link href="/sign-up" className="hover:text-white transition">
                Get started
              </Link>
            </li>
          </ul>
        </div>

        <div className="space-y-3">
          <h4 className="text-[11px] font-bold uppercase tracking-widest text-white/80">
            Legal
          </h4>
          <ul className="space-y-2 text-[13px] text-[var(--color-slate)]">
            <li>
              <Link
                href="/legal/privacy"
                className="hover:text-white transition"
              >
                Privacy
              </Link>
            </li>
            <li>
              <Link href="/legal/terms" className="hover:text-white transition">
                Terms
              </Link>
            </li>
            <li>
              <Link href="/security" className="hover:text-white transition">
                Security
              </Link>
            </li>
          </ul>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 sm:px-8 mt-12 pt-6 border-t border-white/[0.04] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-[12px] text-[var(--color-stone)]">
        <span>© {year} Helix. All rights reserved.</span>
        <span className="text-[11px] uppercase tracking-widest">
          Built for brands that move fast.
        </span>
      </div>
    </footer>
  );
}

export function MarketingShell({
  children,
  bgVariant = "default",
}: {
  children: React.ReactNode;
  bgVariant?: "default" | "warm" | "cool" | "green" | "purple";
}) {
  return (
    <div className="min-h-screen bg-[#07080a] text-white flex flex-col overflow-x-hidden font-sans relative selection:bg-purple-500/30 selection:text-white">
      <MotionBackground variant={bgVariant} />
      <MarketingNav />
      <main className="flex-1 relative z-10">{children}</main>
      <MarketingFooter />
    </div>
  );
}
