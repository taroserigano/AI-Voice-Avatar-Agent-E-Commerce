import { XanaConsole } from "@/components/assistant/xana-console";
import {
  ArrowRightIcon,
  ChatIcon,
  ClockIcon,
  HeadsetIcon,
  MailIcon,
  MapIcon,
  MicIcon,
  NotebookIcon,
  PackageIcon,
  ReturnIcon,
  TagIcon,
  TruckIcon,
  type Icon,
} from "@/components/icons";
import { Badge, type BadgeTone } from "@/components/ui/badge";
import { buttonClasses } from "@/components/ui/button";
import { isDevelopment, serverApi } from "@/lib/api-server";
import { formatDate, orderNumber } from "@/lib/orders";
import type { components } from "@ai-commerce/contracts";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Support",
  description: "Talk with Xana, Serigan Mart's customer-support assistant, about orders, delivery, returns, and refunds.",
};

type Case = components["schemas"]["CaseOut"];

const CASE_STATUS: Record<Case["status"], { label: string; tone: BadgeTone }> = {
  open: { label: "Open", tone: "brand" },
  waiting_on_customer: { label: "Waiting on you", tone: "warning" },
  resolved: { label: "Resolved", tone: "success" },
};

const CHANNEL: Record<Case["channel"], { label: string; Icon: Icon }> = {
  chat: { label: "Chat", Icon: ChatIcon },
  voice: { label: "Voice", Icon: MicIcon },
  email: { label: "Email", Icon: MailIcon },
};

// Deep links into the help center and the pages it points to.
const TOPICS: { href: string; title: string; body: string; Icon: Icon }[] = [
  { href: "/help/returns", title: "Returns & refunds", body: "Windows, final-sale items, and refund timing.", Icon: ReturnIcon },
  { href: "/help#shipping", title: "Delivery", body: "$5.99 shipping, free at $35. Arrives in 2–5 business days.", Icon: TruckIcon },
  { href: "/orders", title: "Orders", body: "Tracking, order status, and buying again.", Icon: PackageIcon },
  { href: "/stores", title: "Stores", body: "Hours, services, and return drop-off.", Icon: MapIcon },
  { href: "/help#labels", title: "Product labels", body: "Organic, gluten-free, and other diet tags.", Icon: TagIcon },
  { href: "/returns-policy", title: "Full return policy", body: "Every rule, with worked examples.", Icon: NotebookIcon },
];

/** The customer's support requests. Optional for the page: if the API fails, the section says so. */
async function loadCases(): Promise<Case[] | null> {
  const api = await serverApi();
  const result = await api.GET("/v1/support/cases");
  return result.data ?? null;
}

export default async function SupportPage({
  searchParams,
}: {
  searchParams: Promise<{ order?: string; line?: string; voice?: string; case?: string }>;
}) {
  const params = await searchParams;
  const uuid = /^[0-9a-f-]{36}$/i;
  const cases = await loadCases();
  // "Continue with Xana" on a request: pick the conversation up where it stopped. Only a request
  // from this customer's own list is used, and the message is built here, never from the URL.
  const followUp = cases?.find((c) => c.reference === params.case && c.status !== "resolved");

  return (
    <div className="space-y-12 pb-24 sm:pb-8">
      <header className="max-w-3xl">
        <p className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">Support</p>
        <h1 className="mt-2 font-display text-3xl font-semibold text-ink sm:text-4xl">
          Help with orders, delivery, and returns
        </h1>
        <p className="mt-3 text-lg leading-relaxed text-ink-soft">
          Ask Xana by voice or text: where an order is, what went wrong with a delivery, or how to return something.
          For a return, she shows your exact refund and starts it only when you confirm.
        </p>
      </header>

      <XanaConsole
        initialOrder={params.order && uuid.test(params.order) ? params.order : undefined}
        initialLine={params.line && uuid.test(params.line) ? params.line : undefined}
        simulator={isDevelopment() || params.voice === "sim"}
        initialMessage={followUp ? followUpMessage(followUp) : undefined}
      />

      <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-10">
        <section aria-labelledby="requests-heading">
          <h2 id="requests-heading" className="font-display text-2xl font-semibold text-ink">
            Your requests
          </h2>
          <p className="mt-1 text-sm text-muted">
            When Xana hands something to our team, it&apos;s tracked here.
          </p>
          {cases === null ? (
            <p className="mt-4 rounded-2xl border border-line bg-raised px-4 py-3 text-sm text-muted">
              We couldn&apos;t load your requests right now. Refresh the page to try again.
            </p>
          ) : cases.length === 0 ? (
            <div className="mt-4 flex items-start gap-3 rounded-3xl border border-dashed border-line-strong px-5 py-6">
              <HeadsetIcon className="mt-0.5 size-5 shrink-0 text-muted" />
              <p className="text-sm text-muted">
                <span className="font-semibold text-ink">No requests yet.</span> If Xana can&apos;t sort something out,
                she can pass it to a person, and you&apos;ll see it here with its status.
              </p>
            </div>
          ) : (
            <ul className="mt-4 space-y-3">
              {cases.map((c) => (
                <CaseCard key={c.id} item={c} />
              ))}
            </ul>
          )}
        </section>

        <ContactCard />
      </div>

      <section aria-labelledby="topics-heading">
        <h2 id="topics-heading" className="font-display text-2xl font-semibold text-ink">
          Help topics
        </h2>
        <ul className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {TOPICS.map(({ href, title, body, Icon }) => (
            <li key={href}>
              <Link
                href={href}
                className="group flex h-full gap-3 rounded-2xl bg-raised p-4 shadow-xs ring-1 ring-inset ring-line transition hover:shadow-sm hover:ring-brand-300"
              >
                <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-700">
                  <Icon className="size-5" />
                </span>
                <span className="min-w-0">
                  <span className="flex items-center gap-1 font-semibold text-ink group-hover:text-brand-700">
                    {title}
                    <ArrowRightIcon className="size-4 opacity-0 transition group-hover:opacity-100" />
                  </span>
                  <span className="mt-0.5 block text-sm text-muted">{body}</span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

/** What the customer says to Xana when they continue a request. */
function followUpMessage(item: Case): string {
  const order = item.order_id ? ` about order ${orderNumber(item.order_id)}` : "";
  return `I'm following up on my request ${item.reference} ("${item.subject}")${order}.`;
}

function CaseCard({ item }: { item: Case }) {
  const status = CASE_STATUS[item.status] ?? { label: item.status, tone: "neutral" as const };
  const channel = CHANNEL[item.channel] ?? CHANNEL.chat;
  const headingId = `case-${item.id}`;
  return (
    <li>
      <article aria-labelledby={headingId} className="rounded-3xl border border-line bg-raised p-4 shadow-xs sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
          <div className="min-w-0">
            <h3 id={headingId} className="font-sans text-base font-semibold text-ink">
              {item.subject}
            </h3>
            <p className="mt-0.5 flex flex-wrap items-center gap-x-2 text-sm text-muted">
              <span className="font-mono text-[0.8125rem] tracking-wide">{item.reference}</span>
              <span aria-hidden="true">·</span>
              <span>
                Opened <time dateTime={item.opened_at}>{formatDate(item.opened_at)}</time>
              </span>
              <span aria-hidden="true">·</span>
              <span className="inline-flex items-center gap-1">
                <channel.Icon className="size-3.5" />
                {channel.label}
              </span>
            </p>
          </div>
          <Badge tone={status.tone} dot size="md">
            <span className="sr-only">Status: </span>
            {status.label}
          </Badge>
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-x-4 gap-y-1 border-t border-line pt-3 text-sm">
          <p className="flex items-center gap-1.5 text-ink-soft">
            <ClockIcon className="size-4 text-brand-600" />
            {item.status === "resolved"
              ? "This request is closed."
              : item.status === "waiting_on_customer"
                ? "We're waiting to hear back from you."
                : `We reply within ${item.reply_within}.`}
          </p>
          {item.order_id ? (
            <Link
              href={`/orders/${item.order_id}`}
              className="inline-flex min-h-11 items-center gap-1 font-semibold text-brand-700 hover:text-brand-900"
            >
              Order #{orderNumber(item.order_id)}
              <ArrowRightIcon className="size-4" />
            </Link>
          ) : null}
        </div>
        {item.status === "waiting_on_customer" ? (
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 rounded-2xl bg-warning-50 px-4 py-3">
            <p className="min-w-0 flex-1 basis-60 text-sm text-ink-soft">
              Reply to keep this request moving. Xana picks it up with the details.
            </p>
            {/* A plain link (not client navigation) so the page starts at the top, on the conversation. */}
            <a
              href={`/support?case=${encodeURIComponent(item.reference)}`}
              aria-describedby={headingId}
              className={buttonClasses("primary", "sm")}
            >
              <ChatIcon className="size-4" />
              Continue with Xana
            </a>
          </div>
        ) : null}
      </article>
    </li>
  );
}

function ContactCard() {
  return (
    <aside aria-labelledby="contact-heading" className="rounded-3xl border border-line bg-raised p-5 shadow-xs sm:p-6">
      <h2 id="contact-heading" className="font-display text-xl font-semibold text-ink">
        Contact us
      </h2>
      <p className="mt-1 text-sm text-muted">Prefer a person? Our team is here every day.</p>
      <dl className="mt-4 space-y-3 text-sm">
        <div className="flex items-start gap-3">
          <dt className="mt-0.5">
            <HeadsetIcon className="size-4.5 text-brand-600" />
            <span className="sr-only">Phone</span>
          </dt>
          <dd>
            <a href="tel:+12145550100" className="font-semibold text-ink underline decoration-line-strong underline-offset-4 hover:text-brand-700">
              (214) 555-0100
            </a>
          </dd>
        </div>
        <div className="flex items-start gap-3">
          <dt className="mt-0.5">
            <MailIcon className="size-4.5 text-brand-600" />
            <span className="sr-only">Email</span>
          </dt>
          <dd>
            <a
              href="mailto:help@serigan-mart.example"
              className="font-semibold text-ink underline decoration-line-strong underline-offset-4 hover:text-brand-700"
            >
              help@serigan-mart.example
            </a>
          </dd>
        </div>
        <div className="flex items-start gap-3">
          <dt className="mt-0.5">
            <ClockIcon className="size-4.5 text-brand-600" />
            <span className="sr-only">Hours</span>
          </dt>
          <dd className="text-ink-soft">7 AM – 10 PM Central, every day</dd>
        </div>
      </dl>
      <p className="mt-4 rounded-xl bg-sunken px-3 py-2 text-xs text-muted">
        <strong className="font-semibold text-ink">Demo contact info.</strong> This phone number and email don&apos;t reach
        a real team.
      </p>
    </aside>
  );
}
