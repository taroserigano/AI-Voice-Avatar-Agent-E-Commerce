import { CheckIcon, UserIcon } from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import { Stars } from "@/components/ui/stars";
import { cn } from "@/lib/cn";
import { formatReviewDate, initials, ratingWord, wasEdited } from "@/lib/reviews-query";
import type { ReviewOut } from "@ai-commerce/contracts";

// Documented text pairs only (DESIGN.md §2): every tint keeps its ink ≥ 7:1.
const AVATAR_TINTS = [
  "bg-brand-100 text-brand-800",
  "bg-accent-100 text-accent-800",
  "bg-success-50 text-success-800",
  "bg-info-50 text-info-800",
  "bg-brand-50 text-brand-900",
];

function tintFor(name: string) {
  let hash = 0;
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  return AVATAR_TINTS[hash % AVATAR_TINTS.length];
}

export function ReviewAvatar({ name, mine = false, className }: { name: string; mine?: boolean; className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "grid size-11 shrink-0 place-items-center rounded-full text-sm font-semibold tracking-wide ring-4 ring-raised",
        mine ? "bg-brand-600 text-white" : tintFor(name),
        className,
      )}
    >
      {initials(name) === "?" ? <UserIcon className="size-5" /> : initials(name)}
    </span>
  );
}

export const SAMPLE_NOTE = "Demo content seeded for the sandbox store";

export function ReviewBadges({ review }: { review: ReviewOut }) {
  if (!review.is_mine && !review.verified_purchase && !review.is_sample) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {review.is_mine ? <Badge tone="brand">Your review</Badge> : null}
      {review.verified_purchase ? (
        <Badge tone="success">
          <CheckIcon />
          Verified purchase
        </Badge>
      ) : null}
      {review.is_sample ? (
        <Badge tone="neutral">
          <span title={SAMPLE_NOTE}>Sample review</span>
          <span className="sr-only">: {SAMPLE_NOTE.toLowerCase()}</span>
        </Badge>
      ) : null}
    </div>
  );
}

/**
 * One review. Title and body are shopper-written, untrusted text: they render as plain React text
 * (never as HTML), with line breaks kept by `whitespace-pre-line`.
 */
export function ReviewItem({ review, headingLevel = "h4" }: { review: ReviewOut; headingLevel?: "h3" | "h4" }) {
  const Heading = headingLevel;
  const edited = wasEdited(review);
  return (
    <article className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-4 sm:gap-x-5">
      <ReviewAvatar name={review.author_name} mine={review.is_mine} />
      <div className="min-w-0">
        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
          <p className="min-w-0 text-sm leading-tight">
            <span className="block font-semibold text-ink">{review.author_name}</span>
            <span className="mt-0.5 block text-muted">
              {/* The browser formats in the viewer's time zone; the server's guess may differ. */}
              <time dateTime={review.created_at} suppressHydrationWarning>
                {formatReviewDate(review.created_at)}
              </time>
              {edited ? <span> · Edited</span> : null}
            </span>
          </p>
          <ReviewBadges review={review} />
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1">
          <Stars rating={review.rating} size="md" label={`Rated ${review.rating} out of 5, ${ratingWord(review.rating)}`} />
          {review.title ? (
            <Heading className="font-sans text-base font-semibold leading-snug text-ink">{review.title}</Heading>
          ) : (
            <span aria-hidden="true" className="text-sm font-medium text-ink-soft">
              {ratingWord(review.rating)}
            </span>
          )}
        </div>

        {review.body ? (
          <p className="mt-2.5 max-w-prose whitespace-pre-line break-words leading-relaxed text-ink-soft">{review.body}</p>
        ) : null}
      </div>
    </article>
  );
}
