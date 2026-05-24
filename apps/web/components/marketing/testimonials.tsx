"use client";

import { motion } from "framer-motion";
import { Quote } from "lucide-react";
import { Reveal, RevealItem, RevealStagger } from "./reveal";

interface Testimonial {
  quote: string;
  author: string;
  role: string;
  company: string;
  metric: string;
  metricLabel: string;
}

const TESTIMONIALS: Testimonial[] = [
  {
    quote: "Helix cut our brand launch time from 3 weeks to 3 days. The packaging workflow alone saved us 40 hours of design work.",
    author: "Sarah Chen",
    role: "Head of Marketing",
    company: "Bowl & Basket",
    metric: "3 weeks → 3 days",
    metricLabel: "Launch time",
  },
  {
    quote: "We went from zero social presence to 60 days of scheduled content in one afternoon. The brand memory means every post stays on-message.",
    author: "Marcus Rivera",
    role: "Founder",
    company: "Taco Theory",
    metric: "60 days",
    metricLabel: "Content scheduled",
  },
  {
    quote: "The intelligence layer caught a competitor price drop and auto-adjusted our Shopify pricing before we even opened Slack.",
    author: "Aisha Patel",
    role: "E-commerce Director",
    company: "Spice Route Kitchen",
    metric: "12%",
    metricLabel: "Revenue lift",
  },
];

export function TestimonialsSection() {
  return (
    <section className="relative max-w-7xl mx-auto w-full px-6 sm:px-8 py-16 md:py-24 border-t border-white/[0.04]">
      <Reveal>
        <div className="text-center max-w-2xl mx-auto space-y-3 mb-12">
          <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-signature)]">
            Proof
          </p>
          <h2 className="font-display text-3xl sm:text-5xl font-light tracking-[-0.015em] text-white text-balance">
            Real results from real brands.
          </h2>
        </div>
      </Reveal>

      <RevealStagger className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {TESTIMONIALS.map((t, i) => (
          <RevealItem key={i}>
            <motion.div
              whileHover={{ y: -4 }}
              className="relative p-6 rounded-2xl border border-white/[0.05] bg-[#0d0e12]/50 backdrop-blur-md h-full flex flex-col"
            >
              <Quote size={20} className="text-[var(--color-signature)] mb-4 opacity-60" />
              
              <p className="text-[14px] leading-relaxed text-[var(--color-slate)] mb-6 flex-1">
                {t.quote}
              </p>

              <div className="pt-4 border-t border-white/[0.04]">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="text-[13px] font-semibold text-white">{t.author}</p>
                    <p className="text-[11px] text-[var(--color-stone)]">
                      {t.role} · {t.company}
                    </p>
                  </div>
                </div>
                
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/8 border border-emerald-500/15">
                  <span className="text-[13px] font-bold text-emerald-400">{t.metric}</span>
                  <span className="text-[10px] text-emerald-400/70">{t.metricLabel}</span>
                </div>
              </div>
            </motion.div>
          </RevealItem>
        ))}
      </RevealStagger>
    </section>
  );
}
