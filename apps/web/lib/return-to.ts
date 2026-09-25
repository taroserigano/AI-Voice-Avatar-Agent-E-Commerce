/**
 * Keep post-sign-in redirects on our own site. Mirrors
 * services/commerce/src/commerce/auth/returnto.py; both are tested with the same cases.
 */
export const DEFAULT_RETURN_TO = "/";
const AUTH_PAGES = ["/sign-in", "/sign-up", "/forgot-password", "/reset-password"];

export function safeReturnTo(value: string | null | undefined): string {
  if (!value || value.length > 2048) return DEFAULT_RETURN_TO;
  // Control characters (incl. CR/LF) could smuggle headers or confuse URL parsers.
  if (/[\u0000-\u001f\u007f]/.test(value)) return DEFAULT_RETURN_TO;
  if (!value.startsWith("/") || value.startsWith("//") || value.includes("\\")) {
    return DEFAULT_RETURN_TO;
  }
  let url: URL;
  try {
    url = new URL(value, "https://same-site.invalid");
  } catch {
    return DEFAULT_RETURN_TO;
  }
  if (url.origin !== "https://same-site.invalid") return DEFAULT_RETURN_TO;
  if (AUTH_PAGES.some((p) => url.pathname === p || url.pathname.startsWith(`${p}/`))) {
    return DEFAULT_RETURN_TO;
  }
  return value;
}
