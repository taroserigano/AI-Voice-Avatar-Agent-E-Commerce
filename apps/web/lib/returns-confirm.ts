"use client";

import { browserApi, errorMessage, goToSignIn } from "./api-browser";

export type ConfirmResult =
  | { ok: true; rmaNumber: string; returnId: string; refundedNowMinor: number; tracking: string | null }
  | { ok: false; status: number; message: string };

/** One idempotency key per quote, kept for the session, so a retry or a double click after a
 * dropped connection repeats the same confirmation instead of making a new one. */
function idempotencyKey(quoteId: string): string {
  const storageKey = `serigan-mart:confirm:${quoteId}`;
  try {
    const existing = window.sessionStorage.getItem(storageKey);
    if (existing) return existing;
    const key = crypto.randomUUID();
    window.sessionStorage.setItem(storageKey, key);
    return key;
  } catch {
    return `${quoteId}-${Date.now()}`;
  }
}

/**
 * Confirm a return quote as the signed-in customer, directly with the store: mint a single-use
 * token for this browser session, then confirm with it. The assistant is never involved; it
 * only hears the outcome afterwards and checks it with the store.
 */
export async function confirmQuote(quoteId: string): Promise<ConfirmResult> {
  const minted = await browserApi.POST("/v1/returns/quotes/{quote_id}/confirmation", {
    params: { path: { quote_id: quoteId } },
  });
  if (minted.response.status === 401) {
    goToSignIn();
    return { ok: false, status: 401, message: "Signed out" };
  }
  if (!minted.data) {
    return { ok: false, status: minted.response.status, message: errorMessage(minted.error, "We couldn't confirm this quote.") };
  }
  const done = await browserApi.POST("/v1/returns/confirm", {
    params: { header: { "Idempotency-Key": idempotencyKey(quoteId) } },
    body: { quote_id: quoteId, confirmation_token: minted.data.confirmation_token },
  });
  if (!done.data) {
    return { ok: false, status: done.response.status, message: errorMessage(done.error, "We couldn't confirm this return.") };
  }
  const ret = done.data.return;
  return {
    ok: true,
    rmaNumber: ret.rma_number,
    returnId: ret.id,
    refundedNowMinor: done.data.refunded_now_minor,
    tracking: done.data.label?.tracking_number ?? null,
  };
}
