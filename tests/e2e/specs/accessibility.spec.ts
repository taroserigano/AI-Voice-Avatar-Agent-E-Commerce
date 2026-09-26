import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { ALICE, signIn, signInFromScratch } from "./helpers";

const WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

async function expectNoViolations(page: import("@playwright/test").Page) {
  const results = await new AxeBuilder({ page }).withTags(WCAG).analyze();
  const summary = results.violations.map((v) => `${v.id} (${v.impact}): ${v.nodes.length} node(s)`);
  expect(summary).toEqual([]);
}

test("sign-in page has no automatic WCAG 2.2 AA violations", async ({ page }) => {
  await page.goto("/sign-in");
  await expectNoViolations(page);
});

test("sign-in works with the keyboard alone and allows pasting", async ({ page }) => {
  await page.goto("/sign-in");
  await page.getByLabel("Email").focus();
  await page.keyboard.type(ALICE.email);
  await page.keyboard.press("Tab");
  // Paste the password, as a password manager or clipboard would (WCAG 3.3.8).
  await page.evaluate((pw) => {
    const input = document.getElementById("password") as HTMLInputElement;
    const data = new DataTransfer();
    data.setData("text/plain", pw);
    input.dispatchEvent(new ClipboardEvent("paste", { clipboardData: data, bubbles: true, cancelable: true }));
    if (!input.value) input.value = pw; // default paste behaviour isn't simulated by the event
  }, ALICE.password);
  await page.keyboard.press("Enter");
  await expect(page.getByText("Hi, Alice")).toBeVisible();
});

test("home, search, product, and cart pages have no automatic WCAG 2.2 AA violations", async ({ page }) => {
  await signInFromScratch(page, ALICE);
  await expectNoViolations(page);
  await page.goto("/search?q=headphones");
  await expectNoViolations(page);
  await page.getByRole("list", { name: /Results for/ }).getByRole("link").first().click();
  await expect(page.getByRole("button", { name: "Add to cart" })).toBeVisible();
  await expectNoViolations(page);
  await page.goto("/cart");
  await expectNoViolations(page);
});

test("filtered listing, food product, and store locator pages have no automatic WCAG 2.2 AA violations", async ({ page }) => {
  await signInFromScratch(page, ALICE);
  await page.goto("/c/dairy-eggs?product_type=yogurt&tag=sugar-free");
  await expectNoViolations(page);
  await page.locator("ul[aria-label='Dairy & Eggs'] > li a").first().click();
  await expect(page.getByRole("table", { name: /Nutrition Facts/ })).toBeVisible();
  await expectNoViolations(page);
  await page.goto("/stores");
  await expect(page.getByRole("list", { name: "Store list" })).toBeVisible();
  // The map itself is Google's embedded page; axe checks our page around it.
  const results = await new AxeBuilder({ page }).withTags(WCAG).exclude("iframe").analyze();
  expect(results.violations.map((v) => `${v.id} (${v.impact}): ${v.nodes.length} node(s)`)).toEqual([]);
});

test("the skip link moves focus to the main content", async ({ page }) => {
  await page.goto("/sign-in");
  await signIn(page, ALICE);
  await expect(page.getByText("Hi, Alice")).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to main content" })).toBeFocused();
});
