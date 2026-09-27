import { cn } from "@/lib/cn";

const STYLES = {
  steph: "bg-linear-to-br from-brand-500 to-brand-700 text-white",
  xana: "bg-linear-to-br from-accent-300 to-accent-500 text-ink",
} as const;

/** Steph's mark: a larkspur flower spike. */
function StephMark() {
  return (
    <svg viewBox="0 0 24 24" className="size-[58%]" fill="currentColor" aria-hidden="true">
      <path d="M11.25 21.5V11h1.5v10.5z" />
      <circle cx="12" cy="4.2" r="2.1" />
      <circle cx="9.2" cy="7.4" r="2" />
      <circle cx="14.8" cy="7.4" r="2" />
      <circle cx="12" cy="9.6" r="2" opacity=".85" />
      <path d="M12.6 16.2c2.2-.2 3.9-1.4 4.6-3.3-2.3 0-4 1.2-4.6 3.3M11.4 18.2c-2.2-.2-3.9-1.4-4.6-3.3 2.3 0 4 1.2 4.6 3.3" opacity=".8" />
    </svg>
  );
}

/** Xana's mark: a voice wave. */
function XanaMark() {
  return (
    <svg viewBox="0 0 24 24" className="size-[58%]" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
      <path d="M4 10.5v3M8 7.5v9M12 4.5v15M16 7.5v9M20 10.5v3" />
    </svg>
  );
}

/** A round mark for an AI assistant. Decorative: the name is always shown or read beside it. */
export function AssistantAvatar({
  who,
  size = "md",
  className,
}: {
  who: keyof typeof STYLES;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}) {
  const sizes = { sm: "size-7", md: "size-8", lg: "size-11", xl: "size-20" };
  return (
    <span
      aria-hidden="true"
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full shadow-xs ring-2 ring-white",
        STYLES[who],
        sizes[size],
        className,
      )}
    >
      {who === "steph" ? <StephMark /> : <XanaMark />}
    </span>
  );
}
