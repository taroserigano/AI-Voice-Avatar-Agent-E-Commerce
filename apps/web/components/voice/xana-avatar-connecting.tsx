"use client";

/* eslint-disable @next/next/no-img-element -- small local images */

import type { Background } from "@/lib/xana-looks";
import { lookThumb } from "@/lib/xana-looks";

/**
 * Holds Xena's place while her video connects (turning Video on, or a new look: a new Tavus
 * room takes ~5-10 s). Without it the page fell back to the orb and looked like video was off.
 * Shows the chosen look on the chosen background, with a spinner.
 */
export function XanaAvatarConnecting({
  look,
  label,
  background,
}: {
  look: string | null;
  label: string | null;
  background: Background;
}) {
  return (
    <div
      role="status"
      className="relative aspect-video w-[min(36rem,92vw,max(10rem,calc((100dvh-31rem)*16/9)))] overflow-hidden rounded-[2rem] border border-white/10 bg-black shadow-[0_24px_80px_-12px_rgb(103_64_222/0.55)]"
    >
      <img src={background.src} alt="" className="absolute inset-0 size-full object-cover" />
      {look ? (
        <img
          src={lookThumb(look)}
          alt=""
          className="absolute bottom-0 left-1/2 h-[92%] -translate-x-1/2 rounded-t-3xl object-cover opacity-70 blur-[2px]"
        />
      ) : null}
      <div className="absolute inset-0 grid place-items-center bg-black/35">
        <div className="flex flex-col items-center gap-3">
          <span
            aria-hidden
            className="size-10 animate-spin rounded-full border-[3px] border-white/30 border-t-white motion-reduce:animate-none"
          />
          <p className="rounded-full bg-black/45 px-4 py-1.5 text-sm font-semibold text-white">
            Connecting {label ?? "Xena"}…
          </p>
        </div>
      </div>
    </div>
  );
}
