import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { ALICE, signInFromScratch } from "./helpers";

const WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

test("the return policy is public, deep-linkable, and accessible", async ({ page }) => {
  // Signed out: a return policy must be readable before buying.
  await page.goto("/returns-policy#rr-7-2");
  await expect(page).toHaveURL(/\/returns-policy#rr-7-2$/);
  await expect(page.getByRole("heading", { level: 1, name: "Returns & refunds" })).toBeVisible();
  await expect(page.getByRole("heading", { name: /7\.2\s*Splitting discounts and tax/ })).toBeInViewport();
  await expect(page.getByText("30 days", { exact: true })).toBeVisible();

  // The regulations document is on the same page, with its own sections.
  await expect(page.getByRole("heading", { level: 2, name: "How we handle returns and refunds" })).toBeVisible();
  await page.goto("about:blank");
  await page.goto("/returns-policy#rg-5-2");
  await expect(page.getByRole("heading", { name: /5\.2\s*Spoken confirmation/ })).toBeInViewport();

  const results = await new AxeBuilder({ page }).withTags(WCAG).analyze();
  expect(results.violations.map((v) => `${v.id} (${v.impact}): ${v.nodes.length} node(s)`)).toEqual([]);
});

test("product pages link to the matching policy section", async ({ page }) => {
  await signInFromScratch(page, ALICE);
  await page.goto("/c/gift-cards");
  await page.locator("main a[href^='/products/']").first().click();
  const link = page.getByRole("link", { name: "Return policy" });
  await expect(link).toHaveAttribute("href", "/returns-policy#rr-3-1");
  await link.click();
  await expect(page.getByRole("heading", { name: /3\.1\s*Gift cards/ })).toBeInViewport();
});
