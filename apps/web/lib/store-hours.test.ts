import { describe, expect, it } from "vitest";
import { distinctServices, localClock, openingText } from "./store-hours";

const week = (opens: string | null, closes: string | null) =>
  ["mon", "tue", "wed", "thu", "fri", "sat", "sun"].map((day) => ({ day, opens, closes }));
const store = { timezone: "America/Chicago", hours: week("07:00", "22:00") };

// Saturday, Sep 26 2026 in Chicago (UTC-5).
const at = (hhmm: string) => new Date(`2026-09-26T${hhmm}:00-05:00`);

describe("localClock", () => {
  it("reads the day and time in the store's zone", () => {
    expect(localClock(new Date("2026-09-27T02:30:00Z"), "America/Chicago")).toEqual({ day: "sat", minutes: 21 * 60 + 30 });
  });
});

describe("openingText", () => {
  it("says when an open store closes", () => {
    expect(openingText(store, true, at("15:00"))).toBe("Closes 10 PM");
  });
  it("says when it opens later today, or tomorrow once it has closed", () => {
    expect(openingText(store, false, at("06:15"))).toBe("Opens 7 AM");
    expect(openingText(store, false, at("22:30"))).toBe("Opens 7 AM tomorrow");
  });
  it("names the day when tomorrow is closed", () => {
    const hours = week("07:00", "22:00").map((h) => (h.day === "sun" ? { ...h, opens: null, closes: null } : h));
    expect(openingText({ ...store, hours }, false, at("23:00"))).toBe("Opens 7 AM Monday");
  });
});

describe("distinctServices", () => {
  it("separates what every store offers from what varies", () => {
    const result = distinctServices([
      { services: ["Grocery", "Return drop-off", "Coffee bar"] },
      { services: ["Grocery", "Return drop-off", "EV charging"] },
    ]);
    expect(result).toEqual({ common: ["Grocery", "Return drop-off"], varying: ["Coffee bar", "EV charging"] });
  });
});
