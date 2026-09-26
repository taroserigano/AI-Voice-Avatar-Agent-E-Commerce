import {
  BagIcon,
  CartIcon,
  ChatIcon,
  CreditCardIcon,
  EyeIcon,
  LockIcon,
  PackageIcon,
  ReturnIcon,
  SearchIcon,
  StarIcon,
  type Icon,
} from "@/components/icons";
import { dataNumber, dataString, groupByDay } from "@/lib/activity";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import { formatTime, orderNumber } from "@/lib/orders";
import type { ActivityOut } from "@ai-commerce/contracts";
import Link from "next/link";
import type { ReactNode } from "react";

type Kind = ActivityOut["type"];

const KIND: Record<Kind, { icon: Icon; tile: string; label: string }> = {
  searched: { icon: SearchIcon, tile: "bg-sunken text-ink-soft", label: "Search" },
  viewed_product: { icon: EyeIcon, tile: "bg-brand-50 text-brand-700", label: "Viewed" },
  added_to_cart: { icon: CartIcon, tile: "bg-brand-50 text-brand-700", label: "Cart" },
  placed_order: { icon: BagIcon, tile: "bg-brand-600 text-white", label: "Order" },
  order_delivered: { icon: PackageIcon, tile: "bg-success-50 text-success-700", label: "Delivered" },
  started_return: { icon: ReturnIcon, tile: "bg-accent-100 text-accent-800", label: "Return" },
  refund_issued: { icon: CreditCardIcon, tile: "bg-success-50 text-success-700", label: "Refund" },
  wrote_review: { icon: StarIcon, tile: "bg-accent-100 text-accent-800", label: "Review" },
  contacted_support: { icon: ChatIcon, tile: "bg-info-50 text-info-700", label: "Support" },
  signed_in: { icon: LockIcon, tile: "bg-sunken text-ink-soft", label: "Account" },
};

const link = "font-semibold text-ink underline decoration-line-strong underline-offset-4 transition-colors hover:text-brand-700 hover:decoration-brand-400";

function OrderLink({ id, start = false }: { id: string; start?: boolean }) {
  return (
    <Link href={`/orders/${id}`} className={link}>
      {start ? "Order" : "order"} #{orderNumber(id)}
    </Link>
  );
}

function ProductLink({ event }: { event: ActivityOut }) {
  if (!event.product) return <span className="font-semibold text-ink">a product</span>;
  return (
    <Link href={`/products/${event.product.id}`} className={link}>
      {event.product.title}
    </Link>
  );
}

/** One sentence per event. Amounts come from the event's own data (server-written). */
function describe(event: ActivityOut, currency = "USD"): ReactNode {
  const money = (key: string) => {
    const v = dataNumber(event, key);
    return v == null ? null : formatMoney(v, currency);
  };
  const rma = dataString(event, "rma_number");
  switch (event.type) {
    case "searched": {
      const q = dataString(event, "query");
      return q ? (
        <>
          Searched for{" "}
          <Link href={`/search?q=${encodeURIComponent(q)}`} className={link}>
            “{q}”
          </Link>
        </>
      ) : (
        "Searched the store"
      );
    }
    case "viewed_product":
      return (
        <>
          Viewed <ProductLink event={event} />
        </>
      );
    case "added_to_cart": {
      const qty = dataNumber(event, "quantity");
      return (
        <>
          Added {qty && qty > 1 ? `${qty} × ` : null}
          <ProductLink event={event} /> to your cart
        </>
      );
    }
    case "placed_order":
      return (
        <>
          Placed {event.order_id ? <OrderLink id={event.order_id} /> : "an order"}
          {money("total_minor") ? <span className="text-muted"> · {money("total_minor")}</span> : null}
        </>
      );
    case "order_delivered":
      return event.order_id ? (
        <>
          <OrderLink id={event.order_id} start /> was delivered
        </>
      ) : (
        "An order was delivered"
      );
    case "started_return":
      return (
        <>
          Started a return{rma ? ` (${rma})` : null}
          {event.order_id ? (
            <>
              {" "}
              for <OrderLink id={event.order_id} />
            </>
          ) : null}
        </>
      );
    case "refund_issued":
      return (
        <>
          {money("refund_minor") ? `Refund of ${money("refund_minor")} issued` : "Refund issued"}
          {event.order_id ? (
            <>
              {" "}
              for <OrderLink id={event.order_id} />
            </>
          ) : null}
        </>
      );
    case "wrote_review":
      return (
        <>
          Reviewed <ProductLink event={event} />
        </>
      );
    case "contacted_support": {
      const ref = dataString(event, "reference");
      return (
        <>
          Contacted support
          {event.order_id ? (
            <>
              {" "}
              about <OrderLink id={event.order_id} />
            </>
          ) : null}
          {ref ? <span className="text-muted"> · ref {ref}</span> : null}
        </>
      );
    }
    case "signed_in":
      return "Signed in";
    default:
      return "Activity";
  }
}

/** Day-grouped activity feed; each day is a section, each event an ordered-list item. */
export function ActivityTimeline({ events, now }: { events: ActivityOut[]; now: Date }) {
  const groups = groupByDay(events, now);
  return (
    <div className="space-y-10">
      {groups.map((group) => {
        const headingId = `day-${group.key}`;
        return (
          <section key={group.key} aria-labelledby={headingId}>
            <h2
              id={headingId}
              className="sticky top-16 z-10 -mx-2 inline-flex rounded-full bg-canvas/90 px-2 py-1 font-display text-lg font-semibold text-ink backdrop-blur lg:top-28"
            >
              {group.label}
            </h2>
            <ol className="mt-3 rounded-3xl border border-line bg-raised px-4 shadow-xs sm:px-6">
              {group.events.map((event, i) => {
                const kind = KIND[event.type] ?? KIND.signed_in;
                const IconCmp = kind.icon;
                const last = i === group.events.length - 1;
                return (
                  <li key={event.id} className="relative flex gap-4 py-4">
                    {!last ? (
                      <span aria-hidden="true" className="absolute -bottom-3 left-5 top-15 w-px -translate-x-1/2 bg-line" />
                    ) : null}
                    <span className={cn("relative grid size-10 shrink-0 place-items-center rounded-xl", kind.tile)}>
                      <IconCmp className="size-5" />
                      <span className="sr-only">{kind.label}: </span>
                    </span>
                    <div className="flex min-w-0 flex-1 items-center gap-4">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm leading-relaxed text-ink-soft sm:text-[0.9375rem]">{describe(event)}</p>
                        <p className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-muted">
                          <time dateTime={event.occurred_at}>{formatTime(event.occurred_at)}</time>
                          {event.is_sample ? (
                            <>
                              <span aria-hidden="true">·</span>
                              <span>Sample activity</span>
                            </>
                          ) : null}
                        </p>
                      </div>
                      {event.product ? (
                        // eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations
                        <img
                          src={event.product.image_path}
                          alt=""
                          width={640}
                          height={640}
                          loading="lazy"
                          className="size-12 shrink-0 rounded-xl bg-sunken object-cover ring-1 ring-inset ring-line/60 sm:size-14"
                        />
                      ) : null}
                    </div>
                  </li>
                );
              })}
            </ol>
          </section>
        );
      })}
    </div>
  );
}
