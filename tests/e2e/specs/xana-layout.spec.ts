import { expect, test, type WebSocketRoute } from "@playwright/test";
import { ALICE, signInFromScratch } from "./helpers";

for (const viewport of [
  { width: 1440, height: 900, video: true },
  { width: 1100, height: 680, video: true },
  { width: 390, height: 700, video: true },
  { width: 390, height: 600, video: true },
  { width: 390, height: 600, video: false },
]) {
  test(`avatar stays in place as the conversation grows at ${viewport.width}x${viewport.height} (${viewport.video ? "video" : "voice only"})`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.addInitScript(() => {
      navigator.mediaDevices.getUserMedia = async () => {
        const ctx = new AudioContext({ sampleRate: 24000 });
        return ctx.createMediaStreamDestination().stream;
      };
    });
    let voiceSocket: WebSocketRoute | undefined;
    await page.routeWebSocket(/\/v1\/voice\/xana/, (socket) => {
      voiceSocket = socket;
      socket.onMessage((raw) => {
        if (typeof raw !== "string" || JSON.parse(raw).type !== "hello") return;
        socket.send(JSON.stringify({
          type: "ready", conversation_id: "layout-test", first_name: "Alice",
          voice: { provider: "openai", name: "Fixture" }, stt: { provider: "fixture", model: "fixture" },
          llm: { model: "fixture", simulated: true }, notice: "Fixture",
          avatars: {
            tavus: { available: true, provider: "tavus", notice: "Tavus fixture" },
            heygen: { available: false },
          },
        }));
        socket.send(JSON.stringify({ type: "state", state: "listening" }));
      });
    });
    await signInFromScratch(page, ALICE);
    await page.goto("/support/voice");
    await page.getByRole("button", { name: "Start talking", exact: true }).click();
    if (viewport.video) {
      await page.getByRole("button", { name: "Video", exact: true }).click();
      await expect(page.getByText("Connecting Xena…")).toBeVisible();
    } else {
      await expect(page.getByRole("button", { name: "Xena is listening" })).toBeVisible();
    }
    const avatar = page.getByRole("tabpanel");
    const initial = await avatar.boundingBox();
    expect(initial).not.toBeNull();

    voiceSocket!.send(JSON.stringify({ type: "user.final", text: "What is the return policy?" }));
    voiceSocket!.send(JSON.stringify({ type: "segment.start", segment: 1, generation: viewport.video ? 1 : 0, kind: "answer", text: "The policy is available." }));
    voiceSocket!.send(JSON.stringify({ type: "segment.unspoken", segment: 1 }));
    await expect(page.locator("p:visible").filter({ hasText: "The policy is available." }).first()).toBeVisible();
    voiceSocket!.send(JSON.stringify({ type: "tool", name: "lookup", label: "Checking the policy…" }));
    voiceSocket!.send(JSON.stringify({ type: "segment.text", segment: 1, text: "More details follow. ".repeat(100) }));
    await expect(page.locator("p:visible").filter({ hasText: "More details follow." }).first()).toHaveCount(1);
    voiceSocket!.send(JSON.stringify({ type: "suggestions", items: [
      "Where is my order?", "How do I start a return?", "What is the return policy?", "Can you help me?",
    ] }));
    voiceSocket!.send(JSON.stringify({ type: "quote", quote: {
      kind: "return_quote", quote_id: "layout-quote", total_refund_minor: 1263,
      lines: [{ title: "Oat milk", quantity: 1, refund_minor: 1263 }],
    } }));
    await expect(page.getByRole("heading", { name: "Confirm your return" })).toHaveCount(1);
    await expect.poll(async () => (await avatar.boundingBox())?.y).toBeCloseTo(initial!.y, 1);
    const details = page.getByRole("region", { name: "Voice conversation details" });
    expect(await details.evaluate((el) => el.clientHeight)).toBeGreaterThan(40);
    const quote = page.getByRole("region", { name: "Return quote" });
    await details.evaluate((el) => {
      const target = el.querySelector('[aria-label="Return quote"]');
      if (target instanceof HTMLElement) {
        el.scrollTop += target.getBoundingClientRect().top - el.getBoundingClientRect().top;
      }
    });
    await expect(quote).toBeInViewport();
    await details.evaluate((el) => {
      const button = el.querySelector('[aria-label="Return quote"] button');
      if (button instanceof HTMLElement) {
        el.scrollTop += button.getBoundingClientRect().bottom - el.getBoundingClientRect().bottom;
      }
    });
    await expect(quote.getByRole("button", { name: "Confirm return" })).toBeInViewport();
    await expect.poll(async () => (await avatar.boundingBox())?.y).toBeCloseTo(initial!.y, 1);

    voiceSocket!.send(JSON.stringify({ type: "error", message: "Speech failed; answers show as text." }));
    await expect(details.getByRole("alert")).toHaveText("Speech failed; answers show as text.");
    await details.evaluate((el) => {
      const target = el.querySelector('[role="alert"]');
      if (target instanceof HTMLElement) {
        el.scrollTop += target.getBoundingClientRect().top - el.getBoundingClientRect().top;
      }
    });
    await expect(details.getByRole("alert")).toBeInViewport();
    await expect(page.getByText("Simulated answers (no AI model connected).", { exact: false })).toBeVisible();
  });
}
