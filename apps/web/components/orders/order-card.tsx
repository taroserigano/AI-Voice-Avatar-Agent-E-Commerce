import { ArrowRightIcon, CheckCircleIcon, CloseIcon, PackageIcon, ReturnIcon, TruckIcon } from "@/components/icons";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import { formatDate, orderListDelivery, orderListReturnHint, orderNumber, plural } from "@/lib/orders";
import type { OrderSummary } from "@ai-commerce/contracts";
import Link from "next/link";
import { BuyAgainButton } from "./buy-again-button";
import { OrderStatusBadge } from "./order-status-badge";

const deliveryIcon: Record<OrderSummary["status"], typeof TruckIcon> = {
  paid: PackageIcon,
  fulfilling: TruckIcon,
  delivered: CheckCircleIcon,
  canceled: CloseIcon,
};

const deliveryTone: Record<OrderSummary["status"], string> = {
  paid: "text-brand-700",
  fulfilling: "text-brand-700",
  delivered: "text-success-700",
  canceled: "text-muted",
};

/**
 * One order in the list. The whole card is one link (the "View order" label stretches over it);
 * delivered orders also get a "Buy again" button, which sits above the link.
 */
export function OrderCard({ order, index, blocked }: { order: OrderSummary; index: number; blocked?: string }) {
  const number = orderNumber(order.id);
  const titleId = `order-${order.id}-title`;
  const DeliveryIcon = deliveryIcon[order.status] ?? PackageIcon;
  const images = order.preview_images.slice(0, 4);
  const returnHint = orderListReturnHint(order, blocked);

  return (
    <li
      className={cn(
        "group relative rounded-3xl border border-line bg-raised shadow-xs transition-[box-shadow,transform,border-color] duration-300 ease-smooth",
        "hover:-translate-y-0.5 hover:border-line-strong hover:shadow-lg motion-reduce:hover:translate-y-0",
        "has-[a:focus-visible]:outline-2 has-[a:focus-visible]:outline-offset-2 has-[a:focus-visible]:outline-focus",
        index < 8 && "animate-fade-up",
      )}
      style={index < 8 ? { animationDelay: `${index * 60}ms` } : undefined}
    >
      <div className="grid grid-cols-[auto_minmax(0,1fr)] items-start gap-4 p-4 sm:flex sm:items-center sm:gap-5 sm:px-5 sm:py-4">
        {/* Preview strip: overlapping tiles, decorative (the items are on the order page) */}
        <div aria-hidden="true" className="relative flex shrink-0 sm:w-32 sm:-space-x-8">
          {images.slice(0, 3).map((src, i) => (
            // eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations
            <img
              key={`${src}-${i}`}
              src={src}
              alt=""
              width={640}
              height={640}
              loading={index < 3 ? "eager" : "lazy"}
              className={cn(
                "size-16 shrink-0 rounded-2xl bg-sunken object-cover ring-3 ring-raised transition-transform duration-300 ease-smooth",
                i > 0 && "max-sm:hidden",
                i === 1 && "group-hover:translate-x-1.5 motion-reduce:group-hover:translate-x-0",
                i === 2 && "group-hover:translate-x-3 motion-reduce:group-hover:translate-x-0",
              )}
              style={{ zIndex: 10 - i }}
            />
          ))}
          {images.length > 3 ? (
            <span className="absolute bottom-1 left-26 z-20 rounded-full max-sm:hidden bg-ink px-1.5 py-px text-[0.6875rem] font-semibold text-white shadow-sm">
              +{images.length - 3}
            </span>
          ) : null}
          {images.length > 1 ? (
            <span className="absolute -bottom-1 -right-1 z-20 rounded-full bg-ink px-1.5 py-px text-[0.6875rem] font-semibold text-white shadow-sm sm:hidden">
              +{images.length - 1}
            </span>
          ) : null}
          {images.length === 0 ? (
            <span className="grid size-16 place-items-center rounded-2xl bg-sunken text-muted">
              <PackageIcon className="size-7" />
            </span>
          ) : null}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
            <h2 id={titleId} className="font-display text-lg font-semibold text-ink">
              Order #{number}
            </h2>
            <OrderStatusBadge status={order.status} size="sm" />
          </div>
          <p className="mt-1 text-sm text-muted">
            Placed <time dateTime={order.placed_at}>{formatDate(order.placed_at)}</time> · {plural(order.item_count, "item")}
          </p>
          <p className={cn("mt-2 flex flex-wrap items-center gap-x-1.5 gap-y-1 text-sm font-medium", deliveryTone[order.status])}>
            <DeliveryIcon className="size-4" />
            {orderListDelivery(order)}
            {returnHint ? (
              <span
                className={cn(
                  "flex items-center gap-1.5 font-normal max-sm:w-full",
                  returnHint.kind === "none" ? "text-muted" : "text-ink",
                )}
              >
                <span aria-hidden="true" className="text-line-strong max-sm:hidden">
                  ·
                </span>
                <ReturnIcon className={cn("size-4", returnHint.kind === "returning" ? "text-brand-700" : "text-muted")} />
                {returnHint.text}
              </span>
            ) : order.status === "fulfilling" ? (
              <span className="flex items-center gap-1.5 font-normal text-muted max-sm:w-full">
                <span aria-hidden="true" className="text-line-strong max-sm:hidden">
                  ·
                </span>
                Track it on the order page
              </span>
            ) : null}
          </p>
        </div>

        <div className="col-span-2 flex flex-wrap items-start justify-between gap-x-4 gap-y-2 border-t border-line pt-3 sm:flex-col sm:flex-nowrap sm:items-end sm:justify-center sm:gap-1 sm:border-0 sm:pt-0">
          <p className="min-h-11 content-center text-lg font-semibold tabular-nums text-ink sm:min-h-0 sm:text-xl">
            <span className="sr-only">Total </span>
            {formatMoney(order.total_minor, order.currency)}
          </p>
          <div className="flex flex-wrap items-start justify-end gap-x-3 gap-y-1 sm:flex-col sm:items-end sm:gap-1">
            {order.status === "delivered" ? <BuyAgainButton orderId={order.id} orderNumber={number} /> : null}
            <Link
              href={`/orders/${order.id}`}
              className="inline-flex min-h-11 items-center gap-1.5 rounded-full text-sm font-semibold text-brand-700 outline-none after:absolute after:inset-0 after:rounded-3xl after:content-[''] group-hover:text-brand-900"
            >
              View order<span className="sr-only"> #{number}</span>
              <ArrowRightIcon className="size-4 transition-transform duration-200 ease-snappy group-hover:translate-x-0.5" />
            </Link>
          </div>
        </div>
      </div>
    </li>
  );
}
