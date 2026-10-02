import { ChatIcon, ClockIcon, CreditCardIcon, InfoIcon, PackageIcon, ReturnIcon, TruckIcon } from "@/components/icons";
import { PolicyMarkdown } from "@/components/legal/policy-markdown";
import { formatMoney } from "@/lib/format";
import { formatEffectiveDate, type PolicyDoc, type TocEntry, tableOfContents } from "@/lib/policy-doc";
import { loadPolicy } from "@/lib/policy-files";
import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Return and refund policy",
  description: "What you can return to Serigan Mart, how to return it, and how much you get back and when.",
};

// Read the approved documents on each request, so a policy edit shows immediately.
export const dynamic = "force-dynamic";

const linkClass =
  "font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700";

export default async function ReturnsPolicyPage() {
  const [policy, regulations] = await Promise.all([
    loadPolicy("returns-and-refunds"),
    loadPolicy("returns-regulations"),
  ]);
  const rules = policy.rules as {
    return_window_days: number;
    perishable_report_days: number;
    instant_refund_under_minor: number;
  };
  const facts = [
    {
      icon: <ClockIcon className="size-5" />,
      big: `${rules.return_window_days} days`,
      small: "to return most items, counted from the delivery date",
    },
    { icon: <TruckIcon className="size-5" />, big: "Free", small: "return shipping, by carrier or at any Serigan Mart store" },
    {
      icon: <PackageIcon className="size-5" />,
      big: `${rules.perishable_report_days} days`,
      small: "to report damaged or spoiled fresh and frozen food",
    },
    {
      icon: <CreditCardIcon className="size-5" />,
      big: `Under ${formatMoney(rules.instant_refund_under_minor).replace(".00", "")}`,
      small: "refunded as soon as your package is scanned",
    },
  ];
  const docs = [policy, regulations];

  return (
    <div data-doc="returns-policy" className="xl:grid xl:grid-cols-[minmax(0,1fr)_14rem] xl:gap-12">
      <div className="min-w-0 animate-fade-up">
        <header>
          <p className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">Help · Returns</p>
          <h1 className="mt-3 font-display text-4xl font-semibold text-ink sm:text-5xl">Returns &amp; refunds</h1>
          <p className="mt-4 max-w-[60ch] text-lg leading-relaxed text-ink-soft">
            What you can return, how to send it back, and exactly how much you get back and when.
          </p>
          <dl className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-muted">
            <div className="flex gap-1.5">
              <dt>Version</dt>
              <dd className="font-mono text-ink">{policy.version}</dd>
            </div>
            <div className="flex gap-1.5">
              <dt>Effective</dt>
              <dd className="text-ink">
                <time dateTime={policy.effectiveDate}>{formatEffectiveDate(policy.effectiveDate)}</time>
              </dd>
            </div>
            {policy.status === "sandbox" ? (
              <div>
                <dt className="sr-only">Status</dt>
                <dd className="rounded-full bg-accent-100 px-2.5 py-0.5 text-xs font-semibold text-accent-800">
                  Sandbox policy (demo store)
                </dd>
              </div>
            ) : null}
          </dl>
        </header>

        <section aria-labelledby="short-version" className="mt-10">
          <h2 id="short-version" className="font-display text-2xl font-semibold text-ink">
            The short version
          </h2>
          <ul className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
            {facts.map((f) => (
              <li key={f.big} className="rounded-2xl bg-raised p-4 shadow-xs ring-1 ring-inset ring-line">
                <span className="text-brand-600">{f.icon}</span>
                <p className="mt-2 font-display text-2xl font-semibold text-ink">{f.big}</p>
                <p className="mt-1 text-sm leading-snug text-muted">{f.small}</p>
              </li>
            ))}
          </ul>
          <ul className="mt-4 space-y-2.5 rounded-2xl bg-raised p-5 shadow-xs ring-1 ring-inset ring-line">
            {policy.summary.map((line) => (
              <li key={line} className="flex gap-3 leading-relaxed text-ink-soft">
                <span aria-hidden="true" className="mt-2.5 size-1.5 shrink-0 rounded-full bg-brand-600" />
                <span>{line}</span>
              </li>
            ))}
          </ul>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <StartCard icon={<ReturnIcon className="size-5" />} title="Orders & returns" href="/orders">
              Choose the order and item, see your exact refund, and confirm.
            </StartCard>
            <StartCard icon={<ChatIcon className="size-5" />} title="Ask Steph">
              Our shopping assistant, at the bottom right of every page, answers policy questions and checks orders.
            </StartCard>
            <StartCard icon={<InfoIcon className="size-5" />} title="Talk to Xena">
              Our customer-support assistant handles returns and refunds by voice or text.
            </StartCard>
          </div>
        </section>

        <details className="mt-10 rounded-2xl bg-raised p-4 shadow-xs ring-1 ring-inset ring-line xl:hidden print:hidden">
          <summary className="cursor-pointer font-semibold text-ink">On this page</summary>
          <TocLists docs={docs} nested />
        </details>

        <div className="mt-12 space-y-16">
          {docs.map((doc) => (
            <PolicyDocument key={doc.id} doc={doc} />
          ))}
          <p className="border-t border-line pt-6 text-sm text-muted">
            Questions this page doesn&apos;t answer? Ask Steph or Xena for a person, and we&apos;ll open a support case.
            See also{" "}
            <Link className={linkClass} href="/help/returns">
              how returns work
            </Link>
            , our{" "}
            <Link className={linkClass} href="/terms">
              terms
            </Link>
            , and our{" "}
            <Link className={linkClass} href="/privacy">
              privacy notice
            </Link>
            .
          </p>
        </div>
      </div>

      <nav
        aria-label="On this page"
        className="hidden xl:sticky xl:top-28 xl:block xl:max-h-[calc(100vh-8rem)] xl:self-start xl:overflow-y-auto print:hidden"
      >
        <p className="text-xs font-semibold uppercase tracking-eyebrow text-muted">On this page</p>
        <TocLists docs={docs} />
      </nav>
    </div>
  );
}

function StartCard({
  icon,
  title,
  href,
  children,
}: {
  icon: ReactNode;
  title: string;
  href?: string;
  children: ReactNode;
}) {
  const body = (
    <>
      <span className="text-brand-600">{icon}</span>
      <p className="mt-2 font-semibold text-ink">{title}</p>
      <p className="mt-1 text-sm leading-snug text-muted">{children}</p>
    </>
  );
  const box = "block rounded-2xl bg-raised p-4 shadow-xs ring-1 ring-inset ring-line";
  return href ? (
    <Link href={href} className={`${box} transition hover:shadow-sm hover:ring-brand-300`}>
      {body}
    </Link>
  ) : (
    <div className={box}>{body}</div>
  );
}

function TocLists({ docs, nested = false }: { docs: PolicyDoc[]; nested?: boolean }) {
  return (
    <div className="mt-3 space-y-5 text-sm">
      {docs.map((doc) => (
        <div key={doc.id}>
          <a href={`#${doc.id}`} className="font-semibold text-ink hover:text-brand-700">
            {doc.title}
          </a>
          <TocList entries={tableOfContents(doc)} nested={nested} />
        </div>
      ))}
    </div>
  );
}

function TocList({ entries, nested }: { entries: TocEntry[]; nested: boolean }) {
  return (
    <ol className="mt-2 border-l border-line">
      {entries.map((e) => (
        <li key={e.id}>
          <a
            href={`#${e.id}`}
            className="-ml-px flex min-h-9 items-center border-l-2 border-transparent pl-3 text-muted transition-colors hover:border-brand-600 hover:text-ink"
          >
            <span className="mr-1.5 tabular-nums">{e.number}.</span>
            {e.title}
          </a>
          {nested && e.children.length ? (
            <ol className="ml-6">
              {e.children.map((c) => (
                <li key={c.id}>
                  <a href={`#${c.id}`} className="flex min-h-8 items-center text-muted hover:text-ink">
                    <span className="mr-1.5 tabular-nums">{c.number}</span>
                    {c.title}
                  </a>
                </li>
              ))}
            </ol>
          ) : null}
        </li>
      ))}
    </ol>
  );
}

function PolicyDocument({ doc }: { doc: PolicyDoc }) {
  return (
    <article id={doc.id} aria-labelledby={`${doc.id}-title`} className="scroll-mt-24">
      <h2 id={`${doc.id}-title`} className="font-display text-3xl font-semibold text-ink">
        {doc.title}
      </h2>
      <p className="mt-2 text-sm text-muted">
        Version <span className="font-mono">{doc.version}</span> · effective {formatEffectiveDate(doc.effectiveDate)}
      </p>
      {doc.intro ? (
        <div className="mt-5">
          <PolicyMarkdown>{doc.intro}</PolicyMarkdown>
        </div>
      ) : null}
      <div className="mt-6 divide-y divide-line">
        {doc.sections
          .filter((s) => s.level === 2)
          .map((top) => (
            <section key={top.id} id={top.id} aria-labelledby={`${top.id}-h`} className="scroll-mt-24 py-8">
              <SectionHeading id={top.id} level={3} number={top.number} title={top.title} />
              {top.body ? (
                <div className="mt-3">
                  <PolicyMarkdown>{top.body}</PolicyMarkdown>
                </div>
              ) : null}
              {doc.sections
                .filter((s) => s.level === 3 && s.id.startsWith(`${top.id}-`))
                .map((sub) => (
                  <section key={sub.id} id={sub.id} aria-labelledby={`${sub.id}-h`} className="mt-6 scroll-mt-24">
                    <SectionHeading id={sub.id} level={4} number={sub.number} title={sub.title} />
                    {sub.body ? (
                      <div className="mt-2">
                        <PolicyMarkdown>{sub.body}</PolicyMarkdown>
                      </div>
                    ) : null}
                  </section>
                ))}
            </section>
          ))}
      </div>
    </article>
  );
}

function SectionHeading({ id, level, number, title }: { id: string; level: 3 | 4; number: string; title: string }) {
  const Heading = level === 3 ? "h3" : "h4";
  return (
    <Heading
      id={`${id}-h`}
      className={`group flex items-baseline gap-2.5 text-ink ${level === 3 ? "font-display text-2xl font-semibold" : "text-lg font-semibold"}`}
    >
      <span className="tabular-nums text-muted">{number}</span>
      <span>{title}</span>
      <a
        href={`#${id}`}
        className="text-sm font-normal text-brand-700 opacity-0 transition group-hover:opacity-100 focus-visible:opacity-100 print:hidden"
        aria-label={`Link to section ${number}`}
      >
        #
      </a>
    </Heading>
  );
}
