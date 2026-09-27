"use client";

import { PUBLIC_PAGES } from "@/lib/public-paths";
import { useLayoutEffect } from "react";

/**
 * Back/forward protection for private pages.
 *
 * Browsers may show a stored copy of a page on Back/Forward without asking the server
 * (the back/forward cache, or the HTTP cache when a page isn't `no-store`; Next's dev
 * server sends `no-cache` on purpose). After signing out, that copy could still show
 * private data. On a back/forward load this hides the page before it paints, re-checks the
 * session, and replaces the page with sign-in on 401.
 *
 * Public pages (sign-in, legal) are skipped, judged by the URL when the check runs (a restored
 * page may have client-navigated since it loaded): a signed-out visitor belongs there, so a 401
 * must not move them.
 *
 * Self-contained (no imports or outer variables): it is also serialized into the inline script.
 */
function installGuard(publicPages: readonly string[]) {
  const w = window as Window & { __sessionGuard?: boolean };
  if (w.__sessionGuard) return;
  w.__sessionGuard = true;
  function check() {
    const path = location.pathname;
    for (let i = 0; i < publicPages.length; i++) {
      if (path === publicPages[i] || path.indexOf(publicPages[i] + "/") === 0) return;
    }
    const style = document.createElement("style");
    style.textContent = "body{visibility:hidden}";
    document.head.appendChild(style);
    fetch("/api/v1/auth/me", { credentials: "same-origin", cache: "no-store" })
      .then(function (r) {
        if (r.status === 401) {
          location.replace("/sign-in?returnTo=" + encodeURIComponent(location.pathname + location.search));
        } else {
          style.remove();
        }
      })
      .catch(function () {
        style.remove();
      });
  }
  const nav = performance.getEntriesByType && (performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming);
  if (nav && nav.type === "back_forward") check();
  addEventListener("pageshow", function (e) {
    if (e.persisted) check();
  });
}

// Static text with no user data. When the CSP arrives (Milestone 5) it gets a nonce.
const SCRIPT = `(${installGuard.toString()})(${JSON.stringify(PUBLIC_PAGES)});`;

/**
 * Render inside the root layout's <head>, per Next's "Preventing flash before hydration" guide:
 * the browser runs the inline script while it parses the server HTML, before the first paint.
 *
 * When React renders this in the browser instead, the script is `text/plain` (inert, and no
 * "Encountered a script tag" warning), and the layout effect installs the same guard before
 * that render paints. That covers Next's client-rendered error documents, such as the 404 for
 * a missing product, whose HTML is an empty shell with no server-rendered layout.
 */
export function SessionGuard() {
  useLayoutEffect(() => installGuard(PUBLIC_PAGES), []);
  return (
    <script
      id="session-guard"
      type={typeof window === "undefined" ? "text/javascript" : "text/plain"}
      suppressHydrationWarning
      dangerouslySetInnerHTML={{ __html: SCRIPT }}
    />
  );
}
