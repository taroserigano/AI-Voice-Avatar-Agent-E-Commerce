import { DepartmentIcon, PackageIcon, SearchIcon } from "@/components/icons";
import { departmentTint } from "@/components/shop/department-style";
import { buttonClasses } from "@/components/ui/button";
import { inputClasses } from "@/components/ui/field";
import { serverApi } from "@/lib/api-server";
import { cn } from "@/lib/cn";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Item not found" };

/** Departments for the chips; the page still works if the list can't be loaded. */
async function loadDepartments() {
  try {
    const api = await serverApi();
    return (await api.GET("/v1/categories")).data ?? [];
  } catch {
    return [];
  }
}

export default async function ProductNotFound() {
  const departments = await loadDepartments();
  return (
    <div className="flex flex-col items-center rounded-3xl bg-mesh-light px-6 py-16 text-center sm:py-20">
      <span className="grid size-16 place-items-center rounded-2xl bg-raised text-brand-600 shadow-md">
        <PackageIcon className="size-8" />
      </span>
      <h1 className="mt-6 font-display text-2xl font-semibold text-ink sm:text-3xl">This item isn&apos;t available</h1>
      <p className="mt-2 max-w-md text-muted">
        The link may be old, or the item is no longer in the catalog. Search for something similar, or browse a
        department.
      </p>

      <form action="/search" method="get" role="search" aria-label="Search products" className="mt-7 flex w-full max-w-md gap-2">
        <div className="relative min-w-0 flex-1">
          <label htmlFor="nf-search" className="sr-only">
            Search products
          </label>
          <SearchIcon className="pointer-events-none absolute left-4 top-1/2 size-4.5 -translate-y-1/2 text-muted" />
          <input
            id="nf-search"
            type="search"
            name="q"
            required
            autoComplete="off"
            placeholder="Search everything"
            className={cn(inputClasses, "min-h-12 rounded-full pl-11")}
          />
        </div>
        <button type="submit" className={buttonClasses("primary", "lg", "min-h-12 px-6")}>
          Search
        </button>
      </form>

      {departments.length > 0 ? (
        <nav aria-labelledby="nf-departments" className="mt-10 w-full max-w-3xl">
          <h2 id="nf-departments" className="text-xs font-semibold uppercase tracking-eyebrow text-muted">
            Browse a department
          </h2>
          <ul className="mt-3 flex flex-wrap justify-center gap-2">
            {departments.map((d) => (
              <li key={d.slug}>
                <Link
                  href={`/c/${d.slug}`}
                  className="inline-flex min-h-10 items-center gap-2 rounded-full bg-raised py-1 pl-1.5 pr-4 text-sm font-medium text-ink shadow-xs ring-1 ring-inset ring-line-strong transition-colors hover:bg-brand-50 hover:text-brand-800 hover:ring-brand-200"
                >
                  <span className={cn("grid size-7 place-items-center rounded-full", departmentTint(d.slug).tile)}>
                    <DepartmentIcon slug={d.slug} className="size-4" />
                  </span>
                  {d.name}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      ) : null}
    </div>
  );
}
