import type { Metadata } from "next";
import { XanaVoiceScreen } from "@/components/voice/xana-voice-screen";
import { getMe } from "@/lib/api-server";

export const metadata: Metadata = { title: "Talk to Xana" };

export default async function XanaVoicePage() {
  const me = await getMe();
  const firstName = (me.display_name ?? "").split(" ")[0] ?? "";
  return <XanaVoiceScreen firstName={firstName} closeHref="/support" />;
}
