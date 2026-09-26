import { Badge } from "@/components/ui/badge";
import { orderStatusMeta } from "@/lib/orders";
import type { OrderSummary, ShipmentOut } from "@ai-commerce/contracts";

/** Order status in words (with a dot), optionally refined by where the parcel is. */
export function OrderStatusBadge({
  status,
  shipment,
  size = "md",
  className,
}: {
  status: OrderSummary["status"];
  shipment?: ShipmentOut | null;
  size?: "sm" | "md";
  className?: string;
}) {
  const meta = orderStatusMeta(status, shipment);
  return (
    <Badge tone={meta.tone} dot size={size} className={className}>
      <span className="sr-only">Status: </span>
      {meta.label}
    </Badge>
  );
}
