import { Listing, type ListingParams } from "@/components/shop/listing";
import { WebVitalsReporter } from "@/components/web-vitals";
import { serverApi, unwrap } from "@/lib/api-server";
import { toProductQuery } from "@/lib/listing-query";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const api = await serverApi();
  const categories = await unwrap(await api.GET("/v1/categories"));
  return { title: categories.find((c) => c.slug === slug)?.name ?? "Department" };
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
  const categories = await unwrap(await api.GET("/v1/categories"));
  const category = categories.find((c) => c.slug === slug);
  if (!category) notFound();
  const page = await unwrap(
    await api.GET("/v1/products", { params: { query: toProductQuery(query, slug) } }),
  );
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
      />
    </>
  );
}
