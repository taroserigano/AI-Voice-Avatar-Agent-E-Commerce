import { StephLauncher } from "@/components/assistant/steph-launcher";
import { Footer } from "@/components/shop/footer";
import { Header } from "@/components/shop/header";
import { containerClasses } from "@/components/ui/container";
import { getMe, isDevelopment, serverApi, unwrap } from "@/lib/api-server";

export default async function ShopLayout({ children }: { children: React.ReactNode }) {
  // getMe() redirects to sign-in if the session is missing, expired, or revoked.
  const user = await getMe();
  const api = await serverApi();
  const [categories, cart] = await Promise.all([
    api.GET("/v1/categories").then(unwrap),
    api.GET("/v1/cart").then(unwrap),
  ]);

  return (
    <div className="flex min-h-screen flex-col">
      {isDevelopment() ? (
        <p
          role="region"
          aria-label="Sandbox notice"
          className="bg-neutral-900 px-4 py-2 text-center text-xs leading-relaxed text-neutral-300 focus-inverse"
        >
          <strong className="mr-2 inline-flex -translate-y-px items-center rounded-full bg-accent-400 px-2 py-px text-[0.6875rem] font-semibold uppercase tracking-eyebrow text-ink">
            Sandbox store
          </strong>
          {/* One line on phones; the full notice from sm up. */}
          <span className="sm:hidden">Test data. No real money moves.</span>
          <span className="max-sm:hidden">
            Development sign-in, test data, and Stripe test-mode payments.{" "}
            <span className="text-white">Nothing ships and no real money moves.</span>
          </span>
        </p>
      ) : null}
      <Header user={user} categories={categories} cart={cart} />
      <main id="main" className={containerClasses("default", "flex-1 pb-8 pt-6 sm:pt-10")}>
        {children}
      </main>
      <Footer categories={categories} />
      <StephLauncher />
    </div>
  );
}
