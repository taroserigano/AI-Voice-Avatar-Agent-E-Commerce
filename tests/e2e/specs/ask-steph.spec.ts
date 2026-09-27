import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { ALICE, emptyCart, signInFromScratch } from "./helpers";

const WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

/** The floating launcher (pages may also have their own "Ask Steph" buttons). */
const launcher = (page: Page) => page.locator('button[aria-controls="steph-panel"]');

test("Steph finds sugar-free yogurt and adds one to the cart", async ({ page }) => {
  await signInFromScratch(page, ALICE);
  await emptyCart(page.request);
  await page.reload();

  await launcher(page).click();
  const panel = page.getByRole("dialog", { name: "Steph" });
  await expect(panel).toBeVisible();
  await expect(panel.getByLabel("Message Steph")).toBeFocused();
  await panel.getByRole("button", { name: "New conversation" }).click();

  await panel.getByLabel("Message Steph").fill("find me sugar free yogurt");
  await page.keyboard.press("Enter");
  const products = panel.getByRole("list", { name: "Products" }).first();
  await expect(products).toBeVisible({ timeout: 30_000 });
  // Every product shown is a yogurt with the sugar-free label.
  const cards = products.locator(":scope > li");
  expect(await cards.count()).toBeGreaterThan(0);
  for (const card of await cards.all()) {
    await expect(card.getByText("Sugar free", { exact: true })).toBeVisible();
    await expect(card.getByRole("link")).toContainText(/yogurt/i);
  }

  await cards.first().getByRole("button", { name: /^Add .* to cart$/ }).click();
  await expect(cards.first().getByRole("button", { name: /to cart$/ })).toContainText("Added");
  await expect(page.getByRole("link", { name: /Cart.*1/ })).toBeVisible();

  const results = await new AxeBuilder({ page }).withTags(WCAG).include("#steph-panel").analyze();
  expect(results.violations.map((v) => `${v.id} (${v.impact}): ${v.nodes.length} node(s)`)).toEqual([]);
});

test("Steph answers policy questions with a cited source, and remembers the conversation", async ({ page }) => {
  await signInFromScratch(page, ALICE);
  await launcher(page).click();
  const panel = page.getByRole("dialog", { name: "Steph" });
  await panel.getByRole("button", { name: "New conversation" }).click();
  await panel.getByLabel("Message Steph").fill("how long do I have to return a blender?");
  await page.keyboard.press("Enter");

  // Sources are folded under a "Sources (n)" disclosure; open it to see the citation.
  await panel.getByText(/^Sources \(\d+\)$/).first().click({ timeout: 30_000 });
  const source = panel.getByRole("link", { name: /Return and refund policy §2\.1/ });
  await expect(source).toBeVisible();
  await expect(source).toHaveAttribute("href", "/returns-policy#rr-2-1");
  await expect(panel.getByText(/30 days after the delivery date/).first()).toBeVisible();

  // Esc closes the panel and returns focus to the launcher; the conversation survives a reload.
  await page.keyboard.press("Escape");
  await expect(panel).toBeHidden();
  await expect(launcher(page)).toBeFocused();
  await page.reload();
  await launcher(page).click();
  await expect(page.getByRole("dialog", { name: "Steph" }).getByText(/30 days after the delivery date/).first()).toBeVisible();
});
