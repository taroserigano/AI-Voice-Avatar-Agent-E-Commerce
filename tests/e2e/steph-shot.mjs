// Scratch (not committed): sign in, open Steph, ask questions, screenshot. node steph-shot.mjs <outdir> [width]
import { chromium } from "@playwright/test";

const [out, w = "1280"] = process.argv.slice(2);
const base = "http://localhost:3200";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: Number(w), height: 900 } });
await page.goto(`${base}/sign-in`);
await page.getByLabel("Email").fill("alice@example.com");
await page.getByLabel("Password", { exact: true }).fill("alice-dev-password");
await page.getByRole("button", { name: "Sign in" }).click();
await page.waitForURL((u) => !u.pathname.startsWith("/sign-in"));
await page.waitForTimeout(1500);
await page.screenshot({ path: `${out}/steph-0-home.png` });
await page.getByRole("button", { name: "Ask Steph" }).click();
await page.getByRole("button", { name: "New conversation" }).click();
await page.waitForTimeout(500);
await page.screenshot({ path: `${out}/steph-1-open.png` });
const ask = async (q, file) => {
  await page.getByLabel("Message Steph").fill(q);
  await page.keyboard.press("Enter");
  await page.getByRole("button", { name: "Send" }).waitFor({ timeout: 60000 });
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${out}/${file}` });
};
await ask("find me sugar free yogurt", "steph-2-yogurt.png");
await ask("how long do I have to return something?", "steph-3-policy.png");
await ask("can I drop off a return at the Plano store?", "steph-4-store.png");
await browser.close();
