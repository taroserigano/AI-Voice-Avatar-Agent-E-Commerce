import "server-only";

import { createCommerceClient } from "@ai-commerce/contracts";
import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";
import { cache } from "react";

const COMMERCE_API_URL = process.env.COMMERCE_API_URL ?? "http://localhost:8000";
export const SESSION_COOKIE = "ac_session";

/**
 * A commerce API client for Server Components. It forwards the visitor's session cookie
 * and address, and never caches: every render reads current prices and stock.
 */
export async function serverApi() {
  const jar = await cookies();
  const hdrs = await headers();
  const session = jar.get(SESSION_COOKIE)?.value;
  const forwardedFor = hdrs.get("x-forwarded-for");
  return createCommerceClient({
    baseUrl: COMMERCE_API_URL,
    headers: {
      ...(session ? { cookie: `${SESSION_COOKIE}=${session}` } : {}),
      ...(forwardedFor ? { "x-forwarded-for": forwardedFor } : {}),
    },
    fetch: (req: Request) => fetch(req, { cache: "no-store" }),
  });
}

/** Where the visitor was going, set by proxy.ts, for the sign-in redirect. */
export async function currentPath(): Promise<string> {
  return (await headers()).get("x-return-to") ?? "/";
}

/** Send the visitor to sign-in, then back here. */
export async function redirectToSignIn(): Promise<never> {
  redirect(`/sign-in?returnTo=${encodeURIComponent(await currentPath())}`);
}

/**
 * Unwrap an API result in a Server Component: 401 means the session is gone (expired or
 * signed out elsewhere), so go to sign-in; other errors surface to the error boundary.
 */
export async function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): Promise<T> {
  if (result.response.status === 401) return redirectToSignIn();
  if (result.data === undefined) {
    throw new Error(`Commerce API error ${result.response.status}`);
  }
  return result.data;
}

export const getMe = cache(async () => {
  const api = await serverApi();
  return unwrap(await api.GET("/v1/auth/me"));
});

export const getAuthConfig = cache(async () => {
  const api = await serverApi();
  const { data } = await api.GET("/v1/auth/config");
  return data ?? { provider: "dev" as const, development_sign_in: true, min_password_length: 8 };
});
