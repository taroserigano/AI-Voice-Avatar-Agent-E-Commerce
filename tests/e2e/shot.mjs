// Scratch screenshot helper (not committed): node shot.mjs <url> <out.png> [width] [height] [fullPage]
import { chromium } from "@playwright/test";

const [url, out, w = "1280", h = "900", full = "0"] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: Number(w), height: Number(h) } });
if (process.env.SIGN_IN) {
  const base = new URL(url).origin;
  await page.goto(`${base}/sign-in`);
  await page.getByLabel("Email").fill("alice@example.com");
  await page.getByLabel("Password", { exact: true }).fill("alice-dev-password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL((u) => !u.pathname.startsWith("/sign-in"));
}
await page.goto(url);
await page.waitForTimeout(800);
await page.screenshot({ path: out, fullPage: full === "1" });
await browser.close();
