import { describe, expect, it } from "vitest";
import { isPublicPath } from "./public-paths";

describe("isPublicPath", () => {
  it.each([
    "/sign-in",
    "/sign-up",
    "/privacy",
    "/terms",
    "/accessibility",
    "/returns-policy",
    "/api/v1/auth/sign-in",
    "/_next/static/chunk.js",
    "/images/products/sonora-arc-wireless-headphones.svg",
  ])("%s is public", (path) => expect(isPublicPath(path)).toBe(true));

  it.each(["/", "/cart", "/search", "/products/0b6c", "/orders", "/c/electronics", "/sign-inx", "/privacyx", "/returns-policyx"])(
    "%s needs sign-in",
    (path) => expect(isPublicPath(path)).toBe(false),
  );
});
