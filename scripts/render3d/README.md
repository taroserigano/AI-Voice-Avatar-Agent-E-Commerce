# render3d: procedural product photography (three.js + headless Chromium)

Every model, texture, label and light is generated in code. No downloaded images, models or HDRIs.

## Setup

This folder is outside the pnpm workspace. Run `npm install` here once (installs `three`); Playwright
and its Chromium come from `tests/e2e` (`pnpm install` at the repo root). Renders are written to
`apps/web/public/images/products-3d/`, and `services/commerce/src/commerce/seed/data.py`
(`_RENDERED_3D`) points products at them.

- `node render.mjs [slug ...] [--frames 256] [--ss 2] [--q 0.95] [--out dir] [--cfg '{json}'] [--swiftshader]`
  starts `server.mjs` (static server for this folder and `node_modules/three`), opens `scene.html?p=<slug>` in
  Playwright Chromium (D3D11 GPU, or SwiftShader as a fallback), and writes
  `apps/web/public/images/products-3d/<slug>.webp` plus a PNG review copy in `out/`.
- `studio.js` is the shared studio. It renders at 2x (2400 px) and accumulates 256 frames in float HDR. Each
  frame gets a sub-pixel camera jitter (anti-aliasing) and a new position for the one shadow light: a key disc
  top-left for a soft cast shadow, or a sky cap for occlusion. It also adds a blurred contact shadow, a
  softbox PMREM environment (key, fill, rims, vertical strips) and a mint sweep. The sweep colours are
  pre-inverted through the custom tone curve, so the output hits #EFFBF8 in the centre and #D3EFE8 at the edges.
  The last step box-filters down to 1200 px with dither.
- `materials.js` holds object-space procedural shaders (soap flecks, bamboo grain, bristle fibres).
- `products/<slug>.js` exports `build()` → `{ root, frame: { fill, elev, azim } }` plus optional `studio`
  overrides. Units are cm, and labels are canvas textures. To add a product, drop in a new file and run `render.mjs <slug>`.
- `compare.mjs <out.png> <slug...>` makes an SVG-vs-render sheet. `debug/_spheres.js` is a studio test scene
  (run it as `render.mjs _spheres`). `sheet.py`, `crop.py`, `px.py` and `banding.py` are review helpers.

Timing on this laptop (Intel UHD, D3D11): 10–25 s per product for 256 frames at 2x, including browser start.
