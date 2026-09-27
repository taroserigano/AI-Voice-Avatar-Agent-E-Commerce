import type { ReactNode } from "react";
import { loadOrder } from "./load-order";

/**
 * Checks the order exists (and is yours) before anything streams. This layout sits above this
 * segment's loading.tsx, so an unknown id answers a real HTTP 404 (orders/not-found.tsx) instead
 * of a 200 with the not-found UI streamed in later.
 */
export default async function OrderLayout({ params, children }: { params: Promise<{ id: string }>; children: ReactNode }) {
  await loadOrder((await params).id);
  return children;
}
