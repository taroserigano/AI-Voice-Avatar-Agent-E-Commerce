import { expect, test } from "@playwright/test";
import { ALICE, signInFromScratch } from "./helpers";

// Explicit opt-in: a real sandbox avatar and a short real Xana/Cartesia response.
test.use({ trace: "off", video: "off", viewport: { width: 1280, height: 1000 } });
test("HeyGen sandbox receives video and speaks Xana's audio", async ({ page }, testInfo) => {
  test.skip(process.env.HEYGEN_E2E_LIVE !== "1", "set HEYGEN_E2E_LIVE=1");
  test.setTimeout(90_000);
  const clientTypes: string[] = [], providerTypes: string[] = [];
  const answerSegments = new Set<number>(), playedSegments = new Set<number>();
  let voiceState = "";
  let available = false;
  page.on("websocket", (socket) => {
    const voice = new URL(socket.url()).pathname === "/v1/voice/xana";
    socket.on("framesent", ({ payload }) => {
      if (typeof payload !== "string") return;
      try {
        const msg = JSON.parse(payload);
        if (voice && msg.type) clientTypes.push(msg.type);
        if (voice && msg.type === "played") playedSegments.add(msg.segment);
      } catch {}
    });
    socket.on("framereceived", ({ payload }) => {
      if (typeof payload !== "string") return;
      try {
        const msg = JSON.parse(payload);
        if (voice && msg.type === "ready") available = msg.avatars?.heygen?.available === true;
        if (voice && msg.type === "segment.start" && msg.kind === "answer") answerSegments.add(msg.segment);
        if (voice && msg.type === "state") voiceState = msg.state;
        if (!voice && typeof msg.type === "string") providerTypes.push(msg.type);
      } catch {}
    });
  });
  await page.addInitScript(() => {
    navigator.mediaDevices.getUserMedia = async () => {
      const ctx = new AudioContext({ sampleRate: 24000 });
      return ctx.createMediaStreamDestination().stream;
    };
    const NativeSocket = window.WebSocket;
    window.WebSocket = class extends NativeSocket {
      constructor(url: string | URL, protocols?: string | string[]) {
        super(url, protocols);
        if (new URL(String(url)).pathname === "/v1/voice/xana") {
          (window as unknown as { xanaTestSocket: WebSocket }).xanaTestSocket = this;
        }
      }
    };
  });
  await signInFromScratch(page, ALICE);
  await page.goto("/support/voice/heygen");
  await page.getByRole("button", { name: "Start talking", exact: true }).click();
  await expect.poll(() => available, { timeout: 25_000 }).toBe(true);
  await page.getByRole("button", { name: "Video", exact: true }).click();
  const video = page.locator("video");
  await expect(video).toBeVisible({ timeout: 30_000 });
  if (await page.getByRole("button", { name: "Play avatar audio" }).isVisible()) {
    await page.getByRole("button", { name: "Play avatar audio" }).click();
  }
  await expect.poll(() => video.evaluate((el: HTMLVideoElement) =>
    el.videoWidth > 0 && !el.paused && el.readyState >= 2), { timeout: 15_000 }).toBe(true);
  await expect.poll(() => clientTypes.includes("avatar.playing")).toBe(true);
  await page.evaluate(() => {
    (window as unknown as { xanaTestSocket: WebSocket }).xanaTestSocket.send(
      JSON.stringify({ type: "text", text: "Say hello in one short sentence." }),
    );
  });
  await expect.poll(() => providerTypes.includes("agent.speak_started"), { timeout: 25_000 }).toBe(true);
  await expect.poll(() => providerTypes.includes("agent.speak_ended"), { timeout: 20_000 }).toBe(true);
  await expect.poll(() => clientTypes.includes("played"), { timeout: 10_000 }).toBe(true);
  await expect.poll(() => [...answerSegments].some((n) => playedSegments.has(n)), { timeout: 20_000 }).toBe(true);
  await expect.poll(() => voiceState).toBe("listening");
  const media = await video.evaluate((el: HTMLVideoElement) => ({
    width: el.videoWidth, height: el.videoHeight, frames: el.getVideoPlaybackQuality().totalVideoFrames,
    audioTracks: (el.srcObject as MediaStream).getAudioTracks().length,
    videoTracks: (el.srcObject as MediaStream).getVideoTracks().length,
  }));
  expect(media.frames).toBeGreaterThan(0);
  expect(media.audioTracks).toBe(1);
  expect(media.videoTracks).toBe(1);
  console.log("HeyGen sandbox media:", JSON.stringify(media));
  await page.screenshot({ path: testInfo.outputPath("heygen-sandbox.png") });
  await page.getByRole("button", { name: "Video off", exact: true }).click();
  await expect(video).toHaveCount(0);
  await page.getByRole("link", { name: "Close voice assistant" }).click();
  await expect(page).toHaveURL(/\/support$/);
});
