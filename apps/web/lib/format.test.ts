import { describe, expect, it } from "vitest";
import { addBusinessDays, deliveryWindow, formatMoney, formatShortDate, formatTime, isoDate } from "./format";

describe("formatTime", () => {
  it("shows store hours the way people say them", () => {
    expect(formatTime("07:00")).toBe("7 AM");
    expect(formatTime("12:00")).toBe("12 PM");
    expect(formatTime("21:30")).toBe("9:30 PM");
    expect(formatTime("00:00")).toBe("12 AM");
  });
});

describe("formatMoney", () => {
  it("formats minor units as dollars", () => {
    expect(formatMoney(12999)).toBe("$129.99");
    expect(formatMoney(0)).toBe("$0.00");
    expect(formatMoney(5)).toBe("$0.05");
  });
});

// Months are 0-based in the Date constructor: 8 is September.
describe("delivery estimates", () => {
  it("skips weekends when counting business days", () => {
    const friday = new Date(2026, 8, 25);
    expect(isoDate(addBusinessDays(friday, 1))).toBe("2026-09-28"); // Monday
    expect(isoDate(addBusinessDays(friday, 5))).toBe("2026-10-02");
    const saturday = new Date(2026, 8, 26);
    expect(isoDate(addBusinessDays(saturday, 1))).toBe("2026-09-28");
    const sunday = new Date(2026, 8, 27);
    expect(isoDate(addBusinessDays(sunday, 2))).toBe("2026-09-29");
  });

  it("gives a 2–5 business day window that can span a weekend and a month end", () => {
    const { start, end } = deliveryWindow(new Date(2026, 8, 30, 23, 30)); // Wednesday night
    expect(formatShortDate(start)).toBe("Fri, Oct 2");
    expect(formatShortDate(end)).toBe("Wed, Oct 7");
  });

  it("counts from the calendar day, whatever the time", () => {
    expect(isoDate(addBusinessDays(new Date(2026, 8, 28, 0, 1), 2))).toBe("2026-09-30");
    expect(isoDate(addBusinessDays(new Date(2026, 8, 28, 23, 59), 2))).toBe("2026-09-30");
  });

  it("doesn't change the date it was given", () => {
    const today = new Date(2026, 8, 28);
    addBusinessDays(today, 3);
    expect(isoDate(today)).toBe("2026-09-28");
  });
});
