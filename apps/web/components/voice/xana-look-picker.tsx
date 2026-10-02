"use client";

/* eslint-disable @next/next/no-img-element -- tiny local thumbnails, no optimization needed */

import { cn } from "@/lib/cn";
import { BACKGROUNDS, lookThumb } from "@/lib/xana-looks";
import type { AvatarLook } from "@/lib/voice-protocol";

/**
 * Two rows of options under Xena's video: which face she has ("Look") and what's behind her
 * ("Background"). A new look takes a few seconds (a new video room); a new background is
 * instant (drawn in the browser).
 */
export function XanaLookPicker({
  looks,
  look,
  background,
  busy,
  onLook,
  onBackground,
}: {
  looks: AvatarLook[];
  look: string | null;
  background: string;
  busy: boolean;
  onLook: (key: string) => void;
  onBackground: (key: string) => void;
}) {
  return (
    <div className="mt-4 w-full max-w-2xl space-y-3 text-left">
      {looks.length > 1 ? (
        <Row label="Look">
          {looks.map((l) => (
            <Chip key={l.key} selected={l.key === look} disabled={busy} onClick={() => onLook(l.key)} label={l.label}>
              <img src={lookThumb(l.key)} alt="" width={28} height={28} className="size-7 rounded-full object-cover" />
            </Chip>
          ))}
        </Row>
      ) : null}
      <Row label="Background">
        {BACKGROUNDS.map((b) => (
          <Chip
            key={b.key}
            selected={b.key === background}
            onClick={() => onBackground(b.key)}
            label={b.label}
          >
            <span className="size-7 rounded-full border border-white/20" style={{ background: b.swatch }} />
          </Chip>
        ))}
      </Row>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-2">
      <span className="w-24 shrink-0 text-right text-xs font-bold uppercase tracking-[0.2em] text-brand-200 max-sm:w-full max-sm:text-center">
        {label}
      </span>
      <div role="radiogroup" aria-label={label} className="flex flex-wrap justify-center gap-2">
        {children}
      </div>
    </div>
  );
}

function Chip({
  selected,
  disabled,
  onClick,
  label,
  children,
}: {
  selected: boolean;
  disabled?: boolean;
  onClick: () => void;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "inline-flex min-h-11 items-center gap-2 rounded-full border py-1.5 pl-1.5 pr-4 text-sm font-medium transition disabled:opacity-60",
        selected
          ? "border-brand-300/70 bg-brand-500/25 text-white"
          : "border-white/15 bg-white/5 text-neutral-200 hover:bg-white/10",
      )}
    >
      {children}
      {label}
    </button>
  );
}
