import { Listing, type ListingParams } from "@/components/shop/listing";
import { WebVitalsReporter } from "@/components/web-vitals";
import { serverApi, unwrap } from "@/lib/api-server";
import { isLandingView, toProductQuery } from "@/lib/listing-query";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { loadDepartment } from "./load-department";

// The layout already answered 404 for an unknown slug; this reuses its (deduped) read.
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  return { title: (await loadDepartment((await params).slug)).name };
}

export default async function CategoryPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<ListingParams>;
}) {
  const { slug } = await params;
  const query = await searchParams;
  const api = await serverApi();
  const landing = isLandingView(query);
  const [categories, page, topRated] = await Promise.all([
    api.GET("/v1/categories").then(unwrap),
    api.GET("/v1/products", { params: { query: toProductQuery(query, slug) } }).then(unwrap),
    // The "Top rated" strip is optional: only on the unfiltered first page, and never fatal.
    landing
      ? api
          .GET("/v1/products", { params: { query: { category: slug, sort: "top_rated", in_stock: true, page_size: 6 } } })
          .then((r) => (r.data?.items ?? []).filter((p) => p.rating_count > 0))
          .catch(() => [])
      : Promise.resolve([]),
  ]);
  const category = categories.find((c) => c.slug === slug);
  if (!category) notFound();
  return (
    <>
      <WebVitalsReporter route="category" />
      <Listing
        page={page}
        params={query}
        basePath={`/c/${slug}`}
        heading={category.name}
        showCategoryFacet={false}
        category={{ slug: category.slug, name: category.name }}
        departments={categories.filter((c) => c.slug !== slug)}
        topRated={topRated.length >= 4 ? topRated : []}
      />
    </>
  );
}
