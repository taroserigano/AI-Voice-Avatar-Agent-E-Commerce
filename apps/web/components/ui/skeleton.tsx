import { cn } from "@/lib/cn";

/**
 * Shimmering placeholder block. Decorative (aria-hidden): wrap loading regions in
 * `<div role="status" aria-live="polite"><span className="sr-only">Loading…</span>…</div>`.
 * The sweep stops under prefers-reduced-motion.
 */
export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cn("animate-shimmer rounded-lg bg-shimmer", className)} />;
}

/** A few lines of text-shaped placeholders; the last line is shorter. */
export function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div aria-hidden="true" className={cn("space-y-2.5", className)}>
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton key={i} className={cn("h-3.5 rounded-full", i === lines - 1 && lines > 1 ? "w-3/5" : "w-full")} />
      ))}
    </div>
  );
}

/** Placeholder matching the product card recipe in docs/design/DESIGN.md. */
export function ProductCardSkeleton() {
  return (
    <div aria-hidden="true" className="flex flex-col gap-3 rounded-2xl border border-line bg-raised p-2.5 pb-4">
      <Skeleton className="aspect-square w-full rounded-xl" />
      <div className="space-y-2 px-1.5">
        <Skeleton className="h-3 w-1/3 rounded-full" />
        <Skeleton className="h-4 w-4/5 rounded-full" />
        <Skeleton className="h-5 w-1/4 rounded-full" />
      </div>
    </div>
  );
}
