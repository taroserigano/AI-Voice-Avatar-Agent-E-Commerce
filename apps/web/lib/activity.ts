/** Pure helpers for the activity timeline and "Recently viewed" (no React, easy to test). */
import type { ActivityOut } from "@ai-commerce/contracts";
import { dayKey, formatDate, formatDay } from "./orders";

export type ActivityGroup = { key: string; label: string; events: ActivityOut[] };

/**
 * Group events (already newest first) by calendar day in the store's time zone, labelled
 * "Today", "Yesterday", "Sep 21", or "Sep 21, 2025" for another year.
 */
export function groupByDay(events: ActivityOut[], now: Date): ActivityGroup[] {
  const today = dayKey(now);
  // Calendar arithmetic on the local date (not "now minus 24h"), so DST changes can't skip a day.
  const [y = 0, m = 1, d = 1] = today.split("-").map(Number);
  const yesterday = new Date(Date.UTC(y, m - 1, d - 1)).toISOString().slice(0, 10);
  const thisYear = today.slice(0, 4);
  const groups: ActivityGroup[] = [];
  for (const event of events) {
    const key = dayKey(event.occurred_at);
    let group = groups.at(-1);
    if (!group || group.key !== key) {
      const label =
        key === today
          ? "Today"
          : key === yesterday
            ? "Yesterday"
            : key.startsWith(thisYear)
              ? formatDay(event.occurred_at)
              : formatDate(event.occurred_at);
      group = { key, label, events: [] };
      groups.push(group);
    }
    group.events.push(event);
  }
  return groups;
}

export type ViewedProduct = NonNullable<ActivityOut["product"]>;

/** Newest-first unique products from viewed_product events, at most `max`. */
export function recentlyViewed(events: ActivityOut[], max = 8): ViewedProduct[] {
  const seen = new Set<string>();
  const out: ViewedProduct[] = [];
  for (const e of events) {
    if (e.type !== "viewed_product" || !e.product || seen.has(e.product.id)) continue;
    seen.add(e.product.id);
    out.push(e.product);
    if (out.length >= max) break;
  }
  return out;
}

/** Read a string/number field from an event's free-form `data`, ignoring anything else. */
export function dataString(event: ActivityOut, key: string): string | null {
  const v = event.data?.[key];
  return typeof v === "string" && v.trim() ? v : null;
}

export function dataNumber(event: ActivityOut, key: string): number | null {
  const v = event.data?.[key];
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}
