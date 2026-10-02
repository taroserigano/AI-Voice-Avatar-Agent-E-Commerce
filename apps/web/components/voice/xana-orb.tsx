"use client";

import { cn } from "@/lib/cn";
import type { VoiceStateName } from "@/lib/voice-protocol";

/**
 * Xena's orb: a glassy rounded square inside two faint rings, with three orbiting motes.
 * It swells with the customer's voice while she listens and with her own voice while she
 * speaks, and pulses slowly while she thinks. Decorative: the state is announced in text.
 */
export function XanaOrb({
  state,
  level,
  className,
}: {
  state: VoiceStateName | "off";
  level: number;
  className?: string;
}) {
  const active = state === "hearing" || state === "speaking";
  // Levels are RMS (speech sits around 0.02–0.2): map to a gentle 0–14% swell.
  const swell = active ? Math.min(0.14, Math.sqrt(Math.max(0, level)) * 0.32) : 0;
  const spin = state === "speaking" ? "6s" : state === "thinking" ? "3.5s" : "18s";

  return (
    <div aria-hidden className={cn("relative grid size-[min(18rem,30vh)] place-items-center sm:size-[min(20rem,32vh)]", className)}>
      {/* Rings */}
      <div className="absolute inset-0 rounded-full border border-white/10" />
      <div className="absolute inset-[9%] rounded-full border border-white/[0.07]" />
      <div
        className={cn(
          "absolute inset-[-6%] rounded-full bg-[radial-gradient(closest-side,rgb(125_100_239/0.30),transparent)] transition-opacity duration-500",
          active || state === "thinking" ? "opacity-100" : "opacity-60",
        )}
      />
      {/* Orbiting motes */}
      <div className="absolute inset-0 animate-[voice-spin_28s_linear_infinite]">
        <span className="absolute right-[12%] top-[10%] size-2 rounded-full bg-brand-200/80 shadow-[0_0_12px_rgb(188_183_255/0.9)]" />
        <span className="absolute bottom-[19%] left-[4%] size-1.5 rounded-full bg-brand-200/70" />
        <span className="absolute bottom-[22%] right-[4%] size-1 rounded-full bg-white/60" />
      </div>
      {/* The orb */}
      <div
        className={cn(
          "relative size-[58%] transition-transform duration-100 ease-out",
          state === "thinking" && "animate-[voice-breathe_1.6s_ease-in-out_infinite]",
          (state === "off" || state === "listening" || state === "connecting") &&
            "animate-[voice-breathe_4.5s_ease-in-out_infinite]",
        )}
        style={{ transform: swell ? `scale(${1 + swell})` : undefined }}
      >
        <div className="absolute inset-0 overflow-hidden rounded-[26%] shadow-[0_24px_80px_-12px_rgb(103_64_222/0.75),inset_0_0_0_1px_rgb(255_255_255/0.25)]">
          <div
            className="absolute inset-[-30%] bg-voice-orb"
            style={{ animation: `voice-spin ${spin} linear infinite` }}
          />
          <div className="absolute inset-0 bg-[radial-gradient(60%_60%_at_50%_45%,rgb(255_255_255/0.28),transparent_70%)]" />
          <div className="absolute inset-0 rounded-[26%] bg-gradient-to-br from-white/25 via-transparent to-brand-900/20" />
        </div>
      </div>
    </div>
  );
}
