import { describe, expect, it } from "vitest";
import { byDistance, findPlace, formatMiles, milesBetween, spreadApart } from "./geo";

describe("spreadApart", () => {
  const dist = (a?: { x: number; y: number }, b?: { x: number; y: number }) =>
    a && b ? Math.hypot(b.x - a.x, b.y - a.y) : NaN;

  it("separates pins that would overlap and leaves distant ones alone", () => {
    const [a, b, c] = spreadApart(
      [
        { x: 100, y: 100 },
        { x: 110, y: 100 },
        { x: 300, y: 300 },
      ],
      38,
    );
    expect(dist(a, b)).toBeGreaterThanOrEqual(38);
    expect(c).toEqual({ x: 300, y: 300 });
  });

  it("splits pins on the exact same spot", () => {
    const [a, b] = spreadApart(
      [
        { x: 50, y: 50 },
        { x: 50, y: 50 },
      ],
      38,
    );
    expect(dist(a, b)).toBeGreaterThanOrEqual(38);
  });
});

const dallas = { lat: 32.7767, lng: -96.797 };
const fortWorth = { lat: 32.7555, lng: -97.3308 };

describe("milesBetween", () => {
  it("measures straight-line miles", () => {
    // Downtown Dallas to downtown Fort Worth is about 31 miles as the crow flies.
    expect(milesBetween(dallas, fortWorth)).toBeGreaterThan(30);
    expect(milesBetween(dallas, fortWorth)).toBeLessThan(32);
    expect(milesBetween(dallas, dallas)).toBe(0);
  });
});

describe("formatMiles", () => {
  it("shows one decimal", () => {
    expect(formatMiles(3.24)).toBe("3.2 mi");
    expect(formatMiles(0.04)).toBe("0.0 mi");
    expect(formatMiles(12)).toBe("12.0 mi");
  });
});

describe("findPlace", () => {
  it("finds DFW ZIP codes, including ZIP+4", () => {
    const hit = findPlace("75204");
    expect(hit.ok && hit.place.label).toBe("75204 (Dallas)");
    expect(findPlace("76013-1234").ok).toBe(true);
  });

  it("says when a ZIP is outside the area it knows", () => {
    expect(findPlace("10001")).toEqual({ ok: false, reason: "unknown_zip" });
  });

  it("finds cities however they're typed", () => {
    for (const q of ["Plano", "plano, tx", "PLANO Texas"]) {
      const hit = findPlace(q);
      expect(hit.ok && hit.place.label).toBe("Plano");
    }
    const ftw = findPlace("Ft. Worth");
    expect(ftw.ok && ftw.place.label).toBe("Fort Worth");
  });

  it("accepts a unique start of a name, but not an ambiguous one", () => {
    const rich = findPlace("richard");
    expect(rich.ok && rich.place.label).toBe("Richardson");
    // "de" is too short to guess from (Denton, DeSoto, Deep Ellum).
    expect(findPlace("de")).toEqual({ ok: false, reason: "unknown_place" });
    expect(findPlace("Springfield")).toEqual({ ok: false, reason: "unknown_place" });
    expect(findPlace("   ")).toEqual({ ok: false, reason: "empty" });
  });
});

describe("byDistance", () => {
  it("sorts nearest first", () => {
    const stores = [
      { code: "ARL", lat: 32.7359, lng: -97.115 },
      { code: "UPTOWN", lat: 32.8003, lng: -96.8009 },
      { code: "FRISCO", lat: 33.151, lng: -96.823 },
    ];
    const plano = findPlace("Plano");
    if (!plano.ok) throw new Error("Plano should be known");
    expect(byDistance(stores, plano.place).map((s) => s.item.code)).toEqual(["FRISCO", "UPTOWN", "ARL"]);
  });
});
