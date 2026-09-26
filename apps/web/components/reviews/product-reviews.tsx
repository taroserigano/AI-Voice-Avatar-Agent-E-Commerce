"use client";

import { ChatIcon, PencilIcon, TrashIcon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { Notice } from "@/components/ui/notice";
import { cn } from "@/lib/cn";
import {
  REVIEW_PAGE_SIZE,
  REVIEW_SORTS,
  ReviewApiError,
  draftFrom,
  formatReviewDate,
  mergeReviewPages,
  pluralize,
  ratingWord,
  useDeleteReview,
  useReviews,
  useSaveReview,
} from "@/lib/reviews-query";
import type { ReviewIn, ReviewOut, ReviewPage, ReviewSort } from "@ai-commerce/contracts";
import { Stars } from "@/components/ui/stars";
import { useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState, type Ref } from "react";
import { PillSelect } from "./pill-select";
import { RatingSummaryPanel } from "./rating-summary";
import { ReviewAvatar, ReviewBadges, ReviewItem } from "./review-item";
import { ReviewForm } from "./review-form";

// Stagger the first eight reviews of each loaded page (static class names so Tailwind emits them).
const ENTRANCE = [
  "animate-fade-up",
  "animate-fade-up animation-delay-40",
  "animate-fade-up animation-delay-80",
  "animate-fade-up animation-delay-120",
  "animate-fade-up animation-delay-160",
  "animate-fade-up animation-delay-200",
  "animate-fade-up animation-delay-240",
  "animate-fade-up animation-delay-280",
];

type Mode = "idle" | "writing" | "editing" | "confirm-delete";
type Status = { tone: "success" | "error"; text: string };
type FocusTarget = "write" | "edit" | "status" | "confirm" | null;

/**
 * The "Ratings & reviews" section: summary, the shopper's own review (write / edit / delete),
 * and the paginated review list. The first page arrives server-rendered as `initialData`.
 */
export function ProductReviews({
  productId,
  productTitle,
  initialData,
}: {
  productId: string;
  productTitle: string;
  initialData?: ReviewPage;
}) {
  const router = useRouter();
  const uid = useId();
  const [sort, setSort] = useState<ReviewSort>("newest");
  const reviews = useReviews(productId, sort, initialData);
  const save = useSaveReview(productId);
  const remove = useDeleteReview(productId);

  const [mode, setMode] = useState<Mode>("idle");
  const [status, setStatus] = useState<Status | null>(null);
  const [formError, setFormError] = useState<string>();

  const writeRef = useRef<HTMLButtonElement>(null);
  const editRef = useRef<HTMLButtonElement>(null);
  const keepRef = useRef<HTMLButtonElement>(null);
  const statusRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLOListElement>(null);
  const focusNext = useRef<FocusTarget>(null);
  const focusReviewIndex = useRef<number | null>(null);

  const pages = reviews.data?.pages ?? (initialData ? [initialData] : []);
  const first = pages[0];
  const summary = first?.summary;
  const mine = first?.my_review ?? null;
  const items = mergeReviewPages(pages);
  const total = first?.total ?? 0;

  // Move focus after the DOM for the new mode exists (WCAG 2.4.3: focus follows the task).
  useEffect(() => {
    const target = focusNext.current;
    focusNext.current = null;
    if (target === "write") writeRef.current?.focus();
    else if (target === "edit") editRef.current?.focus();
    else if (target === "confirm") keepRef.current?.focus();
    else if (target === "status") statusRef.current?.focus();
  });

  // After "Show more", land on the first newly loaded review.
  useEffect(() => {
    const index = focusReviewIndex.current;
    if (index == null || reviews.isFetchingNextPage) return;
    const node = listRef.current?.querySelectorAll<HTMLElement>("[data-review]")[index];
    if (node) {
      focusReviewIndex.current = null;
      node.focus();
    }
  });

  function open(nextMode: "writing" | "editing") {
    setStatus(null);
    setFormError(undefined);
    setMode(nextMode);
  }

  function cancel() {
    focusNext.current = mode === "editing" ? "edit" : "write";
    setFormError(undefined);
    setMode("idle");
  }

  async function submit(body: ReviewIn) {
    setFormError(undefined);
    try {
      await save.mutateAsync(body);
      setMode("idle");
      setStatus({ tone: "success", text: "Thanks — your review is live." });
      focusNext.current = "status";
      router.refresh(); // the buy box rating is server-rendered
    } catch (error) {
      if (error instanceof ReviewApiError && error.status === 401) return; // redirecting to sign-in
      setFormError(error instanceof Error ? error.message : "Something went wrong. Please try again.");
    }
  }

  async function confirmDelete() {
    try {
      await remove.mutateAsync();
      setMode("idle");
      setStatus({ tone: "success", text: "Your review was deleted." });
      focusNext.current = "status";
      router.refresh();
    } catch (error) {
      if (error instanceof ReviewApiError && error.status === 401) return;
      setMode("idle");
      setStatus({ tone: "error", text: error instanceof Error ? error.message : "Couldn't delete your review." });
      focusNext.current = "status";
    }
  }

  function showMore() {
    focusReviewIndex.current = items.length;
    void reviews.fetchNextPage();
  }

  const sortId = `${uid}-sort`;
  const listHeadingId = `${uid}-list`;
  const busy = reviews.isFetching && !reviews.isFetchingNextPage && reviews.isPlaceholderData;

  return (
    <section id="reviews" aria-labelledby="reviews-heading" className="scroll-mt-36">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="max-w-2xl">
          <p className="mb-2 text-xs font-semibold uppercase tracking-eyebrow text-brand-700">From the community</p>
          <h2 id="reviews-heading" className="font-display text-2xl font-semibold text-ink sm:text-3xl">
            Ratings &amp; reviews
          </h2>
          <p className="mt-2 text-base text-muted">Honest takes from Serigan Mart shoppers, good and bad.</p>
        </div>
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,23rem)_minmax(0,1fr)] lg:gap-12 xl:gap-16">
        <div className="lg:sticky lg:top-36 lg:self-start">
          {summary ? (
            <RatingSummaryPanel summary={summary} showSampleNote={items.some((r) => r.is_sample)} />
          ) : (
            <div className="h-80 animate-shimmer rounded-3xl bg-shimmer" aria-hidden="true" />
          )}
        </div>

        <div className="min-w-0">
          {/* Status for write/delete results: a polite live region that also takes focus. */}
          <div
            ref={statusRef}
            tabIndex={-1}
            aria-live="polite"
            className="rounded-xl outline-none focus-visible:outline-2 focus-visible:outline-offset-2 empty:hidden [&:not(:empty)]:mb-5"
          >
            {status ? (
              <Notice tone={status.tone} role={status.tone === "error" ? "alert" : "note"} className="animate-fade-in">
                {status.text}
              </Notice>
            ) : null}
          </div>

          {mode === "writing" || mode === "editing" ? (
            <ReviewForm
              mode={mode === "editing" ? "edit" : "create"}
              productTitle={productTitle}
              initial={draftFrom(mode === "editing" ? mine : null)}
              pending={save.isPending}
              serverError={formError}
              onSubmit={submit}
              onCancel={cancel}
            />
          ) : mine ? (
            <MyReviewCard
              review={mine}
              confirming={mode === "confirm-delete"}
              deleting={remove.isPending}
              editRef={editRef}
              keepRef={keepRef}
              onEdit={() => open("editing")}
              onAskDelete={() => {
                setStatus(null);
                focusNext.current = "confirm";
                setMode("confirm-delete");
              }}
              onKeep={() => {
                focusNext.current = "edit";
                setMode("idle");
              }}
              onDelete={confirmDelete}
            />
          ) : (
            <WritePrompt buttonRef={writeRef} hasReviews={total > 0} onWrite={() => open("writing")} />
          )}

          <div className="mt-10 flex flex-wrap items-end justify-between gap-x-6 gap-y-3 border-b border-line pb-4">
            <h3 id={listHeadingId} className="font-display text-xl font-semibold text-ink">
              {total > 0 ? pluralize(total, "review") : "Reviews"}
            </h3>
            {total > 1 ? (
              <div className="flex items-center gap-3">
                <label htmlFor={sortId} className="text-sm font-medium text-muted">
                  Sort by
                </label>
                <PillSelect
                  id={sortId}
                  value={sort}
                  onChange={(e) => setSort(e.target.value as ReviewSort)}
                  className="min-h-11 w-auto py-0 text-sm"
                >
                  {REVIEW_SORTS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </PillSelect>
              </div>
            ) : null}
          </div>

          {reviews.isError && items.length === 0 ? (
            <Notice tone="error" className="mt-6">
              {reviews.error instanceof Error ? reviews.error.message : "Couldn't load reviews."}{" "}
              <button type="button" onClick={() => reviews.refetch()} className="font-semibold underline underline-offset-4">
                Try again
              </button>
            </Notice>
          ) : items.length === 0 && !reviews.isFetching ? (
            <EmptyReviews />
          ) : (
            <ol
              ref={listRef}
              aria-labelledby={listHeadingId}
              aria-busy={busy || undefined}
              className={cn("divide-y divide-line transition-opacity duration-200", busy && "opacity-60")}
            >
              {items.map((review, i) => (
                <li
                  key={review.id}
                  data-review
                  tabIndex={-1}
                  className={cn(
                    "rounded-sm py-7 outline-offset-4",
                    ENTRANCE[i % REVIEW_PAGE_SIZE],
                  )}
                >
                  <ReviewItem review={review} />
                </li>
              ))}
            </ol>
          )}

          {reviews.hasNextPage ? (
            <div className="mt-2 flex flex-col items-center gap-3 border-t border-line pt-8">
              <p className="text-sm text-muted">
                Showing {items.length} of {total.toLocaleString("en-US")}
              </p>
              <Button variant="outline" onClick={showMore} loading={reviews.isFetchingNextPage}>
                {reviews.isFetchingNextPage ? "Loading reviews…" : "Show more reviews"}
              </Button>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function WritePrompt({
  buttonRef,
  hasReviews,
  onWrite,
}: {
  buttonRef: Ref<HTMLButtonElement>;
  hasReviews: boolean;
  onWrite: () => void;
}) {
  return (
    <div className="relative isolate flex flex-col gap-5 overflow-hidden rounded-3xl bg-mesh-light p-6 sm:flex-row sm:items-center sm:justify-between sm:p-8">
      <div className="flex items-start gap-4">
        <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-raised text-brand-600 shadow-md">
          <ChatIcon className="size-6" />
        </span>
        <div>
          <h3 className="font-display text-lg font-semibold text-ink sm:text-xl">
            {hasReviews ? "Tried it? Share your thoughts" : "Be the first to review"}
          </h3>
          <p className="mt-1 text-sm text-muted">Rate it from 1 to 5 stars and help other shoppers decide.</p>
        </div>
      </div>
      <Button ref={buttonRef} variant="outline" onClick={onWrite} className="shrink-0 self-start sm:self-center">
        <PencilIcon className="size-4" />
        Write a review
      </Button>
    </div>
  );
}

function MyReviewCard({
  review,
  confirming,
  deleting,
  editRef,
  keepRef,
  onEdit,
  onAskDelete,
  onKeep,
  onDelete,
}: {
  review: ReviewOut;
  confirming: boolean;
  deleting: boolean;
  editRef: Ref<HTMLButtonElement>;
  keepRef: Ref<HTMLButtonElement>;
  onEdit: () => void;
  onAskDelete: () => void;
  onKeep: () => void;
  onDelete: () => void;
}) {
  const confirmId = useId();
  return (
    <div className="rounded-3xl border border-brand-200 bg-brand-50 p-5 shadow-xs sm:p-7">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <ReviewAvatar name={review.author_name} mine className="ring-brand-50" />
          <div>
            <h3 className="font-display text-lg font-semibold text-ink">Your review</h3>
            <p className="text-sm text-muted">
              Posted{" "}
              <time dateTime={review.created_at} suppressHydrationWarning>
                {formatReviewDate(review.created_at)}
              </time>{" "}
              as {review.author_name}
            </p>
          </div>
        </div>
        <ReviewBadges review={{ ...review, is_mine: false }} />
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1">
        <Stars rating={review.rating} size="md" label={`You rated it ${review.rating} out of 5, ${ratingWord(review.rating)}`} />
        {review.title ? (
          <p className="font-semibold text-ink">{review.title}</p>
        ) : (
          <p aria-hidden="true" className="text-sm font-medium text-ink-soft">
            {ratingWord(review.rating)}
          </p>
        )}
      </div>
      {review.body ? (
        <p className="mt-2 max-w-prose whitespace-pre-line break-words leading-relaxed text-ink-soft">{review.body}</p>
      ) : null}

      {confirming ? (
        <div
          role="group"
          aria-labelledby={confirmId}
          className="mt-5 flex animate-fade-in flex-col gap-3 rounded-2xl border border-danger-200 bg-raised p-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <p id={confirmId} className="text-sm text-ink">
            <strong className="font-semibold">Delete your review?</strong>{" "}
            <span className="text-muted">This removes your rating too and can&apos;t be undone.</span>
          </p>
          <div className="flex shrink-0 gap-2">
            <Button ref={keepRef} variant="ghost" onClick={onKeep} disabled={deleting}>
              Keep it
            </Button>
            <Button variant="danger" onClick={onDelete} loading={deleting}>
              {deleting ? "Deleting…" : "Delete review"}
            </Button>
          </div>
        </div>
      ) : (
        <div className="mt-5 flex flex-wrap gap-2">
          <Button ref={editRef} variant="outline" onClick={onEdit}>
            <PencilIcon className="size-4" />
            Edit
            <span className="sr-only"> your review</span>
          </Button>
          <Button variant="ghost" onClick={onAskDelete} className="text-danger-700 hover:bg-danger-50">
            <TrashIcon className="size-4" />
            Delete
            <span className="sr-only"> your review</span>
          </Button>
        </div>
      )}
    </div>
  );
}

function EmptyReviews() {
  return (
    <div className="mt-6 flex flex-col items-center rounded-3xl border border-dashed border-line-strong px-6 py-14 text-center">
      <span className="relative grid size-16 place-items-center rounded-2xl bg-accent-50 text-star shadow-xs">
        <Stars rating={0} size="sm" label="" className="absolute -top-2.5 rounded-full bg-raised px-1.5 py-0.5 shadow-xs" />
        <ChatIcon className="size-8 text-accent-700" />
      </span>
      <p className="mt-6 font-display text-xl font-semibold text-ink">No reviews yet.</p>
      <p className="mt-2 max-w-sm text-muted">Share your thoughts — you&apos;ll be the first.</p>
    </div>
  );
}
