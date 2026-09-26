"use client";

import { formatTime } from "@/lib/format";
import type { StoreOut } from "@ai-commerce/contracts";
import { useEffect, useRef, useState } from "react";

const DAY_NAMES: Record<string, string> = {
  mon: "Monday",
  tue: "Tuesday",
  wed: "Wednesday",
  thu: "Thursday",
  fri: "Friday",
  sat: "Saturday",
  sun: "Sunday",
};

function hoursText(opens: string | null, closes: string | null): string {
  return opens && closes ? `${formatTime(opens)} – ${formatTime(closes)}` : "Closed";
}

function directionsUrl(s: StoreOut): string {
  return `https://www.google.com/maps/dir/?api=1&destination=${s.latitude},${s.longitude}`;
}

// --- Google Maps JavaScript API (only when a key is configured) --------------------------

type LatLng = { lat: number; lng: number };
type GoogleMaps = {
  Map: new (el: HTMLElement, opts: { center: LatLng; zoom: number; mapId?: string }) => {
    panTo(p: LatLng): void;
    setZoom(z: number): void;
  };
  Marker: new (opts: { position: LatLng; map: unknown; title: string; label?: string }) => {
    addListener(event: string, fn: () => void): void;
  };
};
declare global {
  interface Window {
    google?: { maps: GoogleMaps };
    __larkspurMapsReady?: () => void;
  }
}

let mapsPromise: Promise<GoogleMaps> | null = null;
function loadGoogleMaps(key: string): Promise<GoogleMaps> {
  mapsPromise ??= new Promise((resolve, reject) => {
    window.__larkspurMapsReady = () => (window.google ? resolve(window.google.maps) : reject(new Error("no maps")));
    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}&v=weekly&callback=__larkspurMapsReady`;
    script.async = true;
    script.onerror = () => reject(new Error("Google Maps failed to load"));
    document.head.appendChild(script);
  });
  return mapsPromise;
}

function InteractiveMap({
  stores,
  mapsKey,
  selected,
  onSelect,
}: {
  stores: StoreOut[];
  mapsKey: string;
  selected: StoreOut;
  onSelect: (code: string) => void;
}) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<InstanceType<GoogleMaps["Map"]> | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    loadGoogleMaps(mapsKey)
      .then((maps) => {
        if (cancelled || !el.current) return;
        const center = { lat: 32.93, lng: -96.82 };
        map.current = new maps.Map(el.current, { center, zoom: 9 });
        stores.forEach((s, i) => {
          const marker = new maps.Marker({
            position: { lat: s.latitude, lng: s.longitude },
            map: map.current,
            title: s.name,
            label: String(i + 1),
          });
          marker.addListener("click", () => onSelect(s.code));
        });
      })
      .catch(() => setFailed(true));
    return () => {
      cancelled = true;
    };
    // The markers are drawn once; selection only pans the map.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapsKey, stores]);

  useEffect(() => {
    map.current?.panTo({ lat: selected.latitude, lng: selected.longitude });
    map.current?.setZoom(12);
  }, [selected]);

  if (failed) return <EmbeddedMap store={selected} />;
  return <div ref={el} role="region" aria-label="Map of all Larkspur stores" className="h-full min-h-80 w-full" />;
}

// --- Keyless embed: one store at a time -------------------------------------------------

function EmbeddedMap({ store }: { store: StoreOut }) {
  const src = `https://maps.google.com/maps?q=${store.latitude},${store.longitude}&z=14&output=embed`;
  return (
    <iframe
      key={store.code}
      title={`Map showing ${store.name}, ${store.address_line1}, ${store.city}`}
      src={src}
      loading="lazy"
      referrerPolicy="no-referrer-when-downgrade"
      className="h-full min-h-80 w-full border-0"
    />
  );
}

export function StoreLocator({ stores, mapsKey }: { stores: StoreOut[]; mapsKey: string | null }) {
  const [code, setCode] = useState(stores[0]?.code);
  const selected = stores.find((s) => s.code === code) ?? stores[0];
  if (!selected) return <p className="mt-6">No stores are open yet.</p>;

  return (
    <div className="mt-6 grid gap-6 lg:grid-cols-[22rem_1fr]">
      <ol aria-label="Store list" className="space-y-3 lg:max-h-160 lg:overflow-y-auto lg:pr-2">
        {stores.map((s, i) => {
          const isSelected = s.code === selected.code;
          return (
            <li key={s.code} className={`rounded-2xl border bg-white p-4 ${isSelected ? "border-brand-700 ring-2 ring-brand-700" : "border-line"}`}>
              <div className="flex items-start justify-between gap-2">
                <h2 className="font-semibold">
                  <span className="mr-2 inline-flex h-6 w-6 items-center justify-center rounded-full bg-brand-700 text-xs text-white" aria-hidden="true">
                    {i + 1}
                  </span>
                  {s.name}
                </h2>
                <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${s.open_now ? "bg-emerald-100 text-emerald-900" : "bg-stone-200 text-stone-800"}`}>
                  {s.open_now ? "Open now" : "Closed"}
                </span>
              </div>
              <address className="mt-2 text-sm not-italic text-stone-700">
                {s.address_line1}
                <br />
                {s.city}, {s.state} {s.postal_code}
                <br />
                <a className="underline underline-offset-2" href={`tel:${s.phone.replace(/[^\d+]/g, "")}`}>
                  {s.phone}
                </a>
              </address>
              <p className="mt-2 text-sm">
                Today: {hoursText(s.today_hours.opens, s.today_hours.closes)}
              </p>
              <details className="mt-1 text-sm">
                <summary className="cursor-pointer text-muted">All hours</summary>
                <table className="mt-1">
                  <tbody>
                    {s.hours.map((h) => (
                      <tr key={h.day}>
                        <th scope="row" className="pr-4 text-left font-normal text-muted">
                          {DAY_NAMES[h.day]}
                        </th>
                        <td>{hoursText(h.opens, h.closes)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
              <p className="mt-2 text-xs text-muted">{s.services.join(" · ")}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  aria-pressed={isSelected}
                  onClick={() => setCode(s.code)}
                  className="min-h-10 rounded-full border border-brand-700 px-4 text-sm font-semibold text-brand-700 hover:bg-brand-50"
                >
                  {isSelected ? "Shown on map" : "Show on map"}
                </button>
                <a
                  href={directionsUrl(s)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex min-h-10 items-center rounded-full px-4 text-sm font-semibold text-brand-700 underline underline-offset-2"
                >
                  Directions<span className="sr-only"> to {s.name} (opens Google Maps)</span>
                </a>
              </div>
            </li>
          );
        })}
      </ol>
      <div className="overflow-hidden rounded-2xl border border-line bg-stone-100 lg:sticky lg:top-4 lg:h-160">
        {mapsKey ? (
          <InteractiveMap stores={stores} mapsKey={mapsKey} selected={selected} onSelect={setCode} />
        ) : (
          <EmbeddedMap store={selected} />
        )}
      </div>
    </div>
  );
}
