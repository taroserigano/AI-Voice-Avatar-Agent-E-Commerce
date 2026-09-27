"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { goToSignIn } from "./api-browser";
import {
  AssistantHttpError,
  createConversation,
  getConversation,
  getStatus,
  resumeTurn,
  sendMessage,
} from "./assistant-client";
import { plainAnswer } from "./assistant-text";
import type { AgentName, AssistantStatus, ChatMessage, ReturnQuoteCard, StreamEvent } from "./assistant-types";
import { CART_KEY } from "./cart-query";

function storageGet(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function storageSet(key: string, value: string | null) {
  try {
    if (value === null) window.localStorage.removeItem(key);
    else window.localStorage.setItem(key, value);
  } catch {
    // Private windows can refuse storage; the conversation just won't survive a reload.
  }
}

let seq = 0;
const localId = (prefix: string) => `${prefix}-${Date.now()}-${++seq}`;

export type AnswerDone = { text: string; quote: ReturnQuoteCard | null };

/**
 * One assistant conversation (Steph or Xana): loads the last one on first use, streams answers,
 * pauses on a return quote until the customer decides, and keeps the header's cart in step.
 */
export function useAssistant(agent: AgentName, options: { onAnswer?: (done: AnswerDone) => void } = {}) {
  const storageKey = `larkspur:assistant:${agent}`;
  const queryClient = useQueryClient();
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<AssistantStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const [pendingQuote, setPendingQuote] = useState<ReturnQuoteCard | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const loadingRef = useRef(false);
  // Bumped by send/reset: a history load that finishes afterwards must not overwrite them.
  const generationRef = useRef(0);
  const onAnswerRef = useRef(options.onAnswer);
  useEffect(() => {
    onAnswerRef.current = options.onAnswer;
  }, [options.onAnswer]);

  const handleAuth = (err: unknown) => {
    if (err instanceof AssistantHttpError && err.status === 401) {
      goToSignIn();
      return true;
    }
    return false;
  };

  const load = useCallback(async () => {
    if (loadingRef.current || loaded) return;
    loadingRef.current = true;
    const generation = generationRef.current;
    try {
      setStatus(await getStatus());
      const saved = storageGet(storageKey);
      if (saved) {
        try {
          const detail = await getConversation(saved);
          if (generation !== generationRef.current) return;
          setConversationId(detail.id);
          const restored = [...detail.messages];
          const last = restored[restored.length - 1];
          if (detail.pending_quote && last?.role === "assistant") {
            restored[restored.length - 1] = { ...last, quote: detail.pending_quote };
          }
          setMessages(restored);
          setPendingQuote(detail.pending_quote);
        } catch (err) {
          if (handleAuth(err)) return;
          storageSet(storageKey, null);
        }
      }
    } catch (err) {
      if (!handleAuth(err)) setUnavailable(true);
    } finally {
      setLoaded(true);
      loadingRef.current = false;
    }
  }, [loaded, storageKey]);

  const update = (id: string, patch: (m: ChatMessage) => ChatMessage) =>
    setMessages((all) => all.map((m) => (m.id === id ? patch(m) : m)));

  /** Stream one answer (a new message or a resumed turn) into a new assistant bubble. */
  const run = useCallback(
    async (userText: string | null, start: (id: string, signal: AbortSignal) => AsyncGenerator<StreamEvent>) => {
      if (busy) return;
      generationRef.current += 1;
      setBusy(true);
      setUnavailable(false);
      const answerId = localId("a");
      setMessages((all) => [
        ...all,
        ...(userText ? [{ id: localId("u"), role: "user" as const, text: userText, cards: [], citations: [] }] : []),
        { id: answerId, role: "assistant", text: "", cards: [], citations: [], pending: true, status: null },
      ]);
      const controller = new AbortController();
      abortRef.current = controller;
      let answer = "";
      let quote: ReturnQuoteCard | null = null;
      try {
        let id = conversationId;
        if (!id) {
          id = (await createConversation(agent)).id;
          setConversationId(id);
          storageSet(storageKey, id);
        }
        for await (const ev of start(id, controller.signal)) {
          if (ev.event === "signals") update(answerId, (m) => ({ ...m, signals: ev.data }));
          else if (ev.event === "status") update(answerId, (m) => ({ ...m, status: ev.data.label }));
          else if (ev.event === "text") {
            answer += ev.data.delta;
            update(answerId, (m) => ({ ...m, text: m.text + ev.data.delta, status: null }));
          } else if (ev.event === "card") {
            update(answerId, (m) => ({ ...m, cards: [...m.cards, ev.data] }));
            if (ev.data.kind === "cart") void queryClient.invalidateQueries({ queryKey: CART_KEY });
          } else if (ev.event === "quote") {
            quote = ev.data;
            update(answerId, (m) => ({ ...m, quote: ev.data }));
          } else if (ev.event === "citations") update(answerId, (m) => ({ ...m, citations: ev.data.valid }));
          else if (ev.event === "error") update(answerId, (m) => ({ ...m, error: ev.data.message }));
          else if (ev.event === "done")
            setStatus((s) => (s ? { ...s, model: ev.data.model, simulated: ev.data.simulated } : s));
        }
        setPendingQuote(quote);
        const spoken = plainAnswer(answer);
        setAnnouncement(quote ? `${spoken} ${quote.readback}`.trim() : spoken);
        onAnswerRef.current?.({ text: answer, quote });
      } catch (err) {
        if (handleAuth(err)) return;
        const aborted = controller.signal.aborted;
        update(answerId, (m) => ({
          ...m,
          error: aborted ? "Stopped." : "Sorry, I couldn't reach the assistant. Please try again.",
        }));
        if (err instanceof AssistantHttpError && err.status === 404) {
          // The saved conversation is gone (or isn't this account's): start a fresh one next time.
          storageSet(storageKey, null);
          setConversationId(null);
        }
      } finally {
        update(answerId, (m) => ({ ...m, pending: false, status: null }));
        abortRef.current = null;
        setBusy(false);
      }
    },
    [agent, busy, conversationId, queryClient, storageKey],
  );

  const send = useCallback(
    async (raw: string, opts: { voice?: boolean } = {}) => {
      const text = raw.trim();
      if (!text) return;
      await run(text, (id, signal) => sendMessage(id, text, signal, opts.voice ?? false));
    },
    [run],
  );

  /** After the customer confirmed (with the store) or declined the waiting quote. */
  const resume = useCallback(
    async (quoteId: string, outcome: "confirmed" | "declined", opts: { voice?: boolean } = {}) => {
      // The quote card is done either way; it shouldn't offer Confirm again.
      setMessages((all) => all.map((m) => (m.quote?.quote_id === quoteId ? { ...m, quote: { ...m.quote, status: outcome === "confirmed" ? "confirmed" : m.quote.status } } : m)));
      setPendingQuote(null);
      await run(null, (id, signal) => resumeTurn(id, quoteId, outcome, signal, opts.voice ?? false));
    },
    [run],
  );

  const stop = useCallback(() => abortRef.current?.abort(), []);

  const reset = useCallback(() => {
    generationRef.current += 1;
    abortRef.current?.abort();
    storageSet(storageKey, null);
    setConversationId(null);
    setMessages([]);
    setPendingQuote(null);
    setAnnouncement("");
  }, [storageKey]);

  return {
    agent,
    conversationId,
    messages,
    status,
    busy,
    loaded,
    unavailable,
    announcement,
    pendingQuote,
    load,
    send,
    resume,
    stop,
    reset,
  };
}

export type AssistantController = ReturnType<typeof useAssistant>;
