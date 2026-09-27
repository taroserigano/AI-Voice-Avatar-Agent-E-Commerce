import { describe, expect, it } from "vitest";
import { directionsUrl, findStore, storePath, telHref } from "./stores";

const stores = [
  { id: "3f0c2d1e-0000-4000-8000-000000000001", code: "DAL-UPTOWN" },
  { id: "3f0c2d1e-0000-4000-8000-000000000002", code: "PLN-LEGACY" },
];

describe("store links", () => {
  it("uses the lowercase code, which survives reseeding", () => {
    expect(storePath({ code: "DAL-UPTOWN" })).toBe("/stores/dal-uptown");
  });

  it("finds a store by code in any case, or by id", () => {
    expect(findStore(stores, "pln-legacy")?.code).toBe("PLN-LEGACY");
    expect(findStore(stores, "DAL-UPTOWN")?.code).toBe("DAL-UPTOWN");
    expect(findStore(stores, "3f0c2d1e-0000-4000-8000-000000000002")?.code).toBe("PLN-LEGACY");
    expect(findStore(stores, "nowhere")).toBeUndefined();
  });

  it("builds directions and phone links", () => {
    expect(directionsUrl({ latitude: 32.8, longitude: -96.8 })).toBe(
      "https://www.google.com/maps/dir/?api=1&destination=32.8,-96.8",
    );
    expect(telHref("(214) 555-0101")).toBe("tel:2145550101");
  });
});
