import { type APIRequestContext, type Page, expect } from "@playwright/test";

export const ALICE = { email: "alice@example.com", password: "alice-dev-password", name: "Alice" };
export const BOB = { email: "bob@example.com", password: "bob-dev-password", name: "Bob" };
export const API_URL = process.env.COMMERCE_API_URL ?? "http://localhost:8000";

export async function signIn(page: Page, user: { email: string; password: string }) {
  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Password", { exact: true }).fill(user.password);
  await page.getByRole("button", { name: "Sign in" }).click();
}

export async function signInFromScratch(page: Page, user: { email: string; password: string; name: string }) {
  await page.goto("/sign-in");
  await signIn(page, user);
  await expect(page.getByText(`Hi, ${user.name}`)).toBeVisible();
}

/** Empty a user's cart through the API (via the web origin, with the page's cookie). */
export async function emptyCart(request: APIRequestContext) {
  const cart = await (await request.get("/api/v1/cart")).json();
  for (const item of cart.items ?? []) await request.delete(`/api/v1/cart/items/${item.id}`);
}
