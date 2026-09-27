"use client";

import { cn } from "@/lib/cn";
import { formatMiles, milesBetween, spreadApart, type LatLng, type Place } from "@/lib/geo";
import { embedUrl } from "@/lib/stores";
import type { StoreOut } from "@ai-commerce/contracts";
import { useEffect, useRef, useState } from "react";

export type NumberedStore = { store: StoreOut; number: number; miles: number | null };

// --- Overview: every store on one to-scale sketch of DFW (no map service involved) --------

// Reference points for orientation: cities without a store, so labels don't sit under pins.
const LANDMARKS: (LatLng & { name: string })[] = [
  { name: "Downtown Dallas", lat: 32.7801, lng: -96.8005 },
  { name: "Fort Worth", lat: 32.7555, lng: -97.3308 },
  { name: "Denton", lat: 33.2148, lng: -97.1331 },
  { name: "Carrollton", lat: 32.9756, lng: -96.89 },
  { name: "Mesquite", lat: 32.7668, lng: -96.5992 },
  { name: "Grand Prairie", lat: 32.746, lng: -96.9978 },
  { name: "Lewisville", lat: 33.0462, lng: -96.9942 },
];

const MILES_PER_DEG_LAT = 69.0;
// Pins are 32px (40px when selected); keep their centers this far apart so none overlap.
const PIN_GAP_PX = 40;

type Frame = { x0: number; y1: number; spanX: number; spanY: number; kx: number };

/** Fit the points into a w×h box (equirectangular, x scaled by cos(latitude)), with padding. */
function frameFor(points: LatLng[], w: number, h: number): Frame {
  const midLat = points.reduce((s, p) => s + p.lat, 0) / points.length;
  const kx = Math.cos((midLat * Math.PI) / 180);
  const xs = points.map((p) => p.lng * kx);
  const ys = points.map((p) => p.lat);
  const [minX, maxX, minY, maxY] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const aspect = w / h;
  let spanX = Math.max(maxX - minX, 0.05) * 1.3;
  let spanY = Math.max(maxY - minY, 0.05) * 1.3;
  if (spanX / spanY < aspect) spanX = spanY * aspect;
  else spanY = spanX / aspect;
  return { x0: (minX + maxX) / 2 - spanX / 2, y1: (minY + maxY) / 2 + spanY / 2, spanX, spanY, kx };
}

const toPct = (f: Frame, p: LatLng) => ({
  left: ((p.lng * f.kx - f.x0) / f.spanX) * 100,
  top: ((f.y1 - p.lat) / f.spanY) * 100,
});

export function OverviewMap({
  allStores,
  shown,
  selectedCode,
  origin,
  onSelect,
}: {
  /** Every store, so the frame doesn't jump when a filter hides some. */
  allStores: StoreOut[];
  shown: NumberedStore[];
  selectedCode: string;
  origin: (Place & { source: "search" | "device" }) | null;
  onSelect: (code: string) => void;
}) {
  const box = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState<{ w: number; h: number } | null>(null);

  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const measure = () => setSize({ w: el.clientWidth, h: el.clientHeight });
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const storePoints = allStores.map((s) => ({ lat: s.latitude, lng: s.longitude }));
  // Include the shopper's point when it's near enough to share the frame with the stores.
  const nearest = origin ? Math.min(...storePoints.map((p) => milesBetween(origin, p))) : Infinity;
  const originInFrame = origin !== null && nearest <= 25;
  const frame =
    size && size.w > 0 && size.h > 0
      ? frameFor(originInFrame && origin ? [...storePoints, origin] : storePoints, size.w, size.h)
      : null;

  // Pin positions in pixels, nudged apart so nearby stores stay separately tappable.
  const truePoints =
    frame && size
      ? shown.map(({ store: s }) => {
          const { left, top } = toPct(frame, { lat: s.latitude, lng: s.longitude });
          return { x: (left / 100) * size.w, y: (top / 100) * size.h };
        })
      : [];
  const spread = spreadApart(truePoints, PIN_GAP_PX);
  const pins = shown.map((n, i) => ({
    ...n,
    x: spread[i]?.x ?? 0,
    y: spread[i]?.y ?? 0,
    trueX: truePoints[i]?.x ?? 0,
    trueY: truePoints[i]?.y ?? 0,
  }));

  // Grid every 5 miles, and a 5-mile scale bar.
  const gridStepDeg = 5 / MILES_PER_DEG_LAT;
  const pxPerDegY = frame && size ? size.h / frame.spanY : 0;
  const scalePx = gridStepDeg * pxPerDegY;

  return (
    <div
      ref={box}
      role="group"
      aria-label="Map of all Larkspur stores"
      className="relative h-full w-full overflow-hidden bg-[radial-gradient(circle_at_40%_45%,var(--color-brand-50),var(--color-sunken)_70%)]"
    >
      {frame && size ? (
        <>
          <svg aria-hidden="true" className="absolute inset-0 size-full" viewBox={`0 0 ${size.w} ${size.h}`}>
            {Array.from({ length: Math.ceil(size.w / scalePx) + 1 }, (_, i) => (
              <line
                key={`v${i}`}
                x1={i * scalePx}
                x2={i * scalePx}
                y1={0}
                y2={size.h}
                className="stroke-line"
                strokeWidth={1}
                strokeDasharray="2 6"
              />
            ))}
            {Array.from({ length: Math.ceil(size.h / scalePx) + 1 }, (_, i) => (
              <line
                key={`h${i}`}
                y1={i * scalePx}
                y2={i * scalePx}
                x1={0}
                x2={size.w}
                className="stroke-line"
                strokeWidth={1}
                strokeDasharray="2 6"
              />
            ))}
          </svg>

          {LANDMARKS.map((l) => {
            const { left, top } = toPct(frame, l);
            if (left < 2 || left > 90 || top < 4 || top > 94) return null;
            // Skip a landmark a pin would sit on (labels run ~90px to the right of their dot).
            const lx = (left / 100) * size.w;
            const ly = (top / 100) * size.h;
            if (pins.some((p) => p.x > lx - 22 && p.x < lx + 100 && p.y > ly - 8 && p.y < ly + 44)) return null;
            return (
              <span
                key={l.name}
                aria-hidden="true"
                className="pointer-events-none absolute flex -translate-y-1/2 items-center gap-1 text-[0.6875rem] font-medium text-muted"
                style={{ left: `${left}%`, top: `${top}%` }}
              >
                <span className="size-1.5 -translate-x-1/2 rounded-full bg-neutral-400" />
                {l.name}
              </span>
            );
          })}

          {originInFrame && origin ? (
            // Drawn above the pins but click-through, so the nearest store's pin stays usable.
            <span
              aria-hidden="true"
              className="pointer-events-none absolute z-30"
              style={{ left: `${toPct(frame, origin).left}%`, top: `${toPct(frame, origin).top}%` }}
            >
              <span className="absolute size-4 -translate-1/2 rounded-full border-3 border-white bg-info-600 shadow-md ring-6 ring-info-500/25" />
            </span>
          ) : null}

          {pins.map(({ store: s, number, miles, x, y, trueX, trueY }) => {
            const selected = s.code === selectedCode;
            const nudged = Math.hypot(x - trueX, y - trueY) > 3;
            return (
              <div key={s.code}>
                {nudged ? (
                  // Where the store really is, when its pin had to move aside for a neighbor.
                  <svg aria-hidden="true" className="pointer-events-none absolute inset-0 size-full">
                    <line x1={trueX} y1={trueY} x2={x} y2={y - 4} className="stroke-brand-500" strokeWidth={1.5} />
                    <circle cx={trueX} cy={trueY} r={3} className="fill-brand-600" />
                  </svg>
                ) : null}
                <button
                  type="button"
                  aria-pressed={selected}
                  aria-label={`${number}. ${s.name}${miles !== null ? `, ${formatMiles(miles)}` : ""}`}
                  title={s.name}
                  onClick={() => onSelect(s.code)}
                  className={cn(
                    "group/pin absolute grid size-8 -translate-x-1/2 -translate-y-full place-items-center text-xs font-semibold tabular-nums",
                    selected ? "z-20 text-white" : "z-10 text-brand-800",
                  )}
                  style={{ left: x, top: y - 4 }}
                >
                  {/* The teardrop: a square with one sharp corner, turned so the corner points down. */}
                  <span
                    aria-hidden="true"
                    className={cn(
                      "absolute inset-0 rotate-45 rounded-full rounded-br-none shadow-md transition-[scale,background-color] duration-200 ease-snappy",
                      selected
                        ? "scale-115 bg-brand-600 ring-3 ring-white"
                        : "bg-raised ring-2 ring-brand-500 group-hover/pin:scale-110 group-hover/pin:bg-brand-50",
                    )}
                  />
                  <span className="relative">{number}</span>
                </button>
              </div>
            );
          })}

          <div aria-hidden="true" className="absolute bottom-3 left-3 flex flex-col gap-1 text-[0.6875rem] text-muted">
            <span className="h-1.5 border-x-2 border-b-2 border-neutral-500" style={{ width: scalePx }} />
            <span>5 mi</span>
          </div>
        </>
      ) : null}
      <p className="absolute right-3 top-3 max-w-[60%] rounded-full bg-raised/90 px-2.5 py-1 text-right text-[0.6875rem] text-muted shadow-xs">
        Overview, to scale · not a street map
      </p>
      {origin && originInFrame ? (
        <p className="absolute bottom-3 left-24 flex items-center gap-1.5 rounded-full bg-raised/95 px-2.5 py-1 text-[0.6875rem] font-medium text-ink shadow-xs">
          <span aria-hidden="true" className="size-2.5 rounded-full bg-info-600 ring-3 ring-info-500/25" />
          {origin.source === "device" ? "Your location" : origin.label}
        </p>
      ) : null}
      {origin && !originInFrame ? (
        <p className="absolute inset-x-3 bottom-10 rounded-xl bg-raised/95 px-3 py-2 text-center text-xs text-ink shadow-sm sm:inset-x-auto sm:right-3">
          {origin.source === "device" ? "You're" : `${origin.label} is`} about {Math.round(nearest)} mi from the nearest
          store, outside this map.
        </p>
      ) : null}
    </div>
  );
}

// --- Keyless embed: one store at a time -------------------------------------------------

export function EmbeddedMap({ store }: { store: StoreOut }) {
  return (
    <iframe
      key={store.code}
      title={`Street map showing ${store.name}, ${store.address_line1}, ${store.city}`}
      src={embedUrl(store)}
      loading="lazy"
      referrerPolicy="no-referrer-when-downgrade"
      className="h-full min-h-80 w-full border-0"
    />
  );
}

// --- Google Maps JavaScript API (only when a key is configured) --------------------------

type MarkerLabel = { text: string; color?: string; fontWeight?: string };
type GoogleMarker = {
  addListener(event: string, fn: () => void): void;
  setLabel(label: MarkerLabel): void;
  setZIndex(z: number): void;
  setVisible(visible: boolean): void;
};
type GoogleMaps = {
  Map: new (el: HTMLElement, opts: { center: LatLng; zoom: number; mapId?: string }) => {
    panTo(p: LatLng): void;
    setZoom(z: number): void;
  };
  Marker: new (opts: { position: LatLng; map: unknown; title: string; label?: MarkerLabel }) => GoogleMarker;
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

/** Every store as a numbered marker; the selected one is drawn on top in white-on-violet. */
export function InteractiveMap({
  stores,
  shown,
  mapsKey,
  selected,
  onSelect,
}: {
  stores: StoreOut[];
  shown: NumberedStore[];
  mapsKey: string;
  selected: StoreOut;
  onSelect: (code: string) => void;
}) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<InstanceType<GoogleMaps["Map"]> | null>(null);
  const markers = useRef(new Map<string, GoogleMarker>());
  const [failed, setFailed] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    loadGoogleMaps(mapsKey)
      .then((maps) => {
        if (cancelled || !el.current) return;
        map.current = new maps.Map(el.current, { center: { lat: 32.93, lng: -96.82 }, zoom: 9 });
        for (const s of stores) {
          const marker = new maps.Marker({ position: { lat: s.latitude, lng: s.longitude }, map: map.current, title: s.name });
          marker.addListener("click", () => onSelect(s.code));
          markers.current.set(s.code, marker);
        }
        setReady(true);
      })
      .catch(() => setFailed(true));
    return () => {
      cancelled = true;
    };
    // The markers are drawn once; numbering and selection update them below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapsKey, stores]);

  useEffect(() => {
    if (!ready) return;
    const numbers = new Map(shown.map((n) => [n.store.code, n.number]));
    for (const [code, marker] of markers.current) {
      const number = numbers.get(code);
      marker.setVisible(number !== undefined);
      if (number === undefined) continue;
      const isSelected = code === selected.code;
      marker.setLabel({ text: String(number), color: isSelected ? "#ffffff" : "#3b0764", fontWeight: "600" });
      marker.setZIndex(isSelected ? 1000 : 100 - number);
    }
  }, [ready, shown, selected]);

  useEffect(() => {
    map.current?.panTo({ lat: selected.latitude, lng: selected.longitude });
    map.current?.setZoom(12);
  }, [selected]);

  if (failed) return <EmbeddedMap store={selected} />;
  return <div ref={el} role="region" aria-label="Map of all Larkspur stores" className="h-full min-h-80 w-full" />;
}
