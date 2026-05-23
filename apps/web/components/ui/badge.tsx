import { cn } from "@/lib/utils";

type Tone = "neutral" | "success" | "warning" | "error" | "info";

const TONE: Record<Tone, string> = {
  neutral:
    "bg-[color:var(--color-surface)] text-[color:var(--color-charcoal)]",
  success:
    "bg-[color:var(--color-success-bg)] text-[color:var(--color-success-text)]",
  warning:
    "bg-[color:var(--color-warning-bg)] text-[color:var(--color-warning-text)]",
  error: "bg-[color:var(--color-error-bg)] text-[color:var(--color-error-text)]",
  info: "bg-[color:var(--color-info-bg)] text-[color:var(--color-info-text)]",
};

export function Badge({
  tone = "neutral",
  className,
  children,
  ...rest
}: {
  tone?: Tone;
} & React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-[4px] px-2 py-0.5 text-micro font-medium",
        TONE[tone],
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  );
}

export function statusTone(status: string): Tone {
  switch (status) {
    case "completed":
    case "ok":
      return "success";
    case "running":
    case "queued":
      return "info";
    case "failed":
    case "error":
      return "error";
    case "cancelled":
      return "warning";
    default:
      return "neutral";
  }
}
