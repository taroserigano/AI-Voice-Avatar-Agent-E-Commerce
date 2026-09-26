import { StarFilledIcon } from "@/components/icons";
import { cn } from "@/lib/cn";

type StarSize = "sm" | "md" | "lg";

const starSize: Record<StarSize, string> = { sm: "size-3.5", md: "size-[1.125rem]", lg: "size-6" };
const valueSize: Record<StarSize, string> = { sm: "text-xs", md: "text-sm", lg: "text-base" };

function clampRating(rating: number | null | undefined) {
  if (rating == null || Number.isNaN(rating)) return 0;
  return Math.min(5, Math.max(0, rating));
}

function formatRating(rating: number) {
  return (Math.round(rating * 10) / 10).toFixed(1);
}

function StarRow({ className }: { className: string }) {
  return (
    <>
      {[0, 1, 2, 3, 4].map((i) => (
        <StarFilledIcon key={i} className={className} />
      ))}
    </>
  );
}

/**
 * Read-only star rating with partial fill (pure CSS width overlay: works in Server Components,
 * no SVG ids). Screen readers hear "Rated 4.3 out of 5". Stars are decorative color: when the
 * rating matters, show the number too (`showValue`) or use <RatingBadge>.
 */
export function Stars({
  rating,
  size = "md",
  showValue = false,
  label,
  className,
}: {
  rating: number | null | undefined;
  size?: StarSize;
  /** Show the numeric value after the stars (visible text, hidden from AT to avoid repeats). */
  showValue?: boolean;
  /** Override the screen-reader text. */
  label?: string;
  className?: string;
}) {
  const value = clampRating(rating);
  const text = formatRating(value);
  return (
    <span className={cn("inline-flex items-center gap-1.5 align-middle", className)}>
      <span className="relative inline-flex shrink-0" aria-hidden="true">
        <span className="flex text-star-empty">
          <StarRow className={starSize[size]} />
        </span>
        <span className="absolute inset-y-0 left-0 flex overflow-hidden text-star" style={{ width: `${(value / 5) * 100}%` }}>
          <StarRow className={starSize[size]} />
        </span>
      </span>
      <span className="sr-only">{label ?? `Rated ${text} out of 5`}</span>
      {showValue ? (
        <span aria-hidden="true" className={cn("font-semibold tabular-nums text-ink", valueSize[size])}>
          {text}
        </span>
      ) : null}
    </span>
  );
}

const countFormat = new Intl.NumberFormat("en-US");

/**
 * Compact rating: "★ 4.3 (128)". Renders "No reviews yet" when there are none.
 * `variant="stars"` shows five stars instead of one.
 */
export function RatingBadge({
  average,
  count,
  variant = "compact",
  size = "sm",
  className,
}: {
  average: number | null | undefined;
  count: number | null | undefined;
  variant?: "compact" | "stars";
  size?: StarSize;
  className?: string;
}) {
  if (!count || average == null) {
    return <span className={cn("text-muted", valueSize[size], className)}>No reviews yet</span>;
  }
  const text = formatRating(clampRating(average));
  const countText = countFormat.format(count);
  const reviews = count === 1 ? "review" : "reviews";
  return (
    <span className={cn("inline-flex items-center gap-1 align-middle", valueSize[size], className)}>
      {variant === "stars" ? (
        <Stars rating={average} size={size} label="" className="mr-0.5" />
      ) : (
        <StarFilledIcon className={cn(starSize[size], "text-star")} />
      )}
      <span aria-hidden="true" className="font-semibold tabular-nums text-ink">
        {text}
      </span>
      <span aria-hidden="true" className="tabular-nums text-muted">
        ({countText})
      </span>
      <span className="sr-only">
        Rated {text} out of 5 from {countText} {reviews}
      </span>
    </span>
  );
}
