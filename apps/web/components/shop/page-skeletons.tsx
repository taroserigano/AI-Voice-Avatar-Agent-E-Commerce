import { ProductCardSkeleton, Skeleton, SkeletonText } from "@/components/ui/skeleton";
import type { ReactNode } from "react";

/*
 * Route loading states (loading.tsx). Each one lives in its own route segment, never in (shop)/
 * itself: a loading boundary makes the response start streaming as 200 before the page runs, so
 * a notFound() below it could only ever be a "soft" 404. Routes that can 404 (products/[id],
 * orders/[id], c/[slug]) check their resource in a layout above their own loading.tsx instead.
 */

function Loading({ children }: { children: ReactNode }) {
  return (
    <div role="status" aria-live="polite">
      <span className="sr-only">Loading…</span>
      {children}
    </div>
  );
}

/** Search results and department pages: heading band, filter rail, product grid. */
export function ListingSkeleton() {
  return (
    <Loading>
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
    </Loading>
  );
}

/** Product detail: breadcrumb, big image, title/price/buy box. */
export function ProductSkeleton() {
  return (
    <Loading>
      <div aria-hidden="true" className="pt-2 sm:pt-4">
        <Skeleton className="h-4 w-64 max-w-full rounded-full" />
        <div className="mt-6 grid gap-8 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] lg:gap-16">
          <Skeleton className="aspect-square w-full rounded-3xl sm:rounded-4xl" />
          <div>
            <Skeleton className="h-3 w-32 rounded-full" />
            <Skeleton className="mt-4 h-9 w-4/5 rounded-full" />
            <Skeleton className="mt-3 h-9 w-3/5 rounded-full" />
            <Skeleton className="mt-5 h-4 w-40 rounded-full" />
            <div className="mt-6 space-y-5 rounded-3xl border border-line bg-raised p-6 shadow-xs">
              <Skeleton className="h-9 w-28 rounded-full" />
              <SkeletonText lines={2} className="max-w-xs" />
              <Skeleton className="h-13 w-full rounded-full" />
            </div>
          </div>
        </div>
      </div>
    </Loading>
  );
}

/** Order detail: heading and total, delivery card, payment summary. */
export function OrderSkeleton() {
  return (
    <Loading>
      <div aria-hidden="true" className="pt-2 sm:pt-4">
        <Skeleton className="h-4 w-40 rounded-full" />
        <div className="mt-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <Skeleton className="h-9 w-64 max-w-full rounded-full" />
            <Skeleton className="mt-3 h-4 w-44 rounded-full" />
          </div>
          <Skeleton className="h-9 w-28 rounded-full" />
        </div>
        <div className="mt-8 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_23.5rem] lg:gap-10">
          <div className="space-y-6 rounded-3xl border border-line bg-raised p-6 shadow-xs sm:p-7">
            <Skeleton className="h-7 w-72 max-w-full rounded-full" />
            <Skeleton className="h-16 w-full rounded-2xl" />
            <SkeletonText lines={3} />
          </div>
          <div className="space-y-4 rounded-3xl border border-line bg-raised p-6 shadow-xs">
            <Skeleton className="h-6 w-40 rounded-full" />
            <SkeletonText lines={4} />
          </div>
        </div>
      </div>
    </Loading>
  );
}

/** Account and support pages: a heading, an intro line, and a couple of content blocks. */
export function PageSkeleton() {
  return (
    <Loading>
      <div aria-hidden="true" className="sm:pt-2">
        <Skeleton className="h-9 w-60 max-w-full rounded-full sm:h-10" />
        <Skeleton className="mt-4 h-4 w-96 max-w-full rounded-full" />
        <div className="mt-8 grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_20rem] lg:gap-10">
          <div className="space-y-3">
            {Array.from({ length: 4 }, (_, i) => (
              <div key={i} className="flex items-center gap-4 rounded-3xl border border-line bg-raised p-5 shadow-xs">
                <Skeleton className="size-12 shrink-0 rounded-xl" />
                <SkeletonText lines={2} className="flex-1" />
              </div>
            ))}
          </div>
          <div className="hidden space-y-4 rounded-3xl border border-line bg-raised p-5 shadow-xs lg:block">
            <Skeleton className="h-6 w-32 rounded-full" />
            <SkeletonText lines={3} />
          </div>
        </div>
      </div>
    </Loading>
  );
}

/** Home below the hero: department tiles, then a product row. */
export function HomeSectionsSkeleton() {
  return (
    <Loading>
      <div aria-hidden="true" className="space-y-16 sm:space-y-24">
        <div>
          <Skeleton className="h-8 w-64 max-w-full rounded-full" />
          <div className="mt-6 grid grid-cols-2 gap-3 sm:mt-8 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4">
            {Array.from({ length: 8 }, (_, i) => (
              <Skeleton key={i} className="h-44 rounded-3xl sm:h-50" />
            ))}
          </div>
        </div>
        <ul className="grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 lg:grid-cols-4 lg:gap-x-6">
          {Array.from({ length: 4 }, (_, i) => (
            <li key={i}>
              <ProductCardSkeleton />
            </li>
          ))}
        </ul>
      </div>
    </Loading>
  );
}
