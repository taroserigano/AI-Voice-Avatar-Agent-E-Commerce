"use client";

import { FilterTabs } from "@/components/account/filter-tabs";
import { AlertCircleIcon, ArrowRightIcon, ChevronDownIcon, CloseIcon, ExternalLinkIcon, MapIcon, SearchIcon } from "@/components/icons";
import { LocateIcon } from "@/components/orders/order-icons";
import { Badge } from "@/components/ui/badge";
import { Button, buttonClasses } from "@/components/ui/button";
import { inputClasses } from "@/components/ui/field";
import { cn } from "@/lib/cn";
import { byDistance, findPlace, formatMiles, PLACE_EXAMPLES, type Place } from "@/lib/geo";
import { DAY_NAMES, distinctServices, hoursText } from "@/lib/store-hours";
import { directionsUrl, storePath, telHref } from "@/lib/stores";
import type { StoreOut } from "@ai-commerce/contracts";
import Link from "next/link";
import { useRef, useState, type FormEvent } from "react";
import { EmbeddedMap, InteractiveMap, OverviewMap, type NumberedStore } from "./store-map";

const ALL = "__all__";
const listFormat = new Intl.ListFormat("en-US", { style: "long", type: "conjunction" });

type Origin = Place & { source: "search" | "device" };

const NOT_FOUND = {
  unknown_zip: "We don't have that ZIP code. Our stores are all around Dallas-Fort Worth; try a DFW ZIP like 75204.",
  unknown_place: `We couldn't find that place. Try a DFW city or ZIP, like ${listFormat.format(PLACE_EXAMPLES.map((e) => e))}.`,
  empty: "Enter a ZIP code or a city.",
} as const;

/**
 * Store list + map. Search by ZIP or city (a built-in table of DFW places; nothing is sent to a
 * geocoding service) or share your location (stays in the browser) to sort stores by straight-line
 * distance. The list scrolls with the page; on large screens the map sticks below the header. On
 * phones a List / Map switch shows one at a time.
 */
export function StoreLocator({
  stores,
  mapsKey,
  status,
}: {
  stores: StoreOut[];
  mapsKey: string | null;
  /** Store code → "Closes 10 PM" / "Opens 7 AM tomorrow", worded on the server. */
  status: Record<string, string>;
}) {
  const [code, setCode] = useState(stores[0]?.code);
  const [service, setService] = useState<string>(ALL);
  const [view, setView] = useState<"list" | "map">("list");
  const [mapMode, setMapMode] = useState<"overview" | "street">("overview");
  const [query, setQuery] = useState("");
  const [origin, setOrigin] = useState<Origin | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [locating, setLocating] = useState(false);
  const viewTabs = useRef<HTMLDivElement>(null);
  const { common, varying } = distinctServices(stores);

  const filtered = service === ALL ? stores : stores.filter((s) => s.services.includes(service));
  const ordered: { store: StoreOut; miles: number | null }[] = origin
    ? byDistance(
        filtered.map((s) => ({ store: s, lat: s.latitude, lng: s.longitude })),
        origin,
      ).map(({ item, miles }) => ({ store: item.store, miles }))
    : filtered.map((s) => ({ store: s, miles: null }));
  const shown: NumberedStore[] = ordered.map((o, i) => ({ ...o, number: i + 1 }));
  const selected = shown.find(({ store }) => store.code === code)?.store ?? shown[0]?.store ?? stores[0];
  if (!selected) return <p className="mt-6 text-muted">No stores are open yet.</p>;

  function applyOrigin(next: Origin) {
    setOrigin(next);
    setError(null);
    const pool = service === ALL ? stores : stores.filter((s) => s.services.includes(service));
    const nearest = byDistance(
      pool.map((s) => ({ code: s.code, lat: s.latitude, lng: s.longitude })),
      next,
    )[0];
    if (nearest) setCode(nearest.item.code);
  }

  function search(e: FormEvent) {
    e.preventDefault();
    const found = findPlace(query);
    if (found.ok) applyOrigin({ ...found.place, source: "search" });
    else setError(NOT_FOUND[found.reason]);
  }

  function locate() {
    setError(null);
    if (!("geolocation" in navigator)) {
      setError("This browser can't share your location. Search by ZIP code or city instead.");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false);
        setQuery("");
        applyOrigin({ lat: pos.coords.latitude, lng: pos.coords.longitude, label: "your location", source: "device" });
      },
      (err) => {
        setLocating(false);
        setError(
          err.code === err.PERMISSION_DENIED
            ? "Location access is off for this site. Search by ZIP code or city instead."
            : "We couldn't get your location just now. Search by ZIP code or city instead.",
        );
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 5 * 60 * 1000 },
    );
  }

  function clearOrigin() {
    setOrigin(null);
    setQuery("");
    setError(null);
  }

  function showOnMap(storeCode: string) {
    setCode(storeCode);
    // On phones the list and the map take turns; jump to the map (large screens show both).
    if (window.matchMedia("(max-width: 63.99rem)").matches) {
      setView("map");
      // The list collapses, so bring the List/Map switch and the map back into view.
      requestAnimationFrame(() => viewTabs.current?.scrollIntoView({ block: "start" }));
    }
  }

  const nearestMiles = shown[0]?.miles ?? null;
  const originName = origin ? (origin.source === "device" ? "your location" : origin.label) : null;
  const statusText = `Showing ${shown.length} ${shown.length === 1 ? "store" : "stores"}${
    originName ? `, nearest to ${originName} first` : ""
  }`;

  return (
    <div className="mt-6">
      <form role="search" aria-label="Find a store near you" onSubmit={search} className="max-w-3xl">
        <label htmlFor="store-search" className="block text-sm font-semibold text-ink">
          ZIP code or city
        </label>
        <div className="mt-1.5 flex flex-col gap-2 sm:flex-row">
          <div className="relative min-w-0 flex-1">
            <SearchIcon className="pointer-events-none absolute left-3.5 top-1/2 size-4.5 -translate-y-1/2 text-muted" />
            <input
              id="store-search"
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. 75204 or Plano"
              autoComplete="postal-code"
              enterKeyHint="search"
              aria-invalid={error ? true : undefined}
              aria-describedby={error ? "store-search-error store-search-hint" : "store-search-hint"}
              className={cn(inputClasses, "pl-10")}
            />
          </div>
          <div className="flex gap-2">
            <Button type="submit" className="flex-1 sm:flex-none">
              Find stores
            </Button>
            <Button type="button" variant="outline" loading={locating} onClick={locate} className="flex-1 sm:flex-none">
              {locating ? null : <LocateIcon className="size-4.5" />}
              Use my location
            </Button>
          </div>
        </div>
        <p id="store-search-hint" className="mt-2 text-sm text-muted">
          Distances are straight-line miles from the ZIP or city center. Your location stays in your browser.
        </p>
        {error ? (
          <p id="store-search-error" role="alert" className="mt-2 flex items-start gap-1.5 text-sm font-medium text-danger-700">
            <AlertCircleIcon className="mt-px size-4" />
            <span>{error}</span>
          </p>
        ) : null}
      </form>

      {origin ? (
        <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 rounded-2xl bg-brand-50 px-4 py-2.5 text-sm text-brand-900 ring-1 ring-inset ring-brand-100">
          <span>
            Sorted by distance from <strong className="font-semibold">{originName}</strong>
            {nearestMiles !== null && nearestMiles > 60
              ? `. The nearest store is ${Math.round(nearestMiles)} mi away; our stores are all around Dallas-Fort Worth.`
              : null}
          </span>
          <Button variant="ghost" size="sm" onClick={clearOrigin} className="-my-1 ml-auto text-brand-800">
            <CloseIcon className="size-4" />
            Clear
            <span className="sr-only"> distance sort</span>
          </Button>
        </div>
      ) : null}

      {varying.length > 0 ? (
        <div className="mt-5 space-y-2">
          <FilterTabs
            label="Filter stores by service"
            options={[
              { value: ALL, label: "All stores", count: stores.length },
              ...varying.map((svc) => ({
                value: svc,
                label: svc,
                count: stores.filter((s) => s.services.includes(svc)).length,
              })),
            ]}
            value={service}
            onChange={setService}
          />
          {common.length > 0 ? (
            <p className="text-sm text-muted">Every store has {listFormat.format(common.map((c) => c.toLowerCase()))}.</p>
          ) : null}
        </div>
      ) : null}
      <p role="status" className="sr-only">
        {statusText}
      </p>

      <div ref={viewTabs} className="scroll-mt-44 lg:hidden">
        <FilterTabs
          label="Show stores as"
          options={[
            { value: "list", label: "List" },
            { value: "map", label: "Map" },
          ]}
          value={view}
          onChange={setView}
          className="mt-4"
        />
      </div>

      <div className="mt-5 grid items-start gap-6 lg:grid-cols-[24rem_minmax(0,1fr)]">
        <ol aria-label="Store list" className={cn("space-y-3", view === "map" && "max-lg:hidden")}>
          {shown.map(({ store: s, number, miles }) => (
            <StoreCard
              key={s.code}
              store={s}
              number={number}
              miles={miles}
              status={status[s.code]}
              selected={s.code === selected.code}
              highlight={service === ALL ? null : service}
              onShow={() => showOnMap(s.code)}
            />
          ))}
        </ol>

        <div className={cn("lg:sticky lg:top-36", view === "list" && "max-lg:hidden")}>
          {!mapsKey ? (
            <FilterTabs
              label="Map view"
              options={[
                { value: "overview", label: "All stores" },
                { value: "street", label: "Street map" },
              ]}
              value={mapMode}
              onChange={setMapMode}
              className="mb-3"
            />
          ) : null}
          <div
            className={cn(
              "h-[60vh] min-h-80 overflow-hidden rounded-3xl border border-line bg-sunken shadow-xs lg:max-h-192",
              mapsKey ? "lg:h-[calc(100vh-11rem)]" : "lg:h-[calc(100vh-15rem)]",
            )}
          >
            {mapsKey ? (
              <InteractiveMap stores={stores} shown={shown} mapsKey={mapsKey} selected={selected} onSelect={setCode} />
            ) : mapMode === "overview" ? (
              <OverviewMap allStores={stores} shown={shown} selectedCode={selected.code} origin={origin} onSelect={setCode} />
            ) : (
              <EmbeddedMap store={selected} />
            )}
          </div>
          <p className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted">
            <MapIcon className="size-4 shrink-0 text-brand-600" />
            <span>
              Selected: <span className="font-semibold text-ink">{selected.name}</span>, {selected.address_line1},{" "}
              {selected.city}
            </span>
            <Link
              href={storePath(selected)}
              className="font-semibold text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700"
            >
              Store details<span className="sr-only"> for {selected.name}</span>
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

function StoreCard({
  store: s,
  number,
  miles,
  status,
  selected,
  highlight,
  onShow,
}: {
  store: StoreOut;
  number: number;
  miles: number | null;
  status: string | undefined;
  selected: boolean;
  highlight: string | null;
  onShow: () => void;
}) {
  return (
    <li
      className={cn(
        "rounded-3xl border bg-raised p-4 shadow-xs transition-[border-color,box-shadow] duration-200 sm:p-5",
        selected ? "border-brand-600 ring-2 ring-brand-600" : "border-line",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <h2 className="flex items-center gap-2.5 font-display text-lg font-semibold text-ink">
          <span
            aria-hidden="true"
            className={cn(
              "grid size-7 shrink-0 place-items-center rounded-full text-xs font-semibold tabular-nums",
              selected ? "bg-brand-600 text-white" : "bg-brand-50 text-brand-700",
            )}
          >
            {number}
          </span>
          {s.name}
        </h2>
        <div className="mt-1 flex shrink-0 flex-col items-end gap-1">
          <Badge tone={s.open_now ? "success" : "neutral"} dot>
            {s.open_now ? "Open now" : "Closed"}
          </Badge>
          {miles !== null ? (
            <span className="text-sm font-semibold tabular-nums text-ink">
              {formatMiles(miles)}
              <span className="sr-only"> away</span>
            </span>
          ) : null}
        </div>
      </div>
      {status ? <p className="mt-1 pl-9.5 text-sm font-medium text-ink-soft">{status}</p> : null}

      <address className="mt-3 text-sm not-italic leading-relaxed text-ink-soft">
        {s.address_line1}
        <br />
        {s.city}, {s.state} {s.postal_code}
        <br />
        <a
          className="font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700"
          href={telHref(s.phone)}
        >
          {s.phone}
        </a>
        <span className="text-xs text-muted"> (demo number)</span>
      </address>

      <details className="group/hours mt-2 text-sm">
        <summary className="inline-flex min-h-11 cursor-pointer list-none items-center gap-1.5 font-semibold text-ink [&::-webkit-details-marker]:hidden">
          Today: {hoursText(s.today_hours.opens, s.today_hours.closes)}
          <span className="font-normal text-muted">· All hours</span>
          <ChevronDownIcon className="size-4 text-muted transition-transform duration-200 group-open/hours:rotate-180" />
        </summary>
        <table className="mb-1 w-full max-w-xs">
          <caption className="sr-only">Opening hours for {s.name}</caption>
          <tbody>
            {s.hours.map((h) => {
              const today = h.day === s.today_hours.day;
              return (
                <tr key={h.day} className={cn(today && "bg-brand-50 text-brand-900")}>
                  <th
                    scope="row"
                    className={cn("rounded-l-lg py-1 pl-2 pr-4 text-left", today ? "font-semibold" : "font-normal text-muted")}
                  >
                    {DAY_NAMES[h.day] ?? h.day}
                    {today ? <span className="ml-1.5 text-xs font-medium text-brand-700">(today)</span> : null}
                  </th>
                  <td className={cn("rounded-r-lg py-1 pr-2 tabular-nums", today ? "font-semibold" : "text-ink")}>
                    {hoursText(h.opens, h.closes)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </details>

      <p className="mt-1 text-xs leading-relaxed text-muted">
        <span className="sr-only">Services: </span>
        {s.services.map((svc, i) => (
          <span key={svc}>
            {i > 0 ? <span aria-hidden="true"> · </span> : null}
            <span className={cn(svc === highlight && "font-semibold text-ink")}>{svc}</span>
            {i < s.services.length - 1 ? <span className="sr-only">,</span> : null}
          </span>
        ))}
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button variant={selected ? "secondary" : "outline"} size="sm" aria-pressed={selected} onClick={onShow}>
          <MapIcon className="size-4" />
          {selected ? "Shown on map" : "Show on map"}
        </Button>
        <a
          href={directionsUrl(s)}
          target="_blank"
          rel="noopener noreferrer"
          className={buttonClasses("ghost", "sm", "text-brand-700")}
        >
          Directions
          <ExternalLinkIcon className="size-4" />
          <span className="sr-only"> to {s.name} (opens Google Maps)</span>
        </a>
        <Link href={storePath(s)} className={buttonClasses("ghost", "sm", "text-brand-700")}>
          Details
          <ArrowRightIcon className="size-4" />
          <span className="sr-only"> for {s.name}</span>
        </Link>
      </div>
    </li>
  );
}
