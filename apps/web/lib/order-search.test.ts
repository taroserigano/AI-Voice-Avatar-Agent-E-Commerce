import { describe, expect, it } from "vitest";
import { filterOrders, matchesOrderQuery, parseOrderRange, rangeStart } from "./order-search";

// Order number is the id's last 8 hex characters, uppercase: "5C2E9A10".
const order = (placed_at: string, item_titles: string[], id = "0f3a4b6c-1d2e-4f50-8a9b-00005c2e9a10") => ({
  id,
  placed_at,
  item_titles,
});

describe("matchesOrderQuery", () => {
  const o = order("2026-09-20T12:00:00Z", ["Wool Socks, 3-Pack", "Organic Crew Tee"]);

  it("finds an order by its number, with or without the # and in any case", () => {
    expect(matchesOrderQuery(o, "#5C2E9A10")).toBe(true);
    expect(matchesOrderQuery(o, "5c2e9a10")).toBe(true);
    expect(matchesOrderQuery(o, "#9a10")).toBe(true);
    expect(matchesOrderQuery(o, "#FFFF0000")).toBe(false);
  });

  it("finds an order when every word appears in one item's title", () => {
    expect(matchesOrderQuery(o, "wool socks")).toBe(true);
    expect(matchesOrderQuery(o, "  TEE ")).toBe(true);
    // "wool" and "tee" are in different items: not one item the shopper means.
    expect(matchesOrderQuery(o, "wool tee")).toBe(false);
  });

  it("doesn't treat short hex-looking words as order numbers", () => {
    // "e9a" is in the order number, but three letters is a word search, and no title has it.
    expect(matchesOrderQuery(o, "e9a")).toBe(false);
  });

  it("matches everything when the query is empty", () => {
    expect(matchesOrderQuery(o, "   ")).toBe(true);
  });
});

describe("rangeStart", () => {
  const now = new Date("2026-09-26T15:00:00Z");

  it("counts back 30 days and 3 calendar months", () => {
    expect(rangeStart("30d", now)?.toISOString()).toBe("2026-08-27T15:00:00.000Z");
    expect(rangeStart("3m", now)?.toISOString()).toBe("2026-06-26T15:00:00.000Z");
  });

  it("starts this year at midnight Jan 1 in Dallas (UTC-6 in winter)", () => {
    expect(rangeStart("year", now)?.toISOString()).toBe("2026-01-01T06:00:00.000Z");
    // Still Dec 31 in Dallas at 03:00 UTC on Jan 1, so "this year" is the one ending.
    expect(rangeStart("year", new Date("2027-01-01T03:00:00Z"))?.toISOString()).toBe("2026-01-01T06:00:00.000Z");
  });

  it("has no start for all time", () => {
    expect(rangeStart("all", now)).toBeNull();
  });
});

describe("filterOrders", () => {
  const now = new Date("2026-09-26T15:00:00Z");
  const recent = order("2026-09-20T12:00:00Z", ["Gooseneck Kettle"], "00000000-0000-4000-8000-0000000000a1");
  const summer = order("2026-07-10T12:00:00Z", ["Gooseneck Kettle"], "00000000-0000-4000-8000-0000000000a2");
  const lastYear = order("2025-12-30T12:00:00Z", ["Throw Blanket"], "00000000-0000-4000-8000-0000000000a3");
  const all = [recent, summer, lastYear];

  it("combines the date range with the search", () => {
    expect(filterOrders(all, { query: "", range: "30d", now })).toEqual([recent]);
    expect(filterOrders(all, { query: "", range: "3m", now })).toEqual([recent, summer]);
    expect(filterOrders(all, { query: "", range: "year", now })).toEqual([recent, summer]);
    expect(filterOrders(all, { query: "kettle", range: "all", now })).toEqual([recent, summer]);
    expect(filterOrders(all, { query: "blanket", range: "year", now })).toEqual([]);
  });
});

describe("parseOrderRange", () => {
  it("accepts known ranges and falls back to all time", () => {
    expect(parseOrderRange("3m")).toBe("3m");
    expect(parseOrderRange(["year", "30d"])).toBe("year");
    expect(parseOrderRange("forever")).toBe("all");
    expect(parseOrderRange(undefined)).toBe("all");
  });
});
