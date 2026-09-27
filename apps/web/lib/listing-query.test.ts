import { describe, expect, it } from "vitest";
import { dollarsToMinor } from "@/components/shop/listing";
import { formatTotal, isLandingView, toProductQuery } from "./listing-query";

describe("dollarsToMinor", () => {
  it("converts dollar strings to integer cents without float math", () => {
    expect(dollarsToMinor("25")).toBe(2500);
    expect(dollarsToMinor("19.9")).toBe(1990);
    expect(dollarsToMinor("0.07")).toBe(7);
    expect(dollarsToMinor(" 100.00 ")).toBe(10000);
  });
  it("rejects anything that isn't a plain amount", () => {
    for (const bad of ["", "abc", "-5", "1.234", "1e3", "$5"]) expect(dollarsToMinor(bad)).toBeUndefined();
  });
});

describe("toProductQuery", () => {
  it("drops invalid sort and page values", () => {
    const q = toProductQuery({ sort: "hack", page: "-3", brand: ["A", ""] });
    expect(q.sort).toBeUndefined();
    expect(q.page).toBe(1);
    expect(q.brand).toEqual(["A"]);
  });
  it("passes through the top-rated sort", () => {
    expect(toProductQuery({ sort: "top_rated" }).sort).toBe("top_rated");
  });
  it("keeps only well-formed tag and product type slugs", () => {
    const q = toProductQuery({ tag: ["organic", "fat-free", "Bad Tag", "x;drop"], product_type: "milk" });
    expect(q.tag).toEqual(["organic", "fat-free"]);
    expect(q.product_type).toEqual(["milk"]);
  });
  it("a fixed category wins over the query string", () => {
    expect(toProductQuery({ category: "toys" }, "electronics").category).toBe("electronics");
  });
  it("passes brand names through as given (they have spaces and capitals)", () => {
    expect(toProductQuery({ brand: "Sonora Audio" }).brand).toEqual(["Sonora Audio"]);
  });
});

describe("isLandingView", () => {
  it("is true only for the plain first page", () => {
    expect(isLandingView({})).toBe(true);
    expect(isLandingView({ page: "1", sort: "relevance" })).toBe(true);
  });
  it("is false once anything narrows or reorders the list", () => {
    for (const params of [
      { tag: "organic" },
      { product_type: ["milk"] },
      { brand: "Keyloft" },
      { max_price: "20" },
      { in_stock: "true" },
      { sort: "price_asc" },
      { page: "2" },
      { q: "milk" },
    ]) {
      expect(isLandingView(params)).toBe(false);
    }
  });
  it("ignores empty values left by a submitted form", () => {
    expect(isLandingView({ min_price: "", brand: [""], tag: [] })).toBe(true);
  });
});

describe("formatTotal", () => {
  it("shows exact totals as they are", () => {
    expect(formatTotal(324)).toBe("324");
    expect(formatTotal(397, false)).toBe("397");
    expect(formatTotal(1284, false)).toBe("1,284");
  });
  it("rounds a capped total down to a round lower bound", () => {
    expect(formatTotal(400, true)).toBe("400+");
    expect(formatTotal(397, true)).toBe("350+");
    expect(formatTotal(1284, true)).toBe("1,200+");
    expect(formatTotal(1000, true)).toBe("1,000+");
    expect(formatTotal(999, true)).toBe("950+");
    expect(formatTotal(57, true)).toBe("57+");
    expect(formatTotal(7, true)).toBe("7+");
  });
  it("doesn't round below the results already on screen", () => {
    expect(formatTotal(397, true, 24)).toBe("350+");
    expect(formatTotal(397, true, 360)).toBe("397+");
  });
  it("never shows more than search actually found", () => {
    for (let n = 1; n <= 2500; n++) {
      const shown = Number(formatTotal(n, true).replace(/[+,]/g, ""));
      expect(shown, String(n)).toBeLessThanOrEqual(n);
      expect(shown, String(n)).toBeGreaterThan(n * 0.6);
    }
  });
  it("never shows 0+", () => {
    expect(formatTotal(0, true)).toBe("0");
  });
});
