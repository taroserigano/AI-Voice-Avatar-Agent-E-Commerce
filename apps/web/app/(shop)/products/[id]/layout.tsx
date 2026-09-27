import type { ReactNode } from "react";
import { loadProduct } from "./load-product";

/**
 * Checks the product exists before anything streams. This layout sits above this segment's
 * loading.tsx, so an unknown id answers a real HTTP 404 (products/not-found.tsx) instead of a
 * 200 with the not-found UI streamed in later.
 */
export default async function ProductLayout({ params, children }: { params: Promise<{ id: string }>; children: ReactNode }) {
  await loadProduct((await params).id);
  return children;
}
