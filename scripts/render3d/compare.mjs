// Side-by-side sheet: current SVG illustration vs. 3D render, one row per product.
// Usage: node compare.mjs <out.png> <slug> [slug ...]
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

// The repo root, two levels up from this folder.
const WORKTREE = fileURLToPath(new URL("../..", import.meta.url)).replace(/[\\/]$/, "");
const require = createRequire(`${WORKTREE}/tests/e2e/package.json`);
const { chromium } = require("@playwright/test");

const [out, ...slugs] = process.argv.slice(2);
const b64 = (p) => readFileSync(p).toString("base64");
const rows = slugs
  .map((s) => {
    const svg = `data:image/svg+xml;base64,${b64(`${WORKTREE}/apps/web/public/images/products/${s}.svg`)}`;
    const webp = `data:image/webp;base64,${b64(`${WORKTREE}/apps/web/public/images/products-3d/${s}.webp`)}`;
    return `<div class="row"><figure><img src="${svg}"><figcaption>current illustration</figcaption></figure>
      <figure><img src="${webp}"><figcaption>3D render &middot; ${s}.webp</figcaption></figure></div>`;
  })
  .join("");
const html = `<!doctype html><style>body{margin:24px;font:14px system-ui;background:#fff;color:#333}
.row{display:flex;gap:24px;margin-bottom:24px}figure{margin:0}img{display:block;width:520px;height:520px;border-radius:12px;box-shadow:0 1px 3px #0003}
figcaption{margin-top:6px}</style>${rows}`;
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1120, height: 800 } });
await page.setContent(html, { waitUntil: "load" });
await page.screenshot({ path: out, fullPage: true });
await browser.close();
console.log(`wrote ${out}`);
