import {
  AlertTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  CreditCardIcon,
  InfoIcon,
  ReturnIcon,
  TagIcon,
  TruckIcon,
} from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Notice } from "@/components/ui/notice";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import { cardLabel, formatDay, ineligibleTitle, ineligibleTone, refundTimingPhrase, variantLabel } from "@/lib/orders";
import type { LineReturnOption, OrderDetail, ReturnOptions } from "@ai-commerce/contracts";
import Link from "next/link";
import { AddToCartButton } from "@/components/account/add-to-cart-button";

const HELPER = "Xena, our support assistant, shows your exact refund. Nothing is returned until you confirm.";

/**
 * Every line of the order with what the server says about returning it. Nothing here decides
 * eligibility or amounts; it only lays out `ReturnOptions` next to the line it belongs to.
 */
export function OrderItems({ order, options }: { order: OrderDetail; options: ReturnOptions | null }) {
  const byLine = new Map(options?.lines.map((l) => [l.order_line_id, l]) ?? []);
  const destination = cardLabel(options?.refund_destination ?? order.payment);
  const shippingBack = options?.whole_order_shipping_refund_minor ?? 0;
  // When the whole order can't be returned for one order-level reason (not delivered yet,
  // canceled), say it once instead of repeating the same panel under every line.
  const first = options?.lines[0];
  const shared =
    first &&
    !first.eligible &&
    (first.reason === "not_delivered" || first.reason === "canceled") &&
    options?.lines.every((l) => !l.eligible && l.reason === first.reason)
      ? first
      : null;

  return (
    <section aria-labelledby="items-heading" id="items" className="scroll-mt-28">
      <div className="flex flex-wrap items-end justify-between gap-x-4 gap-y-1">
        <h2 id="items-heading" className="font-display text-xl font-semibold text-ink sm:text-2xl">
          Items and returns
        </h2>
        <p className="text-sm text-muted">
          {order.lines.length === 1 ? "1 item" : `${order.lines.length} items`}
          {options ? " · Return eligibility from our policy" : null}
        </p>
      </div>

      {!options ? (
        <Notice tone="warning" className="mt-4">
          We couldn&apos;t load return options right now. Refresh the page to try again.
        </Notice>
      ) : null}

      {shared ? <IneligiblePanel option={shared} /> : null}

      <ul className="mt-5 space-y-4">
        {order.lines.map((line) => {
          const opt = byLine.get(line.id);
          return (
            <li key={line.id} className="rounded-3xl border border-line bg-raised p-4 shadow-xs sm:p-5">
              <div className="flex gap-4 sm:gap-5">
                {/* eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations */}
                <img
                  src={line.image_path}
                  alt=""
                  width={640}
                  height={640}
                  loading="lazy"
                  className="size-20 shrink-0 rounded-2xl bg-sunken object-cover ring-1 ring-inset ring-line/60 sm:size-24"
                />
                <div className="flex min-w-0 flex-1 flex-col justify-between gap-2 sm:flex-row sm:gap-6">
                  <div className="min-w-0">
                    <h3 className="font-sans text-base font-semibold leading-snug text-ink">
                      {line.product_id ? (
                        <Link
                          href={`/products/${line.product_id}`}
                          className="transition-colors hover:text-brand-700 hover:underline hover:underline-offset-4"
                        >
                          {line.product_title}
                        </Link>
                      ) : (
                        line.product_title
                      )}
                    </h3>
                    <p className="mt-1 text-sm text-muted">
                      {variantLabel(line.variant_name) ? `${line.variant_name} · ` : null}
                      Qty {line.quantity}
                    </p>
                    {line.amount_discount_minor > 0 ? (
                      <Badge tone="success" className="mt-2">
                        <TagIcon />
                        Saved {formatMoney(line.amount_discount_minor, order.currency)}
                      </Badge>
                    ) : null}
                  </div>
                  <div className="shrink-0 sm:text-right">
                    <p className="text-base font-semibold tabular-nums text-ink">
                      {formatMoney(line.amount_total_minor, order.currency)}
                    </p>
                    <p className="text-xs text-muted tabular-nums">
                      {line.quantity > 1 ? `${formatMoney(line.unit_price_minor, order.currency)} each · ` : null}
                      paid incl. tax
                    </p>
                    {line.product_id ? (
                      <AddToCartButton
                        variantId={line.variant_id}
                        productTitle={line.product_title}
                        label="Buy again"
                        again
                        variant="outline"
                        showCartLink
                        className="mt-2.5 sm:items-end"
                      />
                    ) : null}
                  </div>
                </div>
              </div>
              {opt && !shared ? <Eligibility option={opt} destination={destination} lineId={line.id} orderId={order.id} /> : null}
            </li>
          );
        })}
      </ul>

      {shippingBack > 0 ? (
        <p className="mt-4 flex items-start gap-3 rounded-2xl border border-brand-100 bg-brand-50 px-4 py-3.5 text-sm text-brand-900">
          <TruckIcon className="mt-px size-5 shrink-0 text-brand-600" />
          <span>
            Return everything in this order and we&apos;ll also refund your{" "}
            <strong className="font-semibold tabular-nums">{formatMoney(shippingBack, order.currency)}</strong> shipping.
          </span>
        </p>
      ) : null}
    </section>
  );
}

function Eligibility({
  option,
  destination,
  lineId,
  orderId,
}: {
  option: LineReturnOption;
  destination: string;
  lineId: string;
  orderId: string;
}) {
  const partlyReturned = option.returned_quantity > 0 && option.reason !== "fully_returned";
  if (option.eligible) {
    const helperId = `return-help-${lineId}`;
    const timing = refundTimingPhrase(option.refund_timing);
    return (
      <div className="mt-4 rounded-2xl bg-success-50 p-4 ring-1 ring-inset ring-success-200/70 sm:flex sm:items-start sm:justify-between sm:gap-6 sm:p-5">
        <div className="min-w-0">
          <p className="flex flex-wrap items-center gap-x-2.5 gap-y-1.5 font-semibold text-success-900">
            <CheckCircleIcon className="size-5 text-success-600" />
            {option.window_ends_at ? `Returnable until ${formatDay(option.window_ends_at)}` : "Returnable"}
            {partlyReturned ? (
              <Badge tone="neutral" className="bg-raised">
                {option.returned_quantity} of {option.quantity} already returned
              </Badge>
            ) : null}
          </p>
          <ul className="mt-3 space-y-2 text-sm text-ink-soft">
            {timing ? (
              <li className="flex items-start gap-2.5">
                <ClockIcon className="mt-px size-4.5 text-success-700" />
                <span>{timing}</span>
              </li>
            ) : null}
            <li className="flex items-start gap-2.5">
              <CreditCardIcon className="mt-px size-4.5 text-success-700" />
              <span>
                Up to{" "}
                <strong className="font-semibold tabular-nums text-ink">{formatMoney(option.max_refund_minor, option.currency)}</strong>{" "}
                back to {destination}
                {option.returnable_quantity > 1 ? ` for all ${option.returnable_quantity}` : null}
              </span>
            </li>
          </ul>
          <p className="mt-3 text-xs leading-relaxed text-muted">{option.message}</p>
        </div>
        <div className="mt-4 shrink-0 sm:mt-0 sm:w-52 sm:text-right">
          <ButtonLink
            href={`/support?order=${orderId}&line=${lineId}`}
            variant="primary"
            aria-describedby={helperId}
            className="w-full sm:w-auto"
          >
            <ReturnIcon className="size-4.5" />
            Start a return
            <span className="sr-only"> for {option.product_title}</span>
          </ButtonLink>
          <p id={helperId} className="mt-2 text-xs leading-snug text-muted">
            {HELPER}
          </p>
        </div>
      </div>
    );
  }

  return <IneligiblePanel option={option} />;
}

function IneligiblePanel({ option }: { option: LineReturnOption }) {
  const tone = ineligibleTone(option.reason);
  const Icon = tone === "warning" ? AlertTriangleIcon : option.reason === "final_sale" ? TagIcon : InfoIcon;
  return (
    <div
      className={cn(
        "mt-4 flex items-start gap-3 rounded-2xl p-4 ring-1 ring-inset sm:p-5",
        tone === "warning" ? "bg-warning-50 ring-warning-200/70" : "bg-sunken ring-line",
      )}
    >
      <Icon className={cn("mt-px size-5", tone === "warning" ? "text-warning-600" : "text-muted")} />
      <div className="min-w-0 text-sm">
        <p className={cn("font-semibold", tone === "warning" ? "text-warning-900" : "text-ink")}>
          {ineligibleTitle(option)}
        </p>
        <p className={cn("mt-0.5", tone === "warning" ? "text-warning-800" : "text-muted")}>
          {option.message}
          {option.reason === "fully_returned" ? (
            <>
              {" "}
              <a
                href="#returns"
                className="font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700"
              >
                See the return
              </a>
            </>
          ) : null}
        </p>
      </div>
    </div>
  );
}
