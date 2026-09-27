"use client";

import { SuggestedProducts } from "@/components/account/suggested-products";
import { OpenStephButton } from "@/components/assistant/open-steph";
import {
  AlertTriangleIcon,
  ArrowRightIcon,
  BagIcon,
  CheckCircleIcon,
  CheckIcon,
  CloseIcon,
  InfoIcon,
  MinusIcon,
  PlusIcon,
  ReturnIcon,
  SearchIcon,
  TrashIcon,
  TruckIcon,
} from "@/components/icons";
import { Button, ButtonLink } from "@/components/ui/button";
import { Notice } from "@/components/ui/notice";
import { useCart, useRemoveCartItem, useSetCartItem } from "@/lib/cart-query";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import { freeShippingProgress, variantLabel } from "@/lib/orders";
import type { CartOut, ProductSummary } from "@ai-commerce/contracts";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

const stepButton =
  "grid size-11 shrink-0 place-items-center rounded-full text-ink-soft transition-colors duration-150 " +
  "hover:bg-raised hover:text-ink hover:shadow-xs active:bg-neutral-200 " +
  "disabled:pointer-events-none disabled:text-control";

export function CartView({
  initialCart,
  suggestions,
  popular,
  delivery,
}: {
  initialCart: CartOut;
  /** "You might also need": related to the cart, never already in it. */
  suggestions: ProductSummary[];
  /** Store-wide top-rated products, for the empty cart. */
  popular: ProductSummary[];
  /** Estimated delivery window, e.g. "Tue, Sep 29 – Fri, Oct 2". */
  delivery: string;
}) {
  const { data: cart } = useCart(initialCart);
  const setItem = useSetCartItem();
  const removeItem = useRemoveCartItem();
  const [status, setStatus] = useState<{ tone: "success" | "error"; text: string }>();

  // Success toasts tidy themselves away; errors stay until dismissed or replaced.
  useEffect(() => {
    if (status?.tone !== "success") return;
    const timer = window.setTimeout(() => setStatus(undefined), 6000);
    return () => window.clearTimeout(timer);
  }, [status]);

  if (!cart) return null;

  async function changeQuantity(variantId: string, title: string, quantity: number) {
    setStatus(undefined);
    try {
      await setItem.mutateAsync({ variantId, quantity });
      setStatus({ tone: "success", text: `Updated ${title} to ${quantity}.` });
    } catch (e) {
      setStatus({ tone: "error", text: e instanceof Error ? e.message : "Couldn't update the cart." });
    }
  }

  async function remove(itemId: string, title: string) {
    setStatus(undefined);
    try {
      await removeItem.mutateAsync(itemId);
      setStatus({ tone: "success", text: `Removed ${title}.` });
    } catch (e) {
      setStatus({ tone: "error", text: e instanceof Error ? e.message : "Couldn't remove the item." });
    }
  }

  const itemLabel = `${cart.item_count} ${cart.item_count === 1 ? "item" : "items"}`;

  return (
    // Extra bottom room on phones so the floating "Ask Steph" button never covers the last control.
    <div className="pb-24 sm:pb-8 sm:pt-2">
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <h1 className="font-display text-3xl font-semibold text-ink sm:text-4xl">Your cart</h1>
          {cart.items.length > 0 ? <p className="text-base text-muted tabular-nums">{itemLabel}</p> : null}
        </div>
        {cart.items.length > 0 ? (
          <Link
            href="/"
            className="group inline-flex min-h-11 items-center gap-1.5 text-sm font-semibold text-brand-700 hover:text-brand-800"
          >
            Continue shopping
            <ArrowRightIcon className="size-4 transition-transform duration-200 ease-snappy group-hover:translate-x-0.5" />
          </Link>
        ) : null}
      </div>

      {/* Toast-style status: fixed so updating a quantity never shifts the controls you're using.
          On phones it sits above the floating "Ask Steph" button. */}
      <div
        aria-live="polite"
        className="pointer-events-none fixed inset-x-0 bottom-22 z-50 flex justify-center px-4 sm:bottom-6"
      >
        {status ? (
          <Notice
            tone={status.tone}
            className="pointer-events-auto w-full max-w-md animate-fade-up items-center py-2 pr-2 shadow-xl"
            action={
              <button
                type="button"
                onClick={() => setStatus(undefined)}
                className="grid size-11 place-items-center rounded-lg opacity-80 transition hover:bg-black/5 hover:opacity-100"
              >
                <CloseIcon className="size-4" />
                <span className="sr-only">Dismiss message</span>
              </button>
            }
          >
            {status.text}
          </Notice>
        ) : null}
      </div>

      {cart.warnings.length > 0 ? (
        <Notice tone="warning" title="Some items changed" className="mt-6">
          <ul className="list-disc pl-5">
            {cart.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </Notice>
      ) : null}

      {cart.items.length === 0 ? (
        <EmptyCart popular={popular} />
      ) : (
        <>
          <div className="mt-6 grid items-start gap-6 sm:mt-8 lg:grid-cols-[minmax(0,1fr)_24rem] lg:gap-10">
            <ul aria-label="Cart items" className="divide-y divide-line rounded-3xl border border-line bg-raised shadow-xs">
              {cart.items.map((item) => {
                const busy = setItem.isPending || removeItem.isPending;
                const canDecrease = item.quantity > 1 && item.max_quantity > 0;
                const canIncrease = item.quantity < item.max_quantity;
                const variant = variantLabel(item.variant_name);
                return (
                  <li key={item.id} className="flex gap-4 p-4 sm:gap-6 sm:p-6">
                    <Link
                      href={`/products/${item.product_id}`}
                      tabIndex={-1}
                      aria-hidden="true"
                      className="group shrink-0 self-start overflow-hidden rounded-2xl bg-sunken"
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element -- local SVG placeholders */}
                      <img
                        src={item.image_path}
                        alt=""
                        width={128}
                        height={128}
                        className="size-20 object-cover transition-transform duration-500 ease-smooth group-hover:scale-[1.05] motion-reduce:group-hover:scale-100 sm:size-32"
                      />
                    </Link>

                    {/* Phones: remove icon top-right, price beside the stepper. Wider: price top-right, remove beside the stepper. */}
                    <div className="grid min-w-0 flex-1 grid-cols-[minmax(0,1fr)_auto] content-start gap-x-3 [grid-template-areas:'title_remove'_'meta_meta'_'controls_price'] sm:gap-x-4 sm:[grid-template-areas:'title_price'_'meta_meta'_'controls_remove']">
                      <div className="min-w-0 [grid-area:title]">
                        <Link
                          href={`/products/${item.product_id}`}
                          className="line-clamp-2 font-medium leading-snug text-ink transition-colors hover:text-brand-700 sm:text-lg"
                        >
                          {item.product_title}
                        </Link>
                        {variant ? <p className="mt-1 text-sm text-muted">{variant}</p> : null}
                      </div>
                      <p className="self-center justify-self-end text-base font-semibold tabular-nums text-ink [grid-area:price] sm:self-start sm:text-lg">
                        {formatMoney(item.line_total_minor)}
                      </p>

                      <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm [grid-area:meta]">
                        <span className="text-muted tabular-nums">{formatMoney(item.unit_price_minor)} each</span>
                        {item.in_stock ? (
                          <span className="inline-flex items-center gap-1 font-medium text-success-700">
                            <CheckIcon className="size-4" />
                            In stock
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 font-medium text-danger-700">
                            <AlertTriangleIcon className="size-4" />
                            {item.available === 0 ? "Out of stock" : `Only ${item.available} available`}
                          </span>
                        )}
                      </div>

                      <div className="pt-4 [grid-area:controls]">
                        {/* Stepper: − / native select (keeps full keyboard + screen reader support) / + */}
                        <div className="inline-flex items-center rounded-full bg-sunken p-0.5 ring-1 ring-inset ring-line">
                          <button
                            type="button"
                            className={stepButton}
                            disabled={busy || !canDecrease}
                            onClick={() =>
                              changeQuantity(
                                item.variant_id,
                                item.product_title,
                                Math.min(item.quantity - 1, item.max_quantity),
                              )
                            }
                          >
                            <MinusIcon className="size-4" />
                            <span className="sr-only">Decrease {item.product_title}</span>
                          </button>
                          <label className="sr-only" htmlFor={`qty-${item.id}`}>
                            Quantity
                          </label>
                          <select
                            id={`qty-${item.id}`}
                            value={item.quantity}
                            disabled={setItem.isPending || item.max_quantity === 0}
                            onChange={(e) => changeQuantity(item.variant_id, item.product_title, Number(e.target.value))}
                            className="h-11 min-w-12 appearance-none rounded-full bg-transparent px-2 text-center text-base font-semibold tabular-nums text-ink [text-align-last:center] hover:bg-raised focus-visible:bg-raised disabled:cursor-not-allowed disabled:text-muted"
                          >
                            {Array.from({ length: Math.max(item.max_quantity, item.quantity) }, (_, i) => i + 1).map((n) => (
                              <option key={n} value={n} disabled={n > item.max_quantity}>
                                {n}
                              </option>
                            ))}
                          </select>
                          <button
                            type="button"
                            className={stepButton}
                            disabled={busy || !canIncrease}
                            onClick={() => changeQuantity(item.variant_id, item.product_title, item.quantity + 1)}
                          >
                            <PlusIcon className="size-4" />
                            <span className="sr-only">Increase {item.product_title}</span>
                          </button>
                        </div>
                      </div>

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => remove(item.id, item.product_title)}
                        disabled={removeItem.isPending}
                        className="-mr-2 -mt-1.5 self-start justify-self-end text-muted [grid-area:remove] hover:bg-danger-50 hover:text-danger-700 sm:mr-0 sm:mt-4 sm:self-center"
                      >
                        <TrashIcon className="size-4" />
                        <span className="max-sm:sr-only">Remove</span>
                        <span className="sr-only"> {item.product_title}</span>
                      </Button>
                    </div>
                  </li>
                );
              })}
            </ul>

            <OrderSummary cart={cart} itemLabel={itemLabel} delivery={delivery} />
          </div>

          <SuggestedProducts
            id="also-need"
            title="You might also need"
            description="Top-rated picks that go with what's in your cart."
            products={suggestions}
            className="mt-12 sm:mt-16"
          />
        </>
      )}
    </div>
  );
}

function OrderSummary({ cart, itemLabel, delivery }: { cart: CartOut; itemLabel: string; delivery: string }) {
  const progress = freeShippingProgress(cart);
  const freeShipping = cart.shipping_minor === 0;
  // Display-only sum of two server amounts; tax is added at checkout.
  const estimatedTotal = cart.estimated_total_minor;

  return (
    <aside aria-labelledby="summary" className="lg:sticky lg:top-36">
      <div className="rounded-3xl border border-line bg-raised p-6 shadow-md sm:p-7">
        <h2 id="summary" className="font-display text-xl font-semibold text-ink">
          Order summary
        </h2>

        <div className={cn("mt-5 rounded-2xl p-4", freeShipping ? "bg-success-50" : "bg-brand-50")}>
          <p
            className={cn(
              "flex items-center gap-2 text-sm font-semibold",
              freeShipping ? "text-success-900" : "text-brand-900",
            )}
          >
            {freeShipping ? (
              <CheckCircleIcon className="size-5 text-success-600" />
            ) : (
              <TruckIcon className="size-5 text-brand-600" />
            )}
            {freeShipping
              ? "You've got free shipping"
              : `You're ${formatMoney(cart.free_shipping_remaining_minor, cart.currency)} away from free shipping`}
          </p>
          <div aria-hidden="true" className="mt-3 h-2 overflow-hidden rounded-full bg-raised ring-1 ring-inset ring-line">
            <div
              className={cn(
                "h-full rounded-full transition-[width] duration-500 ease-smooth",
                freeShipping ? "bg-success-600" : "bg-brand-600",
              )}
              style={{ width: `${Math.round(progress * 100)}%` }}
            />
          </div>
          <p className={cn("mt-2 text-xs", freeShipping ? "text-success-800" : "text-brand-800")}>
            Free shipping on orders of {formatMoney(cart.free_shipping_threshold_minor, cart.currency)} or more, after
            discounts.
          </p>
        </div>

        <dl className="mt-5 space-y-3 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-ink-soft">Subtotal ({itemLabel})</dt>
            <dd className="font-semibold tabular-nums text-ink">{formatMoney(cart.subtotal_minor, cart.currency)}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-ink-soft">Shipping</dt>
            <dd className={cn("font-semibold tabular-nums", freeShipping ? "text-success-700" : "text-ink")}>
              {freeShipping ? "Free" : formatMoney(cart.shipping_minor, cart.currency)}
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-ink-soft">Tax</dt>
            <dd className="text-muted">Calculated at checkout</dd>
          </div>
        </dl>
        <div className="mt-5 flex items-baseline justify-between gap-4 border-t border-line pt-5">
          <p className="font-semibold text-ink">
            Estimated total <span className="block text-xs font-normal text-muted">before tax</span>
          </p>
          <p className="font-display text-2xl font-semibold tabular-nums text-ink">
            {formatMoney(estimatedTotal, cart.currency)}
          </p>
        </div>

        <CheckoutButton />

        <p className="mt-4 flex items-start gap-2.5 text-sm text-ink-soft">
          <TruckIcon className="mt-px size-4.5 shrink-0 text-brand-600" />
          <span>
            <span className="font-semibold text-ink">Estimated delivery {delivery}</span>
            <span className="block text-muted">Ships within 1 business day, arrives in 2–5 business days.</span>
          </span>
        </p>
      </div>
      <p className="mt-4 flex items-center gap-2.5 px-2 text-sm text-muted">
        <ReturnIcon className="size-4.5 shrink-0 text-brand-600" />
        <span>
          Returns within 30 days of delivery on most items.{" "}
          <Link href="/help/returns" className="font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700">
            How returns work
          </Link>
        </span>
      </p>
    </aside>
  );
}

/** "Check out" is always enabled: it explains, in a dialog, that this demo store doesn't take orders. */
function CheckoutButton() {
  const dialog = useRef<HTMLDialogElement>(null);
  return (
    <>
      <Button size="lg" className="mt-6 w-full" aria-haspopup="dialog" onClick={() => dialog.current?.showModal()}>
        Check out
        <ArrowRightIcon className="size-4.5" />
      </Button>
      <dialog
        ref={dialog}
        aria-labelledby="checkout-title"
        aria-describedby="checkout-body"
        // Clicking the dimmed backdrop (the dialog element itself, outside the panel) closes it.
        onClick={(e) => {
          if (e.target === e.currentTarget) e.currentTarget.close();
        }}
        className="m-auto w-[min(28rem,calc(100%-2rem))] rounded-3xl bg-raised p-0 text-ink shadow-xl backdrop:bg-neutral-950/50 open:animate-scale-in"
      >
        <div className="relative p-6 sm:p-7">
          <button
            type="button"
            onClick={() => dialog.current?.close()}
            className="absolute right-3 top-3 grid size-11 place-items-center rounded-full text-muted transition-colors hover:bg-neutral-100 hover:text-ink"
          >
            <CloseIcon className="size-5" />
            <span className="sr-only">Close</span>
          </button>
          <span className="grid size-12 place-items-center rounded-2xl bg-brand-50 text-brand-700">
            <InfoIcon className="size-6" />
          </span>
          <h2 id="checkout-title" className="mt-4 pr-8 font-display text-2xl font-semibold text-ink">
            Checkout is turned off
          </h2>
          <p id="checkout-body" className="mt-2 text-ink-soft">
            Checkout is turned off in this demo store. Your cart is saved to your account.
          </p>
          <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row">
            {/* Close first so Steph's panel isn't behind the modal. */}
            <div className="sm:flex-1" onClickCapture={() => dialog.current?.close()}>
              <OpenStephButton variant="outline" className="w-full" />
            </div>
            <ButtonLink href="/" className="sm:flex-1">
              Keep shopping
            </ButtonLink>
          </div>
        </div>
      </dialog>
    </>
  );
}

function EmptyCart({ popular }: { popular: ProductSummary[] }) {
  const art = popular.slice(0, 3);
  return (
    <>
      <div className="relative mt-8 flex flex-col items-center overflow-hidden rounded-3xl bg-mesh-light px-6 py-16 text-center sm:py-20">
        <div aria-hidden="true" className="relative h-28 w-56">
          {art.map((p, i) => (
            // eslint-disable-next-line @next/next/no-img-element -- local SVG product art
            <img
              key={p.id}
              src={p.image_path}
              alt=""
              width={640}
              height={640}
              className={cn(
                "absolute top-2 size-20 rounded-2xl bg-raised shadow-lg ring-1 ring-black/5 animate-fade-up",
                i === 0 && "left-2 -rotate-12",
                i === 1 && "left-1/2 top-0 z-10 -translate-x-1/2 animation-delay-80",
                i === 2 && "right-2 rotate-12 animation-delay-160",
              )}
            />
          ))}
          <span className="absolute -bottom-2 left-1/2 z-20 grid size-12 -translate-x-1/2 place-items-center rounded-2xl bg-brand-600 text-white shadow-glow">
            <BagIcon className="size-6" />
          </span>
        </div>
        <p className="mt-8 font-display text-2xl font-semibold text-ink sm:text-3xl">Your cart is empty.</p>
        <p className="mt-2 max-w-sm text-muted">Find something you love. We&apos;ll keep it here for you.</p>
        <div className="mt-7 flex flex-wrap justify-center gap-3">
          <ButtonLink href="/" size="lg">
            Start shopping
            <ArrowRightIcon className="size-4.5" />
          </ButtonLink>
          <ButtonLink href="/search" variant="outline" size="lg">
            <SearchIcon className="size-4.5" />
            Search products
          </ButtonLink>
        </div>
      </div>
      <SuggestedProducts
        id="popular"
        title="Shopper favorites"
        description="Our top-rated products right now."
        products={popular}
        className="mt-12"
      />
    </>
  );
}
