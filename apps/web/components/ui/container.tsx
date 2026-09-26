import { cn } from "@/lib/cn";
import type { ReactNode } from "react";

type ContainerSize = "narrow" | "default" | "wide";

const widths: Record<ContainerSize, string> = {
  narrow: "max-w-3xl", // 768px: forms, legal, reading
  default: "max-w-7xl", // 1280px: shop pages
  wide: "max-w-[90rem]", // 1440px: full-bleed marketing bands
};

export function containerClasses(size: ContainerSize = "default", className?: string) {
  return cn("mx-auto w-full px-4 sm:px-6 lg:px-8", widths[size], className);
}

/** Centered page column with the standard side gutters (16 / 24 / 32px). */
export function Container({
  size = "default",
  as: Element = "div",
  className,
  children,
}: {
  size?: ContainerSize;
  as?: "div" | "section" | "header" | "footer" | "main" | "nav";
  className?: string;
  children: ReactNode;
}) {
  return <Element className={containerClasses(size, className)}>{children}</Element>;
}
