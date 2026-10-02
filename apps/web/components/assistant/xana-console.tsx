"use client";

import { ChevronDownIcon, MicIcon, PlusIcon, XIcon } from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import { browserApi } from "@/lib/api-browser";
import { confirmCheck, getVoiceConfig } from "@/lib/assistant-client";
import { plainAnswer } from "@/lib/assistant-text";
import type { VoiceConfig } from "@/lib/assistant-types";
import { cn } from "@/lib/cn";
import { useDebugView, useSimulatedVoice } from "@/lib/dev-flags";
import { orderNumber } from "@/lib/orders";
import { confirmQuote } from "@/lib/returns-confirm";
import { type AnswerDone, useAssistant } from "@/lib/use-assistant";
import { type Utterance, useVoice } from "@/lib/use-voice";
import { useCallback, useEffect, useRef, useState } from "react";
import { AssistantAvatar } from "./assistant-avatar";
import { ChatThread, type Persona } from "./chat-thread";

const XANA: Persona = {
  name: "Xena",
  role: "AI customer-support assistant",
  avatar: <AssistantAvatar who="xana" />,
  greeting:
    "Hi, I'm Xena, Serigan Mart's customer-support assistant, and I'm happy you're here! I can answer product questions, help with orders, and handle returns and refunds. Talk to me with the microphone, or type.",
  suggestions: [
    "Find me sugar free yogurt",
    "I want to return my earbuds",
    "The milk I got went bad",
    "Where's my refund?",
    "How long do I have to return something?",
    "I'd like to talk to a person",
  ],
  placeholder: "Type a message to Xena…",
};

const STATE_LABEL: Record<string, string> = {
  off: "Tap the microphone to talk",
  requesting: "Allow the microphone to talk",
  listening: "Listening…",
  hearing: "Listening…",
  transcribing: "Got it…",
  waiting: "Thinking…",
  speaking: "Speaking… talk anytime to interrupt",
  error: "Voice unavailable",
};

const PROVIDER_LABEL: Record<string, string> = {
  deepgram: "Deepgram",
  groq: "Whisper (Groq)",
  browser: "your browser",
  cartesia: "Cartesia",
};

type Caption = { who: "you" | "xana"; text: string };

export function XanaConsole({
  initialOrder,
  initialLine,
  initialMessage,
  simulator,
}: {
  initialOrder?: string;
  initialLine?: string;
  /** Sent once on arrival, e.g. continuing a support request (built on the server). */
  initialMessage?: string;
  simulator: boolean;
}) {
  const [config, setConfig] = useState<VoiceConfig | null>(null);
  const [voiceOn, setVoiceOn] = useState(false);
  const [captions, setCaptions] = useState<Caption[]>([]);
  const [simText, setSimText] = useState("");
  const debugView = useDebugView();
  const simulatedVoice = useSimulatedVoice();
  const voiceOnRef = useRef(false);
  // The read-back for the waiting quote, and whether it played all the way through.
  const readbackRef = useRef<{ quoteId: string; complete: boolean } | null>(null);
  const caption = (c: Caption) => setCaptions((all) => [...all.slice(-5), c]);

  const voiceRef = useRef<ReturnType<typeof useVoice> | null>(null);

  const onAnswer = useCallback(async ({ text, quote }: AnswerDone) => {
    const voice = voiceRef.current;
    if (!voice || !voiceOnRef.current) return;
    const spoken = plainAnswer(text);
    if (spoken) caption({ who: "xana", text: spoken });
    let completed = spoken ? await voice.say(spoken) : true;
    if (quote) {
      caption({ who: "xana", text: quote.readback });
      completed = completed && (await voice.say(quote.readback));
      readbackRef.current = { quoteId: quote.quote_id, complete: completed };
    } else {
      readbackRef.current = null;
    }
    // Listen again (right away if the customer talked over the answer).
    if (voiceOnRef.current && (voice.handsFree || !completed)) void voice.listen();
  }, []);

  const chat = useAssistant("xana", { onAnswer });
  const chatRef = useRef(chat);
  useEffect(() => {
    chatRef.current = chat;
  }, [chat]);

  const onUtterance = useCallback(async (u: Utterance) => {
    const voice = voiceRef.current;
    const current = chatRef.current;
    caption({ who: "you", text: u.text });
    const pending = current.pendingQuote;
    const readback = readbackRef.current;
    if (pending && current.conversationId && readback?.quoteId === pending.quote_id) {
      // The app decides whether this was a clear yes to the read-back, never the model.
      const check = await confirmCheck({
        text: u.text,
        final: u.final,
        readback_complete: readback.complete,
        speech_ms: u.speechMs,
        conversation_id: current.conversationId,
        quote_id: pending.quote_id,
      });
      caption({ who: "xana", text: check.say });
      await voice?.say(check.say);
      if (check.decision === "yes") {
        const result = await confirmQuote(pending.quote_id);
        readbackRef.current = null;
        if (result.ok) await current.resume(pending.quote_id, "confirmed", { voice: true });
        else {
          const sorry = "I couldn't confirm it just now. Please tap Confirm return on the screen.";
          caption({ who: "xana", text: sorry });
          await voice?.say(sorry);
        }
      } else if (check.decision === "no") {
        readbackRef.current = null;
        await current.resume(pending.quote_id, "declined", { voice: true });
      } else if (voiceOnRef.current) {
        void voice?.listen();
      }
      return;
    }
    await current.send(u.text, { voice: true });
  }, []);

  const voice = useVoice({ agent: "xana", config, onUtterance, maxSeconds: config?.max_seconds ?? 30 });
  useEffect(() => {
    voiceRef.current = voice;
  }, [voice]);

  const { load } = chat;
  useEffect(() => {
    void load();
    getVoiceConfig().then(setConfig, () => setConfig(null));
  }, [load]);

  // Arriving from an order's "Start a return": ask about that item. Or, from a support request's
  // "Continue with Xena": say that you're following up on it.
  const startedRef = useRef(false);
  useEffect(() => {
    if (!chat.loaded || startedRef.current || (!initialOrder && !initialMessage)) return;
    startedRef.current = true;
    if (!initialOrder) {
      // Drop ?case= so a reload doesn't send the follow-up again.
      window.history.replaceState(null, "", window.location.pathname);
      if (initialMessage) void chat.send(initialMessage);
      return;
    }
    void (async () => {
      const result = await browserApi.GET("/v1/orders/{order_id}", { params: { path: { order_id: initialOrder } } });
      const line = result.data?.lines.find((l) => l.id === initialLine) ?? result.data?.lines[0];
      if (result.data && line) {
        await chat.send(`I want to return the ${line.product_title} from order ${orderNumber(result.data.id)}`);
      }
    })();
  }, [chat, chat.loaded, initialLine, initialMessage, initialOrder]);

  const startVoice = () => {
    voiceOnRef.current = true;
    setVoiceOn(true);
    void voice.listen();
  };
  const endVoice = () => {
    voiceOnRef.current = false;
    setVoiceOn(false);
    voice.stop();
  };
  // The big button: start talking; while Xena speaks, interrupt her; otherwise listen again.
  const mainAction = () => {
    if (!voiceOn) return startVoice();
    if (voice.state === "speaking") {
      voice.stopSpeaking();
      void voice.listen();
      return;
    }
    if (voice.state === "off" || voice.state === "error") void voice.listen();
  };
  const captionsRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = captionsRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [captions, voice.partial]);

  const state = voiceOn ? voice.state : "off";
  const listening = state === "listening" || state === "hearing";
  const busy = state === "transcribing" || state === "waiting" || state === "requesting";
  const ring = state === "hearing" ? 1 + voice.level * 0.35 : state === "speaking" ? 1.12 : 1;
  const mainLabel = !voiceOn
    ? "Talk with Xena"
    : state === "speaking"
      ? "Interrupt Xena"
      : listening
        ? "Listening"
        : busy
          ? "Working on it"
          : "Listen again";
  const showSimulator = simulator && (simulatedVoice || debugView);

  const micButton = (
    <button
      type="button"
      onClick={voiceOn ? endVoice : startVoice}
      aria-pressed={voiceOn}
      aria-label={voiceOn ? "End voice conversation" : "Talk with Xena by voice"}
      title={voiceOn ? "End voice" : "Talk by voice"}
      className={cn(
        "inline-flex size-10 items-center justify-center rounded-full transition-colors",
        voiceOn ? "bg-accent-400 text-ink" : "text-ink-soft hover:bg-neutral-100 hover:text-brand-700",
      )}
    >
      <MicIcon className="size-5" />
    </button>
  );

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,25rem)_minmax(0,1fr)]">
      <section
        aria-labelledby="xana-title"
        className="relative isolate order-2 flex flex-col items-center overflow-hidden rounded-3xl bg-inverse px-6 pb-6 pt-8 text-center text-white focus-inverse lg:sticky lg:top-36 lg:order-1 lg:self-start"
      >
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(60%_50%_at_50%_0%,rgb(255_180_57/0.28),transparent_70%)]"
        />
        <div className="relative">
          <span
            aria-hidden="true"
            className={cn(
              "absolute inset-0 rounded-full bg-accent-300/30 transition-transform duration-150 motion-reduce:transition-none",
              voiceOn && state !== "error" ? "opacity-100" : "opacity-0",
              listening && "motion-safe:animate-pulse",
            )}
            style={{ transform: `scale(${voiceOn ? ring * 1.35 : 1})` }}
          />
          <AssistantAvatar who="xana" size="xl" className="relative ring-4 ring-white/20" />
        </div>
        <h2 id="xana-title" className="mt-4 font-display text-3xl font-semibold">
          Xena
        </h2>
        <p className="text-sm text-brand-200">Customer support · AI assistant</p>

        <p role="status" aria-live="polite" className="mt-5 min-h-6 text-sm font-medium text-white">
          {STATE_LABEL[state]}
        </p>

        <button
          type="button"
          onClick={mainAction}
          disabled={busy}
          aria-label={mainLabel}
          className={cn(
            "mt-3 inline-flex size-20 items-center justify-center rounded-full bg-accent-400 text-ink shadow-lg transition-colors hover:bg-accent-300 focus-visible:outline-white disabled:opacity-80",
            listening && "ring-4 ring-accent-300/60",
          )}
        >
          {busy ? (
            <svg aria-hidden="true" viewBox="0 0 24 24" className="size-8 animate-spin motion-reduce:animate-none" fill="none">
              <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.25" strokeWidth="3" />
              <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
            </svg>
          ) : state === "speaking" ? (
            <svg aria-hidden="true" viewBox="0 0 24 24" className="size-8" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round">
              <path d="M4 10.5v3M8 7.5v9M12 4.5v15M16 7.5v9M20 10.5v3" />
            </svg>
          ) : (
            <MicIcon className="size-8" />
          )}
        </button>
        {voiceOn ? (
          <button
            type="button"
            onClick={endVoice}
            className="mt-3 inline-flex min-h-11 items-center gap-1.5 rounded-full px-4 text-sm font-semibold text-brand-100 underline-offset-4 hover:text-white hover:underline"
          >
            <XIcon className="size-4" /> End voice
          </button>
        ) : null}

        <div className="mt-4 w-full space-y-2">
          <Switch checked={voice.handsFree} onChange={voice.setHandsFree} label="Hands-free" hint="Keep listening after each answer" />
          <Switch checked={voice.muted} onChange={voice.setMuted} label="Captions only" hint="Don't speak answers aloud" />
        </div>

        {voice.error ? (
          <p role="alert" className="mt-3 rounded-xl bg-white/10 px-3 py-2 text-sm text-white">
            {voice.error}
          </p>
        ) : null}

        {captions.length || voice.partial ? (
          <div
            ref={captionsRef}
            className="mt-5 max-h-56 w-full space-y-2 overflow-y-auto text-left [mask-image:linear-gradient(to_bottom,transparent,black_1.5rem)] pt-4"
            role="region"
            aria-label="Captions"
            tabIndex={0}
          >
            {captions.map((c, i) => (
              <p
                key={i}
                className={cn(
                  "rounded-xl px-3 py-2 text-sm",
                  c.who === "you" ? "ml-8 bg-brand-600/60 text-white" : "mr-8 bg-white/10 text-brand-50",
                )}
              >
                <span className="sr-only">{c.who === "you" ? "You said: " : "Xena said: "}</span>
                {c.text}
              </p>
            ))}
            {voice.partial && listening ? (
              <p className="ml-8 rounded-xl bg-white/10 px-3 py-2 text-sm italic text-brand-100">{voice.partial}</p>
            ) : null}
          </div>
        ) : (
          <div role="region" aria-label="Captions" className="sr-only" />
        )}

        {showSimulator ? (
          <form
            className="mt-5 w-full"
            onSubmit={(e) => {
              e.preventDefault();
              if (!voiceOn) {
                voiceOnRef.current = true;
                setVoiceOn(true);
              }
              // Simulated speech needs no microphone; answers show as captions.
              voice.setMuted(true);
              voice.setHandsFree(false);
              voice.simulate(simText);
              setSimText("");
            }}
          >
            <label htmlFor="sim-voice" className="block text-left text-xs font-semibold uppercase tracking-eyebrow text-brand-200">
              Simulated speech (development)
            </label>
            <div className="mt-1 flex gap-2">
              <input
                id="sim-voice"
                value={simText}
                onChange={(e) => setSimText(e.target.value)}
                placeholder="Type what you'd say"
                className="min-h-11 flex-1 rounded-full bg-white/10 px-4 text-sm text-white placeholder:text-brand-200 focus:outline-2 focus:outline-white"
              />
              <button type="submit" className="rounded-full bg-white/15 px-4 text-sm font-semibold hover:bg-white/25">
                Say
              </button>
            </div>
          </form>
        ) : null}

        <details className="group mt-6 w-full text-left text-xs text-brand-200 [&_summary::-webkit-details-marker]:hidden">
          <summary className="flex cursor-pointer list-none items-center justify-center gap-1 font-semibold text-brand-100">
            About voice and privacy
            <ChevronDownIcon className="size-3.5 transition-transform group-open:rotate-180" />
          </summary>
          <p className="mt-2 leading-relaxed">
            {config?.notice ??
              "Xena is an AI assistant. Speech is turned into text by our speech provider and isn't stored."}{" "}
            A return is only created after you confirm it, by button or a clear “yes” after Xena reads the
            quote back.
          </p>
          {config && debugView ? (
            <p className="mt-2">
              Speech: {PROVIDER_LABEL[config.stt]} · Voice: {PROVIDER_LABEL[config.tts]} · Decisions:{" "}
              {config.decision_model === "jev-simulator" ? "Jev simulator" : config.decision_model}
            </p>
          ) : null}
        </details>
      </section>

      {/* Sized to the conversation, up to a cap: a short one doesn't leave a tall empty transcript,
          a long one scrolls inside. */}
      <section
        aria-labelledby="conversation-title"
        className="order-1 flex max-h-[min(46rem,calc(100dvh-10rem))] min-h-80 flex-col overflow-hidden rounded-3xl bg-raised shadow-sm ring-1 ring-line [overflow-anchor:none] lg:order-2 lg:self-start"
      >
        <header className="flex items-center gap-3 border-b border-line px-4 py-3">
          <AssistantAvatar who="xana" />
          <div className="min-w-0 flex-1">
            <h2 id="conversation-title" className="font-semibold text-ink">
              Conversation with Xena
            </h2>
            <p className="flex flex-wrap items-center gap-1.5 text-xs text-muted">
              {/* Phones keep the header to two lines; the page intro already says this. */}
              <span className="max-sm:hidden">Returns, refunds, and orders</span>
              {chat.status?.simulated ? (
                <span title="Xena's AI model is offline in this demo, so answers come from simple rules and live store data.">
                  <Badge tone="accent">Simulated</Badge>
                </span>
              ) : null}
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              readbackRef.current = null;
              chat.reset();
              setCaptions([]);
            }}
            title="New conversation"
            className="inline-flex min-h-10 min-w-10 shrink-0 items-center justify-center gap-1.5 rounded-full text-sm font-medium text-ink-soft hover:bg-neutral-100 sm:px-3"
          >
            <PlusIcon className="size-5 sm:size-4" />
            {/* Icon-only on phones; the text stays as the button's name. */}
            <span className="max-sm:sr-only">New conversation</span>
          </button>
        </header>
        {/* Messages sit at the bottom of the transcript, newest right above the composer, like a
            chat app. Only the transcript scrolls (ChatThread sets its scrollTop); the page stays
            where it is, so the reply to what you just sent is always next to where you typed.
            overflow-anchor:none on the section stops the browser's scroll anchoring from moving
            the page to follow a message as it slides up the transcript. */}
        <ChatThread
          persona={XANA}
          chat={chat}
          voiceSlot={micButton}
          className="[&>div:first-child]:flex [&>div:first-child]:flex-col [&>div:first-child>:first-child]:mt-auto"
        />
      </section>
    </div>
  );
}

function Switch({
  checked,
  onChange,
  label,
  hint,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  label: string;
  hint: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm hover:bg-white/5"
    >
      <span
        aria-hidden="true"
        className={cn(
          "relative inline-flex h-6 w-10 shrink-0 rounded-full transition-colors",
          checked ? "bg-accent-400" : "bg-white/25",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 size-5 rounded-full bg-white shadow transition-transform",
            checked ? "translate-x-4.5" : "translate-x-0.5",
          )}
        />
      </span>
      <span>
        <span className="block font-medium text-white">{label}</span>
        <span className="block text-xs text-brand-200">{hint}</span>
      </span>
    </button>
  );
}
