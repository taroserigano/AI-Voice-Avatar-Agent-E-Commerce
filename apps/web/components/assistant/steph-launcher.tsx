"use client";

import { ChatIcon, PlusIcon, XIcon } from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/cn";
import { useAssistant } from "@/lib/use-assistant";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import { AssistantAvatar } from "./assistant-avatar";
import { OPEN_STEPH_EVENT } from "./open-steph";
import { ChatThread, type Persona } from "./chat-thread";

const STEPH: Persona = {
  name: "Steph",
  role: "AI shopping assistant",
  avatar: <AssistantAvatar who="steph" />,
  greeting:
    "Hi, I'm Steph, Serigan Mart's shopping assistant. I can find products (down to diet labels and nutrition), check your orders, answer policy questions, and find stores.",
  suggestions: [
    "Non fat organic milk, not regular milk",
    "Find me sugar free yogurt",
    "Where's my latest order?",
    "How long do I have to return something?",
    "Which stores are open now?",
  ],
  placeholder: "Ask Steph anything…",
};

/** "Ask Steph": a lower-right button that opens the shopping assistant on every shop page. */
export function StephLauncher() {
  const [open, setOpen] = useState(false);
  const chat = useAssistant("steph");
  const launcherRef = useRef<HTMLButtonElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { load } = chat;
  // Xana has the Support page; Steph stays out of her way there.
  const onSupport = usePathname()?.startsWith("/support") ?? false;

  const close = useCallback(() => {
    setOpen(false);
    // Return focus to the button that opened the panel.
    requestAnimationFrame(() => launcherRef.current?.focus());
  }, []);

  useEffect(() => {
    if (!open) return;
    void load();
    inputRef.current?.focus();
    const onKey = (e: globalThis.KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, load, close]);

  // Other parts of the site open Steph (optionally with a question) through a window event.
  const pendingPrompt = useRef<string | null>(null);
  useEffect(() => {
    const onOpen = (e: Event) => {
      const prompt = (e as CustomEvent<{ prompt?: string }>).detail?.prompt;
      if (prompt) pendingPrompt.current = prompt;
      setOpen(true);
    };
    window.addEventListener(OPEN_STEPH_EVENT, onOpen);
    return () => window.removeEventListener(OPEN_STEPH_EVENT, onOpen);
  }, []);
  const { loaded, busy, send } = chat;
  useEffect(() => {
    if (open && loaded && !busy && pendingPrompt.current) {
      const prompt = pendingPrompt.current;
      pendingPrompt.current = null;
      void send(prompt);
    }
  }, [open, loaded, busy, send]);

  // The pill shrinks to its icon once the shopper scrolls, so it stops covering content near the
  // bottom-right corner; it opens out again back near the top, or on hover or keyboard focus.
  const [scrolled, setScrolled] = useState(false);
  const [attention, setAttention] = useState({ hover: false, focus: false });
  useEffect(() => {
    let frame = 0;
    const update = () => {
      frame = 0;
      setScrolled(window.scrollY > 64);
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(frame);
    };
  }, []);
  const expanded = !scrolled || attention.hover || attention.focus;

  // Render only once hydrated: a click before then would do nothing.
  const hydrated = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
  if (onSupport || !hydrated) return null;

  return (
    <>
      <button
        ref={launcherRef}
        type="button"
        onClick={() => setOpen(true)}
        onMouseEnter={() => setAttention((a) => ({ ...a, hover: true }))}
        onMouseLeave={() => setAttention((a) => ({ ...a, hover: false }))}
        onFocus={(e) => {
          // Keyboard focus opens it out; a mouse click's focus doesn't need to.
          const keyboard = e.currentTarget.matches(":focus-visible");
          setAttention((a) => ({ ...a, focus: keyboard }));
        }}
        onBlur={() => setAttention((a) => ({ ...a, focus: false }))}
        aria-expanded={open}
        aria-controls="steph-panel"
        className={cn(
          "fixed bottom-4 right-4 z-50 inline-flex size-13 items-center justify-center rounded-full bg-brand-600 font-semibold text-white shadow-glow-lg sm:bottom-5 sm:right-5 sm:h-14 sm:w-auto sm:min-w-14 sm:px-4",
          "transition-[transform,opacity] duration-200 hover:-translate-y-0.5 hover:bg-brand-700 motion-reduce:transition-none print:hidden",
          open && "pointer-events-none translate-y-2 opacity-0",
        )}
        tabIndex={open ? -1 : 0}
      >
        <ChatIcon className="size-5.5 shrink-0" />
        {/* Collapsed, the label is clipped to nothing but stays in the accessible name. */}
        <span
          className={cn(
            "whitespace-nowrap max-sm:sr-only sm:overflow-hidden sm:transition-[max-width,margin-left,opacity] sm:duration-200 sm:ease-snappy motion-reduce:transition-none",
            expanded ? "sm:ml-2.5 sm:max-w-32 sm:pr-1 sm:opacity-100" : "sm:ml-0 sm:max-w-0 sm:opacity-0",
          )}
        >
          Ask Steph
        </span>
      </button>

      {open ? (
        <section
          id="steph-panel"
          role="dialog"
          aria-modal="false"
          aria-labelledby="steph-title"
          className="fixed inset-0 z-50 flex animate-scale-in flex-col bg-raised sm:inset-auto sm:bottom-5 sm:right-5 sm:h-[min(42rem,calc(100vh-2.5rem))] sm:w-104 sm:overflow-hidden sm:rounded-3xl sm:shadow-2xl sm:ring-1 sm:ring-line print:hidden"
        >
          <header className="flex items-center gap-3 border-b border-line bg-[linear-gradient(180deg,var(--color-brand-50),var(--color-raised))] px-4 py-3">
            <AssistantAvatar who="steph" size="lg" />
            <div className="min-w-0 flex-1">
              <h2 id="steph-title" className="font-display text-lg font-semibold leading-tight text-ink">
                Steph
              </h2>
              <p className="flex flex-wrap items-center gap-1.5 text-xs text-muted">
                AI shopping assistant
                {chat.status?.simulated ? (
                  <span
                    className="cursor-help"
                    title="Steph's AI model is offline in this demo, so answers come from simple rules and live store data."
                  >
                    <Badge tone="accent">Simulated</Badge>
                    <span className="sr-only">
                      : the AI model is offline in this demo, so answers come from simple rules and live store data
                    </span>
                  </span>
                ) : null}
              </p>
            </div>
            <button
              type="button"
              onClick={chat.reset}
              className="inline-flex size-10 items-center justify-center rounded-full text-ink-soft hover:bg-neutral-100"
              aria-label="New conversation"
              title="New conversation"
            >
              <PlusIcon className="size-5" />
            </button>
            <button
              type="button"
              onClick={close}
              className="inline-flex size-10 items-center justify-center rounded-full text-ink-soft hover:bg-neutral-100"
              aria-label="Close Steph"
            >
              <XIcon className="size-5" />
            </button>
          </header>
          <ChatThread persona={STEPH} chat={chat} inputRef={inputRef} />
          <p className="bg-raised px-4 pb-3 text-center text-[0.6875rem] leading-snug text-muted">
            Steph is an AI assistant and can make mistakes. Prices, orders, and policies come from Serigan Mart&apos;s
            systems.
          </p>
        </section>
      ) : null}
    </>
  );
}
