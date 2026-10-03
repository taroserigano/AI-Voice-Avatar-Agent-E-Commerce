"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { MicIcon, SparklesIcon, VideoIcon, XIcon } from "@/components/icons";
import { cn } from "@/lib/cn";
import { confirmQuote } from "@/lib/returns-confirm";
import { useVoiceAgent } from "@/lib/use-voice-agent";
import { captionFor, dollars } from "@/lib/voice-captions";
import type { AvatarProvider, QuoteCard } from "@/lib/voice-protocol";
import { XanaProviderTabs } from "./xana-provider-tabs";
import { XanaAvatar } from "./xana-avatar";
import { XanaLookPicker } from "./xana-look-picker";
import { XanaOrb } from "./xana-orb";

/**
 * The Xena voice screen: a full-screen, voice-first conversation for orders, returns, and
 * refunds. Separate from the chat. Everything Xena says is streamed as audio with captions
 * that follow her voice word by word; the customer's words appear live as they speak.
 *
 * A return is only ever confirmed by the customer: by the button, or by a clear spoken yes
 * that the server checks with a strict rule after the read-back played in full. The browser
 * then confirms with the store itself (the model never can).
 *
 * With Video on (when the server offers it), Xena's face (Tavus) takes the orb's place and
 * speaks her answers; captions follow her lips. If video fails, the call carries on as voice.
 */

const STATUS = {
  off: { title: "Tap to talk", hint: "Ask about an order, a return, or a refund." },
  connecting: { title: "Connecting", hint: "Getting Xena on the line…" },
  listening: { title: "Listening", hint: "Speak naturally. Xena answers when you pause." },
  hearing: { title: "Listening", hint: "Go on, Xena's listening." },
  thinking: { title: "Thinking", hint: "One moment…" },
  speaking: { title: "Speaking", hint: "Talk anytime to interrupt." },
  error: { title: "Voice is off", hint: "Something went wrong." },
} satisfies Record<string, { title: string; hint: string }>;

export function XanaVoiceScreen({ firstName, closeHref = "/support", provider = "tavus" }: {
  firstName: string; closeHref?: string; provider?: AvatarProvider;
}) {
  const voice = useVoiceAgent(undefined, provider);
  const { state, quote, confirmDecision, quoteOutcome } = voice;
  const [confirming, setConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState<string | null>(null);
  const handled = useRef<string | null>(null);
  const stage = useRef<HTMLElement>(null);

  // A clear spoken yes (checked by the server's rule, never the model) confirms like the button.
  useEffect(() => {
    if (!quote || !confirmDecision || handled.current === `${quote.quote_id}:${confirmDecision}`) return;
    handled.current = `${quote.quote_id}:${confirmDecision}`;
    if (confirmDecision === "yes") void onConfirm(quote);
    else if (confirmDecision === "no") quoteOutcome(quote.quote_id, "declined");
    // eslint-disable-next-line react-hooks/exhaustive-deps -- runs once per decision
  }, [quote, confirmDecision]);

  async function onConfirm(q: QuoteCard) {
    setConfirming(true);
    setConfirmError(null);
    try {
      // The browser confirms with the store itself; Xena only hears the outcome, then checks it.
      const result = await confirmQuote(q.quote_id);
      if (result.ok) quoteOutcome(q.quote_id, "confirmed");
      else setConfirmError(result.message);
    } finally {
      setConfirming(false);
    }
  }

  const status = STATUS[state];
  const captionNow = captionFor(voice.segments);

  // On short screens the newest words can fall below the fold: bring them just into view (not
  // the whole page to the bottom, which pushed her face off the top). Once the customer scrolls
  // themselves, leave the page where they put it until their next question.
  const transcript = useRef<HTMLDivElement>(null);
  const follow = useRef(true);
  const userFinal = voice.userFinal ? voice.userText : null;
  useEffect(() => {
    follow.current = true;
  }, [userFinal]);
  useEffect(() => {
    const el = stage.current;
    if (!follow.current || !el || el.scrollHeight <= el.clientHeight) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    transcript.current?.scrollIntoView({ block: "nearest", behavior: reduce ? "auto" : "smooth" });
  }, [captionNow, voice.userText, quote]);
  const stopFollowing = () => {
    follow.current = false;
  };
  const hint = state === "thinking" && voice.toolLabel ? voice.toolLabel : status.hint;
  const caption = captionNow;
  const level = state === "speaking" ? voice.speechLevel : voice.micLevel;
  const live = state !== "off" && state !== "error";
  const face = voice.avatar.status === "live" && voice.avatar.stream ? voice.avatar.stream : null;
  const videoOffered = live && voice.avatar.offer.available;

  return (
    <div className="fixed inset-0 z-50 flex flex-col overflow-hidden bg-voice-night text-white focus-inverse">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-white/10 px-4 py-3 sm:px-10">
        <div className="flex items-center gap-3">
          <span className="grid size-11 place-items-center rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 shadow-[0_8px_24px_-8px_rgb(103_64_222/0.9)] sm:size-12">
            <SparklesIcon className="size-6 text-white" />
          </span>
          <div className="leading-tight">
            <p className="font-display text-lg font-extrabold tracking-[0.2em]">XENA</p>
            <p className="text-sm text-neutral-300">Your AI voice assistant</p>
          </div>
        </div>
        <Link
          href={closeHref}
          onClick={() => voice.stop()}
          className="grid size-11 place-items-center rounded-2xl border border-white/15 bg-white/5 text-white transition hover:bg-white/10 sm:size-12"
          aria-label="Close voice assistant"
        >
          <XIcon className="size-6" />
        </Link>
      </header>

      {/* Stage */}
      <main
        ref={stage}
        id="main"
        onWheel={stopFollowing}
        onTouchMove={stopFollowing}
        onKeyDown={(e) => {
          if (["ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End", " "].includes(e.key)) stopFollowing();
        }}
        className={cn(
          "flex flex-1 flex-col items-center overflow-y-auto px-4 pb-6 text-center",
          face ? "pt-3 sm:pt-4" : "pt-6 sm:pt-10",
        )}
      >
        {/* With her face on screen the welcome heading gives its room to the video. */}
        <p className={cn("text-xs font-bold uppercase tracking-[0.32em] text-brand-200 sm:text-sm", face && "sr-only")}>
          Orders &amp; returns, in conversation
        </p>
        <h1
          className={cn("mt-3 font-display text-5xl font-extrabold tracking-[-0.04em] sm:text-7xl", face && "sr-only")}
        >
          Meet Xena
        </h1>
        <XanaProviderTabs provider={provider} disabled={confirming} />
        <section role="tabpanel" id="avatar-provider-panel" aria-labelledby={`avatar-tab-${provider}`} className="mt-4">
        {face ? (
          <XanaAvatar
            stream={face}
            state={state}
            greenscreen={voice.avatar.greenscreen}
            background={voice.avatar.background}
            onPlaying={voice.avatar.playbackStarted}
            onStopped={voice.avatar.playbackStopped}
          />
        ) : (

        <button
          type="button"
          onClick={() => {
            if (!live) void voice.start();
            else if (state === "speaking") voice.interrupt();
          }}
          className="mt-4 rounded-full sm:mt-6"
          aria-label={!live ? "Start talking to Xena" : state === "speaking" ? "Interrupt Xena" : "Xena is listening"}
        >
          <XanaOrb state={state} level={level} />
        </button>
        )}
        {live && voice.ready && !voice.avatar.offer.available ? (
          <p className="mt-3 text-sm text-neutral-300">{provider === "heygen" ? "HeyGen" : "Tavus"} video is not set up yet. You can still talk to Xena.</p>
        ) : null}
        </section>

        <div aria-live="polite" className="mt-1 min-h-20">
          <p className="font-display text-3xl font-bold tracking-tight">
            {status.title}
            {state === "thinking" ? <ThinkingDots /> : null}
          </p>
          <p className="mt-3 text-base text-neutral-300 sm:text-lg">
            {state === "error" && voice.error
              ? voice.error
              : voice.avatar.switching
                ? `Connecting ${provider === "heygen" ? "HeyGen" : "Tavus"} video. Microphone paused briefly…`
                : hint}
          </p>
        </div>

        {/* Live transcript: the customer's words as they speak, then Xena's as she says them. */}
        <div ref={transcript} className="mt-4 w-full max-w-2xl scroll-mb-4 space-y-3 text-lg leading-relaxed sm:text-xl">
          {voice.userText ? (
            <p className={cn("text-neutral-300", !voice.userFinal && "italic")}>
              <span className="sr-only">You said: </span>“{voice.userText}”
            </p>
          ) : live ? (
            <p className="text-neutral-400">Your words will appear here as you speak…</p>
          ) : null}
          {caption ? (
            <p className="font-medium text-white" aria-live="off">
              <span className="sr-only">Xena: </span>
              {caption}
            </p>
          ) : null}
          {voice.citations.length ? (
            <p className="text-sm text-brand-200">
              From{" "}
              {voice.citations.map((c, i) => (
                <span key={c.cite}>
                  {i ? ", " : ""}
                  {c.title}
                  {c.section ? ` §${c.section}` : ""}
                </span>
              ))}
            </p>
          ) : null}
        </div>

        {quote ? (
          <QuotePanel
            quote={quote}
            error={confirmError}
            busy={confirming}
            unclear={confirmDecision === "unclear"}
            buttonOnly={voice.quoteButtonOnly}
            onConfirm={() => void onConfirm(quote)}
            onDecline={() => quoteOutcome(quote.quote_id, "declined")}
          />
        ) : null}

        {live && voice.avatar.wanted && provider === "tavus" ? (
          <XanaLookPicker
            looks={voice.avatar.looks}
            look={voice.avatar.look}
            background={voice.avatar.background.key}
            busy={voice.avatar.status === "starting"}
            onLook={voice.chooseLook}
            onBackground={voice.chooseBackground}
          />
        ) : null}

        {voice.avatar.error ? <p className="mt-4 text-sm text-neutral-300">{voice.avatar.error}</p> : null}

        {voice.error && state !== "error" ? (
          <p role="alert" className="mt-4 text-sm text-danger-200">
            {voice.error}
          </p>
        ) : null}
      </main>

      {/* Controls */}
      <footer className="border-t border-white/10 px-4 pb-4 pt-5 text-center">
        {live ? (
          <div className="flex flex-wrap justify-center gap-3">
            <button
              type="button"
              onClick={() => voice.setMuted(!voice.muted)}
              aria-pressed={voice.muted}
              className={cn(
                "inline-flex min-w-40 items-center justify-center gap-2 rounded-2xl border px-6 py-3.5 text-lg font-medium transition",
                voice.muted
                  ? "border-accent-300/60 bg-accent-400/15 text-accent-200"
                  : "border-white/15 bg-white/5 hover:bg-white/10",
              )}
            >
              <MicIcon className="size-6" />
              {voice.muted ? "Unmute" : "Mute"}
            </button>
            {videoOffered ? (
              <button
                type="button"
                onClick={() => voice.setVideo(!voice.avatar.wanted)}
                aria-pressed={voice.avatar.wanted}
                className={cn(
                  "inline-flex min-w-40 items-center justify-center gap-2 rounded-2xl border px-6 py-3.5 text-lg font-medium transition disabled:opacity-60",
                  voice.avatar.wanted
                    ? "border-brand-300/60 bg-brand-500/20 text-brand-100"
                    : "border-white/15 bg-white/5 hover:bg-white/10",
                )}
              >
                <VideoIcon className="size-6" />
                {voice.avatar.wanted ? "Video off" : "Video"}
              </button>
            ) : null}
          </div>
        ) : (
          <button
            type="button"
            onClick={() => void voice.start()}
            className="inline-flex min-w-40 items-center justify-center gap-2 rounded-2xl bg-brand-600 px-6 py-3.5 text-lg font-semibold transition hover:bg-brand-500"
          >
            <MicIcon className="size-6" />
            {state === "error" ? "Try again" : "Start talking"}
          </button>
        )}
        <p className="mt-4 text-xs text-neutral-400 sm:text-sm">
          AI can make mistakes. Check important details on your order page.
          {voice.ready?.llm.simulated ? " Simulated answers (no AI model connected)." : ""}
          {voice.avatar.wanted && voice.avatar.offer.available ? ` ${voice.avatar.offer.notice}` : ""}
        </p>
        {process.env.NODE_ENV === "development" && voice.metrics?.first_audio_ms !== undefined ? (
          <p className="mt-1 font-mono text-[0.6875rem] text-neutral-500">
            first audio {Math.round(voice.metrics.first_audio_ms)} ms
            {voice.metrics.stt_ms !== undefined ? ` · transcript ${Math.round(voice.metrics.stt_ms)} ms` : ""}
            {voice.metrics.llm_first_token_ms !== undefined
              ? ` · first token ${Math.round(voice.metrics.llm_first_token_ms)} ms`
              : ""}
            {voice.metrics.filler ? " · filler" : ""}
          </p>
        ) : null}
        <span className="sr-only">Signed in as {firstName}.</span>
      </footer>
    </div>
  );
}

function ThinkingDots() {
  return (
    <span aria-hidden className="ml-1 inline-flex gap-1 align-middle">
      {[0, 180, 360].map((d) => (
        <span
          key={d}
          className="size-1.5 rounded-full bg-white animate-[voice-think_1.1s_ease-in-out_infinite]"
          style={{ animationDelay: `${d}ms` }}
        />
      ))}
    </span>
  );
}

function QuotePanel({
  quote,
  error,
  busy,
  unclear,
  buttonOnly,
  onConfirm,
  onDecline,
}: {
  quote: QuoteCard;
  error: string | null;
  busy: boolean;
  unclear: boolean;
  buttonOnly: boolean;
  onConfirm: () => void;
  onDecline: () => void;
}) {
  return (
    <section
      aria-label="Return quote"
      className="mt-6 w-full max-w-md rounded-3xl border border-white/15 bg-white/[0.06] p-5 text-left backdrop-blur"
    >
      <h2 className="font-display text-xl font-bold">Confirm your return</h2>
      <ul className="mt-3 space-y-1.5 text-neutral-200">
        {(quote.lines ?? []).map((ln, i) => (
          <li key={i} className="flex justify-between gap-4">
            <span>
              {ln.quantity} × {ln.title}
            </span>
            <span className="tabular-nums">{dollars(ln.refund_minor)}</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 flex justify-between border-t border-white/10 pt-3 font-semibold">
        <span>Refund{quote.refund_destination ? ` to ${String(quote.refund_destination)}` : ""}</span>
        <span className="tabular-nums">{dollars(quote.total_refund_minor)}</span>
      </p>
      {error ? (
        <p role="alert" className="mt-3 text-sm text-danger-200">
          {error}
        </p>
      ) : buttonOnly ? (
        <p className="mt-3 text-sm text-neutral-300">Review these details and tap Confirm return to continue.</p>
      ) : unclear ? (
        <p className="mt-3 text-sm text-accent-200">I need a clear yes. Say “yes, confirm”, or tap Confirm.</p>
      ) : (
        <p className="mt-3 text-sm text-neutral-300">Say “yes, confirm” or tap Confirm. Nothing is returned until you do.</p>
      )}
      <div className="mt-4 flex gap-3">
        <button
          type="button"
          disabled={busy}
          onClick={onConfirm}
          className="flex-1 rounded-2xl bg-brand-600 px-4 py-3 font-semibold transition hover:bg-brand-500 disabled:opacity-60"
        >
          {busy ? "Confirming…" : "Confirm return"}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={onDecline}
          className="rounded-2xl border border-white/15 px-4 py-3 font-medium transition hover:bg-white/10 disabled:opacity-60"
        >
          Not now
        </button>
      </div>
    </section>
  );
}
