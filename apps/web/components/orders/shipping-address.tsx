import { HomeIcon } from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import type { ShippingAddressOut } from "@ai-commerce/contracts";

/** The address lines as printed on a label: name, street, unit, "City, ST 75023". */
export function AddressLines({ address }: { address: ShippingAddressOut }) {
  return (
    <address className="not-italic leading-relaxed">
      <span className="font-semibold text-ink">{address.name}</span>
      <br />
      {address.line1}
      {address.line2 ? (
        <>
          <br />
          {address.line2}
        </>
      ) : null}
      <br />
      {address.city}, {address.state} {address.postal_code}
      {address.country !== "US" ? (
        <>
          <br />
          {address.country}
        </>
      ) : null}
    </address>
  );
}

/** Where the order went. Seeded demo addresses say so. */
export function ShippingAddressCard({ address }: { address: ShippingAddressOut | null }) {
  return (
    <section aria-labelledby="ship-to-heading" className="rounded-3xl border border-line bg-raised p-5 shadow-xs sm:p-6">
      <div className="flex items-start justify-between gap-3">
        <h2 id="ship-to-heading" className="flex items-center gap-2 font-display text-lg font-semibold text-ink">
          <HomeIcon className="size-5 text-brand-600" />
          Shipping address
        </h2>
        {address?.is_sample ? <Badge tone="neutral">Sample address</Badge> : null}
      </div>
      {address ? (
        <div className="mt-3 text-sm text-ink-soft">
          <AddressLines address={address} />
        </div>
      ) : (
        <p className="mt-3 text-sm text-muted">No delivery address is on file for this order.</p>
      )}
    </section>
  );
}
