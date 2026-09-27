"use client";

import { FilterTabs } from "@/components/account/filter-tabs";
import { ChatIcon, CloseIcon, ReturnIcon, SearchIcon } from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { inputClasses, selectClasses } from "@/components/ui/field";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import { filterOrders, ORDER_RANGES, type OrderRange } from "@/lib/order-search";
import {
  formatDate,
  orderFilterGroup,
  plural,
  refundDisplay,
  returnReasonLabel,
  returnStatusMeta,
  variantLabel,
  type OrderFilter,
} from "@/lib/orders";
import type { OrderSummary, ReturnOut } from "@ai-commerce/contracts";
import Link from "next/link";
import { useState } from "react";
import { OrderCard } from "./order-card";

const FILTERS: { value: OrderFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "in_progress", label: "In progress" },
  { value: "delivered", label: "Delivered" },
  { value: "returns", label: "Returns" },
];

const EMPTY: Record<OrderFilter, string> = {
  all: "No orders yet.",
  in_progress: "Nothing on the way right now. Everything you've ordered has arrived.",
  delivered: "No delivered orders yet.",
  returns: "No returns yet. Start one from an order's page, or ask Xana on the Support page.",
};

/** Keep a list setting in the URL so it survives a refresh and can be linked to. */
function setParam(name: string, value: string | null) {
  const url = new URL(window.location.href);
  if (value) url.searchParams.set(name, value);
  else url.searchParams.delete(name);
  window.history.replaceState(null, "", url);
}

/**
 * Orders with a search box (order number or item), a date range, and filter chips (All / In
 * progress / Delivered / Returns). `GET /v1/orders` returns the shopper's whole history, so all of
 * it filters in the browser; the Returns chip lists `GET /v1/returns` instead of orders. Each choice
 * is kept in the URL (`?q=kettle&range=3m&view=delivered`).
 */
export function OrdersBrowser({
  orders,
  returns,
  blocked,
  initialFilter,
  initialQuery = "",
  initialRange = "all",
  now,
}: {
  orders: OrderSummary[];
  returns: ReturnOut[];
  /** Order id → why nothing in it is returnable ("Final sale"), from the server's return options. */
  blocked: Record<string, string>;
  initialFilter: OrderFilter;
  initialQuery?: string;
  initialRange?: OrderRange;
  /** The server's clock (ISO), so date ranges match between the server render and the browser. */
  now: string;
}) {
  const [filter, setFilter] = useState<OrderFilter>(initialFilter);
  const [query, setQuery] = useState(initialQuery);
  const [range, setRange] = useState<OrderRange>(initialRange);

  const matching = filterOrders(orders, { query, range, now: new Date(now) });
  const narrowed = query.trim() !== "" || range !== "all";
  const counts: Record<OrderFilter, number> = {
    all: matching.length,
    in_progress: matching.filter((o) => orderFilterGroup(o.status) === "in_progress").length,
    delivered: matching.filter((o) => orderFilterGroup(o.status) === "delivered").length,
    returns: returns.length,
  };
  const shown = filter === "all" ? matching : matching.filter((o) => orderFilterGroup(o.status) === filter);

  function choose(next: OrderFilter) {
    setFilter(next);
    setParam("view", next === "all" ? null : next);
  }

  function search(next: string) {
    setQuery(next);
    setParam("q", next.trim() || null);
  }

  function chooseRange(next: OrderRange) {
    setRange(next);
    setParam("range", next === "all" ? null : next);
  }

  function clear() {
    search("");
    chooseRange("all");
  }

  const q = query.trim();
  const rangeLabel = ORDER_RANGES.find((r) => r.value === range)?.label.toLowerCase() ?? "";
  const narrowing = `${q ? ` matching “${q}”` : ""}${range !== "all" ? ` from ${rangeLabel}` : ""}`;
  const resultText = filter === "returns" ? plural(returns.length, "return") : `${plural(shown.length, "order")}${narrowing}`;
  const filterLabel = filter === "all" ? "" : `${FILTERS.find((f) => f.value === filter)?.label.toLowerCase()} `;

  return (
    <div className="mt-6 sm:mt-8">
      {filter !== "returns" ? (
        <div role="search" aria-label="Search your orders" className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="min-w-0 flex-1">
            <label htmlFor="order-search" className="block text-sm font-semibold text-ink">
              Search orders
            </label>
            <div className="relative mt-1.5">
              <SearchIcon className="pointer-events-none absolute left-3.5 top-1/2 size-4.5 -translate-y-1/2 text-muted" />
              <input
                id="order-search"
                type="search"
                value={query}
                onChange={(e) => search(e.target.value)}
                placeholder="Order number or item, e.g. kettle"
                autoComplete="off"
                enterKeyHint="search"
                className={cn(inputClasses, "pl-10")}
              />
            </div>
          </div>
          <div className="sm:w-52">
            <label htmlFor="order-range" className="block text-sm font-semibold text-ink">
              Placed
            </label>
            <select
              id="order-range"
              value={range}
              onChange={(e) => chooseRange(e.target.value as OrderRange)}
              className={cn(selectClasses, "mt-1.5")}
            >
              {ORDER_RANGES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
          {narrowed ? (
            <Button variant="ghost" onClick={clear} className="self-start sm:self-auto">
              <CloseIcon className="size-4" />
              Clear
              <span className="sr-only"> search and date range</span>
            </Button>
          ) : null}
        </div>
      ) : null}
      <FilterTabs
        label="Filter orders"
        options={FILTERS.map((f) => ({ ...f, count: counts[f.value] }))}
        value={filter}
        onChange={choose}
      />
      <p role="status" className="sr-only">
        Showing {resultText}
      </p>

      {filter === "returns" ? (
        returns.length === 0 ? (
          <EmptyFilter text={EMPTY.returns} />
        ) : (
          <ul aria-label="Your returns" className="mt-5 space-y-3">
            {returns.map((r) => (
              <ReturnSummaryCard key={r.id} ret={r} />
            ))}
          </ul>
        )
      ) : shown.length === 0 ? (
        narrowed ? (
          <div className="mt-5 rounded-3xl border border-dashed border-line-strong px-6 py-10 text-center">
            <p className="text-muted">
              No {filterLabel}orders{narrowing}.
            </p>
            <Button variant="outline" size="sm" onClick={clear} className="mt-4">
              Clear search and dates
            </Button>
          </div>
        ) : (
          <EmptyFilter text={EMPTY[filter]} />
        )
      ) : (
        <ul aria-label="Your orders" className="mt-5 space-y-3">
          {shown.map((o, i) => (
            <OrderCard key={o.id} order={o} index={i} blocked={blocked[o.id]} />
          ))}
        </ul>
      )}
    </div>
  );
}

function EmptyFilter({ text }: { text: string }) {
  return <p className="mt-5 rounded-3xl border border-dashed border-line-strong px-6 py-10 text-center text-muted">{text}</p>;
}

/** A return in the Returns tab: RMA, status, what's coming back, and where the refund stands. */
function ReturnSummaryCard({ ret }: { ret: ReturnOut }) {
  const status = returnStatusMeta(ret.status);
  const currency = ret.refund?.currency ?? "USD";
  const refund = refundDisplay(ret, "your original payment method", (m) => formatMoney(m, currency));
  const headingId = `ret-${ret.id}`;
  return (
    <li>
      <article aria-labelledby={headingId} className="rounded-3xl border border-line bg-raised p-4 shadow-xs sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
          <div className="flex min-w-0 items-start gap-3">
            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-700">
              <ReturnIcon className="size-5" />
            </span>
            <div className="min-w-0">
              <h2 id={headingId} className="font-display text-lg font-semibold text-ink">
                Return <span className="font-mono text-base tracking-wide">{ret.rma_number}</span>
              </h2>
              <p className="text-sm text-muted">
                Started <time dateTime={ret.created_at}>{formatDate(ret.created_at)}</time> · {returnReasonLabel(ret.reason)} ·{" "}
                <Link href={`/orders/${ret.order_id}`} className="font-medium text-brand-700 underline-offset-2 hover:underline">
                  View order<span className="sr-only"> for return {ret.rma_number}</span>
                </Link>
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {ret.is_sample ? <Badge tone="neutral">Sample history</Badge> : null}
            <Badge tone={status.tone} dot size="md">
              <span className="sr-only">Return status: </span>
              {status.label}
            </Badge>
          </div>
        </div>

        <div className="mt-4 flex flex-col gap-4 border-t border-line pt-4 sm:flex-row sm:items-center sm:justify-between">
          <ul aria-label="Items in this return" className="flex min-w-0 flex-col gap-2.5">
            {ret.items.map((item) => {
              const variant = variantLabel(item.variant_name);
              return (
                <li key={`${item.order_line_id}-${item.condition}`} className="flex items-center gap-3">
                  {/* eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations */}
                  <img
                    src={item.image_path}
                    alt=""
                    width={640}
                    height={640}
                    loading="lazy"
                    className="size-11 shrink-0 rounded-lg bg-sunken object-cover ring-1 ring-inset ring-line/60"
                  />
                  <p className="min-w-0 text-sm">
                    <span className="font-semibold text-ink">{item.product_title}</span>
                    <span className="block text-xs text-muted tabular-nums">
                      {variant ? `${variant} · ` : null}Qty {item.quantity} · Refund {formatMoney(item.refund_minor, currency)}
                    </span>
                  </p>
                </li>
              );
            })}
          </ul>
          <div className="shrink-0 sm:max-w-xs sm:text-right">
            <p
              className={cn(
                "text-sm font-semibold",
                refund.tone === "success" ? "text-success-700" : refund.tone === "danger" ? "text-danger-700" : "text-ink",
              )}
            >
              <span className="sr-only">Refund: </span>
              {refund.title}
            </p>
            {refund.detail ? <p className="mt-0.5 text-xs text-muted">{refund.detail}</p> : null}
            <ButtonLink href={`/support?order=${ret.order_id}`} variant="ghost" size="sm" className="mt-2 -mr-2 text-brand-700">
              <ChatIcon className="size-4" />
              Ask Xana about it<span className="sr-only"> (return {ret.rma_number})</span>
            </ButtonLink>
          </div>
        </div>
      </article>
    </li>
  );
}
