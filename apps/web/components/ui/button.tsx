import { cn } from "@/lib/cn";
import Link from "next/link";
import type { ComponentProps } from "react";

export type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "danger" | "accent" | "inverse";
export type ButtonSize = "sm" | "md" | "lg" | "icon";

const base =
  "relative inline-flex select-none items-center justify-center gap-2 whitespace-nowrap rounded-full font-semibold " +
  "transition-[background-color,border-color,color,box-shadow,transform,opacity] duration-200 ease-snappy " +
  "active:scale-[0.97] motion-reduce:active:scale-100 " +
  "disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50 " +
  "[&_svg]:shrink-0";

const variants: Record<ButtonVariant, string> = {
  /** The one main action in a view. Violet with a soft glow. */
  primary:
    "bg-brand-600 text-white shadow-glow inset-shadow-highlight " +
    "hover:bg-brand-700 hover:shadow-glow-lg hover:-translate-y-px motion-reduce:hover:translate-y-0",
  /** Supporting actions: tonal violet. */
  secondary: "bg-brand-50 text-brand-800 ring-1 ring-inset ring-brand-100 hover:bg-brand-100 hover:ring-brand-200",
  /** Neutral bordered button on white/canvas. */
  outline:
    "bg-raised text-ink shadow-xs ring-1 ring-inset ring-line-strong hover:bg-neutral-50 hover:ring-neutral-400",
  /** Low-emphasis, inline with content. */
  ghost: "text-ink hover:bg-neutral-100 active:bg-neutral-200",
  /** Destructive confirm. */
  danger: "bg-danger-600 text-white shadow-xs inset-shadow-highlight hover:bg-danger-700",
  /** Marigold highlight (e.g. header search submit). Ink text 9.9:1. */
  accent: "bg-accent-400 text-ink shadow-xs inset-shadow-highlight hover:bg-accent-300",
  /** White button for dark/brand surfaces; pair the surface with `focus-inverse`. */
  inverse: "bg-white text-brand-900 shadow-sm hover:bg-brand-50",
};

// sm is visually 36px but gets an invisible 44px hit area via ::before.
const sizes: Record<ButtonSize, string> = {
  sm: "h-9 px-3.5 text-sm before:absolute before:inset-x-0 before:-inset-y-1 before:content-['']",
  md: "min-h-11 px-5 text-[0.9375rem]",
  lg: "min-h-13 px-7 text-base",
  icon: "size-11 p-0",
};

export function buttonClasses(variant: ButtonVariant = "primary", size: ButtonSize = "md", className?: string) {
  return cn(base, variants[variant], sizes[size], className);
}

function Spinner() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="size-4 animate-spin" fill="none">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.25" strokeWidth="3" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  className,
  type = "button",
  disabled,
  children,
  ...props
}: ComponentProps<"button"> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Shows a spinner, disables the button, and sets aria-busy. Keep the label text meaningful. */
  loading?: boolean;
}) {
  return (
    <button
      type={type}
      className={buttonClasses(variant, size, className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading ? <Spinner /> : null}
      {children}
    </button>
  );
}

export function ButtonLink({
  variant = "primary",
  size = "md",
  className,
  ...props
}: ComponentProps<typeof Link> & { variant?: ButtonVariant; size?: ButtonSize }) {
  return <Link className={buttonClasses(variant, size, className)} {...props} />;
}
