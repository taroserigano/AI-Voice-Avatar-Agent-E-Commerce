import { AlertCircleIcon, AlertTriangleIcon, CheckCircleIcon, ClockIcon, InfoIcon, ReturnIcon } from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import {
  RETURN_STEPS,
  conditionLabel,
  formatDate,
  refundDisplay,
  returnProgress,
  returnReasonLabel,
  returnStatusMeta,
  type Tone,
} from "@/lib/orders";
import type { LineReturnOption, ReturnOut } from "@ai-commerce/contracts";
import { Stepper } from "./stepper";

const refundBox: Record<Tone, { box: string; icon: string; title: string; detail: string }> = {
  neutral: { box: "bg-sunken ring-line", icon: "text-muted", title: "text-ink", detail: "text-muted" },
  brand: { box: "bg-brand-50 ring-brand-100", icon: "text-brand-600", title: "text-brand-900", detail: "text-brand-800" },
  success: { box: "bg-success-50 ring-success-200/70", icon: "text-success-600", title: "text-success-900", detail: "text-success-800" },
  warning: { box: "bg-warning-50 ring-warning-200/70", icon: "text-warning-600", title: "text-warning-900", detail: "text-warning-800" },
  danger: { box: "bg-danger-50 ring-danger-200/70", icon: "text-danger-600", title: "text-danger-900", detail: "text-danger-800" },
  accent: { box: "bg-accent-50 ring-accent-200/70", icon: "text-accent-700", title: "text-accent-900", detail: "text-accent-800" },
};

const refundIcon = { neutral: ClockIcon, brand: ClockIcon, success: CheckCircleIcon, warning: AlertTriangleIcon, danger: AlertCircleIcon, accent: InfoIcon };

/** Past and in-progress returns for this order, each with its own return and refund status. */
export function ReturnsList({
  returns,
  destination,
  currency,
  options,
}: {
  returns: ReturnOut[];
  destination: string;
  currency: string;
  /** Return options by order line, for the refund-timing phrase when the line still has it. */
  options: Map<string, LineReturnOption>;
}) {
  return (
    <section aria-labelledby="returns-heading" id="returns" className="scroll-mt-28">
      <h2 id="returns-heading" className="font-display text-xl font-semibold text-ink sm:text-2xl">
        Returns
      </h2>
      <ul className="mt-5 space-y-4">
        {returns.map((ret) => (
          <ReturnCard key={ret.id} ret={ret} destination={destination} currency={currency} options={options} />
        ))}
      </ul>
    </section>
  );
}

function ReturnCard({
  ret,
  destination,
  currency,
  options,
}: {
  ret: ReturnOut;
  destination: string;
  currency: string;
  options: Map<string, LineReturnOption>;
}) {
  const progress = returnProgress(ret.status);
  const status = returnStatusMeta(ret.status);
  const timing = ret.items.map((i) => options.get(i.order_line_id)?.refund_timing).find(Boolean) ?? null;
  const refund = refundDisplay(ret, destination, (m) => formatMoney(m, ret.refund?.currency ?? currency), timing);
  const box = refundBox[refund.tone];
  const RefundIcon = refundIcon[refund.tone];
  const headingId = `return-${ret.id}`;

  return (
    <li>
      <article aria-labelledby={headingId} className="rounded-3xl border border-line bg-raised shadow-xs">
        <header className="flex flex-wrap items-start justify-between gap-x-4 gap-y-3 p-5 sm:p-6">
          <div className="flex min-w-0 items-start gap-3.5">
            <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-700">
              <ReturnIcon className="size-5.5" />
            </span>
            <div className="min-w-0">
              <h3 id={headingId} className="font-sans text-base font-semibold text-ink">
                Return <span className="font-mono text-[0.9375rem] tracking-wide">{ret.rma_number}</span>
              </h3>
              <p className="mt-0.5 text-sm text-muted">
                Started <time dateTime={ret.created_at}>{formatDate(ret.created_at)}</time>
                {" · "}
                {returnReasonLabel(ret.reason)}
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
        </header>

        <div className="border-t border-line px-5 py-6 sm:px-6">
          {progress.kind === "steps" ? (
            <>
              <Stepper
                size="sm"
                label="Return progress"
                current={progress.current}
                steps={RETURN_STEPS.map((label, i) => ({
                  key: label,
                  label,
                  date: i === 0 ? ret.created_at : i === RETURN_STEPS.length - 1 ? ret.closed_at : null,
                }))}
              />
              {progress.note ? (
                <p className="mt-4 flex items-center justify-center gap-2 text-sm text-muted">
                  <InfoIcon className="size-4 text-brand-600" />
                  {progress.note}
                </p>
              ) : null}
            </>
          ) : (
            <p className="flex items-center gap-2 text-sm font-semibold text-ink">
              <AlertCircleIcon className={cn("size-5", progress.tone === "danger" ? "text-danger-600" : "text-muted")} />
              {progress.label}
            </p>
          )}
        </div>

        <div className="border-t border-line px-5 py-5 sm:px-6">
          <ul className="space-y-3">
            {ret.items.map((item) => (
              <li key={`${item.order_line_id}-${item.condition}`} className="flex items-center gap-3.5">
                {/* eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations */}
                <img
                  src={item.image_path}
                  alt=""
                  width={640}
                  height={640}
                  loading="lazy"
                  className="size-14 shrink-0 rounded-xl bg-sunken object-cover ring-1 ring-inset ring-line/60"
                />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-ink">{item.product_title}</p>
                  <p className="mt-0.5 text-xs text-muted">
                    {item.variant_name !== "Standard" ? `${item.variant_name} · ` : null}
                    Qty {item.quantity} · Condition: {conditionLabel(item.condition)}
                  </p>
                </div>
                <p className="shrink-0 text-right text-sm">
                  <span className="block text-xs text-muted">Refund</span>
                  <span className="font-semibold tabular-nums text-ink">{formatMoney(item.refund_minor, currency)}</span>
                </p>
              </li>
            ))}
          </ul>
          {ret.shipping_refund_minor > 0 ? (
            <p className="mt-3 text-sm text-muted">
              Shipping refund:{" "}
              <span className="font-semibold tabular-nums text-ink">{formatMoney(ret.shipping_refund_minor, currency)}</span>
            </p>
          ) : null}

          <div className={cn("mt-5 flex items-start gap-3 rounded-2xl px-4 py-3.5 ring-1 ring-inset", box.box)}>
            <RefundIcon className={cn("mt-px size-5", box.icon)} />
            <div className="min-w-0 text-sm">
              <p className={cn("font-semibold", box.title)}>
                <span className="sr-only">Refund status: </span>
                {refund.title}
              </p>
              {refund.detail ? <p className={cn("mt-0.5", box.detail)}>{refund.detail}</p> : null}
            </div>
          </div>
        </div>
      </article>
    </li>
  );
}
