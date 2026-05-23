"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useRef } from "react";

/**
 * Shared animated background for all guest / marketing pages.
 *
 * Layers:
 *  1. Three drifting aurora blobs (framer-motion `animate`).
 *  2. Slow-panning conic gradient sheen.
 *  3. Subtle dotted grid that fades from top.
 *  4. Mouse-tracked spotlight (canvas-light, no listener spam).
 *
 * Honors `prefers-reduced-motion`: collapses to a static gradient.
 */

const PALETTES: Record<
  string,
  { a: string; b: string; c: string }
> = {
  default: { a: "#ff6a4d", b: "#a24bff", c: "#4d7bff" },
  warm: { a: "#ff6a4d", b: "#ff3d7f", c: "#ffb347" },
  cool: { a: "#4d7bff", b: "#00d4aa", c: "#a24bff" },
  green: { a: "#00d4aa", b: "#4d7bff", c: "#a24bff" },
  purple: { a: "#a24bff", b: "#ff3d7f", c: "#4d7bff" },
};

export function MotionBackground({
  variant = "default",
  spotlight = true,
}: {
  variant?: keyof typeof PALETTES;
  spotlight?: boolean;
}) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const palette = PALETTES[variant] ?? PALETTES.default;

  useEffect(() => {
    if (!spotlight || reduce) return;
    const el = ref.current;
    if (!el) return;
    let raf = 0;
    let tx = window.innerWidth / 2;
    let ty = window.innerHeight / 3;
    let cx = tx;
    let cy = ty;
    function onMove(e: MouseEvent) {
      tx = e.clientX;
      ty = e.clientY;
    }
    function tick() {
      cx += (tx - cx) * 0.08;
      cy += (ty - cy) * 0.08;
      if (el) {
        el.style.background = `radial-gradient(600px circle at ${cx}px ${cy}px, rgba(255,255,255,0.05), transparent 60%)`;
      }
      raf = requestAnimationFrame(tick);
    }
    window.addEventListener("pointermove", onMove, { passive: true });
    raf = requestAnimationFrame(tick);
    return () => {
      window.removeEventListener("pointermove", onMove);
      cancelAnimationFrame(raf);
    };
  }, [spotlight, reduce]);

  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
    >
      {/* Base ink */}
      <div className="absolute inset-0 bg-[#07080a]" />

      {/* Conic sheen — slow pan */}
      {!reduce && (
        <motion.div
          className="absolute inset-0 opacity-[0.18]"
          style={{
            background: `conic-gradient(from 0deg at 50% 50%, ${palette.a}33, transparent 25%, ${palette.b}33 50%, transparent 75%, ${palette.c}33)`,
            filter: "blur(80px)",
          }}
          animate={{ rotate: 360 }}
          transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
        />
      )}

      {/* Aurora blob 1 */}
      <motion.div
        className="absolute rounded-full"
        style={{
          width: 720,
          height: 720,
          left: "-10%",
          top: "-15%",
          background: `radial-gradient(circle, ${palette.a}38 0%, transparent 60%)`,
          filter: "blur(80px)",
        }}
        animate={
          reduce
            ? undefined
            : {
                x: [0, 80, -40, 0],
                y: [0, 60, 30, 0],
                scale: [1, 1.08, 0.96, 1],
              }
        }
        transition={{ duration: 22, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Aurora blob 2 */}
      <motion.div
        className="absolute rounded-full"
        style={{
          width: 620,
          height: 620,
          right: "-8%",
          top: "10%",
          background: `radial-gradient(circle, ${palette.b}38 0%, transparent 60%)`,
          filter: "blur(80px)",
        }}
        animate={
          reduce
            ? undefined
            : {
                x: [0, -70, 40, 0],
                y: [0, 50, -30, 0],
                scale: [1, 0.94, 1.06, 1],
              }
        }
        transition={{
          duration: 26,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 1.5,
        }}
      />

      {/* Aurora blob 3 */}
      <motion.div
        className="absolute rounded-full"
        style={{
          width: 560,
          height: 560,
          left: "30%",
          bottom: "-15%",
          background: `radial-gradient(circle, ${palette.c}33 0%, transparent 60%)`,
          filter: "blur(80px)",
        }}
        animate={
          reduce
            ? undefined
            : {
                x: [0, -60, 50, 0],
                y: [0, -40, 20, 0],
                scale: [1, 1.05, 0.95, 1],
              }
        }
        transition={{
          duration: 30,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 3,
        }}
      />

      {/* Dotted grid */}
      <div
        className="absolute inset-0 opacity-[0.06]"
        style={{
          backgroundImage:
            "radial-gradient(rgba(255,255,255,0.6) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
          maskImage:
            "linear-gradient(to bottom, black 0%, black 40%, transparent 100%)",
          WebkitMaskImage:
            "linear-gradient(to bottom, black 0%, black 40%, transparent 100%)",
        }}
      />

      {/* Mouse spotlight */}
      {spotlight && (
        <div
          ref={ref}
          className="absolute inset-0 opacity-80 transition-opacity"
        />
      )}

      {/* Vignette */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 0%, transparent 60%, rgba(0,0,0,0.5) 100%)",
        }}
      />
    </div>
  );
}
