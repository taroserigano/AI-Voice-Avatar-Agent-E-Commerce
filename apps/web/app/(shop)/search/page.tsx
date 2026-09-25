import { Listing, type ListingParams } from "@/components/shop/listing";
import { WebVitalsReporter } from "@/components/web-vitals";
import { serverApi, unwrap } from "@/lib/api-server";
import { toProductQuery } from "@/lib/listing-query";
import type { Metadata } from "next";

export async function generateMetadata({ searchParams }: { searchParams: Promise<ListingParams> }): Promise<Metadata> {
  const { q } = await searchParams;
  return { title: q ? `Results for “${q}”` : "Search" };
}

export default async function SearchPage({ searchParams }: { searchParams: Promise<ListingParams> }) {
  const params = await searchParams;
  const api = await serverApi();
  const page = await unwrap(await api.GET("/v1/products", { params: { query: toProductQuery(params) } }));
  const q = params.q?.trim();
  return (
    <>
      <WebVitalsReporter route="search" />
      <Listing
        page={page}
        params={params}
        basePath="/search"
        heading={q ? `Results for “${q}”` : "All products"}
        showCategoryFacet
      />
    </>
  );
}
