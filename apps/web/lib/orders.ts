/**
 * Display helpers for orders, shipments, returns, and refunds.
 *
 * These only translate server values into words and step positions. They never decide whether
 * something is returnable or how much comes back: eligibility, windows, and every amount come
 * from the commerce API as-is.
 */
import type {
  LineReturnOption,
  OrderDetail,
  OrderSummary,
  PaymentOut,
  ReturnOut,
  ShipmentOut,
} from "@ai-commerce/contracts";

export type Tone = "neutral" | "brand" | "success" | "warning" | "danger" | "accent";

/** Dates render on the server in one fixed zone and locale, so they never shift on hydration. */
export const STORE_TIME_ZONE = "America/Chicago";
const LOCALE = "en-US";

const fmt = {
  day: new Intl.DateTimeFormat(LOCALE, { timeZone: STORE_TIME_ZONE, month: "short", day: "numeric" }),
  date: new Intl.DateTimeFormat(LOCALE, { timeZone: STORE_TIME_ZONE, month: "short", day: "numeric", year: "numeric" }),
  weekday: new Intl.DateTimeFormat(LOCALE, {
    timeZone: STORE_TIME_ZONE,
    weekday: "short",
    month: "short",
    day: "numeric",
  }),
  longWeekday: new Intl.DateTimeFormat(LOCALE, {
    timeZone: STORE_TIME_ZONE,
    weekday: "long",
    month: "long",
    day: "numeric",
  }),
  time: new Intl.DateTimeFormat(LOCALE, { timeZone: STORE_TIME_ZONE, hour: "numeric", minute: "2-digit" }),
  ymd: new Intl.DateTimeFormat("en-CA", { timeZone: STORE_TIME_ZONE, year: "numeric", month: "2-digit", day: "2-digit" }),
};

/** "Sep 23" */
export const formatDay = (iso: string) => fmt.day.format(new Date(iso));
/** "Sep 23, 2026" */
export const formatDate = (iso: string) => fmt.date.format(new Date(iso));
/** "Wed, Sep 23" */
export const formatWeekday = (iso: string) => fmt.weekday.format(new Date(iso));
/** "Wednesday, September 23" */
export const formatLongWeekday = (iso: string) => fmt.longWeekday.format(new Date(iso));
/** "12:27 PM" */
export const formatTime = (iso: string) => fmt.time.format(new Date(iso));
/** Calendar day in the store's zone, "2026-09-23" (for grouping). */
export const dayKey = (iso: string | Date) => fmt.ymd.format(typeof iso === "string" ? new Date(iso) : iso);

/** Short, human-friendly order reference: the last 8 characters of the id, uppercase. */
export function orderNumber(id: string): string {
  return id.replaceAll("-", "").slice(-8).toUpperCase();
}

export function plural(n: number, one: string, many = `${one}s`) {
  return `${n} ${n === 1 ? one : many}`;
}

/** Title-case a snake_case code we don't have a label for ("not_as_pictured" → "Not as pictured"). */
export function humanize(code: string): string {
  const words = code.replaceAll(/[_-]+/g, " ").trim();
  return words ? words.charAt(0).toUpperCase() + words.slice(1).toLowerCase() : code;
}

/* ---------- Order status ---------- */

export type StatusMeta = { label: string; tone: Tone };

/**
 * The one order-status vocabulary, used by the list, the detail page, and the filter tabs.
 * Where the parcel is (in transit, out for delivery) is the delivery card's job, not the badge's,
 * so an order never reads "In progress" in one place and "In transit" in another.
 */
const ORDER_STATUS: Record<OrderSummary["status"], StatusMeta> = {
  paid: { label: "Preparing", tone: "brand" },
  fulfilling: { label: "In progress", tone: "brand" },
  delivered: { label: "Delivered", tone: "success" },
  canceled: { label: "Canceled", tone: "neutral" },
};

const SHIPMENT_STATUS: Record<ShipmentOut["status"], StatusMeta> = {
  label_created: { label: "Preparing to ship", tone: "brand" },
  in_transit: { label: "In transit", tone: "brand" },
  out_for_delivery: { label: "Out for delivery", tone: "brand" },
  delivered: { label: "Delivered", tone: "success" },
  exception: { label: "Delivery issue", tone: "warning" },
};

/** Badge for an order: the same label and tone everywhere the order appears. */
export function orderStatusMeta(status: OrderSummary["status"]): StatusMeta {
  return ORDER_STATUS[status] ?? { label: humanize(status), tone: "neutral" };
}

export type OrderFilter = "all" | "in_progress" | "delivered" | "returns";

/** Read the orders list's `?view=` value, falling back to "all". */
export function parseOrderFilter(v: string | string[] | undefined): OrderFilter {
  return v === "in_progress" || v === "delivered" || v === "returns" ? v : "all";
}

/** Which list tab an order belongs to (the "returns" tab lists returns, not orders). */
export function orderFilterGroup(status: OrderSummary["status"]): "in_progress" | "delivered" | "canceled" {
  if (status === "paid" || status === "fulfilling") return "in_progress";
  return status === "delivered" ? "delivered" : "canceled";
}

export function shipmentStatusLabel(status: ShipmentOut["status"]): string {
  return SHIPMENT_STATUS[status]?.label ?? humanize(status);
}

/** One line under an order in the list. */
export function orderListDelivery(
  order: Pick<OrderSummary, "status" | "delivered_at"> & Partial<Pick<OrderSummary, "estimated_delivery_at">>,
): string {
  if (order.status === "canceled") return "Canceled";
  if (order.status === "delivered") return order.delivered_at ? `Delivered ${formatDay(order.delivered_at)}` : "Delivered";
  if (order.status === "fulfilling") {
    return order.estimated_delivery_at ? `Arriving by ${formatDay(order.estimated_delivery_at)}` : "On its way";
  }
  return "Preparing your order";
}

export type ReturnHint = { kind: "open" | "returning" | "none"; text: string };

/**
 * Why nothing in a delivered order can come back, from the server's per-line reasons: "Final
 * sale" for a gift card rather than a vague "No items left to return".
 */
export function blockedReturnText(lines: Pick<LineReturnOption, "eligible" | "reason">[]): string | null {
  if (lines.length === 0 || lines.some((l) => l.eligible)) return null;
  const reasons = new Set(lines.map((l) => l.reason));
  const closed = (r: LineReturnOption["reason"]) => r === "outside_window" || r === "perishable_past_7_days";
  if (reasons.size === 1 && reasons.has("final_sale")) return "Final sale";
  if (reasons.size === 1 && reasons.has("fully_returned")) return "Returned";
  if ([...reasons].every(closed)) return "Return window closed";
  return "No items left to return";
}

/**
 * The return line under a delivered order in the list, from the server's summary fields.
 * `blocked` is `blockedReturnText(...)` when the page looked up why nothing is returnable.
 */
export function orderListReturnHint(
  order: Pick<OrderSummary, "status" | "return_window_ends_at" | "has_open_return">,
  blocked?: string | null,
): ReturnHint | null {
  if (order.has_open_return) return { kind: "returning", text: "Return in progress" };
  if (order.status !== "delivered") return null;
  if (order.return_window_ends_at) {
    return { kind: "open", text: `Returnable until ${formatDay(order.return_window_ends_at)}` };
  }
  return { kind: "none", text: blocked ?? "No items left to return" };
}

/** Variant names that add nothing ("Each", "Standard") are hidden; real ones ("Sand", "$50") show. */
const PLAIN_VARIANTS = new Set(["", "each", "standard", "default", "default title", "one size"]);
export function variantLabel(name: string | null | undefined): string | null {
  if (!name) return null;
  return PLAIN_VARIANTS.has(name.trim().toLowerCase()) ? null : name;
}

/* ---------- Cart: free shipping and the delivery promise ---------- */

/** How far the cart is toward free shipping, 0–1, from the server's threshold and remainder. */
export function freeShippingProgress(cart: {
  free_shipping_threshold_minor: number;
  free_shipping_remaining_minor: number;
}): number {
  const { free_shipping_threshold_minor: threshold, free_shipping_remaining_minor: remaining } = cart;
  if (threshold <= 0 || remaining <= 0) return 1;
  return Math.min(1, Math.max(0, (threshold - remaining) / threshold));
}

/** Add business days (Mon–Fri) to a calendar date "YYYY-MM-DD". */
export function addBusinessDays(ymd: string, days: number): string {
  const [y = 0, m = 1, d = 1] = ymd.split("-").map(Number);
  const date = new Date(Date.UTC(y, m - 1, d));
  let left = days;
  while (left > 0) {
    date.setUTCDate(date.getUTCDate() + 1);
    const dow = date.getUTCDay();
    if (dow !== 0 && dow !== 6) left -= 1;
  }
  return date.toISOString().slice(0, 10);
}

const ymdWeekday = new Intl.DateTimeFormat(LOCALE, { timeZone: "UTC", weekday: "short", month: "short", day: "numeric" });
const formatYmd = (ymd: string) => ymdWeekday.format(new Date(`${ymd}T12:00:00Z`));

/**
 * "Tue, Sep 29 – Fri, Oct 2": our shipping promise (arrives in 2–5 business days, weekends
 * skipped), counted from today in the store's time zone.
 */
export function deliveryEstimate(now: Date, minDays = 2, maxDays = 5): { from: string; to: string; text: string } {
  const today = dayKey(now);
  const from = addBusinessDays(today, minDays);
  const to = addBusinessDays(today, maxDays);
  return { from, to, text: `${formatYmd(from)} – ${formatYmd(to)}` };
}

/* ---------- Delivery progress ---------- */

export type Step = { key: string; label: string; date: string | null };
export type Progress = { steps: Step[]; /** index of the current step */ current: number; issue: boolean };

/** The primary shipment (the most advanced one if there are several). */
export function primaryShipment(shipments: ShipmentOut[]): ShipmentOut | null {
  const rank: Record<ShipmentOut["status"], number> = {
    exception: 0,
    label_created: 1,
    in_transit: 2,
    out_for_delivery: 3,
    delivered: 4,
  };
  // An exception needs attention first; otherwise show the least-advanced parcel (what's still coming).
  const sorted = [...shipments].sort((a, b) => (rank[a.status] ?? 0) - (rank[b.status] ?? 0));
  return sorted[0] ?? null;
}

/**
 * Ordered → Shipped → Out for delivery → Delivered, driven by the shipment status.
 * Returns null for canceled orders (they show a canceled state instead).
 */
export function deliveryProgress(
  order: Pick<OrderDetail, "status" | "placed_at" | "delivered_at">,
  shipment: ShipmentOut | null,
): Progress | null {
  if (order.status === "canceled") return null;
  const outEvent = shipment?.events.find((e) => e.status === "out_for_delivery");
  const steps: Step[] = [
    { key: "ordered", label: "Ordered", date: order.placed_at },
    { key: "shipped", label: "Shipped", date: shipment?.shipped_at ?? null },
    { key: "out_for_delivery", label: "Out for delivery", date: outEvent?.occurred_at ?? null },
    { key: "delivered", label: "Delivered", date: shipment?.delivered_at ?? order.delivered_at },
  ];
  let current = 0;
  let issue = false;
  if (order.status === "delivered" || shipment?.status === "delivered") current = 3;
  else if (shipment?.status === "out_for_delivery") current = 2;
  else if (shipment?.status === "in_transit") current = 1;
  else if (shipment?.status === "exception") {
    issue = true;
    current = shipment.shipped_at ? 1 : 0;
  }
  // Only reached steps keep a date; a future step never shows a stale timestamp.
  return { steps: steps.map((s, i) => (i <= current ? s : { ...s, date: null })), current, issue };
}

/* ---------- Return eligibility (display only) ---------- */

export function refundTimingPhrase(timing: LineReturnOption["refund_timing"]): string | null {
  switch (timing) {
    case "instant":
      return "Instant refund when the carrier scans it";
    case "after_receipt":
      return "Refund after we receive it";
    case "after_inspection":
      return "Refund after inspection (3–5 business days)";
    case "no_return_needed":
      return "No need to send it back";
    default:
      return null;
  }
}

/** Short title for a line that can't be returned; the server's `message` explains it. */
export function ineligibleTitle(line: Pick<LineReturnOption, "reason" | "window_ends_at">): string {
  switch (line.reason) {
    case "final_sale":
      return "Final sale";
    case "outside_window":
      return line.window_ends_at ? `Return window closed on ${formatDay(line.window_ends_at)}` : "Return window closed";
    case "perishable_past_7_days":
      return line.window_ends_at ? `7-day window closed on ${formatDay(line.window_ends_at)}` : "7-day window closed";
    case "not_delivered":
      return "Not delivered yet";
    case "fully_returned":
      return "Already returned";
    case "canceled":
      return "Order canceled";
    default:
      return "Not returnable";
  }
}

/** Neutral for expected states (final sale, not here yet, already returned); warning for "you missed it". */
export function ineligibleTone(reason: LineReturnOption["reason"]): "neutral" | "warning" {
  return reason === "outside_window" || reason === "perishable_past_7_days" ? "warning" : "neutral";
}

/* ---------- Payment ---------- */

const CARD_BRANDS: Record<string, string> = {
  visa: "Visa",
  mastercard: "Mastercard",
  amex: "American Express",
  american_express: "American Express",
  discover: "Discover",
  jcb: "JCB",
  diners: "Diners Club",
  unionpay: "UnionPay",
};

/** "Visa ••4242", or a generic phrase when the card isn't known. */
export function cardLabel(method: { card_brand: string | null; card_last4: string | null } | null | undefined): string {
  if (!method || (!method.card_brand && !method.card_last4)) return "your original payment method";
  const brand = method.card_brand ? (CARD_BRANDS[method.card_brand.toLowerCase()] ?? humanize(method.card_brand)) : "Card";
  return method.card_last4 ? `${brand} ••${method.card_last4}` : brand;
}

export function paymentStatusMeta(status: PaymentOut["status"]): StatusMeta {
  switch (status) {
    case "succeeded":
      return { label: "Paid", tone: "success" };
    case "partially_refunded":
      return { label: "Partially refunded", tone: "brand" };
    case "refunded":
      return { label: "Refunded", tone: "neutral" };
    case "failed":
      return { label: "Payment failed", tone: "danger" };
    default:
      return { label: humanize(status), tone: "neutral" };
  }
}

/* ---------- Returns ---------- */

export const RETURN_STEPS = ["Requested", "In transit", "Received", "Inspected", "Closed"] as const;

export type ReturnProgress =
  | { kind: "steps"; current: number; note: string | null }
  | { kind: "ended"; label: string; tone: Tone };

export function returnProgress(status: ReturnOut["status"]): ReturnProgress {
  switch (status) {
    case "requested":
      return { kind: "steps", current: 0, note: null };
    case "authorized":
      return { kind: "steps", current: 0, note: "Approved: ship it back with the return label" };
    case "in_transit":
      return { kind: "steps", current: 1, note: null };
    case "received":
      return { kind: "steps", current: 2, note: null };
    case "review":
      return { kind: "steps", current: 2, note: "Under review by our returns team" };
    case "inspected":
      return { kind: "steps", current: 3, note: null };
    case "closed":
      return { kind: "steps", current: 4, note: null };
    case "rejected":
      return { kind: "ended", label: "Return not accepted", tone: "danger" };
    case "canceled":
      return { kind: "ended", label: "Return canceled", tone: "neutral" };
    default:
      return { kind: "steps", current: 0, note: null };
  }
}

export function returnStatusMeta(status: ReturnOut["status"]): StatusMeta {
  switch (status) {
    case "requested":
      return { label: "Requested", tone: "brand" };
    case "authorized":
      return { label: "Approved", tone: "brand" };
    case "in_transit":
      return { label: "On its way back", tone: "brand" };
    case "received":
      return { label: "Received", tone: "brand" };
    case "review":
      return { label: "Under review", tone: "warning" };
    case "inspected":
      return { label: "Inspected", tone: "brand" };
    case "closed":
      return { label: "Closed", tone: "success" };
    case "rejected":
      return { label: "Not accepted", tone: "danger" };
    case "canceled":
      return { label: "Canceled", tone: "neutral" };
    default:
      return { label: humanize(status), tone: "neutral" };
  }
}

const RETURN_REASONS: Record<string, string> = {
  not_as_pictured: "Not as pictured",
  ordered_too_many: "Ordered too many",
  changed_mind: "Changed my mind",
  no_longer_needed: "No longer needed",
  damaged: "Arrived damaged",
  defective: "Doesn't work",
  wrong_item: "Wrong item sent",
  wrong_size: "Wrong size",
  better_price: "Found a better price",
};

export const returnReasonLabel = (code: string) => RETURN_REASONS[code] ?? humanize(code);

const CONDITIONS: Record<string, string> = {
  unopened: "Unopened",
  like_new: "Like new",
  opened: "Opened",
  used: "Used",
  damaged: "Damaged",
};

export const conditionLabel = (code: string) => CONDITIONS[code] ?? humanize(code);

export type RefundDisplay = { title: string; detail: string | null; tone: Tone };

/**
 * What the shopper should expect from the refund, in plain words. `timing` is the line's refund
 * timing when the page knows it (it doesn't after a line is fully returned), for a sharper phrase.
 */
export function refundDisplay(
  ret: Pick<ReturnOut, "status" | "refund">,
  destination: string,
  currencyFormat: (minor: number) => string,
  timing?: LineReturnOption["refund_timing"],
): RefundDisplay {
  const refund = ret.refund;
  if (ret.status === "rejected") {
    return { title: "No refund for this return", detail: "The return wasn't accepted.", tone: "neutral" };
  }
  if (ret.status === "canceled" && (!refund || refund.status === "not_requested" || refund.status === "canceled")) {
    return { title: "No refund: the return was canceled", detail: null, tone: "neutral" };
  }
  switch (refund?.status ?? "not_requested") {
    case "not_requested": {
      const title =
        timing === "instant"
          ? "Refund starts at the carrier scan"
          : timing === "after_inspection"
            ? "Refund starts after we inspect it"
            : "Refund starts after we receive it";
      return { title, detail: `It goes back to ${destination}.`, tone: "neutral" };
    }
    case "requested":
    case "pending":
      return {
        title: "Refund pending",
        detail: refund
          ? `${currencyFormat(refund.amount_minor)} to ${destination}. Banks usually post it in 3–5 business days.`
          : null,
        tone: "brand",
      };
    case "succeeded":
      return {
        title: refund
          ? `Refunded ${currencyFormat(refund.amount_minor)} to ${destination}${
              refund.settled_at ? ` on ${formatDay(refund.settled_at)}` : ""
            }`
          : "Refunded",
        detail: null,
        tone: "success",
      };
    case "failed":
      return { title: "Refund failed: we're looking into it", detail: "We'll email you when it's sorted.", tone: "danger" };
    case "requires_action":
      return { title: "Refund needs attention", detail: "We'll contact you about the next step.", tone: "warning" };
    case "canceled":
      return { title: "Refund canceled", detail: null, tone: "neutral" };
    default:
      return { title: "Refund status unavailable", detail: null, tone: "neutral" };
  }
}
