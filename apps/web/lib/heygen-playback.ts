import { pcmBase64, type Completed } from "./avatar-echo";
import type { AvatarPlayback } from "./avatar-playback";
import { SPEECH_RATE } from "./voice-protocol";

export type LiveAvatarCommand = { type: string; event_id?: string; audio?: string };
type Segment = {
  number: number; id: string; samples: number; pending: Int16Array[];
  sealed: boolean; committed: boolean; sent: boolean; started: number | null; ended: number | null;
};

/**
 * One utterance per segment, matched by source_event_id. Buffer acknowledgements never
 * complete playback. Captions use an estimate; server-side spoken confirmation is disabled
 * for this provider until end-to-end playout timing is measured.
 */
export class HeygenPlayback implements AvatarPlayback {
  private queue: Segment[] = [];
  private finished = new Map<number, number>();
  private awaitingSince: number | null = null;
  constructor(private opts: {
    send: (msg: LiveAvatarCommand) => void;
    fail: () => void;
    now?: () => number;
    newId?: () => string;
  }) {}
  private now() { return this.opts.now?.() ?? performance.now(); }
  get idle() { return this.queue.length === 0; }
  segmentStart(number: number, _kind: "filler" | "answer" | "confirm") {
    void _kind; // Confirmation permission lives on the server for this provider.
    this.queue.push({
      number, id: this.opts.newId?.() ?? crypto.randomUUID(), samples: 0,
      pending: [], sealed: false, committed: false, sent: false, started: null, ended: null,
    });
  }
  audio(number: number, pcm: Int16Array) {
    const seg = this.queue.find((s) => s.number === number);
    if (!seg || !pcm.length) return;
    // Bound held audio even if the provider stops acknowledging playback.
    if (this.queue.reduce((n, s) => n + s.samples, 0) + pcm.length > SPEECH_RATE * 90) {
      this.opts.fail();
      return;
    }
    seg.samples += pcm.length;
    for (let i = 0; i < pcm.length; i += SPEECH_RATE) seg.pending.push(pcm.slice(i, i + SPEECH_RATE));
    this.flush();
  }
  segmentEnd(number: number) {
    const seg = this.queue.find((s) => s.number === number);
    if (seg) seg.sealed = true;
    this.flush();
  }
  turnDone() { this.flush(); }
  private flush() {
    const seg = this.queue[0];
    if (!seg) return;
    const pendingSamples = seg.pending.reduce((n, p) => n + p.length, 0);
    if (!seg.sent || seg.sealed || pendingSamples >= SPEECH_RATE) {
      const pending = seg.pending.splice(0);
      const all = new Int16Array(pendingSamples);
      let offset = 0;
      for (const pcm of pending) { all.set(pcm, offset); offset += pcm.length; }
      for (let i = 0; i < all.length; i += SPEECH_RATE) {
        this.opts.send({ type: "agent.speak", event_id: seg.id, audio: pcmBase64(all.subarray(i, i + SPEECH_RATE)) });
        if (!seg.sent) this.awaitingSince = this.now();
        seg.sent = true;
      }
    }
    if (seg.sealed && seg.sent && seg.pending.length === 0 && !seg.committed) {
      this.opts.send({ type: "agent.speak_end", event_id: seg.id });
      seg.committed = true;
    }
    if (seg.sealed && !seg.samples) {
      this.finished.set(seg.number, 0);
      this.queue.shift();
      this.flush();
    }
  }
  onEvent(event: Record<string, unknown>) {
    const seg = this.queue[0];
    if (!seg || event.source_event_id !== seg.id) return;
    if (event.type === "agent.speak_started" && seg.started === null) seg.started = this.now();
    if (event.type === "agent.speak_ended" && seg.sealed && seg.sent && seg.started !== null) {
      seg.ended = this.now();
    }
    if (event.type === "agent.speak_interrupted") this.opts.fail();
  }
  playedMs(number: number) {
    const seg = this.queue.find((s) => s.number === number);
    if (!seg) return this.finished.get(number) ?? 0;
    return seg.started === null ? 0 : Math.min(seg.samples / 24, Math.max(0, this.now() - seg.started - 200));
  }
  tick(): Completed[] {
    const seg = this.queue[0];
    if (!seg) return [];
    if (this.awaitingSince !== null && this.now() - this.awaitingSince > seg.samples / 24 + 15_000) {
      this.opts.fail();
      return [];
    }
    if (seg.ended === null || seg.ended < 0 || seg.started === null ||
        this.now() < Math.max(seg.ended + 350, seg.started + seg.samples / 24 + 350)) return [];
    const playedMs = seg.samples / 24;
    this.finished.set(seg.number, playedMs);
    if (this.finished.size > 100) this.finished.delete(this.finished.keys().next().value!);
    this.queue.shift();
    this.awaitingSince = null;
    this.flush();
    return [{ segment: seg.number, playedMs }];
  }
  drop(numbers: number[]) {
    if (!this.queue.some((s) => numbers.includes(s.number))) return;
    if (this.queue[0] && numbers.includes(this.queue[0].number)) {
      this.opts.send({ type: "agent.interrupt", event_id: this.opts.newId?.() ?? crypto.randomUUID() });
      this.awaitingSince = null;
    }
    this.queue = this.queue.filter((s) => !numbers.includes(s.number));
    this.flush();
  }
}
