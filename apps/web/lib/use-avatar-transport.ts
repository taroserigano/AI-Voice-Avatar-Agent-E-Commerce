"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { EchoMessage } from "./avatar-echo";
import type { LiveAvatarCommand } from "./heygen-playback";
import type { ServerMessage } from "./voice-protocol";

export type AvatarStatus = "off" | "starting" | "live" | "failed";
export type AvatarRoom = Extract<ServerMessage, { type: "avatar" }>;
export type AvatarHandlers = {
  onEvent: (eventType: string, properties: Record<string, unknown> | null) => void;
  onLive: () => void;
  onFailed: () => void;
};

/** Both transports receive remote tracks only. No camera/microphone is published. */
export function useAvatarTransport(handlers: AvatarHandlers) {
  const [status, setStatus] = useState<AvatarStatus>("off");
  const [stream, setStream] = useState<MediaStream | null>(null);
  const epoch = useRef(0);
  const cleanup = useRef<(() => Promise<void>) | null>(null);
  const sendRef = useRef<(msg: EchoMessage | LiveAvatarCommand) => void>(() => undefined);
  const handlersRef = useRef(handlers);
  const playing = useRef(false);
  const disposing = useRef(Promise.resolve());
  const failRef = useRef<() => void>(() => undefined);
  useEffect(() => { handlersRef.current = handlers; });

  const leave = useCallback(async () => {
    ++epoch.current;
    const dispose = cleanup.current;
    cleanup.current = null;
    sendRef.current = () => undefined;
    playing.current = false;
    setStream(null);
    setStatus("off");
    disposing.current = disposing.current.then(() => dispose?.()).catch(() => undefined);
    await disposing.current;
  }, []);

  const join = useCallback(async (credentials: AvatarRoom) => {
    const generation = ++epoch.current;
    const current = () => epoch.current === generation;
    const previous = cleanup.current;
    cleanup.current = null;
    playing.current = false;
    setStream(null);
    setStatus("starting");
    disposing.current = disposing.current.then(() => previous?.()).catch(() => undefined);
    await disposing.current;
    if (!current()) return;
    let failed = false;
    const fail = () => {
      if (!current() || failed) return;
      failed = true;
      void leave();
      setStatus("failed");
      handlersRef.current.onFailed();
    };
    failRef.current = fail;
    const tracks = new Map<string, MediaStreamTrack>();
    let controlReady = credentials.provider === "tavus";
    let timer: ReturnType<typeof setTimeout> | undefined;
    const update = () => {
      if (!current() || !controlReady || !tracks.has("video") || !tracks.has("audio")) return;
      clearTimeout(timer);
      setStream(new MediaStream([...tracks.values()]));
      setStatus("live");
    };
    try {
      if (credentials.provider === "tavus") {
        const { default: Daily } = await import("@daily-co/daily-js");
        if (!current()) return;
        const call = Daily.createCallObject({
          audioSource: false, videoSource: false, subscribeToTracksAutomatically: true,
        });
        cleanup.current = async () => {
          clearTimeout(timer);
          await call.leave().catch(() => undefined);
          await call.destroy().catch(() => undefined);
        };
        timer = setTimeout(fail, 15_000);
        call.on("track-started", (e) => {
          if (!current() || !e?.participant || e.participant.local || !e.track) return;
          tracks.set(e.track.kind, e.track);
          update();
        });
        call.on("track-stopped", () => fail());
        call.on("app-message", (e) => {
          if (!current()) return;
          const data = e?.data as { event_type?: string; properties?: Record<string, unknown> } | undefined;
          if (data?.event_type) handlersRef.current.onEvent(data.event_type, data.properties ?? null);
        });
        call.on("participant-left", (e) => { if (e?.participant && !e.participant.local) fail(); });
        call.on("error", fail);
        sendRef.current = (msg) => {
          if (!current()) return;
          try { call.sendAppMessage(msg, "*"); } catch { fail(); }
        };
        await call.join({
          url: credentials.url, token: credentials.token ?? undefined,
          startVideoOff: true, startAudioOff: true,
        });
      } else {
        const { Room, RoomEvent } = await import("livekit-client");
        if (!current()) return;
        if (!credentials.token || !credentials.ws_url) throw new Error("Missing session credentials");
        const room = new Room({ adaptiveStream: false, dynacast: false });
        const socket = new WebSocket(credentials.ws_url);
        let heartbeat: ReturnType<typeof setInterval> | undefined;
        cleanup.current = async () => {
          clearTimeout(timer);
          clearInterval(heartbeat);
          socket.onclose = socket.onerror = socket.onmessage = null;
          socket.close();
          await room.disconnect().catch(() => undefined);
        };
        timer = setTimeout(fail, 20_000);
        room.on(RoomEvent.TrackSubscribed, (track) => {
          if (!current()) return;
          tracks.set(track.kind, track.mediaStreamTrack);
          update();
        });
        room.on(RoomEvent.TrackUnsubscribed, fail);
        room.on(RoomEvent.Disconnected, fail);
        room.on(RoomEvent.Reconnecting, fail);
        socket.onclose = socket.onerror = fail;
        socket.onmessage = (message) => {
          if (!current()) return;
          try {
            const event = JSON.parse(message.data) as Record<string, unknown>;
            if (event.type === "session.state_updated") {
              if (event.state === "connected") {
                controlReady = true;
                update();
                if (!heartbeat) heartbeat = setInterval(() => {
                  if (current() && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({ type: "session.keep_alive" }));
                  }
                }, 30_000);
              } else if (event.state === "disconnected") fail();
            } else if (event.type === "error") fail();
            else if (typeof event.type === "string") handlersRef.current.onEvent(event.type, event);
          } catch { fail(); }
        };
        sendRef.current = (message) => {
          if (!current()) return;
          if (!controlReady || socket.readyState !== WebSocket.OPEN || socket.bufferedAmount > 1024 * 1024) {
            fail();
            return;
          }
          socket.send(JSON.stringify(message));
        };
        await room.connect(credentials.url, credentials.token, { autoSubscribe: true });
      }
    } catch { fail(); }
  }, [leave]);

  // Tracks alone don't prove the browser is playing audio (autoplay may be blocked).
  const playbackStarted = useCallback(() => {
    if (playing.current) return;
    playing.current = true;
    handlersRef.current.onLive();
  }, []);
  const playbackStopped = useCallback(() => {
    if (playing.current) failRef.current();
  }, []);
  const send = useCallback((msg: EchoMessage | LiveAvatarCommand) => sendRef.current(msg), []);
  useEffect(() => () => { void leave(); }, [leave]);
  return { status, stream, join, leave, send, playbackStarted, playbackStopped };
}
