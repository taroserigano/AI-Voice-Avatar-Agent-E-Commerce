import { InfoIcon } from "@/components/icons";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Privacy" };

const SECTIONS = [
  { id: "what-we-store", title: "What we store" },
  { id: "monitoring", title: "Monitoring" },
  { id: "assistant", title: "The assistant" },
] as const;

export default function PrivacyPage() {
  return (
    <div data-doc="privacy" className="xl:grid xl:grid-cols-[minmax(0,1fr)_12rem] xl:gap-14">
      <article className="max-w-[68ch] animate-fade-up">
        <header>
          <p className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">Legal</p>
          <h1 className="mt-3 font-display text-4xl font-semibold text-ink sm:text-5xl">Privacy</h1>
        </header>

        <div role="note" className="mt-8 flex gap-3 rounded-2xl border border-brand-100 bg-brand-50 p-5 text-brand-900">
          <InfoIcon className="mt-0.5 text-brand-600" />
          <p className="leading-relaxed">
            <strong className="font-semibold">Sandbox notice:</strong> Larkspur is a portfolio demonstration. This page
            describes how the demo handles data; a real privacy policy must be written and approved before any live use.
          </p>
        </div>

        <div className="mt-4 divide-y divide-line">
          <section aria-labelledby="what-we-store" className="py-8">
            <h2 id="what-we-store" className="scroll-mt-24 font-display text-2xl font-semibold text-ink">
              What we store
            </h2>
            <p className="mt-3 text-[1.0625rem] leading-relaxed text-ink-soft">
              Your name, email, a hashed password, your cart, and your orders. Payment card details are entered on
              Stripe&apos;s hosted page and never reach our servers.
            </p>
          </section>
          <section aria-labelledby="monitoring" className="py-8">
            <h2 id="monitoring" className="scroll-mt-24 font-display text-2xl font-semibold text-ink">
              Monitoring
            </h2>
            <p className="mt-3 text-[1.0625rem] leading-relaxed text-ink-soft">
              We record technical traces and logs to keep the service working. Emails, names, addresses, and card-like
              numbers are removed before these are stored, and customers appear only as a one-way hash.
            </p>
          </section>
          <section aria-labelledby="assistant" className="py-8">
            <h2 id="assistant" className="scroll-mt-24 font-display text-2xl font-semibold text-ink">
              The assistant
            </h2>
            <p className="mt-3 text-[1.0625rem] leading-relaxed text-ink-soft">
              When you use the text or voice assistant, we send only what it needs to answer. Audio recording is off by
              default.
            </p>
          </section>
        </div>
      </article>

      <nav aria-label="On this page" className="hidden xl:sticky xl:top-28 xl:block xl:self-start">
        <p className="text-xs font-semibold uppercase tracking-eyebrow text-muted">On this page</p>
        <ul className="mt-3 border-l border-line">
          {SECTIONS.map((s) => (
            <li key={s.id}>
              <a
                href={`#${s.id}`}
                className="-ml-px flex min-h-10 items-center border-l-2 border-transparent pl-4 text-sm text-muted transition-colors hover:border-brand-600 hover:text-ink"
              >
                {s.title}
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
