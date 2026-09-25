import { describe, expect, it } from "vitest";
import { dollarsToMinor } from "@/components/shop/listing";
import { toProductQuery } from "./listing-query";

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
  it("a fixed category wins over the query string", () => {
    expect(toProductQuery({ category: "toys" }, "electronics").category).toBe("electronics");
  });
});
