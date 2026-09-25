import { ProductGrid } from "@/components/shop/product-card";
import { WebVitalsReporter } from "@/components/web-vitals";
import { getMe, serverApi, unwrap } from "@/lib/api-server";
import Link from "next/link";

export default async function HomePage() {
  const user = await getMe();
  const api = await serverApi();
  const [categories, featured] = await Promise.all([
    api.GET("/v1/categories").then(unwrap),
    api.GET("/v1/products", { params: { query: { in_stock: true, sort: "newest", page_size: 8 } } }).then(unwrap),
  ]);

  return (
    <div className="space-y-10">
      <WebVitalsReporter route="home" />
      <section className="overflow-hidden rounded-3xl bg-gradient-to-br from-brand-700 to-brand-900 px-6 py-10 text-white sm:px-10">
        <p className="font-semibold text-accent-400">Welcome back, {user.display_name.split(" ")[0]}</p>
        <h1 className="mt-2 max-w-2xl text-3xl font-extrabold leading-tight sm:text-4xl">
          Everyday essentials, easy returns, and help when you need it.
        </h1>
        <p className="mt-3 max-w-xl text-brand-100">
          Search the catalog, or browse a department below. Returns and the shopping assistant are
          coming next.
        </p>
      </section>

      <section aria-labelledby="departments">
        <h2 id="departments" className="text-xl font-bold">
          Shop by department
        </h2>
        <ul className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {categories.map((c) => (
            <li key={c.slug}>
              <Link
                href={`/c/${c.slug}`}
                className="flex min-h-20 items-center justify-center rounded-2xl border border-line bg-white p-4 text-center font-semibold hover:border-brand-600 hover:bg-brand-50"
              >
                {c.name}
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="featured">
        <h2 id="featured" className="text-xl font-bold">
          New and in stock
        </h2>
        <div className="mt-4">
          <ProductGrid products={featured.items} label="New and in stock" />
        </div>
      </section>
    </div>
  );
}
