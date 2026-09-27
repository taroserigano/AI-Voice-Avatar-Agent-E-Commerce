import { ArrowLeftIcon, MapIcon } from "@/components/icons";
import { ButtonLink } from "@/components/ui/button";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Store not found" };

export default function StoreNotFound() {
  return (
    <div className="flex flex-col items-center rounded-3xl bg-mesh-light px-6 py-16 text-center sm:py-20">
      <span className="grid size-16 place-items-center rounded-2xl bg-raised text-brand-600 shadow-md">
        <MapIcon className="size-8" />
      </span>
      <h1 className="mt-6 font-display text-2xl font-semibold text-ink sm:text-3xl">We couldn&apos;t find that store</h1>
      <p className="mt-2 max-w-sm text-muted">It may have moved or the link is mistyped. All ten stores are on the map.</p>
      <ButtonLink href="/stores" size="lg" className="mt-7">
        <ArrowLeftIcon className="size-4.5" />
        All stores
      </ButtonLink>
    </div>
  );
}
