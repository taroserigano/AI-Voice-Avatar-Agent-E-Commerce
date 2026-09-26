import { cn } from "@/lib/cn";
import type { HTMLAttributes } from "react";

type CardPadding = "none" | "sm" | "md" | "lg";
type CardElement = "div" | "section" | "article" | "aside" | "li";

const paddings: Record<CardPadding, string> = {
  none: "",
  sm: "p-4",
  md: "p-5 sm:p-6",
  lg: "p-6 sm:p-8",
};

export function cardClasses({
  padding = "md",
  interactive = false,
  className,
}: { padding?: CardPadding; interactive?: boolean; className?: string } = {}) {
  return cn(
    "rounded-2xl border border-line bg-raised shadow-xs",
    paddings[padding],
    interactive &&
      "transition-[box-shadow,transform,border-color] duration-300 ease-smooth hover:-translate-y-0.5 hover:border-line-strong hover:shadow-lg motion-reduce:hover:translate-y-0",
    className,
  );
}

/**
 * White raised surface. `interactive` adds hover lift (use when the whole card is a link target).
 * `as` picks the element (default div) so lists can render `as="li"`.
 */
export function Card({
  as: Element = "div",
  padding = "md",
  interactive = false,
  className,
  ...props
}: HTMLAttributes<HTMLElement> & { as?: CardElement; padding?: CardPadding; interactive?: boolean }) {
  return <Element className={cardClasses({ padding, interactive, className })} {...props} />;
}
