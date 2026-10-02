"use client";

import { OpenStephButton } from "@/components/assistant/open-steph";
import { ArrowRightIcon, MicIcon, SearchIcon } from "@/components/icons";
import { ButtonLink } from "@/components/ui/button";
import { inputClasses } from "@/components/ui/field";
import { cn } from "@/lib/cn";
import { type HelpEntry, searchHelp } from "@/lib/help-search";
import { type ReactNode, useId, useMemo, useState } from "react";

const MAX_RESULTS = 8;

/**
 * Filters the help center's own topics and answers as you type (nothing leaves the browser).
 * With no match, it points to Steph and Xena instead of a dead end; `children` (the page's usual
 * assistant buttons) step aside then, so the same two buttons don't show twice.
 */
export function HelpSearch({
  entries,
  className,
  children,
}: {
  entries: HelpEntry[];
  className?: string;
  children?: ReactNode;
}) {
  const [query, setQuery] = useState("");
  const inputId = useId();
  const results = useMemo(() => searchHelp(entries, query), [entries, query]);
  const active = query.trim().length > 0;
  const shown = results.slice(0, MAX_RESULTS);

  // A question lives in a closed <details>; open it on the way there.
  const openTarget = (entry: HelpEntry) => {
    const el = document.getElementById(entry.id);
    if (el instanceof HTMLDetailsElement) el.open = true;
  };

  return (
    <div className={className}>
      <form role="search" aria-label="Help center" onSubmit={(e) => e.preventDefault()} className="relative max-w-xl">
        <label htmlFor={inputId} className="sr-only">
          Search help
        </label>
        <SearchIcon className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-muted" />
        <input
          id={inputId}
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoComplete="off"
          placeholder="Search help, like “refund” or “gluten free”"
          className={cn(inputClasses, "min-h-13 rounded-full pl-12 text-base")}
        />
      </form>

      <p role="status" aria-live="polite" className="sr-only">
        {active ? `${results.length} ${results.length === 1 ? "answer" : "answers"} found` : ""}
      </p>

      {!active ? null : shown.length > 0 ? (
        <div className="mt-4 max-w-3xl">
          <ul className="divide-y divide-line overflow-hidden rounded-2xl border border-line bg-raised shadow-sm">
            {shown.map((entry) => (
              <li key={entry.id}>
                <a
                  href={entry.href}
                  onClick={() => openTarget(entry)}
                  className="group flex items-start gap-3 px-4 py-3.5 transition-colors hover:bg-sunken/60 sm:px-5"
                >
                  <span className="min-w-0 flex-1">
                    <span className="block text-xs font-semibold uppercase tracking-eyebrow text-brand-700">
                      {entry.section}
                    </span>
                    <span className="mt-0.5 block font-semibold text-ink group-hover:text-brand-800">{entry.title}</span>
                    <span className="mt-0.5 line-clamp-2 block text-sm text-muted">{entry.text}</span>
                  </span>
                  <ArrowRightIcon className="mt-5 size-4 shrink-0 text-muted transition-transform duration-200 ease-snappy group-hover:translate-x-0.5" />
                </a>
              </li>
            ))}
          </ul>
          {results.length > shown.length ? (
            <p className="mt-2 px-1 text-sm text-muted">
              Showing the best {shown.length} of {results.length}. Add a word to narrow it down.
            </p>
          ) : null}
        </div>
      ) : (
        <div className="mt-4 max-w-3xl rounded-2xl border border-dashed border-line-strong bg-raised/80 p-5">
          <p className="font-semibold text-ink">Nothing here matches “{query.trim()}”.</p>
          <p className="mt-1 text-sm text-muted">
            Try another word, or ask an assistant: Steph for products and policies, Xena for orders, delivery, and
            returns.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <OpenStephButton prompt={query.trim()} size="sm">
              Ask Steph
            </OpenStephButton>
            <ButtonLink href="/support" variant="outline" size="sm">
              <MicIcon className="size-4" />
              Talk to Xena
            </ButtonLink>
          </div>
        </div>
      )}
      {active && shown.length === 0 ? null : children}
    </div>
  );
}
