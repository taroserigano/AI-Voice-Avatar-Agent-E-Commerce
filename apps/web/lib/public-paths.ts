/**
 * Pages anyone may open without signing in. Everything else sends a signed-out visitor to
 * /sign-in. This is a convenience only: the commerce API checks the session on every call.
 */
export const PUBLIC_PAGES = [
  "/sign-in",
  "/sign-up",
  "/privacy",
  "/terms",
  "/accessibility",
  "/returns-policy",
] as const;

export function isPublicPath(pathname: string): boolean {
  if (PUBLIC_PAGES.some((p) => pathname === p || pathname.startsWith(`${p}/`))) return true;
  // The API enforces its own auth (401), and static assets carry no private data.
  if (pathname.startsWith("/api/")) return true;
  if (pathname.startsWith("/_next/")) return true;
  if (pathname === "/favicon.ico" || pathname === "/robots.txt") return true;
  if (pathname.startsWith("/images/")) return true;
  return false;
}
