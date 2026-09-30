import { SPEECH_RATE } from "./voice-protocol";

/**
 * Xana's face (Tavus, echo mode): turns the speech the voice agent streams into Tavus echo
 * messages, and works out what the customer has actually heard. See
 * docs/features/10-xana-avatar.
 *
 * What the spike showed (2026-09-30), and what this does about it:
 * - Tavus drops audio sent under a new `inference_id` while it's still speaking. So everything
 *   Xana says in one turn goes under one id, closed by a short silent chunk with `done: true`
 *   at `turn.done`, and the next turn's audio waits until Tavus has finished the previous one.
 * - Tavus plays our audio ~0.8 s after we send it. Its `started_speaking` event comes ~150 ms
 *   before the audio is heard, and `stopped_speaking` says whether it was `interrupted`.
 * - Tavus splits one stretch of speech into several utterances at small gaps, so stop events
 *   alone can't say which segment finished. Each segment gets a place on a playback timeline
 *   (it starts when it was sent plus Tavus's delay, or when the one before it ends). A segment
 *   counts as heard in full only when a clean `stopped_speaking` arrives at or after its end.
 *
 * Safety: a confirm segment (the return read-back) is reported complete only on that clean
 * stop. If Tavus never reports one, it stays incomplete, so a spoken yes is "unclear" and the
 * customer can still tap Confirm. Other segments fall back to the timeline after a while, so a
 * lost event can't leave Xana "speaking" forever.
 */

export const DEFAULT_DELAY_MS = 800;
const HEARD_AFTER_EVENT_MS = 150;
const END_TOLERANCE_MS = 250;
const FALLBACK_COMPLETE_MS = 3000;
const PREVIOUS_TURN_TIMEOUT_MS = 2000;
const COALESCE_MS = 100;
const SILENT_TAIL = new Int16Array(SPEECH_RATE / 50); // 20 ms

export type EchoMessage = {
  message_type: "conversation";
  event_type: "conversation.echo" | "conversation.interrupt";
  conversation_id: string;
  properties?: { modality: "audio"; audio: string; sample_rate: number; inference_id: string; done: boolean };
};

export function pcmBase64(pcm: Int16Array): string {
  const bytes = new Uint8Array(pcm.buffer, pcm.byteOffset, pcm.byteLength);
  let s = "";
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(s);
}

type SegmentKind = "filler" | "answer" | "confirm";

type Seg = {
  segment: number;
  kind: SegmentKind;
  turn: Turn | null;
  samples: number;
  /** When its first audio was sent to Tavus. */
  sentAt: number | null;
  /** When the customer starts hearing it: estimated, then confirmed by `started_speaking`. */
  heardStart: number | null;
  confirmedStart: boolean;
  ended: boolean;
  complete: boolean;
  dropped: boolean;
  /** Fixed once it has been heard in full. */
  endAt: number | null;
};

type Turn = {
  id: string;
  segments: Seg[];
  pending: Int16Array[];
  /** Messages held back until the previous turn has finished playing. */
  held: EchoMessage[];
  started: boolean;
  closed: boolean;
  finished: boolean;
};

export type Completed = { segment: number; playedMs: number };

export class AvatarEcho {
  private readonly send: (msg: EchoMessage) => void;
  private readonly conversationId: string;
  private readonly now: () => number;
  private readonly newId: () => string;
  private segs = new Map<number, Seg>();
  private order: Seg[] = [];
  private turns: Turn[] = [];
  private current: Turn | null = null;
  private completed: Completed[] = [];
  delayMs = DEFAULT_DELAY_MS;

  constructor(opts: {
    send: (msg: EchoMessage) => void;
    conversationId: string;
    now?: () => number;
    newId?: () => string;
  }) {
    this.send = opts.send;
    this.conversationId = opts.conversationId;
    this.now = opts.now ?? (() => performance.now());
    this.newId = opts.newId ?? (() => crypto.randomUUID());
  }

  // --- from the voice agent ------------------------------------------------------------

  segmentStart(segment: number, kind: SegmentKind): void {
    if (this.segs.has(segment)) return;
    const seg: Seg = {
      segment,
      kind,
      turn: null,
      samples: 0,
      sentAt: null,
      heardStart: null,
      confirmedStart: false,
      ended: false,
      complete: false,
      dropped: false,
      endAt: null,
    };
    this.segs.set(segment, seg);
    this.order.push(seg);
  }

  audio(segment: number, pcm: Int16Array): void {
    if (!this.segs.has(segment)) this.segmentStart(segment, "answer");
    const seg = this.segs.get(segment)!;
    if (seg.dropped || seg.complete || pcm.length === 0) return;
    const turn = seg.turn ?? this.attach(seg);
    seg.samples += pcm.length;
    turn.pending.push(pcm);
    // The first audio of a turn goes at once (it's what the customer is waiting for).
    if (!turn.started || pendingMs(turn) >= COALESCE_MS) this.flush(turn);
  }

  segmentEnd(segment: number): void {
    const seg = this.segs.get(segment);
    if (!seg) return;
    seg.ended = true;
    if (seg.turn) this.flush(seg.turn);
  }

  /** The server finished the turn: close its utterance so Tavus plays it to the end. */
  turnDone(): void {
    const turn = this.current;
    if (!turn || turn.closed) return;
    this.flush(turn);
    if (turn.started) this.emit(turn, SILENT_TAIL, true);
    turn.closed = true;
    this.current = null;
  }

  /** Barge-in: stop Tavus at once; the dropped segments were never fully heard. */
  drop(segments: number[]): void {
    let any = false;
    for (const n of segments) {
      const seg = this.segs.get(n);
      if (!seg || seg.complete) continue;
      seg.dropped = true;
      any = true;
    }
    if (!any) return;
    for (const turn of this.turns) {
      if (turn.finished) continue;
      if (turn.segments.every((s) => s.dropped || s.complete)) {
        turn.pending = [];
        turn.held = [];
        turn.closed = true;
        turn.finished = true;
        if (this.current === turn) this.current = null;
      }
    }
    this.send({ message_type: "conversation", event_type: "conversation.interrupt", conversation_id: this.conversationId });
    this.release();
  }

  // --- from Tavus ----------------------------------------------------------------------

  onTavus(eventType: string, properties?: { role?: string; interrupted?: boolean } | null): void {
    const role =
      eventType.startsWith("conversation.pal.") ? "pal" : eventType.startsWith("conversation.replica.") ? "replica" : properties?.role;
    if (role !== "pal") return; // Tavus sends each PAL event twice (pal and legacy replica)
    const t = this.now();
    if (eventType.endsWith("started_speaking")) this.onStarted(t);
    else if (eventType.endsWith("stopped_speaking")) this.onStopped(t, Boolean(properties?.interrupted));
  }

  private onStarted(t: number): void {
    const seg = this.order.find((s) => !s.complete && !s.dropped && s.sentAt !== null && s.sentAt <= t);
    if (!seg || seg.confirmedStart) return;
    const prevEnd = this.endBefore(seg);
    const heard = Math.max(t + HEARD_AFTER_EVENT_MS, prevEnd ?? 0);
    if (prevEnd === null || prevEnd < t) {
      // Tavus was quiet before this: a clean sample of its delay.
      const sample = heard - (seg.sentAt ?? heard);
      if (sample > 200 && sample < 4000) this.delayMs = Math.round(this.delayMs * 0.5 + sample * 0.5);
    }
    seg.heardStart = heard;
    seg.confirmedStart = true;
  }

  private onStopped(t: number, interrupted: boolean): void {
    if (interrupted) {
      for (const seg of this.order) {
        const start = this.startOf(seg);
        if (!seg.complete && start !== null && start <= t) seg.dropped = true;
      }
    } else {
      for (const seg of this.order) {
        if (seg.complete || seg.dropped || !seg.ended || seg.sentAt === null) continue;
        const end = this.endOf(seg);
        if (end !== null && end <= t + END_TOLERANCE_MS) this.complete(seg);
      }
    }
    this.release();
  }

  // --- for the screen ------------------------------------------------------------------

  /** How much of a segment the customer has heard, for captions (-1 before it starts). */
  playedMs(segment: number): number {
    const seg = this.segs.get(segment);
    if (!seg) return -1;
    const total = durationMs(seg.samples);
    if (seg.complete) return total;
    const start = this.startOf(seg);
    if (start === null) return -1;
    const t = this.now();
    return t < start ? -1 : Math.min(total, t - start);
  }

  /** Call every ~50 ms: sends coalesced audio, applies fallbacks, returns newly finished
   *  segments (to report to the voice agent as played in full). */
  tick(): Completed[] {
    for (const turn of this.turns) if (!turn.finished) this.flush(turn);
    const t = this.now();
    for (const seg of this.order) {
      if (seg.complete || seg.dropped || !seg.ended || seg.kind === "confirm") continue;
      const end = this.endOf(seg);
      if (end !== null && t > end + FALLBACK_COMPLETE_MS) this.complete(seg);
    }
    // A previous turn that never reported its end doesn't hold the next one forever.
    const blocker = this.turns.find((x) => !x.finished && x.closed);
    if (blocker) {
      const last = [...blocker.segments].reverse().find((s) => !s.dropped);
      const end = last ? this.endOf(last) : null;
      if (end === null || t > end + PREVIOUS_TURN_TIMEOUT_MS) {
        blocker.finished = true;
        this.release();
      }
    }
    this.prune();
    const out = this.completed;
    this.completed = [];
    return out;
  }

  /** Nothing waiting to be heard: a good moment to switch audio back to the local player. */
  get idle(): boolean {
    return this.order.every((s) => s.complete || s.dropped) && this.turns.every((x) => x.finished || x.segments.length === 0);
  }

  // --- internals -----------------------------------------------------------------------

  private attach(seg: Seg): Turn {
    let turn = this.current;
    if (!turn || turn.closed) {
      turn = { id: this.newId(), segments: [], pending: [], held: [], started: false, closed: false, finished: false };
      this.turns.push(turn);
      this.current = turn;
    }
    turn.segments.push(seg);
    seg.turn = turn;
    return turn;
  }

  private flush(turn: Turn): void {
    if (turn.pending.length === 0 || turn.finished) return;
    const merged = concat(turn.pending);
    turn.pending = [];
    this.emit(turn, merged, false);
  }

  private emit(turn: Turn, pcm: Int16Array, done: boolean): void {
    const msg: EchoMessage = {
      message_type: "conversation",
      event_type: "conversation.echo",
      conversation_id: this.conversationId,
      properties: { modality: "audio", audio: pcmBase64(pcm), sample_rate: SPEECH_RATE, inference_id: turn.id, done },
    };
    if (this.blocked(turn)) {
      turn.held.push(msg);
      return;
    }
    this.transmit(turn, msg);
  }

  private transmit(turn: Turn, msg: EchoMessage): void {
    const t = this.now();
    turn.started = true;
    for (const seg of turn.segments) if (seg.sentAt === null && seg.samples > 0) seg.sentAt = t;
    this.send(msg);
  }

  /** A turn waits while an earlier one is still playing. */
  private blocked(turn: Turn): boolean {
    for (const other of this.turns) {
      if (other === turn) return false;
      if (!other.finished) return true;
    }
    return false;
  }

  private release(): void {
    for (const turn of this.turns) {
      if (turn.finished) continue;
      if (turn.closed && turn.segments.every((s) => s.complete || s.dropped)) {
        turn.finished = true;
        continue;
      }
      if (this.blocked(turn)) return;
      const held = turn.held;
      turn.held = [];
      for (const msg of held) this.transmit(turn, msg);
      return;
    }
  }

  private complete(seg: Seg): void {
    const end = this.endOf(seg);
    seg.endAt = end === null ? this.now() : Math.min(end, this.now());
    seg.complete = true;
    this.completed.push({ segment: seg.segment, playedMs: Math.round(durationMs(seg.samples)) });
  }

  private startOf(seg: Seg): number | null {
    if (seg.heardStart !== null && seg.confirmedStart) return seg.heardStart;
    if (seg.sentAt === null) return null;
    const prevEnd = this.endBefore(seg);
    return Math.max(seg.sentAt + this.delayMs, prevEnd ?? 0);
  }

  private endOf(seg: Seg): number | null {
    if (seg.endAt !== null) return seg.endAt;
    const start = this.startOf(seg);
    return start === null ? null : start + durationMs(seg.samples);
  }

  private endBefore(seg: Seg): number | null {
    const i = this.order.indexOf(seg);
    for (let j = i - 1; j >= 0; j--) {
      const prev = this.order[j]!;
      if (prev.dropped || prev.sentAt === null) continue;
      return this.endOf(prev);
    }
    return null;
  }

  /** Forget what's long finished, keeping the last one as the timeline's anchor. */
  private prune(): void {
    while (this.turns.length > 1 && this.turns[0]!.finished) this.turns.shift();
    while (this.order.length > 1) {
      const first = this.order[0]!;
      const next = this.order[1]!;
      if (!(first.complete || first.dropped) || !(next.complete || next.dropped)) break;
      this.order.shift();
      this.segs.delete(first.segment);
    }
    return null;
  }
}

function durationMs(samples: number): number {
  return (samples / SPEECH_RATE) * 1000;
}

function pendingMs(turn: Turn): number {
  return durationMs(turn.pending.reduce((n, p) => n + p.length, 0));
}

function concat(parts: Int16Array[]): Int16Array {
  if (parts.length === 1) return parts[0]!;
  const out = new Int16Array(parts.reduce((n, p) => n + p.length, 0));
  let o = 0;
  for (const p of parts) {
    out.set(p, o);
    o += p.length;
  }
  return out;
}
