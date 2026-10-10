"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { captionFor, type CaptionSegment } from "./voice-captions";
import {
  MIC_RATE,
  SPEECH_RATE,
  parseServerMessage,
  splitAudioFrame,
  type Citation,
  type ClientMessage,
  type AvatarLook,
  type AvatarOffer,
  type AvatarProvider,
  type QuoteCard,
  type ServerMessage,
  type VoiceStateName,
} from "./voice-protocol";
import { CAPTURE_WORKLET, PLAYBACK_WORKLET, addWorklet } from "./voice-worklets";
import { AvatarEcho } from "./avatar-echo";
import { useAvatarTransport, type AvatarStatus, type AvatarRoom } from "./use-avatar-transport";
import type { AvatarPlayback } from "./avatar-playback";
import { HeygenPlayback } from "./heygen-playback";
import { DEFAULT_BACKGROUND, backgroundFor, loadPrefs, savePrefs, type Background } from "./xana-looks";

/**
 * The Xena voice session in the browser: one WebSocket to the voice agent, the microphone
 * streamed up continuously (the server hears the end of speech, not the browser), and Xena's
 * speech streamed down and played gaplessly as it's generated. Captions are driven by the
 * player's clock, so text and voice stay in step. Talking over Xena stops her at once.
 *
 * With Video on (Tavus, docs/features/10-xana-avatar), Xena's speech goes to her face instead
 * of the local player, and what the customer has heard comes from Tavus (avatar-echo.ts): the
 * captions follow her lips, and a segment is reported played in full only once Tavus has said
 * it. Audio switches between the two only between segments.
 */

export type Ready = Extract<ServerMessage, { type: "ready" }>;
export type TurnMetrics = Extract<ServerMessage, { type: "turn.done" }>["metrics"];

export type VoiceAvatar = {
  provider: AvatarProvider;
  switching: boolean;
  offer: AvatarOffer;
  wanted: boolean;
  status: AvatarStatus;
  stream: MediaStream | null;
  error: string | null;
  looks: AvatarLook[];
  look: string | null;
  background: Background;
  greenscreen: boolean;
  playbackStarted: () => void;
  playbackStopped: () => void;
};

/** One finished exchange, for the conversation panel: what the customer said, what Xena was
 *  heard saying, and the cards and sources that came with it. */
export type VoiceTurn = {
  id: number;
  user: string;
  xena: string;
  cards: Record<string, unknown>[];
  citations: Citation[];
};

/** One thing Xena did for the current question ("Looking up your orders…"). */
export type VoiceStep = { label: string; done: boolean };

/** A new step: the ones before it are done (her tools run one after another). */
export function addStep(steps: VoiceStep[], label: string): VoiceStep[] {
  const last = steps.at(-1);
  if (last && !last.done && last.label === label) return steps;
  return [...steps.map((s) => ({ ...s, done: true })), { label, done: false }];
}

function allDone(steps: VoiceStep[]): VoiceStep[] {
  return steps.some((s) => !s.done) ? steps.map((s) => ({ ...s, done: true })) : steps;
}

export type VoiceAgent = {
  state: VoiceStateName | "off";
  /** Earlier exchanges in this call, oldest first (the current one is live in the fields below). */
  history: VoiceTurn[];
  /** Cards sent during the current exchange only. */
  turnCards: Record<string, unknown>[];
  ready: Ready | null;
  userText: string;
  userFinal: boolean;
  segments: CaptionSegment[];
  toolLabel: string | null;
  /** What she did or is doing for this question, in order (shown while she works). */
  steps: VoiceStep[];
  /** Questions to tap next. */
  suggestions: string[];
  quote: QuoteCard | null;
  quoteButtonOnly: boolean;
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
  /** Ask a question as text (a tapped suggestion); stops her first if she's talking. */
  ask: (text: string) => void;
  quoteOutcome: (quoteId: string, outcome: "confirmed" | "declined") => void;
  avatar: VoiceAvatar;
  setVideo: (on: boolean) => void;
  chooseLook: (key: string) => void;
  chooseBackground: (key: string) => void;
};

export function voiceSocketUrl(): string {
  const configured = process.env.NEXT_PUBLIC_VOICE_WS_URL;
  if (configured) return configured;
  const { protocol, hostname } = window.location;
  const port = process.env.NEXT_PUBLIC_VOICE_PORT ?? "8103";
  return `${protocol === "https:" ? "wss" : "ws"}://${hostname}:${port}/v1/voice/xana`;
}

export function useVoiceAgent(conversationId?: string | null, provider: AvatarProvider = "tavus"): VoiceAgent {
  const [state, setState] = useState<VoiceStateName | "off">("off");
  const [ready, setReady] = useState<Ready | null>(null);
  const [userText, setUserText] = useState("");
  const [userFinal, setUserFinal] = useState(false);
  const [segments, setSegments] = useState<CaptionSegment[]>([]);
  const [toolLabel, setToolLabel] = useState<string | null>(null);
  const [steps, setSteps] = useState<VoiceStep[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [quote, setQuote] = useState<QuoteCard | null>(null);
  const [readbackInterrupted, setReadbackInterrupted] = useState(false);
  const [confirmDecision, setConfirmDecision] = useState<"yes" | "no" | "unclear" | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [cards, setCards] = useState<Record<string, unknown>[]>([]);
  const [history, setHistory] = useState<VoiceTurn[]>([]);
  const [turnCards, setTurnCards] = useState<Record<string, unknown>[]>([]);
  // The exchange in progress, read when the next one starts (refs: read inside a server event).
  const turnRef = useRef<{ user: string; cards: Record<string, unknown>[]; citations: Citation[] }>({
    user: "", cards: [], citations: [],
  });
  const segmentsRef = useRef<CaptionSegment[]>([]);
  const stateRef = useRef<VoiceStateName | "off">("off");
  const turnIdRef = useRef(0);
  useEffect(() => {
    segmentsRef.current = segments;
  }, [segments]);
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
  const conversationRef = useRef(conversationId);
  const providerRef = useRef(provider);
  const requestRef = useRef(0);
  const generationsRef = useRef(new Map<number, number>());
  const wantedRef = useRef(false);
  const mutedRef = useRef(false);
  const switchingRef = useRef(false);
  const switchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const selectRef = useRef<(provider: AvatarProvider | null, look?: string) => void>(() => undefined);
  // Video: the echo sender while Tavus is live, whether audio goes to it, and which
  // segments it's playing (the rest play locally).
  const [avatarWanted, setAvatarWanted] = useState(false);
  const [avatarSwitching, setAvatarSwitching] = useState(false);
  const [avatarError, setAvatarError] = useState<string | null>(null);
  // The customer's picks (remembered in this browser) and whether the room is on a green
  // screen (then the background is drawn behind her).
  const [look, setLook] = useState<string | null>(null);
  const [backgroundKey, setBackgroundKey] = useState(DEFAULT_BACKGROUND);
  const [greenscreen, setGreenscreen] = useState(false);
  const echoRef = useRef<AvatarPlayback | null>(null);
  const echoOnRef = useRef(false);
  const echoSegsRef = useRef<Set<number>>(new Set());
  const localLiveRef = useRef<Set<number>>(new Set());
  const avatarRoomRef = useRef<AvatarRoom | null>(null);
  const failVideo = () => {
    dropEchoRef.current();
    wantedRef.current = false;
    setAvatarWanted(false);
    setAvatarError("Video stopped. Xena's voice carries on.");
    selectRef.current(null);
  };
  const avatar = useAvatarTransport({
    onEvent: (eventType, props) => {
      const playback = echoRef.current;
      if (playback instanceof AvatarEcho) playback.onTavus(eventType, props);
      else if (playback instanceof HeygenPlayback && props) playback.onEvent(props);
    },
    // Video is live: Xena's next segment goes to her face.
    onLive: () => {
      const room = avatarRoomRef.current;
      if (!echoRef.current && room && room.request_id === requestRef.current && wantedRef.current) {
        if (switchTimerRef.current) clearTimeout(switchTimerRef.current);
        switchingRef.current = false;
        setAvatarSwitching(false);
        captureNodeRef.current?.port.postMessage({ type: "mute", muted: mutedRef.current });
        sendRef.current({ type: "avatar.playing", request_id: room.request_id });
        echoRef.current = room.provider === "tavus"
          ? new AvatarEcho({ send: avatarRef.current.send, conversationId: room.conversation_id })
          : new HeygenPlayback({ send: avatarRef.current.send, fail: failVideo });
      }
    },
    onFailed: failVideo,
  });
  const avatarRef = useRef(avatar);
  const dropEchoRef = useRef<() => void>(() => undefined);
  const sendRef = useRef<(msg: ClientMessage) => void>(() => undefined);
  useEffect(() => {
    avatarRef.current = avatar;
  });

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
          conversationRef.current = msg.conversation_id;
          try { sessionStorage.setItem("xana.voice.conversation", msg.conversation_id); } catch { /* storage unavailable */ }
          setReady(msg);
          break;
        case "state":
          setState(msg.state);
          stateRef.current = msg.state;
          if (msg.state === "hearing") setToolLabel(null);
          break;
        case "user.partial":
          setUserText(msg.text);
          setUserFinal(false);
          break;
        case "user.final": {
          // A new exchange (she was listening, not mid-answer, which is a corrected
          // transcript): the one before it goes into the history as it was heard.
          const prev = turnRef.current;
          const said = captionFor(segmentsRef.current);
          const fresh = stateRef.current === "listening" || stateRef.current === "hearing";
          if (fresh && (prev.user || said || prev.cards.length)) {
            const done: VoiceTurn = { id: ++turnIdRef.current, user: prev.user, xena: said, cards: prev.cards, citations: prev.citations };
            setHistory((h) => [...h.slice(-49), done]);
          }
          turnRef.current = fresh ? { user: msg.text, cards: [], citations: [] } : { ...prev, user: msg.text };
          if (fresh) setTurnCards([]);
          setUserText(msg.text);
          setUserFinal(true);
          // A new question: the previous answer's captions and cards give way.
          setSegments([]);
          setToolLabel(null);
          if (fresh) setSteps([]);
          setCitations([]);
          setConfirmDecision(null);
          setMetrics(null);
          break;
        }
        case "segment.start":
          generationsRef.current.set(msg.segment, msg.generation ?? 0);
          if ((msg.generation ?? 0) < requestRef.current) {
            droppedRef.current.add(msg.segment);
            break;
          }
          // Audio moves to Xena's face (or back) only when nothing is playing locally.
          if (localLiveRef.current.size === 0) echoOnRef.current = echoRef.current !== null;
          if (echoOnRef.current && echoRef.current) {
            echoRef.current.segmentStart(msg.segment, msg.kind);
            echoSegsRef.current.add(msg.segment);
          }
          setSegments((segs) => [
            ...segs,
            { segment: msg.segment, text: msg.text, words: [], playedMs: 0, done: false },
          ]);
          // Her answer is starting: the work behind it is done (a filler isn't the answer).
          if (msg.kind !== "filler") setSteps(allDone);
          break;
        case "segment.unspoken":
          // No voice for it (the speech engine failed): show its words anyway.
          setSegments((segs) => segs.map((s) => (s.segment === msg.segment ? { ...s, done: true } : s)));
          break;
        case "suggestions":
          setSuggestions(msg.items.slice(0, 4));
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
          if (echoSegsRef.current.has(msg.segment)) echoRef.current?.segmentEnd(msg.segment);
          else playNodeRef.current?.port.postMessage({ type: "end", segment: msg.segment });
          break;
        case "drop":
          for (const s of msg.segments) {
            droppedRef.current.add(s);
            localLiveRef.current.delete(s);
          }
          playNodeRef.current?.port.postMessage({ type: "drop", segments: msg.segments });
          echoRef.current?.drop(msg.segments.filter((s) => echoSegsRef.current.has(s)));
          // Keep what was actually heard; the rest was never said.
          setSegments((segs) =>
            segs
              .map((s) => (msg.segments.includes(s.segment) ? { ...s, text: "", words: [], done: true } : s))
              .filter((s) => s.text !== "" || !msg.segments.includes(s.segment)),
          );
          break;
        case "tool":
          setToolLabel(msg.label);
          setSteps((s) => addStep(s, msg.label));
          break;
        case "card":
          setCards((cs) => [...cs.slice(-5), msg.card]);
          turnRef.current = { ...turnRef.current, cards: [...turnRef.current.cards, msg.card] };
          setTurnCards(turnRef.current.cards);
          break;
        case "quote":
          setQuote(msg.quote);
          setReadbackInterrupted(false);
          setConfirmDecision(null);
          break;
        case "citations":
          setCitations(msg.citations);
          turnRef.current = { ...turnRef.current, citations: msg.citations };
          break;
        case "confirm.result":
          if ((msg.generation ?? 0) !== requestRef.current) break;
          setConfirmDecision(msg.decision);
          break;
        case "turn.done":
          echoRef.current?.turnDone();
          setMetrics(msg.metrics);
          setToolLabel(null);
          setSteps(allDone);
          break;
        case "error":
          setError(msg.message);
          if (msg.fatal) setState("error");
          break;
        case "avatar":
          if (msg.request_id !== requestRef.current || !wantedRef.current) break;
          avatarRoomRef.current = msg;
          setLook(msg.look);
          setGreenscreen(msg.greenscreen);
          void avatarRef.current.join(msg);
          break;
        case "avatar.unavailable":
          if (msg.request_id !== requestRef.current) break;
          if (switchTimerRef.current) clearTimeout(switchTimerRef.current);
          switchingRef.current = false;
          setAvatarSwitching(false);
          captureNodeRef.current?.port.postMessage({ type: "mute", muted: mutedRef.current });
          wantedRef.current = false;
          setAvatarWanted(false);
          setAvatarError(
            msg.reason === "cleanup_pending" ? "The previous video is still closing. Try Video again shortly."
              : msg.reason === "busy" ? "Video is busy right now. Voice works as usual." : "Video isn't available right now.",
          );
          break;
      }
    },
    [],
  );

  const stop = useCallback(() => {
    stoppedRef.current = true;
    if (switchTimerRef.current) clearTimeout(switchTimerRef.current);
    switchingRef.current = false;
    setAvatarSwitching(false);
    wantedRef.current = false;
    echoRef.current = null;
    echoOnRef.current = false;
    echoSegsRef.current.clear();
    localLiveRef.current.clear();
    setAvatarWanted(false);
    void avatarRef.current.leave();
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
    if (!conversationRef.current) {
      try { conversationRef.current = sessionStorage.getItem("xana.voice.conversation"); } catch { /* storage unavailable */ }
    }
    requestRef.current = 0;
    generationsRef.current.clear();
    droppedRef.current.clear();
    setReady(null);
    setSegments([]);
    setSteps([]);
    setSuggestions([]);
    setMutedState(false);
    mutedRef.current = false;
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
          localLiveRef.current.delete(m.segment);
          updateSegment(m.segment, { playedMs: m.playedMs, done: true });
          if (!droppedRef.current.has(m.segment)) {
            send({ type: "played", segment: m.segment, complete: true, played_ms: m.playedMs,
              generation: generationsRef.current.get(m.segment) ?? 0 });
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
            conversation_id: conversationRef.current ?? null,
            mic_rate: MIC_RATE,
            speech_rate: SPEECH_RATE,
          } satisfies ClientMessage),
        );
      ws.onmessage = (e: MessageEvent) => {
        if (wsRef.current !== ws || stoppedRef.current) return;
        if (typeof e.data === "string") {
          const msg = parseServerMessage(e.data);
          if (msg) onServer(msg);
          return;
        }
        const frame = splitAudioFrame(e.data as ArrayBuffer);
        if (!frame || droppedRef.current.has(frame.segment)) return;
        if (echoSegsRef.current.has(frame.segment) && echoRef.current) {
          echoRef.current.audio(frame.segment, frame.pcm.slice());
          return;
        }
        localLiveRef.current.add(frame.segment);
        const pcm = frame.pcm.slice();
        player.port.postMessage({ type: "audio", segment: frame.segment, pcm: pcm.buffer }, [pcm.buffer]);
      };
      ws.onclose = (e) => {
        if (stoppedRef.current) return;
        setError(
          e.code === 4401
            ? "Your session has ended. Sign in again to talk to Xena."
            : "The connection to Xena dropped. Tap the orb to reconnect.",
        );
        stop();
      };
      ws.onerror = () => setError("Couldn't reach Xena's voice service.");
      await playCtx.resume();
    } catch (err) {
      const denied = err instanceof DOMException && (err.name === "NotAllowedError" || err.name === "SecurityError");
      setError(
        denied
          ? "Xena needs your microphone. Allow it in your browser's site settings, then try again."
          : "Couldn't start voice on this device.",
      );
      stop();
      setState("error");
    }
  }, [onServer, send, stop, updateSegment]);

  const setMuted = useCallback(
    (next: boolean) => {
      setMutedState(next);
      mutedRef.current = next;
      captureNodeRef.current?.port.postMessage({ type: "mute", muted: next || switchingRef.current });
      send({ type: "mute", muted: next });
    },
    [send],
  );

  /** Stop sending speech to Xena's face. Anything it was still saying is cut off, so the
   *  voice agent is told, as if the customer had talked over her, and goes back to listening. */
  const dropEcho = useCallback(() => {
    const echo = echoRef.current;
    echoRef.current = null;
    echoOnRef.current = false;
    if (echo && !echo.idle) send({ type: "interrupt" });
    echoSegsRef.current.clear();
    avatarRoomRef.current = null;
  }, [send]);

  const selectAvatar = useCallback((next: AvatarProvider | null, selectedLook?: string) => {
    if (switchTimerRef.current) clearTimeout(switchTimerRef.current);
    switchingRef.current = next !== null;
    setAvatarSwitching(next !== null);
    captureNodeRef.current?.port.postMessage({ type: "mute", muted: mutedRef.current || next !== null });
    if (next !== null) switchTimerRef.current = setTimeout(() => {
      wantedRef.current = false;
      setAvatarWanted(false);
      setAvatarError("Video took too long to connect. Xena's voice carries on.");
      selectRef.current(null);
    }, 45_000);
    setReadbackInterrupted(true);
    setConfirmDecision(null);
    dropEcho();
    const local = [...localLiveRef.current];
    for (const segment of local) droppedRef.current.add(segment);
    playNodeRef.current?.port.postMessage({ type: "drop", segments: local });
    localLiveRef.current.clear();
    void avatarRef.current.leave();
    send({ type: "avatar.select", provider: next, request_id: ++requestRef.current, look: selectedLook });
  }, [dropEcho, send]);

  useEffect(() => {
    dropEchoRef.current = dropEcho;
    sendRef.current = send;
    selectRef.current = selectAvatar;
  }, [dropEcho, send, selectAvatar]);

  useEffect(() => {
    if (providerRef.current === provider) return;
    providerRef.current = provider;
    setAvatarError(null);
    if (wantedRef.current) selectAvatar(provider);
  }, [provider, selectAvatar]);

  const setVideo = useCallback(
    (on: boolean) => {
      setAvatarError(null);
      setAvatarWanted(on);
      wantedRef.current = on;
      if (on) {
        const prefs = loadPrefs();
        const offer = ready?.avatars?.[providerRef.current] ?? ready?.avatar;
        const offered = offer?.available ? (offer.looks ?? []) : [];
        const pick = offered.some((l) => l.key === prefs.look) ? prefs.look : undefined;
        if (prefs.background) setBackgroundKey(backgroundFor(prefs.background).key);
        selectAvatar(providerRef.current, pick);
        return;
      }
      selectAvatar(null);
    },
    [selectAvatar, ready],
  );

  /** A new face: a new video room (a few seconds). Whatever she was saying is cut off. */
  const chooseLook = useCallback(
    (key: string) => {
      setLook(key);
      savePrefs({ ...loadPrefs(), look: key });
      if (!avatarWanted) return;
      selectAvatar(providerRef.current, key);
    },
    [avatarWanted, selectAvatar],
  );

  /** A new background: drawn in the browser, so it changes at once. */
  const chooseBackground = useCallback((key: string) => {
    const bg = backgroundFor(key);
    setBackgroundKey(bg.key);
    savePrefs({ ...loadPrefs(), background: bg.key });
  }, []);

  // What the customer has heard through the face: captions, and segments played in full.
  useEffect(() => {
    if (avatar.status !== "live") return;
    const id = setInterval(() => {
      const echo = echoRef.current;
      if (!echo) return;
      for (const c of echo.tick()) {
        echoSegsRef.current.delete(c.segment);
        if (droppedRef.current.has(c.segment)) continue;
        updateSegment(c.segment, { playedMs: c.playedMs, done: true });
        send({ type: "played", segment: c.segment, complete: true, played_ms: c.playedMs,
          generation: generationsRef.current.get(c.segment) ?? 0 });
      }
      for (const n of echoSegsRef.current) updateSegment(n, { playedMs: echo.playedMs(n) });
    }, 50);
    return () => clearInterval(id);
  }, [avatar.status, send, updateSegment]);

  const interrupt = useCallback(() => send({ type: "interrupt" }), [send]);
  const sendText = useCallback((text: string) => send({ type: "text", text }), [send]);
  const ask = useCallback(
    (text: string) => {
      if (stateRef.current === "speaking") send({ type: "interrupt" });
      send({ type: "text", text });
    },
    [send],
  );
  const quoteOutcome = useCallback(
    (quoteId: string, outcome: "confirmed" | "declined") => {
      setQuote(null);
      send({ type: "quote.outcome", quote_id: quoteId, outcome });
    },
    [send],
  );

  useEffect(() => stop, [stop]);
  const offer = ready?.avatars?.[provider] ?? (provider === "tavus" ? ready?.avatar : undefined) ?? { available: false };

  return {
    state,
    history,
    turnCards,
    ready,
    userText,
    userFinal,
    segments,
    toolLabel,
    steps,
    suggestions,
    quote,
    quoteButtonOnly: readbackInterrupted || (avatarWanted && provider === "heygen"),
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
    ask,
    quoteOutcome,
    avatar: {
      provider,
      switching: avatarSwitching,
      offer,
      wanted: avatarWanted,
      status: avatarWanted && avatar.status === "off" ? "starting" : avatar.status,
      stream: avatar.stream,
      error: avatarError,
      looks: offer.available ? (offer.looks ?? []) : [],
      look,
      background: backgroundFor(backgroundKey),
      greenscreen,
      playbackStarted: avatar.playbackStarted,
      playbackStopped: avatar.playbackStopped,
    },
    setVideo,
    chooseLook,
    chooseBackground,
  };
}
