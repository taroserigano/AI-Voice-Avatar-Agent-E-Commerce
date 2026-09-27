"use client";

import { FilterTabs } from "@/components/account/filter-tabs";
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
import { dataNumber, dataString } from "@/lib/activity";
import { ACTIVITY_FILTERS, activityFeed, filterCounts, type ActivityFilter } from "@/lib/activity-feed";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import { formatTime, orderNumber } from "@/lib/orders";
import type { ActivityOut } from "@ai-commerce/contracts";
import Link from "next/link";
import { useMemo, useState, type ReactNode } from "react";

type Kind = ActivityOut["type"];

// The icon tile is decorative: every sentence starts with its own verb ("Viewed", "Searched for").
const KIND: Record<Kind, { icon: Icon; tile: string }> = {
  searched: { icon: SearchIcon, tile: "bg-sunken text-ink-soft" },
  viewed_product: { icon: EyeIcon, tile: "bg-brand-50 text-brand-700" },
  added_to_cart: { icon: CartIcon, tile: "bg-brand-50 text-brand-700" },
  placed_order: { icon: BagIcon, tile: "bg-brand-600 text-white" },
  order_delivered: { icon: PackageIcon, tile: "bg-success-50 text-success-700" },
  started_return: { icon: ReturnIcon, tile: "bg-accent-100 text-accent-800" },
  refund_issued: { icon: CreditCardIcon, tile: "bg-success-50 text-success-700" },
  wrote_review: { icon: StarIcon, tile: "bg-accent-100 text-accent-800" },
  contacted_support: { icon: ChatIcon, tile: "bg-info-50 text-info-700" },
  signed_in: { icon: LockIcon, tile: "bg-sunken text-ink-soft" },
};

// Links read as bold names, not a wall of underlines; the underline appears on hover/focus.
const link =
  "font-semibold text-ink decoration-brand-400 underline-offset-4 transition-colors hover:text-brand-700 hover:underline focus-visible:underline";

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

/** Product thumbnail that falls back to a neutral tile if the image is missing or fails to load. */
function Thumb({ src }: { src: string | undefined }) {
  const [failed, setFailed] = useState(false);
  const box = "size-12 shrink-0 rounded-xl ring-1 ring-inset ring-line/60 sm:size-14";
  if (!src || failed) {
    return (
      <span aria-hidden="true" className={cn(box, "grid place-items-center bg-sunken text-subtle")}>
        <PackageIcon className="size-5" />
      </span>
    );
  }
  return (
    // eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations
    <img
      src={src}
      alt=""
      width={640}
      height={640}
      loading="lazy"
      onError={() => setFailed(true)}
      className={cn(box, "bg-sunken object-cover")}
    />
  );
}

const EMPTY: Record<ActivityFilter, string> = {
  all: "Nothing here yet.",
  searches: "No searches yet.",
  viewed: "No viewed products yet.",
  cart: "Nothing added to your cart yet.",
  support: "No returns, refunds, or support requests yet.",
};

/**
 * Activity feed with filter chips. Grouped by day (each day a section with its own heading),
 * with consecutive repeats ("Viewed X" twice) folded into one row. `now` comes from the server
 * so "Today" can't disagree between server and browser.
 */
export function ActivityTimeline({ events, now, className }: { events: ActivityOut[]; now: string; className?: string }) {
  const [filter, setFilter] = useState<ActivityFilter>("all");
  const nowDate = useMemo(() => new Date(now), [now]);
  const groups = useMemo(() => activityFeed(events, filter, nowDate), [events, filter, nowDate]);
  const counts = useMemo(() => filterCounts(events), [events]);
  const total = groups.reduce((n, g) => n + g.items.length, 0);

  return (
    <div className={className}>
      <FilterTabs
        label="Filter activity"
        options={ACTIVITY_FILTERS.map((f) => ({ ...f, count: counts[f.value] }))}
        value={filter}
        onChange={setFilter}
      />
      <p role="status" className="sr-only">
        Showing {total} {total === 1 ? "event" : "events"}
      </p>

      {groups.length === 0 ? (
        <p className="mt-6 rounded-3xl border border-dashed border-line-strong px-6 py-10 text-center text-muted">
          {EMPTY[filter]}
        </p>
      ) : (
        <div className="mt-6 space-y-8">
          {groups.map((group) => {
            const headingId = `day-${group.key}`;
            return (
              <section key={group.key} aria-labelledby={headingId}>
                <h2
                  id={headingId}
                  className="sticky top-44 z-10 -mx-2 inline-flex rounded-full md:top-36 bg-canvas/90 px-2 py-1 font-display text-lg font-semibold text-ink backdrop-blur"
                >
                  {group.label}
                </h2>
                <ol className="mt-2 divide-y divide-line rounded-3xl border border-line bg-raised px-4 shadow-xs sm:px-6">
                  {group.items.map(({ event, count }) => {
                    const kind = KIND[event.type] ?? KIND.signed_in;
                    const IconCmp = kind.icon;
                    return (
                      <li key={event.id} className="flex items-center gap-4 py-3.5">
                        <span
                          aria-hidden="true"
                          className={cn("grid size-10 shrink-0 place-items-center rounded-xl", kind.tile)}
                        >
                          <IconCmp className="size-5" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="break-words text-sm leading-relaxed text-ink-soft sm:text-[0.9375rem]">{describe(event)}</p>
                          <p className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-muted">
                            <time dateTime={event.occurred_at}>{formatTime(event.occurred_at)}</time>
                            {count > 1 ? (
                              <>
                                <span aria-hidden="true">·</span>
                                <span>{count} times</span>
                              </>
                            ) : null}
                            {event.is_sample ? (
                              <>
                                <span aria-hidden="true">·</span>
                                <span>Sample activity</span>
                              </>
                            ) : null}
                          </p>
                        </div>
                        {event.product ? <Thumb src={event.product.image_path} /> : null}
                      </li>
                    );
                  })}
                </ol>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
