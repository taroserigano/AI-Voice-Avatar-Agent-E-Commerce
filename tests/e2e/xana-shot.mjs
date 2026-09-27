// Scratch (not committed): screenshot the Xana flow. node xana-shot.mjs <outdir> [width]
import { chromium } from "@playwright/test";

const [out, w = "1280"] = process.argv.slice(2);
const base = "http://localhost:3200";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: Number(w), height: 1000 } });
await page.goto(`${base}/sign-in`);
await page.getByLabel("Email").fill("alice@example.com");
await page.getByLabel("Password", { exact: true }).fill("alice-dev-password");
await page.getByRole("button", { name: "Sign in" }).click();
await page.waitForURL((u) => !u.pathname.startsWith("/sign-in"));
await page.request.post(`${base}/api/v1/returns/dev-reset`);
await page.goto(`${base}/support`);
await page.getByRole("button", { name: "New conversation" }).click();
await page.waitForTimeout(800);
await page.screenshot({ path: `${out}/xana-0.png` });
await page.getByLabel("Simulated speech (development)").fill("I want to return my earbuds, they stopped working");
await page.getByRole("button", { name: "Say", exact: true }).click();
await page.getByRole("region", { name: "Return quote" }).waitFor({ timeout: 30000 });
await page.waitForTimeout(800);
await page.screenshot({ path: `${out}/xana-1-quote.png` });
await page.getByLabel("Simulated speech (development)").fill("yes, confirm the return");
await page.getByRole("button", { name: "Say", exact: true }).click();
await page.getByText(/is confirmed/).first().waitFor({ timeout: 30000 });
await page.waitForTimeout(800);
await page.screenshot({ path: `${out}/xana-2-done.png` });
await browser.close();
