import { serverApi, unwrap } from "@/lib/api-server";
import { openingText } from "@/lib/store-hours";
import type { Metadata } from "next";
import { StoreLocator } from "./store-locator";

export const metadata: Metadata = { title: "Stores" };

export default async function StoresPage() {
  const api = await serverApi();
  const stores = await api.GET("/v1/stores").then(unwrap);
  // A Maps JavaScript API key is public by design (it's restricted by referrer in the
  // Google Cloud console), so passing it to the browser is expected. Without one, the page
  // uses Google's keyless embed, one store at a time.
  const mapsKey = process.env.GOOGLE_MAPS_API_KEY || null;
  // Worded on the server, at the same moment the API decided open_now, so it can't drift on hydration.
  const now = new Date();
  const status = Object.fromEntries(stores.map((s) => [s.code, openingText(s, s.open_now, now)]));

  return (
    <div className="pb-24 sm:pb-8 sm:pt-2">
      <h1 className="font-display text-3xl font-semibold text-ink sm:text-4xl">Stores near Dallas</h1>
      <p className="mt-2 max-w-2xl text-muted">
        {stores.length} Larkspur stores around Dallas-Fort Worth. Drop off a packaged return at any of them.{" "}
        <span className="text-sm">These are demo locations; the addresses and phone numbers are made up.</span>
      </p>
      <StoreLocator stores={stores} mapsKey={mapsKey} status={status} />
    </div>
  );
}
