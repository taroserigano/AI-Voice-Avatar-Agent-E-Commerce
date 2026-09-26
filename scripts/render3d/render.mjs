// Render product scenes to WebP with headless Chromium + three.js.
// Usage: node render.mjs [slug ...] [--frames 64] [--ss 2] [--q 0.9] [--out <dir>] [--swiftshader]
// Default slugs: every file in ./products. Writes <out>/<slug>.webp and ./out/<slug>.png (review copy).
import { mkdirSync, readdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { startServer } from "./server.mjs";

// The repo root, two levels up from this folder.
const WORKTREE = fileURLToPath(new URL("../..", import.meta.url)).replace(/[\\/]$/, "");
const require = createRequire(`${WORKTREE}/tests/e2e/package.json`);
const { chromium } = require("@playwright/test");
const HERE = fileURLToPath(new URL(".", import.meta.url));

const args = process.argv.slice(2);
const opt = (name, def) => {
  const i = args.indexOf(`--${name}`);
  if (i < 0) return def;
  const v = args[i + 1];
  args.splice(i, 2);
  return v;
};
const swift = args.includes("--swiftshader");
if (swift) args.splice(args.indexOf("--swiftshader"), 1);
const frames = opt("frames", "256");
const ss = opt("ss", "2");
const q = opt("q", "0.95");
const cfgOverride = opt("cfg", "{}");
const outDir = opt("out", `${WORKTREE}/apps/web/public/images/products-3d`);
const slugs = args.length ? args : readdirSync(join(HERE, "products")).filter((f) => f.endsWith(".js")).map((f) => f.slice(0, -3));

mkdirSync(outDir, { recursive: true });
mkdirSync(join(HERE, "out"), { recursive: true });
const server = await startServer();
const port = server.address().port;
const browser = await chromium.launch({
  args: swift
    ? ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
    : ["--enable-gpu", "--use-angle=d3d11", "--ignore-gpu-blocklist"],
});
try {
  for (const slug of slugs) {
    const t0 = Date.now();
    const page = await browser.newPage({ viewport: { width: 700, height: 700 } });
    page.on("console", (m) => { if (m.type() === "error" || m.type() === "warning") console.log(`  [${m.type()}] ${m.text()}`); });
    page.on("pageerror", (e) => console.log(`  [pageerror] ${e.message}`));
    await page.goto(`http://127.0.0.1:${port}/scene.html?p=${slug}&n=${frames}&ss=${ss}&q=${q}&cfg=${encodeURIComponent(cfgOverride)}`);
    await page.waitForFunction(() => window.__result, null, { timeout: 600_000, polling: 250 });
    const r = await page.evaluate(() => window.__result);
    await page.close();
    if (r.error) { console.error(`${slug}: ${r.error}`); process.exitCode = 1; continue; }
    const webp = Buffer.from(r.webp.split(",")[1], "base64");
    writeFileSync(join(outDir, `${slug}.webp`), webp);
    writeFileSync(join(HERE, "out", `${slug}.png`), Buffer.from(r.png.split(",")[1], "base64"));
    console.log(`${slug}: ${(webp.length / 1024).toFixed(0)} KB webp, ${r.info}, ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
} finally {
  await browser.close();
  server.close();
}
