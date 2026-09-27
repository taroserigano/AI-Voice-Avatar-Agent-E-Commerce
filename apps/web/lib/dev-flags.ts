"use client";

import { useSyncExternalStore } from "react";

/**
 * Developer views (the assistants' "Why this answer" panel, simulated speech, provider names)
 * stay hidden from shoppers even in development. Turn them on with `?debug=1` once (remembered
 * in this browser) and off with `?debug=0`.
 */
function read(): boolean {
  try {
    const param = new URLSearchParams(window.location.search).get("debug");
    if (param === "1") window.localStorage.setItem("serigan-mart:debug", "1");
    if (param === "0") window.localStorage.removeItem("serigan-mart:debug");
    return window.localStorage.getItem("serigan-mart:debug") === "1";
  } catch {
    return false;
  }
}

export function useDebugView(): boolean {
  return useSyncExternalStore(
    () => () => {},
    read,
    () => false,
  );
}

/** Whether the URL asks for the simulated-speech box on /support (`?voice=sim`). */
export function useSimulatedVoice(): boolean {
  return useSyncExternalStore(
    () => () => {},
    () => {
      try {
        return new URLSearchParams(window.location.search).get("voice") === "sim";
      } catch {
        return false;
      }
    },
    () => false,
  );
}
