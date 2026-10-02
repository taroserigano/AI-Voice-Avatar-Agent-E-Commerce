"use client";

import { ArrowRightIcon, MicIcon } from "@/components/icons";
import { answerBlocks, type Segment } from "@/lib/assistant-text";
import { useDebugView } from "@/lib/dev-flags";
import Link from "next/link";
import type { ChatMessage, TurnSignals } from "@/lib/assistant-types";
import { cn } from "@/lib/cn";
import type { AssistantController } from "@/lib/use-assistant";
import { type FormEvent, type KeyboardEvent, type ReactNode, useEffect, useRef, useState } from "react";
import { ChatCards, Sources } from "./chat-cards";
import { QuoteCard } from "./quote-card";

export type Persona = {
  name: string;
  role: string;
  avatar: ReactNode;
  greeting: string;
  suggestions: string[];
  placeholder: string;
};

/** The message list and composer, shared by the Steph panel and the Xena page. */
export function ChatThread({
  persona,
  chat,
  inputRef,
  voiceSlot,
  className,
}: {
  persona: Persona;
  chat: AssistantController;
  inputRef?: React.RefObject<HTMLTextAreaElement | null>;
  /** Voice controls (Xena); Steph shows a disabled mic until voice arrives. */
  voiceSlot?: ReactNode;
  className?: string;
}) {
  const [draft, setDraft] = useState("");
  const debugView = useDebugView();
  const listRef = useRef<HTMLDivElement>(null);
  const ownRef = useRef<HTMLTextAreaElement>(null);
  const textarea = inputRef ?? ownRef;

  // Keep the newest message in view as it streams.
  const last = chat.messages[chat.messages.length - 1];
  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [chat.messages.length, last?.text, last?.cards.length, last?.status]);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!draft.trim() || chat.busy) return;
    void chat.send(draft);
    setDraft("");
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) submit(e);
  };

  return (
    <div className={cn("flex min-h-0 flex-1 flex-col", className)}>
      <div ref={listRef} className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-4" tabIndex={-1}>
        <Bubble role="assistant" avatar={persona.avatar} name={persona.name}>
          <p className="leading-relaxed">{persona.greeting}</p>
        </Bubble>
        {chat.messages.length === 0 && chat.loaded ? (
          <div>
            <p className="px-1 text-xs font-semibold uppercase tracking-eyebrow text-muted">Try asking</p>
            <ul className="mt-2 flex flex-wrap gap-2">
              {persona.suggestions.map((s) => (
                <li key={s}>
                  <button
                    type="button"
                    onClick={() => void chat.send(s)}
                    className="rounded-full bg-brand-50 px-3 py-1.5 text-left text-sm font-medium text-brand-800 ring-1 ring-inset ring-brand-100 transition-colors hover:bg-brand-100"
                  >
                    {s}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {chat.messages.map((m) => (
          <MessageView key={m.id} message={m} persona={persona} chat={chat} debug={debugView && (chat.status?.debug ?? false)} />
        ))}
        {chat.unavailable ? (
          <p role="alert" className="rounded-xl bg-danger-50 px-3 py-2 text-sm text-danger-800">
            {persona.name} isn&apos;t available right now. Please try again in a moment.
          </p>
        ) : null}
      </div>

      {/* Announce finished answers once; the streaming text itself isn't read token by token. */}
      <p className="sr-only" role="status" aria-live="polite">
        {chat.announcement ? `${persona.name}: ${chat.announcement}` : ""}
      </p>

      <form onSubmit={submit} className="border-t border-line bg-raised px-3 py-3">
        <div className="flex items-end gap-2 rounded-2xl bg-canvas p-1.5 ring-1 ring-inset ring-line focus-within:ring-2 focus-within:ring-brand-600">
          <label htmlFor={`${persona.name}-input`} className="sr-only">
            Message {persona.name}
          </label>
          <textarea
            id={`${persona.name}-input`}
            ref={textarea}
            rows={1}
            value={draft}
            maxLength={2000}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKey}
            placeholder={persona.placeholder}
            className="max-h-32 min-h-10 flex-1 resize-none bg-transparent px-2.5 py-2 text-[0.9375rem] text-ink placeholder:text-muted focus:outline-none"
          />
          {voiceSlot ?? (
            <Link
              href="/support"
              title="Talk by voice with Xena, our support assistant"
              aria-label="Talk by voice with Xena"
              className="inline-flex size-10 items-center justify-center rounded-full text-ink-soft transition-colors hover:bg-neutral-100 hover:text-brand-700"
            >
              <MicIcon className="size-5" />
            </Link>
          )}
          {chat.busy ? (
            <button
              type="button"
              onClick={chat.stop}
              className="inline-flex h-10 items-center rounded-full bg-neutral-200 px-4 text-sm font-semibold text-ink hover:bg-neutral-300"
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              disabled={!draft.trim()}
              aria-label="Send"
              className="inline-flex size-10 items-center justify-center rounded-full bg-brand-600 text-white shadow-xs transition-colors hover:bg-brand-700 disabled:bg-neutral-300"
            >
              <ArrowRightIcon className="size-5" />
            </button>
          )}
        </div>
      </form>
    </div>
  );
}

function Bubble({
  role,
  avatar,
  name,
  children,
}: {
  role: "user" | "assistant";
  avatar?: ReactNode;
  name?: string;
  children: ReactNode;
}) {
  if (role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-brand-600 px-3.5 py-2 text-[0.9375rem] text-white">
          <p className="sr-only">You said:</p>
          {children}
        </div>
      </div>
    );
  }
  return (
    <div className="flex gap-2.5">
      <div className="shrink-0">{avatar}</div>
      <div className="min-w-0 flex-1">
        <p className="sr-only">{name} said:</p>
        <div className="text-[0.9375rem] text-ink">{children}</div>
      </div>
    </div>
  );
}

function MessageView({
  message,
  persona,
  chat,
  debug,
}: {
  message: ChatMessage;
  persona: Persona;
  chat: AssistantController;
  debug: boolean;
}) {
  if (message.role === "user") {
    return (
      <Bubble role="user">
        <p className="whitespace-pre-wrap break-words">{message.text}</p>
      </Bubble>
    );
  }
  const blocks = answerBlocks(message.text, message.citations, message.pending);
  const thinking = message.pending && !message.text && !message.cards.length;
  return (
    <Bubble role="assistant" avatar={persona.avatar} name={persona.name}>
      {thinking ? (
        <p className="flex items-center gap-2 text-sm text-muted">
          <TypingDots />
          {message.status ?? "Thinking…"}
        </p>
      ) : null}
      <div className="space-y-2 leading-relaxed">
        {blocks.map((b, i) =>
          b.kind === "paragraph" ? (
            <p key={i}>
              <Segments segments={b.segments} />
            </p>
          ) : (
            <ul key={i} className="list-disc space-y-1 pl-5 marker:text-brand-400">
              {b.items.map((item, j) => (
                <li key={j}>
                  <Segments segments={item} />
                </li>
              ))}
            </ul>
          ),
        )}
      </div>
      {message.pending && message.status && message.text ? (
        <p className="mt-1 flex items-center gap-2 text-xs text-muted">
          <TypingDots /> {message.status}
        </p>
      ) : null}
      <ChatCards cards={message.cards} onAsk={chat.busy ? undefined : (text) => void chat.send(text)} />
      {message.quote ? (
        <QuoteCard
          quote={message.quote}
          disabled={chat.busy || chat.pendingQuote?.quote_id !== message.quote.quote_id}
          onResolved={(outcome) => chat.resume(message.quote!.quote_id, outcome)}
        />
      ) : null}
      {!message.pending ? <Sources citations={message.citations} /> : null}
      {message.error ? (
        <p role="alert" className="mt-2 text-sm text-danger-700">
          {message.error}
        </p>
      ) : null}
      {debug && message.signals && !message.pending ? <WhyPanel signals={message.signals} /> : null}
    </Bubble>
  );
}

const pct = (n: number | null | undefined) => (n == null ? "–" : `${Math.round(n * 100)}%`);

/** Development only: what the decision model read from the turn, and whether code acted on it. */
function WhyPanel({ signals }: { signals: TurnSignals }) {
  const rows: [string, string][] = [];
  const pick = (label: string, p: TurnSignals["intent"]) => {
    if (p) rows.push([label, `${p.value.replaceAll("_", " ")} · ${pct(p.confidence)}${p.act ? " · used" : " · not confident enough"}`]);
  };
  pick("Intent", signals.intent);
  pick("Return reason", signals.return_reason);
  pick("Order line", signals.target_line);
  rows.push(["Wants a person", pct(signals.wants_person)]);
  rows.push(["Rule-bypass attempt", pct(signals.policy_bypass)]);
  const source =
    signals.source === "jev"
      ? `Jev (${signals.model ?? "?"}, ${Math.round(signals.latency_ms)} ms)`
      : signals.source === "simulated"
        ? "Jev simulator (no TYPESAFE_API_KEY)"
        : signals.source === "error"
          ? "Jev unavailable this turn"
          : "Jev off";
  return (
    <details className="mt-2 rounded-xl bg-canvas px-3 py-2 text-xs text-muted ring-1 ring-inset ring-line">
      <summary className="cursor-pointer font-medium text-ink-soft">Why this answer (development)</summary>
      <p className="mt-1.5">{source}</p>
      <dl className="mt-1 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5">
        {rows.map(([k, v]) => (
          <div key={k} className="contents">
            <dt>{k}</dt>
            <dd className="text-ink-soft">{v}</dd>
          </div>
        ))}
      </dl>
    </details>
  );
}

function Segments({ segments }: { segments: Segment[] }) {
  return (
    <>
      {segments.map((s, i) =>
        s.kind === "text" ? (
          <span key={i}>{s.text}</span>
        ) : (
          <a
            key={i}
            href={s.citation.url ?? "#"}
            target="_blank"
            rel="noreferrer"
            className="mx-0.5 inline-flex size-4.5 -translate-y-1 items-center justify-center rounded-full bg-brand-100 text-[0.625rem] font-semibold text-brand-800 no-underline hover:bg-brand-200"
            aria-label={`Source ${s.n}: ${s.citation.doc_title} section ${s.citation.number} (opens in a new tab)`}
          >
            {s.n}
          </a>
        ),
      )}
    </>
  );
}

function TypingDots() {
  return (
    <span aria-hidden="true" className="inline-flex gap-0.5">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="size-1.5 animate-pulse rounded-full bg-brand-400 motion-reduce:animate-none"
          style={{ animationDelay: `${i * 150}ms` }}
        />
      ))}
    </span>
  );
}
