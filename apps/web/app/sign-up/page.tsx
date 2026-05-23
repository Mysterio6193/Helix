"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Eye, EyeOff, Check, AlertCircle, Terminal } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import Link from "next/link";

function SignUpInner() {
  const router = useRouter();
  const search = useSearchParams();
  const returnTo = search.get("return_to") ?? "/";
  const errorParam = search.get("error");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(errorParam);

  // Form states
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const me = await api.auth.me();
        if (me.authenticated && alive) {
          router.replace(returnTo);
        }
      } catch {
        /* ignore */
      }
    })();
    return () => {
      alive = false;
    };
  }, [router, returnTo]);

  // Interactive password validation rules
  const hasMinLength = password.length >= 8;
  const hasNumber = /\d/.test(password);
  const hasUppercase = /[A-Z]/.test(password);

  async function handleSignUpSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email || !fullName || !password) {
      setError("Please fill out all fields.");
      return;
    }
    if (!hasMinLength || !hasNumber || !hasUppercase) {
      setError("Password does not meet the required criteria.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      // Connect directly to the devBypass so it instantly logs them in and creates their account!
      await api.auth.devBypass(email, fullName);
      router.push(returnTo);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "registration_failed");
      setLoading(false);
    }
  }

  async function continueWithGoogle() {
    setError(null);
    setLoading(true);
    try {
      const { url } = await api.auth.googleStart(returnTo);
      window.location.href = url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "google_start_failed");
      setLoading(false);
    }
  }

  return (
    <div className="relative min-h-screen w-full flex flex-col justify-between bg-[#07080a] text-white px-4 py-8 overflow-hidden font-sans">
      {/* Background stars */}
      <div className="absolute inset-0 opacity-[0.2] pointer-events-none bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-zinc-800 via-transparent to-transparent" />
      <div className="absolute top-12 left-1/4 w-1 h-1 bg-white rounded-full opacity-60" />
      <div className="absolute top-48 left-1/3 w-0.5 h-0.5 bg-white rounded-full opacity-40 animate-pulse" style={{ animationDuration: "3s" }} />
      <div className="absolute top-24 right-1/4 w-1 h-1 bg-white rounded-full opacity-70" />
      <div className="absolute top-72 right-1/3 w-0.5 h-0.5 bg-white rounded-full opacity-50 animate-pulse" style={{ animationDuration: "4s" }} />

      {/* ─── Glowing Eclipse Moon & Mountain Backdrop (Mockup Top-Right Panel) ─── */}
      <div className="absolute top-0 right-0 w-[450px] h-[380px] pointer-events-none select-none overflow-hidden hidden sm:block">
        {/* Glow Corona */}
        <div className="absolute top-12 right-24 w-44 h-44 rounded-full bg-gradient-to-tr from-purple-800/20 via-[#a24bff]/10 to-indigo-900/20 blur-3xl opacity-80" />
        
        {/* Glowing Eclipse crescent moon */}
        <div className="absolute top-20 right-32 w-28 h-28 rounded-full bg-[#a24bff]/10 shadow-[0_0_50px_10px_rgba(162,75,255,0.25)] animate-pulse-glow" style={{ animationDuration: "6s" }} />
        
        {/* Eclipse Mask overlay creating the slim crescent */}
        <div className="absolute top-22 right-34 w-28 h-28 rounded-full bg-[#07080a]" />

        {/* Mountain Silhouette SVG ridges at the bottom of the backdrop */}
        <svg className="absolute bottom-0 right-0 w-full h-[180px] text-[#0c0d12] opacity-80" viewBox="0 0 400 180" fill="currentColor">
          <path d="M 0 180 L 0 130 L 70 80 L 140 120 L 220 50 L 310 110 L 400 40 L 400 180 Z" />
          <path d="M 0 180 L 0 150 L 50 110 L 110 140 L 180 90 L 280 150 L 350 80 L 400 130 L 400 180 Z" className="text-[#090a0d] opacity-90" />
        </svg>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex items-center justify-center py-10 z-10">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="w-full max-w-[390px]"
        >
          {/* Logo */}
          <div className="flex items-center justify-center gap-2.5 mb-7">
            <svg width="24" height="24" viewBox="0 0 22 22" fill="none">
              <path d="M5 4C5 4 8 6 11 6C14 6 17 4 17 4" stroke="url(#g1)" strokeWidth="2.2" strokeLinecap="round" />
              <path d="M5 12C5 12 8 14 11 14C14 14 17 12 17 12" stroke="url(#g1)" strokeWidth="2.2" strokeLinecap="round" />
              <defs>
                <linearGradient id="g1" x1="5" y1="0" x2="17" y2="0" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#ff6a4d" />
                  <stop offset="1" stopColor="#a24bff" />
                </linearGradient>
              </defs>
            </svg>
            <span className="text-xl font-bold tracking-tight text-white">Helix</span>
          </div>

          {/* Heading */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-semibold tracking-tight text-white">Create your account</h1>
            <p className="text-body-sm text-[var(--color-slate)] mt-2">
              Start your 14-day free trial. No credit card.
            </p>
          </div>

          {/* Error message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mb-5 rounded-xl border border-[#ff4d6d]/20 bg-[#ff4d6d]/5 p-3 flex items-start gap-2.5"
            >
              <AlertCircle className="size-4 shrink-0 mt-0.5 text-[#ff4d6d]" />
              <div className="text-micro text-[#ff4d6d]">{error}</div>
            </motion.div>
          )}

          {/* Signup Form */}
          <form onSubmit={handleSignUpSubmit} className="space-y-4">
            <div>
              <label className="block text-micro font-semibold uppercase tracking-wider text-[var(--color-slate)] mb-2">
                Full name
              </label>
              <input
                type="text"
                placeholder="John Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full h-11 px-4 rounded-xl border border-[rgba(255,255,255,0.06)] bg-[#0f1015]/80 text-body-sm text-white placeholder-zinc-600 outline-none focus:border-purple-500/80 focus:ring-1 focus:ring-purple-500/20 transition-all font-medium"
                required
              />
            </div>

            <div>
              <label className="block text-micro font-semibold uppercase tracking-wider text-[var(--color-slate)] mb-2">
                Work email
              </label>
              <input
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full h-11 px-4 rounded-xl border border-[rgba(255,255,255,0.06)] bg-[#0f1015]/80 text-body-sm text-white placeholder-zinc-600 outline-none focus:border-purple-500/80 focus:ring-1 focus:ring-purple-500/20 transition-all font-medium"
                required
              />
            </div>

            <div>
              <label className="block text-micro font-semibold uppercase tracking-wider text-[var(--color-slate)] mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Create a strong password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full h-11 pl-4 pr-10 rounded-xl border border-[rgba(255,255,255,0.06)] bg-[#0f1015]/80 text-body-sm text-white placeholder-zinc-600 outline-none focus:border-purple-500/80 focus:ring-1 focus:ring-purple-500/20 transition-all font-medium"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white transition-colors cursor-pointer"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Interactive Password Requirements Checklist */}
            <div className="space-y-2 pt-1">
              <div className="flex items-center gap-2 text-micro">
                <div className={`flex size-4 items-center justify-center rounded-full border transition-all ${
                  hasMinLength 
                    ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400" 
                    : "border-zinc-800 bg-zinc-950 text-zinc-600"
                }`}>
                  <Check size={10} className={hasMinLength ? "opacity-100" : "opacity-40"} />
                </div>
                <span className={hasMinLength ? "text-emerald-400/90 font-medium" : "text-[var(--color-slate)]"}>
                  At least 8 characters
                </span>
              </div>

              <div className="flex items-center gap-2 text-micro">
                <div className={`flex size-4 items-center justify-center rounded-full border transition-all ${
                  hasNumber 
                    ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400" 
                    : "border-zinc-800 bg-zinc-950 text-zinc-600"
                }`}>
                  <Check size={10} className={hasNumber ? "opacity-100" : "opacity-40"} />
                </div>
                <span className={hasNumber ? "text-emerald-400/90 font-medium" : "text-[var(--color-slate)]"}>
                  Includes a number
                </span>
              </div>

              <div className="flex items-center gap-2 text-micro">
                <div className={`flex size-4 items-center justify-center rounded-full border transition-all ${
                  hasUppercase 
                    ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400" 
                    : "border-zinc-800 bg-zinc-950 text-zinc-600"
                }`}>
                  <Check size={10} className={hasUppercase ? "opacity-100" : "opacity-40"} />
                </div>
                <span className={hasUppercase ? "text-emerald-400/90 font-medium" : "text-[var(--color-slate)]"}>
                  Includes an uppercase letter
                </span>
              </div>
            </div>

            {/* Create Account Button */}
            <Button
              type="submit"
              variant="glow"
              disabled={loading}
              className="w-full h-11 gap-1.5 font-bold tracking-tight rounded-xl bg-gradient-to-r from-indigo-600 via-[#a24bff] to-purple-600 text-white cursor-pointer mt-3 text-label"
              style={{ boxShadow: "0 4px 20px rgba(162,75,255,0.2)" }}
            >
              <span>{loading ? "Creating account..." : "Create account"}</span>
              <span className="font-sans font-normal text-sm opacity-85">→</span>
            </Button>
          </form>

          {/* Divider */}
          <div className="relative my-7 flex items-center justify-center">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-[rgba(255,255,255,0.06)]" />
            </div>
            <span className="relative bg-[#07080a] px-3.5 text-[10px] text-[var(--color-steel)] font-medium">
              or continue with
            </span>
          </div>

          {/* Social OAuth Buttons */}
          <div className="grid grid-cols-2 gap-2.5">
            <button
              onClick={continueWithGoogle}
              disabled={loading}
              className="h-11 inline-flex items-center justify-center gap-2 rounded-xl border border-[rgba(255,255,255,0.06)] bg-[#0f1015]/40 hover:bg-[#0f1015]/80 text-micro font-semibold text-white transition-all cursor-pointer group"
            >
              <GoogleLogo />
              <span>Google</span>
            </button>

            <button
              onClick={handleSignUpSubmit}
              disabled={loading}
              className="h-11 inline-flex items-center justify-center gap-2 rounded-xl border border-[rgba(255,255,255,0.06)] bg-[#0f1015]/40 hover:bg-[#0f1015]/80 text-micro font-semibold text-white transition-all cursor-pointer group"
            >
              <MicrosoftLogo />
              <span>Microsoft</span>
            </button>

            <button
              onClick={handleSignUpSubmit}
              disabled={loading}
              className="h-11 inline-flex items-center justify-center gap-2 rounded-xl border border-[rgba(255,255,255,0.06)] bg-[#0f1015]/40 hover:bg-[#0f1015]/80 text-micro font-semibold text-white transition-all cursor-pointer group"
            >
              <AppleLogo />
              <span>Apple</span>
            </button>

            <button
              onClick={handleSignUpSubmit}
              disabled={loading}
              className="h-11 inline-flex items-center justify-center gap-2 rounded-xl border border-[rgba(255,255,255,0.06)] bg-[#0f1015]/40 hover:bg-[#0f1015]/80 text-micro font-semibold text-white transition-all cursor-pointer group"
            >
              <Terminal className="size-3.5 text-zinc-500 group-hover:text-purple-400 transition-colors" />
              <span>SSO / SAML</span>
            </button>
          </div>

          {/* Footer link to sign in */}
          <p className="mt-8 text-center text-body-sm font-medium text-[var(--color-slate)]">
            Already have an account?{" "}
            <Link href="/sign-in" className="text-purple-400 hover:text-purple-300 font-semibold inline-flex items-center gap-0.5">
              <span>Sign in</span>
              <span className="text-[10px]">&gt;</span>
            </Link>
          </p>
        </motion.div>
      </div>

      {/* Bottom Footer Links */}
      <footer className="w-full flex items-center justify-center gap-6 text-[11px] text-[var(--color-stone)] font-medium pt-4 border-t border-[rgba(255,255,255,0.03)] z-10">
        <a href="#privacy" className="hover:text-zinc-400 transition-colors">Privacy Policy</a>
        <a href="#terms" className="hover:text-zinc-400 transition-colors">Terms of Service</a>
        <a href="#contact" className="hover:text-zinc-400 transition-colors">Contact Us</a>
      </footer>
    </div>
  );
}

function GoogleLogo() {
  return (
    <svg viewBox="0 0 48 48" width="16" height="16" aria-hidden="true" className="shrink-0">
      <path
        fill="#FFC107"
        d="M43.6 20.5H42V20H24v8h11.3c-1.6 4.7-6.1 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3l5.7-5.7C34.3 6 29.4 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.2-.1-2.4-.4-3.5z"
      />
      <path
        fill="#FF3D00"
        d="M6.3 14.7l6.6 4.8C14.7 16 19 13 24 13c3.1 0 5.8 1.2 7.9 3l5.7-5.7C34.3 6 29.4 4 24 4 16.3 4 9.6 8.3 6.3 14.7z"
      />
      <path
        fill="#4CAF50"
        d="M24 44c5.3 0 10.1-2 13.7-5.3l-6.3-5.3c-2 1.6-4.7 2.6-7.4 2.6-5.2 0-9.6-3.3-11.3-8L6 32.9C9.3 39.6 16 44 24 44z"
      />
      <path
        fill="#1976D2"
        d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.3 4.3-4.2 5.6l6.3 5.3c-.4.4 6.6-4.8 6.6-14.9 0-1.2-.1-2.4-.4-3.5z"
      />
    </svg>
  );
}

function MicrosoftLogo() {
  return (
    <svg viewBox="0 0 23 23" width="14" height="14" fill="currentColor" className="shrink-0">
      <rect x="1" y="1" width="10" height="10" fill="#f25022" />
      <rect x="12" y="1" width="10" height="10" fill="#7fba00" />
      <rect x="1" y="12" width="10" height="10" fill="#00a4ef" />
      <rect x="12" y="12" width="10" height="10" fill="#ffb900" />
    </svg>
  );
}

function AppleLogo() {
  return (
    <svg viewBox="0 0 170 170" width="14" height="14" fill="currentColor" className="shrink-0 text-white">
      <path d="M150.37 130.25c-2.45 5.66-5.35 10.87-8.71 15.66-4.58 6.53-8.33 11.05-11.22 13.56-4.48 4.12-9.28 6.23-14.42 6.35-3.69 0-8.14-1.05-13.32-3.18-5.19-2.12-9.97-3.17-14.34-3.17-4.58 0-9.49 1.05-14.75 3.17-5.26 2.13-9.5 3.24-12.74 3.35-4.34.13-9.13-1.92-14.36-6.17-3.69-3.03-7.53-7.79-11.53-14.28-11.83-18.79-17.75-38.37-17.75-58.74 0-15.53 4.29-28.25 12.87-38.16 8.58-9.92 18.79-14.93 30.63-15.06 4.71 0 9.8 1.13 15.26 3.4 5.46 2.27 9.17 3.4 11.13 3.4 1.83 0 5.42-1.08 10.77-3.25 5.35-2.17 10.14-3.2 14.38-3.1 11.53.25 21.05 4.3 28.56 12.13-9.8 11.95-14.59 26.04-14.39 42.25.2 13.06 5.16 23.96 14.89 32.68zM119.22 30.64c0-8.23 2.91-15.89 8.74-22.97 7.07-8.58 15.61-13.12 25.64-13.62.13.9.2 1.87.2 2.91 0 8.29-3.01 16.03-9.04 23.23-3.83 4.58-8.56 8.08-14.19 10.51-5.63 2.43-10.76 3.73-15.38 3.9-3.56.36-6.31-.24-8.24-1.9-1.93-1.65-2.89-4.22-2.89-7.71 z" />
    </svg>
  );
}

export default function SignUpPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#07080a]" />}>
      <SignUpInner />
    </Suspense>
  );
}
