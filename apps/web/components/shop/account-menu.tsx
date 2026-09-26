"use client";

import { ChevronDownIcon, ClockIcon, PackageIcon, ReturnIcon, SitemapIcon } from "@/components/icons";
import Link from "next/link";
import { useEffect, useRef } from "react";
import { SignOutButton } from "./sign-out-button";

const itemClasses =
  "flex min-h-11 w-full items-center gap-3 rounded-lg px-3 text-left text-sm font-medium text-ink transition-colors duration-150 hover:bg-sunken focus-visible:bg-sunken [&_svg]:text-muted";

/**
 * Account disclosure built on <details>/<summary> (works without JS). With JS it also closes on
 * Escape (returning focus to the toggle), on a click outside, and after choosing a link.
 */
export function AccountMenu({ displayName, email }: { displayName: string; email: string }) {
  const ref = useRef<HTMLDetailsElement>(null);
  const firstName = displayName.split(" ")[0] ?? displayName;
  const initial = (firstName[0] ?? "?").toUpperCase();

  useEffect(() => {
    function onPointerDown(event: PointerEvent) {
      const menu = ref.current;
      if (menu?.open && !menu.contains(event.target as Node)) menu.open = false;
    }
    function onKeyDown(event: KeyboardEvent) {
      const menu = ref.current;
      if (event.key === "Escape" && menu?.open) {
        menu.open = false;
        menu.querySelector("summary")?.focus();
      }
    }
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  function close() {
    if (ref.current) ref.current.open = false;
  }

  return (
    <details ref={ref} className="group/account relative">
      <summary className="flex min-h-11 list-none items-center gap-2 rounded-full py-1 pl-1 pr-2.5 text-sm font-semibold text-ink transition-colors duration-150 hover:bg-sunken group-open/account:bg-sunken sm:pr-3">
        <span
          aria-hidden="true"
          className="grid size-8 place-items-center rounded-full bg-linear-to-br from-brand-500 to-brand-700 text-xs font-semibold text-white shadow-xs inset-shadow-highlight"
        >
          {initial}
        </span>
        <span className="max-sm:sr-only">
          <span className="sr-only">Account menu for </span>
          Hi, {firstName}
        </span>
        <ChevronDownIcon className="hidden size-4 text-muted transition-transform duration-200 ease-snappy group-open/account:rotate-180 sm:block" />
      </summary>
      <div className="absolute right-0 top-full z-50 mt-2 w-72 origin-top-right animate-scale-in rounded-2xl border border-line bg-raised p-2 shadow-xl">
        <div className="flex items-center gap-3 rounded-xl bg-mesh-light px-3 py-3">
          <span
            aria-hidden="true"
            className="grid size-10 shrink-0 place-items-center rounded-full bg-linear-to-br from-brand-500 to-brand-700 text-sm font-semibold text-white shadow-sm"
          >
            {initial}
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-semibold text-ink">{displayName}</span>
            <span className="block truncate text-xs text-muted">{email}</span>
          </span>
        </div>
        <ul className="mt-2 space-y-0.5">
          <li>
            <Link href="/orders" className={itemClasses} onClick={close}>
              <PackageIcon />
              Orders &amp; returns
            </Link>
          </li>
          <li>
            <Link href="/help/returns" className={itemClasses} onClick={close}>
              <ReturnIcon />
              How returns work
            </Link>
          </li>
          <li>
            <Link href="/activity" className={itemClasses} onClick={close}>
              <ClockIcon />
              Activity
            </Link>
          </li>
          <li>
            <Link href="/sitemap" className={itemClasses} onClick={close}>
              <SitemapIcon />
              Site map
            </Link>
          </li>
        </ul>
        <div className="my-2 border-t border-line" />
        <SignOutButton className={itemClasses} />
      </div>
    </details>
  );
}
