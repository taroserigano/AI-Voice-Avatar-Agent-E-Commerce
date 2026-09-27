"use client";

import { ArrowRightIcon, DepartmentIcon, SearchIcon, TagIcon } from "@/components/icons";
import { browserApi } from "@/lib/api-browser";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import type { SearchSuggestions } from "@ai-commerce/contracts";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useId, useMemo, useRef, useState, type KeyboardEvent, type ReactNode } from "react";

const DEBOUNCE_MS = 150;
const MIN_CHARS = 2;

type Option = { key: string; href: string; label: string; content: ReactNode; index: number };
type Group = { key: string; label: string; options: Option[] };

/** Bold what the suggestion adds to what was typed ("lact" + "ose-free milk"). */
function Completion({ text, typed }: { text: string; typed: string }) {
  const t = typed.trim().toLowerCase();
  if (t && text.toLowerCase().startsWith(t)) {
    return (
      <span className="truncate">
        {text.slice(0, t.length)}
        <span className="font-semibold">{text.slice(t.length)}</span>
      </span>
    );
  }
  return <span className="truncate font-semibold">{text}</span>;
}

function toGroups(data: SearchSuggestions, typed: string): Group[] {
  const groups: { key: string; label: string; options: Omit<Option, "index">[] }[] = [];
  if (data.completions.length > 0) {
    groups.push({
      key: "queries",
      label: "Suggestions",
      options: data.completions.slice(0, 4).map((text) => ({
        key: `q-${text}`,
        href: `/search?q=${encodeURIComponent(text)}`,
        label: text,
        content: (
          <>
            <SearchIcon className="size-4 shrink-0 text-muted" />
            <Completion text={text} typed={typed} />
          </>
        ),
      })),
    });
  }
  const places: Omit<Option, "index">[] = [
    ...data.departments.map((d) => ({
      key: `d-${d.slug}`,
      href: `/c/${d.slug}`,
      label: d.name,
      content: (
        <>
          <DepartmentIcon slug={d.slug} className="size-4 shrink-0 text-brand-600" />
          <span className="truncate font-medium">{d.name}</span>
          <span className="ml-auto shrink-0 text-xs text-muted">Department</span>
        </>
      ),
    })),
    ...data.product_types.map((t) => ({
      key: `t-${t.value}`,
      href: `/c/${t.category_slug}?product_type=${encodeURIComponent(t.value)}`,
      label: `${t.label} in ${t.category_name}`,
      content: (
        <>
          <TagIcon className="size-4 shrink-0 text-brand-600" />
          <span className="truncate">
            <span className="font-medium">{t.label}</span>
            <span className="text-muted"> in {t.category_name}</span>
          </span>
          <span className="ml-auto shrink-0 text-xs tabular-nums text-muted">
            {t.count}
            <span className="sr-only"> products</span>
          </span>
        </>
      ),
    })),
  ].slice(0, 3);
  if (places.length > 0) groups.push({ key: "places", label: "Shop by type", options: places });
  if (data.products.length > 0) {
    groups.push({
      key: "products",
      label: "Products",
      options: data.products.slice(0, 4).map((p) => ({
        key: `p-${p.id}`,
        href: `/products/${p.id}`,
        label: p.title,
        content: (
          <>
            {/* eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations */}
            <img
              src={p.image_path}
              alt=""
              width={40}
              height={40}
              className="size-10 shrink-0 rounded-lg bg-sunken object-cover ring-1 ring-inset ring-line/60"
            />
            <span className="min-w-0 flex-1">
              <span className="block truncate font-medium">{p.title}</span>
              <span className="block truncate text-xs text-muted">{p.brand}</span>
            </span>
            <span className="shrink-0 text-sm font-semibold tabular-nums">
              {formatMoney(p.price_minor, p.currency)}
              {p.in_stock ? null : <span className="block text-xs font-normal text-muted">Out of stock</span>}
            </span>
          </>
        ),
      })),
    });
  }
  // Number the options in display order, for aria-activedescendant and the arrow keys.
  let next = 0;
  return groups.map((g) => ({ ...g, options: g.options.map((o) => ({ ...o, index: next++ })) }));
}

/**
 * The header search box, with search-as-you-type suggestions (WAI-ARIA combobox with a grouped
 * listbox). Focus stays in the box: arrow keys move the highlighted option
 * (`aria-activedescendant`), Enter opens it, Escape closes the list. Enter with nothing
 * highlighted submits the plain search, and without JavaScript it's an ordinary GET form.
 * `query` pre-fills the box.
 */
export function HeaderSearchForm({ query, className }: { query?: string; className?: string }) {
  const router = useRouter();
  const uid = useId();
  const listId = `${uid}-listbox`;
  const [value, setValue] = useState(query ?? "");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [result, setResult] = useState<{ q: string; data: SearchSuggestions } | null>(null);
  const cache = useRef(new Map<string, SearchSuggestions>());
  const typedRef = useRef(false);

  const typed = value.trim();
  // Keep the last answer on screen while the next one loads, so the list doesn't flicker.
  const data = typed.length >= MIN_CHARS ? result?.data : undefined;
  const groups = useMemo(() => (data ? toGroups(data, typed) : []), [data, typed]);
  const options = groups.flatMap((g) => g.options);
  const expanded = open && options.length > 0;
  const activeIndex = expanded && active < options.length ? active : -1;
  const optionId = (i: number) => `${uid}-option-${i}`;

  // Debounced fetch; only once the shopper has typed (not for the pre-filled query).
  useEffect(() => {
    if (!typedRef.current || typed.length < MIN_CHARS) return;
    const key = typed.toLowerCase();
    const controller = new AbortController();
    const cached = cache.current.get(key);
    const timer = setTimeout(
      async () => {
        let data = cached;
        if (!data) {
          const res = await browserApi
            .GET("/v1/search/suggest", { params: { query: { q: typed } }, signal: controller.signal })
            .catch(() => null);
          data = res?.data;
          if (data) cache.current.set(key, data);
        }
        if (data && !controller.signal.aborted) setResult({ q: key, data });
      },
      cached ? 0 : DEBOUNCE_MS,
    );
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [typed]);

  // Keep the highlighted option visible when the list scrolls.
  useEffect(() => {
    if (activeIndex >= 0) document.getElementById(`${uid}-option-${activeIndex}`)?.scrollIntoView({ block: "nearest" });
  }, [activeIndex, uid]);

  function choose(option: Option) {
    setOpen(false);
    setActive(-1);
    if (option.key.startsWith("q-")) setValue(option.label);
    router.push(option.href);
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    const count = options.length;
    switch (e.key) {
      case "ArrowDown":
        if (!count) return;
        e.preventDefault();
        setOpen(true);
        setActive(expanded ? (activeIndex + 1) % count : 0);
        break;
      case "ArrowUp":
        if (!count) return;
        e.preventDefault();
        setOpen(true);
        setActive(expanded && activeIndex > 0 ? activeIndex - 1 : count - 1);
        break;
      case "Enter": {
        const option = activeIndex >= 0 ? options[activeIndex] : undefined;
        if (option) {
          e.preventDefault();
          choose(option);
        } else {
          setOpen(false); // plain search: the form submits as usual
        }
        break;
      }
      case "Escape":
        if (expanded) {
          e.preventDefault();
          setOpen(false);
          setActive(-1);
        } else if (value) {
          e.preventDefault();
          setValue("");
        }
        break;
      case "Tab":
        setOpen(false);
        break;
    }
  }

  return (
    <form action="/search" method="get" role="search" className={className}>
      <label htmlFor="site-search" className="sr-only">
        Search products
      </label>
      <div className="group/search relative">
        <SearchIcon className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted transition-colors group-focus-within/search:text-brand-600" />
        <input
          id="site-search"
          name="q"
          type="search"
          role="combobox"
          aria-expanded={expanded}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={activeIndex >= 0 ? optionId(activeIndex) : undefined}
          value={value}
          onChange={(e) => {
            typedRef.current = true;
            setValue(e.target.value);
            setOpen(true);
            setActive(-1);
          }}
          onKeyDown={onKeyDown}
          onFocus={() => setOpen(true)}
          onBlur={() => {
            setOpen(false);
            setActive(-1);
          }}
          placeholder="Search everything at Larkspur"
          autoComplete="off"
          autoCorrect="off"
          spellCheck={false}
          enterKeyHint="search"
          className="h-11 w-full rounded-full border border-line bg-sunken/70 pl-11 pr-14 text-base text-ink shadow-2xs inset-shadow-well transition-[background-color,border-color,box-shadow] duration-200 ease-snappy placeholder:text-muted hover:border-line-strong hover:bg-sunken focus-visible:border-brand-600 focus-visible:bg-raised focus-visible:outline-2 focus-visible:outline-transparent focus-visible:ring-4 focus-visible:ring-brand-500/20 sm:pr-28 md:h-12 [&::-webkit-search-cancel-button]:hidden"
        />
        <button
          type="submit"
          className="absolute right-1.5 top-1/2 inline-flex h-8 min-w-8 -translate-y-1/2 items-center justify-center gap-1.5 rounded-full bg-brand-600 px-2.5 text-sm font-semibold text-white shadow-glow inset-shadow-highlight transition-[background-color,box-shadow] duration-200 ease-snappy before:absolute before:-inset-1.5 before:content-[''] hover:bg-brand-700 hover:shadow-glow-lg sm:px-4 md:h-9 md:min-w-9"
        >
          <span className="max-sm:sr-only">Search</span>
          <ArrowRightIcon className="size-4 sm:hidden" />
        </button>
        {/* Always in the DOM (aria-controls must point at it); drawn over the page, so no layout shift. */}
        <div
          id={listId}
          role="listbox"
          aria-label="Search suggestions"
          hidden={!expanded}
          className="absolute inset-x-0 top-full z-50 mt-2 max-h-[min(36rem,calc(100dvh-9rem))] overflow-y-auto overscroll-contain rounded-2xl border border-line bg-raised py-1.5 shadow-xl"
        >
          {groups.map((group) => (
            <ul key={group.key} role="group" aria-labelledby={`${listId}-${group.key}`} className="py-1">
              <li
                role="presentation"
                id={`${listId}-${group.key}`}
                className="px-4 pb-1 pt-1.5 text-xs font-semibold uppercase tracking-eyebrow text-muted"
              >
                {group.label}
              </li>
              {group.options.map((option) => {
                const i = option.index;
                return (
                  <li
                    key={option.key}
                    id={optionId(i)}
                    role="option"
                    aria-selected={i === activeIndex}
                    // Keep focus in the box: choosing happens on click, not on blur.
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => choose(option)}
                    onMouseMove={() => i !== activeIndex && setActive(i)}
                    className={cn(
                      "mx-1.5 flex min-h-11 cursor-pointer items-center gap-3 rounded-xl px-2.5 py-1.5 text-sm text-ink",
                      i === activeIndex && "bg-brand-50 text-brand-900",
                    )}
                  >
                    {option.content}
                  </li>
                );
              })}
            </ul>
          ))}
        </div>
        <p role="status" className="sr-only">
          {expanded ? `${options.length} suggestions. Use the up and down arrows to review them.` : ""}
        </p>
      </div>
    </form>
  );
}

/**
 * Header search that remembers what you searched: on the search page it shows the current `q`.
 * (Department pages have their own filters, so only /search pre-fills.)
 */
export function HeaderSearch({ className }: { className?: string }) {
  const params = useSearchParams();
  const pathname = usePathname();
  const q = pathname === "/search" ? (params.get("q") ?? undefined) : undefined;
  // Re-mount when the query changes so client-side navigation refreshes the box.
  return <HeaderSearchForm key={q ?? ""} query={q} className={className} />;
}
