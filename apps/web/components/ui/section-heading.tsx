import { ArrowRightIcon } from "@/components/icons";
import { cn } from "@/lib/cn";
import Link from "next/link";
import type { ReactNode } from "react";

/**
 * Section header: optional eyebrow, display title, optional description, optional "See all" link.
 * Give `id` and point the section at it: `<section aria-labelledby="featured">`.
 */
export function SectionHeading({
  id,
  title,
  eyebrow,
  description,
  action,
  as: Heading = "h2",
  size = "md",
  className,
}: {
  id?: string;
  title: ReactNode;
  eyebrow?: ReactNode;
  description?: ReactNode;
  /** Trailing link. `srLabel` completes vague labels, e.g. label "See all", srLabel "electronics". */
  action?: { href: string; label: string; srLabel?: string };
  as?: "h1" | "h2" | "h3";
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const titleSize = {
    sm: "text-xl sm:text-2xl",
    md: "text-2xl sm:text-3xl",
    lg: "text-3xl sm:text-4xl",
  }[size];
  return (
    <div className={cn("flex flex-wrap items-end justify-between gap-x-6 gap-y-3", className)}>
      <div className="min-w-0 max-w-2xl">
        {eyebrow ? (
          <p className="mb-2 text-xs font-semibold uppercase tracking-eyebrow text-brand-700">{eyebrow}</p>
        ) : null}
        <Heading id={id} className={cn("font-display font-semibold text-ink", titleSize)}>
          {title}
        </Heading>
        {description ? <p className="mt-2 text-base text-muted">{description}</p> : null}
      </div>
      {action ? (
        <Link
          href={action.href}
          className="group -mr-2 inline-flex min-h-11 items-center gap-1.5 rounded-full px-2 text-sm font-semibold text-brand-700 transition-colors hover:text-brand-900"
        >
          {action.label}
          {action.srLabel ? <span className="sr-only"> {action.srLabel}</span> : null}
          <ArrowRightIcon className="size-4 transition-transform duration-200 ease-snappy group-hover:translate-x-0.5" />
        </Link>
      ) : null}
    </div>
  );
}
