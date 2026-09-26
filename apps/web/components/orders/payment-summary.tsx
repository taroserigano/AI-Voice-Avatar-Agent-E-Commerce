import { ArrowRightIcon, CreditCardIcon, InfoIcon, ReturnIcon } from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import { formatMoney } from "@/lib/format";
import { cardLabel, formatDate, paymentStatusMeta } from "@/lib/orders";
import type { OrderDetail } from "@ai-commerce/contracts";
import Link from "next/link";

function Row({ label, value, className }: { label: string; value: string; className?: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4">
      <dt className="text-muted">{label}</dt>
      <dd className={className ?? "tabular-nums text-ink"}>{value}</dd>
    </div>
  );
}

/** Order totals and the card that paid, exactly as the server charged them. */
export function PaymentSummary({ order }: { order: OrderDetail }) {
  const money = (m: number) => formatMoney(m, order.currency);
  const p = order.payment;
  const status = p ? paymentStatusMeta(p.status) : null;

  return (
    <section aria-labelledby="payment-heading" className="rounded-3xl border border-line bg-raised p-5 shadow-xs sm:p-6">
      <h2 id="payment-heading" className="font-display text-lg font-semibold text-ink">
        Payment summary
      </h2>
      <dl className="mt-4 space-y-2.5 text-sm">
        <Row label="Subtotal" value={money(order.subtotal_minor)} />
        {order.discount_minor > 0 ? (
          <Row label="Discount" value={`−${money(order.discount_minor)}`} className="font-medium tabular-nums text-success-700" />
        ) : null}
        <Row label="Shipping" value={order.shipping_minor > 0 ? money(order.shipping_minor) : "Free"} />
        <Row label="Tax" value={money(order.tax_minor)} />
        <div className="flex items-baseline justify-between gap-4 border-t border-line pt-3.5">
          <dt className="font-semibold text-ink">Total</dt>
          <dd className="font-display text-xl font-semibold tabular-nums text-ink">{money(order.total_minor)}</dd>
        </div>
        {p && p.refunded_minor > 0 ? (
          <div className="flex items-baseline justify-between gap-4">
            <dt className="text-muted">Refunded so far</dt>
            <dd className="font-semibold tabular-nums text-success-700">−{formatMoney(p.refunded_minor, p.currency)}</dd>
          </div>
        ) : null}
      </dl>

      {p ? (
        <div className="mt-5 rounded-2xl bg-sunken p-4">
          <div className="flex items-center gap-3">
            <span className="grid h-8 w-11 shrink-0 place-items-center rounded-md bg-raised text-brand-700 shadow-xs ring-1 ring-line">
              <CreditCardIcon className="size-5" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-xs text-muted">Paid with</p>
              <p className="text-sm font-semibold text-ink">{cardLabel(p)}</p>
            </div>
            {status ? (
              <Badge tone={status.tone} dot className="bg-raised">
                {status.label}
              </Badge>
            ) : null}
          </div>
          {p.captured_at ? (
            <p className="mt-3 text-xs text-muted">
              Charged {formatMoney(p.amount_minor, p.currency)} on <time dateTime={p.captured_at}>{formatDate(p.captured_at)}</time>
            </p>
          ) : null}
          {p.is_simulated ? (
            <p className="mt-2 flex items-start gap-1.5 text-xs text-muted">
              <InfoIcon className="mt-px size-3.5 shrink-0 text-brand-600" />
              <span>
                <strong className="font-semibold text-ink">Simulated payment (sandbox).</strong> No real card was charged.
              </span>
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

/** The one-line policy summary with a link to the full terms. */
export function ReturnPolicyCard({ policyVersion }: { policyVersion?: string }) {
  return (
    <aside aria-labelledby="policy-heading" className="rounded-3xl bg-brand-50/70 p-5 ring-1 ring-inset ring-brand-100 sm:p-6">
      <div className="flex items-start gap-3.5">
        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-raised text-brand-700 shadow-xs">
          <ReturnIcon className="size-5" />
        </span>
        <div className="min-w-0">
          <h2 id="policy-heading" className="font-sans text-sm font-semibold text-ink">
            30-day returns · Refunds to your original payment method
          </h2>
          <p className="mt-1 text-sm text-muted">Counted from delivery. Some items, like gift cards, are final sale.</p>
          <Link
            href="/help/returns"
            className="group mt-2 inline-flex min-h-11 items-center gap-1.5 text-sm font-semibold text-brand-700 hover:text-brand-900"
          >
            How returns work
            <ArrowRightIcon className="size-4 transition-transform duration-200 ease-snappy group-hover:translate-x-0.5" />
          </Link>
          {policyVersion ? <p className="text-xs text-muted">Policy version {policyVersion}</p> : null}
        </div>
      </div>
    </aside>
  );
}
