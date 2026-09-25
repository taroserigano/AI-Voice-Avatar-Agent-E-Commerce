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
