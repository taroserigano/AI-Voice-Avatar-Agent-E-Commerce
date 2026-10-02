"use client";

/* eslint-disable @next/next/no-img-element -- small local previews, no optimization needed */

import { useEffect, useId, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { BACKGROUNDS, backgroundFor, lookClip, lookThumb } from "@/lib/xana-looks";
import type { AvatarLook } from "@/lib/voice-protocol";

/**
 * Choose Xena's look (which face) and what's behind her, from a bar under her video that
 * opens into large preview cards: each look plays a 3-second clip of her, each background shows
 * the picture itself. Closed by default so the call keeps the room. A new look takes a few
 * seconds (a new video room), so picking one closes the panel to show her; a background is
 * drawn in the browser and changes at once.
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
  const [open, setOpen] = useState(false);
  const panel = useId();
  const [still] = useState(() => window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  const current = looks.find((l) => l.key === look) ?? looks[0];
  const bg = backgroundFor(background);

  // Opened below the fold on short screens: bring the whole panel into view.
  const panelRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    panelRef.current?.scrollIntoView({ block: "nearest", behavior: reduce ? "auto" : "smooth" });
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <div className="mt-4 w-full max-w-3xl">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panel}
        onClick={() => setOpen((o) => !o)}
        className="mx-auto flex min-h-14 items-center gap-3 rounded-full border border-white/15 bg-white/5 py-1.5 pl-1.5 pr-5 text-left transition hover:bg-white/10"
      >
        {current ? (
          <img src={lookThumb(current.key)} alt="" width={44} height={44} className="size-11 rounded-full object-cover object-top" />
        ) : null}
        <span className="leading-tight">
          <span className="block text-sm font-semibold text-white">
            {current?.label ?? "Xena"} · {bg.label}
          </span>
          <span className="block text-xs text-brand-200">{open ? "Close" : "Change look"}</span>
        </span>
        <Chevron open={open} />
      </button>

      {open ? (
        <div
          id={panel}
          ref={panelRef}
          className="mt-3 rounded-3xl border border-white/10 bg-white/4 p-4 text-left shadow-[0_24px_60px_-24px_rgb(0_0_0/0.6)] sm:p-5"
        >
          {looks.length > 1 ? (
            <fieldset>
              <legend className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-brand-200">Look</legend>
              <div role="radiogroup" aria-label="Look" className="grid grid-cols-3 gap-3 sm:grid-cols-5">
                {looks.map((l) => {
                  const selected = l.key === look;
                  return (
                    <button
                      key={l.key}
                      type="button"
                      role="radio"
                      aria-checked={selected}
                      disabled={busy}
                      onClick={() => {
                        if (!selected) onLook(l.key);
                        setOpen(false);
                      }}
                      className={cn(
                        "group relative aspect-4/5 overflow-hidden rounded-2xl border-2 bg-black transition disabled:opacity-60",
                        selected
                          ? "border-brand-300 shadow-[0_0_0_4px_rgb(125_100_239/0.35)]"
                          : "border-white/10 hover:-translate-y-0.5 hover:border-white/40",
                      )}
                    >
                      {still ? (
                        <img src={lookThumb(l.key)} alt="" className="size-full object-cover" />
                      ) : (
                        <video
                          src={lookClip(l.key)}
                          poster={lookThumb(l.key)}
                          autoPlay
                          muted
                          loop
                          playsInline
                          aria-hidden
                          className="size-full object-cover"
                        />
                      )}
                      <span className="absolute inset-x-0 bottom-0 bg-linear-to-t from-black/80 to-transparent px-2 pb-2 pt-6 text-center text-sm font-semibold text-white">
                        {l.label}
                      </span>
                      {selected ? <Check /> : null}
                    </button>
                  );
                })}
              </div>
            </fieldset>
          ) : null}

          <fieldset className={cn(looks.length > 1 && "mt-5")}>
            <legend className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-brand-200">Background</legend>
            <div role="radiogroup" aria-label="Background" className="grid grid-cols-3 gap-3 sm:grid-cols-5">
              {BACKGROUNDS.map((b) => {
                const selected = b.key === background;
                return (
                  <button
                    key={b.key}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    onClick={() => onBackground(b.key)}
                    className={cn(
                      "relative aspect-16/10 overflow-hidden rounded-2xl border-2 transition",
                      selected
                        ? "border-brand-300 shadow-[0_0_0_4px_rgb(125_100_239/0.35)]"
                        : "border-white/10 hover:border-white/40",
                    )}
                    style={{ background: b.swatch }}
                  >
                    <img src={b.src} alt="" className="size-full object-cover" />
                    <span className="absolute inset-x-0 bottom-0 bg-linear-to-t from-black/75 to-transparent px-2 pb-1.5 pt-5 text-center text-xs font-semibold text-white">
                      {b.label}
                    </span>
                    {selected ? <Check /> : null}
                  </button>
                );
              })}
            </div>
          </fieldset>
        </div>
      ) : null}
    </div>
  );
}

function Check() {
  return (
    <span className="absolute right-2 top-2 grid size-6 place-items-center rounded-full bg-brand-400 text-white shadow">
      <svg viewBox="0 0 16 16" className="size-3.5" aria-hidden>
        <path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </span>
  );
}

function Chevron({ open }: { open: boolean }) {
  return (
    <svg viewBox="0 0 20 20" className={cn("ml-1 size-5 text-neutral-300 transition-transform", open && "rotate-180")} aria-hidden>
      <path d="M5 8l5 5 5-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
