"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, CheckCircle2, Mail, MessageSquare } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MarketingShell } from "@/components/layout/marketing-shell";

/**
 * /contact — real intake form.
 *
 * POSTs to /api/contact which validates input server-side and persists the
 * submission to a JSONL log. No third-party mock service.
 */

const TOPICS = [
  "Product question",
  "Sales / pricing",
  "Partnership",
  "Press",
  "Support",
  "Other",
];

interface FormState {
  name: string;
  email: string;
  company: string;
  topic: string;
  message: string;
}

const EMPTY_STATE: FormState = {
  name: "",
  email: "",
  company: "",
  topic: TOPICS[0],
  message: "",
};

export default function ContactPage() {
  const [form, setForm] = useState<FormState>(EMPTY_STATE);
  const [submitting, setSubmitting] = useState(false);
  const [submittedId, setSubmittedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, source: "contact-page" }),
      });
      const body = (await res.json().catch(() => ({}))) as {
        ok?: boolean;
        id?: string;
        error?: string;
      };
      if (!res.ok || !body.ok) {
        throw new Error(body.error ?? `Request failed (${res.status})`);
      }
      setSubmittedId(body.id ?? "received");
      setForm(EMPTY_STATE);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <MarketingShell>
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10 opacity-60">
          <div className="absolute top-[-15%] left-[10%] w-[480px] h-[480px] rounded-full blur-[140px] bg-[#4d7bff]/15" />
          <div className="absolute top-[25%] right-[5%] w-[480px] h-[480px] rounded-full blur-[140px] bg-[#a24bff]/15" />
        </div>
        <div className="max-w-7xl mx-auto px-6 sm:px-8 pt-24 pb-12">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
            {/* Left: copy */}
            <div>
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/[0.08] text-[10px] font-bold uppercase tracking-[0.18em] text-white/70 bg-white/[0.02]">
                <Mail size={11} />
                Contact
              </span>
              <h1 className="font-display mt-7 text-[clamp(2.2rem,4.5vw,3.8rem)] font-light leading-[1.04] tracking-[-0.025em] text-balance">
                Talk to a human about{" "}
                <span className="font-display-italic text-gradient-signature font-normal">
                  Helix
                </span>
                .
              </h1>
              <p className="mt-6 text-[15px] leading-relaxed text-[var(--color-slate)] max-w-xl">
                Questions about the product, pricing, or how Helix would fit
                your team? Send a note and we&apos;ll get back to you. For
                support, sign in first so we can find your workspace.
              </p>

              <div className="mt-10 space-y-5">
                <div className="flex items-start gap-3">
                  <span className="mt-1 inline-flex w-9 h-9 rounded-lg items-center justify-center bg-white/[0.04] border border-white/[0.08]">
                    <MessageSquare size={15} className="text-white" />
                  </span>
                  <div>
                    <div className="text-[13px] font-semibold text-white">
                      In-product chat
                    </div>
                    <div className="text-[13px] text-[var(--color-slate)]">
                      Already on Helix? Open the chat surface to ping the
                      operating system directly.
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <span className="mt-1 inline-flex w-9 h-9 rounded-lg items-center justify-center bg-white/[0.04] border border-white/[0.08]">
                    <Mail size={15} className="text-white" />
                  </span>
                  <div>
                    <div className="text-[13px] font-semibold text-white">
                      Email replies
                    </div>
                    <div className="text-[13px] text-[var(--color-slate)]">
                      We respond directly from a real inbox. No bots, no
                      ticketing.
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right: form */}
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-7 md:p-9">
              {submittedId ? (
                <div className="flex flex-col items-center text-center py-10">
                  <span className="inline-flex w-14 h-14 rounded-full items-center justify-center bg-[#00d4aa]/15 border border-[#00d4aa]/30">
                    <CheckCircle2 size={28} className="text-[#00d4aa]" />
                  </span>
                  <h2 className="mt-6 text-xl font-bold tracking-tight text-white">
                    Thanks — we got it.
                  </h2>
                  <p className="mt-3 text-[14px] text-[var(--color-slate)] max-w-sm">
                    Your message was received. Expect a reply from a real
                    person at the email you provided.
                  </p>
                  <div className="mt-7 flex flex-wrap gap-3 justify-center">
                    <Button
                      variant="secondary"
                      size="md"
                      onClick={() => setSubmittedId(null)}
                    >
                      Send another
                    </Button>
                    <Link href="/sign-up">
                      <Button variant="glow" size="md">
                        Get started
                        <ArrowRight size={14} className="ml-2" />
                      </Button>
                    </Link>
                  </div>
                </div>
              ) : (
                <form onSubmit={onSubmit} className="space-y-5">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Field
                      label="Full name"
                      required
                      value={form.name}
                      onChange={(v) => update("name", v)}
                      placeholder="Jane Cooper"
                      autoComplete="name"
                    />
                    <Field
                      label="Work email"
                      required
                      type="email"
                      value={form.email}
                      onChange={(v) => update("email", v)}
                      placeholder="jane@brand.co"
                      autoComplete="email"
                    />
                  </div>
                  <Field
                    label="Company"
                    value={form.company}
                    onChange={(v) => update("company", v)}
                    placeholder="Brand or studio"
                    autoComplete="organization"
                  />
                  <div className="space-y-2">
                    <label className="block text-[11px] font-bold uppercase tracking-[0.16em] text-[var(--color-stone)]">
                      Topic
                    </label>
                    <select
                      value={form.topic}
                      onChange={(e) => update("topic", e.target.value)}
                      className="w-full h-11 rounded-xl bg-white/[0.03] border border-white/[0.08] px-3 text-[14px] text-white focus:outline-none focus:ring-2 focus:ring-white/20 focus:border-white/20"
                    >
                      {TOPICS.map((t) => (
                        <option
                          key={t}
                          value={t}
                          className="bg-[#0a0b0e] text-white"
                        >
                          {t}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="block text-[11px] font-bold uppercase tracking-[0.16em] text-[var(--color-stone)]">
                      Message
                    </label>
                    <textarea
                      required
                      minLength={10}
                      maxLength={4000}
                      value={form.message}
                      onChange={(e) => update("message", e.target.value)}
                      placeholder="Tell us what you're working on and what you're trying to solve."
                      rows={6}
                      className="w-full rounded-xl bg-white/[0.03] border border-white/[0.08] px-3 py-3 text-[14px] text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-white/20 focus:border-white/20 resize-none"
                    />
                  </div>

                  {error && (
                    <div className="text-[13px] text-[#ff5470] bg-[#ff5470]/10 border border-[#ff5470]/20 rounded-lg px-3 py-2">
                      {error}
                    </div>
                  )}

                  <Button
                    type="submit"
                    variant="glow"
                    size="lg"
                    className="w-full font-bold uppercase tracking-wider"
                    disabled={submitting}
                  >
                    {submitting ? "Sending…" : "Send message"}
                    {!submitting && <ArrowRight size={14} className="ml-2" />}
                  </Button>
                  <p className="text-[11px] text-[var(--color-stone)] text-center">
                    By submitting, you agree to our{" "}
                    <Link
                      href="/legal/privacy"
                      className="underline hover:text-white"
                    >
                      privacy policy
                    </Link>
                    .
                  </p>
                </form>
              )}
            </div>
          </div>
        </div>
      </section>
    </MarketingShell>
  );
}

function Field(props: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  required?: boolean;
  type?: string;
  autoComplete?: string;
}) {
  return (
    <div className="space-y-2">
      <label className="block text-[11px] font-bold uppercase tracking-[0.16em] text-[var(--color-stone)]">
        {props.label}
        {props.required && <span className="text-[#ff6a4d] ml-1">*</span>}
      </label>
      <input
        type={props.type ?? "text"}
        required={props.required}
        value={props.value}
        onChange={(e) => props.onChange(e.target.value)}
        placeholder={props.placeholder}
        autoComplete={props.autoComplete}
        className="w-full h-11 rounded-xl bg-white/[0.03] border border-white/[0.08] px-3 text-[14px] text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-white/20 focus:border-white/20"
      />
    </div>
  );
}
