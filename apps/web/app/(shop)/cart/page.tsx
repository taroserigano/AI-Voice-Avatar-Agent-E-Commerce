import { WebVitalsReporter } from "@/components/web-vitals";
import { serverApi, unwrap } from "@/lib/api-server";
import type { Metadata } from "next";
import { CartView } from "./cart-view";

export const metadata: Metadata = { title: "Cart" };

export default async function CartPage() {
  const api = await serverApi();
  const cart = await unwrap(await api.GET("/v1/cart"));
  return (
    <>
      <WebVitalsReporter route="cart" />
      <CartView initialCart={cart} />
    </>
  );
}
