"use client";

import { forwardRef } from "react";

import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "tertiary" | "link" | "icon" | "glow";
type Size = "sm" | "md" | "lg";

interface Props extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  asChild?: never;
}

const SIZE: Record<Size, string> = {
  sm: "h-8 px-3.5 text-label",
  md: "h-10 px-5 text-label",
  lg: "h-12 px-6 text-body-md font-medium",
};

const VARIANT: Record<Variant, string> = {
  primary:
    "bg-[color:var(--color-ink)] text-[color:var(--color-canvas)] hover:opacity-90 active:opacity-80",
  secondary:
    "border text-[color:var(--color-charcoal)] hover:bg-[rgba(255,255,255,0.06)] hover:text-[color:var(--color-ink)] active:opacity-80",
  tertiary:
    "bg-[color:var(--color-surface-elev)] text-[color:var(--color-charcoal)] hover:bg-[rgba(255,255,255,0.1)] hover:text-[color:var(--color-ink)]",
  link:
    "bg-transparent text-[color:var(--color-slate)] hover:text-[color:var(--color-ink)] hover:underline px-0 h-auto",
  icon:
    "bg-[color:var(--color-surface-elev)] text-[color:var(--color-charcoal)] hover:bg-[rgba(255,255,255,0.1)] hover:text-[color:var(--color-ink)] rounded-full h-10 w-10 p-0",
  glow:
    "text-white hover:opacity-90 active:opacity-80",
};

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { className, variant = "primary", size = "md", style, ...rest },
  ref,
) {
  const glowStyle = variant === "glow"
    ? { background: "var(--gradient-brand-coral)", boxShadow: "0 0 20px rgba(255,106,77,0.35)", ...style }
    : variant === "secondary"
    ? { borderColor: "var(--color-hairline-strong)", ...style }
    : style;

  return (
    <button
      ref={ref}
      style={glowStyle}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-full font-medium transition-all duration-150",
        "disabled:cursor-not-allowed disabled:opacity-40",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgba(162,75,255,0.5)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-canvas)]",
        variant !== "icon" && SIZE[size],
        VARIANT[variant],
        className,
      )}
      {...rest}
    />
  );
});
