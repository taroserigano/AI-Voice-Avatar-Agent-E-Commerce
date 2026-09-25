/**
 * Typed commerce API client. `schema.d.ts` is generated from `openapi.json` by
 * `pnpm contracts`; CI fails if either is stale. Never edit them by hand.
 */
import createClient, { type ClientOptions } from "openapi-fetch";
import type { components, paths } from "./schema";

export type { components, paths };
export type Schemas = components["schemas"];

export type ProductSummary = Schemas["ProductSummary"];
export type ProductDetail = Schemas["ProductDetail"];
export type ProductPage = Schemas["ProductPage"];
export type CategoryOut = Schemas["CategoryOut"];
export type CartOut = Schemas["CartOut"];
export type CartLineOut = Schemas["CartLineOut"];
export type UserOut = Schemas["UserOut"];
export type AuthConfigOut = Schemas["AuthConfigOut"];
export type SearchMeta = Schemas["SearchMeta"];
export type OrderSummary = Schemas["OrderSummary"];
export type OrderDetail = Schemas["OrderDetail"];

export function createCommerceClient(options: ClientOptions) {
  return createClient<paths>(options);
}

export type CommerceClient = ReturnType<typeof createCommerceClient>;
