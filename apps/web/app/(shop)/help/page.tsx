import { OpenStephButton } from "@/components/assistant/open-steph";
import { HelpSearch } from "@/components/help/help-search";
import {
  ArrowRightIcon,
  ClockIcon,
  HeadsetIcon,
  LockIcon,
  MailIcon,
  MapIcon,
  MicIcon,
  PackageIcon,
  ReturnIcon,
  TagIcon,
  TruckIcon,
  UserIcon,
  type Icon,
} from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { SectionHeading } from "@/components/ui/section-heading";
import type { HelpEntry } from "@/lib/help-search";
import { deliveryProgress, orderStatusMeta, shipmentStatusLabel } from "@/lib/orders";
import type { OrderSummary } from "@ai-commerce/contracts";
import type { Metadata } from "next";
import Link from "next/link";
import { isValidElement, type ReactNode } from "react";

export const metadata: Metadata = {
  title: "Help center",
  description: "Returns, delivery, orders, stores, product labels, and your account, plus how to reach us.",
};

// Plain-language summaries of the approved policies in content/policies. Keep them in step with
// shipping-and-delivery.md, product-labels.md, and returns-and-refunds.md.

const inlineLink =
  "font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700";

type Topic = {
  id: string;
  icon: Icon;
  title: string;
  body: string;
  links: { href: string; label: string }[];
};

const TOPICS: Topic[] = [
  {
    id: "returns",
    icon: ReturnIcon,
    title: "Returns & refunds",
    body: "30 days from delivery, free return shipping, and your money back on the card you paid with.",
    links: [
      { href: "/help/returns", label: "How returns work" },
      { href: "/returns-policy", label: "Return & refund policy" },
    ],
  },
  {
    id: "delivery",
    icon: TruckIcon,
    title: "Delivery & shipping",
    body: "$5.99 standard shipping, free on orders of $35 or more. Arrives in 2–5 business days.",
    links: [{ href: "#shipping", label: "Shipping details" }],
  },
  {
    id: "orders",
    icon: PackageIcon,
    title: "Orders & tracking",
    body: "Follow every order from preparing to delivered, and start a return right from the order.",
    links: [{ href: "/orders", label: "Your orders" }],
  },
  {
    id: "stores",
    icon: MapIcon,
    title: "Stores & drop-off",
    body: "10 stores around Dallas–Fort Worth. Every one takes return packages at its drop-off counter.",
    links: [{ href: "/stores", label: "Find a store" }],
  },
  {
    id: "labels",
    icon: TagIcon,
    title: "Product labels",
    body: "What “fat free”, “keto friendly”, “organic” and other labels on our products mean.",
    links: [{ href: "#labels", label: "What labels mean" }],
  },
  {
    id: "account",
    icon: UserIcon,
    title: "Account & sign-in",
    body: "Your orders, activity, and cart live in your account. Every page in the store needs you signed in.",
    links: [
      { href: "#account", label: "Account help" },
      { href: "/privacy", label: "Privacy" },
    ],
  },
];

const SHIPPING_FACTS: { term: string; detail: ReactNode }[] = [
  { term: "Standard shipping", detail: "$5.99 per order" },
  { term: "Free shipping", detail: "Orders of $35 or more, after discounts and before tax" },
  { term: "Delivery time", detail: "Ships within 1 business day, arrives in 2–5 business days" },
  { term: "Where we ship", detail: "Addresses in the United States only" },
  { term: "Store pickup", detail: "Not available yet: online orders are always delivered" },
  { term: "Sales tax", detail: "Based on your delivery address. Most grocery food and gift cards aren't taxed in Texas." },
];

// The same words the order list, the order page, and the filter tabs use (lib/orders.ts), so the
// help center never describes a status the shopper can't find on their order.
const ORDER_STATUS_HELP: { status: OrderSummary["status"]; body: string }[] = [
  { status: "paid", body: "We have your order and payment, and we're getting it ready to ship." },
  { status: "fulfilling", body: "Packed and on its way. The delivery card on the order shows where it is." },
  { status: "delivered", body: "It's arrived. Your 30-day return window starts now." },
  { status: "canceled", body: "The order was canceled." },
];

// Delivery-card stages, read from the same function that draws the tracker on an order.
const DELIVERY_STEPS = (deliveryProgress({ status: "paid", placed_at: "", delivered_at: null }, null)?.steps ?? []).map(
  (s) => s.label,
);

const LABELS: { group: string; items: [string, string][] }[] = [
  {
    group: "Nutrition (per serving)",
    items: [
      ["Fat free", "Less than 0.5 g of fat (includes “nonfat” and “skim”)"],
      ["Low fat", "3 g of fat or less"],
      ["Sugar free", "Less than 0.5 g of total sugars"],
      ["No added sugar", "Nothing sweet is added; natural sugars, like the lactose in milk, may remain"],
      ["Keto friendly", "5 g of net carbs (carbs minus fiber) or less"],
      ["High protein", "10 g of protein or more"],
      ["Low sodium", "140 mg of sodium or less"],
    ],
  },
  {
    group: "Diet and allergens",
    items: [
      ["Dairy free", "No milk ingredients at all"],
      ["Lactose free", "Lactose removed, but it can still contain milk, so it isn't safe for a milk allergy"],
      ["Vegan", "No meat, fish, dairy, eggs, honey, or gelatin"],
      ["Gluten free", "Made without wheat, barley, or rye"],
    ],
  },
  {
    group: "Sourcing",
    items: [
      ["Organic", "Produced to USDA organic standards"],
      ["Wild caught", "Fish caught in the wild, not farm raised"],
      ["Texas grown", "Grown in Texas"],
    ],
  },
];

const FAQS: { id: string; q: string; a: ReactNode }[] = [
  {
    id: "faq-shipping-cost",
    q: "How much is shipping?",
    a: "Standard shipping is $5.99, and free when your order is $35 or more after discounts and before tax.",
  },
  {
    id: "faq-return-window",
    q: "How long do I have to return something?",
    a: (
      <>
        30 days from delivery for most items. Fresh and frozen food: tell us within 7 days, and there&apos;s nothing to
        send back. Gift cards are final sale.{" "}
        <Link href="/help/returns" className={inlineLink}>
          How returns work
        </Link>
      </>
    ),
  },
  {
    id: "faq-store-drop-off",
    q: "Can I drop a return off at a store?",
    a: (
      <>
        Yes. Any of our 10{" "}
        <Link href="/stores" className={inlineLink}>
          stores around Dallas–Fort Worth
        </Link>{" "}
        takes labeled return packages for online orders at the drop-off counter.
      </>
    ),
  },
  { id: "faq-store-pickup", q: "Can I pick up an online order at a store?", a: "Not yet. Online orders are always delivered." },
  {
    id: "faq-assistants",
    q: "Who are Steph and Xena?",
    a: (
      <>
        Steph is our shopping assistant: she finds products, checks your orders, and answers policy questions. Xena
        helps with orders, delivery, returns, and refunds by voice or text on the{" "}
        <Link href="/support" className={inlineLink}>
          Support page
        </Link>
        . Both are AI assistants and can make mistakes; prices, orders, and policies always come from the store.
      </>
    ),
  },
  { id: "faq-international", q: "Do you ship outside the United States?", a: "No, we ship to US addresses only." },
];

const ACCOUNT_TIPS: { icon: Icon; title: string; body: ReactNode }[] = [
  {
    icon: LockIcon,
    title: "Signed in everywhere",
    body: "Every store page needs you signed in; the legal pages are open to everyone.",
  },
  {
    icon: ClockIcon,
    title: "Your activity",
    body: (
      <>
        Searches, viewed products, orders, and returns show up in{" "}
        <Link href="/activity" className={inlineLink}>
          Activity
        </Link>
        .
      </>
    ),
  },
  {
    icon: UserIcon,
    title: "Signing out",
    body: "Use Sign out in the account menu at the top of any page. It ends your session on this device.",
  },
];

/** The plain text of a bit of JSX (strings, fragments, links), for the search index. */
function textOf(node: ReactNode): string {
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(textOf).join("");
  if (isValidElement<{ children?: ReactNode }>(node)) return textOf(node.props.children);
  return "";
}

/** Everything on this page the search box can find, each pointing at where it's answered. */
function helpEntries(): HelpEntry[] {
  return [
    ...TOPICS.map((t) => ({ id: `topic-${t.id}`, section: "Topic", title: t.title, text: t.body, href: t.links[0]?.href ?? "#" })),
    ...SHIPPING_FACTS.map((f) => ({
      id: `shipping-${f.term}`,
      section: "Shipping and delivery",
      title: f.term,
      text: textOf(f.detail),
      href: "#shipping",
    })),
    ...ORDER_STATUS_HELP.map((o) => ({
      id: `status-${o.status}`,
      section: "Order status",
      title: orderStatusMeta(o.status).label,
      text: o.body,
      href: "#order-status",
    })),
    {
      id: "status-tracking",
      section: "Order status",
      title: "Delivery tracking",
      text: `${DELIVERY_STEPS.join(", ")}. ${shipmentStatusLabel("exception")} if the carrier reports a problem.`,
      href: "#order-status",
    },
    ...LABELS.flatMap((g) =>
      g.items.map(([term, means]) => ({ id: `label-${term}`, section: `Labels · ${g.group}`, title: term, text: means, href: "#labels" })),
    ),
    ...ACCOUNT_TIPS.map((t) => ({ id: `account-${t.title}`, section: "Account", title: t.title, text: textOf(t.body), href: "#account" })),
    ...FAQS.map((f) => ({ id: f.id, section: "Common questions", title: f.q, text: textOf(f.a), href: `#${f.id}` })),
  ];
}

export default function HelpCenterPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-16 pb-8 sm:space-y-20 sm:pt-2">
      {/* ---------- Hero ---------- */}
      <section aria-labelledby="help-title" className="rounded-3xl bg-mesh-light px-5 py-10 sm:px-10 sm:py-12">
        <p className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">Help center</p>
        <h1 id="help-title" className="mt-2 font-display text-4xl font-semibold text-ink sm:text-5xl">
          How can we help?
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-ink-soft">
          Find answers about returns, delivery, orders, and stores, or ask Steph and Xena. They&apos;re here any
          time.
        </p>
        <HelpSearch entries={helpEntries()} className="mt-6">
          <div className="mt-6 flex flex-wrap gap-3">
            <OpenStephButton>Ask Steph</OpenStephButton>
            <ButtonLink href="/support" variant="outline">
              <MicIcon className="size-4.5" />
              Talk to Xena
            </ButtonLink>
          </div>
        </HelpSearch>
      </section>

      {/* ---------- Topics ---------- */}
      <section aria-labelledby="topics-title">
        <SectionHeading id="topics-title" eyebrow="Browse by topic" title="Help topics" />
        <ul className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {TOPICS.map(({ id, icon: TopicIcon, title, body, links }) => (
            <Card as="li" key={id} className="flex flex-col">
              <span className="grid size-11 place-items-center rounded-2xl bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-100">
                <TopicIcon className="size-5.5" />
              </span>
              <h3 className="mt-4 font-display text-lg font-semibold text-ink">{title}</h3>
              <p className="mt-1 flex-1 text-muted">{body}</p>
              <ul className="mt-4 flex flex-wrap gap-x-4">
                {links.map((l) => (
                  <li key={l.href}>
                    <Link
                      href={l.href}
                      className="group inline-flex min-h-11 items-center gap-1.5 text-sm font-semibold text-brand-700 hover:text-brand-900"
                    >
                      {l.label}
                      <ArrowRightIcon className="size-4 transition-transform duration-200 ease-snappy group-hover:translate-x-0.5" />
                    </Link>
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </ul>
      </section>

      {/* ---------- Shipping ---------- */}
      <section aria-labelledby="shipping-title" id="shipping" className="scroll-mt-44">
        <SectionHeading
          id="shipping-title"
          eyebrow="Delivery"
          title="Shipping and delivery"
          description="Every order ships from our warehouse to your door."
        />
        <div className="mt-8 grid gap-5 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
          <Card padding="none">
            <dl className="divide-y divide-line">
              {SHIPPING_FACTS.map((f) => (
                <div key={f.term} className="grid gap-1 px-5 py-4 sm:grid-cols-[11rem_minmax(0,1fr)] sm:gap-4 sm:px-6">
                  <dt className="font-semibold text-ink">{f.term}</dt>
                  <dd className="text-ink-soft">{f.detail}</dd>
                </div>
              ))}
            </dl>
          </Card>
          <Card id="order-status" className="scroll-mt-44">
            <h3 className="font-display text-lg font-semibold text-ink">Order status</h3>
            <p className="mt-1 text-sm text-muted">
              Each order in{" "}
              <Link href="/orders" className={inlineLink}>
                Orders &amp; returns
              </Link>{" "}
              shows one of these.
            </p>
            <dl className="mt-4 space-y-3">
              {ORDER_STATUS_HELP.map(({ status, body }) => {
                const meta = orderStatusMeta(status);
                return (
                  <div key={status}>
                    <dt>
                      <Badge tone={meta.tone} dot size="md">
                        {meta.label}
                      </Badge>
                    </dt>
                    <dd className="mt-1 text-sm text-muted">{body}</dd>
                  </div>
                );
              })}
            </dl>
            <h4 className="mt-6 text-sm font-semibold text-ink">Tracking a delivery</h4>
            <p className="mt-1 text-sm text-muted">The delivery card on each order moves through these steps:</p>
            <ol className="mt-3 flex flex-wrap items-center gap-x-1.5 gap-y-2 text-sm">
              {DELIVERY_STEPS.map((label, i) => (
                <li key={label} className="flex items-center gap-1.5">
                  <span className="grid size-6 shrink-0 place-items-center rounded-full bg-brand-50 text-xs font-semibold text-brand-700 ring-1 ring-inset ring-brand-100">
                    {i + 1}
                  </span>
                  <span className="font-medium text-ink">{label}</span>
                  {i < DELIVERY_STEPS.length - 1 ? (
                    <ArrowRightIcon aria-hidden="true" className="size-3.5 text-subtle" />
                  ) : null}
                </li>
              ))}
            </ol>
            <p className="mt-3 text-sm text-muted">
              If the carrier reports a problem, the order shows{" "}
              <strong className="font-semibold text-ink">{shipmentStatusLabel("exception")}</strong>. Xena can look into
              it for you.
            </p>
          </Card>
        </div>
      </section>

      {/* ---------- Product labels ---------- */}
      <section aria-labelledby="labels-title" id="labels" className="scroll-mt-44">
        <SectionHeading
          id="labels-title"
          eyebrow="Know what you're buying"
          title="What our product labels mean"
          description="Labels like “Organic” or “Fat free” follow these definitions. Nutrition amounts are per serving, as listed on the Nutrition Facts panel."
        />
        <div className="mt-8 grid gap-5 lg:grid-cols-3">
          {LABELS.map((g) => (
            <Card key={g.group}>
              <h3 className="font-display text-lg font-semibold text-ink">{g.group}</h3>
              <dl className="mt-4 space-y-3">
                {g.items.map(([term, means]) => (
                  <div key={term}>
                    <dt>
                      <Badge tone="brand">{term}</Badge>
                    </dt>
                    <dd className="mt-1 text-sm text-ink-soft">{means}</dd>
                  </div>
                ))}
              </dl>
            </Card>
          ))}
        </div>
        <p className="mt-4 text-sm text-muted">
          Every food page lists its ingredients and major allergens. With a severe allergy, always check the package
          too. Steph can find products by label: try asking for &ldquo;gluten-free pasta&rdquo;.
        </p>
      </section>

      {/* ---------- Account ---------- */}
      <section aria-labelledby="account-title" id="account" className="scroll-mt-44">
        <SectionHeading id="account-title" eyebrow="Your account" title="Account and sign-in" />
        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {ACCOUNT_TIPS.map((t) => (
            <AccountTip key={t.title} icon={t.icon} title={t.title}>
              {t.body}
            </AccountTip>
          ))}
        </div>
      </section>

      {/* ---------- FAQ ---------- */}
      <section aria-labelledby="faq-title">
        <SectionHeading id="faq-title" eyebrow="Quick answers" title="Common questions" />
        <Card padding="none" className="mt-8 divide-y divide-line">
          {FAQS.map((f) => (
            <Faq key={f.id} id={f.id} q={f.q}>
              {f.a}
            </Faq>
          ))}
        </Card>
      </section>

      {/* ---------- Talk to us ---------- */}
      <section
        aria-labelledby="contact-title"
        className="relative isolate overflow-hidden rounded-3xl bg-inverse px-6 py-10 text-brand-200 focus-inverse sm:px-10 sm:py-12"
      >
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(55%_70%_at_100%_0%,rgb(125_100_239/0.35),transparent_70%)]"
        />
        <p className="text-xs font-semibold uppercase tracking-eyebrow text-accent-300">Talk to us</p>
        <h2 id="contact-title" className="mt-2 font-display text-2xl font-semibold text-white sm:text-3xl">
          Still need a hand?
        </h2>
        <div className="mt-8 grid gap-8 lg:grid-cols-2">
          <div>
            <h3 className="font-semibold text-white">Ask an assistant, any time</h3>
            <p className="mt-1">Steph helps you shop. Xena helps with orders, delivery, and returns by voice or text.</p>
            <div className="mt-5 flex flex-wrap gap-3">
              <OpenStephButton variant="inverse">Ask Steph</OpenStephButton>
              <ButtonLink
                href="/support"
                variant="ghost"
                className="text-white ring-1 ring-inset ring-white/25 hover:bg-white/10 active:bg-white/15"
              >
                <MicIcon className="size-4.5" />
                Talk to Xena
              </ButtonLink>
            </div>
          </div>
          <div className="rounded-2xl bg-white/5 p-5 ring-1 ring-inset ring-white/10">
            <h3 className="flex flex-wrap items-center gap-2 font-semibold text-white">
              Contact details
              <span className="rounded-full bg-accent-400 px-2 py-px text-[0.6875rem] font-semibold uppercase tracking-eyebrow text-ink">
                Demo
              </span>
            </h3>
            <p className="mt-1 text-sm">
              Sample contact info for this demo store. Nobody answers these, so use Steph or Xena instead.
            </p>
            <dl className="mt-4 space-y-2.5 text-sm">
              <ContactRow icon={HeadsetIcon} term="Phone">
                (214) 555-0100
              </ContactRow>
              <ContactRow icon={MailIcon} term="Email">
                help@serigan-mart.example
              </ContactRow>
              <ContactRow icon={ClockIcon} term="Hours">
                7am–10pm CT, every day
              </ContactRow>
            </dl>
          </div>
        </div>
      </section>
    </div>
  );
}

function AccountTip({ icon: TipIcon, title, children }: { icon: Icon; title: string; children: ReactNode }) {
  return (
    <Card>
      <TipIcon className="size-5 text-brand-600" />
      <h3 className="mt-3 font-semibold text-ink">{title}</h3>
      <p className="mt-1 text-sm text-muted">{children}</p>
    </Card>
  );
}

function ContactRow({ icon: RowIcon, term, children }: { icon: Icon; term: string; children: ReactNode }) {
  return (
    <div className="flex items-center gap-3">
      <RowIcon className="size-4.5 shrink-0 text-accent-300" />
      <dt className="w-14 shrink-0 text-brand-300">{term}</dt>
      <dd className="font-medium text-white">{children}</dd>
    </div>
  );
}

function Faq({ id, q, children }: { id: string; q: string; children: ReactNode }) {
  return (
    <details id={id} className="group scroll-mt-44 px-5">
      <summary className="flex min-h-14 cursor-pointer list-none items-center justify-between gap-4 font-semibold text-ink">
        {q}
        <span
          aria-hidden="true"
          className="grid size-7 shrink-0 place-items-center rounded-full bg-brand-50 text-brand-700 transition-transform duration-200 group-open:rotate-45"
        >
          <span className="text-lg leading-none">+</span>
        </span>
      </summary>
      <p className="pb-4 text-muted">{children}</p>
    </details>
  );
}
