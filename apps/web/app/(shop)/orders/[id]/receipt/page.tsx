import { ArrowLeftIcon, InfoIcon } from "@/components/icons";
import { LogoMark } from "@/components/logo";
import { OrderStatusBadge } from "@/components/orders/order-status-badge";
import { PrintButton } from "@/components/orders/receipt-actions";
import { AddressLines } from "@/components/orders/shipping-address";
import { Badge } from "@/components/ui/badge";
import { buttonClasses } from "@/components/ui/button";
import { formatMoney } from "@/lib/format";
import { cardLabel, formatDate, formatTime, orderNumber, variantLabel } from "@/lib/orders";
import type { Metadata } from "next";
import Link from "next/link";
// Shared with the order page and its layout: one owner-scoped read per request, and a stranger's
// receipt is a 404 exactly like a missing one.
import { loadOrder } from "../load-order";

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const order = await loadOrder((await params).id);
  return { title: `Receipt for order #${orderNumber(order.id)}` };
}

// Printing hides the store chrome (header, footer, sandbox bar) and the receipt's own buttons, so
// the page prints as just the receipt. Scoped with :has(), so it only applies on this page.
const PRINT_CSS = `
@media print {
  @page { margin: 14mm; }
  body:has(#receipt) header,
  body:has(#receipt) footer,
  body:has(#receipt) [aria-label="Sandbox notice"] { display: none !important; }
  body:has(#receipt) #main { padding: 0 !important; max-width: none !important; }
  body:has(#receipt) { background: #fff !important; }
  #receipt { box-shadow: none !important; border: 0 !important; padding: 0 !important; }
  #receipt * { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
}
`;

function Total({ label, value, strong = false }: { label: string; value: string; strong?: boolean }) {
  return (
    <div className={strong ? "flex justify-between gap-6 border-t border-line pt-2.5" : "flex justify-between gap-6"}>
      <dt className={strong ? "font-semibold text-ink" : "text-muted"}>{label}</dt>
      <dd className={strong ? "font-display text-lg font-semibold tabular-nums text-ink" : "tabular-nums text-ink"}>
        {value}
      </dd>
    </div>
  );
}

export default async function ReceiptPage({ params }: { params: Promise<{ id: string }> }) {
  const order = await loadOrder((await params).id);
  const number = orderNumber(order.id);
  const money = (m: number) => formatMoney(m, order.currency);
  const p = order.payment;

  return (
    <div className="pb-24 pt-2 sm:pb-8 sm:pt-4">
      <style>{PRINT_CSS}</style>

      <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-3 print:hidden">
        <Link href={`/orders/${order.id}`} className={buttonClasses("ghost", "sm", "-ml-3 text-brand-700")}>
          <ArrowLeftIcon className="size-4" />
          Back to order #{number}
        </Link>
        <PrintButton />
      </div>

      <article
        id="receipt"
        aria-labelledby="receipt-heading"
        className="mx-auto mt-4 max-w-3xl rounded-3xl border border-line bg-raised p-5 text-sm text-ink-soft shadow-xs sm:p-10"
      >
        <div className="flex flex-wrap items-start justify-between gap-x-8 gap-y-4 border-b border-line pb-6">
          <div className="flex items-center gap-3">
            <LogoMark className="size-10" />
            <div>
              <p className="font-display text-2xl font-semibold tracking-[-0.03em] text-ink">Serigan Mart</p>
              <p className="text-xs text-muted">Online order · Dallas-Fort Worth (demo store)</p>
            </div>
          </div>
          <div className="sm:text-right">
            <h1 id="receipt-heading" className="font-display text-xl font-semibold text-ink">
              Receipt
            </h1>
            <p className="mt-0.5">
              Order <span className="font-mono font-semibold tracking-wide text-ink">#{number}</span>
            </p>
            <p className="text-muted">
              <time dateTime={order.placed_at}>
                {formatDate(order.placed_at)}, {formatTime(order.placed_at)}
              </time>
            </p>
          </div>
        </div>

        <div className="grid gap-6 border-b border-line py-6 sm:grid-cols-3">
          <div>
            <h2 className="text-xs font-semibold uppercase tracking-eyebrow text-muted">Ship to</h2>
            <div className="mt-1.5">
              {order.shipping_address ? (
                <>
                  <AddressLines address={order.shipping_address} />
                  {order.shipping_address.is_sample ? (
                    <Badge tone="neutral" className="mt-1.5">
                      Sample address
                    </Badge>
                  ) : null}
                </>
              ) : (
                <p className="text-muted">No delivery address on file</p>
              )}
            </div>
          </div>
          <div>
            <h2 className="text-xs font-semibold uppercase tracking-eyebrow text-muted">Paid with</h2>
            <p className="mt-1.5 font-semibold text-ink">{p ? cardLabel(p) : "No payment on file"}</p>
            {p?.captured_at ? (
              <p className="text-muted">
                Charged <time dateTime={p.captured_at}>{formatDate(p.captured_at)}</time>
              </p>
            ) : null}
          </div>
          <div>
            <h2 className="text-xs font-semibold uppercase tracking-eyebrow text-muted">Status</h2>
            <div className="mt-1.5">
              <OrderStatusBadge status={order.status} size="sm" />
            </div>
            {order.delivered_at ? (
              <p className="mt-1 text-muted">
                Delivered <time dateTime={order.delivered_at}>{formatDate(order.delivered_at)}</time>
              </p>
            ) : null}
          </div>
        </div>

        <table className="mt-6 w-full border-collapse text-left">
          <caption className="sr-only">Items in order #{number}</caption>
          <thead>
            <tr className="border-b border-line text-xs uppercase tracking-eyebrow text-muted">
              <th scope="col" className="pb-2 pr-3 font-semibold">
                Item
              </th>
              <th scope="col" className="pb-2 pr-3 text-right font-semibold">
                Qty
              </th>
              <th scope="col" className="hidden pb-2 pr-3 text-right font-semibold sm:table-cell print:table-cell">
                Unit price
              </th>
              <th scope="col" className="pb-2 text-right font-semibold">
                Amount
              </th>
            </tr>
          </thead>
          <tbody>
            {order.lines.map((line) => {
              const variant = variantLabel(line.variant_name);
              return (
                <tr key={line.id} className="border-b border-line/70 align-top">
                  <td className="py-3 pr-3">
                    <p className="font-medium text-ink">{line.product_title}</p>
                    <p className="text-xs text-muted">
                      {variant ? `${variant} · ` : null}SKU {line.sku}
                      <span className="sm:hidden print:hidden"> · {money(line.unit_price_minor)} each</span>
                    </p>
                    {line.amount_discount_minor > 0 ? (
                      <p className="text-xs font-medium text-success-700">
                        Discount −{money(line.amount_discount_minor)}
                      </p>
                    ) : null}
                  </td>
                  <td className="py-3 pr-3 text-right tabular-nums">{line.quantity}</td>
                  <td className="hidden py-3 pr-3 text-right tabular-nums sm:table-cell print:table-cell">
                    {money(line.unit_price_minor)}
                  </td>
                  <td className="py-3 text-right font-medium tabular-nums text-ink">{money(line.amount_subtotal_minor)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>

        <dl className="ml-auto mt-5 max-w-xs space-y-1.5">
          <Total label="Subtotal" value={money(order.subtotal_minor)} />
          {order.discount_minor > 0 ? <Total label="Discounts" value={`−${money(order.discount_minor)}`} /> : null}
          <Total label="Shipping" value={order.shipping_minor > 0 ? money(order.shipping_minor) : "Free"} />
          <Total label="Tax" value={money(order.tax_minor)} />
          <Total label="Total" value={money(order.total_minor)} strong />
          {p && p.refunded_minor > 0 ? (
            <Total label="Refunded so far" value={`−${formatMoney(p.refunded_minor, p.currency)}`} />
          ) : null}
        </dl>

        <div className="mt-8 space-y-1.5 border-t border-line pt-5 text-xs text-muted">
          {p?.is_simulated ? (
            <p className="flex items-start gap-1.5">
              <InfoIcon className="mt-px size-3.5 shrink-0 text-brand-600" />
              <span>
                <strong className="font-semibold text-ink">Sandbox receipt.</strong> The payment was simulated; no real card
                was charged.
              </span>
            </p>
          ) : null}
          <p>Returns within 30 days of delivery, refunded to your original payment method. Some items are final sale.</p>
          <p>Questions about this order? See Help, or ask Xana on the Support page.</p>
        </div>
      </article>
    </div>
  );
}
