import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatRelative(iso?: string | null): string {
  if (!iso) return "—";
  const t = new Date(iso).getTime();
  const now = Date.now();
  const s = Math.round((now - t) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.round(s / 60)}m ago`;
  if (s < 86400) return `${Math.round(s / 3600)}h ago`;
  return `${Math.round(s / 86400)}d ago`;
}

export function shortId(id?: string | null, n = 8): string {
  if (!id) return "—";
  return id.slice(0, n);
}
