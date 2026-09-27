import { defineConfig, devices } from "@playwright/test";

/**
 * Browser journeys against the running stack (`pnpm infra:up`, then `pnpm dev`).
 * Uses the seeded development accounts (alice, bob).
 */
export default defineConfig({
  testDir: "./specs",
  fullyParallel: false, // the specs share the seeded accounts' carts
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"]],
  timeout: 60_000,
  use: {
    baseURL: process.env.WEB_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    // Axe measures contrast mid-animation otherwise; the site honors reduced motion.
    contextOptions: { reducedMotion: "reduce" },
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] }, testMatch: /responsive\.spec\.ts/ },
  ],
});
