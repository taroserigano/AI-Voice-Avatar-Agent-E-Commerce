import { describe, expect, it } from "vitest";
import { safeReturnTo } from "./return-to";

// Same cases as services/commerce/tests/unit/test_returnto.py.
describe("safeReturnTo", () => {
  it.each(["/", "/cart", "/products/123?variant=abc", "/search?q=rain+boots#top", "/orders/9"])(
    "keeps same-site path %s",
    (value) => expect(safeReturnTo(value)).toBe(value),
  );

  it.each([
    null,
    undefined,
    "",
    "https://evil.example/phish",
    "http://localhost:3000/cart",
    "//evil.example",
    "/\\evil.example",
    "\\\\evil.example",
    "javascript:alert(1)",
    "cart",
    "/cart\nSet-Cookie: x=1",
    "/sign-in",
    "/sign-in?returnTo=/cart",
    "/sign-up",
    "/" + "a".repeat(3000),
  ])("falls back to home for %j", (value) => expect(safeReturnTo(value)).toBe("/"));
});
