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
