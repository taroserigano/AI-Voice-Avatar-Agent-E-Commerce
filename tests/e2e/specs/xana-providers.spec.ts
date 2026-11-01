import AxeBuilder from "@axe-core/playwright";
import { expect, test, type WebSocketRoute } from "@playwright/test";
import { ALICE, signInFromScratch } from "./helpers";

// Fixture socket: no provider sessions or external speech calls are started.
test("provider routes preserve a muted call and pending return; keyboard tabs activate manually", async ({ page }) => {
  const messages: Record<string, unknown>[] = [];
  let sockets = 0;
  let voiceSocket: WebSocketRoute | undefined;
  await page.addInitScript(() => {
    navigator.mediaDevices.getUserMedia = async () => {
      const ctx = new AudioContext({ sampleRate: 24000 });
      return ctx.createMediaStreamDestination().stream;
    };
  });
  await page.routeWebSocket(/\/v1\/voice\/xana/, (socket) => {
    sockets++;
    voiceSocket = socket;
    socket.onMessage((raw) => {
      if (typeof raw !== "string") return;
      const msg = JSON.parse(raw);
      messages.push(msg);
      if (msg.type === "hello") {
        socket.send(JSON.stringify({
          type: "ready", conversation_id: "preserved-call", first_name: "Alice",
          voice: { provider: "cartesia", name: "Fixture" }, stt: { provider: "fixture", model: "fixture" },
          llm: { model: "fixture", simulated: true }, notice: "Fixture",
          avatars: {
            tavus: { available: true, provider: "tavus", notice: "Tavus fixture" },
            heygen: { available: true, provider: "heygen", notice: "HeyGen fixture" },
          },
        }));
        socket.send(JSON.stringify({ type: "state", state: "listening" }));
      }
    });
  });
  await signInFromScratch(page, ALICE);
  await page.goto("/support/voice");
  const tavus = page.getByRole("tab", { name: "Tavus", exact: true });
  const heygen = page.getByRole("tab", { name: "HeyGen", exact: true });
  await expect(tavus).toHaveAttribute("aria-selected", "true");
  await tavus.focus();
  await page.keyboard.press("ArrowRight");
  await expect(heygen).toBeFocused();
  await expect(tavus).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/support\/voice\/heygen$/);
  expect(sockets).toBe(0);
  expect(messages).toEqual([]);
  await page.getByRole("button", { name: "Start talking", exact: true }).click();
  await page.getByRole("button", { name: "Mute", exact: true }).click();
  voiceSocket!.send(JSON.stringify({ type: "user.final", text: "Return this item please." }));
  voiceSocket!.send(JSON.stringify({ type: "quote", quote: {
    kind: "return_quote", quote_id: "kept-quote", total_refund_minor: 1263,
    lines: [{ title: "Oat milk", quantity: 1, refund_minor: 1263 }],
  } }));
  await expect(page.getByRole("heading", { name: "Confirm your return" })).toBeVisible();
  await page.getByRole("button", { name: "Video", exact: true }).click();
  await expect.poll(() => messages.filter((m) => m.type === "avatar.select").length).toBe(1);
  await tavus.click();
  await expect(page).toHaveURL(/\/support\/voice\/tavus$/);
  await expect.poll(() => messages.filter((m) => m.type === "avatar.select").length).toBe(2);
  await expect(page.getByRole("button", { name: "Unmute", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("#main p:visible").filter({ hasText: "Return this item please." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Confirm your return" })).toBeVisible();
  expect(sockets).toBe(1);
  expect(messages.filter((m) => m.type === "hello")).toHaveLength(1);
  expect(messages.filter((m) => m.type === "avatar.select").map((m) => m.provider)).toEqual(["heygen", "tavus"]);
  // A stale server response must not turn off the newly selected provider.
  voiceSocket!.send(JSON.stringify({ type: "avatar.unavailable", request_id: 1, reason: "error" }));
  await expect(page.getByRole("button", { name: "Video off", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Video off", exact: true }).click();
  await expect.poll(() => messages.filter((m) => m.type === "avatar.select").at(-1)?.provider).toBe(null);
  const beforeBack = messages.filter((m) => m.type === "avatar.select").length;
  await page.goBack();
  await expect(heygen).toHaveAttribute("aria-selected", "true");
  await expect(page.getByRole("heading", { name: "Confirm your return" })).toBeVisible();
  expect(messages.filter((m) => m.type === "avatar.select")).toHaveLength(beforeBack);
  expect(sockets).toBe(1);
  const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(axe.violations.map((v) => v.id)).toEqual([]);
  await page.getByRole("link", { name: "Close voice assistant" }).click();
  await expect(page).toHaveURL(/\/support$/);
  await page.goto("/support/voice/heygen");
  await expect(page.getByRole("tab", { name: "HeyGen", exact: true })).toHaveAttribute("aria-selected", "true");
  await page.getByRole("button", { name: "Start talking", exact: true }).click();
  await expect.poll(() => messages.filter((m) => m.type === "hello").length).toBe(2);
  expect(messages.filter((m) => m.type === "hello").at(-1)?.conversation_id).toBe("preserved-call");
  await page.goto("/support/voice/unknown-provider");
  await expect(page.getByRole("heading", { name: "Meet Xena" })).toHaveCount(0);
});
