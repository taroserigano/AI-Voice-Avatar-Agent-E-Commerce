import { Badge } from "@/components/ui/badge";
import { orderStatusMeta } from "@/lib/orders";
import type { OrderSummary } from "@ai-commerce/contracts";

/** Order status in words (with a dot): one vocabulary for the list, the detail page, and the tabs. */
export function OrderStatusBadge({
  status,
  size = "md",
  className,
}: {
  status: OrderSummary["status"];
  size?: "sm" | "md";
  className?: string;
}) {
  const meta = orderStatusMeta(status);
  return (
    <Badge tone={meta.tone} dot size={size} className={className}>
      <span className="sr-only">Status: </span>
      {meta.label}
    </Badge>
  );
}
