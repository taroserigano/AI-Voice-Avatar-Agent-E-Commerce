/** Store links and lookups shared by the store locator and the store pages (pure, no React). */
import type { StoreOut } from "@ai-commerce/contracts";

/** URL segment for a store: its code in lowercase ("dal-uptown"), stable across reseeds. */
export const storeSlug = (code: string) => code.toLowerCase();

export const storePath = (store: Pick<StoreOut, "code">) => `/stores/${storeSlug(store.code)}`;

/** The store a URL segment names: its code (any case) or its id. */
export function findStore<T extends Pick<StoreOut, "code" | "id">>(stores: T[], segment: string): T | undefined {
  const s = decodeURIComponent(segment).toLowerCase();
  return stores.find((store) => storeSlug(store.code) === s || store.id.toLowerCase() === s);
}

/** Google Maps directions to the store's pin (opens Maps; no key needed). */
export function directionsUrl(s: Pick<StoreOut, "latitude" | "longitude">): string {
  return `https://www.google.com/maps/dir/?api=1&destination=${s.latitude},${s.longitude}`;
}

/** Keyless Google Maps embed centered on one store. */
export function embedUrl(s: Pick<StoreOut, "latitude" | "longitude">, zoom = 14): string {
  return `https://maps.google.com/maps?q=${s.latitude},${s.longitude}&z=${zoom}&output=embed`;
}

/** `tel:` link for a display phone number. */
export const telHref = (phone: string) => `tel:${phone.replace(/[^\d+]/g, "")}`;
