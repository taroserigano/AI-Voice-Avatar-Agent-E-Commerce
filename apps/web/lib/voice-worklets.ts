/**
 * The two audio worklets for the voice screen, as source text (loaded from a Blob URL, so
 * they need no public route and no bundler support).
 *
 * capture:  microphone → PCM16 mono at the target rate, in 20 ms frames, plus a level (RMS)
 *           for the orb. Resamples from whatever rate the device runs at.
 * playback: a gapless queue of PCM16 segments. It reports progress per segment (how many ms
 *           have played, which drives the captions), when a segment finishes, and the output
 *           level. `drop` removes segments at once (barge-in), mid-sample.
 */

export const CAPTURE_WORKLET = `
class Capture extends AudioWorkletProcessor {
  constructor(options) {
    super();
    this.target = options.processorOptions.targetRate;
    this.ratio = sampleRate / this.target;
    this.frame = Math.round(this.target / 50);
    this.buf = new Int16Array(this.frame);
    this.n = 0;
    this.pos = 0;
    this.sum = 0;
    this.count = 0;
    this.muted = false;
    this.port.onmessage = (e) => { if (e.data && e.data.type === 'mute') this.muted = e.data.muted; };
  }
  process(inputs) {
    const input = inputs[0] && inputs[0][0];
    if (!input) return true;
    for (let i = 0; i < input.length; i++) { this.sum += input[i] * input[i]; this.count++; }
    // Linear-interpolation resampler from the device rate to the target rate.
    while (this.pos < input.length - 1) {
      const i = Math.floor(this.pos);
      const f = this.pos - i;
      const s = input[i] * (1 - f) + input[i + 1] * f;
      const v = this.muted ? 0 : Math.max(-1, Math.min(1, s));
      this.buf[this.n++] = v < 0 ? v * 0x8000 : v * 0x7fff;
      if (this.n === this.frame) {
        const level = Math.sqrt(this.sum / Math.max(1, this.count));
        this.sum = 0; this.count = 0;
        if (!this.muted) this.port.postMessage({ pcm: this.buf.buffer, level }, [this.buf.buffer]);
        else this.port.postMessage({ level: 0 });
        this.buf = new Int16Array(this.frame);
        this.n = 0;
      }
      this.pos += this.ratio;
    }
    this.pos -= input.length;
    return true;
  }
}
registerProcessor('xana-capture', Capture);
`;

export const PLAYBACK_WORKLET = `
class Playback extends AudioWorkletProcessor {
  constructor() {
    super();
    this.queue = [];      // [{segment, data: Float32Array, off}]
    this.ended = new Set(); // segments whose last audio has arrived
    this.played = new Map(); // segment -> samples played
    this.dropped = new Set();
    this.current = -1;
    this.tick = 0;
    this.sum = 0;
    this.port.onmessage = (e) => {
      const m = e.data;
      if (m.type === 'audio') {
        if (this.dropped.has(m.segment)) return;
        const pcm = new Int16Array(m.pcm);
        const data = new Float32Array(pcm.length);
        for (let i = 0; i < pcm.length; i++) data[i] = pcm[i] / 0x8000;
        this.queue.push({ segment: m.segment, data, off: 0 });
      } else if (m.type === 'end') {
        this.ended.add(m.segment);
        this.finishIfDrained(m.segment);
      } else if (m.type === 'drop') {
        for (const s of m.segments) this.dropped.add(s);
        this.queue = this.queue.filter((q) => !this.dropped.has(q.segment));
      }
    };
  }
  finishIfDrained(segment) {
    if (!this.ended.has(segment)) return;
    if (this.queue.some((q) => q.segment === segment)) return;
    this.ended.delete(segment);
    this.port.postMessage({ type: 'done', segment, playedMs: this.ms(segment) });
    this.played.delete(segment);
  }
  ms(segment) { return Math.round(((this.played.get(segment) || 0) / sampleRate) * 1000); }
  process(_inputs, outputs) {
    const out = outputs[0][0];
    let i = 0;
    while (i < out.length && this.queue.length) {
      const q = this.queue[0];
      if (q.segment !== this.current) {
        this.current = q.segment;
        this.port.postMessage({ type: 'start', segment: q.segment });
      }
      const n = Math.min(out.length - i, q.data.length - q.off);
      for (let k = 0; k < n; k++) { const v = q.data[q.off + k]; out[i + k] = v; this.sum += v * v; }
      q.off += n; i += n;
      this.played.set(q.segment, (this.played.get(q.segment) || 0) + n);
      if (q.off >= q.data.length) { this.queue.shift(); this.finishIfDrained(q.segment); }
    }
    for (; i < out.length; i++) out[i] = 0;
    for (let c = 1; c < outputs[0].length; c++) outputs[0][c].set(out);
    // Progress about every 32 ms: which segment is playing, how far in, and the level.
    if (++this.tick % 6 === 0) {
      const level = Math.sqrt(this.sum / (out.length * 6));
      this.sum = 0;
      const seg = this.queue.length ? this.queue[0].segment : -1;
      this.port.postMessage({ type: 'progress', segment: seg, playedMs: seg >= 0 ? this.ms(seg) : 0, level, idle: this.queue.length === 0 });
    }
    return true;
  }
}
registerProcessor('xana-playback', Playback);
`;

export async function addWorklet(ctx: AudioContext, source: string): Promise<void> {
  const url = URL.createObjectURL(new Blob([source], { type: "text/javascript" }));
  try {
    await ctx.audioWorklet.addModule(url);
  } finally {
    URL.revokeObjectURL(url);
  }
}
