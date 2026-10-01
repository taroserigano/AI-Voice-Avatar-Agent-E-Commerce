/**
 * The wire protocol between the Xana voice screen and the voice agent (services/voice).
 *
 * One WebSocket per session:
 * - browser → server, binary: microphone audio, PCM16 mono at MIC_RATE, ~20 ms per frame;
 * - server → browser, binary: speech audio, a 4-byte little-endian segment number followed by
 *   PCM16 mono at SPEECH_RATE. Audio for a segment the browser was told to drop is discarded;
 * - both ways, text: one JSON message per frame (the types below).
 */

export const MIC_RATE = 24_000;
export const SPEECH_RATE = 24_000;

export type VoiceStateName = "connecting" | "listening" | "hearing" | "thinking" | "speaking" | "error";

export type Word = { w: string; start_ms: number; end_ms: number };

export type QuoteLine = { title: string; quantity: number; refund_minor: number };

export type QuoteCard = {
  kind: "return_quote";
  quote_id: string;
  order_number?: string;
  lines?: QuoteLine[];
  total_refund_minor?: number;
  refund_destination?: string;
  needs_shipping?: boolean;
  expires_at?: string;
  readback?: string;
  [key: string]: unknown;
};

export type Citation = { cite: string; title: string; section?: string; url?: string; snippet?: string };

export type ServerMessage =
  | {
      type: "ready";
      conversation_id: string;
      first_name: string;
      voice: { provider: string; name: string };
      stt: { provider: string; model: string };
      llm: { model: string; simulated: boolean };
      /** Xana's face (Tavus): offered only when the server has it set up. */
      avatar?: AvatarOffer;
      notice: string;
    }
  | { type: "state"; state: VoiceStateName }
  | { type: "user.partial"; text: string }
  | { type: "user.final"; text: string }
  | { type: "segment.start"; segment: number; kind: "filler" | "answer" | "confirm"; text: string }
  /** More text for a segment (appended; an answer arrives clause by clause). */
  | { type: "segment.text"; segment: number; text: string }
  /** Word timings for a segment, from its start (appended). */
  | { type: "segment.words"; segment: number; words: Word[] }
  | { type: "segment.end"; segment: number }
  | { type: "drop"; segments: number[] }
  | { type: "tool"; name: string; label: string }
  | { type: "card"; card: Record<string, unknown> }
  | { type: "quote"; quote: QuoteCard }
  | { type: "citations"; citations: Citation[] }
  | {
      type: "turn.done";
      metrics: { stt_ms?: number; first_audio_ms?: number; llm_first_token_ms?: number; filler?: boolean };
    }
  | { type: "confirm.result"; decision: "yes" | "no" | "unclear"; quote_id: string }
  | { type: "error"; message: string; fatal?: boolean }
  /** The private Tavus room for this call, for this customer only. */
  | {
      type: "avatar";
      provider: "tavus";
      conversation_id: string;
      url: string;
      token: string | null;
      /** Which look this room shows, and whether it's on a green screen (the browser then
       *  puts the chosen background behind her). */
      look: string | null;
      greenscreen: boolean;
    }
  | { type: "avatar.unavailable"; reason: "not_configured" | "busy" | "error" }
  | { type: "avatar.ended" };

export type AvatarLook = { key: string; label: string };

export type AvatarOffer =
  | { available: false }
  | { available: true; provider: "tavus"; notice: string; looks?: AvatarLook[]; default_look?: string | null };

export type ClientMessage =
  | { type: "hello"; conversation_id?: string | null; mic_rate: number; speech_rate: number }
  | { type: "mute"; muted: boolean }
  | { type: "played"; segment: number; complete: boolean; played_ms: number }
  | { type: "interrupt" }
  | { type: "text"; text: string }
  | { type: "quote.outcome"; quote_id: string; outcome: "confirmed" | "declined" }
  | { type: "avatar.start"; look?: string }
  | { type: "avatar.stop" };

export function parseServerMessage(raw: string): ServerMessage | null {
  try {
    const msg = JSON.parse(raw) as { type?: unknown };
    return typeof msg?.type === "string" ? (msg as ServerMessage) : null;
  } catch {
    return null;
  }
}

/** Split a server audio frame into its segment number and PCM16 samples. */
export function splitAudioFrame(buf: ArrayBuffer): { segment: number; pcm: Int16Array } | null {
  if (buf.byteLength < 4 || (buf.byteLength - 4) % 2 !== 0) return null;
  const segment = new DataView(buf).getUint32(0, true);
  return { segment, pcm: new Int16Array(buf, 4) };
}
