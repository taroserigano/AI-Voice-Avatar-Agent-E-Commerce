"use client";

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
        className="flex min-h-11 w-full items-center justify-between rounded-full border border-brand-700 px-5 font-semibold text-brand-700 lg:hidden"
      >
        <span>
          Filters and sort{activeCount > 0 ? ` (${activeCount} active)` : ""}
        </span>
        <span aria-hidden="true">{open ? "▲" : "▼"}</span>
      </button>
      <div id="filter-panel" className={`${open ? "mt-4 block" : "hidden"} lg:mt-0 lg:block`}>
        {children}
      </div>
    </div>
  );
}
