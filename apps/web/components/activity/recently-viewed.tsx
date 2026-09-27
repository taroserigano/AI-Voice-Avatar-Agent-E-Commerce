import { SectionHeading } from "@/components/ui/section-heading";
import type { ViewedProduct } from "@/lib/activity";
import { formatMoney } from "@/lib/format";
import Link from "next/link";

/**
 * One entry per product (the first, i.e. newest, wins). Distinct products that would render as
 * identical tiles (same title and art, e.g. two sizes of the same milk) collapse too.
 */
function unique(products: ViewedProduct[]): ViewedProduct[] {
  const seen = new Set<string>();
  return products.filter((p) => {
    const keys = [`id:${p.id}`, `look:${p.title}|${p.image_path}`];
    if (keys.some((k) => seen.has(k))) return false;
    for (const k of keys) seen.add(k);
    return true;
  });
}

/** A compact rail of products the shopper looked at recently (newest first). */
export function RecentlyViewed({ products: all }: { products: ViewedProduct[] }) {
  const products = unique(all);
  if (products.length === 0) return null;
  return (
    <section aria-labelledby="recently-viewed">
      <SectionHeading
        id="recently-viewed"
        eyebrow="Pick up where you left off"
        title="Recently viewed"
        size="sm"
        action={{ href: "/activity", label: "Your activity" }}
      />
      <ul className="-mx-4 mt-5 flex snap-x snap-mandatory gap-3 overflow-x-auto px-4 pb-2 scrollbar-none sm:mx-0 sm:mt-6 sm:grid sm:grid-cols-4 sm:gap-4 sm:overflow-visible sm:px-0 lg:grid-cols-8">
        {products.map((p) => (
          <li key={p.id} className="w-32 shrink-0 snap-start sm:w-auto">
            <Link
              href={`/products/${p.id}`}
              className="group -m-1.5 flex flex-col rounded-2xl p-1.5 transition-[background-color,box-shadow] duration-200 ease-smooth hover:bg-raised hover:shadow-md"
            >
              <span className="block overflow-hidden rounded-xl bg-sunken ring-1 ring-inset ring-line/60">
                {/* eslint-disable-next-line @next/next/no-img-element -- local SVG illustrations */}
                <img
                  src={p.image_path}
                  alt=""
                  width={640}
                  height={640}
                  loading="lazy"
                  className="aspect-square w-full object-cover transition-transform duration-500 ease-smooth group-hover:scale-[1.05] motion-reduce:group-hover:scale-100"
                />
              </span>
              <span className="mt-2 line-clamp-2 px-0.5 text-[0.8125rem] font-medium leading-snug text-ink group-hover:text-brand-700">
                {p.title}
              </span>
              <span className="mt-0.5 px-0.5 text-[0.8125rem] font-semibold tabular-nums text-ink">
                {p.price_minor === null ? (
                  <span className="font-normal text-muted">Unavailable</span>
                ) : p.in_stock ? (
                  formatMoney(p.price_minor, p.currency)
                ) : (
                  <>
                    {formatMoney(p.price_minor, p.currency)}{" "}
                    <span className="font-normal text-muted">· Out of stock</span>
                  </>
                )}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
