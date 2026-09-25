import { cn } from "@/lib/cn";
import Link from "next/link";
import type { ComponentProps } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

const base =
  "inline-flex items-center justify-center gap-2 rounded-full font-semibold transition-colors " +
  "disabled:cursor-not-allowed disabled:opacity-60 min-h-11 min-w-11";
const variants: Record<Variant, string> = {
  primary: "bg-brand-700 text-white hover:bg-brand-800",
  secondary: "border border-brand-700 bg-white text-brand-700 hover:bg-brand-50",
  ghost: "text-ink hover:bg-stone-100",
  danger: "border border-red-700 bg-white text-red-700 hover:bg-red-50",
};
const sizes: Record<Size, string> = {
  sm: "px-3 text-sm min-h-9",
  md: "px-5 text-sm",
  lg: "px-6 text-base min-h-12",
};

export function buttonClasses(variant: Variant = "primary", size: Size = "md", className?: string) {
  return cn(base, variants[variant], sizes[size], className);
}

export function Button({
  variant = "primary",
  size = "md",
  className,
  type = "button",
  ...props
}: ComponentProps<"button"> & { variant?: Variant; size?: Size }) {
  return <button type={type} className={buttonClasses(variant, size, className)} {...props} />;
}

export function ButtonLink({
  variant = "primary",
  size = "md",
  className,
  ...props
}: ComponentProps<typeof Link> & { variant?: Variant; size?: Size }) {
  return <Link className={buttonClasses(variant, size, className)} {...props} />;
}
