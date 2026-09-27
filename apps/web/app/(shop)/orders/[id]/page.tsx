import { ChevronRightIcon } from "@/components/icons";
import { DeliveryCard } from "@/components/orders/delivery-card";
import { OrderHelpCard } from "@/components/orders/order-help";
import { OrderItems } from "@/components/orders/order-items";
import { OrderStatusBadge } from "@/components/orders/order-status-badge";
import { PaymentSummary, ReturnPolicyCard } from "@/components/orders/payment-summary";
import { PrinterIcon } from "@/components/orders/order-icons";
import { ReturnsList } from "@/components/orders/returns-list";
import { ShippingAddressCard } from "@/components/orders/shipping-address";
import { buttonClasses } from "@/components/ui/button";
import { WebVitalsReporter } from "@/components/web-vitals";
import { redirectToSignIn, serverApi } from "@/lib/api-server";
import { formatMoney } from "@/lib/format";
import { cardLabel, formatDate, orderNumber, plural, primaryShipment } from "@/lib/orders";
import type { LineReturnOption, ReturnOptions } from "@ai-commerce/contracts";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { loadOrder, UUID_RE } from "./load-order";

/** Return eligibility is optional for rendering: if it fails, the order still shows. */
async function loadReturnOptions(id: string): Promise<ReturnOptions | null> {
  if (!UUID_RE.test(id)) return null;
  const api = await serverApi();
  const result = await api.GET("/v1/orders/{order_id}/return-options", { params: { path: { order_id: id } } });
  if (result.response.status === 401) return redirectToSignIn();
  if (result.response.status === 404) notFound();
  return result.data ?? null;
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const order = await loadOrder((await params).id);
  return { title: `Order #${orderNumber(order.id)}` };
}

export default async function OrderPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [order, options] = await Promise.all([loadOrder(id), loadReturnOptions(id)]);
  const number = orderNumber(order.id);
  const shipment = primaryShipment(order.shipments);
  const destination = cardLabel(options?.refund_destination ?? order.payment);
  const optionsByLine = new Map<string, LineReturnOption>(options?.lines.map((l) => [l.order_line_id, l]) ?? []);

  return (
    <div className="pb-24 pt-2 sm:pb-8 sm:pt-4">
      <WebVitalsReporter route="order" />

      <nav aria-label="Breadcrumb">
        <ol className="flex items-center gap-x-1.5 text-sm text-muted">
          <li className="flex shrink-0 items-center gap-1.5">
            <Link
              href="/orders"
              className="inline-flex min-h-11 items-center rounded-md hover:text-ink hover:underline hover:underline-offset-4 sm:min-h-8"
            >
              Orders
            </Link>
            <ChevronRightIcon className="size-3.5 text-subtle" />
          </li>
          <li aria-current="page" className="min-w-0 truncate font-medium text-ink">
            Order #{number}
          </li>
        </ol>
      </nav>

      <header className="mt-3 flex flex-wrap items-end justify-between gap-x-8 gap-y-4 sm:mt-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
            <h1 className="font-display text-3xl font-semibold tracking-tight text-ink sm:text-4xl">Order #{number}</h1>
            <OrderStatusBadge status={order.status} />
          </div>
          <p className="mt-2 text-muted">
            Placed <time dateTime={order.placed_at}>{formatDate(order.placed_at)}</time> · {plural(order.item_count, "item")}
            <span className="sm:hidden">
              {" · "}
              <span className="font-semibold tabular-nums text-ink">{formatMoney(order.total_minor, order.currency)}</span>
            </span>
          </p>
        </div>
        <div className="flex flex-col items-start gap-2 sm:items-end">
          <div className="hidden text-right sm:block">
            <p className="text-xs font-semibold uppercase tracking-eyebrow text-muted">Order total</p>
            <p className="mt-0.5 font-display text-3xl font-semibold tabular-nums text-ink">
              {formatMoney(order.total_minor, order.currency)}
            </p>
          </div>
          <Link href={`/orders/${order.id}/receipt`} className={buttonClasses("outline", "sm")}>
            <PrinterIcon className="size-4" />
            Receipt
            <span className="sr-only"> for order #{number} (printable)</span>
          </Link>
        </div>
      </header>

      <div className="mt-8 grid gap-8 lg:mt-10 lg:grid-cols-12 lg:gap-10">
        <div className="space-y-10 lg:col-span-8 sm:space-y-12">
          <DeliveryCard order={order} shipment={shipment} />
          <OrderItems order={order} options={options} />
          {order.returns.length > 0 ? (
            <ReturnsList returns={order.returns} destination={destination} currency={order.currency} options={optionsByLine} />
          ) : null}
        </div>
        <div className="lg:col-span-4">
          <div className="space-y-4">
            <PaymentSummary order={order} />
            <ShippingAddressCard address={order.shipping_address} />
            <OrderHelpCard orderId={order.id} orderNumber={number} />
            <ReturnPolicyCard />
          </div>
        </div>
      </div>
    </div>
  );
}
