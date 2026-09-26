import { describe, expect, it } from "vitest";
import { formatMoney, formatTime } from "./format";

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
