import {
  ArrowRightIcon,
  BasketIcon,
  ChatIcon,
  CheckIcon,
  ClockIcon,
  CreditCardIcon,
  PackageIcon,
  ReturnIcon,
  SearchIcon,
  ShieldCheckIcon,
  TagIcon,
  UserIcon,
  XIcon,
} from "@/components/icons";
import { Badge, type BadgeTone } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { SectionHeading } from "@/components/ui/section-heading";
import { cn } from "@/lib/cn";
import { RETURN_STEPS } from "@/lib/orders";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import {
  BoltIcon,
  BoxArt,
  CalendarArt,
  CardArt,
  ElectronicsArt,
  FlowArrow,
  GiftCardArt,
  ScanIcon,
  StepConfirmArt,
  StepPickArt,
  StepQuoteArt,
  StepShipArt,
  StoreArt,
  WarehouseIcon,
} from "./illustrations";

export const metadata: Metadata = { title: "How returns work" };

// A plain-language picture of the return policy. The server decides every real eligibility and
// amount; this page only explains. Keep these in step with SANDBOX_POLICY in
// services/commerce/src/commerce/returns/policy.py.
const WINDOW_DAYS = 30;
const PERISHABLE_DAYS = 7;
const INSTANT_UNDER = "$25";

const steps = [
  {
    art: <StepPickArt />,
    title: "Pick the item",
    body: "Open the order under Orders & returns and choose Start a return. Or just ask the assistant.",
  },
  {
    art: <StepQuoteArt />,
    title: "See your refund",
    body: "We show exactly how much comes back and where it goes. The quote is good for a limited time.",
  },
  {
    art: <StepConfirmArt />,
    title: "Confirm it yourself",
    body: "Tap Confirm return, or say a clear “yes” to the assistant. Nothing happens until you do.",
  },
  {
    art: <StepShipArt />,
    title: "Send it back",
    body: "Right after you confirm, you get a return label or drop-off details. Pack it up and send it.",
  },
];

export default function HowReturnsWorkPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-16 pb-8 sm:space-y-20 sm:pt-2">
      {/* ---------- Hero ---------- */}
      <section aria-labelledby="returns-title" className="rounded-3xl bg-mesh-light px-5 py-10 sm:px-10 sm:py-12">
        <p className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">Help · Returns</p>
        <h1 id="returns-title" className="mt-2 font-display text-4xl font-semibold text-ink sm:text-5xl">
          Returns, made simple
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-ink-soft">
          Changed your mind? Send it back within {WINDOW_DAYS} days of delivery and get your money back on the
          card you paid with.
        </p>

        <ol className="mt-10 flex items-start justify-center gap-1 sm:gap-4" aria-label="The return journey">
          <Station art={<BoxArt className="size-20 sm:size-28" />} label="You send it back" />
          <li aria-hidden="true" className="mt-8 w-6 shrink-0 sm:mt-12 sm:w-10">
            <FlowArrow className="w-full" />
          </li>
          <Station art={<StoreArt className="size-20 sm:size-28" />} label="We receive it" />
          <li aria-hidden="true" className="mt-8 w-6 shrink-0 sm:mt-12 sm:w-10">
            <FlowArrow className="w-full" />
          </li>
          <Station art={<CardArt className="size-20 sm:size-28" />} label="Money back to your card" />
        </ol>

        <ul className="mt-10 flex flex-wrap justify-center gap-2">
          <Fact icon={<ClockIcon className="size-4" />}>{WINDOW_DAYS} days from delivery</Fact>
          <Fact icon={<CreditCardIcon className="size-4" />}>Refund to original payment</Fact>
          <Fact icon={<CheckIcon className="size-4" />}>No restocking fee</Fact>
        </ul>
        <p className="mt-6 text-center text-sm text-muted">
          <Badge tone="accent" className="mr-1.5 align-[1px]">
            Soon
          </Badge>
          Online returns open in the next update. Each order already shows what you&apos;d get back.
        </p>
      </section>

      {/* ---------- Four steps ---------- */}
      <section aria-labelledby="steps-title">
        <SectionHeading id="steps-title" eyebrow="4 quick steps" title="How to return something" />
        <ol className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, i) => (
            <Card as="li" padding="sm" key={step.title} className="relative">
              <span className="absolute -top-3 left-4 grid size-8 place-items-center rounded-full bg-brand-600 text-sm font-semibold text-white shadow-glow">
                {i + 1}
              </span>
              <div className="mt-2">{step.art}</div>
              <h3 className="mt-4 font-display text-lg font-semibold text-ink">{step.title}</h3>
              <p className="mt-1 text-muted">{step.body}</p>
            </Card>
          ))}
        </ol>
      </section>

      {/* ---------- What can be returned ---------- */}
      <section aria-labelledby="what-title">
        <SectionHeading id="what-title" eyebrow="Before you start" title="What can I return?" />
        <ul className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Rule
            art={<CalendarArt className="size-20" />}
            tone="success"
            icon={<CheckIcon />}
            verdict="Yes"
            title="Most items"
            body={`Anything delivered in the last ${WINDOW_DAYS} days.`}
          />
          <Rule
            art={<ElectronicsArt className="size-20" />}
            tone="warning"
            icon={<SearchIcon />}
            verdict="Yes, after a check"
            title="Electronics"
            body="Our warehouse inspects them before we refund."
          />
          <Rule
            art={
              <span className="grid size-20 place-items-center text-success-600">
                <BasketIcon className="size-12" />
              </span>
            }
            tone="brand"
            icon={<CheckIcon />}
            verdict="Keep it"
            title="Fresh & frozen food"
            body={`Tell us within ${PERISHABLE_DAYS} days of delivery. There's nothing to send back.`}
          />
          <Rule
            art={<GiftCardArt className="size-20" />}
            tone="danger"
            icon={<XIcon />}
            verdict="No"
            title="Final sale"
            body="Gift cards and other final-sale items can't be returned."
          />
        </ul>
      </section>

      {/* ---------- How much ---------- */}
      <section aria-labelledby="money-title">
        <SectionHeading id="money-title" eyebrow="No surprises" title="How much do I get back?" />
        <Card padding="lg" className="mt-8">
          <p className="text-center font-medium text-muted">For each item you return:</p>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-2 sm:gap-3">
            <MathChip icon={<TagIcon className="size-4" />} label="What you paid" value="$30.00" />
            <Operator>−</Operator>
            <MathChip icon={<TagIcon className="size-4" />} label="Any discount" value="$3.00" />
            <Operator>+</Operator>
            <MathChip icon={<CreditCardIcon className="size-4" />} label="Tax you paid" value="$2.16" />
            <Operator>=</Operator>
            <MathChip icon={<CheckIcon className="size-4" />} label="Your refund" value="$29.16" highlight />
          </div>
          <p className="mt-3 text-center text-sm text-muted">Example: a $30.00 shirt bought with a $3.00 coupon.</p>

          <ul className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <Good>No restocking fee, ever.</Good>
            <Good>Shipping is refunded when you return the whole order.</Good>
            <Good>Money goes back to the card you paid with. No store credit.</Good>
          </ul>
          <p className="mt-6 text-sm text-muted">
            Bought several of the same item with one discount? We split it evenly to the cent. Any leftover cent
            goes on the last one you return, so you never get back more than you paid.
          </p>
        </Card>
      </section>

      {/* ---------- When ---------- */}
      <section aria-labelledby="when-title">
        <SectionHeading
          id="when-title"
          eyebrow="Timing"
          title="When do I get my money?"
          description="It depends on the item. Your order page tells you which one applies."
        />
        <div className="mt-8 grid grid-cols-1 gap-5 lg:grid-cols-3">
          <Lane
            tone="success"
            icon={<BoltIcon className="size-6" />}
            title="Instant refund"
            who={`Items under ${INSTANT_UNDER} that don't need a check`}
            track={[
              { icon: <PackageIcon />, label: "Drop off" },
              { icon: <ScanIcon />, label: "Scanned" },
              { icon: <CreditCardIcon />, label: "Refund starts" },
            ]}
          />
          <Lane
            tone="brand"
            icon={<WarehouseIcon className="size-6" />}
            title="After we receive it"
            who="Most other items"
            track={[
              { icon: <PackageIcon />, label: "Drop off" },
              { icon: <WarehouseIcon />, label: "We receive it" },
              { icon: <CreditCardIcon />, label: "Refund starts" },
            ]}
          />
          <Lane
            tone="warning"
            icon={<SearchIcon className="size-6" />}
            title="After inspection"
            who="All electronics"
            track={[
              { icon: <WarehouseIcon />, label: "We receive it" },
              { icon: <SearchIcon />, label: "We inspect it" },
              { icon: <CreditCardIcon />, label: "Refund starts" },
            ]}
          />
        </div>
      </section>

      {/* ---------- Tracking ---------- */}
      <section aria-labelledby="track-title">
        <SectionHeading
          id="track-title"
          eyebrow="Stay in the loop"
          title="Following your return"
          description="Your order page tracks the return and the refund separately."
        />
        <Card className="mt-8">
          <h3 className="font-display text-lg font-semibold text-ink">Your return</h3>
          <ol className="mt-5 grid grid-cols-5 gap-1" aria-label="Return steps">
            {RETURN_STEPS.map((label, i) => (
              <li key={label} className="relative flex flex-col items-center text-center">
                {i > 0 ? (
                  <span aria-hidden="true" className="absolute right-1/2 top-4 h-0.5 w-full -translate-y-1/2 bg-brand-200" />
                ) : null}
                <span className="relative grid size-8 place-items-center rounded-full bg-brand-600 text-sm font-semibold text-white ring-4 ring-raised">
                  {i + 1}
                </span>
                <span className="mt-2 text-xs font-semibold leading-tight text-ink sm:text-sm">{label}</span>
              </li>
            ))}
          </ol>
          <p className="mt-5 text-sm text-muted">
            Anything unusual, like damage or a disagreement, goes to a person on our returns team.
          </p>
        </Card>

        <h3 className="mt-8 font-display text-lg font-semibold text-ink">Your refund</h3>
        <div className="mt-4 grid grid-cols-1 items-stretch gap-3 md:grid-cols-[1fr_auto_1fr_auto_1fr]">
          <Status tone="warning" icon={<ClockIcon />} name="Refund pending" body="We've started it. It's on its way." />
          <FlowArrow className="mx-auto w-10 rotate-90 self-center md:rotate-0" />
          <Status
            tone="success"
            icon={<CheckIcon />}
            name="Refunded"
            body="Done. The money was sent to the card you paid with."
          />
          <span className="self-center text-center text-sm font-semibold text-muted">or, rarely</span>
          <Status
            tone="danger"
            icon={<XIcon />}
            name="Refund failed"
            body="It didn't go through. We're looking into it and will email you."
          />
        </div>
        <p className="mt-3 text-sm text-muted">We only say “Refunded” once the money has actually been sent.</p>
      </section>

      {/* ---------- Two ways to start ---------- */}
      <section aria-labelledby="start-title">
        <SectionHeading id="start-title" eyebrow="Your choice" title="Two ways to start" />
        <div className="mt-8 grid grid-cols-1 gap-5 md:grid-cols-2">
          <Card>
            <h3 className="flex items-center gap-2 font-display text-lg font-semibold text-ink">
              <ReturnIcon className="text-brand-600" />
              Click it
            </h3>
            <p className="mt-1 text-muted">Open the order and choose Start a return next to the item.</p>
            {/* A picture of an order line, not a working control. */}
            <div aria-hidden="true" className="mt-5 rounded-2xl bg-sunken p-3">
              <div className="flex items-center gap-3 rounded-xl bg-raised p-3 shadow-xs">
                <div className="size-12 shrink-0 rounded-lg bg-brand-100" />
                <div className="min-w-0 flex-1">
                  <p className="truncate font-semibold text-ink">Wireless Headphones</p>
                  <p className="text-sm text-muted">Delivered 6 days ago</p>
                </div>
                <span className="shrink-0 rounded-full px-3 py-1.5 text-sm font-semibold text-brand-700 ring-1 ring-brand-300">
                  Start a return
                </span>
              </div>
            </div>
          </Card>
          <Card>
            <h3 className="flex items-center gap-2 font-display text-lg font-semibold text-ink">
              <ChatIcon className="text-brand-600" />
              Just ask
            </h3>
            <p className="mt-1 text-muted">
              Tell the assistant in your own words. If more than one item matches, it shows you cards to pick
              from.
            </p>
            {/* A picture of a chat, not a working chat. */}
            <div aria-hidden="true" className="mt-5 space-y-2 rounded-2xl bg-sunken p-3 text-sm">
              <p className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-sm bg-brand-600 px-3 py-2 text-white">
                I want to return the headphones from last week.
              </p>
              <p className="w-fit max-w-[85%] rounded-2xl rounded-bl-sm bg-raised px-3 py-2 text-ink shadow-xs">
                Here&apos;s your refund quote: <strong>$59.39</strong> back to your card. Tap{" "}
                <strong>Confirm return</strong> when you&apos;re ready.
              </p>
            </div>
          </Card>
        </div>
        <div className="mt-5 flex items-start gap-3 rounded-2xl bg-brand-50 p-4 text-brand-900 ring-1 ring-inset ring-brand-100">
          <ShieldCheckIcon className="mt-0.5 text-brand-600" />
          <p>
            <strong className="font-semibold">You&apos;re always in charge.</strong> The assistant can find your
            item and get a quote, but only you can confirm. Background noise or an unclear answer never counts as
            a “yes.”
          </p>
        </div>
      </section>

      {/* ---------- FAQ ---------- */}
      <section aria-labelledby="faq-title">
        <SectionHeading id="faq-title" eyebrow="Quick answers" title="Common questions" />
        <Card padding="none" className="mt-8 divide-y divide-line">
          <Faq q="Can I get store credit instead?">No. Refunds always go back to the original payment method.</Faq>
          <Faq q="My quote expired. What now?">Just start the return again and you&apos;ll get a fresh quote.</Faq>
          <Faq q="What if I tap Confirm twice?">
            You still get exactly one return and one refund. We never refund twice.
          </Faq>
          <Faq q="Can the assistant return something without asking me?">
            No. It can help, but a return is only created after you tap Confirm or say a clear “yes.”
          </Faq>
          <Faq q="My situation is unusual. Who can help?">
            Damaged items, disagreements, or anything out of the ordinary go to a person on our returns team.
          </Faq>
        </Card>
      </section>

      {/* ---------- CTA ---------- */}
      <section className="relative isolate flex flex-col items-center gap-3 overflow-hidden rounded-3xl bg-inverse px-6 py-12 text-center text-white focus-inverse">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(55%_70%_at_100%_0%,rgb(125_100_239/0.35),transparent_70%)]"
        />
        <UserIcon className="size-8 text-accent-300" />
        <h2 className="font-display text-2xl font-semibold sm:text-3xl">Ready to start a return?</h2>
        <p className="text-brand-200">Find the order, pick the item, and you&apos;re most of the way there.</p>
        <ButtonLink href="/orders" variant="inverse" size="lg" className="mt-3">
          Go to Orders &amp; returns
          <ArrowRightIcon className="size-4.5" />
        </ButtonLink>
      </section>
    </div>
  );
}

/* ---------- Page pieces ---------- */

function Station({ art, label }: { art: ReactNode; label: string }) {
  return (
    <li className="flex w-24 flex-col items-center text-center sm:w-36">
      {art}
      <span className="mt-2 text-sm font-semibold leading-tight text-ink sm:text-base">{label}</span>
    </li>
  );
}

function Fact({ icon, children }: { icon: ReactNode; children: ReactNode }) {
  return (
    <li className="inline-flex items-center gap-2 rounded-full bg-raised px-4 py-2 text-sm font-medium text-ink shadow-xs ring-1 ring-inset ring-line">
      <span className="text-brand-600">{icon}</span>
      {children}
    </li>
  );
}

function Rule({
  art,
  tone,
  icon,
  verdict,
  title,
  body,
}: {
  art: ReactNode;
  tone: BadgeTone;
  icon: ReactNode;
  verdict: string;
  title: string;
  body: string;
}) {
  return (
    <Card as="li" padding="sm" className="flex items-center gap-4">
      <div className="shrink-0 rounded-2xl bg-sunken p-1">{art}</div>
      <div className="min-w-0">
        <Badge tone={tone} size="md">
          {icon}
          {verdict}
        </Badge>
        <h3 className="mt-2 font-display text-lg font-semibold text-ink">{title}</h3>
        <p className="text-muted">{body}</p>
      </div>
    </Card>
  );
}

function MathChip({ icon, label, value, highlight }: { icon: ReactNode; label: string; value: string; highlight?: boolean }) {
  return (
    <div
      className={cn(
        "flex min-w-32 flex-col items-center rounded-2xl px-4 py-3 ring-1 ring-inset",
        highlight ? "bg-success-50 text-success-800 ring-success-200" : "bg-sunken text-ink ring-line",
      )}
    >
      <span className={cn("flex items-center gap-1.5 text-sm", highlight ? "font-semibold" : "text-muted")}>
        {icon}
        {label}
      </span>
      <span className="mt-1 font-display text-xl font-semibold">{value}</span>
    </div>
  );
}

function Operator({ children }: { children: ReactNode }) {
  return (
    <span aria-hidden="true" className="text-2xl font-semibold text-subtle">
      {children}
    </span>
  );
}

function Good({ children }: { children: ReactNode }) {
  return (
    <li className="flex items-start gap-2.5 rounded-xl bg-sunken p-3 text-ink">
      <span className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full bg-success-600 text-white">
        <CheckIcon className="size-3.5" strokeWidth={2.5} />
      </span>
      <span>{children}</span>
    </li>
  );
}

const laneTones = {
  success: { head: "bg-success-600 text-white", dot: "bg-success-50 text-success-700", line: "bg-success-200", ring: "ring-success-200" },
  brand: { head: "bg-brand-600 text-white", dot: "bg-brand-50 text-brand-700", line: "bg-brand-200", ring: "ring-brand-200" },
  warning: { head: "bg-warning-100 text-warning-900", dot: "bg-warning-50 text-warning-700", line: "bg-warning-200", ring: "ring-warning-200" },
};

function Lane({
  tone,
  icon,
  title,
  who,
  track,
}: {
  tone: keyof typeof laneTones;
  icon: ReactNode;
  title: string;
  who: string;
  track: { icon: ReactNode; label: string }[];
}) {
  const t = laneTones[tone];
  return (
    <div className={cn("overflow-hidden rounded-2xl bg-raised shadow-xs ring-1 ring-inset", t.ring)}>
      <div className={cn("flex items-center gap-3 px-5 py-4", t.head)}>
        {icon}
        <div>
          <h3 className="font-display text-lg font-semibold">{title}</h3>
          <p className="text-sm opacity-90">{who}</p>
        </div>
      </div>
      <ol className="relative flex justify-between px-5 py-6">
        <span aria-hidden="true" className={cn("absolute left-12 right-12 top-12 h-0.5 rounded-full", t.line)} />
        {track.map((s) => (
          <li key={s.label} className="relative flex w-20 flex-col items-center text-center">
            <span className={cn("grid size-12 place-items-center rounded-full ring-4 ring-raised", t.dot)}>{s.icon}</span>
            <span className="mt-2 text-xs font-semibold leading-tight text-ink sm:text-sm">{s.label}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

const statusTones = {
  warning: "bg-warning-50 ring-warning-200",
  success: "bg-success-50 ring-success-200",
  danger: "bg-danger-50 ring-danger-200",
} as const;

function Status({
  tone,
  icon,
  name,
  body,
}: {
  tone: keyof typeof statusTones;
  icon: ReactNode;
  name: string;
  body: string;
}) {
  return (
    <div className={cn("rounded-2xl p-4 ring-1 ring-inset", statusTones[tone])}>
      <Badge tone={tone} size="md">
        {icon}
        {name}
      </Badge>
      <p className="mt-2 text-ink">{body}</p>
    </div>
  );
}

function Faq({ q, children }: { q: string; children: ReactNode }) {
  return (
    <details className="group px-5">
      <summary className="flex min-h-14 cursor-pointer list-none items-center justify-between gap-4 font-semibold text-ink">
        {q}
        <span aria-hidden="true" className="grid size-7 shrink-0 place-items-center rounded-full bg-brand-50 text-brand-700 transition-transform duration-200 group-open:rotate-45">
          <span className="text-lg leading-none">+</span>
        </span>
      </summary>
      <p className="pb-4 text-muted">{children}</p>
    </details>
  );
}
