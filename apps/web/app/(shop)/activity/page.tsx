import { ActivityTimeline } from "@/components/activity/activity-timeline";
import { ArrowRightIcon, ClockIcon, HeadsetIcon, LockIcon, PackageIcon } from "@/components/icons";
import { ButtonLink } from "@/components/ui/button";
import { WebVitalsReporter } from "@/components/web-vitals";
import { serverApi, unwrap } from "@/lib/api-server";
import type { ActivityOut } from "@ai-commerce/contracts";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Your activity" };

const MILESTONES: ActivityOut["type"][] = [
  "placed_order",
  "order_delivered",
  "started_return",
  "refund_issued",
  "contacted_support",
  "wrote_review",
];

const RELATED = [
  { href: "/orders", label: "Orders & returns", Icon: PackageIcon },
  { href: "/support", label: "Support requests", Icon: HeadsetIcon },
];

export default async function ActivityPage() {
  const api = await serverApi();
  // Browsing can fill the recent window quickly, so milestones (orders, returns, support) are
  // fetched on their own too and merged in: they never scroll out behind a burst of page views.
  const [recent, milestones] = await Promise.all([
    api.GET("/v1/activity", { params: { query: { limit: 100 } } }).then(unwrap),
    api
      .GET("/v1/activity", { params: { query: { limit: 100, type: MILESTONES } } })
      .then((r) => r.data ?? []),
  ]);
  const byId = new Map([...recent, ...milestones].map((e) => [e.id, e]));
  const events = [...byId.values()].sort((a, b) => Date.parse(b.occurred_at) - Date.parse(a.occurred_at));
  const hasSample = events.some((e) => e.is_sample);
  // Rendered on the server so "Today" can't disagree with the browser on hydration.
  const now = new Date().toISOString();

  return (
    <div className="pb-24 sm:pb-8 sm:pt-2">
      <WebVitalsReporter route="activity" />
      <h1 className="font-display text-3xl font-semibold text-ink sm:text-4xl">Your activity</h1>
      <p className="mt-2 max-w-2xl text-muted">
        What you searched, viewed, bought, and returned, newest first.
      </p>

      {events.length === 0 ? (
        <div className="mt-8 flex flex-col items-center rounded-3xl bg-mesh-light px-6 py-16 text-center">
          <span className="grid size-16 place-items-center rounded-2xl bg-raised text-brand-600 shadow-md">
            <ClockIcon className="size-8" />
          </span>
          <h2 className="mt-6 font-display text-2xl font-semibold text-ink">Nothing here yet</h2>
          <p className="mt-2 max-w-sm text-muted">Searches, products you view, and orders will show up here.</p>
          <ButtonLink href="/" className="mt-6">
            Start shopping
            <ArrowRightIcon className="size-4.5" />
          </ButtonLink>
        </div>
      ) : (
        // minmax(0,1fr), not the implicit auto column: a long row (the filter chips) must scroll
        // inside the column rather than stretch it past the screen on phones.
        <div className="mt-6 grid grid-cols-[minmax(0,1fr)] items-start gap-8 sm:mt-8 lg:grid-cols-[minmax(0,1fr)_20rem] lg:gap-10">
          <ActivityTimeline events={events} now={now} className="min-w-0" />

          <aside aria-labelledby="activity-about" className="min-w-0 space-y-4 lg:sticky lg:top-36">
            <div className="rounded-3xl border border-line bg-raised p-5 shadow-xs">
              <h2 id="activity-about" className="flex items-center gap-2 font-display text-lg font-semibold text-ink">
                <LockIcon className="size-4.5 text-brand-600" />
                Private to you
              </h2>
              <p className="mt-2 text-sm text-muted">
                Only you can see this history: your recent browsing plus your orders, returns, and support requests.
                Repeats in a row are folded together.
              </p>
              {hasSample ? (
                <p className="mt-3 rounded-xl bg-sunken px-3 py-2 text-xs text-muted">
                  <strong className="font-semibold text-ink">Sample activity</strong> was seeded for the demo store and is
                  labeled on each event.
                </p>
              ) : null}
            </div>
            <nav aria-label="Related pages" className="rounded-3xl border border-line bg-raised p-2 shadow-xs">
              <ul>
                {RELATED.map(({ href, label, Icon }) => (
                  <li key={href}>
                    <Link
                      href={href}
                      className="group flex min-h-11 items-center gap-3 rounded-2xl px-3 py-2 text-sm font-semibold text-ink transition-colors hover:bg-neutral-50"
                    >
                      <Icon className="size-4.5 text-brand-600" />
                      <span className="flex-1">{label}</span>
                      <ArrowRightIcon className="size-4 text-muted transition-transform duration-200 ease-snappy group-hover:translate-x-0.5" />
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          </aside>
        </div>
      )}
    </div>
  );
}
