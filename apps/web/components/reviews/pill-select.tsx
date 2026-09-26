import { Select } from "@/components/ui/field";
import { cn } from "@/lib/cn";
import type { ComponentProps } from "react";

/** Rounded native <select>; the chevron comes from the shared `Select` styling. */
export function PillSelect({ className, wrapperClassName, ...props }: ComponentProps<"select"> & { wrapperClassName?: string }) {
  return (
    <div className={wrapperClassName}>
      <Select className={cn("rounded-full pl-4 pr-10 font-medium", className)} {...props} />
    </div>
  );
}
