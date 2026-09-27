import { InfoIcon, StarFilledIcon } from "@/components/icons";
import { Stars } from "@/components/ui/stars";
import { distributionRows, pluralize } from "@/lib/reviews-query";
import { cn } from "@/lib/cn";
import type { RatingSummary } from "@ai-commerce/contracts";

/**
 * Average, stars, count, and the 5 → 1 distribution. Each row is a toggle button that shows only
 * that star rating, read as one sentence ("5 stars, 8 reviews, 67%"); the bar and the visible
 * numbers are hidden from assistive tech so nothing is announced twice.
 */
export function RatingSummaryPanel({
  summary,
  showSampleNote,
  selected = null,
  onSelect,
}: {
  summary: RatingSummary;
  showSampleNote: boolean;
  selected?: number | null;
  onSelect?: (stars: number | null) => void;
}) {
  const rows = distributionRows(summary);
  const hasReviews = summary.count > 0 && summary.average != null;
  const average = hasReviews ? (summary.average as number).toFixed(1) : null;

  return (
    <div className="rounded-3xl border border-line bg-raised p-6 shadow-xs sm:p-8">
      <h3 className="sr-only">Rating summary</h3>
      {hasReviews ? (
        <div className="flex items-end gap-4">
          <p className="font-display text-6xl font-semibold leading-none tracking-tight text-ink tabular-nums">
            {average}
            <span className="sr-only"> out of 5 stars</span>
          </p>
          <div className="pb-1">
            <Stars rating={summary.average} size="lg" label="" />
            <p className="mt-1.5 text-sm text-muted">Based on {pluralize(summary.count, "review")}</p>
          </div>
        </div>
      ) : (
        <div>
          <p className="font-display text-2xl font-semibold text-ink">No ratings yet</p>
          <Stars rating={0} size="lg" label="" className="mt-2" />
          <p className="mt-1.5 text-sm text-muted">Be the first to rate this item.</p>
        </div>
      )}

      <ul className="mt-7 space-y-1" aria-label="Rating breakdown">
        {rows.map((row) => (
          <li key={row.stars}>
            <button
              type="button"
              aria-pressed={selected === row.stars}
              disabled={!onSelect || row.count === 0}
              onClick={() => onSelect?.(selected === row.stars ? null : row.stars)}
              className={cn(
                "grid w-full grid-cols-[2.25rem_minmax(0,1fr)_2.5rem] items-center gap-3 rounded-lg px-2 py-1.5 text-sm transition-colors enabled:hover:bg-sunken disabled:cursor-default",
                selected === row.stars && "bg-brand-50 ring-1 ring-inset ring-brand-200",
                selected !== null && selected !== row.stars && "opacity-60",
              )}
            >
              <span aria-hidden="true" className="inline-flex items-center gap-1 font-medium tabular-nums text-ink">
                {row.stars}
                <StarFilledIcon className="size-3.5 text-star" />
              </span>
              <span aria-hidden="true" className="relative h-2 overflow-hidden rounded-full bg-sunken">
                <span
                  className="absolute inset-y-0 left-0 rounded-full bg-star transition-[width] duration-700 ease-smooth"
                  style={{ width: `${row.percent}%` }}
                />
              </span>
              <span aria-hidden="true" className="text-right tabular-nums text-muted">
                {row.count}
              </span>
              <span className="sr-only">
                {row.label}
                {onSelect && row.count > 0
                  ? selected === row.stars
                    ? ". Showing only these"
                    : ". Show only these"
                  : ""}
              </span>
            </button>
          </li>
        ))}
      </ul>

      {showSampleNote ? (
        <p className="mt-7 flex gap-2.5 rounded-xl bg-sunken px-4 py-3 text-xs leading-relaxed text-muted">
          <InfoIcon className="mt-px size-4 shrink-0 text-brand-600" />
          <span>
            Reviews labeled <strong className="font-semibold text-ink-soft">Sample review</strong> are demo content
            seeded for this sandbox store, not real shoppers.
          </span>
        </p>
      ) : null}
    </div>
  );
}
