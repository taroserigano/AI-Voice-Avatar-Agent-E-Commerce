import { WebVitalsReporter } from "@/components/web-vitals";
import { serverApi, unwrap } from "@/lib/api-server";
import { deliveryEstimate } from "@/lib/orders";
import type { ProductSummary } from "@ai-commerce/contracts";
import type { Metadata } from "next";
import { CartView } from "./cart-view";

export const metadata: Metadata = { title: "Cart" };

type Api = Awaited<ReturnType<typeof serverApi>>;

/** Top-rated, in-stock products, optionally in one category. Suggestions are optional: failures return []. */
async function topRated(api: Api, category?: string): Promise<ProductSummary[]> {
  const result = await api.GET("/v1/products", {
    params: { query: { sort: "top_rated", page_size: 12, in_stock: true, ...(category ? { category } : {}) } },
  });
  return result.data?.items ?? [];
}

/** The last item's category, so "You might also need" sits next to what's in the cart. */
async function lastItemCategory(api: Api, productId: string | undefined): Promise<string | undefined> {
  if (!productId) return undefined;
  const result = await api.GET("/v1/products/{product_id}", { params: { path: { product_id: productId } } });
  return result.data?.category.slug;
}

export default async function CartPage() {
  const api = await serverApi();
  const cart = await unwrap(await api.GET("/v1/cart"));
  const category = await lastItemCategory(api, cart.items.at(-1)?.product_id);
  const [related, popular] = await Promise.all([category ? topRated(api, category) : [], topRated(api)]);

  // Related first, topped up with store-wide favourites; never suggest what's already in the cart.
  const inCart = new Set(cart.items.map((i) => i.product_id));
  const seen = new Set<string>();
  const suggestions = [...related, ...popular]
    .filter((p) => !inCart.has(p.id) && !seen.has(p.id) && seen.add(p.id))
    .slice(0, 4);

  return (
    <>
      <WebVitalsReporter route="cart" />
      <CartView
        initialCart={cart}
        suggestions={suggestions}
        popular={popular.slice(0, 4)}
        // Rendered on the server so the dates can't disagree with the client on hydration.
        delivery={deliveryEstimate(new Date()).text}
      />
    </>
  );
}
