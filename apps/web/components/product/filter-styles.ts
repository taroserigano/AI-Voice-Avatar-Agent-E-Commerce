// Shared class strings for the listing filters. Kept in a plain module (not a "use client" one)
// so both the server-rendered filter groups and the client ones get real strings.

export const legendClasses = "float-left w-full text-xs font-semibold uppercase tracking-eyebrow text-muted";
export const optionRow =
  "flex min-h-10 cursor-pointer items-center gap-3 rounded-lg px-2 text-sm text-ink-soft transition-colors duration-150 hover:bg-sunken hover:text-ink has-[:checked]:font-semibold has-[:checked]:text-ink";
export const countPill = "ml-auto rounded-full bg-sunken px-2 py-0.5 text-xs tabular-nums text-muted";
export const controlClasses = "size-4.5 shrink-0 accent-brand-600";
