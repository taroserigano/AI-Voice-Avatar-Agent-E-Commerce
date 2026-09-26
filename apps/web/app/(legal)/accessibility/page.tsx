import type { Metadata } from "next";

export const metadata: Metadata = { title: "Accessibility" };

export default function AccessibilityPage() {
  return (
    <article data-doc="accessibility" className="max-w-[68ch] animate-fade-up">
      <header>
        <p className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">Legal</p>
        <h1 className="mt-3 font-display text-4xl font-semibold text-ink sm:text-5xl">Accessibility</h1>
      </header>

      <p className="mt-6 text-lg leading-relaxed text-ink-soft">
        Serigan Mart aims to meet the Web Content Accessibility Guidelines (WCAG) 2.2 at level AA. Every page works with a
        keyboard, shows where focus is, and labels its controls for screen readers. Sign-in works with password managers
        and allows pasting.
      </p>

      <section aria-labelledby="known-gaps" className="mt-8 border-t border-line py-8">
        <h2 id="known-gaps" className="scroll-mt-24 font-display text-2xl font-semibold text-ink">
          Known gaps
        </h2>
        <p className="mt-3 text-[1.0625rem] leading-relaxed text-ink-soft">
          A full audit is scheduled before any pilot. If something doesn&apos;t work for you, the assistant can hand you
          to a person, and every task can also be done without it.
        </p>
      </section>
    </article>
  );
}
