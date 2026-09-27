import { CheckIcon, ChevronRightIcon, ClockIcon, ExternalLinkIcon, MapIcon, ReturnIcon } from "@/components/icons";
import { PhoneIcon } from "@/components/orders/order-icons";
import { Badge } from "@/components/ui/badge";
import { buttonClasses } from "@/components/ui/button";
import { serverApi, unwrap } from "@/lib/api-server";
import { cn } from "@/lib/cn";
import { byDistance, formatMiles } from "@/lib/geo";
import { DAY_NAMES, hoursText, openingText } from "@/lib/store-hours";
import { directionsUrl, embedUrl, findStore, storePath, telHref } from "@/lib/stores";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { cache } from "react";

// One read per request for the metadata and the page. Unknown codes are a 404.
const loadStores = cache(async () => {
  const api = await serverApi();
  return api.GET("/v1/stores").then(unwrap);
});

async function loadStore(id: string) {
  const stores = await loadStores();
  const store = findStore(stores, id);
  if (!store) notFound();
  return { store, stores };
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { store } = await loadStore((await params).id);
  return { title: store.name, description: `${store.name}, ${store.address_line1}, ${store.city}: hours and services.` };
}

export default async function StorePage({ params }: { params: Promise<{ id: string }> }) {
  const { store: s, stores } = await loadStore((await params).id);
  // Worded on the server, at the same moment the API decided open_now.
  const opening = openingText(s, s.open_now, new Date());
  const nearby = byDistance(
    stores.filter((o) => o.code !== s.code).map((o) => ({ store: o, lat: o.latitude, lng: o.longitude })),
    { lat: s.latitude, lng: s.longitude },
  ).slice(0, 3);

  return (
    <div className="pb-24 pt-2 sm:pb-8 sm:pt-4">
      <nav aria-label="Breadcrumb">
        <ol className="flex items-center gap-x-1.5 text-sm text-muted">
          <li className="flex shrink-0 items-center gap-1.5">
            <Link
              href="/stores"
              className="inline-flex min-h-11 items-center rounded-md hover:text-ink hover:underline hover:underline-offset-4 sm:min-h-8"
            >
              Stores
            </Link>
            <ChevronRightIcon className="size-3.5 text-subtle" />
          </li>
          <li aria-current="page" className="min-w-0 truncate font-medium text-ink">
            {s.name}
          </li>
        </ol>
      </nav>

      <header className="mt-3 sm:mt-4">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <h1 className="font-display text-3xl font-semibold tracking-tight text-ink sm:text-4xl">{s.name}</h1>
          <Badge tone={s.open_now ? "success" : "neutral"} dot size="md">
            {s.open_now ? "Open now" : "Closed"}
          </Badge>
        </div>
        <p className="mt-2 text-muted">
          {opening} · {s.city}, {s.state}
          <span className="block text-sm sm:inline">
            <span className="hidden sm:inline"> · </span>A demo location: the street address and phone number are made up.
          </span>
        </p>
      </header>

      <div className="mt-8 grid gap-8 lg:grid-cols-12 lg:gap-10">
        <div className="space-y-6 lg:col-span-5">
          <section aria-labelledby="visit-heading" className="rounded-3xl border border-line bg-raised p-5 shadow-xs sm:p-6">
            <h2 id="visit-heading" className="font-display text-lg font-semibold text-ink">
              Address
            </h2>
            <address className="mt-3 text-sm not-italic leading-relaxed text-ink-soft">
              {s.address_line1}
              <br />
              {s.city}, {s.state} {s.postal_code}
            </address>
            <p className="mt-3 flex items-center gap-2 text-sm">
              <PhoneIcon className="size-4 text-brand-600" />
              <a
                href={telHref(s.phone)}
                className="font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700"
              >
                {s.phone}
              </a>
              <Badge tone="neutral">Demo number</Badge>
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              <a href={directionsUrl(s)} target="_blank" rel="noopener noreferrer" className={buttonClasses("primary", "md")}>
                <MapIcon className="size-4.5" />
                Get directions
                <ExternalLinkIcon className="size-4" />
                <span className="sr-only"> (opens Google Maps)</span>
              </a>
            </div>
          </section>

          <section aria-labelledby="hours-heading" className="rounded-3xl border border-line bg-raised p-5 shadow-xs sm:p-6">
            <h2 id="hours-heading" className="flex items-center gap-2 font-display text-lg font-semibold text-ink">
              <ClockIcon className="size-5 text-brand-600" />
              Hours
            </h2>
            <table className="mt-3 w-full text-sm">
              <caption className="sr-only">Opening hours for {s.name}, local time</caption>
              <tbody>
                {s.hours.map((h) => {
                  const today = h.day === s.today_hours.day;
                  return (
                    <tr key={h.day} className={cn(today && "bg-brand-50 text-brand-900")}>
                      <th
                        scope="row"
                        className={cn("rounded-l-lg py-2 pl-3 pr-4 text-left", today ? "font-semibold" : "font-normal text-muted")}
                      >
                        {DAY_NAMES[h.day] ?? h.day}
                        {today ? <span className="ml-1.5 text-xs font-medium text-brand-700">(today)</span> : null}
                      </th>
                      <td className={cn("rounded-r-lg py-2 pr-3 text-right tabular-nums", today ? "font-semibold" : "text-ink")}>
                        {hoursText(h.opens, h.closes)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="mt-3 text-xs text-muted">Central Time. Holiday hours may differ.</p>
          </section>

          <section aria-labelledby="services-heading" className="rounded-3xl border border-line bg-raised p-5 shadow-xs sm:p-6">
            <h2 id="services-heading" className="font-display text-lg font-semibold text-ink">
              Services
            </h2>
            <ul className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
              {s.services.map((svc) => (
                <li key={svc} className="flex items-center gap-2 text-ink-soft">
                  <CheckIcon className="size-4 text-success-700" />
                  {svc}
                </li>
              ))}
            </ul>
            {s.services.includes("Return drop-off") ? (
              <p className="mt-4 flex items-start gap-2 rounded-2xl bg-sunken px-3.5 py-3 text-sm text-ink-soft">
                <ReturnIcon className="mt-px size-4.5 shrink-0 text-brand-600" />
                <span>
                  Drop off a packaged online return here.{" "}
                  <Link
                    href="/help/returns"
                    className="font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700"
                  >
                    How returns work
                  </Link>
                </span>
              </p>
            ) : null}
          </section>
        </div>

        <div className="space-y-6 lg:col-span-7">
          <div className="h-80 overflow-hidden rounded-3xl border border-line bg-sunken shadow-xs sm:h-96">
            <iframe
              title={`Street map showing ${s.name}, ${s.address_line1}, ${s.city}`}
              src={embedUrl(s, 15)}
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
              className="size-full border-0"
            />
          </div>

          <section aria-labelledby="nearby-heading">
            <h2 id="nearby-heading" className="font-display text-xl font-semibold text-ink">
              Nearby stores
            </h2>
            <ul className="mt-3 divide-y divide-line rounded-3xl border border-line bg-raised shadow-xs">
              {nearby.map(({ item: { store: o }, miles }) => (
                <li key={o.code} className="flex items-center justify-between gap-4 px-5 py-3.5">
                  <div className="min-w-0">
                    <Link
                      href={storePath(o)}
                      className="font-semibold text-ink hover:text-brand-700 hover:underline hover:underline-offset-4"
                    >
                      {o.name}
                    </Link>
                    <p className="text-sm text-muted">
                      {o.address_line1}, {o.city} · {o.open_now ? "Open now" : "Closed"}
                    </p>
                  </div>
                  <span className="shrink-0 text-sm font-semibold tabular-nums text-ink">
                    {formatMiles(miles)}
                    <span className="sr-only"> away</span>
                  </span>
                </li>
              ))}
            </ul>
            <Link
              href="/stores"
              className="mt-3 inline-flex min-h-11 items-center gap-1.5 text-sm font-semibold text-brand-700 hover:text-brand-900"
            >
              See all {stores.length} stores on the map
              <ChevronRightIcon className="size-4" />
            </Link>
          </section>
        </div>
      </div>
    </div>
  );
}
