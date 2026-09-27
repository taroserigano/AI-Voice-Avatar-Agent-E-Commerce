import type { ReturnOut, ShipmentOut } from "@ai-commerce/contracts";
import { describe, expect, it } from "vitest";
import { formatMoney } from "./format";
import {
  addBusinessDays,
  blockedReturnText,
  cardLabel,
  deliveryEstimate,
  deliveryProgress,
  formatDay,
  freeShippingProgress,
  ineligibleTitle,
  orderFilterGroup,
  orderListDelivery,
  orderListReturnHint,
  orderNumber,
  orderStatusMeta,
  variantLabel,
  primaryShipment,
  refundDisplay,
  refundTimingPhrase,
  returnProgress,
} from "./orders";

function shipment(overrides: Partial<ShipmentOut> = {}): ShipmentOut {
  return {
    id: "s1",
    carrier: "Swiftline Parcel",
    service: "2-Day",
    tracking_number: "SW1",
    status: "in_transit",
    shipped_at: "2026-09-25T21:00:00-05:00",
    estimated_delivery_at: "2026-09-29T12:00:00-05:00",
    delivered_at: null,
    is_simulated: true,
    events: [],
    ...overrides,
  };
}

const order = { status: "fulfilling" as const, placed_at: "2026-09-25T12:00:00-05:00", delivered_at: null };

describe("orderNumber", () => {
  it("uses the last 8 characters of the id, uppercase", () => {
    expect(orderNumber("95267545-6c62-5784-becc-b33c336d27fc")).toBe("336D27FC");
  });
});

describe("dates", () => {
  it("formats in the store's time zone, not the machine's", () => {
    // 03:30 UTC on the 24th is still the evening of the 23rd in Chicago.
    expect(formatDay("2026-09-24T03:30:00Z")).toBe("Sep 23");
  });
});

describe("order status", () => {
  it("uses one label and tone per status, matching the list tabs", () => {
    expect(orderStatusMeta("fulfilling")).toEqual({ label: "In progress", tone: "brand" });
    expect(orderStatusMeta("delivered")).toEqual({ label: "Delivered", tone: "success" });
    expect(orderStatusMeta("canceled").label).toBe("Canceled");
    expect(orderFilterGroup("paid")).toBe("in_progress");
    expect(orderFilterGroup("fulfilling")).toBe("in_progress");
    expect(orderFilterGroup("delivered")).toBe("delivered");
    expect(orderFilterGroup("canceled")).toBe("canceled");
  });
  it("describes delivery for the list", () => {
    expect(orderListDelivery({ status: "delivered", delivered_at: "2026-09-23T12:27:35-05:00" })).toBe("Delivered Sep 23");
    expect(orderListDelivery({ status: "canceled", delivered_at: null })).toBe("Canceled");
  });
  it("gives an arrival date while it's on its way", () => {
    const moving = { status: "fulfilling" as const, delivered_at: null };
    expect(orderListDelivery({ ...moving, estimated_delivery_at: "2026-09-29T12:00:00-05:00" })).toBe("Arriving by Sep 29");
    expect(orderListDelivery({ ...moving, estimated_delivery_at: null })).toBe("On its way");
  });
});

describe("orderListReturnHint", () => {
  const delivered = { status: "delivered" as const, return_window_ends_at: null, has_open_return: false };
  it("shows an open return first", () => {
    expect(orderListReturnHint({ ...delivered, has_open_return: true })?.text).toBe("Return in progress");
  });
  it("shows the server's return deadline", () => {
    expect(orderListReturnHint({ ...delivered, return_window_ends_at: "2026-10-23T12:00:00-05:00" })?.text).toBe(
      "Returnable until Oct 23",
    );
  });
  it("says when nothing can come back, and stays quiet before delivery", () => {
    expect(orderListReturnHint(delivered)?.kind).toBe("none");
    expect(orderListReturnHint({ ...delivered, status: "fulfilling" })).toBeNull();
  });
  it("names the server's reason when nothing is returnable", () => {
    expect(orderListReturnHint(delivered, blockedReturnText([{ eligible: false, reason: "final_sale" }]))?.text).toBe(
      "Final sale",
    );
    expect(blockedReturnText([{ eligible: false, reason: "fully_returned" }])).toBe("Returned");
    expect(
      blockedReturnText([
        { eligible: false, reason: "outside_window" },
        { eligible: false, reason: "perishable_past_7_days" },
      ]),
    ).toBe("Return window closed");
    expect(
      blockedReturnText([
        { eligible: false, reason: "final_sale" },
        { eligible: false, reason: "fully_returned" },
      ]),
    ).toBe("No items left to return");
    expect(blockedReturnText([{ eligible: true, reason: "within_window" }])).toBeNull();
  });
});

describe("variantLabel", () => {
  it("hides placeholder variant names and keeps real ones", () => {
    expect(variantLabel("Each")).toBeNull();
    expect(variantLabel("Standard")).toBeNull();
    expect(variantLabel("Sand")).toBe("Sand");
    expect(variantLabel("$50")).toBe("$50");
  });
});

describe("cart shipping and delivery", () => {
  it("measures progress toward free shipping from the server's numbers", () => {
    const cart = (remaining: number) => ({ free_shipping_threshold_minor: 3500, free_shipping_remaining_minor: remaining });
    expect(freeShippingProgress(cart(3500))).toBe(0);
    expect(freeShippingProgress(cart(1750))).toBe(0.5);
    expect(freeShippingProgress(cart(0))).toBe(1);
  });
  it("skips weekends when counting business days", () => {
    expect(addBusinessDays("2026-09-25", 1)).toBe("2026-09-28"); // Fri + 1 → Mon
    expect(addBusinessDays("2026-09-26", 2)).toBe("2026-09-29"); // Sat + 2 → Tue
    expect(addBusinessDays("2026-09-28", 5)).toBe("2026-10-05"); // Mon + 5 → next Mon
  });
  it("gives a 2–5 business day window counted in the store's time zone", () => {
    // Saturday evening in Chicago (already Sunday in UTC).
    const est = deliveryEstimate(new Date("2026-09-27T02:00:00Z"));
    expect(est).toEqual({ from: "2026-09-29", to: "2026-10-02", text: "Tue, Sep 29 – Fri, Oct 2" });
  });
});

describe("deliveryProgress", () => {
  it("is null for canceled orders", () => {
    expect(deliveryProgress({ ...order, status: "canceled" }, null)).toBeNull();
  });
  it("maps shipment status to the current step", () => {
    expect(deliveryProgress(order, null)?.current).toBe(0);
    expect(deliveryProgress(order, shipment({ status: "label_created", shipped_at: null }))?.current).toBe(0);
    expect(deliveryProgress(order, shipment())?.current).toBe(1);
    expect(deliveryProgress(order, shipment({ status: "out_for_delivery" }))?.current).toBe(2);
    const done = deliveryProgress(
      { ...order, status: "delivered", delivered_at: "2026-09-23T12:00:00-05:00" },
      shipment({ status: "delivered", delivered_at: "2026-09-23T12:00:00-05:00" }),
    );
    expect(done?.current).toBe(3);
    expect(done?.steps[3]?.date).toBe("2026-09-23T12:00:00-05:00");
  });
  it("hides dates on steps not reached yet", () => {
    const p = deliveryProgress(order, shipment());
    expect(p?.steps[1]?.date).toBe("2026-09-25T21:00:00-05:00");
    expect(p?.steps[3]?.date).toBeNull();
  });
  it("flags a delivery exception", () => {
    const p = deliveryProgress(order, shipment({ status: "exception" }));
    expect(p?.issue).toBe(true);
    expect(p?.current).toBe(1);
  });
  it("prefers a parcel with a problem, then the one still coming", () => {
    const delivered = shipment({ id: "a", status: "delivered" });
    const moving = shipment({ id: "b", status: "in_transit" });
    expect(primaryShipment([delivered, moving])?.id).toBe("b");
    expect(primaryShipment([moving, shipment({ id: "c", status: "exception" })])?.id).toBe("c");
    expect(primaryShipment([])).toBeNull();
  });
});

describe("eligibility wording", () => {
  it("names each refund timing in plain words", () => {
    expect(refundTimingPhrase("instant")).toMatch(/carrier scans/);
    expect(refundTimingPhrase("after_inspection")).toMatch(/inspection/);
    expect(refundTimingPhrase(null)).toBeNull();
  });
  it("titles ineligible lines, including when the window closed", () => {
    expect(ineligibleTitle({ reason: "final_sale", window_ends_at: null })).toBe("Final sale");
    expect(ineligibleTitle({ reason: "outside_window", window_ends_at: "2026-09-12T12:27:35-05:00" })).toBe(
      "Return window closed on Sep 12",
    );
    expect(ineligibleTitle({ reason: "fully_returned", window_ends_at: null })).toBe("Already returned");
  });
});

describe("cardLabel", () => {
  it("shows brand and last four", () => {
    expect(cardLabel({ card_brand: "visa", card_last4: "4242" })).toBe("Visa ••4242");
    expect(cardLabel({ card_brand: "mastercard", card_last4: "4444" })).toBe("Mastercard ••4444");
  });
  it("falls back when the card is unknown", () => {
    expect(cardLabel(null)).toBe("your original payment method");
    expect(cardLabel({ card_brand: null, card_last4: null })).toBe("your original payment method");
  });
});

describe("returns", () => {
  it("places each return status on the stepper", () => {
    expect(returnProgress("requested")).toMatchObject({ kind: "steps", current: 0 });
    expect(returnProgress("in_transit")).toMatchObject({ kind: "steps", current: 1 });
    expect(returnProgress("review")).toMatchObject({ kind: "steps", current: 2, note: expect.any(String) });
    expect(returnProgress("closed")).toMatchObject({ kind: "steps", current: 4 });
    expect(returnProgress("rejected")).toMatchObject({ kind: "ended" });
  });

  const money = (m: number) => formatMoney(m);
  const refund = (status: NonNullable<ReturnOut["refund"]>["status"]): ReturnOut["refund"] => ({
    status,
    amount_minor: 7576,
    currency: "USD",
    requested_at: "2026-09-17T09:27:35-05:00",
    settled_at: "2026-09-17T09:29:35-05:00",
    failure_reason: null,
  });

  it("uses the server's refund amount and settle date", () => {
    const d = refundDisplay({ status: "closed", refund: refund("succeeded") }, "Visa ••4242", money);
    expect(d).toMatchObject({ title: "Refunded $75.76 to Visa ••4242 on Sep 17", tone: "success" });
  });
  it("explains a refund that hasn't started, by timing when known", () => {
    expect(refundDisplay({ status: "in_transit", refund: null }, "Visa ••4242", money).title).toBe(
      "Refund starts after we receive it",
    );
    expect(refundDisplay({ status: "in_transit", refund: null }, "Visa ••4242", money, "instant").title).toBe(
      "Refund starts at the carrier scan",
    );
  });
  it("never claims money moved when it didn't", () => {
    expect(refundDisplay({ status: "received", refund: refund("pending") }, "Visa", money).title).toBe("Refund pending");
    expect(refundDisplay({ status: "received", refund: refund("failed") }, "Visa", money).tone).toBe("danger");
    expect(refundDisplay({ status: "rejected", refund: null }, "Visa", money).title).toMatch(/No refund/);
  });
});
