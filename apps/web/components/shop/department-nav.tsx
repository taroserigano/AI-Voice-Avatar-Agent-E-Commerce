"use client";

import { ChevronLeftIcon, ChevronRightIcon, DepartmentIcon, GridIcon } from "@/components/icons";
import { containerClasses } from "@/components/ui/container";
import { cn } from "@/lib/cn";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

const pill =
  "inline-flex min-h-10 items-center gap-2 whitespace-nowrap rounded-full px-3 text-sm font-medium text-ink-soft transition-colors duration-150 hover:bg-sunken hover:text-ink lg:text-[0.8125rem] " +
  "aria-[current=page]:bg-brand-50 aria-[current=page]:text-brand-800 aria-[current=page]:ring-1 aria-[current=page]:ring-inset aria-[current=page]:ring-brand-100 " +
  "[&_svg]:size-4 [&_svg]:text-muted [&_svg]:transition-colors hover:[&_svg]:text-brand-600 aria-[current=page]:[&_svg]:text-brand-600";

// Mouse-only helpers: keyboard users reach every link with Tab (the rail scrolls to follow focus).
const scrollButton =
  "absolute top-1/2 z-10 grid size-8 -translate-y-1/2 place-items-center rounded-full bg-raised text-ink shadow-md ring-1 ring-line transition-opacity duration-200 hover:bg-sunken max-md:hidden";

/**
 * Department rail under the header. "All departments" stays pinned on the left; the rest scrolls
 * sideways, with a fade and arrow on whichever edge has more. Marks the current department with
 * aria-current.
 */
export function DepartmentNav({ categories }: { categories: { slug: string; name: string }[] }) {
  const pathname = usePathname();
  const scroller = useRef<HTMLDivElement>(null);
  const [edges, setEdges] = useState({ start: false, end: false });

  const measure = useCallback(() => {
    const el = scroller.current;
    if (!el) return;
    const start = el.scrollLeft > 4;
    const end = el.scrollLeft + el.clientWidth < el.scrollWidth - 4;
    setEdges((prev) => (prev.start === start && prev.end === end ? prev : { start, end }));
  }, []);

  useEffect(() => {
    const el = scroller.current;
    if (!el) return;
    measure();
    el.addEventListener("scroll", measure, { passive: true });
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => {
      el.removeEventListener("scroll", measure);
      observer.disconnect();
    };
  }, [measure]);

  function nudge(direction: 1 | -1) {
    const el = scroller.current;
    if (!el) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    el.scrollBy({ left: direction * el.clientWidth * 0.7, behavior: reduce ? "auto" : "smooth" });
  }

  return (
    <nav aria-label="Departments" className="border-t border-line/70">
      <div className={containerClasses("wide", "flex items-center gap-1")}>
        <Link
          href="/sitemap#departments"
          aria-current={pathname === "/sitemap" ? "page" : undefined}
          className={cn(pill, "shrink-0 font-semibold text-ink")}
        >
          <GridIcon />
          <span>
            All<span className="max-sm:sr-only"> departments</span>
          </span>
        </Link>
        <span aria-hidden="true" className="h-5 w-px shrink-0 bg-line" />
        <div className="relative min-w-0 flex-1">
          <div ref={scroller} className="overflow-x-auto scrollbar-none">
            <ul className="flex w-max items-center gap-1 py-1">
              {categories.map((c) => {
                const href = `/c/${c.slug}`;
                return (
                  <li key={c.slug}>
                    <Link href={href} aria-current={pathname === href ? "page" : undefined} className={pill}>
                      <DepartmentIcon slug={c.slug} />
                      {c.name}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
          {/* edge fades: a visual hint that the rail scrolls */}
          <span
            aria-hidden="true"
            className={cn(
              "pointer-events-none absolute inset-y-0 left-0 w-10 bg-linear-to-r from-raised to-transparent transition-opacity duration-200",
              edges.start ? "opacity-100" : "opacity-0",
            )}
          />
          <span
            aria-hidden="true"
            className={cn(
              "pointer-events-none absolute inset-y-0 right-0 w-16 bg-linear-to-l from-raised via-raised/80 to-transparent transition-opacity duration-200",
              edges.end ? "opacity-100" : "opacity-0",
            )}
          />
          <button
            type="button"
            tabIndex={-1}
            aria-hidden="true"
            onClick={() => nudge(-1)}
            className={cn(scrollButton, "left-0", edges.start ? "opacity-100" : "pointer-events-none opacity-0")}
          >
            <ChevronLeftIcon className="size-4" />
          </button>
          <button
            type="button"
            tabIndex={-1}
            aria-hidden="true"
            onClick={() => nudge(1)}
            className={cn(scrollButton, "right-0", edges.end ? "opacity-100" : "pointer-events-none opacity-0")}
          >
            <ChevronRightIcon className="size-4" />
          </button>
        </div>
      </div>
    </nav>
  );
}
