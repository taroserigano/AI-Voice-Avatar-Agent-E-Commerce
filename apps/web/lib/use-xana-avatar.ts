"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { DailyCall } from "@daily-co/daily-js";
import type { EchoMessage } from "./avatar-echo";

/**
 * Xana's face in the browser: joins the private Tavus room the voice agent made for this call
 * (daily-js as a call object, our own UI) and shows the video that comes back.
 *
 * The browser publishes nothing to the room: no microphone and no camera, so the customer's
 * voice and face never reach Tavus. Xana's speech goes in as echo messages (avatar-echo.ts).
 * If the room can't be joined, or no video arrives within 8 s, it reports "failed" and the
 * call carries on with the orb and local audio.
 */

export type AvatarStatus = "off" | "starting" | "live" | "failed";
export type AvatarHandlers = {
  /** A Tavus event (speaking started or stopped, and so on). */
  onEvent: (eventType: string, properties: Record<string, unknown> | null) => void;
  /** Her video is showing. */
  onLive: () => void;
  /** The room couldn't be joined, no video came, or the face left. */
  onFailed: () => void;
};

const VIDEO_TIMEOUT_MS = 8000;

export function useXanaAvatar(handlers: AvatarHandlers) {
  const [status, setStatus] = useState<AvatarStatus>("off");
  const [stream, setStream] = useState<MediaStream | null>(null);
  const callRef = useRef<DailyCall | null>(null);
  const handlersRef = useRef(handlers);
  useEffect(() => {
    handlersRef.current = handlers;
  });

  const leave = useCallback(async () => {
    const call = callRef.current;
    callRef.current = null;
    setStream(null);
    setStatus("off");
    if (!call) return;
    try {
      await call.leave();
    } catch {
      // already gone
    }
    await call.destroy().catch(() => undefined);
  }, []);

  const join = useCallback(
    async (room: { url: string; token: string | null }) => {
      if (callRef.current) await leave();
      setStatus("starting");
      const fail = async () => {
        if (!callRef.current) return;
        await leave();
        setStatus("failed");
        handlersRef.current.onFailed();
      };
      try {
        const { default: Daily } = await import("@daily-co/daily-js");
        const call = Daily.createCallObject({
          audioSource: false,
          videoSource: false,
          subscribeToTracksAutomatically: true,
        });
        callRef.current = call;
        const tracks = new Map<string, MediaStreamTrack>();
        const timer = setTimeout(() => {
          if (!tracks.has("video")) void fail();
        }, VIDEO_TIMEOUT_MS);

        call.on("track-started", (e) => {
          if (!e?.participant || e.participant.local || !e.track) return;
          if (e.track.kind !== "video" && e.track.kind !== "audio") return;
          tracks.set(e.track.kind, e.track);
          setStream(new MediaStream([...tracks.values()]));
          if (e.track.kind === "video") {
            clearTimeout(timer);
            setStatus("live");
            handlersRef.current.onLive();
          }
        });
        call.on("app-message", (e) => {
          const data = (e?.data ?? {}) as {
            event_type?: unknown;
            properties?: unknown;
          };
          if (typeof data.event_type === "string") {
            handlersRef.current.onEvent(data.event_type, (data.properties as Record<string, unknown>) ?? null);
          }
        });
        call.on("participant-left", (e) => {
          if (e?.participant && !e.participant.local) void fail();
        });
        call.on("error", () => void fail());

        await call.join({
          url: room.url,
          token: room.token ?? undefined,
          startVideoOff: true,
          startAudioOff: true,
        });
      } catch {
        if (callRef.current) await fail();
        else {
          setStatus("failed");
          handlersRef.current.onFailed();
        }
      }
    },
    [leave],
  );

  const send = useCallback((msg: EchoMessage) => {
    try {
      callRef.current?.sendAppMessage(msg, "*");
    } catch {
      // a closed room: the timeline's fallbacks cover what wasn't heard
    }
  }, []);

  useEffect(
    () => () => {
      void leave();
    },
    [leave],
  );

  return { status, stream, join, leave, send };
}
