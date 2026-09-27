"use client";

import { CloseIcon, SearchIcon, SlidersIcon } from "@/components/icons";
import { controlClasses, countPill, legendClasses, optionRow } from "@/components/product/filter-styles";
import { buttonClasses } from "@/components/ui/button";
import { inputClasses } from "@/components/ui/field";
import { cn } from "@/lib/cn";
import { useRouter } from "next/navigation";
import {
  createContext,
  useContext,
  useEffect,
  useId,
  useRef,
  useState,
  useTransition,
  type FormEvent,
  type ReactNode,
  type RefObject,
} from "react";

const LG = "(min-width: 64rem)";

/**
 * The filter form. Checkboxes and radios apply as soon as they change (a client-side navigation
 * that keeps the scroll position); price applies on Enter or its Apply button. Without
 * JavaScript it is still a plain GET form. Empty fields are left out of the URL.
 *
 * `query` is the current search string: when the URL changes some other way (removing a chip,
 * Back), the controls are set to match it instead of being remounted, so focus stays put.
 */
export function FilterForm({
  id,
  action,
  query,
  defaults = {},
  className,
  children,
}: {
  id: string;
  action: string;
  query: string;
  /** Values left out of the URL because they're what the page does anyway (e.g. sort=relevance). */
  defaults?: Record<string, string>;
  className?: string;
  children: ReactNode;
}) {
  const router = useRouter();
  const ref = useRef<HTMLFormElement>(null);
  const [pending, startTransition] = useTransition();

  useEffect(() => {
    const form = ref.current;
    if (!form) return;
    const sp = new URLSearchParams(query);
    for (const el of Array.from(form.elements)) {
      if (el instanceof HTMLInputElement && el.name) {
        if (el.type === "checkbox") el.checked = sp.getAll(el.name).includes(el.value);
        else if (el.type === "radio") el.checked = (sp.get(el.name) ?? "") === el.value;
        else if (el.type !== "hidden" && el !== document.activeElement) el.value = sp.get(el.name) ?? "";
      } else if (el instanceof HTMLSelectElement && el.name) {
        const value = sp.get(el.name);
        const known = [...el.options].some((o) => o.value === value);
        el.value = value && known ? value : (el.options[0]?.value ?? "");
      }
    }
  }, [query]);

  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const sp = new URLSearchParams();
    for (const [key, value] of new FormData(e.currentTarget)) {
      if (typeof value !== "string" || value.trim() === "" || defaults[key] === value) continue;
      sp.append(key, value.trim());
    }
    const qs = sp.toString();
    startTransition(() => router.push(qs ? `${action}?${qs}` : action, { scroll: false }));
  }

  return (
    <form
      ref={ref}
      id={id}
      method="get"
      action={action}
      onSubmit={submit}
      onChange={(e) => {
        const t = e.target;
        if (t instanceof HTMLInputElement && t.name && (t.type === "checkbox" || t.type === "radio")) {
          t.form?.requestSubmit();
        }
      }}
      data-pending={pending || undefined}
      aria-busy={pending || undefined}
      className={className}
    >
      {children}
      <p role="status" className="sr-only">
        {pending ? "Updating results…" : ""}
      </p>
    </form>
  );
}

type Facet = { value: string; label: string; count: number };

/**
 * A checkbox group. Long lists show the first `limit` values (plus anything selected) with a
 * "Show all" toggle, and lists longer than 12 get a box to find a value. Hidden checkboxes stay
 * in the form, so a selected value is still submitted.
 */
export function FacetOptions({
  legend,
  name,
  facets,
  selected,
  noun,
  limit = 8,
}: {
  legend: string;
  name: string;
  facets: Facet[];
  selected: string[];
  /** Singular word for one value ("brand"), used in the find box. */
  noun: string;
  limit?: number;
}) {
  const uid = useId();
  const [expanded, setExpanded] = useState(false);
  const [needle, setNeedle] = useState("");
  if (facets.length === 0) return null;
  const find = needle.trim().toLowerCase();
  const searchable = facets.length > 12;
  // Hiding just one or two values behind a toggle isn't worth the extra click.
  const long = facets.length > limit + 2;
  const shows = (f: Facet, i: number) =>
    find ? f.label.toLowerCase().includes(find) : expanded || !long || i < limit || selected.includes(f.value);
  const matches = find ? facets.filter((f, i) => shows(f, i)).length : null;
  const listId = `${uid}-list`;

  return (
    <fieldset className="px-1 py-4">
      <legend className={cn(legendClasses, "px-2")}>{legend}</legend>
      {searchable ? (
        <div className="relative clear-both px-1 pt-3">
          <label htmlFor={`${uid}-find`} className="sr-only">
            Find a {noun}
          </label>
          <SearchIcon className="pointer-events-none absolute left-4 top-[calc(50%+0.375rem)] size-4 -translate-y-1/2 text-muted" />
          <input
            id={`${uid}-find`}
            type="search"
            // No name: it only narrows the list and is never submitted.
            value={needle}
            onChange={(e) => setNeedle(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") e.preventDefault();
            }}
            placeholder={`Find a ${noun}`}
            aria-controls={listId}
            autoComplete="off"
            className={cn(inputClasses, "min-h-10 pl-9 pr-3 text-sm")}
          />
        </div>
      ) : null}
      <div id={listId} className="clear-both space-y-0.5 pt-2">
        {facets.map((f, i) => (
          <label key={f.value} className={cn(optionRow, !shows(f, i) && "hidden")}>
            <input
              type="checkbox"
              name={name}
              value={f.value}
              defaultChecked={selected.includes(f.value)}
              className={cn(controlClasses, "rounded")}
            />
            <span className="min-w-0 truncate">{f.label}</span>
            <span className={countPill}>
              <span className="sr-only">(</span>
              {f.count}
              <span className="sr-only">)</span>
            </span>
          </label>
        ))}
        {matches === 0 ? <p className="px-2 py-2 text-sm text-muted">No {noun} matches “{needle.trim()}”.</p> : null}
      </div>
      <p className="sr-only" aria-live="polite">
        {matches !== null ? `${matches} ${matches === 1 ? "match" : "matches"}` : ""}
      </p>
      {long && !find ? (
        <button
          type="button"
          aria-expanded={expanded}
          aria-controls={listId}
          onClick={() => setExpanded((x) => !x)}
          className="mt-1 inline-flex min-h-10 items-center rounded-lg px-2 text-sm font-semibold text-brand-700 hover:text-brand-900 hover:underline hover:underline-offset-4"
        >
          {expanded ? "Show fewer" : `Show all ${facets.length}`}
          <span className="sr-only"> {legend} options</span>
        </button>
      ) : null}
    </fieldset>
  );
}

type Sheet = {
  open: boolean;
  setOpen: (open: boolean) => void;
  triggerRef: RefObject<HTMLButtonElement | null>;
};

const SheetContext = createContext<Sheet | null>(null);

function useSheet(): Sheet {
  const sheet = useContext(SheetContext);
  if (!sheet) throw new Error("FilterTrigger and FilterPanel must be inside <FilterSheet>");
  return sheet;
}

/**
 * Shares the phone filter sheet's open state between its trigger (in the results toolbar, next
 * to the count and sort) and the panel itself (in the sidebar slot).
 */
export function FilterSheet({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  return <SheetContext value={{ open, setOpen, triggerRef }}>{children}</SheetContext>;
}

/** The "Filters" button that opens the sheet below the lg breakpoint. */
export function FilterTrigger({ activeCount }: { activeCount: number }) {
  const { open, setOpen, triggerRef } = useSheet();
  return (
    <button
      ref={triggerRef}
      type="button"
      aria-haspopup="dialog"
      aria-expanded={open}
      aria-controls="filter-panel"
      onClick={() => setOpen(true)}
      className="inline-flex min-h-11 shrink-0 items-center gap-2 rounded-full border border-line bg-raised pl-3.5 pr-4 text-sm font-semibold text-ink shadow-xs transition-colors duration-150 hover:border-line-strong lg:hidden"
    >
      <SlidersIcon className="size-4.5 text-brand-600" />
      <span>Filters</span>
      {activeCount > 0 ? (
        <span className="rounded-full bg-brand-600 px-2 py-0.5 text-xs font-semibold tabular-nums text-white">
          {activeCount}
          <span className="sr-only"> active</span>
        </span>
      ) : null}
    </button>
  );
}

/**
 * On large screens the filters sit in a sidebar. On phones and tablets they open as a full-height
 * sheet (a modal dialog) from the "Filters" button, so the products aren't pushed down the page.
 * Filters still apply instantly inside the sheet; "Show N results" just closes it.
 */
export function FilterPanel({
  total,
  totalLabel,
  children,
}: {
  total: number;
  /** How the count reads: "324", or "400+" when search stopped at its candidate limit. */
  totalLabel?: string;
  children: ReactNode;
}) {
  const { open, setOpen, triggerRef } = useSheet();
  const closeRef = useRef<HTMLButtonElement>(null);
  const sheetRef = useRef<HTMLDivElement>(null);
  const wasOpen = useRef(false);

  // Opening: lock page scroll and move focus in. Closing: give focus back to the trigger.
  useEffect(() => {
    if (open) {
      wasOpen.current = true;
      const previous = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      closeRef.current?.focus();
      return () => {
        document.body.style.overflow = previous;
      };
    }
    if (wasOpen.current) {
      wasOpen.current = false;
      triggerRef.current?.focus();
    }
  }, [open, triggerRef]);

  // The sheet only exists below the lg breakpoint; widening the window closes it.
  useEffect(() => {
    const mq = window.matchMedia(LG);
    const onChange = () => {
      if (mq.matches) setOpen(false);
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [setOpen]);

  function onKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (!open) return;
    if (e.key === "Escape") {
      e.stopPropagation();
      setOpen(false);
      return;
    }
    if (e.key !== "Tab" || !sheetRef.current) return;
    // Keep Tab inside the sheet while it's modal.
    const focusable = [
      ...sheetRef.current.querySelectorAll<HTMLElement>(
        "a[href], button:not([disabled]), input:not([disabled]):not([type=hidden]), select:not([disabled])",
      ),
    ].filter((el) => el.offsetParent !== null);
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (!first || !last) return;
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  return (
    <div
      ref={sheetRef}
      id="filter-panel"
      role={open ? "dialog" : undefined}
      aria-modal={open || undefined}
      aria-labelledby={open ? "filter-sheet-title" : undefined}
      onKeyDown={onKeyDown}
      className={cn(
        open ? "fixed inset-0 z-60 flex animate-fade-in flex-col bg-canvas motion-reduce:animate-none" : "hidden",
        "lg:static lg:z-auto lg:block lg:animate-none lg:bg-transparent",
      )}
    >
      <div className="flex items-center gap-3 border-b border-line bg-raised px-4 py-2 lg:hidden">
        <SlidersIcon className="size-5 text-brand-600" />
        <p id="filter-sheet-title" className="font-display text-lg font-semibold text-ink">
          Filters
        </p>
        <button
          ref={closeRef}
          type="button"
          onClick={() => setOpen(false)}
          className={buttonClasses("ghost", "icon", "-mr-2 ml-auto")}
        >
          <CloseIcon className="size-5" />
          <span className="sr-only">Close filters</span>
        </button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-3 lg:overflow-visible lg:p-0">{children}</div>
      <div className="border-t border-line bg-raised px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 lg:hidden">
        <button type="button" onClick={() => setOpen(false)} className={buttonClasses("primary", "lg", "w-full")}>
          Show {totalLabel ?? total} {total === 1 ? "result" : "results"}
        </button>
      </div>
    </div>
  );
}
