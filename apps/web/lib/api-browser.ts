"use client";

import { createCommerceClient } from "@ai-commerce/contracts";

/**
 * The commerce API client for the browser. Calls go to /api on this origin (rewritten to
 * the API by next.config.ts), so the HttpOnly session cookie rides along automatically.
 */
export const browserApi = createCommerceClient({ baseUrl: "/api", credentials: "same-origin" });

export function errorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (error && typeof error === "object" && "detail" in error) {
    const detail = (error as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0] && typeof detail[0] === "object" && "msg" in detail[0]) {
      return String((detail[0] as { msg: unknown }).msg).replace(/^Value error, /, "");
    }
  }
  return fallback;
}

/** After a 401 in the browser, do a full navigation so the proxy and server agree. */
export function goToSignIn() {
  const here = `${window.location.pathname}${window.location.search}`;
  // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- full reload on auth loss
  window.location.assign(`/sign-in?returnTo=${encodeURIComponent(here)}`);
}
