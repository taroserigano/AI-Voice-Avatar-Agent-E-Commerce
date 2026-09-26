import { ActivityTimeline } from "@/components/activity/activity-timeline";
import { ArrowRightIcon, ClockIcon, InfoIcon } from "@/components/icons";
import { ButtonLink } from "@/components/ui/button";
import { WebVitalsReporter } from "@/components/web-vitals";
import { serverApi, unwrap } from "@/lib/api-server";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Your activity" };

export default async function ActivityPage() {
  const api = await serverApi();
  const events = await unwrap(await api.GET("/v1/activity", { params: { query: { limit: 60 } } }));
  const hasSample = events.some((e) => e.is_sample);
  // Rendered on the server only, so "Today" can't disagree with the client on hydration.
  const now = new Date();

  return (
    <div className="mx-auto max-w-3xl pb-8 sm:pt-2">
      <WebVitalsReporter route="activity" />
      <h1 className="font-display text-3xl font-semibold text-ink sm:text-4xl">Your activity</h1>
      <p className="mt-2 text-muted">What you searched, viewed, bought, and returned, newest first. Only you can see this.</p>

      {hasSample ? (
        <p className="mt-5 flex items-start gap-2.5 rounded-2xl border border-line bg-raised px-4 py-3 text-sm text-muted shadow-xs">
          <InfoIcon className="mt-px size-4.5 shrink-0 text-brand-600" />
          <span>
            <strong className="font-semibold text-ink">Sample activity.</strong> Some of this history was seeded for the demo
            store and is labeled on each event.
          </span>
        </p>
      ) : null}

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
        <div className="mt-8 sm:mt-10">
          <ActivityTimeline events={events} now={now} />
        </div>
      )}
    </div>
  );
}
