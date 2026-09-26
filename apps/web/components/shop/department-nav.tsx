"use client";

import { DepartmentIcon } from "@/components/icons";
import { containerClasses } from "@/components/ui/container";
import Link from "next/link";
import { usePathname } from "next/navigation";

const pill =
  "inline-flex min-h-10 items-center gap-2 whitespace-nowrap rounded-full px-3 text-sm font-medium text-ink-soft transition-colors duration-150 hover:bg-sunken hover:text-ink lg:text-[0.8125rem] " +
  "aria-[current=page]:bg-brand-50 aria-[current=page]:text-brand-800 aria-[current=page]:ring-1 aria-[current=page]:ring-inset aria-[current=page]:ring-brand-100 " +
  "[&_svg]:size-4 [&_svg]:text-muted [&_svg]:transition-colors hover:[&_svg]:text-brand-600 aria-[current=page]:[&_svg]:text-brand-600";

/**
 * Department rail under the header: centered when it fits, otherwise it scrolls sideways (with
 * a soft fade hinting at more). Marks the current department with aria-current.
 */
export function DepartmentNav({ categories }: { categories: { slug: string; name: string }[] }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Departments" className="border-t border-line/70">
      <div
        className={containerClasses(
          "wide",
          "overflow-x-auto scrollbar-none max-[1440px]:[mask-image:linear-gradient(to_right,black_calc(100%-3rem),transparent)]",
        )}
      >
        <ul className="mx-auto flex w-max items-center gap-1 py-1.5 max-[1440px]:pr-10">
          {categories.map((c) => {
            const href = `/c/${c.slug}`;
            return (
              <li key={c.slug}>
                <Link href={href} aria-current={pathname === href ? "page" : undefined} className={pill}>
                  <DepartmentIcon slug={c.slug} />
                  {c.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
