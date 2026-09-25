import { type NextRequest, NextResponse } from "next/server";
import { isPublicPath } from "./lib/public-paths";
import { safeReturnTo } from "./lib/return-to";

const SESSION_COOKIE = "ac_session";

/**
 * Sign-in wall: a visitor with no session cookie is sent to /sign-in?returnTo=<page>.
 *
 * This only checks that a cookie exists; it is a convenience, not security. Every commerce
 * API route validates the session itself and answers 401, and Server Components redirect
 * to sign-in when that happens (an expired or revoked session).
 */
export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const here = safeReturnTo(`${pathname}${search}`);

  if (isPublicPath(pathname)) return NextResponse.next();

  if (!request.cookies.get(SESSION_COOKIE)?.value) {
    const url = request.nextUrl.clone();
    url.pathname = "/sign-in";
    url.search = here === "/" ? "" : `?returnTo=${encodeURIComponent(here)}`;
    return NextResponse.redirect(url);
  }

  // Tell Server Components where the visitor was going, for the 401 -> sign-in redirect.
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-return-to", here);
  const response = NextResponse.next({ request: { headers: requestHeaders } });
  // Private pages must never be served from a shared or back/forward cache.
  response.headers.set("Cache-Control", "private, no-store");
  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
