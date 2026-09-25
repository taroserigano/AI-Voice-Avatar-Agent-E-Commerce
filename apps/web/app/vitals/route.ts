import { metrics } from "@opentelemetry/api";
import { NextResponse } from "next/server";

const meter = metrics.getMeter("web");
const lcp = meter.createHistogram("web.vitals.lcp", { unit: "ms", description: "Largest Contentful Paint" });
const inp = meter.createHistogram("web.vitals.inp", { unit: "ms", description: "Interaction to Next Paint" });

// Only known route templates become metric labels, never raw URLs (no IDs or queries).
const ROUTES = new Set(["home", "category", "search", "product", "cart", "orders"]);

export async function POST(request: Request) {
  let body: { name?: unknown; value?: unknown; route?: unknown };
  try {
    body = JSON.parse(await request.text());
  } catch {
    return new NextResponse(null, { status: 400 });
  }
  const value = typeof body.value === "number" && Number.isFinite(body.value) ? body.value : null;
  const route = typeof body.route === "string" && ROUTES.has(body.route) ? body.route : "other";
  if (value === null || value < 0 || value > 120_000) return new NextResponse(null, { status: 400 });
  if (body.name === "LCP") lcp.record(value, { route });
  else if (body.name === "INP") inp.record(value, { route });
  else return new NextResponse(null, { status: 400 });
  return new NextResponse(null, { status: 204 });
}
