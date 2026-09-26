"use client";

import { ChevronDownIcon, SlidersIcon } from "@/components/icons";
import { cn } from "@/lib/cn";
import { useState } from "react";

/** On small screens the filters collapse behind a button; on large screens they're always shown. */
export function FilterPanel({ activeCount, children }: { activeCount: number; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <button
        type="button"
        aria-expanded={open}
        aria-controls="filter-panel"
        onClick={() => setOpen((o) => !o)}
        className="flex min-h-12 w-full items-center gap-3 rounded-2xl border border-line bg-raised px-4 text-sm font-semibold text-ink shadow-xs transition-colors duration-150 hover:border-line-strong lg:hidden"
      >
        <SlidersIcon className="text-brand-600" />
        <span>Filters</span>
        {activeCount > 0 ? (
          <span className="rounded-full bg-brand-600 px-2 py-0.5 text-xs font-semibold tabular-nums text-white">
            {activeCount}
            <span className="sr-only"> active</span>
          </span>
        ) : null}
        <ChevronDownIcon
          className={cn("ml-auto size-4 text-muted transition-transform duration-200 ease-snappy", open && "rotate-180")}
        />
      </button>
      <div id="filter-panel" className={cn(open ? "mt-3 block animate-slide-down" : "hidden", "lg:mt-0 lg:block lg:animate-none")}>
        {children}
      </div>
    </div>
  );
}
