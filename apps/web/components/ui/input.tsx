import { forwardRef } from "react";

import { cn } from "@/lib/utils";

type Props = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = forwardRef<HTMLInputElement, Props>(function Input(
  { className, type = "text", ...rest },
  ref,
) {
  return (
    <input
      ref={ref}
      type={type}
      className={cn(
        "h-10 w-full rounded-[8px] border border-[color:var(--color-hairline)]",
        "bg-[color:var(--color-canvas)] px-3 text-body-md text-[color:var(--color-ink)]",
        "placeholder:text-[color:var(--color-stone)]",
        "focus-visible:outline-none focus-visible:border-[color:var(--color-ink)] focus-visible:ring-2 focus-visible:ring-[color:var(--color-ink)]",
        "disabled:bg-[color:var(--color-surface)] disabled:text-[color:var(--color-muted)]",
        className,
      )}
      {...rest}
    />
  );
});

export const SearchPill = forwardRef<HTMLInputElement, Props>(function SearchPill(
  { className, ...rest },
  ref,
) {
  return (
    <input
      ref={ref}
      type="search"
      className={cn(
        "h-11 w-full rounded-full bg-[color:var(--color-surface)] px-5 text-body-md text-[color:var(--color-ink)]",
        "placeholder:text-[color:var(--color-stone)] border border-transparent",
        "focus-visible:outline-none focus-visible:border-[color:var(--color-ink)] focus-visible:ring-2 focus-visible:ring-[color:var(--color-ink)]",
        className,
      )}
      {...rest}
    />
  );
});
