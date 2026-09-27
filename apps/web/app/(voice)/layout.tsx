import { SessionGuard } from "@/components/session-guard";
import { getMe } from "@/lib/api-server";

/** Full-screen, voice-first pages (no shop header or footer). Sign-in required like the shop. */
export default async function VoiceLayout({ children }: { children: React.ReactNode }) {
  // getMe() redirects to sign-in if the session is missing, expired, or revoked.
  await getMe();
  return (
    <>
      <SessionGuard />
      {children}
    </>
  );
}
