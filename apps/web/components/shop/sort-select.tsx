"use client";

import { selectClasses } from "@/components/ui/field";
import { cn } from "@/lib/cn";

/**
 * Sort control for the results toolbar. It belongs to the filter form (via `form`), so "Apply
 * filters" also sends it; with JS it re-sorts straight away. The hint tells screen-reader users
 * that choosing an option reloads the results.
 */
export function SortSelect({
  formId,
  defaultValue,
  options,
}: {
  formId: string;
  defaultValue: string;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="flex items-center gap-2.5">
      <label htmlFor="sort" className="whitespace-nowrap text-sm font-medium text-muted">
        Sort by
      </label>
      <select
        id="sort"
        name="sort"
        form={formId}
        defaultValue={defaultValue}
        aria-describedby="sort-hint"
        onChange={(e) => e.currentTarget.form?.requestSubmit()}
        className={cn(selectClasses, "min-h-11 w-auto rounded-full py-0 pl-4 text-sm font-semibold")}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <span id="sort-hint" className="sr-only">
        Choosing an option reloads the results.
      </span>
    </div>
  );
}
