import { StarFilledIcon } from "@/components/icons";
import { formatMoney } from "@/lib/format";
import type { ProductSummary } from "@ai-commerce/contracts";
import Link from "next/link";

/**
 * A compact, ranked "Top rated in <department>" row for a department landing page. Each item is
 * one link (stretched over the tile). Scrolls sideways on phones instead of stacking.
 */
export function TopRatedStrip({ department, items }: { department: string; items: ProductSummary[] }) {
  if (items.length === 0) return null;
  return (
    <section aria-labelledby="top-rated-heading" className="mt-8 sm:mt-10">
      <div className="flex items-baseline justify-between gap-4">
        <h2 id="top-rated-heading" className="font-display text-xl font-semibold text-ink sm:text-2xl">
          Top rated in {department}
        </h2>
        <p className="hidden text-sm text-muted sm:block">By shopper reviews</p>
      </div>
      <ol className="-mx-4 mt-4 flex snap-x snap-mandatory gap-3 overflow-x-auto px-4 pb-2 [scrollbar-width:thin] sm:mx-0 sm:grid sm:snap-none sm:grid-cols-2 sm:overflow-visible sm:px-0 sm:pb-0 lg:grid-cols-3 xl:grid-cols-6">
        {items.map((p, i) => (
          <li
            key={p.id}
            className="group relative flex w-64 shrink-0 snap-start items-center gap-3 rounded-2xl border border-line bg-raised p-2.5 shadow-xs transition-[box-shadow,border-color] duration-200 has-[a:focus-visible]:outline-2 has-[a:focus-visible]:outline-offset-2 has-[a:focus-visible]:outline-focus hover:border-line-strong hover:shadow-md sm:w-auto xl:flex-col xl:items-stretch"
          >
            <div className="relative shrink-0">
              {/* eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations */}
              <img
                src={p.image_path}
                alt=""
                width={640}
                height={640}
                loading="lazy"
                decoding="async"
                className="size-16 rounded-xl bg-sunken object-cover ring-1 ring-inset ring-line/60 xl:aspect-square xl:size-auto xl:w-full"
              />
              <span className="absolute -left-1.5 -top-1.5 grid size-6 place-items-center rounded-full bg-ink font-display text-xs font-semibold tabular-nums text-white shadow-sm">
                <span className="sr-only">Number </span>
                {i + 1}
              </span>
            </div>
            <div className="min-w-0 flex-1 xl:px-1 xl:pb-1">
              <h3 className="line-clamp-2 text-sm font-medium leading-snug text-ink">
                <Link
                  href={`/products/${p.id}`}
                  className="outline-none after:absolute after:inset-0 after:rounded-2xl after:content-[''] group-hover:text-brand-700"
                >
                  {p.title}
                </Link>
              </h3>
              <p className="mt-1 flex items-center gap-2 text-xs text-muted">
                <span className="inline-flex items-center gap-0.5 font-semibold text-ink">
                  <StarFilledIcon className="size-3.5 text-star" />
                  {p.rating_average?.toFixed(1)}
                  <span className="sr-only"> out of 5 stars from</span>
                </span>
                <span>
                  ({p.rating_count}
                  <span className="sr-only"> reviews</span>)
                </span>
                <span aria-hidden="true">·</span>
                <span className="font-semibold tabular-nums text-ink">{formatMoney(p.price_minor, p.currency)}</span>
              </p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
