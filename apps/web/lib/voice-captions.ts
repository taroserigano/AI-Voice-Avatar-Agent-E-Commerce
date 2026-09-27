import type { Word } from "./voice-protocol";

/**
 * Captions that follow the voice: each word appears when the speaker actually reaches it.
 *
 * The server sends each spoken segment's text and word timings (from the speech engine); the
 * player reports how many milliseconds of each segment have played. `visibleText` is what the
 * customer has heard so far, so the words on screen never run ahead of (or lag behind) Xana.
 * Without timings (an engine that gives none) the whole text shows as soon as audio starts.
 */

export type CaptionSegment = {
  segment: number;
  text: string;
  words: Word[];
  playedMs: number;
  done: boolean;
};

export function visibleText(seg: CaptionSegment): string {
  if (seg.done) return seg.text;
  if (seg.words.length === 0) return seg.playedMs > 0 ? seg.text : "";
  const heard = seg.words.filter((w) => w.start_ms <= seg.playedMs).map((w) => w.w);
  return joinWords(heard);
}

/** Join engine words back into text: no space before punctuation or after an opening quote. */
export function joinWords(words: string[]): string {
  let out = "";
  for (const w of words) {
    if (!w) continue;
    if (out === "" || /^[,.;:!?%)\]'’”]/.test(w) || /[(\["“$]$/.test(out)) out += w;
    else out += ` ${w}`;
  }
  return out;
}

/** Everything heard in this answer so far, across its segments (fillers excluded). */
export function captionFor(segments: CaptionSegment[]): string {
  return segments
    .map(visibleText)
    .filter((t) => t.length > 0)
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
}

/** Money for the screen, from minor units. */
export function dollars(minor: number | undefined): string {
  if (minor === undefined || Number.isNaN(minor)) return "";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(minor / 100);
}
