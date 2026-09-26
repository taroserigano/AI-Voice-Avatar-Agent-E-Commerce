import { serverApi, unwrap } from "@/lib/api-server";
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
  return (
    <div>
      <h1 className="text-2xl font-bold">Stores near Dallas</h1>
      <p className="mt-1 text-muted">
        {stores.length} Serigan Mart stores around Dallas-Fort Worth. Drop off a packaged return at any of them.
      </p>
      <p className="mt-1 text-sm text-muted">Demo locations for this sandbox store; the addresses and phone numbers are made up.</p>
      <StoreLocator stores={stores} mapsKey={mapsKey} />
    </div>
  );
}
