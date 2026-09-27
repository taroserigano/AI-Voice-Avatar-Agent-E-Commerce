import { ArrowRightIcon, ClockIcon, PackageIcon, ReturnIcon, TruckIcon } from "@/components/icons";
import { OrdersBrowser } from "@/components/orders/orders-browser";
import { ButtonLink } from "@/components/ui/button";
import { WebVitalsReporter } from "@/components/web-vitals";
import { serverApi, unwrap } from "@/lib/api-server";
import { parseOrderRange } from "@/lib/order-search";
import { blockedReturnText, parseOrderFilter } from "@/lib/orders";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Orders" };

type Search = { view?: string | string[]; q?: string | string[]; range?: string | string[] };

export default async function OrdersPage({ searchParams }: { searchParams: Promise<Search> }) {
  const { view, q, range } = await searchParams;
  const api = await serverApi();
  const [orders, returnsResult] = await Promise.all([
    api.GET("/v1/orders").then(unwrap),
    // The Returns tab is optional: if it fails, the orders still show.
    api.GET("/v1/returns"),
  ]);
  const returns = returnsResult.data ?? [];
  const open = orders.filter((o) => o.status === "paid" || o.status === "fulfilling").length;

  // For delivered orders with nothing returnable, ask the server why ("Final sale" for a gift card,
  // "Return window closed"), so the list doesn't just say "No items left to return".
  const unclear = orders.filter((o) => o.status === "delivered" && !o.return_window_ends_at && !o.has_open_return);
  const reasons = await Promise.all(
    unclear.map(async (o) => {
      const r = await api.GET("/v1/orders/{order_id}/return-options", { params: { path: { order_id: o.id } } });
      const text = r.data ? blockedReturnText(r.data.lines) : null;
      return [o.id, text] as const;
    }),
  );
  const blocked = Object.fromEntries(reasons.filter((r): r is readonly [string, string] => r[1] !== null));

  return (
    <div className="pb-24 sm:pb-8 sm:pt-2">
      <WebVitalsReporter route="orders" />
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
        <div>
          <h1 className="font-display text-3xl font-semibold text-ink sm:text-4xl">Orders &amp; returns</h1>
          <p className="mt-2 text-muted">
            {orders.length === 0
              ? "Track deliveries and start returns from here."
              : `${orders.length} ${orders.length === 1 ? "order" : "orders"}, newest first${
                  open > 0 ? ` · ${open} on the way` : ""
                }.`}
          </p>
        </div>
        {orders.length > 0 ? (
          <Link
            href="/activity"
            className="group -mr-2 inline-flex min-h-11 items-center gap-1.5 rounded-full px-2 text-sm font-semibold text-brand-700 transition-colors hover:text-brand-900"
          >
            <ClockIcon className="size-4" />
            Your activity
            <ArrowRightIcon className="size-4 transition-transform duration-200 ease-snappy group-hover:translate-x-0.5" />
          </Link>
        ) : null}
      </div>

      {orders.length === 0 ? (
        <div className="mt-8 flex flex-col items-center rounded-3xl bg-mesh-light px-6 py-16 text-center sm:py-20">
          <span className="grid size-16 place-items-center rounded-2xl bg-raised text-brand-600 shadow-md">
            <PackageIcon className="size-8" />
          </span>
          <p className="mt-6 font-display text-2xl font-semibold text-ink sm:text-3xl">No orders yet.</p>
          <p className="mt-2 max-w-sm text-muted">When you buy something, it shows up here.</p>
          <ButtonLink href="/" size="lg" className="mt-7">
            Start shopping
            <ArrowRightIcon className="size-4.5" />
          </ButtonLink>
          <ul className="mt-10 grid gap-3 text-left text-sm text-muted sm:grid-cols-2 sm:gap-6">
            <li className="flex items-center gap-3">
              <span className="grid size-9 shrink-0 place-items-center rounded-full bg-raised text-brand-600 shadow-xs">
                <TruckIcon className="size-4.5" />
              </span>
              Follow each order from paid to delivered
            </li>
            <li className="flex items-center gap-3">
              <span className="grid size-9 shrink-0 place-items-center rounded-full bg-raised text-brand-600 shadow-xs">
                <ReturnIcon className="size-4.5" />
              </span>
              Start a return within 30 days of delivery
            </li>
          </ul>
        </div>
      ) : (
        <OrdersBrowser
          orders={orders}
          returns={returns}
          blocked={blocked}
          initialFilter={parseOrderFilter(view)}
          initialQuery={(Array.isArray(q) ? q[0] : q)?.slice(0, 80) ?? ""}
          initialRange={parseOrderRange(range)}
          now={new Date().toISOString()}
        />
      )}
    </div>
  );
}
