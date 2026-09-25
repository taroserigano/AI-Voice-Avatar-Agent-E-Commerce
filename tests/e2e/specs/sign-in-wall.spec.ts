import { expect, test } from "@playwright/test";
import { ALICE, API_URL, signIn, signInFromScratch } from "./helpers";

test.describe("sign-in wall", () => {
  for (const path of ["/", "/cart", "/search?q=headphones", "/c/electronics", "/orders"]) {
    test(`signed-out visitor opening ${path} lands on sign-in`, async ({ page }) => {
      await page.goto(path);
      await expect(page).toHaveURL(/\/sign-in/);
      await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
    });
  }

  test("a product page is behind the wall too", async ({ page, request }) => {
    // Find a real product ID through the API as Alice, then visit signed out.
    const login = await request.post(`${API_URL}/v1/auth/sign-in`, { data: ALICE });
    expect(login.ok()).toBeTruthy();
    const products = await (await request.get(`${API_URL}/v1/products?page_size=1`)).json();
    const id = products.items[0].id as string;

    await page.goto(`/products/${id}`);
    await expect(page).toHaveURL(new RegExp(`/sign-in\\?returnTo=%2Fproducts%2F${id}`));
  });

  test("after signing in, the visitor returns to the page they asked for", async ({ page }) => {
    await page.goto("/search?q=rain+boots");
    await expect(page).toHaveURL(/returnTo=/);
    await signIn(page, ALICE);
    await expect(page).toHaveURL(/\/search\?q=rain\+boots$/);
    await expect(page.getByRole("heading", { name: /Results for/ })).toBeVisible();
  });

  test("a returnTo pointing to another site is ignored", async ({ page }) => {
    await page.goto("/sign-in?returnTo=https%3A%2F%2Fevil.example%2Fphish");
    await signIn(page, ALICE);
    await expect(page).toHaveURL("http://localhost:3000/");
    await page.goto("/sign-in?returnTo=%2F%2Fevil.example");
    await expect(page).toHaveURL(/localhost:3000/);
  });

  test("wrong password shows one generic message", async ({ page }) => {
    await page.goto("/sign-in");
    await signIn(page, { email: ALICE.email, password: "not-it" });
    // Filter by text: Next's route announcer is also role="alert".
    const alert = page.getByRole("alert").filter({ hasText: /\S/ });
    await expect(alert).toHaveText("Wrong email or password.");
    await page.getByLabel("Email").fill("nobody-here@example.com");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(alert).toHaveText("Wrong email or password.");
  });

  test("private APIs answer 401 with no session, even bypassing the web app", async ({ playwright }) => {
    const anon = await playwright.request.newContext();
    for (const path of ["/v1/cart", "/v1/products", "/v1/orders", "/v1/categories", "/v1/auth/me"]) {
      expect((await anon.get(`${API_URL}${path}`)).status(), path).toBe(401);
      expect((await anon.get(`http://localhost:3000/api${path}`)).status(), `/api${path}`).toBe(401);
    }
    await anon.dispose();
  });

  test("after signing out, Back shows no private data", async ({ page }) => {
    await signInFromScratch(page, ALICE);
    await page.goto("/cart");
    await expect(page.getByRole("heading", { name: "Your cart" })).toBeVisible();

    await page.getByText("Hi, Alice").click();
    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(page).toHaveURL(/\/sign-in$/);

    await page.goBack();
    await expect(page).toHaveURL(/\/sign-in/);
    await expect(page.getByRole("heading", { name: "Your cart" })).toHaveCount(0);
    await expect(page.getByText("Hi, Alice")).toHaveCount(0);
  });
});
