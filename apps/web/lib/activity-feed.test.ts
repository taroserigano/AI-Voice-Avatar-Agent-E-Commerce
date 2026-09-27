import type { ActivityOut } from "@ai-commerce/contracts";
import { describe, expect, it } from "vitest";
import { activityFeed, collapseRepeats, filterCounts, matchesFilter } from "./activity-feed";

let n = 0;
function ev(type: ActivityOut["type"], at: string, extra: Partial<ActivityOut> = {}): ActivityOut {
  n += 1;
  return { id: `e${n}`, type, occurred_at: at, data: {}, is_sample: false, order_id: null, product: null, ...extra };
}
const product = (id: string) => ({
  id,
  title: `Product ${id}`,
  image_path: `/images/${id}.svg`,
  price_minor: 499,
  currency: "USD",
  in_stock: true,
});

describe("collapseRepeats", () => {
  it("folds the same product viewed twice in a row into one row, keeping the newest", () => {
    const events = [
      ev("viewed_product", "2026-09-26T15:03:00-05:00", { product: product("a") }),
      ev("viewed_product", "2026-09-26T15:02:00-05:00", { product: product("a") }),
      ev("viewed_product", "2026-09-26T15:01:00-05:00", { product: product("b") }),
      ev("viewed_product", "2026-09-26T15:00:00-05:00", { product: product("a") }),
    ];
    const items = collapseRepeats(events);
    expect(items.map((i) => [i.event.product?.id, i.count])).toEqual([
      ["a", 2],
      ["b", 1],
      ["a", 1], // not consecutive, so it stays
    ]);
    expect(items[0]?.event.occurred_at).toBe("2026-09-26T15:03:00-05:00");
  });
  it("treats the same search typed differently as a repeat, but different searches as distinct", () => {
    const items = collapseRepeats([
      ev("searched", "2026-09-26T10:02:00-05:00", { data: { query: "Milk " } }),
      ev("searched", "2026-09-26T10:01:00-05:00", { data: { query: "milk" } }),
      ev("searched", "2026-09-26T10:00:00-05:00", { data: { query: "eggs" } }),
    ]);
    expect(items.map((i) => i.count)).toEqual([2, 1]);
  });
});

describe("activity filters", () => {
  const events = [
    ev("searched", "2026-09-26T12:00:00-05:00", { data: { query: "tea" } }),
    ev("viewed_product", "2026-09-26T11:00:00-05:00", { product: product("a") }),
    ev("added_to_cart", "2026-09-26T10:00:00-05:00", { product: product("a") }),
    ev("started_return", "2026-09-25T10:00:00-05:00", { order_id: "o1" }),
    ev("contacted_support", "2026-09-25T09:00:00-05:00"),
    ev("placed_order", "2026-09-24T09:00:00-05:00", { order_id: "o2" }),
  ];
  it("puts returns, refunds, and support together, and orders only under All", () => {
    expect(events.filter((e) => matchesFilter(e, "support")).map((e) => e.type)).toEqual([
      "started_return",
      "contacted_support",
    ]);
    expect(filterCounts(events)).toEqual({ all: 6, searches: 1, viewed: 1, cart: 1, support: 2 });
  });
  it("groups the filtered feed by day in the store's time zone", () => {
    const groups = activityFeed(events, "all", new Date("2026-09-26T20:00:00Z"));
    expect(groups.map((g) => [g.label, g.items.length])).toEqual([
      ["Today", 3],
      ["Yesterday", 2],
      ["Sep 24", 1],
    ]);
    expect(activityFeed(events, "cart", new Date("2026-09-26T20:00:00Z"))).toHaveLength(1);
  });
});
