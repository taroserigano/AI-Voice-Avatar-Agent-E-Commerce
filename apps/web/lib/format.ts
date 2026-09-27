const formatters = new Map<string, Intl.NumberFormat>();

/** Format integer minor units (cents) for display. Never do money math in the browser. */
export function formatMoney(amountMinor: number, currency = "USD"): string {
  let fmt = formatters.get(currency);
  if (!fmt) {
    fmt = new Intl.NumberFormat("en-US", { style: "currency", currency });
    formatters.set(currency, fmt);
  }
  return fmt.format(amountMinor / 100);
}

/** Store hours: "07:00" -> "7 AM", "21:30" -> "9:30 PM", "00:00" -> "12 AM". */
export function formatTime(hhmm: string): string {
  const [h = 0, m = 0] = hhmm.split(":").map(Number);
  const suffix = h >= 12 ? "PM" : "AM";
  const hour = h % 12 === 0 ? 12 : h % 12;
  return m ? `${hour}:${String(m).padStart(2, "0")} ${suffix}` : `${hour} ${suffix}`;
}

/** `date` moved forward by `days` business days (Saturdays and Sundays don't count). */
export function addBusinessDays(date: Date, days: number): Date {
  const out = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  let left = days;
  while (left > 0) {
    out.setDate(out.getDate() + 1);
    const day = out.getDay();
    if (day !== 0 && day !== 6) left -= 1;
  }
  return out;
}

/**
 * Standard shipping estimate: arrives 2–5 business days after `from` (weekends skipped).
 * For display only; the warehouse's real ship date isn't known here.
 */
export function deliveryWindow(from: Date, minDays = 2, maxDays = 5): { start: Date; end: Date } {
  return { start: addBusinessDays(from, minDays), end: addBusinessDays(from, maxDays) };
}

const shortDate = new Intl.DateTimeFormat("en-US", { weekday: "short", month: "short", day: "numeric" });

/** "Tue, Sep 29" */
export function formatShortDate(date: Date): string {
  return shortDate.format(date);
}

/** "2026-09-29" (local calendar date), for a `<time dateTime>` attribute. */
export function isoDate(date: Date): string {
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${m}-${d}`;
}
