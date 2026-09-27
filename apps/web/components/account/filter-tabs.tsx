"use client";

import { cn } from "@/lib/cn";

export type FilterOption<T extends string> = { value: T; label: string; count?: number };

/**
 * A row of filter chips (toggle buttons with `aria-pressed`) for account lists: orders, activity,
 * store services. Each button says its count, so the result size is known before choosing.
 * Scrolls sideways on narrow screens instead of wrapping into a tall block.
 */
export function FilterTabs<T extends string>({
  label,
  options,
  value,
  onChange,
  className,
}: {
  /** Accessible name for the group, e.g. "Filter orders". */
  label: string;
  options: FilterOption<T>[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
}) {
  return (
    <div
      role="group"
      aria-label={label}
      className={cn("-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 scrollbar-none sm:mx-0 sm:flex-wrap sm:px-0", className)}
    >
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(o.value)}
            className={cn(
              "inline-flex min-h-11 shrink-0 items-center gap-2 rounded-full px-4 text-sm font-semibold transition-colors duration-150 ease-snappy",
              active
                ? "bg-ink text-white shadow-xs"
                : "bg-raised text-ink-soft ring-1 ring-inset ring-line-strong hover:bg-neutral-50 hover:text-ink",
            )}
          >
            {o.label}
            {o.count !== undefined ? (
              <span
                className={cn(
                  "min-w-5 rounded-full px-1.5 text-center text-xs tabular-nums",
                  active ? "bg-white/20 text-white" : "bg-neutral-100 text-neutral-700",
                )}
              >
                {o.count}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
