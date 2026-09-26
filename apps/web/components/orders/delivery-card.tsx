import {
  AlertTriangleIcon,
  CheckCircleIcon,
  ChevronDownIcon,
  CloseIcon,
  InfoIcon,
  PackageIcon,
  TruckIcon,
} from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import {
  cardLabel,
  deliveryProgress,
  formatLongWeekday,
  formatTime,
  formatWeekday,
  plural,
  shipmentStatusLabel,
  type Tone,
} from "@/lib/orders";
import type { OrderDetail, ShipmentOut } from "@ai-commerce/contracts";
import type { ReactNode } from "react";
import { CopyButton } from "./copy-button";
import { Stepper } from "./stepper";

type Headline = { title: string; detail: ReactNode; tone: Tone; icon: ReactNode };

function headline(order: OrderDetail, shipment: ShipmentOut | null): Headline {
  if (order.status === "canceled") {
    const p = order.payment;
    return {
      title: "This order was canceled",
      detail:
        p && p.refunded_minor > 0
          ? `${formatMoney(p.refunded_minor, p.currency)} went back to ${cardLabel(p)}.`
          : "Nothing will ship.",
      tone: "neutral",
      icon: <CloseIcon className="size-6" />,
    };
  }
  const deliveredAt = shipment?.delivered_at ?? order.delivered_at;
  if ((order.status === "delivered" || shipment?.status === "delivered") && deliveredAt) {
    return {
      title: `Delivered ${formatLongWeekday(deliveredAt)}`,
      detail: shipment?.events.find((e) => e.status === "delivered")?.description ?? "Your package arrived.",
      tone: "success",
      icon: <CheckCircleIcon className="size-6" />,
    };
  }
  if (shipment?.status === "exception") {
    return {
      title: "There's a problem with this delivery",
      detail: shipment.events[0]?.description ?? "The carrier reported an issue. We're on it.",
      tone: "warning",
      icon: <AlertTriangleIcon className="size-6" />,
    };
  }
  const eta = shipment?.estimated_delivery_at;
  if (shipment?.status === "out_for_delivery") {
    return {
      title: "Out for delivery",
      detail: eta ? `Arriving by ${formatLongWeekday(eta)}.` : "Arriving soon.",
      tone: "brand",
      icon: <TruckIcon className="size-6" />,
    };
  }
  if (shipment?.status === "in_transit") {
    return {
      title: eta ? `Arriving by ${formatLongWeekday(eta)}` : "On its way",
      detail: `Shipped with ${shipment.carrier} ${shipment.service}.`,
      tone: "brand",
      icon: <TruckIcon className="size-6" />,
    };
  }
  return {
    title: "We're getting your order ready",
    detail: eta ? `Estimated arrival ${formatLongWeekday(eta)}.` : "We'll share tracking as soon as it ships.",
    tone: "brand",
    icon: <PackageIcon className="size-6" />,
  };
}

const iconTile: Record<Tone, string> = {
  neutral: "bg-sunken text-muted",
  brand: "bg-brand-50 text-brand-700",
  success: "bg-success-50 text-success-700",
  warning: "bg-warning-50 text-warning-700",
  danger: "bg-danger-50 text-danger-700",
  accent: "bg-accent-100 text-accent-800",
};

/** Delivery status: headline, progress stepper, and the carrier's tracking details. */
export function DeliveryCard({ order, shipment }: { order: OrderDetail; shipment: ShipmentOut | null }) {
  const h = headline(order, shipment);
  const progress = deliveryProgress(order, shipment);
  const inProgress = order.status !== "delivered" && order.status !== "canceled";

  return (
    <section aria-labelledby="delivery-heading" className="rounded-3xl border border-line bg-raised shadow-xs">
      <div className="p-5 sm:p-7">
        <div className="flex items-start gap-4">
          <span className={cn("grid size-12 shrink-0 place-items-center rounded-2xl", iconTile[h.tone])}>{h.icon}</span>
          <div className="min-w-0">
            <p aria-hidden="true" className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">
              Delivery
            </p>
            <h2 id="delivery-heading" className="mt-1 font-display text-xl font-semibold text-ink sm:text-2xl">
              <span className="sr-only">Delivery: </span>
              {h.title}
            </h2>
            <p className="mt-1 text-sm text-muted">{h.detail}</p>
          </div>
        </div>

        {progress ? (
          <Stepper
            label="Delivery progress"
            steps={progress.steps}
            current={progress.current}
            issue={progress.issue}
            className="mt-7 sm:mt-8"
          />
        ) : null}
      </div>

      {shipment ? <Tracking shipment={shipment} open={inProgress} /> : null}
    </section>
  );
}

function Tracking({ shipment, open }: { shipment: ShipmentOut; open: boolean }) {
  const eta = shipment.delivered_at ?? shipment.estimated_delivery_at;
  return (
    <div className="border-t border-line">
      <dl className="grid grid-cols-2 gap-x-6 gap-y-4 px-5 py-5 text-sm sm:grid-cols-3 sm:px-7">
        <div>
          <dt className="text-muted">Carrier</dt>
          <dd className="mt-0.5 font-medium text-ink">
            {shipment.carrier} <span className="text-muted">· {shipment.service}</span>
          </dd>
        </div>
        <div className="col-span-2 min-w-0 sm:order-none sm:col-span-1 max-sm:order-last">
          <dt className="text-muted">Tracking number</dt>
          <dd className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="font-mono text-[0.8125rem] font-medium tracking-wide text-ink">{shipment.tracking_number}</span>
            <CopyButton value={shipment.tracking_number} label="tracking number" />
          </dd>
        </div>
        <div>
          <dt className="text-muted">{shipment.delivered_at ? "Delivered" : "Estimated delivery"}</dt>
          <dd className="mt-0.5 font-medium text-ink">
            {eta ? <time dateTime={eta}>{formatWeekday(eta)}</time> : "Not available yet"}
          </dd>
        </div>
      </dl>

      {shipment.is_simulated ? (
        <p className="mx-5 mb-4 flex items-start gap-2 rounded-xl bg-sunken px-3.5 py-2.5 text-xs text-muted sm:mx-7">
          <InfoIcon className="mt-px size-4 shrink-0 text-brand-600" />
          <span>
            <strong className="font-semibold text-ink">Simulated tracking (sandbox).</strong> These scans are generated test
            data; no real carrier is involved.
          </span>
        </p>
      ) : null}

      {shipment.events.length > 0 ? (
        <details open={open} className="group/track border-t border-line">
          <summary className="flex min-h-13 cursor-pointer list-none items-center justify-between gap-3 px-5 text-sm font-semibold text-ink transition-colors hover:bg-neutral-50 sm:px-7 [&::-webkit-details-marker]:hidden">
            <span className="flex items-center gap-2">
              Tracking history
              <Badge tone="neutral">{plural(shipment.events.length, "update")}</Badge>
            </span>
            <ChevronDownIcon className="size-4.5 text-muted transition-transform duration-200 ease-snappy group-open/track:rotate-180" />
          </summary>
          <ScanTimeline events={shipment.events} />
        </details>
      ) : null}
    </div>
  );
}

function ScanTimeline({ events }: { events: ShipmentOut["events"] }) {
  return (
    <ol aria-label="Tracking scans, newest first" className="animate-slide-down px-5 pb-6 pt-1 sm:px-7">
      {events.map((e, i) => {
        const latest = i === 0;
        const last = i === events.length - 1;
        return (
          <li key={`${e.occurred_at}-${i}`} className="relative flex gap-4 pb-5 last:pb-0">
            {!last ? <span aria-hidden="true" className="absolute left-1.75 top-5 bottom-0 w-0.5 bg-line" /> : null}
            <span
              aria-hidden="true"
              className={cn(
                "relative mt-1 size-4 shrink-0 rounded-full ring-4",
                latest
                  ? e.status === "delivered"
                    ? "bg-success-600 ring-success-100"
                    : "bg-brand-600 ring-brand-100"
                  : "bg-raised ring-0 border-2 border-line-strong",
              )}
            />
            <div className="min-w-0 flex-1 sm:flex sm:items-baseline sm:justify-between sm:gap-6">
              <div className="min-w-0">
                <p className={cn("text-sm", latest ? "font-semibold text-ink" : "font-medium text-ink-soft")}>
                  {e.description}
                  {latest ? <span className="sr-only"> (latest)</span> : null}
                </p>
                <p className="mt-0.5 text-xs text-muted">
                  {shipmentStatusLabel(e.status)}
                  {e.location ? ` · ${e.location}` : null}
                </p>
              </div>
              <p className="mt-1 shrink-0 text-xs tabular-nums text-muted sm:mt-0 sm:text-right">
                <time dateTime={e.occurred_at}>
                  {formatWeekday(e.occurred_at)} · {formatTime(e.occurred_at)}
                </time>
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
