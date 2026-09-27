"use client";

import { cn } from "@/lib/cn";
import Link from "next/link";
import { useId, useState } from "react";

export type TypeChip = { value: string; label: string; count?: number; href: string; current: boolean };

/**
 * "Shop by type" links for a department banner. On wider screens it shows the first `limit`
 * (plus the current one), with a toggle for the rest so a 30-type department doesn't fill the
 * banner. On phones every chip sits in one row that scrolls sideways, so the banner stays short
 * and the products start near the top of the page.
 */
export function TypeChips({ chips, limit = 10, className }: { chips: TypeChip[]; limit?: number; className?: string }) {
  const uid = useId();
  const [expanded, setExpanded] = useState(false);
  if (chips.length === 0) return null;
  const long = chips.length > limit;
  const listId = `${uid}-types`;
  return (
    <div className={className}>
      <h2
        id={`${uid}-heading`}
        className="text-xs font-semibold uppercase tracking-eyebrow text-ink-soft max-sm:sr-only"
      >
        Shop by type
      </h2>
      <ul
        id={listId}
        aria-labelledby={`${uid}-heading`}
        className="-mx-4 flex snap-x gap-2 overflow-x-auto px-4 pb-1 [scrollbar-width:none] sm:mx-0 sm:mt-2.5 sm:snap-none sm:flex-wrap sm:overflow-visible sm:px-0 sm:pb-0"
      >
        {chips.map((chip, i) => (
          <li
            key={chip.value}
            // Collapsed on wider screens: `limit` chips (plus the current one). Phones scroll instead.
            className={cn("shrink-0 snap-start", !expanded && !chip.current && i >= limit && "sm:hidden")}
          >
            <Link
              href={chip.href}
              scroll={false}
              aria-current={chip.current ? "true" : undefined}
              className="inline-flex min-h-9 items-center gap-1.5 whitespace-nowrap rounded-full bg-raised/90 px-3.5 text-sm font-medium text-ink shadow-xs ring-1 ring-inset ring-black/5 transition-colors duration-150 hover:bg-raised hover:text-brand-800 hover:ring-brand-200 aria-current:bg-ink aria-current:text-white aria-current:ring-ink"
            >
              {chip.label}
              {chip.count !== undefined ? (
                <span className="text-xs tabular-nums text-muted [a[aria-current=true]_&]:text-white/80">
                  <span className="sr-only">, </span>
                  {chip.count}
                  <span className="sr-only"> products</span>
                </span>
              ) : null}
            </Link>
          </li>
        ))}
        {long ? (
          <li className="max-sm:hidden">
            <button
              type="button"
              aria-expanded={expanded}
              aria-controls={listId}
              onClick={() => setExpanded((x) => !x)}
              className="inline-flex min-h-9 items-center rounded-full px-3 text-sm font-semibold text-brand-800 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700"
            >
              {expanded ? "Fewer types" : `All ${chips.length} types`}
            </button>
          </li>
        ) : null}
      </ul>
    </div>
  );
}
