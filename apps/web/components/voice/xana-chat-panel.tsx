"use client";

import { useEffect, useRef, useState } from "react";
import { ChatCards } from "@/components/assistant/chat-cards";
import { SparklesIcon } from "@/components/icons";
import type { Card } from "@/lib/assistant-types";
import { cn } from "@/lib/cn";
import type { VoiceTurn } from "@/lib/use-voice-agent";
import type { Citation, VoiceStateName } from "@/lib/voice-protocol";

const CARD_KINDS = new Set([
  "search", "xana", "product", "order", "store", "cart", "handoff", "return_options", "return_status",
]);

export function shownCards(cards: Record<string, unknown>[]): Card[] {
  return cards.filter((c) => CARD_KINDS.has(String(c.kind))) as unknown as Card[];
}

/**
 * The whole call as a chat: every question and every answer, with the products, orders, and
 * stores Xena found shown as cards under her words. Scrolls on its own; it follows the newest
 * message unless the customer has scrolled up to read, and then offers a way back down.
 */
export function XanaChatPanel({
  history,
  current,
  state,
  className,
}: {
  history: VoiceTurn[];
  current: { user: string; userFinal: boolean; xena: string; cards: Record<string, unknown>[]; citations: Citation[] };
  state: VoiceStateName | "off";
  className?: string;
}) {
  const scroller = useRef<HTMLDivElement>(null);
  const [pinned, setPinned] = useState(true);
  const turns: Omit<VoiceTurn, "id">[] = [...history];
  const live = Boolean(current.user || current.xena || current.cards.length);
  if (live) turns.push({ user: current.user, xena: current.xena, cards: current.cards, citations: current.citations });
  const thinking = state === "thinking";
  const size = `${history.length}:${current.user}:${current.xena}:${current.cards.length}:${thinking}`;

  useEffect(() => {
    const el = scroller.current;
    if (!el || !pinned) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [size, pinned]);

  return (
    <section
      aria-label="Conversation"
      className={cn(
        "flex min-h-0 flex-col overflow-hidden rounded-3xl border border-white/10 bg-white/4 text-left shadow-[0_30px_80px_-30px_rgb(0_0_0/0.8)] backdrop-blur-xl",
        className,
      )}
    >
      <header className="flex items-center gap-3 border-b border-white/10 bg-linear-to-r from-brand-500/25 via-brand-400/10 to-transparent px-5 py-3.5">
        <span className="relative grid size-9 place-items-center rounded-xl bg-linear-to-br from-brand-400 to-brand-600 shadow-[0_8px_20px_-8px_rgb(103_64_222/0.9)]">
          <SparklesIcon className="size-5 text-white" />
          {state !== "off" ? (
            <span className="absolute -right-0.5 -top-0.5 size-2.5 rounded-full bg-emerald-400 ring-2 ring-[#121638] motion-safe:animate-pulse" />
          ) : null}
        </span>
        <div className="leading-tight">
          <h2 className="text-sm font-semibold text-white">Conversation</h2>
          <p className="text-xs text-neutral-300">
            {turns.length ? `${turns.length} ${turns.length === 1 ? "exchange" : "exchanges"}` : "Everything you and Xena say shows here"}
          </p>
        </div>
      </header>

      <div className="relative min-h-0 flex-1">
        <div
          ref={scroller}
          onScroll={(e) => {
            const el = e.currentTarget;
            setPinned(el.scrollHeight - el.scrollTop - el.clientHeight < 60);
          }}
          className="h-full space-y-5 overflow-y-auto overscroll-contain px-4 py-5 [scrollbar-color:rgb(255_255_255/0.2)_transparent] [scrollbar-width:thin]"
        >
          {turns.length === 0 ? (
            <div className="grid h-full place-items-center px-6 text-center text-sm text-neutral-400">
              <p>Ask about an order, a product, or a return. Your conversation will build up here.</p>
            </div>
          ) : null}
          {turns.map((t, i) => (
            <div key={i} className="space-y-3">
              {t.user ? <UserBubble text={t.user} pending={i === turns.length - 1 && live && !current.userFinal} /> : null}
              {t.xena || t.cards.length ? (
                <XenaMessage text={t.xena} cards={shownCards(t.cards)} citations={t.citations} />
              ) : null}
            </div>
          ))}
          {thinking ? <Typing /> : null}
        </div>
        {!pinned ? (
          <button
            type="button"
            onClick={() => {
              setPinned(true);
              scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" });
            }}
            className="absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full border border-white/15 bg-[#1b1d4a]/90 px-4 py-1.5 text-xs font-semibold text-white shadow-lg backdrop-blur hover:bg-[#25285c]"
          >
            ↓ Latest
          </button>
        ) : null}
      </div>
    </section>
  );
}

function UserBubble({ text, pending }: { text: string; pending: boolean }) {
  return (
    <div className="flex justify-end motion-safe:animate-fade-in">
      <p
        className={cn(
          "max-w-[85%] rounded-2xl rounded-br-md border border-white/10 bg-white/10 px-4 py-2.5 text-[15px] leading-relaxed text-white",
          pending && "italic text-neutral-300",
        )}
      >
        <span className="sr-only">You: </span>
        {text}
      </p>
    </div>
  );
}

function XenaMessage({ text, cards, citations }: { text: string; cards: Card[]; citations: Citation[] }) {
  return (
    <div className="flex gap-2.5 motion-safe:animate-fade-in">
      <span aria-hidden className="mt-1 size-7 shrink-0 rounded-full bg-voice-orb shadow-[0_0_14px_rgb(125_100_239/0.6)]" />
      <div className="min-w-0 max-w-[88%] space-y-2">
        {text ? (
          <p className="rounded-2xl rounded-tl-md border border-brand-300/20 bg-linear-to-br from-brand-500/35 to-brand-700/20 px-4 py-2.5 text-[15px] leading-relaxed text-white shadow-[0_10px_30px_-18px_rgb(103_64_222/0.9)]">
            <span className="sr-only">Xena: </span>
            {text}
          </p>
        ) : null}
        {cards.length ? (
          <div className="[&_article]:shadow-[0_12px_30px_-18px_rgb(0_0_0/0.7)]">
            <ChatCards cards={cards} />
          </div>
        ) : null}
        {citations.length ? (
          <p className="px-1 text-xs text-brand-200">
            From {citations.map((c) => `${c.title}${c.section ? ` §${c.section}` : ""}`).join(", ")}
          </p>
        ) : null}
      </div>
    </div>
  );
}

function Typing() {
  return (
    <div className="flex items-center gap-2.5" role="status" aria-label="Xena is thinking">
      <span aria-hidden className="size-7 rounded-full bg-voice-orb opacity-80" />
      <span className="flex gap-1 rounded-2xl rounded-tl-md border border-brand-300/20 bg-brand-500/20 px-4 py-3">
        {[0, 150, 300].map((d) => (
          <span
            key={d}
            className="size-1.5 rounded-full bg-brand-100 motion-safe:animate-bounce"
            style={{ animationDelay: `${d}ms` }}
          />
        ))}
      </span>
    </div>
  );
}
