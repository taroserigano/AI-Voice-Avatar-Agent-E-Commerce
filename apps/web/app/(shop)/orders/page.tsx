import { ButtonLink } from "@/components/ui/button";
import { WebVitalsReporter } from "@/components/web-vitals";
import { serverApi, unwrap } from "@/lib/api-server";
import { formatMoney } from "@/lib/format";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Orders" };

export default async function OrdersPage() {
  const api = await serverApi();
  const orders = await unwrap(await api.GET("/v1/orders"));
  return (
    <div>
      <WebVitalsReporter route="orders" />
      <h1 className="text-2xl font-bold">Orders &amp; returns</h1>
      {orders.length === 0 ? (
        <div className="mt-6 rounded-2xl border border-dashed border-stone-300 bg-white p-10 text-center">
          <p className="text-lg font-semibold">No orders yet.</p>
          <p className="mt-1 text-muted">When you buy something, it shows up here.</p>
          <ButtonLink href="/" variant="secondary" className="mt-4">
            Start shopping
          </ButtonLink>
        </div>
      ) : (
        <ul className="mt-4 divide-y divide-line rounded-2xl border border-line bg-white">
          {orders.map((o) => (
            <li key={o.id} className="flex flex-wrap justify-between gap-2 p-4">
              <div>
                <p className="font-semibold">Order placed {new Date(o.placed_at).toLocaleDateString("en-US")}</p>
                <p className="text-sm text-muted">
                  {o.item_count} {o.item_count === 1 ? "item" : "items"} · {o.status}
                </p>
              </div>
              <p className="font-semibold">{formatMoney(o.total_minor, o.currency)}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
