import { cn } from "@/lib/cn";
import type { ReactNode } from "react";

export type BadgeTone = "neutral" | "brand" | "success" | "warning" | "danger" | "sale" | "accent";

const tones: Record<BadgeTone, string> = {
  neutral: "bg-neutral-100 text-neutral-700 ring-neutral-200",
  brand: "bg-brand-50 text-brand-700 ring-brand-100",
  success: "bg-success-50 text-success-800 ring-success-200",
  warning: "bg-warning-50 text-warning-800 ring-warning-200",
  danger: "bg-danger-50 text-danger-800 ring-danger-200",
  sale: "bg-danger-600 text-white ring-danger-600",
  accent: "bg-accent-100 text-accent-800 ring-accent-200",
};

const dotTones: Record<BadgeTone, string> = {
  neutral: "bg-neutral-500",
  brand: "bg-brand-600",
  success: "bg-success-600",
  warning: "bg-warning-600",
  danger: "bg-danger-600",
  sale: "bg-white",
  accent: "bg-accent-600",
};

export function badgeClasses(tone: BadgeTone = "neutral", size: "sm" | "md" = "sm", className?: string) {
  return cn(
    "inline-flex items-center gap-1 whitespace-nowrap rounded-full font-semibold ring-1 ring-inset [&_svg]:size-3.5",
    size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm",
    tones[tone],
    className,
  );
}

/**
 * Small status label. Always carries words (color is never the only signal).
 * `dot` adds a leading status dot.
 */
export function Badge({
  tone = "neutral",
  size = "sm",
  dot = false,
  className,
  children,
}: {
  tone?: BadgeTone;
  size?: "sm" | "md";
  dot?: boolean;
  className?: string;
  children: ReactNode;
}) {
  return (
    <span className={badgeClasses(tone, size, className)}>
      {dot ? <span aria-hidden="true" className={cn("size-1.5 rounded-full", dotTones[tone])} /> : null}
      {children}
    </span>
  );
}
