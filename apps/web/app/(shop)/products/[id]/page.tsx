import { WebVitalsReporter } from "@/components/web-vitals";
import { serverApi, unwrap } from "@/lib/api-server";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { AddToCart } from "./add-to-cart";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

async function load(id: string) {
  if (!UUID_RE.test(id)) notFound();
  const api = await serverApi();
  const result = await api.GET("/v1/products/{product_id}", { params: { path: { product_id: id } } });
  if (result.response.status === 404) notFound();
  return unwrap(result);
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const product = await load((await params).id);
  return { title: product.title };
}

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const product = await load((await params).id);
  return (
    <div>
      <WebVitalsReporter route="product" />
      <nav aria-label="Breadcrumb" className="text-sm text-muted">
        <ol className="flex flex-wrap gap-1">
          <li>
            <Link href="/" className="underline underline-offset-2 hover:text-ink">
              Home
            </Link>{" "}
            /
          </li>
          <li>
            <Link href={`/c/${product.category.slug}`} className="underline underline-offset-2 hover:text-ink">
              {product.category.name}
            </Link>{" "}
            /
          </li>
          <li aria-current="page" className="text-ink">
            {product.title}
          </li>
        </ol>
      </nav>

      <div className="mt-4 grid gap-8 md:grid-cols-2">
        {/* eslint-disable-next-line @next/next/no-img-element -- local SVG placeholders */}
        <img
          src={product.image_path}
          alt={`${product.title} (illustration)`}
          width={640}
          height={640}
          className="aspect-square w-full rounded-3xl border border-line bg-white object-cover"
        />
        <div>
          <p className="font-medium text-brand-700">{product.brand}</p>
          <h1 className="mt-1 text-3xl font-bold leading-tight">{product.title}</h1>
          <AddToCart product={product} />
          <section aria-labelledby="about" className="mt-8 border-t border-line pt-6">
            <h2 id="about" className="text-lg font-semibold">
              About this item
            </h2>
            <p className="mt-2 leading-relaxed text-stone-700">{product.description}</p>
            {product.category.policy_class === "final_sale" ? (
              <p className="mt-3 text-sm font-medium text-red-800">Final sale: this item can&apos;t be returned.</p>
            ) : product.category.policy_class === "inspection" ? (
              <p className="mt-3 text-sm text-muted">Returnable within 30 days of delivery; refunded after inspection.</p>
            ) : (
              <p className="mt-3 text-sm text-muted">Returnable within 30 days of delivery.</p>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
