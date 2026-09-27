import { ArrowLeftIcon, PackageIcon } from "@/components/icons";
import { ButtonLink } from "@/components/ui/button";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Order not found" };

export default function OrderNotFound() {
  return (
    <div className="flex flex-col items-center rounded-3xl bg-mesh-light px-6 py-16 text-center sm:py-20">
      <span className="grid size-16 place-items-center rounded-2xl bg-raised text-brand-600 shadow-md">
        <PackageIcon className="size-8" />
      </span>
      <h1 className="mt-6 font-display text-2xl font-semibold text-ink sm:text-3xl">We couldn&apos;t find that order</h1>
      <p className="mt-2 max-w-sm text-muted">
        Check the link, or pick the order from your list. You can only see orders placed with this account.
      </p>
      <ButtonLink href="/orders" size="lg" className="mt-7">
        <ArrowLeftIcon className="size-4.5" />
        Back to your orders
      </ButtonLink>
    </div>
  );
}
