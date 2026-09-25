import Link from "next/link";

export function Logo({ href = "/", inverted = false }: { href?: string; inverted?: boolean }) {
  return (
    <Link
      href={href}
      className={`inline-flex items-center gap-2 text-xl font-extrabold tracking-tight ${inverted ? "text-white" : "text-brand-800"}`}
      aria-label="Larkspur home"
    >
      <svg aria-hidden="true" viewBox="0 0 32 32" className="h-8 w-8">
        <circle cx="16" cy="16" r="16" fill={inverted ? "#fff" : "#4338ca"} />
        <path
          d="M16 6c2.5 3 2.5 6 0 9-2.5-3-2.5-6 0-9Zm-6 8c3.5.5 5.5 2.5 6 6-3.5-.5-5.5-2.5-6-6Zm12 0c-.5 3.5-2.5 5.5-6 6 .5-3.5 2.5-5.5 6-6Zm-6 7v5"
          stroke={inverted ? "#4338ca" : "#fbbf24"}
          strokeWidth="2"
          strokeLinecap="round"
          fill="none"
        />
      </svg>
      Larkspur
    </Link>
  );
}
