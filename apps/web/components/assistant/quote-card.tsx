"use client";

import { CheckCircleIcon, ClockIcon, CreditCardIcon, PackageIcon, ReturnIcon } from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import type { ReturnQuoteCard } from "@/lib/assistant-types";
import { formatMoney } from "@/lib/format";
import { confirmQuote } from "@/lib/returns-confirm";
import { useEffect, useState } from "react";

function useCountdown(expiresAt: string) {
  const [left, setLeft] = useState(() => Math.max(0, new Date(expiresAt).getTime() - Date.now()));
  useEffect(() => {
    const t = window.setInterval(() => setLeft(Math.max(0, new Date(expiresAt).getTime() - Date.now())), 1000);
    return () => window.clearInterval(t);
  }, [expiresAt]);
  const m = Math.floor(left / 60000);
  const s = Math.floor((left % 60000) / 1000);
  return { left, label: `${m}:${String(s).padStart(2, "0")}` };
}

/**
 * A priced return waiting for the customer. Confirm goes straight to the store from this browser
 * (a single-use token the assistant never sees); the conversation then resumes with the outcome.
 */
export function QuoteCard({
  quote,
  onResolved,
  disabled = false,
}: {
  quote: ReturnQuoteCard;
  onResolved: (outcome: "confirmed" | "declined") => void | Promise<void>;
  disabled?: boolean;
}) {
  const [busy, setBusy] = useState<"confirm" | "decline" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { left, label } = useCountdown(quote.expires_at);
  const expired = quote.status === "expired" || left <= 0;
  const done = quote.status === "confirmed";

  const confirm = async () => {
    setBusy("confirm");
    setError(null);
    const result = await confirmQuote(quote.quote_id);
    if (result.ok) {
      await onResolved("confirmed");
    } else {
      setError(result.status === 410 ? "This quote expired. Ask for a new one." : result.message);
    }
    setBusy(null);
  };

  const decline = async () => {
    setBusy("decline");
    await onResolved("declined");
    setBusy(null);
  };

  return (
    <section
      aria-label="Return quote"
      className="mt-2 overflow-hidden rounded-2xl bg-raised shadow-sm ring-1 ring-inset ring-brand-200"
    >
      <header className="flex items-center justify-between gap-2 bg-brand-50 px-4 py-2.5">
        <p className="flex items-center gap-2 text-sm font-semibold text-brand-900">
          <ReturnIcon className="size-4.5" /> Your return quote
        </p>
        {done ? (
          <Badge tone="success">Confirmed</Badge>
        ) : expired ? (
          <Badge tone="neutral">Expired</Badge>
        ) : (
          <Badge tone="brand">
            <ClockIcon /> Valid {label}
          </Badge>
        )}
      </header>
      <ul className="divide-y divide-line px-4">
        {quote.lines.map((ln) => (
          <li key={ln.order_line_id} className="flex gap-3 py-3">
            {/* eslint-disable-next-line @next/next/no-img-element -- local product illustrations */}
            <img src={ln.image_path} alt="" width={44} height={44} className="size-11 shrink-0 rounded-xl bg-canvas object-contain" />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-ink">
                {ln.quantity} × {ln.title}
              </p>
              {ln.variant_name ? <p className="text-xs text-muted">{ln.variant_name}</p> : null}
              <p className="mt-0.5 text-xs text-muted">{ln.timing_message}</p>
            </div>
            <p className="text-sm font-semibold tabular-nums text-ink">{formatMoney(ln.refund_minor, quote.currency)}</p>
          </li>
        ))}
      </ul>
      <dl className="space-y-1 border-t border-line px-4 py-3 text-sm">
        {quote.shipping_refund_minor > 0 ? (
          <div className="flex justify-between text-ink-soft">
            <dt>Shipping refund</dt>
            <dd className="tabular-nums">{formatMoney(quote.shipping_refund_minor, quote.currency)}</dd>
          </div>
        ) : null}
        <div className="flex items-baseline justify-between">
          <dt className="font-semibold text-ink">You get back</dt>
          <dd className="font-display text-2xl font-semibold tabular-nums text-ink">
            {formatMoney(quote.total_refund_minor, quote.currency)}
          </dd>
        </div>
      </dl>
      <div className="space-y-1 px-4 pb-3 text-xs text-muted">
        <p className="flex items-center gap-1.5">
          <CreditCardIcon className="size-3.5" /> To {quote.refund_destination}
        </p>
        <p className="flex items-center gap-1.5">
          <PackageIcon className="size-3.5" />
          {quote.needs_shipping
            ? "Free prepaid label after you confirm; drop it with the carrier or at any Larkspur store."
            : "Nothing to send back."}
        </p>
      </div>
      {done ? (
        <p className="flex items-center gap-2 border-t border-line bg-success-50 px-4 py-3 text-sm font-medium text-success-800">
          <CheckCircleIcon className="size-4.5" /> Return confirmed.
        </p>
      ) : expired ? (
        <p className="border-t border-line px-4 py-3 text-sm text-muted">This quote expired. Ask for a new one.</p>
      ) : (
        <div className="flex flex-wrap items-center gap-2 border-t border-line px-4 py-3">
          <button
            type="button"
            onClick={() => void confirm()}
            disabled={disabled || busy !== null}
            className="inline-flex min-h-11 items-center gap-2 rounded-full bg-brand-600 px-5 text-sm font-semibold text-white shadow-glow hover:bg-brand-700 disabled:opacity-60"
          >
            {busy === "confirm" ? "Confirming…" : "Confirm return"}
          </button>
          <button
            type="button"
            onClick={() => void decline()}
            disabled={disabled || busy !== null}
            className="inline-flex min-h-11 items-center rounded-full px-4 text-sm font-semibold text-ink-soft hover:bg-neutral-100 disabled:opacity-60"
          >
            Not now
          </button>
          {error ? (
            <p role="alert" className="w-full text-sm text-danger-700">
              {error}
            </p>
          ) : null}
        </div>
      )}
      <p className="border-t border-line px-4 py-2 text-[0.6875rem] text-muted">
        Policy {quote.policy_version}. Demo store: refunds are simulated.
      </p>
    </section>
  );
}
