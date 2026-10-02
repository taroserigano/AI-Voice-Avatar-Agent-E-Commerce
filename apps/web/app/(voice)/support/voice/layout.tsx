import { XanaVoiceShell } from "@/components/voice/xana-voice-shell";
import { getMe } from "@/lib/api-server";

/** Persists across provider route changes: one voice controller, transcript and quote. */
export default async function VoiceLayout({ children }: { children: React.ReactNode }) {
  const me = await getMe();
  return <>
    <XanaVoiceShell firstName={(me.display_name ?? "").split(" ")[0] ?? ""} />
    {children}
  </>;
}
