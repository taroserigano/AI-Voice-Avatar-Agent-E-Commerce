import { cn } from "@/lib/cn";
import Link from "next/link";

/**
 * The Larkspur mark: a flower spike (florets that shrink toward a marigold bud) on a
 * rounded violet tile. Pure geometry, no gradients or ids, so it can render many times per page.
 */
export function LogoMark({ inverted = false, className }: { inverted?: boolean; className?: string }) {
  const tile = inverted ? "#ffffff" : "var(--color-brand-600)";
  const glow = inverted ? "var(--color-brand-100)" : "var(--color-brand-500)";
  const petal = inverted ? "var(--color-brand-600)" : "#ffffff";
  const bud = inverted ? "var(--color-accent-500)" : "var(--color-accent-300)";
  return (
    <svg aria-hidden="true" focusable="false" viewBox="0 0 32 32" className={cn("size-8 shrink-0", className)}>
      <rect width="32" height="32" rx="9.5" fill={tile} />
      {/* soft highlight in the top-right corner for depth */}
      <path d="M32 9.5V20C25 16 20 9 20.5 0H22.5A9.5 9.5 0 0 1 32 9.5Z" fill={glow} opacity={inverted ? 0.7 : 0.55} />
      {/* stem */}
      <path d="M15.6 27.5c.2-4.8.1-10.6 1.1-18.2" stroke={petal} strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.85" />
      {/* leaf */}
      <path d="M15.7 27.4c-3.1.1-5.2-1.4-5.9-3.8 2.8-.3 4.9.9 5.9 3.8Z" fill={petal} opacity="0.75" />
      {/* florets, largest at the base */}
      <circle cx="19.4" cy="21.2" r="3.1" fill={petal} />
      <circle cx="13" cy="17.6" r="2.7" fill={petal} />
      <circle cx="18.9" cy="13.9" r="2.25" fill={petal} />
      <circle cx="14" cy="10.6" r="1.8" fill={petal} />
      <circle cx="17.4" cy="6.9" r="1.55" fill={bud} />
    </svg>
  );
}

export function Logo({
  href = "/",
  inverted = false,
  className,
}: {
  href?: string;
  inverted?: boolean;
  className?: string;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "group inline-flex min-h-11 items-center gap-2.5 rounded-xl font-display text-[1.375rem] font-semibold tracking-[-0.03em]",
        inverted ? "text-white" : "text-ink",
        className,
      )}
      aria-label="Larkspur home"
    >
      <LogoMark
        inverted={inverted}
        className="transition-transform duration-300 ease-spring group-hover:-rotate-6 motion-reduce:group-hover:rotate-0"
      />
      <span aria-hidden="true">Larkspur</span>
    </Link>
  );
}
