"use client";

import {
  ArrowRightIcon,
  CartIcon,
  ChatIcon,
  CheckCircleIcon,
  ChevronDownIcon,
  ClockIcon,
  ExternalLinkIcon,
  MapIcon,
  PackageIcon,
  UserIcon,
} from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import { RatingBadge } from "@/components/ui/stars";
import type {
  ActivityCard,
  CartCard,
  CartSummaryCard,
  Card,
  CitationCard,
  HandoffCard,
  OrderCard,
  ProductCard,
  ReturnOptionsCard,
  ReturnStatusCard,
  SearchCard,
  StoreCard,
  SupportCasesCard,
  XanaCard,
} from "@/lib/assistant-types";
import { formatDate, orderStatusMeta } from "@/lib/orders";
import { AssistantAvatar } from "./assistant-avatar";
import { useCart, useSetCartItem } from "@/lib/cart-query";
import { formatMoney } from "@/lib/format";
import Link from "next/link";
import { useState } from "react";

const cardBox = "rounded-2xl bg-raised p-3 shadow-xs ring-1 ring-inset ring-line";
const smallLink = "inline-flex items-center gap-1 text-sm font-semibold text-brand-700 hover:text-brand-900";

export function ChatCards({ cards, onAsk }: { cards: Card[]; onAsk?: (text: string) => void }) {
  if (!cards.length) return null;
  const products = cards.filter((c): c is ProductCard => c.kind === "product");
  const others = cards.filter((c) => c.kind !== "product");
  return (
    <div className="mt-2 space-y-2">
      {products.length ? (
        <ul aria-label="Products" className="space-y-2">
          {products.map((p) => (
            <li key={p.id}>
              <ProductChatCard card={p} />
            </li>
          ))}
        </ul>
      ) : null}
      {others.map((c, i) => (
        <OtherCard key={`${c.kind}-${i}`} card={c} onAsk={onAsk} />
      ))}
    </div>
  );
}

function OtherCard({ card, onAsk }: { card: Exclude<Card, ProductCard>; onAsk?: (text: string) => void }) {
  switch (card.kind) {
    case "search":
      return <SearchSummaryChatCard card={card} />;
    case "xana":
      return <XanaChatCard card={card} />;
    case "return_options":
      return <ReturnOptionsChatCard card={card} onAsk={onAsk} />;
    case "return_status":
      return <ReturnStatusChatCard card={card} />;
    case "order":
      return <OrderChatCard card={card} />;
    case "store":
      return <StoreChatCard card={card} />;
    case "cart":
      return <CartChatCard card={card} />;
    case "cart_summary":
      return <CartSummaryChatCard card={card} />;
    case "support_cases":
      return <SupportCasesChatCard card={card} />;
    case "activity":
      return <ActivityChatCard card={card} />;
    case "handoff":
      return <HandoffChatCard card={card} />;
  }
}

function ProductChatCard({ card }: { card: ProductCard }) {
  const cart = useCart();
  const setItem = useSetCartItem();
  const [added, setAdded] = useState(false);
  const inCart = cart.data?.items.find((i) => i.variant_id === card.variant_id)?.quantity ?? 0;

  const add = () => {
    if (!card.variant_id) return;
    setItem.mutate({ variantId: card.variant_id, quantity: inCart + 1 }, { onSuccess: () => setAdded(true) });
  };

  return (
    <article className={`${cardBox} flex gap-3`} aria-label={card.title}>
      {/* eslint-disable-next-line @next/next/no-img-element -- local product illustrations */}
      <img src={card.image_path} alt="" width={64} height={64} className="size-16 shrink-0 rounded-xl bg-canvas object-contain" />
      <div className="min-w-0 flex-1">
        <Link href={card.url} className="line-clamp-2 text-sm font-semibold leading-snug text-ink hover:text-brand-700">
          {card.title}
        </Link>
        <p className="flex flex-wrap items-center gap-x-2 text-xs text-muted">
          <span>{card.brand}</span>
          {card.rating_count ? <RatingBadge average={card.rating_average} count={card.rating_count} size="sm" /> : null}
        </p>
        {card.tags.length ? (
          <ul className="mt-1 flex flex-wrap gap-1" aria-label="Labels">
            {card.tags.slice(0, 3).map((t) => (
              <li key={t.value}>
                <Badge tone="success">{t.label}</Badge>
              </li>
            ))}
          </ul>
        ) : null}
        {card.facts[0] ? <p className="mt-1 truncate text-xs text-muted">{card.facts[0]}</p> : null}
        <div className="mt-2 flex items-center justify-between gap-2">
          <p className="font-semibold tabular-nums text-ink">
            {formatMoney(card.price_minor, card.currency)}
            {!card.in_stock ? <span className="ml-2 text-xs font-medium text-danger-700">Out of stock</span> : null}
          </p>
          {card.variant_id && card.in_stock ? (
            <button
              type="button"
              onClick={add}
              disabled={setItem.isPending}
              className="inline-flex h-8 items-center gap-1 rounded-full bg-brand-600 px-3 text-xs font-semibold text-white shadow-xs hover:bg-brand-700 disabled:opacity-60"
              aria-label={`Add ${card.title} to cart`}
            >
              {added ? <CheckCircleIcon className="size-3.5" /> : null}
              {added ? "Added" : "Add"}
            </button>
          ) : null}
        </div>
        {setItem.isError ? <p className="mt-1 text-xs text-danger-700">Couldn&apos;t add it. Please try again.</p> : null}
      </div>
    </article>
  );
}

function SearchSummaryChatCard({ card }: { card: SearchCard }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted">
      <span>
        {card.total === 0
          ? "No exact matches for"
          : `Showing ${card.shown} of ${card.total.toLocaleString("en-US")} for`}
      </span>
      {card.chips.map((c) => (
        <span key={c} className="rounded-full bg-neutral-100 px-2 py-0.5 font-medium text-ink-soft">
          {c}
        </span>
      ))}
      {card.total > card.shown ? (
        <Link href={card.url} className={`${smallLink} ml-auto text-xs`}>
          See all <ArrowRightIcon className="size-3.5" />
        </Link>
      ) : null}
    </div>
  );
}

function XanaChatCard({ card }: { card: XanaCard }) {
  return (
    <article className={`${cardBox} flex gap-3`} aria-label="Returns and refunds with Xena">
      <AssistantAvatar who="xana" size="lg" />
      <div>
        <p className="text-sm font-semibold text-ink">Returns and refunds with Xena</p>
        <p className="mt-0.5 text-sm text-ink-soft">{card.message}</p>
        <Link href={card.url} className={`${smallLink} mt-1.5`}>
          Open Support <ArrowRightIcon className="size-3.5" />
        </Link>
      </div>
    </article>
  );
}

function OrderChatCard({ card }: { card: OrderCard }) {
  const date = formatDate(card.delivered_at ?? card.placed_at);
  const status = orderStatusMeta(card.status as Parameters<typeof orderStatusMeta>[0]);
  return (
    <article className={cardBox} aria-label={`Order ${card.number}`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="flex items-center gap-1.5 text-sm font-semibold text-ink">
            <PackageIcon className="size-4 text-brand-600" />
            Order #{card.number}
          </p>
          <p className="text-xs text-muted">
            {card.delivered_at ? `Delivered ${date}` : `Placed ${date}`} · {card.item_count} item
            {card.item_count === 1 ? "" : "s"} · {formatMoney(card.total_minor, card.currency)}
          </p>
        </div>
        <Badge tone={status.tone}>{status.label}</Badge>
      </div>
      <ul className="mt-2 space-y-1" aria-label="Items">
        {card.lines.slice(0, 3).map((l) => (
          <li key={l.id} className="flex items-center gap-2 text-sm text-ink-soft">
            {/* eslint-disable-next-line @next/next/no-img-element -- local product illustrations */}
            <img src={l.image_path} alt="" width={28} height={28} className="size-7 rounded-lg bg-canvas object-contain" />
            <span className="truncate">
              {l.quantity} × {l.title}
            </span>
          </li>
        ))}
      </ul>
      <Link href={card.url} className={`${smallLink} mt-2`}>
        View order <ArrowRightIcon className="size-3.5" />
      </Link>
    </article>
  );
}

function StoreChatCard({ card }: { card: StoreCard }) {
  return (
    <article className={cardBox} aria-label={card.name}>
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-semibold text-ink">{card.name}</p>
        <Badge tone={card.open_now ? "success" : "neutral"} dot>
          {card.open_now ? "Open now" : "Closed"}
        </Badge>
      </div>
      <p className="mt-0.5 text-xs text-muted">{card.address}</p>
      <p className="mt-1 flex items-center gap-1.5 text-xs text-ink-soft">
        <ClockIcon className="size-3.5" /> Today {card.today_hours}
      </p>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
        <a href={`tel:${card.phone.replace(/[^\d+]/g, "")}`} className={smallLink}>
          {card.phone}
        </a>
        <a href={card.directions_url} target="_blank" rel="noreferrer" className={smallLink}>
          <MapIcon className="size-3.5" /> Directions <span className="sr-only">(opens Google Maps)</span>
        </a>
      </div>
    </article>
  );
}

function CartChatCard({ card }: { card: CartCard }) {
  return (
    <article className={`${cardBox} flex items-center gap-3`} aria-label="Added to cart">
      <CheckCircleIcon className="size-6 shrink-0 text-success-600" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-ink">
          Added {card.quantity} × {card.added_title}
        </p>
        <p className="text-xs text-muted">
          Cart: {card.item_count} items · {formatMoney(card.subtotal_minor, card.currency)}
        </p>
      </div>
      <Link href="/cart" className={smallLink}>
        View cart
      </Link>
    </article>
  );
}

function CartSummaryChatCard({ card }: { card: CartSummaryCard }) {
  const money = (minor: number) => formatMoney(minor, card.currency);
  return (
    <article className={cardBox} aria-label="Your cart">
      <div className="flex items-center justify-between gap-2">
        <p className="flex items-center gap-1.5 text-sm font-semibold text-ink">
          <CartIcon className="size-4 text-brand-600" />
          Your cart · {card.item_count} {card.item_count === 1 ? "item" : "items"}
        </p>
        <p className="text-sm font-semibold tabular-nums text-ink">{money(card.subtotal_minor)}</p>
      </div>
      <ul className="mt-2 space-y-1.5" aria-label="Items">
        {card.lines.map((l) => (
          <li key={l.url + l.variant_name} className="flex items-center gap-2 text-sm text-ink-soft">
            {/* eslint-disable-next-line @next/next/no-img-element -- local product illustrations */}
            <img src={l.image_path} alt="" width={28} height={28} className="size-7 shrink-0 rounded-lg bg-canvas object-contain" />
            <Link href={l.url} className="min-w-0 flex-1 truncate hover:text-brand-700">
              {l.quantity} × {l.title}
              {l.variant_name ? <span className="text-muted"> · {l.variant_name}</span> : null}
            </Link>
            {!l.in_stock ? <span className="text-xs font-medium text-danger-700">Out of stock</span> : null}
            <span className="tabular-nums text-ink">{money(l.line_total_minor)}</span>
          </li>
        ))}
      </ul>
      {card.more_lines ? <p className="mt-1 text-xs text-muted">and {card.more_lines} more</p> : null}
      <p className="mt-2 text-xs text-muted">
        {card.shipping_minor ? `Shipping ${money(card.shipping_minor)}` : "Free shipping"} · Estimated{" "}
        {money(card.estimated_total_minor)} before tax
        {card.free_shipping_remaining_minor ? ` · ${money(card.free_shipping_remaining_minor)} more for free shipping` : ""}
      </p>
      <Link href={card.url} className={`${smallLink} mt-2`}>
        Go to cart <ArrowRightIcon className="size-3.5" />
      </Link>
    </article>
  );
}

const caseTone: Record<string, "brand" | "warning" | "success"> = {
  open: "brand",
  waiting_on_customer: "warning",
  resolved: "success",
};

function SupportCasesChatCard({ card }: { card: SupportCasesCard }) {
  return (
    <article className={cardBox} aria-label="Your support cases">
      <p className="flex items-center gap-1.5 text-sm font-semibold text-ink">
        <ChatIcon className="size-4 text-brand-600" />
        Support cases
        {card.total > card.cases.length ? (
          <span className="font-normal text-muted">
            · {card.cases.length} of {card.total}
          </span>
        ) : null}
      </p>
      <ul className="mt-2 divide-y divide-line" aria-label="Cases">
        {card.cases.map((c) => (
          <li key={c.reference} className="py-2 first:pt-0 last:pb-0">
            <div className="flex items-start justify-between gap-2">
              <p className="min-w-0 text-sm text-ink">
                <span className="font-semibold tabular-nums">{c.reference}</span> · {c.topic}
              </p>
              <Badge tone={caseTone[c.status] ?? "neutral"}>{c.status_label}</Badge>
            </div>
            <p className="mt-0.5 text-xs text-muted">
              Opened {formatDate(c.opened_at)}
              {c.order_number && c.order_url ? (
                <>
                  {" · "}
                  <Link href={c.order_url} className="hover:text-brand-700">
                    Order #{c.order_number}
                  </Link>
                </>
              ) : null}
              {c.status !== "resolved" && c.reply_within ? ` · Reply within ${c.reply_within}` : ""}
            </p>
          </li>
        ))}
      </ul>
      <Link href={card.url} className={`${smallLink} mt-2`}>
        Open Support <ArrowRightIcon className="size-3.5" />
      </Link>
    </article>
  );
}

function ActivityChatCard({ card }: { card: ActivityCard }) {
  return (
    <article className={cardBox} aria-label="Your recent activity">
      <p className="flex items-center gap-1.5 text-sm font-semibold text-ink">
        <ClockIcon className="size-4 text-brand-600" />
        Recent activity
      </p>
      <ol className="mt-2 space-y-2 border-l border-line pl-3" aria-label="Events">
        {card.events.map((e, i) => (
          <li key={`${e.occurred_at}-${i}`} className="relative flex items-center gap-2">
            <span aria-hidden className="absolute -left-4.25 size-2 rounded-full bg-brand-400 ring-2 ring-raised" />
            {e.image_path ? (
              /* eslint-disable-next-line @next/next/no-img-element -- local product illustrations */
              <img src={e.image_path} alt="" width={28} height={28} className="size-7 shrink-0 rounded-lg bg-canvas object-contain" />
            ) : null}
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm text-ink">
                <span className="font-medium">{e.what}</span>
                {e.product_title && e.product_url ? (
                  <>
                    {" · "}
                    <Link href={e.product_url} className="text-ink-soft hover:text-brand-700">
                      {e.product_title}
                    </Link>
                  </>
                ) : null}
                {e.detail ? <span className="text-ink-soft"> · {e.detail}</span> : null}
              </p>
              <p className="text-xs text-muted">
                {formatDate(e.occurred_at)}
                {e.order_number && e.order_url ? (
                  <>
                    {" · "}
                    <Link href={e.order_url} className="hover:text-brand-700">
                      Order #{e.order_number}
                    </Link>
                  </>
                ) : null}
                {e.is_sample ? " · Sample" : ""}
              </p>
            </div>
          </li>
        ))}
      </ol>
      <Link href={card.url} className={`${smallLink} mt-2`}>
        See all activity <ArrowRightIcon className="size-3.5" />
      </Link>
    </article>
  );
}

function HandoffChatCard({ card }: { card: HandoffCard }) {
  return (
    <article className={`${cardBox} flex gap-3`} aria-label="Talk to a person">
      <UserIcon className="size-6 shrink-0 text-brand-600" />
      <div>
        <p className="text-sm font-semibold text-ink">Talk to a person</p>
        <p className="mt-0.5 text-sm text-ink-soft">{card.message}</p>
        <Link href="/support" className={`${smallLink} mt-1.5`}>
          Open Support <ArrowRightIcon className="size-3.5" />
        </Link>
      </div>
    </article>
  );
}

function ReturnOptionsChatCard({ card, onAsk }: { card: ReturnOptionsCard; onAsk?: (text: string) => void }) {
  return (
    <article className={cardBox} aria-label="What can be returned">
      <p className="text-sm font-semibold text-ink">What can be returned</p>
      <ul className="mt-2 divide-y divide-line">
        {card.lines.map((ln) => (
          <li key={ln.order_line_id} className="flex items-center gap-3 py-2">
            {/* eslint-disable-next-line @next/next/no-img-element -- local product illustrations */}
            <img src={ln.image_path} alt="" width={36} height={36} className="size-9 shrink-0 rounded-lg bg-canvas object-contain" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-ink">{ln.title}</p>
              <p className="text-xs text-muted">
                {ln.eligible ? `Up to ${formatMoney(ln.max_refund_minor)} back` : ln.message}
              </p>
            </div>
            {ln.eligible ? (
              onAsk ? (
                <button
                  type="button"
                  onClick={() => onAsk(`Return the ${ln.title}`)}
                  className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-800 ring-1 ring-inset ring-brand-100 hover:bg-brand-100"
                >
                  Return this
                </button>
              ) : (
                <Badge tone="success">Returnable</Badge>
              )
            ) : (
              <Badge tone="neutral">Not returnable</Badge>
            )}
          </li>
        ))}
      </ul>
    </article>
  );
}

const RETURN_STEP: Record<string, string> = {
  requested: "Requested",
  authorized: "Label ready",
  in_transit: "On its way back",
  received: "Received",
  inspected: "Inspected",
  closed: "Complete",
  review: "In review",
  rejected: "Not accepted",
  canceled: "Canceled",
};

function ReturnStatusChatCard({ card }: { card: ReturnStatusCard }) {
  if (card.outcome === "superseded") return null;
  if (card.outcome === "declined" || card.outcome === "expired") {
    return (
      <p className={`${cardBox} text-sm text-ink-soft`}>
        {card.outcome === "declined" ? "Quote not confirmed. Nothing was returned." : "The quote expired. Nothing was returned."}
      </p>
    );
  }
  return (
    <article className={`${cardBox} flex gap-3`} aria-label={`Return ${card.rma_number ?? ""}`}>
      <CheckCircleIcon className={`size-6 shrink-0 ${card.outcome === "confirmed" ? "text-success-600" : "text-brand-600"}`} />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-ink">
          {card.outcome === "confirmed" ? "Return confirmed" : "Return"} {card.rma_number}
        </p>
        <p className="text-xs text-muted">
          {RETURN_STEP[card.status ?? ""] ?? card.status}
          {card.refund_minor ? ` · ${formatMoney(card.refund_minor)}` : ""}
          {card.refund_status ? ` · refund ${card.refund_status.replaceAll("_", " ")}` : ""}
        </p>
        {card.items?.length ? <p className="mt-0.5 truncate text-xs text-muted">{card.items.join(", ")}</p> : null}
        {card.outcome === "confirmed" && card.needs_shipping ? (
          <p className="mt-1 text-xs text-ink-soft">Your prepaid label is on the order page. Any Serigan Mart store takes drop-offs.</p>
        ) : null}
        <Link href="/orders" className={`${smallLink} mt-1`}>
          Orders &amp; returns <ArrowRightIcon className="size-3.5" />
        </Link>
      </div>
    </article>
  );
}

export function Sources({ citations }: { citations: CitationCard[] }) {
  if (!citations.length) return null;
  return (
    <details className="group mt-2 rounded-2xl bg-canvas px-3 py-2 ring-1 ring-inset ring-line [&_summary::-webkit-details-marker]:hidden">
      <summary className="flex cursor-pointer list-none items-center gap-1.5 text-xs font-semibold uppercase tracking-eyebrow text-muted">
        Sources ({citations.length})
        <ChevronDownIcon className="size-3.5 transition-transform group-open:rotate-180" />
      </summary>
      <ol className="mt-1.5 space-y-1.5 pb-1">
        {citations.map((c, i) => (
          <li key={c.cite} className="flex gap-2 text-sm">
            <span className="mt-px inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-brand-100 text-[0.6875rem] font-semibold text-brand-800">
              {i + 1}
            </span>
            {c.url ? (
              <Link href={c.url} className="text-ink-soft hover:text-brand-700" target="_blank">
                {c.doc_title} §{c.number} {c.title}
                <ExternalLinkIcon className="ml-1 inline size-3" />
                <span className="sr-only"> (opens in a new tab)</span>
              </Link>
            ) : (
              <span className="text-ink-soft">
                {c.doc_title} {c.title}
              </span>
            )}
          </li>
        ))}
      </ol>
    </details>
  );
}
