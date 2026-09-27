import "server-only";

import { serverApi, unwrap } from "@/lib/api-server";
import { notFound } from "next/navigation";
import { cache } from "react";

/** The department for a slug, or notFound(). Deduped per request (layout and generateMetadata). */
export const loadDepartment = cache(async (slug: string) => {
  const api = await serverApi();
  const categories = await unwrap(await api.GET("/v1/categories"));
  const category = categories.find((c) => c.slug === slug);
  if (!category) notFound();
  return category;
});
