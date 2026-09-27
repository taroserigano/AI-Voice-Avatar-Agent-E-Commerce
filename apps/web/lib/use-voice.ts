"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AssistantHttpError, speak as fetchSpeech, transcribe } from "./assistant-client";
import type { AgentName, VoiceConfig } from "./assistant-types";

/**
 * Turn-based voice in the browser (no LiveKit yet): listen for one utterance, detect when the
 * customer stops talking, turn it into text, and play the assistant's answer, stopping at once
 * if the customer talks over it.
 *
 * - Speech-to-text runs on the server when a provider is configured (the clip is uploaded and not
 *   stored), otherwise with the browser's own recognizer.
 * - Text-to-speech: the server's voice when configured, otherwise the browser's.
 * - `simulate(text)` feeds a typed "utterance" through the same path (no microphone needed).
 */

export type VoiceState =
  | "off"
  | "requesting"
  | "listening"
  | "hearing"
  | "transcribing"
  | "waiting"
  | "speaking"
  | "error";

export type Utterance = { text: string; final: boolean; speechMs: number; simulated: boolean };

type Options = {
  agent: AgentName;
  config: VoiceConfig | null;
  onUtterance: (u: Utterance) => void;
  maxSeconds?: number;
};

// Energy-based voice activity detection, tuned for a laptop mic in a quiet room.
const FRAME_MS = 50;
const START_MS = 150; // this much speech starts an utterance
const END_SILENCE_MS = 900; // this much quiet after speech ends it
const MIN_RMS = 0.015;

type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((e: { results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }> }) => void) | null;
  onend: (() => void) | null;
  onerror: ((e: { error: string }) => void) | null;
};

function browserRecognizer(): SpeechRecognitionLike | null {
  const w = window as unknown as { SpeechRecognition?: new () => SpeechRecognitionLike; webkitSpeechRecognition?: new () => SpeechRecognitionLike };
  const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition;
  return Ctor ? new Ctor() : null;
}

export function useVoice({ agent, config, onUtterance, maxSeconds = 30 }: Options) {
  const [state, setState] = useState<VoiceState>("off");
  const [error, setError] = useState<string | null>(null);
  const [partial, setPartial] = useState("");
  const [level, setLevel] = useState(0);
  const [handsFree, setHandsFree] = useState(true);
  // Captions only: the assistant's answers aren't played aloud (and count as fully "heard").
  const [muted, setMuted] = useState(false);
  const mutedRef = useRef(false);
  useEffect(() => {
    mutedRef.current = muted;
  }, [muted]);

  const streamRef = useRef<MediaStream | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const playbackRef = useRef<{ resolve: (completed: boolean) => void } | null>(null);
  const recognizerRef = useRef<SpeechRecognitionLike | null>(null);
  const stateRef = useRef<VoiceState>("off");
  // Hands-free mode listens again after a quiet turn; `listen` calls itself through this ref.
  const listenRef = useRef<(() => Promise<void>) | null>(null);
  const onUtteranceRef = useRef(onUtterance);
  useEffect(() => {
    onUtteranceRef.current = onUtterance;
  }, [onUtterance]);

  const set = (s: VoiceState) => {
    stateRef.current = s;
    setState(s);
  };

  const stopTimer = () => {
    if (timerRef.current !== null) window.clearInterval(timerRef.current);
    timerRef.current = null;
  };

  /** Stop any playback now (barge-in or Stop). Resolves the pending playback as interrupted. */
  const stopSpeaking = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
      audioRef.current = null;
    }
    if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
    playbackRef.current?.resolve(false);
    playbackRef.current = null;
  }, []);

  const release = useCallback(() => {
    stopTimer();
    recognizerRef.current?.abort();
    recognizerRef.current = null;
    if (recorderRef.current && recorderRef.current.state !== "inactive") recorderRef.current.stop();
    recorderRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    void ctxRef.current?.close();
    ctxRef.current = null;
    analyserRef.current = null;
    setLevel(0);
  }, []);

  useEffect(() => () => {
    stopSpeaking();
    release();
  }, [release, stopSpeaking]);

  const ensureMic = useCallback(async (): Promise<boolean> => {
    if (streamRef.current) return true;
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("This browser can't use a microphone here. You can type instead.");
      set("error");
      return false;
    }
    set("requesting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      streamRef.current = stream;
      const ctx = new AudioContext();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 1024;
      ctx.createMediaStreamSource(stream).connect(analyser);
      ctxRef.current = ctx;
      analyserRef.current = analyser;
      return true;
    } catch {
      setError("Microphone access was blocked. Allow it in your browser, or type instead.");
      set("error");
      return false;
    }
  }, []);

  const rms = () => {
    const analyser = analyserRef.current;
    if (!analyser) return 0;
    const data = new Float32Array(analyser.fftSize);
    analyser.getFloatTimeDomainData(data);
    let sum = 0;
    for (const v of data) sum += v * v;
    return Math.sqrt(sum / data.length);
  };

  /** Listen for one utterance, then hand it (as text) to onUtterance. */
  const listen = useCallback(async () => {
    setError(null);
    setPartial("");
    if (!(await ensureMic())) return;

    // Browser recognizer: no upload; it gives text directly.
    if (config?.stt === "browser") {
      const rec = browserRecognizer();
      if (!rec) {
        setError("Voice isn't available in this browser. You can type instead.");
        set("error");
        return;
      }
      recognizerRef.current = rec;
      rec.lang = "en-US";
      rec.interimResults = true;
      rec.continuous = false;
      const started = performance.now();
      let finalText = "";
      rec.onresult = (e) => {
        let interim = "";
        for (let i = 0; i < e.results.length; i++) {
          const r = e.results[i]!;
          if (r.isFinal) finalText += r[0].transcript;
          else interim += r[0].transcript;
        }
        setPartial(finalText || interim);
        if (stateRef.current === "listening") set("hearing");
      };
      rec.onerror = (e) => {
        if (e.error !== "no-speech" && e.error !== "aborted") setError("I couldn't hear that. Try again, or type.");
      };
      rec.onend = () => {
        recognizerRef.current = null;
        const text = finalText.trim();
        if (text) {
          set("waiting");
          onUtteranceRef.current({ text, final: true, speechMs: Math.round(performance.now() - started), simulated: false });
        } else {
          set(handsFree ? "listening" : "off");
          if (handsFree) void listenRef.current?.();
        }
      };
      set("listening");
      rec.start();
      return;
    }

    // Server speech-to-text: record, detect the end of speech, upload the clip.
    const stream = streamRef.current!;
    const mime = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"].find((m) =>
      MediaRecorder.isTypeSupported(m),
    );
    const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    recorderRef.current = recorder;
    chunksRef.current = [];
    recorder.ondataavailable = (e) => {
      if (e.data.size) chunksRef.current.push(e.data);
    };
    let speechMs = 0;
    let silenceMs = 0;
    let heard = false;
    let noise = MIN_RMS;
    let elapsed = 0;
    recorder.onstop = async () => {
      stopTimer();
      recorderRef.current = null;
      if (!heard) {
        set("off");
        return;
      }
      set("transcribing");
      const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
      try {
        const result = await transcribe(blob);
        if (!result.text.trim()) {
          setError("I didn't catch that. Try again, or type.");
          set("off");
          return;
        }
        set("waiting");
        onUtteranceRef.current({ text: result.text, final: true, speechMs, simulated: false });
      } catch (err) {
        setError(
          err instanceof AssistantHttpError && err.status === 503
            ? "Speech-to-text isn't set up on the server. You can type instead."
            : "I couldn't understand that recording. Try again, or type.",
        );
        set("error");
      }
    };
    recorder.start(250);
    set("listening");
    timerRef.current = window.setInterval(() => {
      const r = rms();
      setLevel(Math.min(1, r * 8));
      elapsed += FRAME_MS;
      const threshold = Math.max(MIN_RMS, noise * 3);
      if (r > threshold) {
        speechMs += FRAME_MS;
        silenceMs = 0;
        if (!heard && speechMs >= START_MS) {
          heard = true;
          set("hearing");
        }
      } else {
        if (!heard) noise = noise * 0.95 + r * 0.05; // learn the room's noise floor
        if (heard) silenceMs += FRAME_MS;
      }
      const tooLong = elapsed >= maxSeconds * 1000;
      const quietTooLong = !heard && elapsed >= 12_000;
      if ((heard && silenceMs >= END_SILENCE_MS) || tooLong || quietTooLong) {
        stopTimer();
        if (recorder.state !== "inactive") recorder.stop();
      }
    }, FRAME_MS);
  }, [config?.stt, ensureMic, handsFree, maxSeconds]);

  useEffect(() => {
    listenRef.current = listen;
  }, [listen]);

  /**
   * Say `text` in the assistant's voice. Resolves true if it played to the end, false if it was
   * interrupted (by the customer talking, or Stop). While playing, talking over it stops it.
   */
  const say = useCallback(
    async (text: string): Promise<boolean> => {
      stopSpeaking();
      if (!text.trim() || mutedRef.current) {
        if (stateRef.current === "waiting") set("off");
        return true;
      }
      set("speaking");
      const done = new Promise<boolean>((resolve) => {
        playbackRef.current = { resolve };
      });
      // Barge-in: watch the mic while speaking; a clear burst of speech stops playback.
      let bargeMs = 0;
      const watch = streamRef.current
        ? window.setInterval(() => {
            if (rms() > 0.05) bargeMs += FRAME_MS;
            else bargeMs = 0;
            if (bargeMs >= 200) stopSpeaking();
          }, FRAME_MS)
        : null;
      try {
        if (config?.tts === "cartesia") {
          const blob = await fetchSpeech(text, agent);
          if (!playbackRef.current) return false; // stopped while loading
          const audio = new Audio(URL.createObjectURL(blob));
          audioRef.current = audio;
          audio.onended = () => {
            playbackRef.current?.resolve(true);
            playbackRef.current = null;
          };
          audio.onerror = () => {
            playbackRef.current?.resolve(false);
            playbackRef.current = null;
          };
          await audio.play();
        } else if ("speechSynthesis" in window) {
          const u = new SpeechSynthesisUtterance(text);
          u.lang = "en-US";
          u.rate = 1.02;
          u.onend = () => {
            playbackRef.current?.resolve(true);
            playbackRef.current = null;
          };
          window.speechSynthesis.speak(u);
        } else {
          playbackRef.current?.resolve(true);
        }
        const completed = await done;
        return completed;
      } catch {
        playbackRef.current?.resolve(false);
        playbackRef.current = null;
        return false;
      } finally {
        if (watch !== null) window.clearInterval(watch);
        if (stateRef.current === "speaking") set("off");
      }
    },
    [agent, config?.tts, stopSpeaking],
  );

  /** Stop listening and speaking; release the microphone. */
  const stop = useCallback(() => {
    stopSpeaking();
    release();
    set("off");
  }, [release, stopSpeaking]);

  /** A typed "utterance" through the same path as speech (simulated voice, no microphone). */
  const simulate = useCallback((text: string) => {
    if (!text.trim()) return;
    set("waiting");
    onUtteranceRef.current({ text: text.trim(), final: true, speechMs: Math.max(400, text.length * 60), simulated: true });
  }, []);

  return {
    state,
    error,
    partial,
    level,
    handsFree,
    setHandsFree,
    muted,
    setMuted,
    listen,
    say,
    stop,
    stopSpeaking,
    simulate,
    setState: set,
  };
}

export type VoiceController = ReturnType<typeof useVoice>;
