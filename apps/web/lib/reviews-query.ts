"use client";

import type { RatingSummary, ReviewIn, ReviewOut, ReviewPage, ReviewSort } from "@ai-commerce/contracts";
import { keepPreviousData, useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { browserApi, errorMessage, goToSignIn } from "./api-browser";

// ---------------------------------------------------------------------------------------------
// Pure helpers (unit tested in reviews-query.test.ts)
// ---------------------------------------------------------------------------------------------

export const REVIEW_PAGE_SIZE = 10;
/** Mirrors the API limits in services/commerce/src/commerce/reviews/schemas.py. */
export const TITLE_MAX = 120;
export const BODY_MAX = 2000;

export const REVIEW_SORTS: { value: ReviewSort; label: string }[] = [
  { value: "newest", label: "Newest" },
  { value: "highest", label: "Highest rated" },
  { value: "lowest", label: "Lowest rated" },
];

const RATING_WORDS = ["Poor", "Fair", "Good", "Very good", "Excellent"] as const;

/** 1 → "Poor" … 5 → "Excellent". Empty string outside 1–5. */
export function ratingWord(stars: number): string {
  return RATING_WORDS[stars - 1] ?? "";
}

export function pluralize(count: number, one: string, many = `${one}s`): string {
  return `${count.toLocaleString("en-US")} ${count === 1 ? one : many}`;
}

/** The next page to request, or undefined when every review has been loaded. */
export function nextReviewPage(last: Pick<ReviewPage, "page" | "page_size" | "total" | "items">): number | undefined {
  if (last.items.length === 0) return undefined;
  return last.page * last.page_size < last.total ? last.page + 1 : undefined;
}

/**
 * Flatten loaded pages into one list. Offsets can shift when someone posts a review between
 * page loads, so the same review may come back twice; keep the first copy.
 */
export function mergeReviewPages(pages: readonly Pick<ReviewPage, "items">[]): ReviewOut[] {
  const seen = new Set<string>();
  const out: ReviewOut[] = [];
  for (const page of pages) {
    for (const review of page.items) {
      if (seen.has(review.id)) continue;
      seen.add(review.id);
      out.push(review);
    }
  }
  return out;
}

export type DistributionRow = { stars: number; count: number; percent: number; label: string };

/** Five rows, 5 → 1 stars, each with a whole-number percent and a screen-reader sentence. */
export function distributionRows(summary: Pick<RatingSummary, "count" | "distribution">): DistributionRow[] {
  const byStars = new Map(summary.distribution.map((b) => [b.stars, b.count]));
  return [5, 4, 3, 2, 1].map((stars) => {
    const count = byStars.get(stars) ?? 0;
    const percent = summary.count > 0 ? Math.round((count / summary.count) * 100) : 0;
    return {
      stars,
      count,
      percent,
      label: `${pluralize(stars, "star")}, ${pluralize(count, "review")}, ${percent}%`,
    };
  });
}

export type ReviewDraft = { rating: number | null; title: string; body: string };
export type ReviewErrors = Partial<Record<keyof ReviewDraft, string>>;

/** Client-side checks that mirror the API; the server still validates everything. */
export function validateReview(
  draft: ReviewDraft,
): { ok: true; value: ReviewIn } | { ok: false; errors: ReviewErrors } {
  const errors: ReviewErrors = {};
  const title = draft.title.trim();
  const body = draft.body.trim();
  if (draft.rating == null || !Number.isInteger(draft.rating) || draft.rating < 1 || draft.rating > 5) {
    errors.rating = "Choose a star rating from 1 to 5.";
  }
  if (title.length > TITLE_MAX) errors.title = `Keep the title to ${TITLE_MAX} characters or fewer.`;
  if (body.length > BODY_MAX) errors.body = `Keep the review to ${BODY_MAX.toLocaleString("en-US")} characters or fewer.`;
  if (Object.keys(errors).length > 0) return { ok: false, errors };
  return { ok: true, value: { rating: draft.rating as number, title: title || null, body: body || null } };
}

/** The draft to start editing from: the shopper's saved review, or an empty form. */
export function draftFrom(review: Pick<ReviewOut, "rating" | "title" | "body"> | null | undefined): ReviewDraft {
  return { rating: review?.rating ?? null, title: review?.title ?? "", body: review?.body ?? "" };
}

/** "Alice W." → "AW"; "Serigan Mart shopper" → "SS"; "" → "?". */
export function initials(name: string): string {
  const letters = name
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part.replace(/[^\p{L}\p{N}]/gu, "").charAt(0))
    .filter(Boolean);
  const first = letters[0];
  if (!first) return "?";
  const last = letters.length > 1 ? letters[letters.length - 1] : "";
  return `${first}${last}`.toUpperCase();
}

/** True when the review changed meaningfully after it was first posted (more than a minute later). */
export function wasEdited(review: Pick<ReviewOut, "created_at" | "updated_at">): boolean {
  return Date.parse(review.updated_at) - Date.parse(review.created_at) > 60_000;
}

const dateFormat = new Intl.DateTimeFormat("en-US", { month: "long", day: "numeric", year: "numeric" });

/** "August 6, 2026" in the viewer's time zone (render with suppressHydrationWarning). */
export function formatReviewDate(iso: string): string {
  const time = Date.parse(iso);
  return Number.isNaN(time) ? "" : dateFormat.format(time);
}

// ---------------------------------------------------------------------------------------------
// Queries and mutations
// ---------------------------------------------------------------------------------------------

export class ReviewApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

function fail(result: { error?: unknown; response: Response }): never {
  if (result.response.status === 401) {
    goToSignIn();
    throw new ReviewApiError("Your session ended. Taking you to sign in…", 401);
  }
  throw new ReviewApiError(errorMessage(result.error), result.response.status);
}

async function check<T>(result: { data?: T; error?: unknown; response: Response }): Promise<T> {
  if (result.data === undefined) fail(result);
  return result.data;
}

/** Every reviews query for a product (all sorts), for invalidation. */
export function reviewsKey(productId: string, sort?: ReviewSort) {
  return sort ? (["reviews", productId, sort] as const) : (["reviews", productId] as const);
}

/**
 * Reviews for one product and sort, 10 at a time. `initialData` is the server-rendered first page
 * of the default sort ("newest"), so the section paints without a client round trip.
 */
export function useReviews(productId: string, sort: ReviewSort, initialData?: ReviewPage) {
  return useInfiniteQuery({
    queryKey: reviewsKey(productId, sort),
    queryFn: async ({ pageParam }) =>
      check(
        await browserApi.GET("/v1/products/{product_id}/reviews", {
          params: { path: { product_id: productId }, query: { sort, page: pageParam, page_size: REVIEW_PAGE_SIZE } },
        }),
      ),
    initialPageParam: 1,
    getNextPageParam: nextReviewPage,
    initialData: initialData && sort === "newest" ? { pages: [initialData], pageParams: [1] } : undefined,
    // Keep the old list on screen while a new sort loads.
    placeholderData: keepPreviousData,
  });
}

/** Create or update the signed-in shopper's review (an idempotent upsert on the API). */
export function useSaveReview(productId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async (body: ReviewIn) =>
      check(
        await browserApi.PUT("/v1/products/{product_id}/reviews/mine", {
          params: { path: { product_id: productId } },
          body,
        }),
      ),
    // Returning the promise makes mutateAsync wait until the list and summary are fresh.
    onSuccess: () => client.invalidateQueries({ queryKey: reviewsKey(productId) }),
  });
}

export function useDeleteReview(productId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const result = await browserApi.DELETE("/v1/products/{product_id}/reviews/mine", {
        params: { path: { product_id: productId } },
      });
      if (!result.response.ok) fail(result);
    },
    onSuccess: () => client.invalidateQueries({ queryKey: reviewsKey(productId) }),
  });
}
