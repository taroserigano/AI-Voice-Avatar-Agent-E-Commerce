import { ArrowRightIcon, GridIcon, SearchIcon } from "@/components/icons";
import { ButtonLink } from "@/components/ui/button";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Department not found" };

/** An unknown /c/<slug> (caught here from c/[slug]/layout.tsx, which answers a real 404). */
export default function DepartmentNotFound() {
  return (
    <div className="flex flex-col items-center rounded-3xl bg-mesh-light px-6 py-16 text-center sm:py-20">
      <span className="grid size-16 place-items-center rounded-2xl bg-raised text-brand-600 shadow-md">
        <GridIcon className="size-8" />
      </span>
      <h1 className="mt-6 font-display text-2xl font-semibold text-ink sm:text-3xl">We couldn&apos;t find that department</h1>
      <p className="mt-2 max-w-md text-muted">The link may be old or mistyped. Pick a department from the list, or search.</p>
      <div className="mt-7 flex flex-wrap justify-center gap-3">
        <ButtonLink href="/sitemap#departments" size="lg">
          All departments
          <ArrowRightIcon className="size-4.5" />
        </ButtonLink>
        <ButtonLink href="/search" variant="outline" size="lg">
          <SearchIcon className="size-4.5" />
          Search the store
        </ButtonLink>
      </div>
    </div>
  );
}
