import type { ActivityOut } from "@ai-commerce/contracts";
import { describe, expect, it } from "vitest";
import { dataNumber, dataString, groupByDay, recentlyViewed } from "./activity";

let n = 0;
function event(occurred_at: string, overrides: Partial<ActivityOut> = {}): ActivityOut {
  n += 1;
  return {
    id: `e${n}`,
    type: "signed_in",
    occurred_at,
    product: null,
    order_id: null,
    data: {},
    is_sample: false,
    ...overrides,
  };
}

describe("groupByDay", () => {
  const now = new Date("2026-09-26T15:00:00-05:00");

  it("labels today, yesterday, and older days in the store's zone", () => {
    const groups = groupByDay(
      [
        event("2026-09-26T06:00:00-05:00"),
        event("2026-09-26T01:00:00-05:00"),
        // 02:00 UTC on the 26th is still the 25th in Chicago.
        event("2026-09-26T02:00:00Z"),
        event("2026-09-21T12:00:00-05:00"),
        event("2025-12-31T12:00:00-06:00"),
      ],
      now,
    );
    expect(groups.map((g) => g.label)).toEqual(["Today", "Yesterday", "Sep 21", "Dec 31, 2025"]);
    expect(groups[0]?.events).toHaveLength(2);
  });

  it("returns nothing for no events", () => {
    expect(groupByDay([], now)).toEqual([]);
  });
});

describe("recentlyViewed", () => {
  const p = (id: string) => ({ id, title: id, image_path: `/images/${id}.svg` });
  it("dedupes by product, keeps newest first, and caps the count", () => {
    const events = [
      event("2026-09-26T06:00:00Z", { type: "viewed_product", product: p("a") }),
      event("2026-09-26T05:00:00Z", { type: "viewed_product", product: p("b") }),
      event("2026-09-26T04:00:00Z", { type: "viewed_product", product: p("a") }),
      event("2026-09-26T03:00:00Z", { type: "searched" }),
      event("2026-09-26T02:00:00Z", { type: "viewed_product", product: null }),
      event("2026-09-26T01:00:00Z", { type: "viewed_product", product: p("c") }),
    ];
    expect(recentlyViewed(events).map((x) => x.id)).toEqual(["a", "b", "c"]);
    expect(recentlyViewed(events, 2).map((x) => x.id)).toEqual(["a", "b"]);
  });
});

describe("event data", () => {
  it("reads only well-typed values", () => {
    const e = event("2026-09-26T06:00:00Z", { data: { query: "yoga mat", total_minor: 6493, bad: { x: 1 } } });
    expect(dataString(e, "query")).toBe("yoga mat");
    expect(dataNumber(e, "total_minor")).toBe(6493);
    expect(dataString(e, "bad")).toBeNull();
    expect(dataNumber(e, "query")).toBeNull();
  });
});
