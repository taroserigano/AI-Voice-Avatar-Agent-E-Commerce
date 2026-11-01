"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { createGreenScreen, type GreenScreen } from "@/lib/green-screen";
import type { Background } from "@/lib/xana-looks";
import type { VoiceStateName } from "@/lib/voice-protocol";

/**
 * Xena's face (Tavus) where the orb was: her live video and voice, on the same dark stage,
 * with a soft glow that follows the call's state like the orb's rings did. When Tavus renders
 * her on a green screen, the chosen background is drawn behind her (lib/green-screen.ts).
 * The state is announced in text beside it, so the video itself is decorative for screen
 * readers.
 */
export function XanaAvatar({
  stream,
  state,
  greenscreen,
  background,
  onPlaying,
  onStopped,
}: {
  stream: MediaStream;
  state: VoiceStateName | "off";
  greenscreen: boolean;
  background: Background;
  onPlaying: () => void;
  onStopped: () => void;
}) {
  const video = useRef<HTMLVideoElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const screen = useRef<GreenScreen | null>(null);
  const bgSrc = useRef(background.src);
  // Only shown once, after the customer turned video on, so this never runs on the server.
  const [webgl] = useState(() => Boolean(document.createElement("canvas").getContext("webgl")));
  const keyed = greenscreen && webgl;
  const [blocked, setBlocked] = useState(false);

  useEffect(() => {
    const el = video.current;
    if (!el || el.srcObject === stream) return;
    el.srcObject = stream;
    let cancelled = false;
    void el.play().catch(() => { if (!cancelled) setBlocked(true); });
    return () => { cancelled = true; el.srcObject = null; };
  }, [stream]);

  // Key out the green, frame by frame, while the room is on a green screen.
  useEffect(() => {
    const el = video.current;
    const cv = canvas.current;
    if (!keyed || !el || !cv) return;
    const gs = createGreenScreen(cv, el);
    if (!gs) return;
    screen.current = gs;
    loadBackground(gs, bgSrc.current);
    let stop = false;
    const tick = () => {
      if (stop) return;
      gs.render();
      if ("requestVideoFrameCallback" in el) el.requestVideoFrameCallback(tick);
      else requestAnimationFrame(tick);
    };
    tick();
    return () => {
      stop = true;
      gs.dispose();
      screen.current = null;
    };
  }, [keyed]);

  useEffect(() => {
    bgSrc.current = background.src;
    if (screen.current) loadBackground(screen.current, background.src);
  }, [background.src]);

  return (
    <div
      className={cn(
        "relative aspect-video w-[min(36rem,92vw,max(10rem,calc((100dvh-31rem)*16/9)))] overflow-hidden rounded-[2rem] border border-white/10 bg-black",
        "shadow-[0_24px_80px_-12px_rgb(103_64_222/0.55)] transition-shadow duration-300",
        state === "speaking" && "shadow-[0_24px_90px_-8px_rgb(125_100_239/0.85)]",
        state === "hearing" && "ring-2 ring-brand-300/50",
      )}
    >
      {/* Plays her voice; hidden under the keyed canvas when there is one. */}
      <video ref={video} autoPlay playsInline aria-label="Xena avatar"
        onPlaying={() => { setBlocked(false); onPlaying(); }}
        onPause={onStopped} onError={onStopped}
        className="absolute inset-0 size-full object-cover" />
      <canvas ref={canvas} aria-hidden className={cn("absolute inset-0 size-full object-cover", !keyed && "hidden")} />
      {blocked ? <button type="button" className="absolute inset-x-8 bottom-6 z-10 rounded-xl bg-brand-600 px-4 py-3 font-semibold"
        onClick={() => { void video.current?.play().catch(() => setBlocked(true)); }}>Play avatar audio</button> : null}
      <div className="pointer-events-none absolute inset-0 rounded-[2rem] shadow-[inset_0_0_0_1px_rgb(255_255_255/0.08)]" />
    </div>
  );
}

function loadBackground(gs: GreenScreen, src: string): void {
  const img = new Image();
  img.onload = () => gs.setBackground(img);
  img.src = src;
}
