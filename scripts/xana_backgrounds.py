"""Make the backgrounds the customer can put behind Xana's face (docs/features/10-xana-avatar).

Soft, defocused "rooms" and washes, like a camera's background blur, so they read as light and
casual without looking like a photo someone has to license. Run:

  uv run --with pillow python scripts/xana_backgrounds.py

Writes apps/web/public/xana/backgrounds/<key>.jpg (1280x720).
"""

from __future__ import annotations

import random
from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H = 1280, 720
OUT = Path(__file__).resolve().parents[1] / "apps/web/public/xana/backgrounds"
Draw = Callable[[ImageDraw.ImageDraw], None]


def sunlit(d: ImageDraw.ImageDraw) -> None:
    """A bright room: a window, a plant, a shelf."""
    d.rectangle([0, 0, W, H], fill=(244, 236, 224))
    d.rectangle([90, 60, 520, 560], fill=(255, 252, 244))
    d.rectangle([300, 60, 312, 560], fill=(232, 222, 206))
    d.ellipse([920, 330, 1180, 700], fill=(132, 166, 120))
    d.ellipse([980, 250, 1150, 520], fill=(150, 184, 134))
    d.rectangle([0, 600, W, H], fill=(214, 196, 172))
    d.rectangle([820, 140, 1240, 170], fill=(205, 182, 150))
    for i, x in enumerate((840, 900, 950, 1010)):
        d.rectangle([x, 70, x + 40, 140], fill=(220, 168, 140) if i % 2 else (170, 190, 210))


def cafe(d: ImageDraw.ImageDraw) -> None:
    """Warm café lights."""
    d.rectangle([0, 0, W, H], fill=(245, 232, 218))
    r = random.Random(4)
    for _ in range(26):
        x, y, s = r.randint(0, W), r.randint(0, H), r.randint(40, 140)
        tone = r.choice([(255, 226, 180), (255, 244, 226), (236, 200, 160), (250, 214, 196)])
        d.ellipse([x - s, y - s, x + s, y + s], fill=tone)
    d.rectangle([0, 560, W, H], fill=(196, 160, 128))


def mint(d: ImageDraw.ImageDraw) -> None:
    d.rectangle([0, 0, W, H], fill=(226, 244, 236))
    d.ellipse([-200, -150, 600, 500], fill=(246, 253, 249))
    d.ellipse([800, 300, 1500, 900], fill=(198, 232, 218))


def lavender(d: ImageDraw.ImageDraw) -> None:
    d.rectangle([0, 0, W, H], fill=(236, 232, 252))
    d.ellipse([700, -200, 1500, 450], fill=(250, 248, 255))
    d.ellipse([-300, 350, 500, 1000], fill=(216, 208, 246))


def night(d: ImageDraw.ImageDraw) -> None:
    """The voice screen's own dark stage."""
    d.rectangle([0, 0, W, H], fill=(14, 12, 34))
    d.ellipse([340, 60, 940, 660], fill=(40, 30, 92))
    d.ellipse([-200, 400, 400, 1000], fill=(22, 18, 52))


BACKGROUNDS: dict[str, tuple[Draw, int]] = {
    "sunlit": (sunlit, 34),
    "cafe": (cafe, 30),
    "mint": (mint, 60),
    "lavender": (lavender, 60),
    "night": (night, 90),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for key, (draw, blur) in BACKGROUNDS.items():
        im = Image.new("RGB", (W, H))
        draw(ImageDraw.Draw(im))
        im.filter(ImageFilter.GaussianBlur(blur)).save(OUT / f"{key}.jpg", quality=86, optimize=True)
        print(key, (OUT / f"{key}.jpg").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
