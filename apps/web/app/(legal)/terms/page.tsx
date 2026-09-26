import { InfoIcon } from "@/components/icons";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Terms" };

export default function TermsPage() {
  return (
    <article data-doc="terms" className="max-w-[68ch] animate-fade-up">
      <header>
        <p className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">Legal</p>
        <h1 className="mt-3 font-display text-4xl font-semibold text-ink sm:text-5xl">Terms</h1>
      </header>

      <div role="note" className="mt-8 flex gap-3 rounded-2xl border border-brand-100 bg-brand-50 p-5 text-brand-900">
        <InfoIcon className="mt-0.5 text-brand-600" />
        <p className="leading-relaxed">
          <strong className="font-semibold">Sandbox notice:</strong> Serigan Mart is a portfolio demonstration, not a real
          store. Payments run in Stripe test mode, nothing ships, and no real money moves.
        </p>
      </div>

      <section aria-labelledby="returns" className="mt-4 py-8">
        <h2 id="returns" className="scroll-mt-24 font-display text-2xl font-semibold text-ink">
          Returns
        </h2>
        <p className="mt-3 text-[1.0625rem] leading-relaxed text-ink-soft">
          The sandbox return policy is 30 days from delivery. Gift cards are final sale. Electronics are refunded after
          inspection. Refunds go back to the original payment method.
        </p>
      </section>
    </article>
  );
}
