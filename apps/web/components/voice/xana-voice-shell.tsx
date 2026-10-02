"use client";

import { useSelectedLayoutSegment } from "next/navigation";
import { XanaVoiceScreen } from "./xana-voice-screen";

export function XanaVoiceShell({ firstName }: { firstName: string }) {
  const segment = useSelectedLayoutSegment();
  return <XanaVoiceScreen firstName={firstName} provider={segment === "heygen" ? "heygen" : "tavus"} />;
}
