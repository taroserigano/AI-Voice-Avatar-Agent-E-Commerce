"""Generate original SVG placeholder images for every seeded product.

Run: uv run python scripts/generate_placeholders.py
Writes apps/web/public/images/products/<slug>.svg. Nothing is downloaded from anywhere.
"""

from __future__ import annotations

import html
import textwrap
from pathlib import Path

from commerce.seed.data import CATEGORIES, PRODUCTS

OUT = Path(__file__).resolve().parents[1] / "apps" / "web" / "public" / "images" / "products"

# A simple glyph per department, drawn with basic shapes (white, centered at 320,250).
GLYPHS = {
    "electronics": '<path d="M250 270a70 70 0 0 1 140 0" fill="none" stroke="#fff" stroke-width="18" stroke-linecap="round"/>'
    '<rect x="228" y="262" width="36" height="64" rx="14" fill="#fff"/><rect x="376" y="262" width="36" height="64" rx="14" fill="#fff"/>',
    "home-kitchen": '<path d="M250 230h140v70a50 50 0 0 1-50 50h-40a50 50 0 0 1-50-50z" fill="#fff"/>'
    '<path d="M390 250h22a22 22 0 0 1 0 44h-22" fill="none" stroke="#fff" stroke-width="14"/>',
    "clothing-shoes": '<path d="M262 200l-52 30 22 44 30-14v110h116V260l30 14 22-44-52-30c-8 20-28 32-58 32s-50-12-58-32z" fill="#fff"/>',
    "outdoor": '<path d="M320 180l110 170H210z" fill="#fff"/><path d="M320 260l40 90h-80z" fill-opacity=".25" fill="#000"/>',
    "sports": '<circle cx="320" cy="270" r="80" fill="none" stroke="#fff" stroke-width="16"/>'
    '<path d="M240 270h160M320 190c-40 50-40 110 0 160M320 190c40 50 40 110 0 160" stroke="#fff" stroke-width="10" fill="none"/>',
    "toys": '<rect x="240" y="210" width="70" height="70" rx="10" fill="#fff"/><rect x="330" y="210" width="70" height="70" rx="10" fill="#fff" fill-opacity=".8"/>'
    '<rect x="285" y="290" width="70" height="70" rx="10" fill="#fff" fill-opacity=".9"/>',
    "beauty": '<rect x="290" y="210" width="60" height="30" rx="6" fill="#fff"/><rect x="270" y="240" width="100" height="120" rx="22" fill="#fff"/>',
    "office": '<rect x="250" y="200" width="140" height="170" rx="10" fill="#fff"/>'
    '<path d="M275 240h90M275 270h90M275 300h60" stroke="#94a3b8" stroke-width="10" stroke-linecap="round"/>',
    "gift-cards": '<rect x="220" y="215" width="200" height="130" rx="16" fill="#fff"/>'
    '<path d="M320 215v130M220 270h200" stroke="#fbbf24" stroke-width="14"/>',
}


def svg_for(title: str, brand: str, color: str, category: str) -> str:
    lines = textwrap.wrap(title, width=24)[:3]
    text_y = 450
    tspans = "".join(
        f'<tspan x="320" dy="{0 if i == 0 else 40}">{html.escape(line)}</tspan>'
        for i, line in enumerate(lines)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" role="img" aria-label="{html.escape(title)} illustration">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{color}"/>
      <stop offset="1" stop-color="{color}" stop-opacity=".72"/>
    </linearGradient>
  </defs>
  <rect width="640" height="640" fill="url(#g)"/>
  <circle cx="540" cy="90" r="160" fill="#fff" fill-opacity=".08"/>
  <circle cx="80" cy="600" r="140" fill="#000" fill-opacity=".06"/>
  {GLYPHS.get(category, "")}
  <text y="{text_y}" text-anchor="middle" font-family="system-ui, -apple-system, Segoe UI, sans-serif" font-size="32" font-weight="700" fill="#fff">{tspans}</text>
  <text x="320" y="600" text-anchor="middle" font-family="system-ui, -apple-system, Segoe UI, sans-serif" font-size="22" fill="#fff" fill-opacity=".85">{html.escape(brand)}</text>
</svg>
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    colors = {c.slug: c.color for c in CATEGORIES}
    for p in PRODUCTS:
        (OUT / f"{p.slug}.svg").write_text(
            svg_for(p.title, p.brand, colors[p.category], p.category),
            encoding="utf-8",
            newline="\n",
        )
    print(f"wrote {len(PRODUCTS)} placeholders to {OUT}")


if __name__ == "__main__":
    main()
