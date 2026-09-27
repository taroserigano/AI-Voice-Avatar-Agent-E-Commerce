"use client";

import { CartIcon, CheckIcon } from "@/components/icons";
import { PillSelect } from "@/components/reviews/pill-select";
import { Button, ButtonLink } from "@/components/ui/button";
import { Notice } from "@/components/ui/notice";
import { CART_KEY, useSetCartItem } from "@/lib/cart-query";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import { meaningfulSize, optionsToChoose } from "@/lib/product-display";
import type { CartOut, ProductDetail } from "@ai-commerce/contracts";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, type ReactNode } from "react";

type Variant = ProductDetail["variants"][number];

/** Attributes shown first, as swatches. */
const COLOR_KEYS = ["color", "colour", "shade"];

/** Swatch fills for the colour names the catalog uses; unknown names get no swatch. */
const SWATCHES: Record<string, string> = {
  black: "#1f1f24",
  white: "#f7f7f5",
  ivory: "#f4efe1",
  cream: "#efe6cf",
  navy: "#1f2a44",
  midnight: "#1c2340",
  blue: "#2f5fb3",
  sky: "#8fb8e0",
  sand: "#d8c7a8",
  oat: "#d9cdb4",
  beige: "#d9c8a9",
  tan: "#c3a27a",
  brown: "#6b4a33",
  olive: "#6b6b3a",
  green: "#2f7a4a",
  sage: "#a3b18a",
  slate: "#5b6770",
  charcoal: "#3a3d42",
  grey: "#9a9aa0",
  gray: "#9a9aa0",
  "heather grey": "#a3a3a8",
  silver: "#c0c3c8",
  red: "#c0392b",
  pink: "#e8a1b5",
  blush: "#e9b8b0",
  purple: "#6d4aa8",
  lavender: "#b9a7d9",
  yellow: "#f2c94c",
  orange: "#e67e22",
  coral: "#f08070",
  teal: "#2a8c8c",
};

function titleCase(key: string) {
  return key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, " ");
}

/**
 * The attributes a shopper chooses between: string-valued keys that differ between variants.
 * Numeric helpers such as `net_oz` (used for unit prices) aren't options. Colour comes first.
 */
export function optionKeys(variants: Variant[]): string[] {
  const keys: string[] = [];
  for (const v of variants) {
    for (const [k, value] of Object.entries(v.attributes)) {
      if (typeof value === "string" && !keys.includes(k)) keys.push(k);
    }
  }
  return keys.sort((a, b) => Number(COLOR_KEYS.includes(b)) - Number(COLOR_KEYS.includes(a)));
}

function attr(v: Variant, key: string): string {
  const value = v.attributes[key];
  return typeof value === "string" ? value : "";
}

/** Distinct values of `key`, in catalog order. */
function valuesOf(variants: Variant[], key: string): string[] {
  return [...new Set(variants.map((v) => attr(v, key)).filter(Boolean))];
}

/**
 * The variant to switch to when the shopper picks `value` for `key`: the one that keeps every
 * other choice, else the in-stock one that keeps the most, else any with that value. Options
 * the shopper hasn't picked yet (`open`) only break ties: they have no choice to keep.
 */
function pick(
  variants: Variant[],
  keys: string[],
  current: Variant,
  key: string,
  value: string,
  open: ReadonlySet<string> = new Set(),
): Variant | undefined {
  const candidates = variants.filter((v) => attr(v, key) === value);
  const others = keys.filter((k) => k !== key);
  const kept = (v: Variant) =>
    others.reduce((n, k) => n + (attr(v, k) === attr(current, k) ? (open.has(k) ? 1 : 100) : 0), 0);
  const exact = candidates.find((v) => others.every((k) => attr(v, k) === attr(current, k)));
  if (exact?.in_stock) return exact;
  const inStock = candidates.filter((v) => v.in_stock).sort((a, b) => kept(b) - kept(a));
  return inStock[0] ?? exact ?? candidates[0];
}

/** The picker key for products whose options are listed by variant name (one attribute or none). */
const VARIANT = "variant";

function Swatch({ name }: { name: string }) {
  const fill = SWATCHES[name.trim().toLowerCase()];
  if (!fill) return null;
  return (
    <span
      aria-hidden="true"
      className="size-4.5 shrink-0 rounded-full shadow-inner ring-1 ring-inset ring-black/15"
      style={{ backgroundColor: fill }}
    />
  );
}

function StockStatus({ inStock, available }: { inStock: boolean; available: number }) {
  const low = inStock && available <= 5;
  return (
    <p
      className={cn(
        "inline-flex items-center gap-2 text-sm font-semibold",
        !inStock ? "text-danger-700" : low ? "text-warning-700" : "text-success-700",
      )}
    >
      <span className="relative flex size-2.5" aria-hidden="true">
        {inStock && !low ? (
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-success-600 opacity-40 motion-reduce:hidden" />
        ) : null}
        <span
          className={cn(
            "relative inline-flex size-2.5 rounded-full",
            !inStock ? "bg-danger-600" : low ? "bg-warning-600" : "bg-success-600",
          )}
        />
      </span>
      {inStock ? (low ? `Only ${available} left in stock` : "In stock") : "Out of stock"}
    </p>
  );
}

const chipClasses = (inStock: boolean) =>
  cn(
    "group relative flex min-h-11 cursor-pointer select-none items-center gap-2 rounded-full bg-raised px-4 text-sm font-medium text-ink",
    "ring-1 ring-inset transition-[box-shadow,background-color,color] duration-150 ease-snappy",
    "has-checked:bg-brand-50 has-checked:text-brand-900 has-checked:ring-2 has-checked:ring-brand-600",
    "has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-focus",
    "has-disabled:cursor-not-allowed has-disabled:opacity-60",
    inStock
      ? "ring-line-strong hover:ring-neutral-500"
      : "text-muted ring-line-strong [background-image:repeating-linear-gradient(135deg,transparent_0_6px,var(--color-neutral-100)_6px_7px)]",
  );

function OptionChip({
  name,
  value,
  checked,
  inStock,
  disabled = false,
  swatch = false,
  note,
  onSelect,
}: {
  name: string;
  value: string;
  checked: boolean;
  inStock: boolean;
  disabled?: boolean;
  swatch?: boolean;
  /** Why it's struck through, for screen readers and as small visible text. */
  note?: string;
  onSelect: () => void;
}) {
  return (
    <label className={chipClasses(inStock)}>
      <input
        type="radio"
        name={name}
        value={value}
        checked={checked}
        disabled={disabled}
        onChange={onSelect}
        className="sr-only"
      />
      <CheckIcon className="hidden size-4 text-brand-700 group-has-checked:block" />
      {swatch ? <Swatch name={value} /> : null}
      <span className={inStock ? undefined : "line-through decoration-neutral-400"}>{value}</span>
      {note ? <span className="text-xs">({note})</span> : null}
    </label>
  );
}

/**
 * Price, stock, option pickers, quantity, and Add to cart. `trust` renders under the result
 * message (server-rendered delivery and policy copy). On phones a bar with the price and
 * Add to cart sticks to the bottom once the main button has scrolled away.
 *
 * Products sold in sizes or colors (the cards' "Choose options") start with those options
 * unselected: the price reads "From $X" until the choice settles it, and Add to cart points the
 * shopper at the picker instead of adding a size they never chose. Packs and containers start on
 * the default option, as quick add does.
 */
export function AddToCart({ product, trust }: { product: ProductDetail; trust?: ReactNode }) {
  const firstInStock = product.variants.find((v) => v.in_stock) ?? product.variants[0];
  const keys = optionKeys(product.variants);
  // One picker per attribute when options combine two or more (color and size); otherwise one
  // picker over the variants by name.
  const perAttribute = product.variants.length > 1 && keys.length > 1;
  const [variantId, setVariantId] = useState(firstInStock?.id ?? "");
  // The pickers the shopper hasn't used yet: nothing is checked in them.
  const [open, setOpen] = useState<ReadonlySet<string>>(
    () =>
      new Set(
        optionsToChoose(
          product,
          perAttribute
            ? keys.map((k) => [k, valuesOf(product.variants, k)])
            : [[VARIANT, product.variants.map((v) => v.name)]],
        ),
      ),
  );
  const [prompted, setPrompted] = useState(false);
  const [quantity, setQuantity] = useState(1);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string }>();
  const [barVisible, setBarVisible] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const buyRowRef = useRef<HTMLDivElement>(null);
  const setItem = useSetCartItem();
  const client = useQueryClient();

  // Show the phone bar only after the real button has scrolled up out of view. The observed area
  // runs from the top of the viewport all the way down, so the change fires when the row crosses
  // the top edge even if it started below the fold and a fast scroll skipped straight past it.
  useEffect(() => {
    const el = buyRowRef.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry) setBarVisible(!entry.isIntersecting && entry.boundingClientRect.top < 0);
      },
      { rootMargin: "0px 0px 100000px 0px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const variant = product.variants.find((v) => v.id === variantId) ?? firstInStock;
  if (!variant) return null;
  const prices = new Set(product.variants.map((v) => v.price_minor));
  // The one option a single-option product comes in ("Size: 1 gallon", "Color: Navy"), but not
  // a placeholder name like "Standard" or "Each" (the cards hide those the same way).
  const singleValue = keys[0] ? attr(variant, keys[0]) : variant.name;
  const singleOption = meaningfulSize(singleValue)
    ? { label: keys[0] ? titleCase(keys[0]) : "Size", value: singleValue }
    : null;

  // Until every option is picked, the price and stock describe all the variants still possible.
  const choosing = open.size > 0;
  const possible = !choosing
    ? [variant]
    : perAttribute
      ? product.variants.filter((v) => keys.every((k) => open.has(k) || attr(v, k) === attr(variant, k)))
      : product.variants;
  const inStock = possible.some((v) => v.in_stock);
  const available = Math.max(0, ...possible.filter((v) => v.in_stock).map((v) => v.available));
  const maxQty = Math.max(1, Math.min(10, available));
  const lowest = Math.min(...possible.map((v) => v.price_minor));
  const onePrice = possible.every((v) => v.price_minor === lowest);
  const unitPrice = possible.every((v) => v.unit_price === variant.unit_price) ? variant.unit_price : null;
  const price = formatMoney(onePrice ? variant.price_minor : lowest, variant.currency);

  /** "Select a size", "Select a color": what the picker for `key` asks for. */
  const selectText = (key: string) => {
    const noun = (key === VARIANT ? (keys[0] ? titleCase(keys[0]) : "option") : titleCase(key)).toLowerCase();
    return `Select ${/^[aeiou]/.test(noun) ? "an" : "a"} ${noun}`;
  };
  // The first picker still to use, in page order: the prompt and the phone bar point there.
  const firstOpen = (perAttribute ? keys : [VARIANT]).find((k) => open.has(k));

  function choose(v: Variant | undefined, key: string) {
    if (!v) return;
    setVariantId(v.id);
    setOpen((prev) => new Set([...prev].filter((k) => k !== key)));
    setQuantity((q) => Math.min(q, Math.max(1, Math.min(10, v.available))));
    setMessage(undefined);
  }

  /** Bring the shopper to the first unpicked option, with the prompt showing. */
  function showPicker() {
    setPrompted(true);
    const input = rootRef.current?.querySelector<HTMLInputElement>("fieldset[data-open] input:not(:disabled)");
    if (!input) return;
    const smooth = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    input.closest("fieldset")?.scrollIntoView({ block: "center", behavior: smooth ? "smooth" : "auto" });
    input.focus({ preventScroll: true });
  }

  async function add() {
    if (choosing) {
      showPicker();
      return;
    }
    if (!variant) return;
    setMessage(undefined);
    // PUT sets the line quantity, so add on top of what's already in the cart.
    const cart = client.getQueryData<CartOut>(CART_KEY);
    const existing = cart?.items.find((i) => i.variant_id === variant.id)?.quantity ?? 0;
    try {
      await setItem.mutateAsync({ variantId: variant.id, quantity: Math.min(existing + quantity, maxQty) });
      setMessage({ tone: "success", text: `Added to cart: ${product.title}${product.variants.length > 1 ? ` (${variant.name})` : ""}.` });
    } catch (e) {
      setMessage({ tone: "error", text: e instanceof Error ? e.message : "Couldn't add to cart." });
    }
  }

  /** The legend's value: the current choice, or "Select a size" (red once they've tried to add). */
  const legendValue = (key: string, chosen: string) => (
    <span
      className={open.has(key) && prompted && key === firstOpen ? "font-medium text-danger-700" : "font-normal text-muted"}
    >
      {open.has(key) ? selectText(key) : chosen}
    </span>
  );
  const prompt = (key: string) =>
    prompted && key === firstOpen ? (
      <p role="alert" className="mt-2 text-sm font-medium text-danger-700">
        {selectText(key)} to add this to your cart.
      </p>
    ) : null;

  return (
    <div ref={rootRef}>
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
        <div>
          <p className="font-display text-4xl font-semibold tabular-nums tracking-tight text-ink">
            {onePrice ? null : <span className="mr-2 font-sans text-lg font-medium tracking-normal text-muted">From</span>}
            {price}
            {prices.size > 1 && !choosing ? <span className="sr-only"> for {variant.name}</span> : null}
          </p>
          {unitPrice ? (
            <p className="mt-1 text-sm tabular-nums text-muted">
              <span className="sr-only">Unit price: </span>
              {unitPrice}
            </p>
          ) : null}
        </div>
        <div className="flex flex-col items-end gap-1 pt-1.5">
          <StockStatus inStock={inStock} available={available} />
          {choosing ? null : <p className="text-xs text-muted">Item #{variant.sku}</p>}
        </div>
      </div>

      {perAttribute ? (
        keys.map((key, index) => {
          const isColor = COLOR_KEYS.includes(key);
          const isOpen = open.has(key);
          return (
            <fieldset key={key} data-open={isOpen || undefined} className={index === 0 ? "mt-7" : "mt-5"}>
              <legend className="text-sm font-semibold text-ink">
                {titleCase(key)}: {legendValue(key, attr(variant, key))}
              </legend>
              {prompt(key)}
              <div className="mt-3 flex flex-wrap gap-2">
                {valuesOf(product.variants, key).map((value) => {
                  // Variants with this value that keep the other picks; an unpicked option
                  // matches anything.
                  const combos = product.variants.filter(
                    (v) =>
                      attr(v, key) === value &&
                      keys.every((k) => k === key || open.has(k) || attr(v, k) === attr(variant, k)),
                  );
                  const comboInStock = combos.some((v) => v.in_stock);
                  const anyInStock = product.variants.some((v) => attr(v, key) === value && v.in_stock);
                  // The first attribute (usually colour) is always choosable; later ones are
                  // disabled when that combination is sold out or doesn't exist.
                  const disabled = index > 0 && !comboInStock;
                  const valueInStock = index === 0 ? anyInStock : comboInStock;
                  return (
                    <OptionChip
                      key={value}
                      name={`option-${key}`}
                      value={value}
                      checked={!isOpen && attr(variant, key) === value}
                      inStock={valueInStock}
                      disabled={disabled}
                      swatch={isColor}
                      note={!valueInStock ? (index > 0 && !combos.length ? "not available" : "out of stock") : undefined}
                      onSelect={() => choose(pick(product.variants, keys, variant, key, value, open), key)}
                    />
                  );
                })}
              </div>
            </fieldset>
          );
        })
      ) : product.variants.length > 1 ? (
        <fieldset data-open={open.has(VARIANT) || undefined} className="mt-7">
          <legend className="text-sm font-semibold text-ink">
            {keys[0] ? titleCase(keys[0]) : "Options"}: {legendValue(VARIANT, variant.name)}
          </legend>
          {prompt(VARIANT)}
          <div className="mt-3 flex flex-wrap gap-2">
            {product.variants.map((v) => (
              <OptionChip
                key={v.id}
                name="variant"
                value={v.name}
                checked={!choosing && v.id === variant.id}
                inStock={v.in_stock}
                swatch={!!keys[0] && COLOR_KEYS.includes(keys[0])}
                note={v.in_stock ? undefined : "out of stock"}
                onSelect={() => choose(v, VARIANT)}
              />
            ))}
          </div>
        </fieldset>
      ) : singleOption ? (
        <p className="mt-5 text-sm text-ink">
          <span className="font-semibold">{singleOption.label}:</span>{" "}
          <span className="text-muted">{singleOption.value}</span>
        </p>
      ) : null}

      <div ref={buyRowRef}>
        {inStock ? (
          <div className="mt-7 flex items-end gap-3">
            <div className="w-24 shrink-0">
              <label htmlFor="quantity" className="block text-sm font-semibold text-ink">
                Quantity
              </label>
              <PillSelect
                id="quantity"
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
                wrapperClassName="mt-2"
                className="min-h-13 pl-5 tabular-nums"
              >
                {Array.from({ length: maxQty }, (_, i) => i + 1).map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </PillSelect>
            </div>
            <Button size="lg" onClick={add} loading={setItem.isPending} className="min-w-0 flex-1">
              {setItem.isPending ? null : <CartIcon className="size-5" />}
              {setItem.isPending ? "Adding…" : "Add to cart"}
            </Button>
          </div>
        ) : (
          <p className="mt-7 rounded-2xl bg-sunken px-5 py-4 text-sm text-ink-soft">
            {product.variants.length > 1
              ? `This option is out of stock right now. ${product.variants.some((v) => v.in_stock) ? "Try another option above." : "Check back soon."}`
              : "This item is out of stock right now. Check back soon."}
          </p>
        )}
      </div>

      <div aria-live="polite" className="empty:hidden not-empty:mt-4">
        {message ? (
          <Notice
            tone={message.tone}
            className="animate-fade-in"
            action={
              message.tone === "success" ? (
                <ButtonLink href="/cart" variant="outline" size="sm">
                  View cart
                </ButtonLink>
              ) : undefined
            }
          >
            {message.text}
          </Notice>
        ) : null}
      </div>

      {/* Its own wrapper: `trust` comes from the server component and can arrive as a lazy RSC
          chunk. Among sibling children React would key-check it once resolved ("Each child in a
          list should have a unique key"); as an only child it isn't part of a list. */}
      {trust ? <div>{trust}</div> : null}

      {barVisible && inStock ? (
        <div className="fixed inset-x-0 bottom-0 z-40 animate-fade-in border-t border-line bg-raised/95 py-3 pl-4 pr-22 shadow-[0_-8px_24px_-12px_rgb(24_24_35/0.25)] backdrop-blur-md pb-[max(0.75rem,env(safe-area-inset-bottom))] lg:hidden print:hidden">
          <div className="flex items-center gap-3">
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs text-muted">
                {product.variants.length > 1 && !choosing ? variant.name : product.title}
              </p>
              <p className="font-display text-lg font-semibold tabular-nums leading-tight text-ink">
                {onePrice ? null : <span className="mr-1 font-sans text-sm font-medium text-muted">From</span>}
                {price}
              </p>
            </div>
            {firstOpen ? (
              // Takes the shopper back up to the picker; adding waits for the choice.
              <Button onClick={showPicker} className="shrink-0">
                {selectText(firstOpen)}
              </Button>
            ) : (
              <Button onClick={add} loading={setItem.isPending} className="shrink-0">
                {setItem.isPending ? null : message?.tone === "success" ? <CheckIcon className="size-4.5" /> : <CartIcon className="size-4.5" />}
                {setItem.isPending ? "Adding…" : "Add to cart"}
              </Button>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
