import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";
import { ALICE, signInFromScratch } from "./helpers";

const WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

/** Start clean: undo returns this account made in earlier runs (development-only endpoint). */
async function resetReturns(page: Page) {
  const resp = await page.request.post("/api/v1/returns/dev-reset");
  expect(resp.status()).toBe(204);
}

async function openSupport(page: Page, query = "") {
  await signInFromScratch(page, ALICE);
  await resetReturns(page);
  if (query) await page.goto(`/support${query}`);
  else await page.getByRole("link", { name: "Support", exact: true }).first().click();
  await expect(page.getByRole("heading", { name: "Xana", level: 2, exact: true })).toBeVisible();
  await page.getByRole("button", { name: "New conversation" }).click();
}

test("Xana prices a return and it's confirmed only by the customer's button", async ({ page }) => {
  await openSupport(page);
  await page.getByLabel("Message Xana").fill("I want to return my gel pens");
  await page.keyboard.press("Enter");

  const quote = page.getByRole("region", { name: "Return quote" });
  await expect(quote).toBeVisible({ timeout: 30_000 });
  await expect(quote.getByText(/Gel Pens/)).toBeVisible();
  await expect(quote.getByRole("button", { name: "Confirm return" })).toBeEnabled();

  // A typed "yes" is not a confirmation.
  await page.getByLabel("Message Xana").fill("yes");
  await page.keyboard.press("Enter");
  await expect(page.getByText(/tap Confirm return on the quote/).first()).toBeVisible();

  await quote.getByRole("button", { name: "Confirm return" }).last().click();
  await expect(page.getByText(/Return R-[0-9A-F]{8} is confirmed/).first()).toBeVisible({ timeout: 30_000 });
  await expect(page.getByRole("article", { name: /Return R-/ }).last()).toContainText("Return confirmed");

  const results = await new AxeBuilder({ page }).withTags(WCAG).analyze();
  expect(results.violations.map((v) => `${v.id} (${v.impact}): ${v.nodes.length} node(s)`)).toEqual([]);
});

test("a spoken yes confirms only when it's clear (simulated speech)", async ({ page }) => {
  await openSupport(page, "?voice=sim");
  const say = async (text: string) => {
    await page.getByLabel("Simulated speech (development)").fill(text);
    await page.getByRole("button", { name: "Say", exact: true }).click();
  };
  await say("I want to return my gel pens");
  const captions = page.getByLabel("Captions");
  await expect(captions.getByText(/Here's your return: 1 × .*Gel Pens/)).toBeVisible({ timeout: 30_000 });

  await say("mm-hmm");
  await expect(captions.getByText(/I need a clear yes/)).toBeVisible();
  await expect(page.getByText(/is confirmed/)).toHaveCount(0);

  await say("yes, confirm the return");
  await expect(page.getByText(/Return R-[0-9A-F]{8} is confirmed/).first()).toBeVisible({ timeout: 30_000 });
});

test("the order page's Start a return opens Xana on that item", async ({ page }) => {
  await signInFromScratch(page, ALICE);
  await resetReturns(page);
  // An order with something returnable right now.
  const orders: { id: string }[] = await (await page.request.get("/api/v1/orders")).json();
  let target: string | undefined;
  for (const o of orders) {
    const opts = await (await page.request.get(`/api/v1/orders/${o.id}/return-options`)).json();
    if (opts.lines.some((l: { eligible: boolean }) => l.eligible)) {
      target = o.id;
      break;
    }
  }
  expect(target).toBeTruthy();
  await page.goto(`/orders/${target}`);
  const start = page.getByRole("link", { name: /Start a return/ }).first();
  await expect(start).toHaveAttribute("href", /\/support\?order=[0-9a-f-]{36}&line=[0-9a-f-]{36}/);
  await start.click();
  await expect(page.getByText(/^I want to return the .+ from order/)).toBeVisible({ timeout: 30_000 });
});
