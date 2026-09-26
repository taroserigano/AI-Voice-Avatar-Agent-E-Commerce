import { expect, test } from "@playwright/test";
import { ALICE, signInFromScratch } from "./helpers";

test.describe("stores and diet filters", () => {
  test.beforeEach(async ({ page }) => {
    await signInFromScratch(page, ALICE);
  });

  test("the store locator lists ten stores and shows the chosen one on a map", async ({ page }) => {
    await page.getByRole("link", { name: "Stores", exact: true }).click();
    await expect(page.getByRole("heading", { level: 1, name: "Stores near Dallas" })).toBeVisible();
    const list = page.getByRole("list", { name: "Store list" });
    await expect(list.getByRole("listitem")).toHaveCount(10);

    const map = page.locator("iframe[title^='Map showing'], [aria-label='Map of all Serigan Mart stores']").first();
    await expect(map).toBeVisible();

    const plano = list.getByRole("listitem").filter({ hasText: "Serigan Mart Plano Legacy" });
    await plano.getByRole("button", { name: "Show on map" }).click();
    await expect(plano.getByRole("button", { name: "Shown on map" })).toHaveAttribute("aria-pressed", "true");
    await expect(plano.getByRole("link", { name: /Directions/ })).toHaveAttribute("href", /google\.com\/maps\/dir/);
  });

  test("organic + fat free narrows milk to exactly those products", async ({ page }) => {
    await page.goto("/c/dairy-eggs?product_type=milk&tag=organic&tag=fat-free");
    const results = page.getByRole("list", { name: "Dairy & Eggs" });
    const cards = results.locator(":scope > li"); // product cards, not their tag badges
    await expect(cards.first()).toBeVisible();
    for (const card of await cards.all()) {
      await expect(card).toContainText(/Organic/);
      await expect(card).toContainText(/Fat Free/);
    }
    await expect(page.getByRole("checkbox", { name: /^Organic/ })).toBeChecked();

    await cards.first().getByRole("link").click();
    await expect(page.getByRole("table", { name: /Nutrition Facts/ })).toBeVisible();
    await expect(page.getByText("Allergens:")).toBeVisible();
  });
});
