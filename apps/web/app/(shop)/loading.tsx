import { ProductCardSkeleton, Skeleton, SkeletonText } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <div role="status" aria-live="polite">
      <span className="sr-only">Loading…</span>
      <div aria-hidden="true" className="rounded-3xl bg-sunken/70 px-6 py-8 sm:rounded-4xl sm:px-10 sm:py-12">
        <Skeleton className="h-4 w-32 rounded-full" />
        <Skeleton className="mt-7 h-10 w-72 max-w-full rounded-full sm:h-12" />
        <SkeletonText lines={2} className="mt-5 max-w-md" />
      </div>
      <div className="mt-8 sm:mt-10 lg:grid lg:grid-cols-[16.5rem_minmax(0,1fr)] lg:gap-10">
        <div aria-hidden="true" className="hidden space-y-5 rounded-3xl border border-line bg-raised p-5 shadow-xs lg:block">
          <Skeleton className="h-6 w-24 rounded-full" />
          {Array.from({ length: 3 }, (_, i) => (
            <div key={i} className="space-y-3 border-t border-line pt-5">
              <Skeleton className="h-3 w-20 rounded-full" />
              <SkeletonText lines={3} />
            </div>
          ))}
          <Skeleton className="h-11 w-full rounded-full" />
        </div>
        <div>
          <Skeleton className="h-12 w-full rounded-2xl lg:hidden" />
          <div className="mt-6 flex items-center justify-between border-b border-line pb-4 lg:mt-0">
            <Skeleton className="h-4 w-36 rounded-full" />
            <Skeleton className="h-11 w-44 rounded-full" />
          </div>
          <ul aria-hidden="true" className="mt-8 grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 lg:grid-cols-4 lg:gap-x-6">
            {Array.from({ length: 8 }, (_, i) => (
              <li key={i}>
                <ProductCardSkeleton />
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
