import { expect, test } from "@playwright/test";
import { ALICE, signInFromScratch } from "./helpers";

test("sign-in, search, and cart work on a phone-sized screen", async ({ page }) => {
  await signInFromScratch(page, ALICE);
  await page.getByRole("searchbox", { name: "Search products" }).fill("headlamp");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page.getByRole("list", { name: /Results for/ })).toContainText("Trailbeam Rechargeable Headlamp");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  expect(overflow).toBe(false);
  await page.getByRole("link", { name: /Cart/ }).click();
  await expect(page.getByRole("heading", { name: "Your cart" })).toBeVisible();
});
