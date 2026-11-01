// Records a real Xena voice call on the local :3100 stack: the customer's question goes in as a
// virtual microphone, and the screen (CDP screencast, timestamped) and everything the page plays
// (Xena's voice, the avatar's audio, the question) are captured, then muxed with ffmpeg.
//
//   node record.mjs voice   -> out/voice/   (orb only)
//   node record.mjs avatar  -> out/avatar/  (Tavus video on before the question)
import { createRequire } from "node:module";
import { mkdirSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require(
  "C:/Users/taro/Documents/TEMP/Walmart App/ai-commerce/.claude/worktrees/integration/tests/e2e/node_modules/@playwright/test",
);
const here = dirname(fileURLToPath(import.meta.url));
//   node record.mjs voice q1.wav,q2.wav,q3.wav voice30   -> several questions, out/voice30/
const mode = process.argv[2] ?? "voice";
const out = join(here, "out", process.argv[4] ?? mode);
rmSync(out, { recursive: true, force: true });
mkdirSync(join(out, "frames"), { recursive: true });
const BASE = "http://localhost:3100";
const questions = (process.argv[3] ?? "question.wav")
  .split(",")
  .map((f) => readFileSync(join(here, f)).toString("base64"));
const log = (...a) => console.log(new Date().toISOString().slice(11, 23), ...a);

const INIT = () => {
  const RealAC = window.AudioContext;
  const master = { ctx: null, dest: null, chunks: [], rec: null };
  const ensure = () => {
    if (!master.ctx) {
      master.ctx = new RealAC({ sampleRate: 48000 });
      master.ctx.__noTap = true;
      master.dest = master.ctx.createMediaStreamDestination();
    }
    return master;
  };
  const taps = new WeakMap();
  const fedTracks = new Set();
  const origConnect = AudioNode.prototype.connect;
  const feed = (stream) => {
    const m = ensure();
    for (const track of stream.getAudioTracks()) {
      if (fedTracks.has(track.id)) continue;
      fedTracks.add(track.id);
      const source = m.ctx.createMediaStreamSource(new MediaStream([track]));
      const gain = m.ctx.createGain();
      gain.gain.value = 0.35;
      origConnect.call(source, gain);
      origConnect.call(gain, m.dest);
      track.addEventListener("ended", () => fedTracks.delete(track.id), { once: true });
    }
  };
  // Everything a page context plays to its speakers also goes to the recording.
  AudioNode.prototype.connect = function (target, ...rest) {
    const r = origConnect.call(this, target, ...rest);
    if (target instanceof AudioDestinationNode && !this.context.__noTap) {
      let tap = taps.get(this.context);
      if (!tap) {
        tap = this.context.createMediaStreamDestination();
        taps.set(this.context, tap);
        feed(tap.stream);
      }
      try { origConnect.call(this, tap); } catch {}
    }
    return r;
  };
  // The avatar's audio arrives as a WebRTC stream on a <video>.
  const desc = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, "srcObject");
  Object.defineProperty(HTMLMediaElement.prototype, "srcObject", {
    configurable: true,
    get() { return desc.get.call(this); },
    set(v) {
      desc.set.call(this, v);
      if (v && typeof v.getAudioTracks === "function") {
        const seen = new Set();
        const add = (t) => { if (t.kind === "audio" && !seen.has(t.id)) { seen.add(t.id); feed(new MediaStream([t])); } };
        v.getAudioTracks().forEach(add);
        v.addEventListener("addtrack", (e) => add(e.track));
      }
    },
  });
  // The microphone: silence until the demo speaks the question.
  const mic = new RealAC({ sampleRate: 48000 });
  mic.__noTap = true;
  const micDest = mic.createMediaStreamDestination();
  let fedMic = false;
  const origGUM = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
  navigator.mediaDevices.getUserMedia = async (c) => {
    if (c && c.audio) {
      await mic.resume();
      return new MediaStream([micDest.stream.getAudioTracks()[0].clone()]);
    }
    return origGUM(c);
  };
  window.__demo = {
    startRec() {
      const m = ensure();
      void m.ctx.resume();
      // A silent source keeps the track running from the start, so the recording's time zero
      // is now (otherwise it starts at the first sound and drifts from the video).
      const hum = m.ctx.createConstantSource();
      hum.offset.value = 0;
      origConnect.call(hum, m.dest);
      hum.start();
      m.rec = new MediaRecorder(m.dest.stream, { mimeType: "audio/webm;codecs=opus", audioBitsPerSecond: 160000 });
      m.rec.ondataavailable = (e) => e.data.size && m.chunks.push(e.data);
      m.rec.start(250);
      return Date.now();
    },
    async say(b64) {
      const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
      const buf = await mic.decodeAudioData(bytes.buffer);
      if (!fedMic) { fedMic = true; feed(micDest.stream); }
      const src = mic.createBufferSource();
      src.buffer = buf;
      src.connect(micDest);
      src.start();
      return { at: Date.now(), seconds: buf.duration };
    },
    async stopRec() {
      const m = master;
      await new Promise((ok) => { m.rec.onstop = ok; m.rec.stop(); });
      const blob = new Blob(m.chunks, { type: "audio/webm" });
      const b = new Uint8Array(await blob.arrayBuffer());
      let s = "";
      for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode(...b.subarray(i, i + 0x8000));
      return btoa(s);
    },
  };
};

const browser = await chromium.launch({
  headless: true,
  args: ["--autoplay-policy=no-user-gesture-required", "--use-fake-ui-for-media-stream"],
});
const context = await browser.newContext({
  viewport: { width: 1600, height: 900 },
  deviceScaleFactor: 1.2,
  permissions: ["microphone", "camera"],
});
await context.addInitScript(INIT);
const page = await context.newPage();
page.on("console", (m) => { if (m.type() === "error" || m.type() === "warning") log("page", m.type(), m.text().slice(0, 200)); });
const signIn = await page.request.post(`${BASE}/api/v1/auth/sign-in`, {
  data: { email: "alice@example.com", password: "alice-dev-password" },
});
if (!signIn.ok()) throw new Error(`sign-in ${signIn.status()}`);
await page.goto(`${BASE}/support/voice`, { waitUntil: "networkidle" });
await page.getByRole("button", { name: "Start talking", exact: true }).waitFor({ timeout: 30000 });
// The Next.js dev-tools badge is not part of the app.
await page.addStyleTag({ content: "nextjs-portal{display:none!important}" });

// Screencast with wall-clock timestamps (the same clock as Date.now() in the page).
const cdp = await context.newCDPSession(page);
const frames = [];
cdp.on("Page.screencastFrame", async ({ data, metadata, sessionId }) => {
  const file = join(out, "frames", `${String(frames.length).padStart(5, "0")}.jpg`);
  writeFileSync(file, Buffer.from(data, "base64"));
  frames.push({ file, t: metadata.timestamp * 1000 });
  await cdp.send("Page.screencastFrameAck", { sessionId }).catch(() => {});
});
await cdp.send("Page.startScreencast", { format: "jpeg", quality: 92, maxWidth: 1920, maxHeight: 1080 });
const recAt = await page.evaluate(() => window.__demo.startRec());
const marks = { recAt };
await page.waitForTimeout(4000);

marks.start = Date.now();
await page.getByRole("button", { name: "Start talking", exact: true }).click();
log("start");
try {
  await page.getByText("Listening", { exact: true }).first().waitFor({ timeout: 30000 });
} catch (e) {
  await page.screenshot({ path: join(out, "stuck.png") });
  log("stuck:", (await page.locator("body").innerText()).slice(0, 600).replace(/\s+/g, " "));
  throw e;
}
log("listening");

if (mode === "avatar") {
  const video = page.getByRole("button", { name: /^Video$/ });
  await video.waitFor({ timeout: 30000 });
  await page.waitForTimeout(600);
  marks.videoClick = Date.now();
  await video.click();
  log("video on");
  // Live when her <video> has frames.
  await page.waitForFunction(
    () => [...document.querySelectorAll("video")].some((v) => v.readyState >= 3 && v.videoWidth > 0 && !v.paused),
    null,
    { timeout: 90000, polling: 250 },
  );
  marks.avatarLive = Date.now();
  log("avatar live");
  await page.waitForTimeout(2500);
} else {
  await page.waitForTimeout(1500);
}

marks.turns = [];
for (const [i, q] of questions.entries()) {
  const said = await page.evaluate((b64) => window.__demo.say(b64), q);
  if (i === 0) {
    marks.question = said.at;
    marks.questionSeconds = said.seconds;
  }
  log(`question ${i + 1}`, said.seconds.toFixed(2), "s");
  await page.getByText("Speaking", { exact: true }).first().waitFor({ timeout: 45000 });
  const speaking = Date.now();
  log("speaking");
  await page.getByText("Listening", { exact: true }).first().waitFor({ timeout: 60000 });
  marks.done = Date.now();
  marks.turns.push({ question: said.at, speaking, done: marks.done });
  log("done");
  // The next question comes as soon as she's finished, like a customer would.
  await page.waitForTimeout(i + 1 < questions.length ? 0 : 1500);
}
marks.end = Date.now();

const audio = await page.evaluate(() => window.__demo.stopRec());
await cdp.send("Page.stopScreencast");
writeFileSync(join(out, "audio.webm"), Buffer.from(audio, "base64"));
writeFileSync(join(out, "marks.json"), JSON.stringify({ ...marks, frames: frames.map((f) => f.t) }, null, 1));
// ffmpeg concat list: each frame shown until the next one.
const lines = [];
for (let i = 0; i < frames.length; i++) {
  const next = i + 1 < frames.length ? frames[i + 1].t : marks.end;
  lines.push(`file '${frames[i].file.replaceAll("\\", "/")}'`, `duration ${((next - frames[i].t) / 1000).toFixed(4)}`);
}
lines.push(`file '${frames.at(-1).file.replaceAll("\\", "/")}'`);
writeFileSync(join(out, "frames.txt"), lines.join("\n"));
log(`frames ${frames.length}; first frame ${frames[0].t - recAt} ms after audio start`);
await page.getByRole("button", { name: /Close voice assistant/ }).click().catch(() => {});
await page.waitForTimeout(500);
await browser.close();
