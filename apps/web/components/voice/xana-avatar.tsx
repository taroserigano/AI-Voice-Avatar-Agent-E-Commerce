"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/cn";
import type { VoiceStateName } from "@/lib/voice-protocol";

/**
 * Xana's face (Tavus) where the orb was: her live video and voice, on the same dark stage,
 * with a soft glow that follows the call's state like the orb's rings did. The state is
 * announced in text beside it, so the video itself is decorative for screen readers.
 */
export function XanaAvatar({ stream, state }: { stream: MediaStream; state: VoiceStateName | "off" }) {
  const video = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const el = video.current;
    if (!el || el.srcObject === stream) return;
    el.srcObject = stream;
    void el.play().catch(() => undefined);
  }, [stream]);

  return (
    <div
      aria-hidden
      className={cn(
        "relative aspect-video w-[min(36rem,92vw)] overflow-hidden rounded-[2rem] border border-white/10 bg-black",
        "shadow-[0_24px_80px_-12px_rgb(103_64_222/0.55)] transition-shadow duration-300",
        state === "speaking" && "shadow-[0_24px_90px_-8px_rgb(125_100_239/0.85)]",
        state === "hearing" && "ring-2 ring-brand-300/50",
      )}
    >
      <video ref={video} autoPlay playsInline className="size-full object-cover" />
      <div className="pointer-events-none absolute inset-0 rounded-[2rem] shadow-[inset_0_0_0_1px_rgb(255_255_255/0.08)]" />
    </div>
  );
}
