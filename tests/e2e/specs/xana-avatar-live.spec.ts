import { expect, type Page, test } from "@playwright/test";
import { ALICE, signInFromScratch } from "./helpers";

// Xena's spoken confirmation and barge-in with her Tavus face on, and the same with it off
// (docs/features/10-xana-avatar, phase A3), plus the timings for A4. Real OpenAI, Cartesia,
// and Tavus: Tavus bills per minute (about two minutes a run), so it runs only when asked.
//
// Turns are typed into the call's socket: a typed turn goes through the same read-back rule as
// a spoken one. The store's confirmation endpoint is stubbed, so a "yes" never creates a return.

const LIVE = process.env.TAVUS_E2E_LIVE === "1";
const RETURN_ASK = "I'd like to return the Arc over-ear headphones";

test.use({
  trace: "off",
  video: "off",
  viewport: { width: 1280, height: 1000 },
  launchOptions: { args: ["--autoplay-policy=no-user-gesture-required"] },
});

type Event = { at: number; type: string; msg: Record<string, unknown> };

class Call {
  events: Event[] = [];
  sent: Event[] = [];
  audioFrames: number[] = [];
  levels: { at: number; on: boolean }[] = [];
  confirmCalls = 0;

  constructor(readonly page: Page) {}

  since(at: number, type: string, match: (m: Record<string, unknown>) => boolean = () => true) {
    return this.events.find((e) => e.at >= at && e.type === type && match(e.msg));
  }

  async next(at: number, type: string, match?: (m: Record<string, unknown>) => boolean, timeout = 30_000) {
    await expect.poll(() => Boolean(this.since(at, type, match)), { timeout, message: `waiting for ${type}` }).toBe(true);
    return this.since(at, type, match)!;
  }

  async say(text: string): Promise<number> {
    const at = Date.now();
    await this.page.evaluate((t) => {
      (window as unknown as { xenaTestSocket: WebSocket }).xenaTestSocket.send(JSON.stringify({ type: "text", text: t }));
    }, text);
    return at;
  }

  async interrupt(): Promise<number> {
    const at = Date.now();
    await this.page.evaluate(() => {
      (window as unknown as { xenaTestSocket: WebSocket }).xenaTestSocket.send(JSON.stringify({ type: "interrupt" }));
    });
    return at;
  }

  async listening(at: number) {
    await this.next(at, "state", (m) => m.state === "listening", 45_000);
  }

  /** When her face's audio first went loud after `at` (video on only). */
  heardAfter(at: number) {
    return this.levels.find((l) => l.at >= at && l.on)?.at;
  }
}

async function openCall(page: Page, video: boolean): Promise<Call> {
  const call = new Call(page);
  await page.exposeFunction("xenaLevel", (on: boolean, at: number) => call.levels.push({ on, at }));
  await page.route("**/v1/returns/quotes/*/confirmation", (route) => {
    call.confirmCalls += 1;
    return route.fulfill({ status: 503, json: { detail: "stubbed by the test" } });
  });
  page.on("websocket", (socket) => {
    if (new URL(socket.url()).pathname !== "/v1/voice/xana") return;
    socket.on("framereceived", ({ payload }) => {
      const at = Date.now();
      if (typeof payload !== "string") {
        call.audioFrames.push(at);
        return;
      }
      try {
        const msg = JSON.parse(payload);
        if (msg.type) call.events.push({ at, type: msg.type, msg });
      } catch {}
    });
    socket.on("framesent", ({ payload }) => {
      if (typeof payload !== "string") return;
      try {
        const msg = JSON.parse(payload);
        if (msg.type) call.sent.push({ at: Date.now(), type: msg.type, msg });
      } catch {}
    });
  });
  await page.addInitScript(() => {
    // A silent microphone: every turn in this test is typed.
    navigator.mediaDevices.getUserMedia = async () => new AudioContext({ sampleRate: 24000 }).createMediaStreamDestination().stream;
    const NativeSocket = window.WebSocket;
    window.WebSocket = class extends NativeSocket {
      constructor(url: string | URL, protocols?: string | string[]) {
        super(url, protocols);
        if (new URL(String(url)).pathname === "/v1/voice/xana") {
          (window as unknown as { xenaTestSocket: WebSocket }).xenaTestSocket = this;
        }
      }
    };
    // Is her face's audio loud right now? Reported on each change; quiet only after 300 ms.
    const report = (window as unknown as { xenaLevel: (on: boolean, at: number) => void });
    let ctx: AudioContext | null = null;
    let analyser: AnalyserNode | null = null;
    let source: MediaStream | null = null;
    let on = false;
    let quietSince = 0;
    setInterval(() => {
      const el = document.querySelector("video");
      const stream = el?.srcObject instanceof MediaStream ? el.srcObject : null;
      if (stream !== source) {
        source = stream;
        analyser = null;
        if (stream && stream.getAudioTracks().length) {
          ctx ??= new AudioContext();
          analyser = ctx.createAnalyser();
          analyser.fftSize = 512;
          ctx.createMediaStreamSource(stream).connect(analyser);
        }
      }
      if (!analyser) return;
      const buf = new Float32Array(analyser.fftSize);
      analyser.getFloatTimeDomainData(buf);
      const rms = Math.sqrt(buf.reduce((s, v) => s + v * v, 0) / buf.length);
      const now = Date.now();
      if (rms > 0.01) {
        quietSince = 0;
        if (!on) { on = true; report.xenaLevel(true, now); }
      } else if (on) {
        quietSince ||= now;
        if (now - quietSince >= 300) { on = false; report.xenaLevel(false, quietSince); }
      }
    }, 10);
  });
  await signInFromScratch(page, ALICE);
  await page.goto("/support/voice");
  await page.getByRole("button", { name: "Start talking", exact: true }).click();
  const ready = await call.next(0, "ready");
  await call.next(0, "state", (m) => m.state === "listening");
  if (video) {
    expect((ready.msg.avatars as Record<string, { available?: boolean }>)?.tavus?.available).toBe(true);
    await page.getByRole("button", { name: "Video", exact: true }).click();
    const el = page.locator("video");
    await expect.poll(() => el.evaluate((v: HTMLVideoElement) => v.videoWidth > 0 && !v.paused && v.readyState >= 2)
      .catch(() => false), { timeout: 45_000 }).toBe(true);
    await expect.poll(() => call.sent.some((e) => e.type === "avatar.playing"), { timeout: 15_000 }).toBe(true);
  }
  return call;
}

async function hangUp(page: Page) {
  await page.getByRole("link", { name: "Close voice assistant" }).click();
  await expect(page).toHaveURL(/\/support$/);
}

/** The read-back segment of the quote that arrived after `at`, once it has started playing. */
async function readBack(call: Call, at: number) {
  await call.next(at, "quote", undefined, 60_000);
  const seg = await call.next(at, "segment.start", (m) => m.kind === "confirm", 30_000);
  return seg.msg.segment as number;
}

async function confirmationAndBargeIn(page: Page, video: boolean) {
  const call = await openCall(page, video);
  try {
    await steps(page, call, video);
  } catch (e) {
    // What the call looked like, for the failure report.
    const t0 = call.events[0]?.at ?? 0;
    const line = (dir: string) => (e: Event) => `${((e.at - t0) / 1000).toFixed(2)} ${dir} ${e.type} ${JSON.stringify(e.msg).slice(0, 140)}`;
    const all = [...call.events.map(line("<-")), ...call.sent.map(line("->"))].sort((a, b) => parseFloat(a) - parseFloat(b));
    console.log(all.filter((l) => !/segment\.words|segment\.text/.test(l)).join("\n"));
    throw e;
  }
}

async function steps(page: Page, call: Call, video: boolean) {
  const timings: Record<string, number | undefined>[] = [];

  // A4: first words, a few times.
  for (const q of ["Where is my most recent order?", "What time does the Uptown store close today?"]) {
    const at = await call.say(q);
    const first = await call.next(at, "segment.start");
    await expect.poll(() => call.audioFrames.some((t) => t >= at), { timeout: 30_000 }).toBe(true);
    const frame = call.audioFrames.find((t) => t >= at)!;
    if (video) await expect.poll(() => call.heardAfter(frame), { timeout: 15_000 }).toBeDefined();
    const heard = video ? call.heardAfter(frame) : undefined;
    timings.push({
      first_segment_ms: first.at - at,
      first_audio_ms: frame - at,
      heard_ms: heard && heard - at,
      face_adds_ms: heard && heard - frame,
    });
    await call.listening(at);
  }

  // A yes while she's still reading the quote back is unclear: no confirmation.
  let at = await call.say(RETURN_ASK);
  const early = await readBack(call, at);
  if (video) await expect.poll(() => call.heardAfter(call.since(at, "segment.start", (m) => m.segment === early)!.at),
    { timeout: 20_000 }).toBeDefined();
  else await page.waitForTimeout(800);
  expect(call.sent.some((e) => e.type === "played" && e.msg.segment === early && e.msg.complete)).toBe(false);
  let yes = await call.say("yes");
  const unclear = await call.next(yes, "confirm.result");
  expect(unclear.msg.decision).toBe("unclear");
  await call.listening(yes);
  expect(call.confirmCalls).toBe(0);

  // A new quote, heard in full this time: now a yes confirms (through the browser, stubbed).
  at = await call.say("Okay, let's start over. " + RETURN_ASK);
  const full = await readBack(call, at);
  await expect.poll(() => call.sent.some((e) => e.type === "played" && e.msg.segment === full && e.msg.complete),
    { timeout: 45_000, message: "the read-back reported heard in full" }).toBe(true);
  const heardAt = call.sent.find((e) => e.type === "played" && e.msg.segment === full)!.at;
  if (video) {
    // Heard in full means her face finished it, not just that our server finished sending it.
    const end = call.since(at, "segment.end", (m) => m.segment === full);
    expect(end && heardAt > end.at).toBe(true);
  }
  await call.listening(at);
  yes = await call.say("yes");
  const confirmed = await call.next(yes, "confirm.result");
  expect(confirmed.msg.decision).toBe("yes");
  await expect.poll(() => call.confirmCalls, { timeout: 10_000 }).toBe(1);
  await call.listening(yes);

  // Barge-in: talking over her stops her, and what she hadn't said is dropped.
  at = await call.say("Tell me everything about how returns work for electronics, in detail.");
  const answer = await call.next(at, "segment.start", (m) => m.kind === "answer", 45_000);
  if (video) {
    // Into the answer (not the filler before it), and mid-word.
    await expect.poll(() => call.heardAfter(answer.at), { timeout: 20_000 }).toBeDefined();
    await page.waitForTimeout(1000);
    await expect.poll(() => call.levels.at(-1)?.on, { timeout: 5_000 }).toBe(true);
  } else {
    await expect.poll(() => call.audioFrames.filter((t) => t >= at).length > 20, { timeout: 20_000 }).toBe(true);
  }
  const cut = await call.interrupt();
  const drop = await call.next(cut, "drop", undefined, 5_000);
  let quiet: number | undefined;
  if (video) {
    await expect.poll(() => call.levels.find((l) => l.at >= cut - 300 && !l.on), { timeout: 5_000 }).toBeDefined();
    quiet = call.levels.find((l) => l.at >= cut - 300 && !l.on)!.at;
    expect(quiet - cut).toBeLessThan(1500);
  }
  // She stops and listens to the customer (an interrupt is what talking over her sends).
  await call.next(cut, "state", (m) => m.state === "hearing", 5_000);
  const timing = { drop_ms: drop.at - cut, quiet_ms: quiet && quiet - cut };

  console.log(`video ${video ? "on" : "off"}:`, JSON.stringify({ first_words: timings, barge_in: timing }));
  if (video) {
    await page.getByRole("button", { name: "Video off", exact: true }).click();
    await expect(page.locator("video")).toHaveCount(0);
  }
  await hangUp(page);
}

test("with video on, a yes counts only after her face finished the read-back; barge-in stops her", async ({ page }) => {
  test.skip(!LIVE, "set TAVUS_E2E_LIVE=1 (real Tavus minutes, OpenAI, and Cartesia)");
  test.setTimeout(240_000);
  await confirmationAndBargeIn(page, true);
});

test("with video off, the same rules hold", async ({ page }) => {
  test.skip(!LIVE, "set TAVUS_E2E_LIVE=1 (real OpenAI and Cartesia)");
  test.setTimeout(240_000);
  await confirmationAndBargeIn(page, false);
});
