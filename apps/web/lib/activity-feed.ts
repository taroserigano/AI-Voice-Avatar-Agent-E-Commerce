/** Filtering and de-duplication for the activity page (pure, no React). */
import type { ActivityOut } from "@ai-commerce/contracts";
import { groupByDay } from "./activity";

export type ActivityFilter = "all" | "searches" | "viewed" | "cart" | "support";

export const ACTIVITY_FILTERS: { value: ActivityFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "searches", label: "Searches" },
  { value: "viewed", label: "Viewed" },
  { value: "cart", label: "Cart" },
  { value: "support", label: "Returns & support" },
];

const FILTER_TYPES: Record<Exclude<ActivityFilter, "all">, ActivityOut["type"][]> = {
  searches: ["searched"],
  viewed: ["viewed_product"],
  cart: ["added_to_cart"],
  support: ["started_return", "refund_issued", "contacted_support"],
};

export function matchesFilter(event: ActivityOut, filter: ActivityFilter): boolean {
  return filter === "all" || FILTER_TYPES[filter].includes(event.type);
}

/** What an event is about, so "Viewed X" twice in a row reads as one row. */
function subjectKey(event: ActivityOut): string {
  const query = event.data?.query;
  const ref = event.data?.reference ?? event.data?.rma_number;
  return [
    event.type,
    event.product?.id ?? "",
    event.order_id ?? "",
    typeof query === "string" ? query.trim().toLowerCase() : "",
    typeof ref === "string" ? ref : "",
  ].join("|");
}

export type FeedItem = { event: ActivityOut; /** how many identical events in a row this row stands for */ count: number };

/** Collapse consecutive repeats (same kind, same product/search/order), keeping the newest. */
export function collapseRepeats(events: ActivityOut[]): FeedItem[] {
  const out: FeedItem[] = [];
  let lastKey: string | null = null;
  for (const event of events) {
    const key = subjectKey(event);
    const last = out.at(-1);
    if (last && key === lastKey) last.count += 1;
    else out.push({ event, count: 1 });
    lastKey = key;
  }
  return out;
}

export type FeedGroup = { key: string; label: string; items: FeedItem[] };

/** Filter, group by day in the store's zone ("Today", "Yesterday", "Sep 21"), and collapse repeats per day. */
export function activityFeed(events: ActivityOut[], filter: ActivityFilter, now: Date): FeedGroup[] {
  return groupByDay(
    events.filter((e) => matchesFilter(e, filter)),
    now,
  ).map((g) => ({ key: g.key, label: g.label, items: collapseRepeats(g.events) }));
}

export function filterCounts(events: ActivityOut[]): Record<ActivityFilter, number> {
  const counts = { all: 0, searches: 0, viewed: 0, cart: 0, support: 0 } satisfies Record<ActivityFilter, number>;
  for (const f of ACTIVITY_FILTERS) {
    counts[f.value] = collapseRepeats(events.filter((e) => matchesFilter(e, f.value))).length;
  }
  return counts;
}
