/** Search and date-range filtering for the order list (pure, no React). */
import type { OrderSummary } from "@ai-commerce/contracts";
import { STORE_TIME_ZONE, orderNumber } from "./orders";

export type OrderRange = "all" | "30d" | "3m" | "year";

export const ORDER_RANGES: { value: OrderRange; label: string }[] = [
  { value: "all", label: "All time" },
  { value: "30d", label: "Last 30 days" },
  { value: "3m", label: "Last 3 months" },
  { value: "year", label: "This year" },
];

export function parseOrderRange(v: string | string[] | undefined): OrderRange {
  const value = Array.isArray(v) ? v[0] : v;
  return ORDER_RANGES.some((r) => r.value === value) ? (value as OrderRange) : "all";
}

/** The earliest placed date a range includes, or null for "All time". */
export function rangeStart(range: OrderRange, now: Date): Date | null {
  if (range === "all") return null;
  if (range === "30d") return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
  if (range === "3m") {
    const d = new Date(now);
    d.setUTCMonth(d.getUTCMonth() - 3);
    return d;
  }
  // "This year" is the calendar year where the stores are (Dallas), from Jan 1 at midnight local.
  const year = Number(new Intl.DateTimeFormat("en-US", { timeZone: STORE_TIME_ZONE, year: "numeric" }).format(now));
  const utcMidnight = Date.UTC(year, 0, 1);
  const offset = zoneOffsetMinutes(new Date(utcMidnight), STORE_TIME_ZONE);
  return new Date(utcMidnight - offset * 60 * 1000);
}

/** Minutes the zone is ahead of UTC at `at` (Chicago: -360 in winter). */
function zoneOffsetMinutes(at: Date, timeZone: string): number {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(at);
  const get = (type: string) => Number(parts.find((p) => p.type === type)?.value ?? 0);
  const asUtc = Date.UTC(get("year"), get("month") - 1, get("day"), get("hour"), get("minute"));
  return Math.round((asUtc - at.getTime()) / 60000);
}

const normalize = (s: string) =>
  s
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "");

/**
 * Whether an order matches what the shopper typed: its order number ("#1A2B3C4D", with or without
 * the #, or part of it) or every word appearing in one item's title ("wool socks").
 */
export function matchesOrderQuery(order: Pick<OrderSummary, "id" | "item_titles">, query: string): boolean {
  const q = normalize(query).trim();
  if (!q) return true;
  const compact = q.replace(/^#/, "").replace(/\s+/g, "");
  // Order numbers are hex, so plain words like "beef" could look like one: count it as a number
  // search only with a digit, a leading "#", or most of a number typed.
  const looksLikeNumber =
    /^[0-9a-f]{4,8}$/.test(compact) && (/\d/.test(compact) || q.startsWith("#") || compact.length >= 6);
  if (looksLikeNumber && orderNumber(order.id).toLowerCase().includes(compact)) return true;
  const words = q.replace(/^#/, "").split(/\s+/).filter(Boolean);
  return order.item_titles.some((title) => {
    const t = normalize(title);
    return words.every((w) => t.includes(w));
  });
}

export function filterOrders<T extends Pick<OrderSummary, "id" | "item_titles" | "placed_at">>(
  orders: T[],
  { query, range, now }: { query: string; range: OrderRange; now: Date },
): T[] {
  const start = rangeStart(range, now);
  return orders.filter(
    (o) => (start === null || new Date(o.placed_at) >= start) && matchesOrderQuery(o, query),
  );
}
