"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { CaptionSegment } from "./voice-captions";
import {
  MIC_RATE,
  SPEECH_RATE,
  parseServerMessage,
  splitAudioFrame,
  type Citation,
  type ClientMessage,
  type QuoteCard,
  type ServerMessage,
  type VoiceStateName,
} from "./voice-protocol";
import { CAPTURE_WORKLET, PLAYBACK_WORKLET, addWorklet } from "./voice-worklets";

/**
 * The Xana voice session in the browser: one WebSocket to the voice agent, the microphone
 * streamed up continuously (the server hears the end of speech, not the browser), and Xana's
 * speech streamed down and played gaplessly as it's generated. Captions are driven by the
 * player's clock, so text and voice stay in step. Talking over Xana stops her at once.
 */

export type Ready = Extract<ServerMessage, { type: "ready" }>;
export type TurnMetrics = Extract<ServerMessage, { type: "turn.done" }>["metrics"];

export type VoiceAgent = {
  state: VoiceStateName | "off";
  ready: Ready | null;
  userText: string;
  userFinal: boolean;
  segments: CaptionSegment[];
  toolLabel: string | null;
  quote: QuoteCard | null;
  confirmDecision: "yes" | "no" | "unclear" | null;
  citations: Citation[];
  cards: Record<string, unknown>[];
  metrics: TurnMetrics | null;
  error: string | null;
  muted: boolean;
  micLevel: number;
  speechLevel: number;
  start: () => Promise<void>;
  stop: () => void;
  setMuted: (muted: boolean) => void;
  interrupt: () => void;
  sendText: (text: string) => void;
  quoteOutcome: (quoteId: string, outcome: "confirmed" | "declined") => void;
};

export function voiceSocketUrl(): string {
  const configured = process.env.NEXT_PUBLIC_VOICE_WS_URL;
  if (configured) return configured;
  const { protocol, hostname } = window.location;
  const port = process.env.NEXT_PUBLIC_VOICE_PORT ?? "8103";
  return `${protocol === "https:" ? "wss" : "ws"}://${hostname}:${port}/v1/voice/xana`;
}

export function useVoiceAgent(conversationId?: string | null): VoiceAgent {
  const [state, setState] = useState<VoiceStateName | "off">("off");
  const [ready, setReady] = useState<Ready | null>(null);
  const [userText, setUserText] = useState("");
  const [userFinal, setUserFinal] = useState(false);
  const [segments, setSegments] = useState<CaptionSegment[]>([]);
  const [toolLabel, setToolLabel] = useState<string | null>(null);
  const [quote, setQuote] = useState<QuoteCard | null>(null);
  const [confirmDecision, setConfirmDecision] = useState<"yes" | "no" | "unclear" | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [cards, setCards] = useState<Record<string, unknown>[]>([]);
  const [metrics, setMetrics] = useState<TurnMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [muted, setMutedState] = useState(false);
  const [micLevel, setMicLevel] = useState(0);
  const [speechLevel, setSpeechLevel] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const micRef = useRef<MediaStream | null>(null);
  const captureCtxRef = useRef<AudioContext | null>(null);
  const captureNodeRef = useRef<AudioWorkletNode | null>(null);
  const playCtxRef = useRef<AudioContext | null>(null);
  const playNodeRef = useRef<AudioWorkletNode | null>(null);
  const droppedRef = useRef<Set<number>>(new Set());
  const stoppedRef = useRef(true);

  const send = useCallback((msg: ClientMessage) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(msg));
  }, []);

  const updateSegment = useCallback((segment: number, patch: Partial<CaptionSegment>) => {
    setSegments((segs) => segs.map((s) => (s.segment === segment ? { ...s, ...patch } : s)));
  }, []);

  const onServer = useCallback(
    (msg: ServerMessage) => {
      switch (msg.type) {
        case "ready":
          setReady(msg);
          break;
        case "state":
          setState(msg.state);
          if (msg.state === "hearing") setToolLabel(null);
          break;
        case "user.partial":
          setUserText(msg.text);
          setUserFinal(false);
          break;
        case "user.final":
          setUserText(msg.text);
          setUserFinal(true);
          // A new question: the previous answer's captions and cards give way.
          setSegments([]);
          setToolLabel(null);
          setCitations([]);
          setConfirmDecision(null);
          setMetrics(null);
          break;
        case "segment.start":
          setSegments((segs) => [
            ...segs,
            { segment: msg.segment, text: msg.text, words: [], playedMs: 0, done: false },
          ]);
          break;
        case "segment.text":
          setSegments((segs) =>
            segs.map((s) =>
              s.segment === msg.segment ? { ...s, text: s.text ? `${s.text} ${msg.text}` : msg.text } : s,
            ),
          );
          break;
        case "segment.words":
          setSegments((segs) =>
            segs.map((s) => (s.segment === msg.segment ? { ...s, words: [...s.words, ...msg.words] } : s)),
          );
          break;
        case "segment.end":
          playNodeRef.current?.port.postMessage({ type: "end", segment: msg.segment });
          break;
        case "drop":
          for (const s of msg.segments) droppedRef.current.add(s);
          playNodeRef.current?.port.postMessage({ type: "drop", segments: msg.segments });
          // Keep what was actually heard; the rest was never said.
          setSegments((segs) =>
            segs
              .map((s) => (msg.segments.includes(s.segment) ? { ...s, text: "", words: [], done: true } : s))
              .filter((s) => s.text !== "" || !msg.segments.includes(s.segment)),
          );
          break;
        case "tool":
          setToolLabel(msg.label);
          break;
        case "card":
          setCards((cs) => [...cs.slice(-5), msg.card]);
          break;
        case "quote":
          setQuote(msg.quote);
          setConfirmDecision(null);
          break;
        case "citations":
          setCitations(msg.citations);
          break;
        case "confirm.result":
          setConfirmDecision(msg.decision);
          break;
        case "turn.done":
          setMetrics(msg.metrics);
          setToolLabel(null);
          break;
        case "error":
          setError(msg.message);
          if (msg.fatal) setState("error");
          break;
      }
    },
    [],
  );

  const stop = useCallback(() => {
    stoppedRef.current = true;
    wsRef.current?.close(1000);
    wsRef.current = null;
    micRef.current?.getTracks().forEach((t) => t.stop());
    micRef.current = null;
    captureNodeRef.current?.disconnect();
    playNodeRef.current?.disconnect();
    void captureCtxRef.current?.close().catch(() => undefined);
    void playCtxRef.current?.close().catch(() => undefined);
    captureCtxRef.current = null;
    playCtxRef.current = null;
    captureNodeRef.current = null;
    playNodeRef.current = null;
    setState("off");
    setMicLevel(0);
    setSpeechLevel(0);
  }, []);

  const start = useCallback(async () => {
    if (!stoppedRef.current) return;
    stoppedRef.current = false;
    setError(null);
    setState("connecting");
    try {
      // Playback first, inside the click, so the browser lets it make sound.
      const playCtx = new AudioContext({ sampleRate: SPEECH_RATE, latencyHint: "interactive" });
      playCtxRef.current = playCtx;
      await addWorklet(playCtx, PLAYBACK_WORKLET);
      const player = new AudioWorkletNode(playCtx, "xana-playback", { outputChannelCount: [1] });
      player.connect(playCtx.destination);
      playNodeRef.current = player;
      player.port.onmessage = (e: MessageEvent) => {
        const m = e.data as { type: string; segment: number; playedMs: number; level?: number; idle?: boolean };
        if (m.type === "progress") {
          setSpeechLevel(m.level ?? 0);
          if (m.segment >= 0) updateSegment(m.segment, { playedMs: m.playedMs });
        } else if (m.type === "done") {
          updateSegment(m.segment, { playedMs: m.playedMs, done: true });
          if (!droppedRef.current.has(m.segment)) {
            send({ type: "played", segment: m.segment, complete: true, played_ms: m.playedMs });
          }
        }
      };

      const mic = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      if (stoppedRef.current) {
        mic.getTracks().forEach((t) => t.stop());
        return;
      }
      micRef.current = mic;
      // The device's own rate (some browsers can't mix rates); the worklet resamples.
      const captureCtx = new AudioContext({ latencyHint: "interactive" });
      captureCtxRef.current = captureCtx;
      await addWorklet(captureCtx, CAPTURE_WORKLET);
      const capture = new AudioWorkletNode(captureCtx, "xana-capture", {
        processorOptions: { targetRate: MIC_RATE },
      });
      captureCtx.createMediaStreamSource(mic).connect(capture);
      captureNodeRef.current = capture;

      const ws = new WebSocket(voiceSocketUrl());
      ws.binaryType = "arraybuffer";
      wsRef.current = ws;
      capture.port.onmessage = (e: MessageEvent) => {
        const m = e.data as { pcm?: ArrayBuffer; level: number };
        setMicLevel(m.level);
        if (m.pcm && ws.readyState === WebSocket.OPEN) ws.send(m.pcm);
      };
      ws.onopen = () =>
        ws.send(
          JSON.stringify({
            type: "hello",
            conversation_id: conversationId ?? null,
            mic_rate: MIC_RATE,
            speech_rate: SPEECH_RATE,
          } satisfies ClientMessage),
        );
      ws.onmessage = (e: MessageEvent) => {
        if (typeof e.data === "string") {
          const msg = parseServerMessage(e.data);
          if (msg) onServer(msg);
          return;
        }
        const frame = splitAudioFrame(e.data as ArrayBuffer);
        if (!frame || droppedRef.current.has(frame.segment)) return;
        const pcm = frame.pcm.slice();
        player.port.postMessage({ type: "audio", segment: frame.segment, pcm: pcm.buffer }, [pcm.buffer]);
      };
      ws.onclose = (e) => {
        if (stoppedRef.current) return;
        setError(
          e.code === 4401
            ? "Your session has ended. Sign in again to talk to Xana."
            : "The connection to Xana dropped. Tap the orb to reconnect.",
        );
        stop();
      };
      ws.onerror = () => setError("Couldn't reach Xana's voice service.");
      await playCtx.resume();
    } catch (err) {
      const denied = err instanceof DOMException && (err.name === "NotAllowedError" || err.name === "SecurityError");
      setError(
        denied
          ? "Xana needs your microphone. Allow it in your browser's site settings, then try again."
          : "Couldn't start voice on this device.",
      );
      stop();
      setState("error");
    }
  }, [conversationId, onServer, send, stop, updateSegment]);

  const setMuted = useCallback(
    (next: boolean) => {
      setMutedState(next);
      captureNodeRef.current?.port.postMessage({ type: "mute", muted: next });
      send({ type: "mute", muted: next });
    },
    [send],
  );

  const interrupt = useCallback(() => send({ type: "interrupt" }), [send]);
  const sendText = useCallback((text: string) => send({ type: "text", text }), [send]);
  const quoteOutcome = useCallback(
    (quoteId: string, outcome: "confirmed" | "declined") => {
      setQuote(null);
      send({ type: "quote.outcome", quote_id: quoteId, outcome });
    },
    [send],
  );

  useEffect(() => stop, [stop]);

  return {
    state,
    ready,
    userText,
    userFinal,
    segments,
    toolLabel,
    quote,
    confirmDecision,
    citations,
    cards,
    metrics,
    error,
    muted,
    micLevel,
    speechLevel,
    start,
    stop,
    setMuted,
    interrupt,
    sendText,
    quoteOutcome,
  };
}
