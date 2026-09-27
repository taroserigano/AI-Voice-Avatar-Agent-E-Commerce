/**
 * Store distances without a geocoding service: a small built-in table of Dallas-Fort Worth ZIP
 * codes and place names with approximate center points, and straight-line (great-circle) miles.
 * Nothing leaves the browser; a place that isn't in the table just isn't found.
 */

export type LatLng = { lat: number; lng: number };
export type Place = LatLng & { label: string };

const EARTH_RADIUS_MI = 3958.8;

/** Great-circle distance in miles (haversine). */
export function milesBetween(a: LatLng, b: LatLng): number {
  const rad = (d: number) => (d * Math.PI) / 180;
  const dLat = rad(b.lat - a.lat);
  const dLng = rad(b.lng - a.lng);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_RADIUS_MI * Math.asin(Math.min(1, Math.sqrt(h)));
}

/** "3.2 mi" (one decimal, as store locators usually show it). */
export function formatMiles(miles: number): string {
  return `${(Math.round(miles * 10) / 10).toFixed(1)} mi`;
}

export function byDistance<T extends LatLng>(items: T[], from: LatLng): { item: T; miles: number }[] {
  return items.map((item) => ({ item, miles: milesBetween(from, item) })).sort((a, b) => a.miles - b.miles);
}

// Approximate centers. [lat, lng, city]
// prettier-ignore
const ZIPS: Record<string, [number, number, string]> = {
  // Dallas
  "75201": [32.7876, -96.7994, "Dallas"], "75202": [32.7806, -96.804, "Dallas"], "75203": [32.7456, -96.8069, "Dallas"],
  "75204": [32.803, -96.7852, "Dallas"], "75205": [32.836, -96.796, "Dallas"], "75206": [32.831, -96.77, "Dallas"],
  "75207": [32.787, -96.823, "Dallas"], "75208": [32.75, -96.839, "Dallas"], "75209": [32.845, -96.826, "Dallas"],
  "75210": [32.77, -96.745, "Dallas"], "75211": [32.732, -96.905, "Dallas"], "75212": [32.783, -96.871, "Dallas"],
  "75214": [32.824, -96.749, "Dallas"], "75215": [32.758, -96.762, "Dallas"], "75216": [32.709, -96.795, "Dallas"],
  "75217": [32.724, -96.675, "Dallas"], "75218": [32.846, -96.697, "Dallas"], "75219": [32.813, -96.814, "Dallas"],
  "75220": [32.868, -96.862, "Dallas"], "75223": [32.794, -96.748, "Dallas"], "75224": [32.711, -96.838, "Dallas"],
  "75225": [32.863, -96.791, "Dallas"], "75226": [32.788, -96.767, "Dallas"], "75227": [32.767, -96.683, "Dallas"],
  "75228": [32.825, -96.678, "Dallas"], "75229": [32.893, -96.864, "Dallas"], "75230": [32.899, -96.79, "Dallas"],
  "75231": [32.876, -96.749, "Dallas"], "75232": [32.664, -96.838, "Dallas"], "75233": [32.704, -96.873, "Dallas"],
  "75234": [32.924, -96.893, "Farmers Branch"], "75235": [32.825, -96.839, "Dallas"], "75236": [32.69, -96.918, "Dallas"],
  "75237": [32.659, -96.876, "Dallas"], "75238": [32.877, -96.708, "Dallas"], "75240": [32.937, -96.787, "Dallas"],
  "75241": [32.672, -96.777, "Dallas"], "75243": [32.91, -96.728, "Dallas"], "75244": [32.932, -96.835, "Dallas"],
  "75246": [32.794, -96.77, "Dallas"], "75247": [32.815, -96.877, "Dallas"], "75248": [32.968, -96.794, "Dallas"],
  "75249": [32.646, -96.969, "Dallas"], "75251": [32.918, -96.775, "Dallas"], "75252": [32.997, -96.792, "Dallas"],
  "75254": [32.95, -96.82, "Dallas"],
  // Collin County
  "75002": [33.089, -96.625, "Allen"], "75013": [33.117, -96.679, "Allen"],
  "75023": [33.055, -96.736, "Plano"], "75024": [33.075, -96.804, "Plano"], "75025": [33.079, -96.729, "Plano"],
  "75074": [33.027, -96.678, "Plano"], "75075": [33.024, -96.739, "Plano"], "75093": [33.035, -96.804, "Plano"],
  "75094": [33.015, -96.612, "Murphy"],
  "75033": [33.185, -96.843, "Frisco"], "75034": [33.128, -96.854, "Frisco"], "75035": [33.152, -96.778, "Frisco"],
  "75036": [33.136, -96.912, "Frisco"],
  "75069": [33.198, -96.615, "McKinney"], "75070": [33.172, -96.694, "McKinney"], "75071": [33.245, -96.63, "McKinney"],
  "75072": [33.184, -96.722, "McKinney"],
  "75078": [33.239, -96.797, "Prosper"], "75098": [33.011, -96.523, "Wylie"],
  // Northeast and east
  "75080": [32.968, -96.74, "Richardson"], "75081": [32.949, -96.709, "Richardson"], "75082": [32.99, -96.669, "Richardson"],
  "75040": [32.923, -96.625, "Garland"], "75041": [32.88, -96.64, "Garland"], "75042": [32.917, -96.677, "Garland"],
  "75043": [32.858, -96.58, "Garland"], "75044": [32.962, -96.653, "Garland"],
  "75048": [32.97, -96.58, "Sachse"], "75088": [32.899, -96.548, "Rowlett"], "75089": [32.933, -96.56, "Rowlett"],
  "75087": [32.913, -96.448, "Rockwall"], "75032": [32.86, -96.42, "Rockwall"],
  "75149": [32.768, -96.608, "Mesquite"], "75150": [32.815, -96.631, "Mesquite"],
  // North and northwest
  "75001": [32.96, -96.838, "Addison"],
  "75006": [32.962, -96.897, "Carrollton"], "75007": [33.005, -96.897, "Carrollton"], "75010": [33.031, -96.877, "Carrollton"],
  "75019": [32.967, -96.986, "Coppell"], "75056": [33.092, -96.885, "The Colony"], "75068": [33.174, -96.951, "Little Elm"],
  "75057": [33.053, -96.999, "Lewisville"], "75067": [33.017, -96.996, "Lewisville"], "75077": [33.077, -97.059, "Lewisville"],
  "75022": [33.027, -97.121, "Flower Mound"], "75028": [33.037, -97.068, "Flower Mound"],
  "76201": [33.217, -97.144, "Denton"], "76205": [33.19, -97.128, "Denton"], "76209": [33.232, -97.11, "Denton"],
  // Irving and Grand Prairie
  "75038": [32.865, -96.99, "Irving"], "75039": [32.887, -96.94, "Irving"], "75060": [32.8, -96.958, "Irving"],
  "75061": [32.826, -96.963, "Irving"], "75062": [32.848, -96.965, "Irving"], "75063": [32.918, -96.976, "Irving"],
  "75050": [32.771, -97.012, "Grand Prairie"], "75051": [32.724, -97.007, "Grand Prairie"],
  "75052": [32.663, -97.024, "Grand Prairie"],
  // South Dallas County
  "75104": [32.587, -96.955, "Cedar Hill"], "75115": [32.601, -96.864, "DeSoto"], "75116": [32.651, -96.911, "Duncanville"],
  "75137": [32.634, -96.912, "Duncanville"], "75134": [32.618, -96.772, "Lancaster"], "75146": [32.579, -96.755, "Lancaster"],
  // Mid-Cities
  "76039": [32.859, -97.081, "Euless"], "76040": [32.817, -97.099, "Euless"], "76051": [32.933, -97.093, "Grapevine"],
  "76092": [32.958, -97.15, "Southlake"], "76021": [32.853, -97.135, "Bedford"], "76022": [32.83, -97.145, "Bedford"],
  "76053": [32.817, -97.179, "Hurst"], "76054": [32.858, -97.177, "Hurst"], "76180": [32.841, -97.219, "North Richland Hills"],
  "76182": [32.882, -97.209, "North Richland Hills"], "76117": [32.804, -97.266, "Haltom City"],
  "76248": [32.928, -97.248, "Keller"],
  // Arlington
  "76010": [32.72, -97.082, "Arlington"], "76011": [32.758, -97.1, "Arlington"], "76012": [32.754, -97.135, "Arlington"],
  "76013": [32.72, -97.145, "Arlington"], "76014": [32.695, -97.088, "Arlington"], "76015": [32.693, -97.134, "Arlington"],
  "76016": [32.689, -97.19, "Arlington"], "76017": [32.663, -97.163, "Arlington"], "76018": [32.654, -97.093, "Arlington"],
  "76063": [32.571, -97.138, "Mansfield"],
  // Fort Worth
  "76102": [32.753, -97.329, "Fort Worth"], "76104": [32.726, -97.318, "Fort Worth"], "76107": [32.739, -97.385, "Fort Worth"],
  "76109": [32.702, -97.379, "Fort Worth"], "76110": [32.706, -97.338, "Fort Worth"], "76116": [32.725, -97.446, "Fort Worth"],
  "76132": [32.671, -97.406, "Fort Worth"], "76137": [32.866, -97.289, "Fort Worth"], "76177": [32.947, -97.32, "Fort Worth"],
  "76244": [32.931, -97.283, "Fort Worth"], "76028": [32.527, -97.312, "Burleson"],
};

// Cities and a few well-known Dallas neighborhoods. [lat, lng]
// prettier-ignore
const PLACES: Record<string, [number, number]> = {
  Dallas: [32.7767, -96.797], "Fort Worth": [32.7555, -97.3308], Plano: [33.0198, -96.6989], Frisco: [33.1507, -96.8236],
  McKinney: [33.1972, -96.6398], Richardson: [32.9483, -96.7299], Garland: [32.9126, -96.6389], Irving: [32.814, -96.9489],
  Arlington: [32.7357, -97.1081], Allen: [33.1032, -96.6706], Carrollton: [32.9756, -96.89], Addison: [32.9618, -96.8292],
  Mesquite: [32.7668, -96.5992], "Grand Prairie": [32.746, -96.9978], Denton: [33.2148, -97.1331],
  Lewisville: [33.0462, -96.9942], "Flower Mound": [33.0146, -97.097], Coppell: [32.9546, -97.015],
  Grapevine: [32.9343, -97.0781], Southlake: [32.9412, -97.1342], Rowlett: [32.9029, -96.5639], Rockwall: [32.9312, -96.4597],
  Wylie: [33.0151, -96.5389], Prosper: [33.2362, -96.8011], "Little Elm": [33.1626, -96.9375], "The Colony": [33.089, -96.8864],
  "Farmers Branch": [32.9265, -96.8961], "University Park": [32.8501, -96.8], "Highland Park": [32.8335, -96.792],
  Duncanville: [32.6518, -96.9083], DeSoto: [32.5899, -96.857], "Cedar Hill": [32.5885, -96.9561], Lancaster: [32.5921, -96.7561],
  Euless: [32.8371, -97.082], Bedford: [32.844, -97.1431], Hurst: [32.8235, -97.1706], Keller: [32.9346, -97.2517],
  Mansfield: [32.5632, -97.1417], Murphy: [33.0151, -96.613], Sachse: [32.9762, -96.5953], "Balch Springs": [32.7287, -96.6228],
  "North Richland Hills": [32.8343, -97.2289], "Haltom City": [32.7996, -97.2692], Burleson: [32.5421, -97.3208],
  Uptown: [32.799, -96.801], "Deep Ellum": [32.7843, -96.7836], Lakewood: [32.819, -96.751], "Bishop Arts": [32.7487, -96.8288],
  "Oak Cliff": [32.73, -96.84], "Downtown Dallas": [32.7801, -96.8005], "Las Colinas": [32.885, -96.942],
  "Lake Highlands": [32.883, -96.714], "Preston Hollow": [32.887, -96.804], Legacy: [33.0768, -96.8236],
};

// Keys are in the normalized form `key()` produces (lowercase, no punctuation or state).
const ALIASES: Record<string, string> = {
  "ft worth": "Fort Worth",
  fw: "Fort Worth",
  dfw: "Dallas",
  downtown: "Downtown Dallas",
  "n richland hills": "North Richland Hills",
  nrh: "North Richland Hills",
};

const key = (s: string) =>
  s
    .toLowerCase()
    .replace(/[.,]/g, " ")
    .replace(/\b(tx|texas|usa|us)\b/g, " ")
    .replace(/\s+/g, " ")
    .trim();

const PLACE_KEYS = new Map(Object.keys(PLACES).map((name) => [key(name), name]));

export type PlaceLookup = { ok: true; place: Place } | { ok: false; reason: "empty" | "unknown_zip" | "unknown_place" };

/** A ZIP code ("75204", "75204-1234") or a DFW city or neighborhood ("Plano", "ft worth, tx"). */
export function findPlace(query: string): PlaceLookup {
  const q = query.trim();
  if (!q) return { ok: false, reason: "empty" };
  const zip = /^(\d{5})(?:-\d{4})?$/.exec(q)?.[1];
  if (zip) {
    const hit = ZIPS[zip];
    return hit ? { ok: true, place: { lat: hit[0], lng: hit[1], label: `${zip} (${hit[2]})` } } : { ok: false, reason: "unknown_zip" };
  }
  const k = key(q);
  const name = PLACE_KEYS.get(k) ?? ALIASES[k];
  if (name && PLACES[name]) {
    const [lat, lng] = PLACES[name];
    return { ok: true, place: { lat, lng, label: name } };
  }
  // A unique prefix is enough ("rich" -> Richardson), so typos at the end still land.
  if (k.length >= 3) {
    const matches = [...PLACE_KEYS.entries()].filter(([pk]) => pk.startsWith(k));
    if (matches.length === 1 && matches[0]) {
      const name2 = matches[0][1];
      const [lat, lng] = PLACES[name2] as [number, number];
      return { ok: true, place: { lat, lng, label: name2 } };
    }
  }
  return { ok: false, reason: "unknown_place" };
}

/** A few examples for the search hint and "not found" message. */
export const PLACE_EXAMPLES = ["75204", "Plano", "Fort Worth", "Arlington"] as const;

type Point = { x: number; y: number };

/**
 * Nudge points (in pixels) apart until no two are closer than `gap`, so pins for stores a few
 * miles apart don't overlap on a small screen. Moves are small and symmetric; order is kept.
 */
export function spreadApart(points: Point[], gap: number, rounds = 40): Point[] {
  const out = points.map((p) => ({ ...p }));
  for (let r = 0; r < rounds; r += 1) {
    let moved = false;
    for (let i = 0; i < out.length; i += 1) {
      for (let j = i + 1; j < out.length; j += 1) {
        const a = out[i] as Point;
        const b = out[j] as Point;
        let dx = b.x - a.x;
        let dy = b.y - a.y;
        let d = Math.hypot(dx, dy);
        if (d >= gap) continue;
        if (d < 0.01) {
          // Same spot: split sideways.
          [dx, dy, d] = [1, 0, 1];
        }
        const push = (gap - d) / 2 + 0.01;
        a.x -= (dx / d) * push;
        a.y -= (dy / d) * push;
        b.x += (dx / d) * push;
        b.y += (dy / d) * push;
        moved = true;
      }
    }
    if (!moved) break;
  }
  return out;
}
