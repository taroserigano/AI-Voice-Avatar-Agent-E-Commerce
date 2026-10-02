import { readFileSync } from "node:fs";
import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";
import { ALICE, signInFromScratch } from "./helpers";

// Xena's full-screen voice agent (/support/voice), in a real browser against the real voice
// service. The microphone is a stand-in stream: silence, or a recorded question.

const WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];
const QUESTION = readFileSync(new URL("../fixtures/where-is-my-order.wav", import.meta.url)).toString("base64");

/** Replace the microphone: `wav` plays once after a short pause, then silence forever. */
async function fakeMicrophone(page: Page, wav: string | null) {
  await page.addInitScript((b64) => {
    navigator.mediaDevices.getUserMedia = async () => {
      const ctx = new AudioContext({ sampleRate: 24000 });
      const dest = ctx.createMediaStreamDestination();
      if (b64) {
        const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
        const src = ctx.createBufferSource();
        src.buffer = await ctx.decodeAudioData(bytes.buffer);
        src.connect(dest);
        src.start(ctx.currentTime + 1.5);
      }
      return dest.stream;
    };
  }, wav);
}

async function openVoice(page: Page, wav: string | null) {
  await fakeMicrophone(page, wav);
  await signInFromScratch(page, ALICE);
  await page.goto("/support");
  await page.getByRole("link", { name: /Talk to Xena by voice/ }).click();
  await expect(page).toHaveURL(/\/support\/voice$/);
  await expect(page.getByRole("heading", { name: "Meet Xena" })).toBeVisible();
}

test("the voice screen connects, listens, and mutes", async ({ page }) => {
  await openVoice(page, null);
  const results = await new AxeBuilder({ page }).withTags(WCAG).analyze();
  expect(results.violations.map((v) => v.id)).toEqual([]);

  await page.getByRole("button", { name: "Start talking to Xena" }).click();
  const status = page.locator("[aria-live=polite] p").first();
  await expect(status).toHaveText("Listening", { timeout: 20_000 });
  await expect(page.getByText("Your words will appear here as you speak…")).toBeVisible();

  const mute = page.getByRole("button", { name: "Mute" });
  await mute.click();
  await expect(page.getByRole("button", { name: "Unmute" })).toHaveAttribute("aria-pressed", "true");

  await page.getByRole("link", { name: "Close voice assistant" }).click();
  await expect(page).toHaveURL(/\/support$/);
});

// Real speech-to-text, model, and voice: costs a few cents, so it runs only when asked.
test("a spoken question gets a spoken, captioned answer", async ({ page }) => {
  test.skip(process.env.VOICE_E2E_LIVE !== "1", "set VOICE_E2E_LIVE=1 (uses OpenAI and Cartesia)");
  await openVoice(page, QUESTION);
  await page.getByRole("button", { name: "Start talking to Xena" }).click();

  // The customer's words appear as they speak, then Xena answers from their real order.
  await expect(page.getByText(/where(’s|'s| is) my most recent order/i)).toBeVisible({ timeout: 20_000 });
  const caption = page.locator("main p.font-medium");
  await expect(caption).toContainText(/September 30|arriv|expected/i, { timeout: 30_000 });
  await expect(page.locator("[aria-live=polite] p").first()).toHaveText(/Speaking|Listening/);
});
