/** Store-hours wording for the store locator (pure, no React). */
import type { DayHours, StoreOut } from "@ai-commerce/contracts";
import { formatTime } from "./format";

export const DAY_KEYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"] as const;

export const DAY_NAMES: Record<string, string> = {
  mon: "Monday",
  tue: "Tuesday",
  wed: "Wednesday",
  thu: "Thursday",
  fri: "Friday",
  sat: "Saturday",
  sun: "Sunday",
};

export function hoursText(opens: string | null, closes: string | null): string {
  return opens && closes ? `${formatTime(opens)} – ${formatTime(closes)}` : "Closed";
}

const toMinutes = (hhmm: string) => {
  const [h = 0, m = 0] = hhmm.split(":").map(Number);
  return h * 60 + m;
};

/** Day key ("sat") and minutes since midnight for `now` in the store's own time zone. */
export function localClock(now: Date, timeZone: string): { day: string; minutes: number } {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(now);
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  return { day: get("weekday").slice(0, 3).toLowerCase(), minutes: Number(get("hour")) * 60 + Number(get("minute")) };
}

/**
 * "Closes 10 PM", "Opens 7 AM", "Opens 7 AM tomorrow", or "Opens 7 AM Monday". `openNow` is the
 * server's answer (it decides the badge); this only words when that changes.
 */
export function openingText(store: Pick<StoreOut, "hours" | "timezone">, openNow: boolean, now: Date): string {
  const { day, minutes } = localClock(now, store.timezone);
  const byDay = new Map<string, DayHours>(store.hours.map((h) => [h.day, h]));
  const today = byDay.get(day);
  if (openNow) return today?.closes ? `Closes ${formatTime(today.closes)}` : "Open now";
  if (today?.opens && minutes < toMinutes(today.opens)) return `Opens ${formatTime(today.opens)}`;
  const start = DAY_KEYS.indexOf(day as (typeof DAY_KEYS)[number]);
  for (let i = 1; i <= 7; i += 1) {
    const key = DAY_KEYS[(start + i) % 7] ?? "mon";
    const h = byDay.get(key);
    if (h?.opens) return `Opens ${formatTime(h.opens)} ${i === 1 ? "tomorrow" : (DAY_NAMES[key] ?? key)}`;
  }
  return "Closed";
}

/** Services not every store offers (the useful ones to filter by), in first-seen order. */
export function distinctServices(stores: Pick<StoreOut, "services">[]): { common: string[]; varying: string[] } {
  const all: string[] = [];
  for (const s of stores) for (const svc of s.services) if (!all.includes(svc)) all.push(svc);
  const common = all.filter((svc) => stores.every((s) => s.services.includes(svc)));
  return { common, varying: all.filter((svc) => !common.includes(svc)) };
}
