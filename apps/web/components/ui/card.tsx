import { forwardRef } from "react";

import { cn } from "@/lib/utils";

/**
 * Quiet card family — `rounded-[16px]`, hairline border, canvas/surface bg.
 * Use for: dashboards, lists, settings panels.
 */
export const Card = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & {
  feature?: boolean;
}>(function Card({ className, feature, ...rest }, ref) {
  return (
    <div
      ref={ref}
      className={cn(
        "rounded-[16px] border border-[color:var(--color-hairline)] p-6",
        feature
          ? "bg-[color:var(--color-surface)]"
          : "bg-[color:var(--color-canvas)]",
        className,
      )}
      {...rest}
    />
  );
});

export function CardHeader({
  className,
  ...rest
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("mb-4 flex items-start justify-between gap-3", className)} {...rest} />;
}

export function CardTitle({
  className,
  ...rest
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("text-heading-md text-[color:var(--color-charcoal)]", className)}
      {...rest}
    />
  );
}

export function CardSubtitle({
  className,
  ...rest
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("text-body-sm text-[color:var(--color-steel)]", className)}
      {...rest}
    />
  );
}

/**
 * Vibrant product card — `rounded-[32px]`, brand gradient bg, ink text.
 * Use SPARINGLY — 4–6 per page max. (DESIGN.md §1 + §8.2)
 */
export type Gradient = "coral" | "magenta" | "blue" | "purple" | "amber";

const GRADIENT_CLASS: Record<Gradient, string> = {
  coral: "bg-brand-coral",
  magenta: "bg-brand-magenta",
  blue: "bg-brand-blue",
  purple: "bg-brand-purple",
  amber: "bg-brand-amber",
};

export function ProductCard({
  gradient = "coral",
  className,
  children,
  ...rest
}: {
  gradient?: Gradient;
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-[32px] p-8 text-[color:var(--color-ink)] shadow-[0_4px_12px_rgba(10,10,10,0.06)] transition-transform hover:-translate-y-0.5",
        GRADIENT_CLASS[gradient],
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
