import { expect, test } from "@playwright/test";
import { ALICE, BOB, emptyCart, signInFromScratch } from "./helpers";

test.describe("shopping journey", () => {
  test.beforeEach(async ({ page }) => {
    await signInFromScratch(page, ALICE);
    await emptyCart(page.request);
  });

  test("search, open a product, add to cart, change quantity, remove", async ({ page }) => {
    await page.getByRole("combobox", { name: "Search products" }).fill("wireless headphones");
    await page.getByRole("button", { name: "Search", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Results for “wireless headphones”" })).toBeVisible();

    const results = page.getByRole("list", { name: /Results for/ });
    await expect(results.locator(":scope > li").first()).toContainText(/Wireless.*Headphones/);
    await results.getByRole("link", { name: /Arc Wireless Over-Ear Headphones/ }).click();

    await expect(page.getByRole("heading", { level: 1, name: "Arc Wireless Over-Ear Headphones" })).toBeVisible();
    await expect(page.getByText("$129.99").first()).toBeVisible();
    await page.getByText("Sand", { exact: true }).click(); // choose the second colour
    await page.getByLabel("Quantity").selectOption("2");
    await page.getByRole("button", { name: "Add to cart" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Added to cart" })).toBeVisible();
    await expect(page.getByRole("link", { name: /Cart.*2 items/ })).toBeVisible();

    await page.getByRole("link", { name: /Cart/ }).click();
    await expect(page.getByRole("heading", { name: "Your cart" })).toBeVisible();
    const cart = page.getByRole("list", { name: "Cart items" });
    await expect(cart).toContainText("Arc Wireless Over-Ear Headphones");
    await expect(cart).toContainText("Sand");
    await expect(page.getByText("$259.98").first()).toBeVisible();

    await cart.getByLabel("Quantity").selectOption("1");
    await expect(page.getByRole("status").filter({ hasText: "Updated" })).toBeVisible();
    await expect(page.getByText("$129.99").first()).toBeVisible();

    await cart.getByRole("button", { name: /Remove/ }).click();
    await expect(page.getByText("Your cart is empty.")).toBeVisible();
  });

  test("the cart survives a refresh", async ({ page }) => {
    await page.goto("/search?q=jump+rope");
    await page.getByRole("link", { name: /Speed Jump Rope/ }).first().click();
    await page.getByRole("button", { name: "Add to cart" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Added to cart" })).toBeVisible();
    await page.goto("/cart");
    await page.reload();
    await expect(page.getByRole("list", { name: "Cart items" })).toContainText("Speed Jump Rope");
  });

  test("rain shoes search finds waterproof footwear", async ({ page }) => {
    await page.goto("/search?q=waterproof+shoes+for+rain");
    const results = page.getByRole("list", { name: /Results for/ });
    await expect(results).toContainText("Puddle Waterproof Rain Boots");
    await expect(results).toContainText("Ridge Waterproof Trail Running Shoes");
  });

  test("filters: department, in-stock only, and price", async ({ page }) => {
    await page.goto("/c/home-kitchen?product_type=mixing-bowls&product_type=candle");
    await expect(page.getByRole("heading", { name: "Home & Kitchen" })).toBeVisible();
    await expect(page.getByText("Nesting Stainless Mixing Bowls, Set of 5")).toBeVisible(); // sold out
    await page.getByLabel("In stock only").check();
    await page.getByLabel("Maximum price in dollars").fill("30");
    await page.getByRole("button", { name: "Apply filters" }).click();
    await expect(page).toHaveURL(/in_stock=true/);
    await expect(page).toHaveURL(/product_type=candle/); // the checked types are kept
    await expect(page.getByText("Nesting Stainless Mixing Bowls, Set of 5")).toHaveCount(0);
    await expect(page.getByText("Cedar & Sea Salt Soy Candle")).toBeVisible();
  });

  test("Bob never sees Alice's cart", async ({ page, browser }) => {
    await page.goto("/search?q=yoga+mat");
    await page.getByRole("link", { name: /Grip Yoga Mat/ }).first().click();
    await page.getByText("Plum", { exact: true }).click(); // colours start unselected
    await page.getByRole("button", { name: "Add to cart" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Added to cart" })).toBeVisible();
    const aliceCart = await (await page.request.get("/api/v1/cart")).json();
    const aliceItemId = aliceCart.items[0].id as string;

    const bobContext = await browser.newContext();
    const bob = await bobContext.newPage();
    await signInFromScratch(bob, BOB);
    await emptyCart(bob.request);
    await bob.goto("/cart");
    await expect(bob.getByText("Your cart is empty.")).toBeVisible();
    expect((await bob.request.delete(`/api/v1/cart/items/${aliceItemId}`)).status()).toBe(404);
    await bobContext.close();

    await page.goto("/cart");
    await expect(page.getByRole("list", { name: "Cart items" })).toContainText("Grip Yoga Mat");
  });
});
