import { formatMoney } from "@/lib/format";
import type { ProductSummary, TagOut } from "@ai-commerce/contracts";
import Link from "next/link";

export function TagBadges({ tags, max, className = "" }: { tags: TagOut[]; max?: number; className?: string }) {
  const shown = max === undefined ? tags : tags.slice(0, max);
  if (shown.length === 0) return null;
  return (
    <ul aria-label="Features" className={`flex flex-wrap gap-1 ${className}`}>
      {shown.map((t) => (
        <li key={t.value} className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-900 ring-1 ring-emerald-200">
          {t.label}
        </li>
      ))}
    </ul>
  );
}

export function ProductCard({ product, priority = false }: { product: ProductSummary; priority?: boolean }) {
  return (
    <li className="group flex flex-col rounded-2xl border border-line bg-white p-3 transition-shadow hover:shadow-md">
      <Link href={`/products/${product.id}`} className="flex flex-1 flex-col">
        {/* eslint-disable-next-line @next/next/no-img-element -- local SVG placeholders */}
        <img
          src={product.image_path}
          alt=""
          width={320}
          height={320}
          loading={priority ? "eager" : "lazy"}
          className="aspect-square w-full rounded-xl bg-stone-100 object-cover"
        />
        <p className="mt-3 text-lg font-bold">
          {product.variant_count > 1 ? <span className="text-sm font-medium text-muted">From </span> : null}
          {formatMoney(product.price_minor, product.currency)}
        </p>
        <h3 className="mt-1 line-clamp-2 font-medium group-hover:underline">{product.title}</h3>
        <p className="mt-0.5 text-sm text-muted">{product.brand}</p>
        <TagBadges tags={product.tags} max={3} className="mt-2" />
        <p className={`mt-auto pt-2 text-sm font-medium ${product.in_stock ? "text-emerald-800" : "text-red-800"}`}>
          {product.in_stock ? "In stock" : "Out of stock"}
        </p>
      </Link>
    </li>
  );
}

export function ProductGrid({ products, label }: { products: ProductSummary[]; label: string }) {
  return (
    <ul aria-label={label} className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {products.map((p, i) => (
        <ProductCard key={p.id} product={p} priority={i < 4} />
      ))}
    </ul>
  );
}
