import "server-only";

import { serverApi, unwrap } from "@/lib/api-server";
import { notFound } from "next/navigation";
import { cache } from "react";

export const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * The order, or notFound(). The API answers 404 for orders that aren't yours too, so a stranger's
 * order id looks exactly like a missing one. Deduped per request: the layout (which gates the
 * route so a missing order is a real HTTP 404), generateMetadata, and the page share one read.
 */
export const loadOrder = cache(async (id: string) => {
  if (!UUID_RE.test(id)) notFound();
  const api = await serverApi();
  const result = await api.GET("/v1/orders/{order_id}", { params: { path: { order_id: id } } });
  if (result.response.status === 404) notFound();
  return unwrap(result);
});
