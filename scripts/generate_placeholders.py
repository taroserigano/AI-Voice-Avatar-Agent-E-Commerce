"""Generate original SVG placeholder images for the seed catalog.

Run: uv run --directory services/commerce python ../../scripts/generate_placeholders.py [--force]
Writes apps/web/public/images/products/<slug>.svg for the hand-written products and
apps/web/public/images/types/<product-type>.svg, shared by every generated product of that
type; the type illustrations live in placeholder_glyphs.py. --force redraws the type images
only; product images are never overwritten. Nothing is downloaded from anywhere.
"""

from __future__ import annotations

import html
import sys
import textwrap
from pathlib import Path

from placeholder_glyphs import OUTLINE_W, art_for, shade

from commerce.seed.catalog import PRODUCTS
from commerce.seed.data import CATEGORIES

IMAGES = Path(__file__).resolve().parents[1] / "apps" / "web" / "public" / "images"
OUT = IMAGES / "products"
TYPES = IMAGES / "types"

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
    "dairy-eggs": '<path d="M270 230l20-40h60l20 40v140H270z" fill="#fff"/><path d="M290 190h60v-20h-60z" fill="#fff" fill-opacity=".8"/>'
    '<rect x="290" y="270" width="60" height="50" rx="8" fill="#0369a1" fill-opacity=".35"/>',
    "produce": '<circle cx="300" cy="285" r="62" fill="#fff"/><circle cx="345" cy="285" r="62" fill="#fff" fill-opacity=".85"/>'
    '<path d="M322 222c0-24 12-40 34-46" stroke="#fff" stroke-width="10" fill="none" stroke-linecap="round"/>',
    "meat-seafood": '<path d="M220 270c40-60 140-60 180 0-40 60-140 60-180 0z" fill="#fff"/><path d="M400 270l40-40v80z" fill="#fff"/>'
    '<circle cx="262" cy="262" r="8" fill="#b91c1c"/>',
    "bakery": '<path d="M230 300c0-60 40-90 90-90s90 30 90 90v40H230z" fill="#fff"/>'
    '<path d="M280 250l-12 40M320 240v48M360 250l12 40" stroke="#92400e" stroke-width="8" stroke-linecap="round" stroke-opacity=".5"/>',
    "frozen": '<path d="M320 180v180M242 225l156 90M242 315l156-90" stroke="#fff" stroke-width="16" stroke-linecap="round"/>'
    '<circle cx="320" cy="270" r="20" fill="#fff"/>',
    "pantry": '<rect x="260" y="200" width="120" height="30" rx="8" fill="#fff" fill-opacity=".85"/><rect x="250" y="230" width="140" height="140" rx="20" fill="#fff"/>'
    '<rect x="275" y="275" width="90" height="50" rx="6" fill="#a16207" fill-opacity=".35"/>',
    "snacks": '<path d="M250 200h140l-12 30 12 30-12 30 12 30-12 30 12 30H250l12-30-12-30 12-30-12-30 12-30z" fill="#fff"/>',
    "beverages": '<path d="M300 180h40v40c30 20 40 40 40 70v80H260v-80c0-30 10-50 40-70z" fill="#fff"/>'
    '<rect x="260" y="290" width="120" height="40" fill="#1d4ed8" fill-opacity=".35"/>',
    "household": '<path d="M290 230h60l20 30v110H270V260z" fill="#fff"/><path d="M300 230v-30h50l30 16-30 14" fill="#fff" fill-opacity=".85"/>',
    "health-wellness": '<rect x="230" y="235" width="180" height="70" rx="35" fill="#fff"/><path d="M320 235v70" stroke="#15803d" stroke-width="10" stroke-opacity=".5"/>',
    "baby": '<path d="M300 210h40v30c20 10 30 25 30 45v85h-100v-85c0-20 10-35 30-45z" fill="#fff"/><rect x="305" y="180" width="30" height="30" rx="12" fill="#fff" fill-opacity=".85"/>',
    "pet": '<ellipse cx="320" cy="310" rx="60" ry="48" fill="#fff"/><circle cx="260" cy="245" r="22" fill="#fff"/><circle cx="300" cy="215" r="22" fill="#fff"/>'
    '<circle cx="340" cy="215" r="22" fill="#fff"/><circle cx="380" cy="245" r="22" fill="#fff"/>',
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


def _mix(hex_color: str, weight: float) -> str:
    """Blend a #rrggbb color toward white; weight 0 = the color, 1 = white."""
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    r, g, b = (round(c + (255 - c) * weight) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def svg_for_type(product_type: str, color: str, category: str) -> str:
    """A shared image for every generated product of one type, in the storefront's
    illustration style: a light, department-tinted studio sweep with a soft floor shadow and
    a flat illustration of the product family (see ``placeholder_glyphs``). There is no text
    label: product cards already show the title, and the image is decorative."""
    uid = f"t-{product_type}"
    light, mid = _mix(color, 0.95), _mix(color, 0.83)
    label = html.escape(type_label(product_type))
    glyph = art_for(product_type, category, color)
    outline = shade(color, 0.6)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" width="640" height="640" role="img" aria-label="{label}">
  <title>{label}</title>
  <defs>
    <radialGradient id="{uid}-bg" cx="320" cy="260" r="520" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{light}"/>
      <stop offset="1" stop-color="{mid}"/>
    </radialGradient>
    <filter id="{uid}-blur" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="10"/>
    </filter>
  </defs>
  <rect width="640" height="640" fill="url(#{uid}-bg)"/>
  <circle cx="320" cy="312" r="216" fill="#fff" fill-opacity=".5"/>
  <ellipse cx="320" cy="494" rx="160" ry="16" fill="#1e1b4b" fill-opacity=".14" filter="url(#{uid}-blur)"/>
  <g transform="translate(320 318) scale(1.2) translate(-320 -295)" stroke="{outline}" stroke-width="{OUTLINE_W}" stroke-linejoin="round" stroke-opacity=".45">{glyph}</g>
</svg>
"""


def type_label(product_type: str) -> str:
    return product_type.replace("-", " ").capitalize()


def _write(path: Path, svg: str, force: bool) -> bool:
    """Only fill gaps unless forced: existing images may be hand-drawn or real photos."""
    if path.exists() and not force:
        return False
    path.write_text(svg, encoding="utf-8", newline="\n")
    return True


def main() -> None:
    # Redraw the shared type images. Product images are never overwritten: most are hand-drawn.
    force = "--force" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    TYPES.mkdir(parents=True, exist_ok=True)
    colors = {c.slug: c.color for c in CATEGORIES}
    written = 0
    for p in PRODUCTS:
        if p.image_path is None:
            svg = svg_for(p.title, p.brand, colors[p.category], p.category)
            written += _write(OUT / f"{p.slug}.svg", svg, force=False)
    types: dict[str, str] = {}
    for p in PRODUCTS:
        if p.image_path and p.image_path.startswith("/images/types/"):
            types.setdefault(p.product_type, p.category)
    for product_type, category in sorted(types.items()):
        svg = svg_for_type(product_type, colors[category], category)
        written += _write(TYPES / f"{product_type}.svg", svg, force)
    print(f"wrote {written} placeholders under {IMAGES} (--force redraws the type images)")


if __name__ == "__main__":
    main()
