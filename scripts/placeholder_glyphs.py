# ruff: noqa: E501  (inline SVG path data, like generate_placeholders.py)
"""Flat product illustrations for the shared product-type images.

``art_for(product_type, category, color)`` returns the SVG markup for one product type: a
glyph drawn on a 640x640 canvas, standing on a ground line at y=440 and centered on x=320.
Glyphs use a small palette derived from the department color (``Pal``) plus a few natural
colors (fruit, bread, cheese), so a department page stays coherent while each product family
is recognizable. Closely related types share a drawing (``@art("hoodie", "fleece-jacket")``)
and differ by accent color; a type with no drawing at all falls back to a keyword rule, then
the department's default glyph (see ``resolve``).

Everything is drawn from basic shapes; nothing is traced or downloaded.
"""

from __future__ import annotations

import math
import zlib
from collections.abc import Callable
from dataclasses import dataclass

# ---------------------------------------------------------------------------------------------
# Colors


def mix(hex_color: str, weight: float) -> str:
    """Blend a #rrggbb color toward white; weight 0 = the color, 1 = white."""
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    r, g, b = (round(v + (255 - v) * weight) for v in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def shade(hex_color: str, weight: float) -> str:
    """Blend a #rrggbb color toward black; weight 0 = the color, 1 = black."""
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    r, g, b = (round(v * (1 - weight)) for v in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


@dataclass(frozen=True)
class Pal:
    """Department ink (I) with deep (D), mid (M), tint (T) and pale (P) steps, plus an
    accent (A) with dark (AD) and light (AL) steps that varies between types."""

    I: str  # noqa: E741 - short names keep the drawings readable
    D: str
    M: str
    T: str
    P: str
    A: str
    AD: str
    AL: str

    @classmethod
    def make(cls, color: str, accent: str) -> Pal:
        return cls(
            I=color,
            D=shade(color, 0.3),
            M=mix(color, 0.45),
            T=mix(color, 0.72),
            P=mix(color, 0.88),
            A=accent,
            AD=shade(accent, 0.22),
            AL=mix(accent, 0.55),
        )

    def with_accent(self, accent: str) -> Pal:
        return Pal.make(self.I, accent) if accent != self.A else self


# Accents rotate between types that share a glyph, so sibling types don't look identical.
ACCENTS = (
    "#f59e0b",  # amber
    "#ef4444",  # red
    "#10b981",  # emerald
    "#8b5cf6",  # violet
    "#f97316",  # orange
    "#ec4899",  # pink
    "#0ea5e9",  # sky
    "#84cc16",  # lime
    "#eab308",  # yellow
    "#14b8a6",  # teal
)

# Every glyph is wrapped in a group with a thin outline in a dark shade of the department
# color, so light shapes (white cartons, garlic, eggs) stay readable on the pale background.
OUTLINE_W = 4

W = "#ffffff"
SIL, SILD = "#e2e8f0", "#b6c2cf"  # metal / foil
INK = "#334155"  # dark details: screens, handles, eyes
SCREEN = "#1e293b"
CREAM = "#fff6e5"
RED, RED_D = "#e5484d", "#b42f35"
ORANGE = "#f59331"
YELLOW, YELLOW_D = "#f9c846", "#e0a41c"
GREEN, GREEN_D, GREEN_L = "#5fae3a", "#3f7f22", "#a3d97a"
BROWN, TAN, CRUST, CRUMB = "#8a5a33", "#d9a066", "#c97d38", "#f7e2b5"
MEAT, FAT = "#dd5a5f", "#fde4dc"
PURPLE = "#7e4db8"

# ---------------------------------------------------------------------------------------------
# Primitives


def _fmt(v: object) -> str:
    return f"{v:g}" if isinstance(v, float) else str(v)


def el(tag: str, **attrs: object) -> str:
    parts = "".join(
        f' {k.rstrip("_").replace("_", "-")}="{_fmt(v)}"' for k, v in attrs.items() if v is not None
    )
    return f"<{tag}{parts}/>"


def R(x: float, y: float, w: float, h: float, f: str, r: float = 0, **a: object) -> str:
    return el("rect", x=x, y=y, width=w, height=h, rx=r or None, fill=f, **a)


def C(cx: float, cy: float, r: float, f: str, **a: object) -> str:
    return el("circle", cx=cx, cy=cy, r=r, fill=f, **a)


def E(cx: float, cy: float, rx: float, ry: float, f: str, **a: object) -> str:
    return el("ellipse", cx=cx, cy=cy, rx=rx, ry=ry, fill=f, **a)


def P(d: str, f: str, **a: object) -> str:
    return el("path", d=d, fill=f, **a)


def L(d: str, s: str, w: float = 10, **a: object) -> str:
    """A stroked, round-capped line."""
    attrs: dict[str, object] = {
        "stroke_linecap": "round",
        "stroke_linejoin": "round",
        "stroke_opacity": 1,
    }
    attrs.update(a)
    return el("path", d=d, fill="none", stroke=s, stroke_width=w, **attrs)


def G(inner: str, tr: str) -> str:
    return f'<g transform="{tr}">{inner}</g>'


def shine(d: str, w: float = 12, o: float = 0.5) -> str:
    return L(d, W, w, stroke_opacity=o)


def T(x: float, y: float, text: str, f: str, size: int = 40) -> str:
    return (
        f'<text x="{_fmt(x)}" y="{_fmt(y)}" text-anchor="middle" font-family="system-ui, -apple-system, '
        f'Segoe UI, sans-serif" font-size="{size}" font-weight="800" fill="{f}" stroke="none">{text}</text>'
    )


def box3d(x: float, y: float, w: float, h: float, d: float, front: str, top: str, side: str) -> str:
    """An oblique box: the front face at (x, y, w, h), with its top and right side visible."""
    dy = d * 0.5
    return (
        P(f"M{_fmt(x)} {_fmt(y)}l{_fmt(d)} {_fmt(-dy)}h{_fmt(w)}l{_fmt(-d)} {_fmt(dy)}z", top)
        + P(
            f"M{_fmt(x + w)} {_fmt(y)}l{_fmt(d)} {_fmt(-dy)}v{_fmt(h)}l{_fmt(-d)} {_fmt(dy)}z", side
        )
        + R(x, y, w, h, front)
    )


def at(inner: str, x: float, y: float, s: float = 1, rot: float = 0) -> str:
    tr = f"translate({_fmt(x)} {_fmt(y)})"
    if rot:
        tr += f" rotate({_fmt(rot)})"
    if s == 1:
        return G(inner, tr)
    # Keep the inherited outline the same visual width whatever the scale.
    return f'<g transform="{tr} scale({_fmt(s)})" stroke-width="{OUTLINE_W / s:.2f}">{inner}</g>'


# ---------------------------------------------------------------------------------------------
# Emblems: small marks drawn around (0, 0) inside a ~50px box, placed on labels with ``at``.

Emblem = Callable[["Pal"], str]


def em_drop(f: str = W) -> Emblem:
    return lambda c: P("M0-24C10-10 18 0 18 8A18 18 0 0 1-18 8C-18 0-10-10 0-24z", f)


def em_leaf(f: str = GREEN) -> Emblem:
    return lambda c: (
        P("M-18 20C-22-6 0-22 22-22 22 2 6 20-18 20z", f)
        + L("M-14 16 10-8", W, 3, stroke_opacity=0.7)
    )


def em_fruit(f: str = RED) -> Emblem:
    return lambda c: (
        C(0, 5, 19, f)
        + P("M2-12c6-12 16-14 22-12-4 10-14 14-22 12z", GREEN)
        + C(-7, -1, 5, W, fill_opacity=0.5)
    )


def em_berry(f: str = RED) -> Emblem:
    return lambda c: (
        P("M0 24C-16 16-22 2-20-8-14-14-6-12 0-10 6-12 14-14 20-8 22 2 16 16 0 24z", f)
        + P("M-12-12 0-6 12-12 6-18 0-14-6-18z", GREEN)
        + C(-7, 2, 2, YELLOW)
        + C(6, 0, 2, YELLOW)
        + C(0, 12, 2, YELLOW)
    )


def em_beans(f: str = "#9a4a2c") -> Emblem:
    b = "M-10-6c0-8 12-10 14-2 2 4 8 2 8 8 0 10-22 12-22-6z"
    return lambda c: at(P(b, f), -8, -6) + at(P(b, f), 10, 2, rot=40) + at(P(b, f), -6, 12, rot=-30)


def em_tomato() -> Emblem:
    return lambda c: C(0, 4, 20, RED) + P("M0-16l5 6 8-2-4 6 6 4-9 0-6 5-2-7-8-1 6-5z", GREEN)


def em_fish(f: str = W) -> Emblem:
    return lambda c: (
        P("M-24 0C-12-14 8-14 16 0 8 14-12 14-24 0z", f)
        + P("M14 0l12-12v24z", f)
        + C(-12, -2, 3, c.I)
    )


def em_bone(f: str = W) -> Emblem:
    return lambda c: (
        R(-16, -5, 32, 10, f)
        + C(-18, -6, 7, f)
        + C(-18, 6, 7, f)
        + C(18, -6, 7, f)
        + C(18, 6, 7, f)
    )


def em_wheat(f: str = YELLOW) -> Emblem:
    def draw(c: Pal) -> str:
        s = L("M0 24V-22", f, 4)
        for y in (-14, -2, 10):
            s += E(-7, y, 5, 9, f, transform=f"rotate(-30 -7 {y})") + E(
                7, y, 5, 9, f, transform=f"rotate(30 7 {y})"
            )
        return s + E(0, -24, 5, 8, f)

    return draw


def em_bolt(f: str = YELLOW) -> Emblem:
    return lambda c: P("M4-26-14 4H0l-4 22 18-30H0z", f)


def em_snow(f: str = W) -> Emblem:
    return lambda c: L("M0-22V22M-19-11l38 22M-19 11l38-22", f, 5)


def em_sun(f: str = YELLOW) -> Emblem:
    return lambda c: (
        C(0, 0, 11, f)
        + L("M0-24v6M0 18v6M-24 0h6M18 0h6M-17-17l4 4M13 13l4 4M-17 17l4-4M13-13l4-4", f, 4)
    )


def em_cross(f: str = W) -> Emblem:
    return lambda c: P("M-7-22h14v15h15v14H7v15H-7V7h-15V-7h15z", f)


def em_moon(f: str = YELLOW) -> Emblem:
    return lambda c: P("M8-22A22 22 0 1 0 22 8 18 18 0 0 1 8-22z", f)


def em_flower(f: str = "#f472b6") -> Emblem:
    return lambda c: (
        "".join(C(x, y, 9, f) for x, y in ((0, -12), (11, -4), (7, 10), (-7, 10), (-11, -4)))
        + C(0, 0, 7, YELLOW)
    )


def em_pepper(f: str = RED) -> Emblem:
    return lambda c: (
        P("M-18 18C-4 16 12 0 14-14 16-20 22-22 20-14 18 4 2 22-18 18z", f)
        + L("M16-16c2-6 6-8 10-8", GREEN, 4)
    )


def em_heart(f: str = W) -> Emblem:
    return lambda c: P("M0 20C-26 2-22-20-8-20c4 0 7 2 8 6 1-4 4-6 8-6 14 0 18 22-8 40z", f)


def em_star(f: str = YELLOW) -> Emblem:
    return lambda c: P("M0-24l7 15 16 2-12 11 3 16-14-8-14 8 3-16-12-11 16-2z", f)


def em_capsule(a: str = W, b: str | None = None) -> Emblem:
    return lambda c: G(
        P("M0-10h-14a10 10 0 0 0 0 20H0z", b or c.A) + P("M0-10h14a10 10 0 0 1 0 20H0z", a),
        "rotate(-35) scale(1.3)",
    )


def em_bowl(f: str = W, food: str = YELLOW) -> Emblem:
    return lambda c: (
        C(-10, -4, 6, food)
        + C(2, -8, 6, food)
        + C(12, -3, 6, food)
        + C(-2, 0, 6, food)
        + P("M-24-2h48a24 22 0 0 1-48 0z", f)
    )


def em_letter(text: str, f: str = W, size: int = 34) -> Emblem:
    return lambda c: T(0, size * 0.36, text, f, size)


def em_steam(f: str = W) -> Emblem:
    return lambda c: L("M-10 20c-8-10 8-16 0-28M6 20c-8-10 8-16 0-28", f, 5) + L("M-16 24h32", f, 5)


def em_cup(f: str = W) -> Emblem:
    return lambda c: (
        P("M-18-10h30v14a15 15 0 0 1-30 0z", f)
        + L("M12-6h4a6 6 0 0 1 0 12h-6", f, 4)
        + L("M-8-24c-3 4 3 6 0 10M2-24c-3 4 3 6 0 10", f, 3)
    )


def em_bean(f: str = W) -> Emblem:
    return lambda c: (
        E(0, 0, 15, 21, f, transform="rotate(30)")
        + L("M-4-18c10 10-6 26 4 36", c.I, 4, transform="rotate(30)")
    )


def em_bubbles(f: str = W) -> Emblem:
    return lambda c: (
        C(-8, 8, 10, "none", stroke=f, stroke_width=4)
        + C(10, -6, 7, "none", stroke=f, stroke_width=4)
        + C(-4, -16, 5, "none", stroke=f, stroke_width=3)
    )


def em_cube(f: str = W) -> Emblem:
    return lambda c: box3d(
        -16, -6, 26, 26, 12, f, mix(c.I, 0.4) if f == W else mix(f, 0.4), shade(f, 0.12)
    )


def em_maple(f: str = "#dc4c2c") -> Emblem:
    return lambda c: P(
        "M0-26l6 12 8-4-2 14 10-4-4 10 8 2-16 10 2 8-10-2V28h-4v-8l-10 2 2-8-16-10 8-2-4-10 10 4-2-14 8 4z",
        f,
    )


def em_egg(f: str = CREAM) -> Emblem:
    return lambda c: E(0, 2, 16, 21, f) + E(-5, -6, 4, 6, W, fill_opacity=0.7)


def em_peanut(f: str = TAN) -> Emblem:
    return lambda c: G(
        P(
            "M-12-22a12 12 0 0 1 24 0c0 8-5 10-5 22s5 14 5 22a12 12 0 0 1-24 0c0-8 5-10 5-22s-5-14-5-22z",
            f,
        ),
        "rotate(35) scale(.85)",
    )


def em_paw(f: str = W) -> Emblem:
    return lambda c: (
        E(0, 8, 13, 11, f) + C(-15, -6, 6, f) + C(-6, -16, 6, f) + C(6, -16, 6, f) + C(15, -6, 6, f)
    )


def em_pancakes(f: str = CRUMB) -> Emblem:
    return lambda c: (
        E(0, 14, 24, 7, CRUST)
        + E(0, 6, 24, 7, f)
        + E(0, 0, 24, 7, CRUST)
        + E(0, -8, 24, 7, f)
        + P("M-6-12h12l-2 10h-8z", YELLOW)
    )


def em_cake(f: str = "#f9a8d4") -> Emblem:
    return lambda c: (
        R(-20, -4, 40, 24, CRUMB, 4)
        + P("M-20-4h40v6c-6 6-8-2-14 4s-8-2-14 4-8-2-12 0z", f)
        + C(0, -12, 5, RED)
    )


def em_wave(f: str = W) -> Emblem:
    return lambda c: L("M-22-8c7-7 15 7 22 0s15 7 22 0M-22 8c7-7 15 7 22 0s15 7 22 0", f, 5)


# ---------------------------------------------------------------------------------------------
# Generic packaging, parameterized by colors and an emblem.


def label_em(em: Emblem | None, c: Pal, x: float, y: float, s: float = 1.3) -> str:
    # Emblems are small marks: they never take the glyph outline.
    return f'<g stroke="none">{at(em(c), x, y, s)}</g>' if em else ""


def carton(
    c: Pal, em: Emblem | None = None, top: float = 150, w: float = 136, band: str | None = None
) -> str:
    """A gable-top carton (milk, juice, cream)."""
    x0, x1 = 320 - w / 2, 320 + w / 2
    eave = top + 64
    band_y = eave + (440 - eave) * 0.3
    band_h = (440 - eave) * 0.42
    return (
        R(x0 + 20, top, w - 40, 22, c.M, 4)
        + P(f"M{x0} {eave}L{x0 + 20} {top + 18}H{x1 - 20}L{x1} {eave}z", c.T)
        + L(f"M{x0 + 22} {top + 22}L{x0 + 34} {eave}", W, 5, stroke_opacity=0.6)
        + R(x0, eave, w, 440 - eave, W, 6)
        + R(x0, band_y, w, band_h, band or c.I)
        + label_em(em, c, 320, band_y + band_h / 2, 1.3 * w / 136)
        + shine(f"M{x0 + 14} {eave + 14}V{band_y - 12}", 10, 0.9)
    )


def brick(c: Pal, em: Emblem | None = None, band: str | None = None) -> str:
    """An aseptic box carton with a screw cap (broth, plant milk)."""
    return (
        box3d(250, 184, 130, 256, 34, c.P, c.T, c.M)
        + E(344, 176, 17, 7, c.AD)
        + R(327, 158, 34, 18, c.A, 5)
        + R(250, 262, 130, 104, band or c.I)
        + label_em(em, c, 315, 314)
        + shine("M264 200V246", 10, 0.9)
    )


def box(
    c: Pal,
    em: Emblem | None = None,
    x: float = 232,
    y: float = 170,
    w: float = 156,
    h: float = 270,
    d: float = 36,
    front: str | None = None,
    window: str | None = None,
) -> str:
    """A 3/4-view carton box (cereal, pasta, mixes)."""
    front = front or c.I
    s = box3d(x, y, w, h, d, front, mix(front, 0.35), shade(front, 0.2))
    s += R(x + 14, y + 18, w - 28, 26, W, 13, fill_opacity=0.9)
    s += R(x + 30, y + 27, w - 60, 8, front, 4, fill_opacity=0.5)
    if window:
        s += R(x + 18, y + 64, w - 36, h - 100, window, 18)
    s += label_em(em, c, x + w / 2, y + h * 0.6, 1.9)
    return s


def bag(
    c: Pal,
    em: Emblem | None = None,
    body: str | None = None,
    x0: float = 240,
    x1: float = 400,
    top: float = 162,
    window: str | None = None,
) -> str:
    """A pillow bag with crimped seals (chips, frozen vegetables)."""
    body = body or c.I
    zig_t = "".join("l8-12l8 12" for _ in range(int((x1 - x0) // 16)))
    zig_b = "".join("l-8 12l-8-12" for _ in range(int((x1 - x0) // 16)))
    w = (x1 - x0) // 16 * 16
    x1 = x0 + w
    s = P(f"M{x0} {top + 30}Q{x0 - 16} 300 {x0} 418H{x1}Q{x1 + 16} 300 {x1} {top + 30}z", body)
    s += P(f"M{x0} {top + 36}V{top + 12}{zig_t}V{top + 36}z", shade(body, 0.18))
    s += P(f"M{x1} 410V428{zig_b}V410z", shade(body, 0.18))
    if window:
        s += E((x0 + x1) / 2, 318, (x1 - x0) * 0.36, 62, window)
    s += label_em(em, c, (x0 + x1) / 2, 318, 1.9)
    s += shine(f"M{x0 + 16} {top + 60}Q{x0 + 8} 300 {x0 + 16} 380", 10, 0.45)
    return s


def pouch(
    c: Pal, em: Emblem | None = None, body: str | None = None, window: str | None = None
) -> str:
    """A stand-up pouch with a zipper (nuts, trail mix, coffee)."""
    body = body or c.I
    return (
        P("M246 172H394L404 414Q406 440 380 440H260Q234 440 236 414z", body)
        + R(246, 172, 148, 16, shade(body, 0.2))
        + L("M254 206H386", shade(body, 0.25), 5)
        + (E(320, 318, 58, 66, window) if window else "")
        + label_em(em, c, 320, 318, 1.9)
        + shine("M258 222L252 400", 10, 0.45)
    )


def food_can(
    c: Pal,
    em: Emblem | None = None,
    label: str | None = None,
    band: str | None = None,
    x: float = 238,
    w: float = 164,
    top: float = 232,
) -> str:
    """A ribbed tin can (beans, soup, tomatoes)."""
    label = label or c.I
    x1 = x + w
    rx = w / 2
    s = R(x, top, w, 440 - top - 8, SIL)
    s += E(x + rx, 432, rx, 12, SILD)
    s += R(x, top + 16, w, 440 - top - 42, label)
    if band:
        s += R(x, top + 30, w, 24, band)
    s += L(f"M{x} {top + 8}H{x1}M{x} 424H{x1}", SILD, 4)
    s += E(x + rx, top, rx, 14, SILD) + E(x + rx, top, rx - 10, 9, SIL)
    s += label_em(em, c, x + rx, (top + 440) / 2 + 6, 1.9)
    s += shine(f"M{x + 16} {top + 30}V410", 10, 0.4)
    return s


def jar(
    c: Pal,
    fill: str,
    em: Emblem | None = None,
    lid: str | None = None,
    label: str = W,
    x: float = 246,
    w: float = 148,
    top: float = 196,
) -> str:
    """A glass jar with a screw lid (jam, sauce, peanut butter)."""
    lid = lid or c.I
    x1 = x + w
    return (
        P(
            f"M{x + 10} {top + 40}H{x1 - 10}Q{x1} {top + 40} {x1} {top + 62}V412Q{x1} 440 {x1 - 28} 440H{x + 28}Q{x} 440 {x} 412V{top + 62}Q{x} {top + 40} {x + 10} {top + 40}z",
            fill,
        )
        + R(x + 6, top, w - 12, 44, lid, 10)
        + L(
            f"M{x + 20} {top + 14}V{top + 32}M{x + 38} {top + 14}V{top + 32}M{x1 - 38} {top + 14}V{top + 32}M{x1 - 20} {top + 14}V{top + 32}",
            shade(lid, 0.2),
            5,
        )
        + R(x, top + 96, w, 104, label)
        + label_em(em, c, x + w / 2, top + 148, 1.5)
        + shine(f"M{x + 16} {top + 70}V{top + 86}M{x + 16} {top + 212}V400", 10, 0.55)
    )


def bottle(
    c: Pal,
    body: str,
    em: Emblem | None = None,
    cap: str | None = None,
    label: str | None = None,
    neck: float = 18,
    shoulder: float = 236,
    w: float = 116,
    top: float = 150,
) -> str:
    """A long-necked bottle (oil, dressing, vinegar, cold brew, kombucha)."""
    cap = cap or c.A
    x0, x1 = 320 - w / 2, 320 + w / 2
    n0, n1 = 320 - neck, 320 + neck
    nt = top + 26
    return (
        P(
            f"M{n0} {nt}H{n1}V{shoulder - 30}Q{x1} {shoulder - 6} {x1} {shoulder + 30}V424Q{x1} 440 {x1 - 16} 440H{x0 + 16}Q{x0} 440 {x0} 424V{shoulder + 30}Q{x0} {shoulder - 6} {n0} {shoulder - 30}z",
            body,
        )
        + R(n0 - 4, top, 2 * neck + 8, 30, cap, 6)
        + (R(x0, shoulder + 56, w, 96, label) if label else "")
        + label_em(em, c, 320, shoulder + 104, 1.4 * w / 116)
        + shine(
            f"M{x0 + 14} {shoulder + 36}V{shoulder + 46}M{x0 + 14} {shoulder + 166}V414", 9, 0.55
        )
    )


def pet_bottle(
    c: Pal,
    body: str,
    cap: str | None = None,
    label: str | None = None,
    em: Emblem | None = None,
    top: float = 150,
) -> str:
    """A plastic drink bottle (water, soda, sports drink)."""
    cap = cap or c.A
    return (
        P(
            f"M298 {top + 30}H342V{top + 48}Q380 {top + 70} 380 {top + 116}V{top + 150}Q370 {top + 162} 380 {top + 176}V424Q380 440 364 440H276Q260 440 260 424V{top + 176}Q270 {top + 162} 260 {top + 150}V{top + 116}Q260 {top + 70} 298 {top + 48}z",
            body,
        )
        + R(294, top, 52, 32, cap, 7)
        + R(290, top + 28, 60, 8, shade(cap, 0.15), 3)
        + (R(260, top + 184, 120, 88, label or c.I) if label is not False else "")
        + label_em(em, c, 320, top + 228, 1.3)
        + shine(f"M276 {top + 110}V{top + 140}M276 {top + 290}V410", 9, 0.6)
    )


def can(
    c: Pal,
    body: str | None = None,
    em: Emblem | None = None,
    slim: bool = False,
    stripe: str | None = None,
) -> str:
    """A beverage can."""
    body = body or c.I
    w = 92 if slim else 116
    h0 = 170 if slim else 196
    x0 = 320 - w / 2
    s = R(x0 + 6, h0 - 14, w - 12, 24, SILD, 10)
    s += R(x0, h0, w, 440 - h0 - 10, body, 14)
    s += R(x0 + 6, 418, w - 12, 22, SILD, 10)
    if stripe:
        s += P(f"M{x0} {h0 + 170}L{x0 + w} {h0 + 110}V{h0 + 150}L{x0} {h0 + 210}z", stripe)
    s += label_em(em, c, 320, h0 + 90, 1.5 if slim else 1.8)
    s += shine(f"M{x0 + 16} {h0 + 20}V{418 - 16}", 10, 0.45)
    return s


def tub(
    c: Pal,
    em: Emblem | None = None,
    top: float = 262,
    w: float = 164,
    body: str = W,
    lid: str | None = None,
    band: str | None = None,
) -> str:
    """A round tub with a lid (sour cream, protein powder, ice cream)."""
    lid = lid or c.I
    x0, x1 = 320 - w / 2, 320 + w / 2
    b = P(
        f"M{x0} {top + 26}L{x0 + 12} 428Q{x0 + 13} 440 {x0 + 26} 440H{x1 - 26}Q{x1 - 13} 440 {x1 - 12} 428L{x1} {top + 26}z",
        body,
    )
    if band:
        mid = (top + 26 + 440) / 2
        b += P(f"M{x0 + 3} {mid - 36}H{x1 - 3}L{x1 - 8.5} {mid + 36}H{x0 + 8.5}z", band)
    return (
        b
        + R(x0 - 8, top, w + 16, 36, lid, 12)
        + R(x0 - 8, top + 26, w + 16, 10, shade(lid, 0.18), 5)
        + label_em(em, c, 320, (top + 36 + 440) / 2, 1.5)
        + shine(f"M{x0 + 16} {top + 52}L{x0 + 24} 420", 9, 0.45)
    )


def pill_bottle(c: Pal, em: Emblem | None = None, body: str = W, cap: str | None = None) -> str:
    cap = cap or c.A
    return (
        R(262, 240, 116, 200, body, 18)
        + R(254, 188, 132, 60, cap, 12)
        + L(
            "M274 200V236M294 200V236M314 200V236M334 200V236M354 200V236M374 200V236",
            shade(cap, 0.18),
            5,
        )
        + R(262, 282, 116, 110, c.I)
        + label_em(em, c, 320, 337, 1.4)
        + shine("M278 256V270M278 404V424", 9, 0.8)
    )


def pump_bottle(c: Pal, body: str | None = None, em: Emblem | None = None, label: str = W) -> str:
    body = body or c.I
    return (
        R(313, 170, 14, 60, SILD, 4)
        + P("M286 158h60a8 8 0 0 1 8 8v14h-68z", c.A)
        + R(254, 162, 40, 12, c.A, 5)
        + R(294, 222, 52, 26, c.AD, 6)
        + R(262, 244, 116, 196, body, 28)
        + R(276, 292, 88, 100, label, 10)
        + label_em(em, c, 320, 342, 1.3)
        + shine("M276 262V278", 9, 0.6)
    )


def flip_bottle(c: Pal, body: str | None = None, em: Emblem | None = None, label: str = W) -> str:
    """A shampoo-style bottle standing on its flip cap... or not: cap up."""
    body = body or c.I
    return (
        R(286, 160, 68, 44, c.A, 12)
        + R(286, 194, 68, 10, c.AD)
        + P(
            "M286 204H354Q386 214 386 250V412Q386 440 358 440H282Q254 440 254 412V250Q254 214 286 204z",
            body,
        )
        + R(272, 284, 96, 112, label, 14)
        + label_em(em, c, 320, 340, 1.4)
        + shine("M270 244V268", 9, 0.6)
    )


def tube(
    c: Pal, body: str = W, em: Emblem | None = None, band: str | None = None, cap: str | None = None
) -> str:
    """A squeeze tube standing on its cap (toothpaste, cream)."""
    band = band or c.I
    cap = cap or c.A
    return (
        R(290, 390, 60, 50, cap, 8)
        + R(284, 384, 72, 14, c.AD, 5)
        + P("M252 180H388L354 386H286z", body)
        + P("M258 244H382L372 306H268z", band)
        + R(246, 160, 148, 26, shade(body, 0.08), 4)
        + L(
            "M262 166V180M278 166V180M294 166V180M310 166V180M326 166V180M342 166V180M358 166V180M374 166V180",
            shade(body, 0.2),
            3,
        )
        + label_em(em, c, 320, 275, 1.1)
        + shine("M270 196L290 372", 8, 0.8 if body == W else 0.45)
    )


def spray_bottle(
    c: Pal, body: str | None = None, em: Emblem | None = None, head: str | None = None
) -> str:
    body = body or c.I
    head = head or c.A
    return (
        R(284, 214, 60, 36, shade(head, 0.15), 6)
        + P("M270 160H372Q386 160 386 174V214H300L262 188Q256 160 270 160z", head)
        + R(236, 168, 40, 18, shade(head, 0.15), 6)
        + L("M304 214Q292 238 302 258", shade(head, 0.15), 12)
        + P(
            "M290 246H346Q390 262 390 310V416Q390 440 366 440H266Q242 440 242 416V330Q242 262 290 246z",
            body,
        )
        + R(262, 320, 108, 90, W, 12)
        + label_em(em, c, 316, 365, 1.3)
        + shine("M258 330V400", 9, 0.4)
    )


def aerosol(c: Pal, body: str | None = None, em: Emblem | None = None) -> str:
    body = body or c.I
    return (
        R(284, 156, 72, 56, c.A, 16)
        + P("M276 222Q276 204 300 202H340Q364 204 364 222z", SIL)
        + R(272, 218, 96, 222, body, 14)
        + R(272, 290, 96, 70, W, 0, fill_opacity=0.92)
        + label_em(em, c, 320, 325, 1.2)
        + shine("M288 236V274M288 376V420", 9, 0.45)
    )


def roll(
    c: Pal, cx: float, top: float, h: float, rx: float = 64, paper: str = W, core: str | None = None
) -> str:
    """A paper roll seen slightly from above."""
    core = core or c.T
    return (
        R(cx - rx, top, 2 * rx, h, paper)
        + E(cx, top + h, rx, 16, paper)
        + E(cx, top, rx, 16, mix(c.I, 0.93))
        + E(cx, top, 18, 7, core)
        + L(f"M{cx - rx + 10} {top + 20}V{top + h - 4}", c.P, 6)
    )


def stick_pack(c: Pal, color: str, x: float, rot: float) -> str:
    return at(
        R(-22, -110, 44, 220, color, 6)
        + R(-22, -110, 44, 18, shade(color, 0.2), 4)
        + R(-22, 92, 44, 18, shade(color, 0.2), 4),
        x,
        330,
        1,
        rot,
    )


# ---------------------------------------------------------------------------------------------
# Registry: product type -> drawing. ``accent`` pins the accent color; otherwise it is derived
# from the type name so siblings sharing a drawing still differ.

Draw = Callable[[Pal], str]
ART: dict[str, tuple[Draw, str | None]] = {}


def art(*names: str, accent: str | None = None) -> Callable[[Draw], Draw]:
    def deco(fn: Draw) -> Draw:
        for n in names:
            ART[n] = (fn, accent)
        return fn

    return deco


def reg(name: str, fn: Draw, accent: str | None = None) -> None:
    ART[name] = (fn, accent)


def plate(c: Pal, y: float = 424, rx: float = 150) -> str:
    return E(320, y + 4, rx, 18, c.T) + E(320, y, rx - 12, 12, c.P)


# --- Dairy & eggs ----------------------------------------------------------------------------

reg("milk", lambda c: carton(c, em_drop()))
reg("cream", lambda c: carton(c, em_drop(), top=214, w=112, band=c.M))
reg("plant-milk", lambda c: brick(c, em_leaf(GREEN_L)), accent="#84cc16")


def dairy_bottle(c: Pal, em: Emblem | None, body: str = W, label: str | None = None) -> str:
    return (
        P(
            "M296 198V184H344V198C372 212 380 234 380 264V420Q380 440 360 440H280Q260 440 260 420V264C260 234 268 212 296 198z",
            body,
        )
        + R(290, 156, 60, 32, c.A, 8)
        + R(286, 182, 68, 9, c.AD, 3)
        + R(260, 290, 120, 96, label or c.I)
        + label_em(em, c, 320, 338, 1.3)
        + shine("M276 268V278M276 398V420", 9, 0.9 if body == W else 0.5)
    )


reg("kefir", lambda c: dairy_bottle(c, em_drop()), accent="#8b5cf6")
reg("creamer", lambda c: dairy_bottle(c, em_cup()), accent="#f59e0b")


@art("cheese")
def cheese(c: Pal) -> str:
    hole = "#f0a21c"
    return (
        R(166, 418, 308, 22, c.T, 11)
        + P("M190 318L420 236L456 290z", "#fde68a")
        + P("M190 318L456 290V398L190 426z", "#fbc53a")
        + P("M456 290L420 236V344L456 398z", "#f2a51f")
        + E(262, 376, 15, 11, hole)
        + E(336, 346, 21, 14, hole)
        + E(410, 378, 12, 10, hole)
        + E(296, 404, 9, 6, hole)
        + E(352, 274, 13, 4, "#f7c64a")
        + E(292, 292, 8, 3, "#f7c64a")
    )


@art("eggs")
def eggs(c: Pal) -> str:
    s = R(196, 240, 248, 86, c.T, 22) + L("M218 264H422", c.P, 6)
    for x in (234, 292, 350, 408):
        s += E(x, 318, 30, 40, CREAM) + E(x - 10, 302, 6, 11, W)
    s += R(186, 338, 268, 102, c.I, 20)
    s += L("M263 354V424M321 354V424M379 354V424", c.D, 4, stroke_opacity=0.5)
    s += shine("M204 356H436", 6, 0.3)
    return s


def yogurt_cup(c: Pal, lid: str, band: str, em: Emblem) -> str:
    return (
        P("M-76-80L-58 80Q-57 90-46 90H46Q57 90 58 80L76-80z", W)
        + P("M-70-30H70L63 40H-63z", band)
        + label_em(em, c, 0, 5, 1.2)
        + E(0, -82, 84, 18, lid)
        + E(0, -86, 70, 11, mix(lid, 0.35))
        + P("M-80-86l-26-8q-6 10 4 18z", lid)
    )


@art("yogurt", accent="#ec4899")
def yogurt(c: Pal) -> str:
    return at(yogurt_cup(c, "#f59e0b", c.M, em_fruit(ORANGE)), 408, 377, 0.7) + at(
        yogurt_cup(c, c.A, c.I, em_berry()), 296, 350
    )


@art("butter", accent=YELLOW)
def butter(c: Pal) -> str:
    return G(
        P("M190 330L226 296H336L300 330z", "#fff1a8")
        + R(190, 330, 110, 78, "#fde58a")
        + P("M300 330L336 296H486L450 330z", SIL)
        + R(300, 330, 150, 78, W)
        + P("M450 330L486 296V374L450 408z", "#d7dee7")
        + R(300, 352, 150, 20, c.I)
        + P("M450 352L486 318V338L450 372z", c.D),
        "translate(-18 30)",
    )


reg("sour-cream", lambda c: tub(c, em_drop(c.I), band=c.P), accent="#0ea5e9")


# --- Produce ---------------------------------------------------------------------------------


@art("apples")
def apples(c: Pal) -> str:
    return (
        P(
            "M320 250C290 226 222 232 216 312C210 384 262 440 300 432C310 430 314 426 320 426C326 426 330 430 340 432C378 440 430 384 424 312C418 232 350 226 320 250z",
            RED,
        )
        + L("M320 252Q316 214 332 194", BROWN, 9)
        + P("M330 226Q350 188 392 198Q366 236 330 226z", GREEN)
        + E(266, 300, 14, 30, W, fill_opacity=0.35, transform="rotate(20 266 300)")
    )


@art("citrus")
def citrus(c: Pal) -> str:
    return (
        C(280, 338, 94, ORANGE)
        + E(246, 300, 15, 26, W, fill_opacity=0.3, transform="rotate(30 246 300)")
        + P("M284 246Q300 212 336 214Q322 248 284 246z", GREEN)
        + C(280, 248, 5, GREEN_D)
        + C(394, 384, 58, ORANGE)
        + C(394, 384, 50, "#fde7b0")
        + C(394, 384, 44, "#fbbf24")
        + L("M394 342V426M352 384H436M364 354L424 414M364 414L424 354", "#fde7b0", 4)
        + C(394, 384, 7, "#fde7b0")
    )


@art("berries")
def berries(c: Pal) -> str:
    blue = "#4f5fd8"
    return (
        at(em_berry()(c), 296, 330, 4.3)
        + C(424, 404, 34, blue)
        + L("M412 386l12 8 12-8", "#2e3a9c", 5)
        + C(372, 424, 24, "#3f4fc6")
        + L("M364 412l8 5 8-5", "#2e3a9c", 4)
    )


@art("tomatoes")
def tomatoes(c: Pal) -> str:
    return (
        at(em_tomato()(c), 296, 336, 4.6)
        + E(254, 318, 14, 24, W, fill_opacity=0.35, transform="rotate(25 254 318)")
        + at(em_tomato()(c), 420, 408, 1.6)
    )


@art("fresh-herbs")
def fresh_herbs(c: Pal) -> str:
    s = L(
        "M320 440V310M320 440L268 300M320 440L376 300M320 440L300 250M320 440L346 244", GREEN_D, 6
    )
    for x, y, r in (
        (268, 300, -60),
        (376, 300, 20),
        (300, 250, -40),
        (346, 244, 0),
        (320, 312, -20),
        (240, 340, -80),
        (404, 346, 40),
        (282, 208, -30),
        (356, 196, 10),
        (322, 262, -10),
    ):
        s += at(em_leaf(GREEN if (x + y) % 3 else GREEN_L)(c), x, y, 1.5, r)
    return s + R(302, 396, 36, 22, c.I, 6)


def cup_container(c: Pal, pieces: str) -> str:
    """A clear clamshell with cut pieces inside."""
    return (
        pieces
        + R(206, 290, 228, 150, "#e0f2fe", 22, fill_opacity=0.35)
        + R(196, 266, 248, 34, "#f0f9ff", 16, fill_opacity=0.85)
        + R(274, 356, 92, 44, c.I, 8)
        + L("M290 372H350M290 386H334", W, 5)
        + shine("M218 310V420", 8, 0.7)
    )


@art("cut-fruit")
def cut_fruit(c: Pal) -> str:
    pcs = ""
    for x, y, col, r in (
        (244, 330, "#fb923c", 10),
        (300, 318, "#facc15", -8),
        (360, 326, "#bef264", 14),
        (408, 334, "#fb923c", -6),
        (262, 392, "#facc15", 4),
        (330, 388, "#fb7185", -12),
        (396, 394, "#facc15", 8),
    ):
        pcs += at(R(-24, -24, 48, 48, col, 8), x, y, 1, r)
    return cup_container(c, pcs)


@art("cut-vegetables", "vegetable-tray")
def cut_vegetables(c: Pal) -> str:
    pcs = ""
    for x, r in ((236, -20), (262, -8), (288, 6)):
        pcs += at(R(-10, -60, 20, 120, ORANGE, 8), x, 372, 1, r)
    for x, r in ((380, 12), (404, 24)):
        pcs += at(R(-12, -60, 24, 120, GREEN_L, 10), x, 372, 1, r)
    pcs += (
        C(330, 344, 22, GREEN)
        + C(350, 328, 20, GREEN_D)
        + C(316, 324, 18, GREEN)
        + R(326, 350, 12, 50, GREEN_L, 5)
    )
    return cup_container(c, pcs)


def potato_pile(c: Pal, col: str) -> str:
    eye = shade(col, 0.35)
    return (
        E(380, 396, 72, 46, shade(col, 0.08), transform="rotate(14 380 396)")
        + E(290, 366, 94, 64, col, transform="rotate(-12 290 366)")
        + C(252, 352, 4, eye)
        + C(304, 334, 4, eye)
        + C(320, 386, 4, eye)
        + C(402, 392, 4, eye)
        + E(262, 336, 20, 10, W, fill_opacity=0.3, transform="rotate(-20 262 336)")
    )


reg("potatoes", lambda c: potato_pile(c, "#cf9f62"))


@art("sweet-potatoes")
def sweet_potatoes(c: Pal) -> str:
    col = "#b5523b"
    return (
        P(
            "M188 404C226 334 362 300 460 330C424 404 300 432 188 404z",
            shade(col, 0.1),
            transform="translate(0 20)",
        )
        + P("M180 350C220 280 360 250 460 280C424 354 290 382 180 350z", col)
        + C(270, 318, 4, shade(col, 0.35))
        + C(380, 304, 4, shade(col, 0.35))
    )


def leafy_head(c: Pal, outer: str, inner: str) -> str:
    vein = mix(inner, 0.5)
    return (
        C(246, 372, 62, outer)
        + C(394, 372, 62, outer)
        + C(320, 398, 58, outer)
        + C(320, 332, 84, inner)
        + C(284, 318, 40, mix(inner, 0.2))
        + C(356, 318, 40, mix(inner, 0.2))
        + L(
            "M320 260V412M284 290Q300 330 320 340M356 290Q340 330 320 340M232 356Q260 372 280 400M408 356Q380 372 360 400",
            vein,
            5,
        )
    )


reg("lettuce", lambda c: leafy_head(c, GREEN, GREEN_L))
reg("leafy-greens", lambda c: leafy_head(c, GREEN_D, GREEN))
reg("cabbage", lambda c: leafy_head(c, "#7fbf6a", "#cdeeb5"))


@art("salad-greens")
def salad_greens(c: Pal) -> str:
    pcs = ""
    for x, y, r, col in (
        (236, 336, -50, GREEN),
        (282, 318, -20, GREEN_L),
        (330, 312, 10, GREEN_D),
        (378, 320, 40, GREEN),
        (414, 344, 70, GREEN_L),
        (258, 376, -30, GREEN_D),
        (320, 370, 0, GREEN),
        (384, 378, 30, GREEN_L),
    ):
        pcs += at(em_leaf(col)(c), x, y, 2, r)
    return cup_container(c, pcs)


def _greens(c: Pal) -> str:
    return "".join(
        at(em_leaf(col)(c), x, y, 0.9, r)
        for x, y, r, col in (
            (-16, -8, -40, GREEN),
            (10, -12, 20, GREEN_L),
            (0, 10, -10, GREEN_D),
            (-22, 14, -70, GREEN_L),
            (22, 12, 50, GREEN),
        )
    )


reg("salad-kit", lambda c: bag(c, _greens, window="#ecfccb"))


@art("peppers")
def peppers(c: Pal) -> str:
    body = "M0-78C40-96 100-78 106-10C112 60 72 100 38 96C24 94 16 88 0 88C-16 88-24 94-38 96C-72 100-112 60-106-10C-100-78-40-96 0-78z"

    def pep(col: str) -> str:
        return (
            P(body, col)
            + L("M-2-70V80", shade(col, 0.2), 6, stroke_opacity=0.5)
            + E(-50, -30, 12, 26, W, fill_opacity=0.3)
            + E(0, -78, 34, 10, GREEN)
            + P("M-8-76C-10-110 10-124 30-126L32-112C18-108 12-96 12-76z", GREEN_D)
        )

    return at(pep(YELLOW), 392, 370, 0.72) + at(pep(RED), 300, 344, 1)


@art("onions")
def onions(c: Pal) -> str:
    def onion(col: str) -> str:
        return (
            P(
                "M0-104C10-70 100-50 100 20C100 70 56 100 0 100C-56 100-100 70-100 20C-100-50-10-70 0-104z",
                col,
            )
            + L("M-24-50Q-54 20-22 92M24-50Q54 20 22 92", shade(col, 0.2), 5, stroke_opacity=0.6)
            + L("M0-102V-128", GREEN, 8)
        )

    return at(onion("#a8436a"), 404, 374, 0.66) + at(onion("#e0a458"), 294, 336, 1)


@art("melons")
def melons(c: Pal) -> str:
    return G(
        P("M190 300H450A130 130 0 0 1 190 300z", GREEN_D)
        + P("M202 300H438A118 118 0 0 1 202 300z", "#e9f9d2")
        + P("M212 300H428A108 108 0 0 1 212 300z", "#f25c6a")
        + "".join(
            E(x, y, 5, 9, INK, transform=f"rotate({r} {x} {y})")
            for x, y, r in (
                (270, 334, 20),
                (320, 352, 0),
                (370, 334, -20),
                (296, 380, 10),
                (346, 380, -10),
            )
        ),
        "rotate(-12 320 360) translate(0 20)",
    )


@art("squash")
def squash(c: Pal) -> str:
    return (
        P(
            "M300 222C332 214 346 240 344 280C342 320 404 338 404 390C404 430 372 444 330 440C288 436 240 420 246 378C252 338 292 320 290 280C288 240 288 224 300 222z",
            "#f3b562",
        )
        + R(306, 196, 14, 32, BROWN, 5)
        + E(270, 380, 12, 26, W, fill_opacity=0.3)
        + C(360, 408, 10, "#e29a45")
    )


@art("mushrooms")
def mushrooms(c: Pal) -> str:
    def mush(cap: str) -> str:
        return (
            P("M-24 0H24L20 62Q20 70 12 70H-12Q-20 70-20 62z", "#f4ebe0")
            + P("M-66 4C-66-50-24-74 0-74C24-74 66-50 66 4z", cap)
            + C(-28, -36, 7, W, fill_opacity=0.35)
            + C(18, -48, 5, W, fill_opacity=0.35)
        )

    return at(mush("#a47551"), 398, 384, 0.8) + at(mush("#c19a74"), 290, 370, 1)


@art("grapes")
def grapes(c: Pal) -> str:
    s = L("M320 244V206", BROWN, 8) + P("M324 222Q350 186 392 196Q370 234 324 222z", GREEN)
    k = 0
    for y, xs in (
        (268, (245, 295, 345, 395)),
        (316, (270, 320, 370)),
        (364, (295, 345)),
        (410, (320,)),
    ):
        for x in xs:
            k += 1
            s += C(x, y, 28, PURPLE if k % 2 else "#6b3fa3") + C(
                x - 9, y - 9, 6, W, fill_opacity=0.35
            )
    return s


@art("carrots")
def carrots(c: Pal) -> str:
    one = (
        L("M0 0L-16-52M0 0L0-60M0 0L16-50", GREEN, 8)
        + P("M-26 0Q0-12 26 0L5 184Q0 192-5 184z", ORANGE)
        + L("M-12 40h14M4 80h12M-8 120h10", shade(ORANGE, 0.2), 4)
    )
    return at(one, 290, 250, 1, -16) + at(one, 352, 256, 1, 14) + at(one, 322, 250, 1, 0)


@art("stone-fruit")
def stone_fruit(c: Pal) -> str:
    return (
        C(320, 350, 90, "#fdab7a")
        + E(290, 372, 62, 58, "#f47a5a", fill_opacity=0.55)
        + L("M322 262Q300 340 322 438", "#e8795c", 5, stroke_opacity=0.6)
        + L("M322 262Q318 240 330 226", BROWN, 8)
        + P("M332 238Q352 204 394 212Q370 248 332 238z", GREEN)
        + E(272, 316, 14, 26, W, fill_opacity=0.35, transform="rotate(20 272 316)")
    )


@art("pineapple")
def pineapple(c: Pal) -> str:
    s = (
        P("M320 276L284 196L312 240L320 170L328 240L356 196z", GREEN)
        + P("M320 280L262 222L300 256z", GREEN_D)
        + P("M320 280L378 222L340 256z", GREEN_D)
    )
    s += E(320, 360, 74, 86, "#f2b632")
    marks = ""
    for y in range(296, 436, 28):
        half = 74 * (1 - ((y - 360) / 86) ** 2) ** 0.5
        x = 320 - half + 20
        while x < 320 + half - 12:
            marks += f"M{x - 9:.0f} {y - 6}l9 6 9-6"
            x += 30
    return s + L(marks, "#c9861a", 4)


@art("pears")
def pears(c: Pal) -> str:
    return (
        P(
            "M320 232C340 232 346 262 350 290C356 326 410 350 410 396C410 432 372 444 320 444C268 444 230 432 230 396C230 350 284 326 290 290C294 262 300 232 320 232z",
            "#c3d44a",
        )
        + E(280, 390, 14, 30, W, fill_opacity=0.3)
        + L("M320 234Q318 212 330 198", BROWN, 8)
        + P("M328 216Q350 188 386 196Q364 226 328 216z", GREEN)
    )


@art("garlic")
def garlic(c: Pal) -> str:
    return (
        P(
            "M320 232C326 262 400 300 400 370C400 420 366 440 320 440C274 440 240 420 240 370C240 300 314 262 320 232z",
            "#f6efe4",
        )
        + L("M320 256V434M290 300Q268 370 292 434M350 300Q372 370 348 434", "#d9cbb6", 5)
        + L("M320 236V210", "#d9cbb6", 8)
    )


@art("cucumbers")
def cucumbers(c: Pal) -> str:
    def cuke(col: str) -> str:
        return (
            R(-130, -30, 260, 60, col, 30)
            + L("M-100-12H90", mix(col, 0.35), 6)
            + "".join(
                C(x, y, 3, mix(col, 0.5))
                for x, y in ((-80, 10), (-30, 14), (20, 8), (70, 14), (-54, -2), (46, -4))
            )
        )

    return at(cuke(GREEN), 330, 332, 1, -24) + at(cuke(GREEN_D), 310, 396, 1, -8)


@art("celery")
def celery(c: Pal) -> str:
    s = ""
    for x, y in ((262, 240), (294, 222), (330, 214), (364, 226), (390, 246)):
        s += at(em_leaf(GREEN)(c), x, y, 1.3, (x - 326) / 2)
    for x, r in ((282, -8), (306, -3), (334, 3), (358, 8)):
        s += at(R(-13, -150, 26, 190, "#b7de7c", 13) + L("M-4-130V30", "#d6efb0", 4), x, 400, 1, r)
    return s + R(292, 350, 56, 20, c.I, 6)


def florets(c: Pal, head: str, head2: str, stem: str, leaves: bool) -> str:
    s = ""
    if leaves:
        s += P("M220 400C200 340 240 320 270 350L320 400L370 350C400 320 440 340 420 400z", GREEN)
    s += P("M296 440L304 340H336L344 440z", stem)
    for x, y, r, col in (
        (262, 318, 44, head2),
        (378, 318, 44, head2),
        (320, 282, 54, head),
        (292, 342, 40, head),
        (348, 342, 40, head),
    ):
        s += C(x, y, r, col) + C(x - r * 0.3, y - r * 0.3, r * 0.3, mix(col, 0.3))
    return s


reg("broccoli", lambda c: florets(c, GREEN, GREEN_D, "#9ccc65", False))
reg("cauliflower", lambda c: florets(c, "#f7f1e1", "#ede3c8", "#e6dcc0", True))


@art("bananas")
def bananas(c: Pal) -> str:
    b = "M0 0C10 90 90 150 190 130C200 128 204 118 196 112C110 118 50 70 28-6z"
    s = ""
    for dx, dy, col in ((22, 50, YELLOW_D), (10, 25, "#f6bd33"), (0, 0, YELLOW)):
        s += at(P(b, col) + C(194, 120, 6, "#6b4f1d"), 222 + dx, 236 + dy)
    return s + R(212, 214, 22, 34, "#8a6d2b", 5)


@art("avocados")
def avocados(c: Pal) -> str:
    sh = "M0-104C36-104 52-60 66-20C84 28 76 100 0 100C-76 100-84 28-66-20C-52-60-36-104 0-104z"
    return (
        at(P(sh, "#3f6b2a"), 320, 338)
        + at(P(sh, "#b6d46a"), 320, 346, 0.88)
        + at(P(sh, "#e6f0a6"), 320, 350, 0.8)
        + C(320, 378, 36, "#8b5a2b")
        + C(308, 366, 10, W, fill_opacity=0.3)
    )


@art("asparagus")
def asparagus(c: Pal) -> str:
    s = ""
    for x, r in ((270, -10), (294, -5), (320, 0), (346, 5), (370, 10)):
        s += at(
            R(-9, -190, 18, 200, "#7cb342", 9)
            + P("M-12-176Q0-214 12-176z", "#557f2a")
            + L("M-5-120l8-6M-5-60l8-6", "#557f2a", 4),
            x,
            432,
            1,
            r,
        )
    return s + R(274, 366, 92, 24, c.I, 6)


@art("mangoes")
def mangoes(c: Pal) -> str:
    return (
        P(
            "M236 300C250 238 340 222 392 258C444 294 440 380 390 418C340 452 256 440 232 390C220 364 228 332 236 300z",
            "#f6a531",
        )
        + P(
            "M390 258C444 294 440 380 390 418C420 360 410 300 372 250z", "#ef6b4a", fill_opacity=0.8
        )
        + L("M300 244Q296 220 310 204", BROWN, 7)
        + P("M306 222Q330 190 370 200Q346 234 306 222z", GREEN)
        + E(262, 330, 12, 30, W, fill_opacity=0.35, transform="rotate(15 262 330)")
    )


@art("kiwi")
def kiwi(c: Pal) -> str:
    seeds = ""
    for i in range(10):
        a = i * math.pi / 5
        x, y = 392 + 31 * math.cos(a), 380 + 31 * math.sin(a)
        seeds += E(
            round(x),
            round(y),
            3,
            6,
            INK,
            transform=f"rotate({round(math.degrees(a)) + 90} {round(x)} {round(y)})",
        )
    return (
        E(282, 372, 90, 68, "#8b6a3e")
        + C(392, 380, 58, "#8b6a3e")
        + C(392, 380, 50, "#8cc63f")
        + C(392, 380, 16, "#f3f7d6")
        + seeds
    )


@art("green-beans")
def green_beans(c: Pal) -> str:
    s = ""
    for i, (y, r) in enumerate(((300, -8), (330, 4), (360, -4), (390, 8), (418, -2))):
        col = GREEN if i % 2 else GREEN_D
        s += at(
            L("M-120 0Q0-30 120 0", col, 22) + L("M-90-8Q0-28 90-8", mix(col, 0.35), 4),
            320,
            y,
            1,
            r,
        )
    return s


@art("corn")
def corn(c: Pal) -> str:
    k = ""
    for row in range(-2, 3):
        for col in range(-6, 7):
            if abs(row) == 2 and abs(col) > 4:
                continue
            k += C(col * 18, row * 20, 8, "#f5c542" if (row + col) % 2 else "#fbd96b")
    return (
        at(
            P("M-150 30C-80-10 20 10 90 60C20 70-80 60-150 30z", GREEN_D)
            + P("M-150-30C-80 10 20-10 90-60C20-70-80-60-150-30z", GREEN),
            330,
            350,
            1,
            -20,
        )
        + at(R(-130, -56, 260, 112, "#f0b429", 56) + k, 340, 334, 1, -20)
        + at(P("M-150 40C-90 10-20 30 40 70C-20 90-100 80-150 40z", GREEN), 300, 380, 1, -20)
    )


@art("cherries")
def cherries(c: Pal) -> str:
    col = "#c81d3a"
    return (
        L("M280 352Q296 280 340 222M374 342Q362 280 340 222", GREEN_D, 6)
        + P("M340 224Q370 190 410 200Q386 236 340 224z", GREEN)
        + C(280, 390, 46, col)
        + C(374, 380, 46, col)
        + C(264, 374, 10, W, fill_opacity=0.35)
        + C(358, 364, 10, W, fill_opacity=0.35)
    )


@art("brussels-sprouts")
def brussels(c: Pal) -> str:
    s = ""
    for x, y, r in ((262, 392, 46), (378, 396, 44), (320, 350, 50), (316, 414, 30)):
        col = GREEN_L if x == 320 else GREEN
        s += C(x, y, r, col) + L(
            f"M{x - r * 0.5:.0f} {y - r * 0.2:.0f}Q{x} {y + r * 0.5:.0f} {x + r * 0.5:.0f} {y - r * 0.2:.0f}",
            GREEN_D,
            4,
        )
    return s


# --- Meat & seafood --------------------------------------------------------------------------


@art("steak", "beef-roast")
def steak(c: Pal) -> str:
    return (
        R(172, 396, 296, 44, c.P, 14)
        + P(
            "M204 322C198 262 262 238 334 246C408 254 452 290 446 346C440 400 380 426 310 420C240 414 210 384 204 322z",
            MEAT,
            stroke=FAT,
            stroke_width=16,
            stroke_opacity=1,
        )
        + L(
            "M262 296Q300 318 290 360M344 286Q380 326 420 318M318 382Q360 372 382 402",
            W,
            6,
            stroke_opacity=0.5,
        )
        + at(em_leaf(GREEN)(c), 420, 262, 1.2, 30)
    )


@art("chicken", "frozen-chicken")
def chicken(c: Pal) -> str:
    bone = "#f7efe2"
    stick = (
        R(50, -15, 96, 30, bone, 15)
        + C(148, -17, 19, bone)
        + C(148, 17, 19, bone)
        + P(
            "M-124 0C-124-60-70-84-20-76C24-70 54-38 68-12L74 0L68 12C54 38 24 70-20 76C-70 84-124 60-124 0z",
            "#e39a4c",
        )
        + E(-70, -34, 30, 12, W, fill_opacity=0.35, transform="rotate(-10 -70 -34)")
        + L("M-60 20q20 10 40 4M-20 40q14 6 30 0", "#c9823b", 5)
    )
    return at(stick, 296, 350, 1, -28)


def meat_tray(c: Pal, content: str) -> str:
    return (
        P("M188 352H452L436 430Q434 440 422 440H218Q206 440 204 430z", W)
        + content
        + P("M186 356C200 300 440 300 454 356z", "#e0f2fe", fill_opacity=0.35)
        + R(178, 346, 284, 20, "#eef2f6", 10)
        + R(370, 380, 64, 40, c.I, 6)
        + L("M382 394H420M382 406H408", W, 4)
    )


def _ground(col: str) -> str:
    s = P("M218 350C212 300 280 280 320 286C380 278 432 300 424 350z", col)
    for x, y in (
        (250, 330),
        (280, 310),
        (318, 322),
        (350, 304),
        (390, 330),
        (300, 340),
        (370, 336),
        (236, 344),
    ):
        s += C(x, y, 7, shade(col, 0.2))
    return s


reg("ground-beef", lambda c: meat_tray(c, _ground("#c63b3b")))
reg("ground-turkey", lambda c: meat_tray(c, _ground("#e39a92")))
reg("ground-chicken", lambda c: meat_tray(c, _ground("#f0b7a4")))


@art("pork")
def pork(c: Pal) -> str:
    chop = "M-90 10C-100-40-40-66 20-60C80-54 110-20 96 14C84 44 40 40 10 50C-30 64-80 50-90 10z"
    return meat_tray(
        c,
        at(
            P(chop, "#f2a3a0", stroke=FAT, stroke_width=12, stroke_opacity=1)
            + E(-40, -10, 14, 10, FAT),
            318,
            326,
        ),
    )


@art("deli-meat")
def deli_meat(c: Pal) -> str:
    s = R(176, 404, 288, 30, W, 6)
    for x in (238, 290, 342, 394):
        s += (
            C(x, 356, 64, "#f6c1c6")
            + C(x, 356, 54, "#ec8e9b")
            + C(x - 16, 344, 6, "#f6c1c6")
            + C(x + 14, 370, 5, "#f6c1c6")
        )
    return s


@art("bacon")
def bacon(c: Pal) -> str:
    s = ""
    wave = "M0 0c30-22 60 22 90 0s60 22 90 0s60 22 90 0"
    for y in (270, 336, 402):
        s += at(
            L(wave, "#b83a34", 40)
            + L(wave, FAT, 12)
            + L("M0 -12c30-22 60 22 90 0s60 22 90 0s60 22 90 0", "#e0625c", 5),
            186,
            y,
        )
    return s


@art("sausage", "hot-dogs")
def sausage(c: Pal) -> str:
    link = R(-62, -28, 124, 56, "#b5562f", 28) + shine("M-40-12H36", 8, 0.35)
    return (
        at(link, 246, 382, 1, -22)
        + at(link, 342, 356, 1, 4)
        + at(link, 404, 300, 1, -58)
        + C(296, 364, 9, "#8c3f1f")
        + C(386, 334, 9, "#8c3f1f")
    )


@art("salmon", "fish")
def salmon(c: Pal) -> str:
    return (
        R(172, 400, 296, 40, c.P, 14)
        + P(
            "M186 356C214 290 330 270 446 292C466 316 456 380 434 400C330 424 240 410 186 356z",
            "#f7875f",
        )
        + P("M186 356C240 410 330 424 434 400L440 412C330 438 236 424 186 356z", "#c9d3db")
        + L(
            "M250 322Q270 352 252 390M300 306Q322 348 302 398M352 298Q374 346 354 402M402 296Q422 342 404 400",
            "#ffd2bf",
            6,
        )
        + at(em_leaf(GREEN)(c), 430, 270, 1.1, 20)
    )


@art("shrimp", "frozen-shrimp", "scallops")
def shrimp(c: Pal) -> str:
    arc = "M376 280A76 76 0 1 0 306 420"
    return (
        L(arc, "#f7875f", 58)
        + L(arc, "#e5673f", 58, stroke_dasharray="5 34", stroke_linecap="butt")
        + P("M300 420L346 392L352 446z", "#e5673f")
        + C(376, 278, 7, INK)
        + L("M384 262q30-30 60-20M380 268q34-10 56 10", "#e5673f", 4)
    )


@art("tofu")
def tofu(c: Pal) -> str:
    return (
        R(180, 390, 280, 50, c.I, 14)
        + L("M200 408H440", W, 4, stroke_opacity=0.5)
        + box3d(214, 300, 120, 96, 44, "#f8f4ea", "#fffdf7", "#e7dfcc")
        + box3d(330, 318, 86, 78, 34, "#f8f4ea", "#fffdf7", "#e7dfcc")
    )


@art("plant-based-meat")
def plant_patty(c: Pal) -> str:
    return (
        E(310, 396, 128, 42, "#5e3620")
        + E(310, 378, 128, 40, "#8a5634")
        + L("M230 370l40 20M280 360l50 26M340 358l48 24", "#5e3620", 7)
        + at(em_leaf(GREEN)(c), 400, 272, 2.6, 10)
    )


# --- Bakery ----------------------------------------------------------------------------------


@art("bread")
def bread(c: Pal) -> str:
    return (
        P("M262 440V300C262 250 302 226 362 226C422 226 462 250 462 300V440z", CRUST)
        + L("M318 262l20-18M362 258l20-18M406 262l20-18", "#e8a860", 7)
        + P(
            "M186 440V330C162 318 164 262 210 254C232 226 312 226 334 254C380 262 382 318 358 330V440z",
            CRUST,
        )
        + P(
            "M200 440V338C180 324 180 272 218 266C238 242 308 242 326 266C364 272 364 324 344 338V440z",
            CRUMB,
        )
        + C(240, 320, 5, "#e8c88a")
        + C(290, 300, 4, "#e8c88a")
        + C(306, 360, 5, "#e8c88a")
        + C(250, 390, 4, "#e8c88a")
    )


@art("tortillas")
def tortillas(c: Pal) -> str:
    s = ""
    for y in (426, 414, 402, 390, 378):
        s += E(320, y, 146, 36, "#e2bd7c") + E(320, y - 3, 144, 34, "#f6e2b3")
    for x, y in ((270, 370), (340, 362), (390, 378), (300, 388), (228, 378), (360, 392)):
        s += E(x, y, 10, 5, "#d6a45a")
    return s + P("M254 406H386V440H254z", c.I) + L("M274 422H366", W, 5)


@art("pita", "naan")
def flatbread(c: Pal) -> str:
    naan = "M-150 20C-150-40-40-80 60-70C140-62 160 0 130 40C90 80-150 90-150 20z"
    spots = "".join(
        E(x, y, 11, 6, "#c98a45", transform=f"rotate({x % 40 - 20} {x} {y})")
        for x, y in (
            (-90, 0),
            (-40, -30),
            (20, -40),
            (70, -20),
            (-60, 40),
            (0, 10),
            (60, 30),
            (100, 0),
        )
    )
    return at(P(naan, "#e2b872") + spots, 330, 330, 0.8, -10) + at(
        P(naan, "#efcd8f") + spots, 316, 380, 1, 4
    )


@art("pie")
def pie(c: Pal) -> str:
    crust = "#e2a55a"
    lattice = "M214 346H426M196 368H444M214 390H426M260 331V405M320 326V410M380 331V405"
    return (
        E(320, 392, 156, 56, c.I)
        + E(320, 380, 150, 54, "#c98a45")
        + E(320, 374, 136, 46, crust)
        + E(320, 370, 124, 40, "#a3243b")
        + L(lattice, crust, 14)
        + "".join(
            C(
                320 + 140 * math.cos(a / 8 * math.pi),
                374 + 50 * math.sin(a / 8 * math.pi),
                7,
                "#f0bd74",
            )
            for a in range(16)
        )
    )


@art("english-muffins")
def english_muffins(c: Pal) -> str:
    def half(tilt: float) -> str:
        return (
            E(0, 10, 110, 40, "#d9a15c")
            + E(0, 0, 110, 40, "#f3dcaa")
            + "".join(
                E(x, y, 7, 4, "#dfb877")
                for x, y in (
                    (-60, -6),
                    (-30, -20),
                    (10, -18),
                    (50, -8),
                    (-40, 14),
                    (0, 4),
                    (40, 16),
                    (70, 6),
                )
            )
        )

    return at(half(0), 330, 300, 0.85, -14) + at(half(0), 316, 392)


@art("bagels")
def bagels(c: Pal) -> str:
    def bagel(col: str) -> str:
        ring = "M-100 0a100 62 0 1 0 200 0a100 62 0 1 0-200 0zM-26-4a26 12 0 1 0 52 0a26 12 0 1 0-52 0z"
        return (
            E(0, 16, 100, 60, shade(col, 0.2))
            + P(ring, col, fill_rule="evenodd")
            + "".join(
                E(x, y, 5, 3, CREAM)
                for x, y in (
                    (-60, -20),
                    (-30, -40),
                    (20, -40),
                    (60, -18),
                    (-70, 16),
                    (70, 20),
                    (-20, 36),
                    (30, 38),
                )
            )
        )

    return at(bagel("#c98a48"), 330, 286, 0.8) + at(bagel("#d9a15c"), 316, 376)


@art("buns")
def buns(c: Pal) -> str:
    return (
        R(206, 374, 228, 56, "#e3a95e", 24)
        + R(212, 358, 216, 22, CRUMB, 10)
        + P("M200 364C200 282 260 250 320 250C380 250 440 282 440 364z", "#d9944a")
        + "".join(
            E(x, y, 7, 4, CREAM, transform=f"rotate({r} {x} {y})")
            for x, y, r in (
                (270, 300, -20),
                (318, 284, 0),
                (366, 302, 20),
                (296, 330, 10),
                (348, 328, -10),
                (238, 336, -30),
                (400, 334, 30),
            )
        )
        + E(262, 300, 16, 8, W, fill_opacity=0.25, transform="rotate(-30 262 300)")
    )


@art("cake")
def cake(c: Pal) -> str:
    frost = "#f472b6"
    return (
        E(320, 436, 150, 14, c.T)
        + R(214, 290, 212, 144, "#f9d9b5", 10)
        + R(214, 360, 212, 14, frost)
        + P(
            "M214 300Q214 288 226 288H414Q426 288 426 300V318Q416 342 404 320Q394 350 382 322Q370 340 356 318Q344 350 330 320Q318 342 304 318Q292 348 280 320Q268 340 256 318Q244 346 232 320Q222 336 214 322z",
            frost,
        )
        + C(270, 276, 15, RED)
        + C(320, 272, 15, RED)
        + C(370, 276, 15, RED)
    )


@art("muffins")
def muffins(c: Pal) -> str:
    return (
        P("M236 330H404L386 432Q384 440 376 440H264Q256 440 254 432z", c.I)
        + L("M270 338L276 436M304 338L306 436M336 338L334 436M370 338L364 436", c.D, 5)
        + P("M226 340C212 282 262 234 320 234C378 234 428 282 414 340z", "#c98646")
        + C(278, 298, 10, "#4b4f9e")
        + C(322, 270, 10, "#4b4f9e")
        + C(362, 306, 10, "#4b4f9e")
        + C(318, 318, 9, "#4b4f9e")
        + E(270, 270, 18, 9, W, fill_opacity=0.3, transform="rotate(-30 270 270)")
    )


@art("croissants", "pastries")
def croissants(c: Pal) -> str:
    col, dk = "#e39b45", "#c77d2c"
    return (
        E(214, 392, 28, 36, dk, transform="rotate(50 214 392)")
        + E(426, 392, 28, 36, dk, transform="rotate(-50 426 392)")
        + E(260, 352, 42, 54, col, transform="rotate(34 260 352)")
        + E(380, 352, 42, 54, col, transform="rotate(-34 380 352)")
        + E(320, 326, 52, 66, "#eba652")
        + L(
            "M300 280Q320 300 340 280M296 330Q320 350 344 330M246 330Q262 350 284 342M394 330Q378 350 356 342",
            dk,
            5,
        )
    )


@art("donuts")
def donuts(c: Pal) -> str:
    ring = "M-130 0a130 78 0 1 0 260 0a130 78 0 1 0-260 0zM-36 0a36 18 0 1 0 72 0a36 18 0 1 0-72 0z"
    icing = (
        "M-114-6a114 64 0 1 0 228 0a114 64 0 1 0-228 0zM-44-4a44 24 0 1 0 88 0a44 24 0 1 0-88 0z"
    )
    sprinkles = ""
    for i, (x, y) in enumerate(
        (
            (-80, -20),
            (-50, -44),
            (0, -52),
            (50, -42),
            (84, -16),
            (-86, 20),
            (86, 22),
            (-40, 38),
            (10, 44),
            (56, 36),
        )
    ):
        col = (YELLOW, "#60a5fa", W, "#34d399")[i % 4]
        sprinkles += R(x - 8, y - 3, 16, 6, col, 3, transform=f"rotate({(i * 47) % 180} {x} {y})")
    return at(
        E(0, 14, 130, 74, "#c98a48")
        + P(ring, "#e2a55e", fill_rule="evenodd")
        + P(icing, "#f472b6", fill_rule="evenodd")
        + f'<g stroke="none">{sprinkles}</g>',
        320,
        366,
    )


# --- Frozen ----------------------------------------------------------------------------------


def em_scoop(col: str = "#f9a8d4") -> Emblem:
    return lambda c: (
        P("M-14 4H14L0 26z", TAN) + C(0, -6, 15, col) + C(-8, -12, 4, W, fill_opacity=0.5)
    )


reg(
    "ice-cream",
    lambda c: tub(c, em_scoop(), top=210, w=156, body=c.I, lid=c.P, band=c.D),
    accent="#f9a8d4",
)


@art("frozen-novelty")
def frozen_novelty(c: Pal) -> str:
    return (
        R(306, 376, 28, 66, "#e4c28f", 10)
        + P("M264 230a56 56 0 0 1 112 0V380H264z", "#fbcfe8")
        + P(
            "M264 230a56 56 0 0 1 112 0V292Q360 312 346 292Q330 320 316 294Q300 316 286 292Q274 306 264 292z",
            "#7a4a2c",
        )
        + P("M376 240a14 14 0 0 1 0 28 14 14 0 0 1 0 28z", c.P)
        + shine("M284 312V360", 9, 0.6)
    )


@art("frozen-yogurt")
def frozen_yogurt(c: Pal) -> str:
    return (
        P("M268 324H372L320 444z", TAN)
        + L("M284 340L338 410M312 330L350 380M356 336L302 410M330 330L292 380", "#c08a4e", 4)
        + E(320, 318, 66, 24, "#fbcfe8")
        + E(320, 290, 54, 22, "#fbd5ea")
        + E(320, 264, 40, 18, "#fde2ef")
        + P("M306 250Q320 214 340 222Q330 238 334 250z", "#fde2ef")
    )


def em_veg(c: Pal) -> str:
    return (
        C(-14, -8, 9, GREEN)
        + C(6, -14, 9, GREEN)
        + C(-4, 10, 9, GREEN)
        + R(8, -2, 16, 16, ORANGE, 3)
        + R(-26, 4, 14, 14, ORANGE, 3)
        + R(-6, -26, 12, 12, YELLOW, 3)
    )


def em_fries(c: Pal) -> str:
    return "".join(
        R(x - 5, -26 + abs(x) // 2, 10, 44, YELLOW, 3, transform=f"rotate({x // 2} {x} 0)")
        for x in (-20, -8, 4, 16)
    ) + P("M-24 4H24L18 26H-18z", RED)


def em_frozen_berries(c: Pal) -> str:
    return (
        C(-10, 6, 11, "#4f5fd8")
        + C(10, 10, 10, "#7e4db8")
        + at(em_berry()(c), 4, -10, 0.6)
        + C(-14, -12, 9, "#c81d3a")
    )


def frost_bag(em: Callable[[Pal], str]) -> Draw:
    return lambda c: bag(c, em, window=c.P) + label_em(em_snow(c.I), c, 372, 216, 0.7)


reg("frozen-vegetables", frost_bag(em_veg))
reg("frozen-fruit", frost_bag(em_frozen_berries))
reg("frozen-potatoes", frost_bag(em_fries))


@art("frozen-meal")
def frozen_meal(c: Pal) -> str:
    return (
        P("M170 330L232 272H472L410 330z", "#3a4450")
        + P("M170 330H410V420H170z", "#2b333d")
        + P("M410 330L472 272V362L410 420z", "#222931")
        + P("M196 322L226 294H320L290 322z", "#f4d06f")
        + P("M300 322L330 294H420L390 322z", MEAT)
        + E(250, 308, 22, 8, "#f7df98")
        + L("M320 312l40-10M340 318l40-10", "#b83a34", 5)
        + R(170, 356, 240, 34, c.I)
        + label_em(em_snow(W), c, 290, 373, 0.55)
    )


@art("pizza")
def pizza(c: Pal) -> str:
    s = (
        E(320, 382, 150, 60, "#d99a4e")
        + E(320, 376, 134, 50, "#e8563f")
        + E(320, 376, 124, 44, "#f9d56e")
    )
    for x, y in (
        (260, 366),
        (320, 356),
        (380, 368),
        (290, 396),
        (352, 396),
        (230, 388),
        (410, 390),
    ):
        s += E(x, y, 17, 8, "#c0392b")
    s += L(
        "M320 376L196 376M320 376L444 376M320 376L240 336M320 376L400 416M320 376L400 336M320 376L240 416",
        "#e9b35c",
        3,
    )
    return s + at(em_leaf(GREEN)(c), 332, 330, 0.7, -20) + at(em_leaf(GREEN)(c), 380, 400, 0.6, 40)


@art("waffles")
def waffles(c: Pal) -> str:
    def waffle(col: str) -> str:
        cells = "".join(
            R(x - 14, y - 14, 28, 28, shade(col, 0.2), 5)
            for x in (-48, -16, 16, 48)
            for y in (-48, -16, 16, 48)
            if x * x + y * y < 4400
        )
        return C(0, 0, 90, col) + cells

    return (
        at(waffle("#e7ae5a"), 360, 330, 0.8, 10)
        + at(waffle("#efb865"), 300, 360, 1, -8)
        + R(282, 334, 40, 26, "#fde68a", 6)
    )


@art("fish-sticks")
def fish_sticks(c: Pal) -> str:
    stick = R(-90, -20, 180, 40, "#e3a04c", 12) + "".join(
        C(x, y, 3, "#b5752e") for x, y in ((-60, -6), (-20, 8), (20, -8), (60, 6))
    )
    lemon = P("M0 0L60-30A68 68 0 0 1 60 30z", YELLOW) + P(
        "M8 0L56-22A58 58 0 0 1 56 22z", "#fef3c7"
    )
    return (
        plate(c, 424, 160)
        + at(stick, 290, 404, 1, -4)
        + at(stick, 300, 364, 1, 6)
        + at(stick, 290, 322, 1, -6)
        + at(lemon, 386, 300, 1, -30)
    )


@art("chicken-nuggets")
def nuggets(c: Pal) -> str:
    blob = "M-40-10C-40-40 0-44 20-34C44-24 48 10 30 26C10 42-20 40-34 24C-44 14-40 4-40-10z"
    s = R(356, 360, 90, 76, c.I, 12) + E(401, 360, 45, 12, "#e5484d")
    for x, y, r, col in (
        (250, 400, 10, "#e7a64f"),
        (310, 404, -20, "#dd9a43"),
        (230, 340, -30, "#dd9a43"),
        (292, 346, 30, "#e7a64f"),
        (270, 290, 0, "#eab15f"),
    ):
        s += at(P(blob, col) + C(-10, -10, 3, "#b5752e") + C(12, 4, 3, "#b5752e"), x, y, 1, r)
    return s


@art("breakfast-sandwich")
def breakfast_sandwich(c: Pal) -> str:
    return (
        R(206, 392, 228, 44, "#e1b574", 20)
        + R(200, 374, 240, 26, "#8a4a2a", 12)
        + P("M196 368Q210 344 240 350Q270 334 320 342Q380 334 410 350Q440 346 446 368z", W)
        + E(300, 356, 26, 10, YELLOW)
        + P("M216 346H424L404 372H236z", "#f7b733")
        + P("M206 346C206 290 260 268 320 268C380 268 434 290 434 346z", "#e8bf7c")
        + E(260, 298, 14, 7, W, fill_opacity=0.35, transform="rotate(-25 260 298)")
    )


@art("burritos")
def burritos(c: Pal) -> str:
    return at(
        R(-140, -56, 280, 112, "#f0d39a", 56)
        + L("M-60-54Q-40 0-60 54M-10-56Q10 0-10 56", "#d9b273", 5)
        + P("M30-56H84A56 56 0 0 1 84 56H30z", SIL)
        + L("M50-40l14 10-10 10 14 10-10 10 14 10", SILD, 4)
        + C(-120, 0, 6, "#b5752e"),
        320,
        360,
        1,
        -18,
    )


# --- Pantry ----------------------------------------------------------------------------------


def em_penne(c: Pal) -> str:
    piece = P("M-22-7h34l10 14h-34z", YELLOW) + L("M-12-5l8 10M0-5l8 10", YELLOW_D, 2)
    return at(piece, -10, -12, 1, -20) + at(piece, 10, 0, 1, 25) + at(piece, -8, 14, 1, 5)


def em_grains(f: str = W) -> Emblem:
    return lambda c: "".join(
        E(x, y, 4, 8, f, transform=f"rotate({r} {x} {y})")
        for x, y, r in (
            (-14, -12, 30),
            (0, -16, -20),
            (14, -10, 40),
            (-18, 6, -30),
            (-4, 2, 10),
            (12, 8, -40),
            (-8, 18, 50),
            (8, 20, 0),
        )
    )


def em_macaroni(c: Pal) -> str:
    return "".join(
        at(L("M-8 6A10 10 0 0 1 8 6", YELLOW, 7), x, y, 1, r)
        for x, y, r in ((-12, -10, 20), (10, -12, -30), (0, 4, 60), (-14, 14, -10), (14, 12, 30))
    )


def em_almond(f: str = "#b07a4f") -> Emblem:
    return lambda c: at(
        P("M0-24C14-10 16 10 0 24C-16 10-14-10 0-24z", f)
        + L("M-2-14Q-6 0-2 14", shade(f, 0.25), 3),
        0,
        0,
        1,
        30,
    )


def em_chips(c: Pal) -> str:
    chip = P("M-16-10C-4-18 14-14 18 0C14 14-6 18-16 8-22 2-22-4-16-10z", "#f5c542")
    return at(chip, -8, -8, 1, -20) + at(chip, 10, 4, 1, 30) + at(chip, -6, 12, 1, 10)


def em_choc_chips(c: Pal) -> str:
    drop = P("M0-10C6-2 10 4 10 8A10 6 0 0 1-10 8C-10 4-6-2 0-10z", "#5b3a24")
    return (
        at(drop, -10, -8)
        + at(drop, 10, -4)
        + at(drop, 0, 12)
        + at(drop, -16, 12)
        + at(drop, 16, 14)
    )


def sack(
    c: Pal, em: Emblem | None, body: str | None = None, band: str | None = None, w: float = 176
) -> str:
    """A paper or poly sack with a folded top (rice, flour, pet food, soil)."""
    body = body or c.I
    x0, x1 = 320 - w / 2, 320 + w / 2
    return (
        P(
            f"M{x0 + 6} 208H{x1 - 6}L{x1 + 8} 418Q{x1 + 10} 440 {x1 - 12} 440H{x0 + 12}Q{x0 - 10} 440 {x0 - 8} 418z",
            body,
        )
        + R(x0 + 4, 180, w - 8, 36, shade(body, 0.15), 6)
        + L(f"M{x0 + 14} 206H{x1 - 14}", W, 3, stroke_dasharray="8 8", stroke_opacity=0.7)
        + (R(x0 - 2, 262, w + 4, 112, band) if band else "")
        + label_em(em, c, 320, 318, 1.9)
        + shine(f"M{x0 + 14} 236L{x0 + 8} 408", 10, 0.4)
    )


def squeeze(c: Pal, body: str, em: Emblem | None = None, cap: str = W) -> str:
    return (
        P("M306 178L316 140H324L334 178z", cap)
        + R(282, 172, 76, 46, cap, 12)
        + P(
            "M282 214H358Q394 228 394 272V412Q394 440 366 440H274Q246 440 246 412V272Q246 228 282 214z",
            body,
        )
        + R(262, 298, 116, 92, W, 14)
        + label_em(em, c, 320, 344, 1.3)
        + shine("M262 250V282M262 402V420", 9, 0.45)
    )


reg("cereal", lambda c: box(c, em_bowl(W, YELLOW)))
reg("granola", lambda c: pouch(c, em_bowl(W, TAN)), accent="#b07a4f")
reg("baking-mix", lambda c: box(c, em_cake()))
reg("pancake-mix", lambda c: box(c, em_pancakes()))
reg("mac-and-cheese", lambda c: box(c, em_macaroni, y=250, h=190, front=c.A), accent="#2563eb")
reg("canned-beans", lambda c: food_can(c, em_beans(), band=c.A))
reg("canned-tomatoes", lambda c: food_can(c, em_tomato(), label=RED_D, band=YELLOW))
reg("soup", lambda c: food_can(c, em_steam(), label=RED, band=W))
reg("canned-vegetables", lambda c: food_can(c, em_veg, label=GREEN_D, band=YELLOW))
reg("canned-fruit", lambda c: food_can(c, em_fruit(ORANGE), label="#f59e0b", band=W))
reg("chili", lambda c: food_can(c, em_pepper(), label="#7f1d1d", band=YELLOW))
reg("pasta-sauce", lambda c: jar(c, "#c0392b", em_tomato(), lid=GREEN_D))
reg("salsa", lambda c: jar(c, "#c2412d", em_pepper(), lid=INK), accent="#ef4444")
reg("peanut-butter", lambda c: jar(c, "#c68642", em_peanut(), lid=RED))
reg("nut-butter", lambda c: jar(c, "#b07a4f", em_almond(), lid=c.I))
reg("mayonnaise", lambda c: jar(c, "#fbf3dc", em_egg(YELLOW), lid="#2563eb"))
reg("applesauce", lambda c: jar(c, "#ecd38b", em_fruit(RED), lid=GREEN))
reg("queso", lambda c: jar(c, "#f2b233", em_pepper(GREEN), lid=RED))
reg("bean-dip", lambda c: jar(c, "#8a5a3c", em_beans(), lid=GREEN_D))
reg("broth", lambda c: brick(c, em_steam()))
reg("rice", lambda c: sack(c, em_grains()))
reg("flour", lambda c: sack(c, em_wheat(), body="#f5ecd8", band=c.I))
reg("sugar", lambda c: sack(c, em_cube(), body=W, band="#2563eb"))
reg("grains", lambda c: pouch(c, em_grains(TAN), window=W), accent="#84cc16")
reg("baking-chips", lambda c: bag(c, em_choc_chips, window=CREAM))
reg("cooking-oil", lambda c: bottle(c, "#e2b53b", em_drop(YELLOW), cap=GREEN_D, label=GREEN_D))
reg("vinegar", lambda c: bottle(c, "#9f2b3a", em_fruit(RED), cap=INK, label=W))
reg("salad-dressing", lambda c: bottle(c, "#f3e2b8", em_leaf(), cap=GREEN, label=c.I, neck=22))
reg("soy-sauce", lambda c: bottle(c, "#3b2418", em_leaf(GREEN_L), cap=RED, label=W, neck=14, w=100))
reg(
    "hot-sauce",
    lambda c: bottle(c, "#c81d25", em_pepper(), cap=GREEN_D, label=W, neck=12, w=84, shoulder=250),
)
reg("syrup", lambda c: bottle(c, "#b45a1c", em_maple(), cap=RED, label=W, neck=16, w=128))
reg("ketchup", lambda c: squeeze(c, RED, em_tomato()))
reg("mustard", lambda c: squeeze(c, YELLOW, em_wheat(YELLOW_D), cap=RED))
reg("bbq-sauce", lambda c: squeeze(c, "#6b2d1a", em_pepper(), cap=INK))


@art("spices", "salt")
def spices(c: Pal) -> str:
    def jar_(fill: str) -> str:
        return (
            R(-36, -64, 72, 150, "#eaf2f8")
            + R(-36, -34, 72, 120, fill, 10)
            + R(-36, 0, 72, 44, W)
            + R(-40, -96, 80, 38, INK, 8)
            + "".join(C(x, -84, 3, W) for x in (-16, 0, 16))
        )

    return (
        at(jar_("#c2410c"), 250, 354, 0.92)
        + at(jar_(GREEN_D), 390, 354, 0.92)
        + at(jar_("#6b5e57"), 320, 354)
    )


@art("oatmeal")
def oatmeal(c: Pal) -> str:
    return (
        R(248, 214, 144, 226, c.I)
        + E(320, 440, 72, 14, c.I)
        + E(320, 214, 72, 16, c.T)
        + R(248, 206, 144, 16, c.D)
        + E(320, 206, 72, 14, c.M)
        + R(248, 276, 144, 108, W, 0, fill_opacity=0.95)
        + label_em(em_bowl(c.I, TAN), c, 320, 330, 1.6)
        + shine("M262 236V260M262 398V424", 9, 0.45)
    )


@art("jam")
def jam(c: Pal) -> str:
    return (
        jar(c, "#8e1b3a", em_berry(), lid=RED)
        + P(
            "M232 212Q320 176 408 212L398 254Q384 244 370 256Q356 244 342 256Q328 244 314 256Q300 244 286 256Q272 244 258 256Q246 244 242 254z",
            RED,
        )
        + "".join(
            R(x, y, 14, 14, W, 2, fill_opacity=0.8)
            for x, y in (
                (258, 212),
                (298, 200),
                (338, 200),
                (378, 212),
                (278, 232),
                (318, 222),
                (358, 232),
            )
        )
    )


@art("canned-fish")
def canned_fish(c: Pal) -> str:
    def tin(label: str) -> str:
        return (
            R(-110, 0, 220, 70, label)
            + E(0, 70, 110, 18, shade(label, 0.2))
            + E(0, 0, 110, 24, SIL)
            + E(0, 0, 98, 18, SILD)
            + E(-54, -2, 18, 8, "none", stroke=INK, stroke_width=5)
            + label_em(em_fish(W), c, 30, 38, 1.4)
        )

    return at(tin(c.A), 330, 300, 0.85) + at(tin(c.I), 310, 350)


@art("honey")
def honey(c: Pal) -> str:
    amber = "#f2a51a"
    return (
        C(260, 250, 22, amber)
        + C(380, 250, 22, amber)
        + C(320, 272, 62, amber)
        + E(320, 380, 92, 70, amber)
        + R(290, 172, 60, 42, c.I, 8)
        + P("M310 172L320 146L330 172z", c.I)
        + R(262, 352, 116, 58, W, 12)
        + label_em(em_letter("HONEY", c.D, 22), c, 320, 381, 1)
        + C(298, 262, 7, "#8a5a1c")
        + C(342, 262, 7, "#8a5a1c")
        + E(320, 290, 12, 8, "#8a5a1c")
        + E(276, 310, 10, 24, W, fill_opacity=0.35)
    )


@art("sweetener")
def sweetener(c: Pal) -> str:
    def packet(col: str) -> str:
        return (
            R(-66, -46, 132, 92, col, 8)
            + R(-66, -46, 132, 16, shade(col, 0.15), 6)
            + L("M-40 6H40M-40 22H20", W, 6)
        )

    return (
        at(packet("#60a5fa"), 270, 380, 1, -14)
        + at(packet(YELLOW), 370, 380, 1, 12)
        + at(packet("#f472b6"), 320, 340, 1, -2)
    )


@art("pasta")
def pasta(c: Pal) -> str:
    return box(c, em_penne, window=CREAM) + f'<g stroke="none">{at(em_penne(c), 432, 420, 1.8)}</g>'


@art("ramen")
def ramen(c: Pal) -> str:
    return (
        L("M380 240L430 160M396 248L454 170", "#d9a066", 9)
        + P("M236 250L260 428Q262 440 276 440H364Q378 440 380 428L404 250z", c.I)
        + P("M242 300H398L392 350H248z", W)
        + L("M262 326c10-10 20 10 30 0s20 10 30 0s20 10 30 0s20 10 30 0", YELLOW_D, 5)
        + E(320, 250, 86, 18, SIL)
        + E(320, 247, 74, 12, "#fbe7b5")
    )


# --- Snacks ----------------------------------------------------------------------------------


def em_puffs(c: Pal) -> str:
    return "".join(
        at(L("M-10 0q5-8 10 0t10 0", ORANGE, 9), x, y, 1, r)
        for x, y, r in ((-10, -10, 20), (8, 0, -30), (-6, 12, 60))
    )


def em_trail(c: Pal) -> str:
    return (
        em_almond()(c)
        + C(-16, 12, 6, RED)
        + C(16, -14, 6, "#60a5fa")
        + C(18, 14, 6, YELLOW)
        + C(-18, -14, 6, "#6b3fa3")
    )


def em_dried(c: Pal) -> str:
    return C(-10, -6, 12, ORANGE) + C(10, 4, 12, "#f59e0b") + C(-4, 14, 8, "#6b3fa3")


def em_gummies(c: Pal) -> str:
    def bear(col: str) -> str:
        return C(0, -8, 7, col) + E(0, 6, 8, 10, col) + C(-5, -14, 3, col) + C(5, -14, 3, col)

    return at(bear(RED), -14, 0) + at(bear("#34d399"), 4, -6) + at(bear(YELLOW), 16, 8)


def em_jerky(c: Pal) -> str:
    return at(P("M-24-6C-10-16 10 0 24-10L20 8C6 16-12 2-22 10z", "#7a3b1e"), 0, 0, 1, -15)


def em_seaweed(c: Pal) -> str:
    return R(-22, -16, 44, 32, "#2f4f2f", 4) + L("M-16-8H16M-16 0H16M-16 8H16", "#476b47", 2)


reg("chips", lambda c: bag(c, em_chips, window="#fde68a"))
reg("pork-rinds", lambda c: bag(c, em_chips, window=CREAM, body=INK), accent=RED)
reg("cheese-puffs", lambda c: bag(c, em_puffs, window="#fed7aa", body=ORANGE))
reg("corn-chips", lambda c: bag(c, em_chips, window="#fef3c7", body=c.D))
reg("trail-mix", lambda c: pouch(c, em_trail, window=W))
reg("nuts", lambda c: pouch(c, em_almond(), window="#fdf1dc"))
reg("dried-fruit", lambda c: pouch(c, em_dried, window=W))
reg("fruit-snacks", lambda c: pouch(c, em_gummies, window=W))
reg("jerky", lambda c: pouch(c, em_jerky, window="#f5e6d3", body=INK))
reg("seaweed-snacks", lambda c: box(c, em_seaweed, y=280, h=160, w=190, x=214, front=GREEN_D))


def wrapped_bar(c: Pal, inside: str, dots: str, body: str | None = None) -> str:
    body = body or c.I
    zz = "".join("l8 12l-8 12" for _ in range(4))
    return at(
        R(-150, -34, 80, 68, inside, 10)
        + "".join(
            C(x, y, 5, dots)
            for x, y in ((-134, -16), (-116, 8), (-100, -10), (-128, 18), (-90, 14))
        )
        + R(-100, -46, 220, 92, body, 6)
        + P(f"M120-48{zz}H120z", shade(body, 0.2))
        + P("M-100-46l-8 10 8 12-8 12 8 12-8 12 8 10z", shade(body, 0.2))
        + R(-60, -24, 140, 48, W, 24, fill_opacity=0.9)
        + R(-40, -8, 100, 16, body, 8, fill_opacity=0.6),
        330,
        350,
        1,
        -16,
    )


reg("protein-bar", lambda c: wrapped_bar(c, "#6b4226", "#8a5a3c"))
reg("granola-bar", lambda c: wrapped_bar(c, "#e0b36a", "#b07a3c", body=GREEN_D))
reg("fruit-nut-bar", lambda c: wrapped_bar(c, "#c98a4a", RED, body=c.A))


@art("candy")
def candy(c: Pal) -> str:
    def piece(col: str) -> str:
        return (
            P("M-40 0L-80-30V30z", col)
            + P("M40 0L80-30V30z", col)
            + C(0, 0, 44, col)
            + L("M-26-30Q0 0-26 30M0-44Q26 0 0 44M26-30Q52 0 26 30", W, 6, stroke_opacity=0.7)
        )

    return (
        at(piece("#8b5cf6"), 380, 300, 0.75, 30)
        + at(piece(YELLOW_D), 250, 330, 0.75, -20)
        + at(piece(RED), 320, 390, 1, -8)
    )


@art("rice-cakes")
def rice_cakes(c: Pal) -> str:
    s = ""
    for y in (410, 368, 326):
        s += (
            E(320, y + 18, 110, 30, "#dcc38c")
            + R(210, y - 12, 220, 30, "#dcc38c")
            + E(320, y - 12, 110, 30, "#f1e2b8")
        )
        s += "".join(C(x, y - 12 + (x % 3) * 5 - 5, 4, "#e2cc93") for x in range(240, 410, 26))
    return s


@art("chocolate")
def chocolate(c: Pal) -> str:
    grid = "".join(R(x, y, 42, 34, "#6b4226", 5) for x in (-104, -58, -12) for y in (-40, 2))
    return at(
        R(-112, -48, 150, 96, "#5b3a24", 8)
        + grid
        + P("M28-52H124V52H28L40 36 26 20 40 4 26-12 40-28z", SIL)
        + R(56, -56, 76, 112, c.I, 4)
        + label_em(em_star(W), c, 94, 0, 1),
        320,
        350,
        1,
        -18,
    )


@art("cookies")
def cookies(c: Pal) -> str:
    def cookie(col: str) -> str:
        return C(0, 0, 76, col) + "".join(
            P(
                "M0-8C6-4 8 2 6 6-2 10-8 6-8 0-6-6 0-8 0-8z",
                "#5b3a24",
                transform=f"translate({x} {y}) rotate({x * 3})",
            )
            for x, y in ((-30, -30), (20, -40), (40, 4), (-10, 10), (-44, 20), (14, 44), (-8, -32))
        )

    return at(cookie("#c98a48"), 386, 334, 0.8) + at(cookie("#d9a060"), 290, 362)


@art("crackers")
def crackers(c: Pal) -> str:
    def cracker(col: str) -> str:
        return R(-62, -62, 124, 124, col, 10) + "".join(
            C(x, y, 5, shade(col, 0.2)) for x in (-34, 0, 34) for y in (-34, 0, 34)
        )

    return (
        at(cracker("#dcaa5c"), 380, 330, 0.9, 14)
        + at(cracker("#e8bb6c"), 262, 336, 0.9, -12)
        + at(cracker("#f0c679"), 322, 380, 1, 4)
    )


@art("tortilla-chips")
def tortilla_chips(c: Pal) -> str:
    chip = P("M0-70L62 44Q64 52 56 52H-56Q-64 52-62 44z", "#f5c542")
    return (
        at(chip, 256, 312, 0.9, -24)
        + at(chip, 384, 312, 0.9, 20)
        + at(chip, 320, 296, 1, 2)
        + at(chip, 290, 330, 0.8, -50)
        + at(chip, 352, 332, 0.8, 50)
        + P("M186 350H454Q446 440 320 440Q194 440 186 350z", c.I)
        + E(320, 350, 134, 14, c.D)
        + shine("M216 372Q240 420 300 430", 9, 0.35)
    )


@art("popcorn")
def popcorn(c: Pal) -> str:
    s = ""
    for x, y in (
        (262, 262),
        (298, 240),
        (338, 238),
        (378, 258),
        (318, 270),
        (284, 286),
        (356, 284),
        (248, 294),
        (392, 292),
    ):
        s += C(x, y, 24, "#fff4c6") + C(x + 8, y - 6, 12, W)
    s += P("M238 294H402L380 440H260z", W)
    s += P("M262 294H290L296 440H274zM318 294H346L344 440H322zM374 294H400L382 440H366z", RED)
    return s


@art("pretzels")
def pretzels(c: Pal) -> str:
    path = "M262 408C196 380 200 280 262 268C318 258 344 336 320 380C296 336 322 258 378 268C440 280 444 380 378 408M262 408L372 318M378 408L268 318"
    return (
        L(path, "#8a4a22", 34)
        + L(path, "#b8692f", 24)
        + "".join(
            R(x, y, 8, 4, W, 2, stroke="none")
            for x, y in (
                (230, 320),
                (260, 282),
                (380, 282),
                (410, 330),
                (300, 350),
                (338, 350),
                (270, 396),
                (366, 396),
            )
        )
    )


# --- Beverages -------------------------------------------------------------------------------


reg(
    "cold-brew",
    lambda c: bottle(c, "#3b2418", em_bean("#6b4226"), cap=c.I, label=W, neck=24, w=120),
    accent=INK,
)


@art("coffee")
def coffee(c: Pal) -> str:
    brown = "#4a3426"
    return (
        P("M250 200H390L398 424Q398 440 382 440H258Q242 440 242 424z", brown)
        + R(250, 178, 140, 28, "#3a281c", 4)
        + R(236, 196, 168, 10, SILD, 4)
        + C(320, 330, 52, W)
        + label_em(em_bean("#6b4226"), c, 320, 330, 1.6)
        + C(358, 238, 10, "#3a281c")
        + f'<g stroke="none">{at(em_bean("#6b4226")(c), 430, 424, 1.1)}{at(em_bean("#5a3a26")(c), 206, 428, 1, -60)}</g>'
    )


reg("soda", lambda c: can(c, c.A, em_bubbles(), stripe=W), accent=RED)
reg(
    "sparkling-water",
    lambda c: can(c, c.P, em_bubbles(c.I), slim=True, stripe=c.A),
    accent="#84cc16",
)
reg("energy-drink", lambda c: can(c, INK, em_bolt(c.A), slim=True, stripe=c.I), accent="#a3e635")
reg("juice", lambda c: carton(c, em_fruit(ORANGE), band=c.I), accent=ORANGE)
reg("water", lambda c: pet_bottle(c, "#dbeefe", cap=c.I, label=c.I, em=em_drop()))
reg(
    "sports-drink",
    lambda c: pet_bottle(c, c.A, cap=INK, label=INK, em=em_bolt(c.A)),
    accent="#22d3ee",
)
reg(
    "electrolyte-drink",
    lambda c: pet_bottle(c, c.AL, cap=c.A, label=W, em=em_drop(c.A)),
    accent="#ec4899",
)
reg("iced-tea", lambda c: pet_bottle(c, "#c47a2c", cap=YELLOW, label=W, em=em_fruit(YELLOW)))
reg("protein-shake", lambda c: dairy_bottle(c, em_bolt(YELLOW), label=INK), accent=INK)
reg("kombucha", lambda c: bottle(c, "#b5651d", em_leaf(), cap=INK, label=W, neck=20))


@art("tea")
def tea(c: Pal) -> str:
    return (
        box3d(214, 262, 170, 178, 44, c.I, c.T, c.D)
        + R(228, 284, 142, 108, W, 12, fill_opacity=0.95)
        + label_em(em_cup(c.I), c, 299, 338, 1.8)
        + L("M340 262Q372 240 408 300", INK, 3)
        + R(386, 300, 56, 70, "#ead7b2", 8)
        + R(398, 376, 30, 28, c.A, 4)
        + L("M414 300V376", INK, 3)
    )


# --- Household -------------------------------------------------------------------------------


def jug(c: Pal, body: str, em: Emblem | None = None, cap: str | None = None) -> str:
    cap = cap or c.A
    outer = "M246 440Q226 440 226 420V244Q226 206 262 204H290V196H336V204H378Q414 206 414 244V420Q414 440 394 440z"
    hole = "M350 226h30a10 10 0 0 1 10 10v24a10 10 0 0 1-10 10h-30a10 10 0 0 1-10-10v-24a10 10 0 0 1 10-10z"
    return (
        R(284, 166, 58, 36, cap, 6)
        + R(280, 194, 66, 10, shade(cap, 0.2), 3)
        + P(outer + hole, body, fill_rule="evenodd")
        + R(246, 296, 148, 112, W, 16)
        + label_em(em, c, 320, 352, 1.6)
        + shine("M242 292V408", 10, 0.4)
    )


reg("laundry-detergent", lambda c: jug(c, c.I, em_bubbles(c.I)), accent="#f97316")
reg("fabric-softener", lambda c: jug(c, "#8b5cf6", em_flower()), accent="#f472b6")


@art("dish-soap", "rinse-aid")
def dish_soap(c: Pal) -> str:
    return (
        P("M310 178L320 146L330 178z", c.I)
        + R(298, 174, 44, 36, c.I, 8)
        + P(
            "M296 206H344Q372 218 372 256V424Q372 440 356 440H284Q268 440 268 424V256Q268 218 296 206z",
            c.A,
        )
        + R(268, 290, 104, 100, W)
        + label_em(em_bubbles(c.I), c, 320, 340, 1.4)
        + shine("M284 240V276", 9, 0.5)
    )


@art("toilet-bowl-cleaner")
def toilet_bowl_cleaner(c: Pal) -> str:
    return (
        L("M322 262L344 200L388 186", c.A, 36)
        + at(R(-16, -18, 32, 36, c.I, 6), 400, 182, 1, -70)
        + P(
            "M272 250H372Q392 250 392 272V424Q392 440 376 440H268Q252 440 252 424V272Q252 250 272 250z",
            c.A,
        )
        + R(252, 310, 140, 96, W)
        + label_em(em_drop(c.I), c, 322, 358, 1.3)
    )


reg("all-purpose-cleaner", lambda c: spray_bottle(c, c.I, em_bubbles(c.I)), accent="#f59e0b")
reg("glass-cleaner", lambda c: spray_bottle(c, "#38bdf8", em_star(c.I), head=c.I))
reg("bathroom-cleaner", lambda c: spray_bottle(c, c.A, em_drop(c.I), head=INK), accent="#34d399")
reg("stain-remover", lambda c: spray_bottle(c, "#f97316", em_star(c.I), head=c.I))


@art("trash-bags")
def trash_bags(c: Pal) -> str:
    bag_ = c.D
    return (
        P(
            "M240 440C196 440 196 330 238 290C258 270 288 262 298 250L292 216C300 206 340 206 348 216L342 250C352 262 382 270 402 290C444 330 444 440 400 440z",
            bag_,
        )
        + P("M300 220L264 178L298 196L320 168L342 196L376 178L340 220z", bag_)
        + R(298, 226, 44, 16, c.A, 5)
        + L("M262 320Q250 370 262 420M300 300Q290 360 300 424", W, 6, stroke_opacity=0.25)
    )


@art("batteries", "battery-charger")
def batteries(c: Pal) -> str:
    def cell(top: str) -> str:
        return (
            R(-10, -124, 20, 16, SILD, 4)
            + R(-30, -110, 60, 220, INK, 12)
            + R(-30, -110, 60, 74, top, 12)
            + R(-30, -48, 60, 12, top)
            + label_em(em_bolt(W), c, 0, 30, 1.1)
        )

    return at(cell(c.A), 250, 330, 0.92) + at(cell(c.A), 390, 330, 0.92) + at(cell(c.A), 320, 330)


@art("toilet-paper")
def toilet_paper(c: Pal) -> str:
    return (
        roll(c, 386, 290, 136, 62)
        + roll(c, 268, 252, 172, 76)
        + P("M344 330V420Q360 436 380 430V332z", W)
    )


@art("paper-towels")
def paper_towels(c: Pal) -> str:
    dots = "".join(C(x, y, 4, c.T) for x in (270, 300, 330, 360) for y in (230, 270, 310, 350, 390))
    return (
        roll(c, 316, 196, 228, 74)
        + dots
        + P("M376 300H420V440H376z", W)
        + L("M384 330H412M384 370H412", c.T, 4)
    )


@art("facial-tissues")
def facial_tissues(c: Pal) -> str:
    return (
        box3d(214, 294, 180, 146, 48, c.I, c.T, c.D)
        + E(328, 282, 56, 10, c.D)
        + P("M290 282C280 242 314 220 326 244C338 214 380 226 366 262C382 266 374 286 362 286z", W)
        + label_em(em_flower(W), c, 304, 368, 1.6)
    )


@art("dryer-sheets")
def dryer_sheets(c: Pal) -> str:
    return (
        P("M268 262L300 190H392L372 262z", W)
        + box3d(222, 262, 170, 178, 44, c.A, mix(c.A, 0.4), shade(c.A, 0.2))
        + R(236, 290, 142, 110, W, 14)
        + label_em(em_flower(c.I), c, 307, 345, 1.6)
    )


@art("light-bulbs")
def light_bulbs(c: Pal) -> str:
    def bulb() -> str:
        return (
            P("M-30 36C-30 10-70-10-70-54A70 70 0 1 1 70-54C70-10 30 10 30 36z", "#fff3b0")
            + L("M-16 30V-10L0-26L16-10V30", "#e0a41c", 5)
            + R(-32, 36, 64, 44, SILD, 6)
            + L("M-32 50H32M-32 64H32", "#94a3b8", 4)
            + R(-18, 80, 36, 16, INK, 6)
            + E(-34, -70, 12, 22, W, fill_opacity=0.8, transform="rotate(30 -34 -70)")
        )

    return L("M250 196l-16-16M390 196l16-16M320 170v-22", c.A, 7) + at(bulb(), 320, 328)


@art("food-storage-bags")
def food_storage_bags(c: Pal) -> str:
    return (
        R(250, 206, 170, 214, "#e0f2fe", 16)
        + R(250, 206, 170, 20, c.A, 6)
        + R(214, 236, 180, 204, "#eef8ff", 16, fill_opacity=0.95)
        + R(214, 236, 180, 22, c.I, 6)
        + R(366, 226, 30, 42, c.A, 8)
        + R(236, 300, 110, 50, W, 8)
        + L("M252 318H330M252 334H306", c.T, 5)
        + shine("M230 276V420", 8, 0.8)
    )


@art("sponges")
def sponges(c: Pal) -> str:
    return (
        box3d(200, 340, 200, 80, 56, YELLOW, "#fde68a", YELLOW_D)
        + P("M200 340l56-28h200l-56 28z", GREEN)
        + P("M200 318l56-28h200v22l-56 28H200z", GREEN_D)
        + P("M200 318l56-28h200l-56 28z", GREEN)
        + "".join(
            C(x, y, 5, YELLOW_D)
            for x, y in ((230, 370), (270, 392), (320, 364), (360, 396), (250, 404), (380, 372))
        )
    )


@art("disinfecting-wipes", "cleaning-wipes")
def wipes_canister(c: Pal) -> str:
    return (
        R(250, 236, 140, 204, c.I, 22)
        + R(244, 210, 152, 44, c.A, 16)
        + E(320, 214, 56, 10, shade(c.A, 0.2))
        + P("M300 212C290 180 318 160 330 178C346 158 366 180 350 204z", W)
        + R(262, 300, 116, 94, W, 12)
        + label_em(em_bubbles(c.I), c, 320, 347, 1.3)
    )


def long_box(c: Pal, sheet: str, band: str) -> str:
    return (
        P("M200 356L180 420H430L440 356z", sheet, fill_opacity=0.95)
        + box3d(168, 316, 280, 76, 52, band, mix(band, 0.4), shade(band, 0.2))
        + E(468, 328, 16, 26, shade(band, 0.4))
        + E(468, 328, 8, 13, SIL)
        + R(190, 334, 120, 40, W, 8)
        + L("M206 350H292M206 362H260", band, 5)
        + P("M168 392H448L430 440H186z", sheet)
    )


reg("aluminum-foil", lambda c: long_box(c, SIL, c.I))
reg("plastic-wrap", lambda c: long_box(c, "#e0f2fe", c.A), accent="#ef4444")
reg("parchment-paper", lambda c: long_box(c, "#f3e7c9", "#b45309"))


@art("dishwasher-detergent")
def dishwasher_pods(c: Pal) -> str:
    def pod(a: str) -> str:
        return (
            R(-46, -42, 92, 84, "#60a5fa", 30)
            + P("M-46 0Q-46-42 0-42H10Q-10 0 10 42H0Q-46 42-46 0z", W, fill_opacity=0.85)
            + C(14, 0, 16, a)
            + E(-20, -22, 10, 6, W)
        )

    return (
        at(pod(c.A), 260, 400, 0.85, -12)
        + at(pod(GREEN), 380, 400, 0.85, 12)
        + at(pod(c.A), 320, 330, 1, -4)
    )


@art("dryer-balls")
def dryer_balls(c: Pal) -> str:
    def ball(col: str) -> str:
        return C(0, 0, 58, col) + L(
            "M-40-20Q0 20 40-20M-44 14Q0 50 44 14M-30-40Q0-10 30-40", shade(col, 0.12), 5
        )

    return (
        at(ball("#f5efe4"), 254, 392, 0.8)
        + at(ball("#d6d3d1"), 386, 392, 0.8)
        + at(ball("#e7ddd0"), 320, 318)
    )


# --- Health & wellness -----------------------------------------------------------------------

reg("multivitamin", lambda c: pill_bottle(c, em_letter("A–Z", W, 28)), accent="#f59e0b")
reg("vitamin-d", lambda c: pill_bottle(c, em_letter("D", W, 46)), accent=YELLOW_D)
reg("vitamin-c", lambda c: pill_bottle(c, em_letter("C", W, 46)), accent=ORANGE)
reg("vitamin-b12", lambda c: pill_bottle(c, em_letter("B12", W, 34)), accent="#ef4444")
reg("magnesium", lambda c: pill_bottle(c, em_letter("Mg", W, 40)), accent="#8b5cf6")
reg("calcium", lambda c: pill_bottle(c, em_letter("Ca", W, 40)), accent="#0ea5e9")
reg("biotin", lambda c: pill_bottle(c, em_letter("B7", W, 40)), accent="#ec4899")
reg("melatonin", lambda c: pill_bottle(c, em_moon()), accent="#6366f1")
reg("probiotic", lambda c: pill_bottle(c, em_capsule(W, YELLOW)), accent="#14b8a6")
reg("fish-oil", lambda c: pill_bottle(c, em_drop(YELLOW), body="#fef3c7"), accent="#0ea5e9")
reg("omega-3", lambda c: pill_bottle(c, em_fish(W)), accent="#f59e0b")
reg(
    "elderberry",
    lambda c: pill_bottle(
        c,
        lambda c: (
            C(-10, -6, 10, PURPLE)
            + C(10, -6, 10, PURPLE)
            + C(0, 10, 10, "#6b3fa3")
            + L("M0-16V-26", W, 3)
        ),
    ),
    accent=PURPLE,
)
reg(
    "protein-powder",
    lambda c: tub(c, em_bolt(YELLOW), top=204, w=190, body=c.I, lid=INK, band=INK),
    accent=INK,
)
reg(
    "collagen",
    lambda c: tub(c, em_drop(c.I), top=246, w=170, body=W, lid=c.A, band=c.P),
    accent="#f472b6",
)
reg(
    "fiber-supplement",
    lambda c: tub(c, em_wheat(YELLOW), top=220, w=150, body=c.I, lid=c.A),
    accent="#f59e0b",
)


@art("electrolyte-mix")
def electrolyte_mix(c: Pal) -> str:
    return (
        stick_pack(c, "#f472b6", 260, -16)
        + stick_pack(c, "#22d3ee", 380, 16)
        + stick_pack(c, c.I, 320, 0)
        + label_em(em_drop(W), c, 320, 330, 1.1)
    )


@art("bandages")
def bandages(c: Pal) -> str:
    def band() -> str:
        return (
            R(-140, -38, 280, 76, "#f2c29b", 38)
            + R(-44, -30, 88, 60, "#fbe3cf", 8)
            + "".join(C(x, y, 3, "#d9a27a") for x in (-100, -80, 80, 100) for y in (-12, 12))
        )

    return at(band(), 320, 340, 1, -32) + at(band(), 320, 340, 1, 32)


@art("thermometer")
def thermometer(c: Pal) -> str:
    return at(
        P("M-150-26H100Q130-26 140 0Q130 26 100 26H-150Q-164 26-164 12V-12Q-164-26-150-26z", W)
        + R(-110, -16, 90, 32, c.P, 6)
        + T(-65, 12, "98.6", c.D, 26)
        + R(40, -12, 24, 24, c.A, 12)
        + L("M100-26H150", SILD, 4)
        + P("M140 0L178-8V8z", SILD),
        320,
        330,
        1,
        -30,
    )


@art("first-aid-kit")
def first_aid_kit(c: Pal) -> str:
    return (
        P(
            "M280 262V232Q280 218 294 218H346Q360 218 360 232V262",
            "none",
            stroke=c.D,
            stroke_width=16,
            stroke_opacity=1,
        )
        + R(200, 256, 240, 184, c.I, 26)
        + R(200, 330, 240, 12, c.D)
        + label_em(em_cross(W), c, 320, 336, 2.4)
    )


@art("ice-pack")
def ice_pack(c: Pal) -> str:
    return (
        R(206, 262, 228, 172, "#7dd3fc", 34)
        + R(222, 278, 196, 140, "#bae6fd", 24)
        + L("M226 290H414M226 406H414", "#38bdf8", 6)
        + label_em(em_snow(c.I), c, 320, 348, 2)
    )


@art("pill-organizer")
def pill_organizer(c: Pal) -> str:
    s = R(176, 336, 288, 94, c.T, 16)
    for i, col in enumerate(
        ("#f87171", "#fb923c", "#facc15", "#4ade80", "#38bdf8", "#818cf8", "#f472b6")
    ):
        x = 186 + i * 39.5
        s += R(x, 316, 34, 44, col, 8) + R(x + 4, 368, 26, 48, W, 6)
    return s + C(206, 392, 6, "#f472b6") + C(248, 390, 6, YELLOW)


# --- Baby ------------------------------------------------------------------------------------


@art("baby-food")
def baby_food(c: Pal) -> str:
    return (
        R(296, 150, 48, 36, c.A, 10)
        + R(304, 182, 32, 30, W)
        + P("M264 212H376L394 418Q396 440 374 440H266Q244 440 246 418z", c.I)
        + R(262, 280, 116, 106, W, 16)
        + label_em(em_fruit(ORANGE), c, 320, 333, 1.6)
        + shine("M268 230L262 270", 9, 0.5)
    )


@art("baby-wipes")
def baby_wipes(c: Pal) -> str:
    return (
        R(190, 290, 260, 150, c.P, 40)
        + R(254, 306, 132, 60, c.I, 24)
        + R(270, 318, 100, 36, c.D, 18)
        + P("M290 330C286 300 318 288 326 306C340 288 362 304 350 330z", W)
        + label_em(em_heart(c.I), c, 320, 402, 1.2)
    )


@art("baby-snacks")
def baby_snacks(c: Pal) -> str:
    return (
        R(260, 234, 120, 206, c.I, 18)
        + R(252, 210, 136, 36, c.A, 12)
        + R(260, 292, 120, 96, W)
        + label_em(em_star(YELLOW), c, 320, 340, 1.5)
        + "".join(C(x, 430, 10, "#f8dfa6") for x in (212, 236, 404, 428))
        + C(224, 410, 10, "#f8dfa6")
    )


@art("diapers", "training-pants", "swim-diapers")
def diapers(c: Pal) -> str:
    return (
        R(180, 274, 46, 50, c.A, 12)
        + R(414, 274, 46, 50, c.A, 12)
        + P(
            "M200 262H440V300Q440 334 418 352Q380 382 372 428Q370 440 358 440H282Q270 440 268 428Q260 382 222 352Q200 334 200 300z",
            W,
        )
        + R(200, 262, 240, 28, c.T)
        + label_em(em_star(c.I), c, 320, 344, 1.3)
    )


@art("baby-bottles", "sippy-cup")
def baby_bottles(c: Pal) -> str:
    return (
        P("M298 204Q298 150 320 150Q342 150 342 204z", "#f3d9a6")
        + R(272, 196, 96, 40, c.A, 12)
        + R(262, 232, 116, 208, "#f5fbff", 30)
        + R(266, 300, 108, 136, CREAM, 26)
        + L("M340 270H374M350 310H374M340 350H374M350 390H374", c.I, 5)
        + shine("M280 252V420", 9, 0.9)
    )


reg("diaper-cream", lambda c: tube(c, W, em_heart(W)))
reg("baby-wash", lambda c: pump_bottle(c, c.P, em_bubbles(c.I)))
reg("baby-lotion", lambda c: pump_bottle(c, W, em_heart(c.I)))
reg("baby-oil", lambda c: bottle(c, "#fde2ef", em_drop(c.I), cap=c.I, label=W, neck=20))


@art("pacifier", "bottle-brush")
def pacifier(c: Pal) -> str:
    return (
        C(320, 256, 50, "none", stroke=c.A, stroke_width=18, stroke_opacity=1)
        + P("M212 330Q320 280 428 330Q420 380 320 372Q220 380 212 330z", c.I)
        + C(320, 330, 26, c.D)
        + P("M300 356Q300 440 320 440Q340 440 340 356z", "#f3d9a6")
    )


@art("bibs", "baby-towel", "swaddle")
def bibs(c: Pal) -> str:
    return (
        P(
            "M232 230C232 204 262 196 280 212C300 246 340 246 360 212C378 196 408 204 408 230C408 260 440 300 432 360C424 420 380 440 320 440C260 440 216 420 208 360C200 300 232 260 232 230z",
            c.T,
        )
        + P(
            "M280 212C300 246 340 246 360 212",
            "none",
            stroke=c.I,
            stroke_width=14,
            stroke_opacity=1,
        )
        + R(260, 360, 120, 44, c.P, 14)
        + label_em(em_heart(c.I), c, 320, 312, 1.4)
    )


# --- Pet supplies ----------------------------------------------------------------------------


@art("dog-food")
def dog_food(c: Pal) -> str:
    kibble = "".join(
        E(x, y, 11, 8, "#a8642f")
        for x, y in ((190, 432), (212, 424), (440, 430), (420, 436), (452, 420))
    )
    return sack(c, em_bone(W), body=c.I, band=c.A, w=210) + kibble


@art("cat-food")
def cat_food(c: Pal) -> str:
    def pcan(label: str) -> str:
        return (
            R(-80, 0, 160, 86, label)
            + E(0, 86, 80, 14, shade(label, 0.2))
            + E(0, 0, 80, 18, SIL)
            + E(0, 0, 70, 13, SILD)
            + label_em(em_fish(W), c, 0, 46, 1.5)
        )

    return at(pcan(c.A), 320, 262, 0.9) + at(pcan(c.I), 256, 342) + at(pcan(c.I), 390, 342, 0.9)


@art("cat-litter", "litter-box")
def cat_litter(c: Pal) -> str:
    return (
        P(
            "M262 236Q262 170 320 170Q378 170 378 236",
            "none",
            stroke=INK,
            stroke_width=12,
            stroke_opacity=1,
        )
        + P("M232 236H408L394 428Q392 440 380 440H260Q248 440 246 428z", c.I)
        + R(224, 224, 192, 30, c.D, 10)
        + R(250, 290, 140, 100, W, 14)
        + label_em(em_paw(c.I), c, 320, 340, 1.5)
    )


@art("dog-treats")
def dog_treats(c: Pal) -> str:
    bone = em_bone("#d59b5b")
    return (
        at(bone(c), 262, 400, 2.6, -20)
        + at(bone(c), 380, 396, 2.4, 24)
        + at(bone(c), 320, 330, 3, -6)
    )


@art("pet-bed")
def pet_bed(c: Pal) -> str:
    ring = "M-160 0a160 58 0 1 0 320 0a160 58 0 1 0-320 0zM-112-6a112 34 0 1 0 224 0a112 34 0 1 0-224 0z"
    return at(
        E(0, 22, 160, 54, c.D)
        + E(0, -4, 112, 34, c.P)
        + P(ring, c.I, fill_rule="evenodd")
        + label_em(em_paw(c.M), c, 0, -2, 1.1),
        320,
        384,
    )


@art("dog-toy")
def dog_toy(c: Pal) -> str:
    rope = "M190 300Q260 250 320 320T450 330"
    return (
        L(rope, "#e7d7bd", 30)
        + L(rope, c.A, 30, stroke_dasharray="14 18", stroke_linecap="butt")
        + C(196, 300, 26, c.A)
        + C(446, 330, 26, c.A)
        + C(320, 390, 50, "#c6e14b")
        + L("M280 364Q320 390 280 418M360 364Q320 390 360 418", W, 6)
    )


@art("poop-bags")
def poop_bags(c: Pal) -> str:
    def rl(col: str) -> str:
        return (
            E(0, 0, 36, 60, shade(col, 0.2))
            + R(-120, -60, 120, 120, col)
            + E(-120, 0, 36, 60, col)
            + E(-120, 0, 14, 22, W)
        )

    return at(rl(c.A), 390, 300, 0.8) + at(rl(GREEN), 420, 390)


@art("dog-leash", "dog-harness", "dog-collar", "cat-collar")
def dog_collar(c: Pal) -> str:
    return (
        E(320, 320, 120, 70, "none", stroke=c.I, stroke_width=26, stroke_opacity=1)
        + R(206, 300, 30, 44, SILD, 6)
        + C(320, 392, 10, "none", stroke=SILD, stroke_width=6, stroke_opacity=1)
        + P("M320 404L352 420L346 440H294L288 420z", YELLOW)
        + label_em(em_paw(YELLOW_D), c, 320, 424, 0.5)
    )


@art("pet-bowl")
def pet_bowl(c: Pal) -> str:
    kib = "".join(
        E(x, y, 13, 9, "#a8642f")
        for x, y in (
            (250, 352),
            (280, 340),
            (312, 348),
            (344, 338),
            (376, 350),
            (296, 332),
            (360, 330),
            (390, 340),
        )
    )
    return (
        kib
        + P("M200 356H440L416 430Q412 440 398 440H242Q228 440 224 430z", c.I)
        + E(320, 356, 120, 14, c.D)
        + label_em(em_bone(W), c, 320, 400, 1.3)
    )


# --- Beauty & personal care ------------------------------------------------------------------

reg("sunscreen", lambda c: tube(c, W, em_sun(), band=c.A), accent="#f59e0b")
reg("after-sun", lambda c: tube(c, "#dcfce7", em_leaf(), band=c.I))
reg("face-wash", lambda c: tube(c, W, em_bubbles(W), band=c.I))
reg("shampoo", lambda c: flip_bottle(c, c.I, em_drop(c.I)), accent="#f59e0b")
reg("conditioner", lambda c: flip_bottle(c, c.A, em_leaf(), label=W), accent="#a78bfa")
reg("body-wash", lambda c: flip_bottle(c, "#38bdf8", em_bubbles(c.I)), accent="#0ea5e9")
reg("body-lotion", lambda c: pump_bottle(c, c.P, em_drop(c.I)), accent="#f472b6")
reg("mouthwash", lambda c: bottle(c, "#34d399", em_drop(W), cap=W, label=c.I, neck=26, w=124))
reg("shaving-cream", lambda c: aerosol(c, c.I, em_bubbles(c.I)), accent=INK)
reg("dry-shampoo", lambda c: aerosol(c, c.A, em_drop(c.I)), accent="#a78bfa")


@art("face-moisturizer", "eye-cream", "hair-styling")
def cosmetic_jar(c: Pal) -> str:
    return (
        R(222, 330, 196, 110, c.P, 24)
        + R(222, 360, 196, 50, W)
        + label_em(em_drop(c.I), c, 320, 385, 1)
        + R(214, 290, 212, 52, c.A, 16)
        + R(214, 328, 212, 10, c.AD)
        + shine("M240 306H300", 8, 0.5)
    )


@art("face-serum")
def face_serum(c: Pal) -> str:
    return (
        P("M306 200Q306 150 320 150Q334 150 334 200z", INK)
        + R(296, 196, 48, 44, SIL, 8)
        + R(266, 236, 108, 204, "#f6c77a", 24)
        + R(266, 300, 108, 88, W)
        + label_em(em_drop("#f59e0b"), c, 320, 344, 1.3)
        + shine("M282 252V286", 9, 0.6)
    )


@art("toothpaste")
def toothpaste(c: Pal) -> str:
    return at(
        P("M-150-50H60L120-22V22L60 50H-150z", W)
        + R(-160, -54, 26, 108, SIL, 4)
        + P("M-110-50H20V50H-110z", c.I)
        + R(120, -20, 40, 40, c.A, 6)
        + label_em(em_star(W), c, -46, 0, 1.4)
        + L("M172 0q20-20 40 0t30-10", "#e0f2fe", 18),
        300,
        360,
        1,
        -14,
    )


@art("toothbrush", "toothbrush-heads", "electric-toothbrush")
def toothbrush(c: Pal) -> str:
    bristles = "".join(
        R(x, -34, 10, 28, "#e0f2fe" if i % 2 else W, 3) for i, x in enumerate(range(-150, -86, 13))
    )
    return at(
        bristles
        + R(-160, -10, 90, 26, c.A, 12)
        + R(-80, -6, 240, 22, c.A, 11)
        + R(20, -8, 110, 26, c.I, 12),
        320,
        340,
        1,
        -24,
    )


@art("deodorant")
def deodorant(c: Pal) -> str:
    return (
        R(268, 250, 104, 190, c.I, 30)
        + R(268, 170, 104, 100, c.A, 30)
        + R(268, 250, 104, 16, c.AD)
        + R(268, 300, 104, 80, W, 0, fill_opacity=0.95)
        + label_em(em_leaf(c.I), c, 320, 340, 1.1)
        + shine("M284 190V232", 9, 0.5)
    )


@art("lip-balm", "lip-color", "mascara", "foundation", "makeup-remover")
def lip_balm(c: Pal) -> str:
    return (
        R(254, 280, 64, 160, c.I, 12)
        + P("M262 280V218Q262 196 286 190L310 184V280z", c.A)
        + R(334, 300, 72, 140, INK, 12)
        + R(334, 250, 72, 60, SIL, 8)
        + R(346, 360, 48, 50, c.A, 6)
    )


@art("razor", "razor-cartridges", "beard-trimmer")
def razor(c: Pal) -> str:
    return at(
        R(-18, -40, 36, 220, c.I, 18)
        + L("M-6 40V160", c.D, 4)
        + R(-70, -90, 140, 50, c.A, 12)
        + R(-62, -82, 124, 10, SIL, 4)
        + R(-62, -66, 124, 10, SIL, 4),
        320,
        280,
        1,
        18,
    )


@art("bar-soap")
def bar_soap(c: Pal) -> str:
    return (
        box3d(210, 346, 190, 70, 56, c.T, c.P, c.M)
        + P("M218 346l56-28h186", "none", stroke=W, stroke_width=4, stroke_opacity=0.6)
        + label_em(em_flower(c.I), c, 305, 381, 1.2)
        + C(282, 272, 20, "none", stroke=c.M, stroke_width=6, stroke_opacity=1)
        + C(326, 252, 12, "none", stroke=c.M, stroke_width=5, stroke_opacity=1)
        + C(362, 280, 16, "none", stroke=c.M, stroke_width=5, stroke_opacity=1)
    )


@art("dental-floss")
def dental_floss(c: Pal) -> str:
    return (
        R(250, 260, 140, 180, c.I, 30)
        + P("M250 290Q250 240 300 240H340Q390 240 390 290z", c.A)
        + L("M320 240Q360 200 420 210", W, 4)
        + label_em(em_star(W), c, 320, 356, 1.3)
    )


@art("nail-polish", "nail-polish-remover", "nail-care", "makeup-sponges", "makeup-brushes")
def nail_polish(c: Pal) -> str:
    return (
        R(292, 150, 56, 110, INK, 10)
        + R(300, 250, 40, 20, SIL)
        + P(
            "M270 280Q270 264 290 264H350Q370 264 370 280L380 420Q380 440 360 440H280Q260 440 260 420z",
            c.A,
        )
        + shine("M282 290L278 410", 10, 0.5)
    )


@art("hair-dryer", "flat-iron")
def hair_dryer(c: Pal) -> str:
    return (
        R(290, 290, 52, 150, c.A, 20)
        + R(220, 216, 200, 96, c.I, 48)
        + C(392, 264, 34, c.D)
        + C(392, 264, 20, INK)
        + R(170, 240, 60, 48, c.D, 10)
        + C(316, 350, 8, W)
    )


reg("cat-treats", lambda c: pouch(c, em_fish(), window=W), accent="#f59e0b")


@art("cat-toy")
def cat_toy(c: Pal) -> str:
    return (
        L("M366 400Q420 420 440 380T470 330", c.A, 6)
        + C(300, 350, 88, c.A)
        + L(
            "M232 320Q300 360 360 280M226 360Q300 410 380 300M252 410Q330 420 386 340M270 270Q300 330 250 390",
            shade(c.A, 0.2),
            6,
        )
    )


@art("cat-scratcher")
def cat_scratcher(c: Pal) -> str:
    return (
        R(196, 408, 248, 32, c.I, 10)
        + R(290, 196, 60, 216, "#e7d7bd")
        + L(
            "M290 220H350M290 250H350M290 280H350M290 310H350M290 340H350M290 370H350M290 400H350",
            "#c9b28c",
            5,
        )
        + R(236, 176, 168, 30, c.I, 10)
        + L("M390 206V260", c.A, 4)
        + C(390, 274, 16, c.A)
    )


@art("puppy-pads")
def puppy_pads(c: Pal) -> str:
    return at(
        R(-140, -100, 280, 200, W, 20)
        + R(-116, -76, 232, 152, "#e0f2fe", 12)
        + L("M-116-26H116M-116 26H116M-40-76V76M40-76V76", "#bae6fd", 5)
        + label_em(em_paw(c.I), c, 0, 0, 1.6),
        320,
        350,
        1,
        -8,
    )


@art("heating-pad")
def heating_pad(c: Pal) -> str:
    return (
        L("M300 250Q310 220 300 196M340 250Q350 220 340 196M260 250Q270 220 260 196", "#f97316", 8)
        + R(196, 262, 248, 150, c.A, 30)
        + L("M216 312H424M216 362H424", shade(c.A, 0.15), 6)
        + L("M444 380Q480 400 470 440", INK, 6)
        + R(440, 408, 40, 32, W, 8)
    )


@art("medical-tape", "gauze", "elastic-bandage")
def tape_roll(c: Pal) -> str:
    ring = (
        "M-100 0a100 100 0 1 0 200 0a100 100 0 1 0-200 0zM-46 0a46 46 0 1 0 92 0a46 46 0 1 0-92 0z"
    )
    return at(
        P("M0 100H160V140H0z", W)
        + P(ring, W, fill_rule="evenodd", transform="translate(14 8)")
        + P(ring, "#f8fafc", fill_rule="evenodd")
        + C(0, 0, 46, "none", stroke=c.T, stroke_width=10)
        + C(0, 0, 86, "none", stroke=c.P, stroke_width=4),
        300,
        320,
        1,
    )


# --- Electronics -----------------------------------------------------------------------------


@art("tv")
def tv(c: Pal) -> str:
    return (
        L("M214 384L200 440M426 384L440 440", INK, 10)
        + R(160, 196, 320, 196, INK, 14)
        + R(172, 208, 296, 170, c.I)
        + P("M172 378L300 208H340L212 378z", W, fill_opacity=0.14)
        + P("M232 378L360 208H376L248 378z", W, fill_opacity=0.14)
    )


@art("monitor")
def monitor(c: Pal) -> str:
    return (
        R(306, 376, 28, 52, SILD)
        + E(320, 434, 76, 10, SILD)
        + R(182, 206, 276, 176, INK, 12)
        + R(192, 216, 256, 150, c.P)
        + R(206, 230, 110, 70, c.I, 6)
        + R(328, 230, 106, 30, c.T, 6)
        + R(328, 270, 106, 30, c.T, 6)
        + R(206, 312, 228, 40, c.M, 6)
    )


@art("headphones")
def headphones(c: Pal) -> str:
    return (
        L("M222 340A98 98 0 0 1 418 340", INK, 24)
        + R(190, 300, 64, 118, c.I, 28)
        + R(386, 300, 64, 118, c.I, 28)
        + R(240, 316, 24, 86, INK, 12)
        + R(376, 316, 24, 86, INK, 12)
        + shine("M206 320V360", 8, 0.4)
    )


@art("earbuds")
def earbuds(c: Pal) -> str:
    def bud() -> str:
        return R(-12, 0, 24, 80, W, 12) + C(0, 0, 28, W) + C(10, -6, 12, c.I)

    return (
        E(320, 312, 96, 34, c.P)
        + at(bud(), 282, 300, 1, -8)
        + at(bud(), 358, 300, 1, 8)
        + P("M216 330H424V392Q424 440 376 440H264Q216 440 216 392z", W)
        + C(320, 380, 6, "#22c55e")
    )


@art("bluetooth-speaker")
def bluetooth_speaker(c: Pal) -> str:
    dots = "".join(C(x, y, 5, c.D) for x in range(238, 404, 22) for y in (330, 352, 374, 396))
    return (
        R(196, 292, 248, 148, c.I, 74)
        + dots
        + R(290, 300, 60, 16, INK, 8)
        + R(186, 330, 22, 72, INK, 11)
        + R(432, 330, 22, 72, INK, 11)
    )


@art("usb-c-charger", "car-charger")
def charger(c: Pal) -> str:
    return (
        R(290, 174, 16, 50, SILD, 4)
        + R(334, 174, 16, 50, SILD, 4)
        + R(254, 214, 132, 150, W, 24)
        + label_em(em_bolt(c.I), c, 320, 290, 1.5)
        + L("M320 364V384Q320 420 360 420H420", INK, 12)
        + R(414, 406, 40, 28, SILD, 8)
    )


@art("power-bank")
def power_bank(c: Pal) -> str:
    return (
        R(236, 206, 168, 234, INK, 26)
        + R(252, 222, 136, 150, c.I, 16)
        + label_em(em_bolt(W), c, 320, 296, 1.8)
        + "".join(C(x, 404, 6, "#22c55e" if x < 340 else "#475569") for x in (290, 310, 330, 350))
    )


@art("wireless-charger")
def wireless_charger(c: Pal) -> str:
    return (
        E(320, 408, 150, 34, INK)
        + E(320, 396, 150, 34, "#334155")
        + at(R(-60, -100, 120, 200, INK, 18) + R(-52, -90, 104, 180, c.I, 12), 320, 356, 1, 0)
        + label_em(em_bolt(W), c, 320, 356, 1.4)
    )


@art("printer-ink")
def printer_ink(c: Pal) -> str:
    def cart(col: str) -> str:
        return (
            R(-40, -80, 80, 160, INK, 10) + R(-40, -40, 80, 70, col) + R(-14, 80, 28, 14, SILD, 3)
        )

    return (
        at(cart("#06b6d4"), 240, 340, 0.9)
        + at(cart("#ec4899"), 320, 340, 0.9)
        + at(cart(YELLOW), 400, 340, 0.9)
    )


@art("usb-c-cable", "hdmi-cable", "usb-hub")
def cable(c: Pal) -> str:
    return (
        E(320, 350, 110, 62, "none", stroke=INK, stroke_width=12, stroke_opacity=1)
        + E(330, 340, 90, 48, "none", stroke="#475569", stroke_width=12, stroke_opacity=1)
        + L("M220 360Q190 400 200 430M424 330Q470 300 460 250", INK, 12)
        + R(186, 420, 30, 20, SILD, 4)
        + R(180, 404, 42, 22, c.I, 8)
        + R(446, 226, 30, 22, SILD, 4)
        + R(440, 242, 42, 24, c.I, 8)
    )


@art("streaming-device")
def streaming_device(c: Pal) -> str:
    return (
        R(360, 196, 72, 244, INK, 34)
        + C(396, 250, 22, "#475569")
        + C(396, 250, 8, c.I)
        + C(380, 310, 8, "#94a3b8")
        + C(412, 310, 8, "#94a3b8")
        + C(380, 342, 8, "#94a3b8")
        + C(412, 342, 8, "#94a3b8")
        + R(196, 360, 140, 56, INK, 14)
        + R(166, 372, 36, 32, SILD, 5)
        + C(304, 388, 6, c.I)
    )


@art("soundbar")
def soundbar(c: Pal) -> str:
    return (
        L("M470 290q16 30 0 60M492 274q26 46 0 92", c.A, 6)
        + R(150, 330, 330, 64, INK, 32)
        + L("M184 362H446", "#475569", 20, stroke_dasharray="2 8", stroke_linecap="butt")
        + C(460, 362, 6, c.I)
        + R(150, 394, 330, 8, c.I, 4)
    )


@art("security-camera", "webcam", "video-doorbell")
def security_camera(c: Pal) -> str:
    return (
        R(376, 260, 50, 150, "#cbd5e1", 10)
        + L("M390 300L340 320", "#94a3b8", 16)
        + at(
            R(-110, -46, 200, 92, W, 40)
            + C(-86, 0, 32, INK)
            + C(-86, 0, 18, c.I)
            + C(-80, -6, 6, W)
            + C(50, -20, 5, "#ef4444"),
            300,
            320,
            1,
            12,
        )
    )


@art("mouse")
def mouse(c: Pal) -> str:
    return (
        L("M320 210Q320 160 380 150", INK, 6)
        + P(
            "M320 214C388 214 404 280 404 340C404 404 368 440 320 440C272 440 236 404 236 340C236 280 252 214 320 214z",
            W,
        )
        + P("M320 214V300H236C238 250 262 214 320 214z", c.P)
        + L("M320 214V300M236 300H404", "#cbd5e1", 4)
        + R(312, 236, 16, 40, c.I, 8)
    )


@art("keyboard")
def keyboard(c: Pal) -> str:
    keys = "".join(
        R(196 + i * 36 + (j % 2) * 10, 318 + j * 32, 28, 24, W, 5)
        for j in range(3)
        for i in range(7)
    )
    return (
        P("M160 300H480L470 430H170z", INK)
        + keys
        + R(250, 402, 140, 20, W, 5)
        + L("M170 430H470", c.I, 8)
    )


@art("tablet", "e-reader")
def tablet(c: Pal) -> str:
    return (
        R(196, 190, 248, 250, INK, 22)
        + R(210, 206, 220, 206, c.P)
        + R(226, 222, 86, 60, c.I, 6)
        + L(
            "M324 230H412M324 252H400M324 274H412M226 302H412M226 324H390M226 346H412M226 368H380",
            c.T,
            8,
        )
        + C(320, 426, 6, "#475569")
    )


@art("phone-case", "screen-protector")
def phone_case(c: Pal) -> str:
    return (
        at(
            R(-70, -130, 140, 260, c.A, 26)
            + R(-54, -114, 50, 70, INK, 14)
            + C(-30, -90, 14, "#475569")
            + C(-30, -60, 8, "#475569"),
            380,
            320,
            0.85,
            10,
        )
        + R(214, 180, 128, 260, INK, 22)
        + R(224, 196, 108, 228, c.I, 12)
        + P("M224 330L332 230V270L224 370z", W, fill_opacity=0.18)
    )


@art("flash-drive", "memory-card", "ssd")
def flash_drive(c: Pal) -> str:
    return at(
        R(-40, -150, 80, 60, SILD, 6)
        + R(-24, -132, 16, 16, INK)
        + R(8, -132, 16, 16, INK)
        + R(-56, -96, 112, 220, c.I, 20)
        + C(0, 90, 12, "none", stroke=W, stroke_width=6)
        + label_em(em_letter("64", W, 36), c, 0, 0, 1),
        320,
        312,
        1,
        20,
    )


@art("smart-plug", "surge-protector")
def smart_plug(c: Pal) -> str:
    return (
        R(240, 200, 160, 180, W, 34)
        + C(320, 262, 26, c.P)
        + E(308, 262, 5, 10, INK)
        + E(332, 262, 5, 10, INK)
        + C(320, 334, 16, c.I)
        + C(320, 334, 7, W)
        + R(296, 380, 12, 50, SILD, 4)
        + R(332, 380, 12, 50, SILD, 4)
    )


@art("smart-thermostat")
def smart_thermostat(c: Pal) -> str:
    return (
        C(320, 320, 110, SIL)
        + C(320, 320, 92, INK)
        + C(320, 320, 80, "none", stroke=c.I, stroke_width=8, stroke_dasharray="300 200")
        + T(320, 342, "72°", W, 60)
    )


@art("smart-bulb", "smart-light-strip")
def smart_bulb(c: Pal) -> str:
    return light_bulbs(c).replace("#fff3b0", mix(c.A, 0.55)) + L(
        "M400 212a40 40 0 0 1 40-40M398 186a70 70 0 0 1 70-70", c.I, 7
    )


@art("printer")
def printer(c: Pal) -> str:
    return (
        R(248, 194, 144, 90, W)
        + L("M268 222H372M268 246H352", c.T, 6)
        + R(196, 270, 248, 130, "#cbd5e1", 18)
        + R(196, 270, 248, 36, "#94a3b8", 18)
        + R(236, 360, 168, 16, INK, 6)
        + R(248, 372, 144, 60, W)
        + C(410, 300, 6, "#22c55e")
    )


# --- Home & kitchen --------------------------------------------------------------------------


def folded_stack(c: Pal, colors: tuple[str, ...], stripe: str | None = None) -> str:
    s = ""
    for i, col in enumerate(colors):
        y = 390 - i * 54
        s += (
            R(196, y, 248, 50, col, 16)
            + L(f"M216 {y + 24}H424", shade(col, 0.1), 4)
            + P(f"M424 {y}h4a16 16 0 0 1 16 16v18a16 16 0 0 1-16 16h-4z", shade(col, 0.15))
        )
        if stripe:
            s += R(196, y + 34, 228, 8, stripe)
    return s


reg("sheet-set", lambda c: folded_stack(c, (c.I, W, c.T)) + R(206, 212, 228, 40, c.P, 16))
reg("bath-towels", lambda c: folded_stack(c, (c.A, W, c.A), stripe=W))
reg("comforter", lambda c: folded_stack(c, (W, c.T, c.I)))
reg("duvet-cover", lambda c: folded_stack(c, (c.T, c.I, W)))
reg("weighted-blanket", lambda c: folded_stack(c, ("#64748b", "#94a3b8", "#475569")))


@art("bakeware")
def bakeware(c: Pal) -> str:
    cookies = "".join(
        E(x, y, 26, 12, "#d49a58") + C(x - 6, y - 2, 3, "#5b3a24") + C(x + 8, y + 2, 3, "#5b3a24")
        for x, y in ((240, 356), (310, 346), (380, 336), (270, 386), (340, 376), (410, 366))
    )
    return (
        P("M160 380L240 310H480L400 380z", SILD)
        + P("M160 380H400V404H160z", "#94a3b8")
        + P("M400 380L480 310V334L400 404z", "#7c8a9a")
        + cookies
    )


@art("skillet", "griddle")
def skillet(c: Pal) -> str:
    return (
        L("M400 348L476 300", INK, 26)
        + E(290, 362, 138, 62, INK)
        + E(290, 352, 122, 50, "#475569")
        + P("M230 350C220 320 270 312 290 326C320 310 360 330 344 356C330 380 250 384 230 350z", W)
        + C(290, 346, 18, YELLOW)
    )


@art("cookware-set", "stockpot", "saucepan", "dutch-oven", "pressure-cooker")
def pot(c: Pal) -> str:
    return (
        R(180, 300, 40, 22, INK, 10)
        + R(420, 300, 40, 22, INK, 10)
        + R(204, 290, 232, 150, c.I, 20)
        + R(204, 290, 232, 20, c.D)
        + P("M196 290Q320 220 444 290z", c.M)
        + R(300, 238, 40, 22, INK, 10)
        + shine("M222 324V420", 10, 0.35)
    )


@art("candle")
def candle(c: Pal) -> str:
    return (
        P("M320 176C334 200 340 220 320 240C300 220 306 200 320 176z", "#f59e0b")
        + P("M320 200C328 214 330 226 320 234C310 226 312 214 320 200z", YELLOW)
        + L("M320 240V262", INK, 4)
        + R(236, 256, 168, 184, c.T, 24)
        + R(244, 264, 152, 30, CREAM, 12)
        + R(236, 316, 168, 80, W)
        + label_em(em_leaf(c.I), c, 320, 356, 1.2)
        + shine("M254 306V420", 9, 0.6)
    )


@art("fan")
def fan(c: Pal) -> str:
    blades = "".join(at(E(0, -46, 24, 44, c.T), 320, 280, 1, a) for a in (0, 120, 240))
    return (
        R(310, 360, 20, 60, INK)
        + E(320, 430, 80, 14, INK)
        + C(320, 280, 108, W)
        + blades
        + C(320, 280, 20, c.I)
        + C(320, 280, 108, "none", stroke=c.I, stroke_width=8, stroke_opacity=1)
        + L("M320 172V388M212 280H428M244 204L396 356M244 356L396 204", c.I, 2, stroke_opacity=0.35)
    )


@art("air-fryer", "slow-cooker", "rice-cooker")
def air_fryer(c: Pal) -> str:
    return (
        R(232, 190, 176, 250, INK, 44)
        + R(248, 206, 144, 56, "#334155", 20)
        + C(320, 234, 16, c.A)
        + R(248, 290, 144, 120, "#475569", 18)
        + R(290, 330, 60, 18, c.I, 9)
    )


@art("storage-bins", "food-storage")
def storage_bins(c: Pal) -> str:
    def bin_(col: str) -> str:
        return (
            P("M-110-60H110L96 60Q94 70 84 70H-84Q-94 70-96 60z", col)
            + R(-118, -74, 236, 22, shade(col, 0.15), 8)
            + R(-30, -30, 60, 18, shade(col, 0.3), 9)
        )

    return at(bin_(c.T), 320, 300, 0.9) + at(bin_(c.I), 320, 370)


@art("kitchen-utensils", "flatware")
def kitchen_utensils(c: Pal) -> str:
    return (
        L("M280 330L250 190", "#d9a066", 12)
        + E(246, 176, 18, 26, "#d9a066", transform="rotate(-12 246 176)")
        + L("M320 330V180", SILD, 8)
        + P(
            "M300 150Q320 220 340 150Q340 200 320 210Q300 200 300 150z",
            "none",
            stroke=SILD,
            stroke_width=6,
            stroke_opacity=1,
        )
        + L("M360 330L392 200", INK, 12)
        + R(376, 150, 44, 56, INK, 8, transform="rotate(14 398 178)")
        + P("M246 300H394L380 432Q378 440 368 440H272Q262 440 260 432z", c.I)
        + R(240, 296, 160, 18, c.D, 8)
    )


@art("kitchen-knife", "knife-set", "knife-sharpener")
def kitchen_knife(c: Pal) -> str:
    return at(
        P("M-40-26H150Q160-26 150 0L120 26H-40z", SIL)
        + L("M-30 16H120", "#cbd5e1", 4)
        + R(-160, -22, 124, 44, INK, 14)
        + C(-120, 0, 5, SILD)
        + C(-80, 0, 5, SILD),
        320,
        330,
        1,
        -30,
    )


@art("cutting-board")
def cutting_board(c: Pal) -> str:
    return (
        P(
            "M210 230H410Q430 230 430 250V420Q430 440 410 440H230Q210 440 210 420V300Q180 290 180 262Q180 232 210 230z",
            "#d9a066",
        )
        + C(206, 262, 12, W)
        + L("M250 280Q330 300 400 280M250 360Q330 380 400 360", "#c08850", 4)
        + at(em_tomato()(c), 350, 400, 1.2)
    )


@art("blender", "food-processor", "stand-mixer", "hand-mixer")
def blender(c: Pal) -> str:
    return (
        R(268, 170, 104, 24, INK, 8)
        + P("M264 192H376L360 350H280z", "#e0f2fe", fill_opacity=0.9)
        + P("M270 260H370L360 350H280z", "#fbcfe8")
        + L("M300 330l20 10 20-10", SILD, 5)
        + P("M376 210H404V300H372", "none", stroke="#cbd5e1", stroke_width=10, stroke_opacity=1)
        + R(248, 346, 144, 94, c.I, 18)
        + C(320, 392, 14, W)
    )


@art("toaster")
def toaster(c: Pal) -> str:
    return (
        R(252, 222, 60, 80, CRUMB, 14)
        + R(330, 212, 60, 90, CRUMB, 14)
        + R(252, 222, 60, 14, CRUST, 7)
        + R(330, 212, 60, 14, CRUST, 7)
        + R(214, 270, 212, 170, c.I, 36)
        + R(236, 262, 168, 12, c.D, 6)
        + R(410, 320, 30, 16, INK, 6)
        + shine("M236 300V410", 10, 0.35)
    )


@art("coffee-maker", "espresso-machine")
def coffee_maker(c: Pal) -> str:
    return (
        P("M220 190H420V240H300V420H420V440H220z", INK)
        + R(300, 240, 120, 30, "#475569")
        + P(
            "M312 330H408L400 420Q398 432 386 432H334Q322 432 320 420z",
            "#e0f2fe",
            fill_opacity=0.85,
        )
        + P("M316 370H404L400 420Q398 432 386 432H334Q322 432 320 420z", "#6b4226")
        + P(
            "M408 350Q434 360 428 400L402 410", "none", stroke=INK, stroke_width=8, stroke_opacity=1
        )
        + C(260, 300, 10, c.A)
    )


@art("mugs")
def mugs(c: Pal) -> str:
    return (
        L("M290 236c-10-14 10-22 0-40M330 236c-10-14 10-22 0-40", "#cbd5e1", 6)
        + P(
            "M384 290H400Q440 290 440 340Q440 390 396 390H384",
            "none",
            stroke=c.I,
            stroke_width=20,
            stroke_opacity=1,
        )
        + P("M224 260H404V400Q404 440 364 440H264Q224 440 224 400z", c.I)
        + R(224, 260, 180, 14, c.D)
        + label_em(em_heart(W), c, 314, 352, 1.4)
    )


@art("shower-curtain")
def shower_curtain(c: Pal) -> str:
    rings = "".join(C(x, 200, 9, "none", stroke=SILD, stroke_width=5) for x in range(214, 440, 32))
    return (
        L("M190 190H450", SILD, 10)
        + rings
        + P(
            "M204 208H436V440Q420 420 404 440T372 440T340 440T308 440T276 440T244 440T212 440L204 440z",
            c.T,
        )
        + L("M236 212V430M268 212V430M300 212V430M332 212V430M364 212V430M396 212V430", c.M, 4)
        + label_em(em_wave(c.I), c, 320, 320, 1.8)
    )


# --- Clothing & shoes ------------------------------------------------------------------------


@art("t-shirt", "shirt")
def t_shirt(c: Pal) -> str:
    return (
        P(
            "M268 190L200 222L176 300L226 316L240 290V440H400V290L414 316L464 300L440 222L372 190C362 214 344 228 320 228S278 214 268 190z",
            c.I,
        )
        + P(
            "M268 190C278 214 296 228 320 228S362 214 372 190L360 186C352 204 338 214 320 214S288 204 280 186z",
            c.D,
        )
        + label_em(em_star(W), c, 320, 320, 1.6)
    )


@art("polo")
def polo(c: Pal) -> str:
    return (
        t_shirt(c).replace(label_em(em_star(W), c, 320, 320, 1.6), "")
        + P("M280 190L320 236L360 190L376 204L338 250H302L264 204z", W)
        + R(312, 236, 16, 60, c.D)
        + C(320, 260, 4, W)
        + C(320, 282, 4, W)
    )


@art("hoodie", "fleece-jacket")
def hoodie(c: Pal) -> str:
    return (
        P(
            "M262 200L196 236L170 400L218 408L236 300V440H404V300L422 408L470 400L444 236L378 200z",
            c.I,
        )
        + P("M262 200C262 150 378 150 378 200C378 240 352 256 320 256S262 240 262 200z", c.D)
        + P(
            "M280 208C284 180 356 180 360 208C356 232 340 242 320 242S284 232 280 208z",
            shade(c.I, 0.45),
        )
        + R(270, 350, 100, 60, c.D, 12)
        + L("M304 256V300M336 256V300", W, 5)
    )


@art("puffer-jacket")
def puffer_jacket(c: Pal) -> str:
    return (
        P(
            "M262 196L196 228L170 410L220 418L238 300V440H402V300L420 418L470 410L444 228L378 196z",
            c.I,
        )
        + L(
            "M238 250H402M238 300H402M238 350H402M238 396H402M180 300l50 4M460 300l-50 4M176 356l52 4M464 356l-52 4",
            c.D,
            5,
        )
        + P("M270 196Q320 168 370 196L360 214Q320 196 280 214z", c.D)
        + L("M320 206V440", c.A, 6)
    )


@art("jeans")
def jeans(c: Pal) -> str:
    blue = "#3b82f6" if c.I != "#be185d" else "#3b6fb6"
    return (
        P("M226 196H414L428 440H340L320 270L300 440H212z", blue)
        + R(226, 196, 188, 28, shade(blue, 0.2))
        + L("M320 224V266M250 232Q270 260 300 240M390 232Q370 260 340 240", shade(blue, 0.35), 4)
        + R(246, 200, 12, 20, c.A, 3)
        + R(382, 200, 12, 20, c.A, 3)
    )


@art("shorts", "underwear")
def shorts(c: Pal) -> str:
    return (
        P("M214 250H426L444 400H344L320 330L296 400H196z", c.I)
        + R(214, 250, 212, 34, c.D)
        + L("M306 266l-14 36M334 266l14 36", W, 5)
    )


@art("socks")
def socks(c: Pal) -> str:
    def sock(col: str) -> str:
        return (
            P("M-40-120H40V40Q40 70 70 80Q110 94 104 120Q98 140 70 140H-10Q-40 140-40 100z", col)
            + R(-40, -120, 80, 30, W)
            + L("M-40-80H40M-40-66H40", shade(col, 0.2), 4)
            + P("M60 80Q104 90 104 120Q98 140 70 140H56z", W)
        )

    return at(sock(c.A), 350, 296, 0.85, 10) + at(sock(c.I), 270, 300)


@art("sneakers", "running-shoes")
def sneakers(c: Pal) -> str:
    return (
        P("M176 410V330Q176 300 206 300H250Q280 340 330 350L420 370Q464 380 464 410z", c.I)
        + P("M170 404H470V428Q470 440 458 440H182Q170 440 170 428z", W)
        + L("M250 316l18 14M266 304l18 14M282 296l18 14", W, 6)
        + P("M320 360Q380 360 440 380", "none", stroke=c.A, stroke_width=10, stroke_opacity=1)
        + R(170, 424, 300, 8, c.P)
    )


@art("boots")
def boots(c: Pal) -> str:
    tan = "#b7793e"
    return (
        P("M230 190H330V340Q390 350 432 372Q456 386 456 410V440H212V200z", tan)
        + R(208, 420, 252, 20, INK, 6)
        + R(226, 190, 108, 26, shade(tan, 0.25), 6)
        + L("M290 240h30M290 270h30M290 300h30", "#fde68a", 5)
    )


@art("sandals", "slippers")
def sandals(c: Pal) -> str:
    def sole(col: str) -> str:
        return P(
            "M-44-110Q0-130 44-110Q60-40 40 20Q54 90 30 120H-30Q-54 90-40 20Q-60-40-44-110z", col
        )

    return at(
        sole("#d9a066") + P("M-44-60Q0-10 44-60V-30Q0 20-44-30z", c.I), 260, 320, 1, -14
    ) + at(sole("#d9a066") + P("M-44-60Q0-10 44-60V-30Q0 20-44-30z", c.I), 380, 320, 1, 14)


# --- Office & school -------------------------------------------------------------------------


@art("notebook", "planner", "legal-pad")
def notebook(c: Pal) -> str:
    rings = "".join(R(222, y, 34, 10, SILD, 5) for y in range(214, 430, 26))
    return (
        R(246, 190, 180, 250, c.A, 14)
        + R(236, 196, 180, 244, c.I, 14)
        + R(290, 230, 100, 50, W, 8)
        + L("M304 248H376M304 262H350", c.T, 5)
        + R(380, 196, 16, 244, c.A)
        + rings
    )


@art("markers", "highlighters")
def markers(c: Pal) -> str:
    def marker(col: str) -> str:
        return (
            R(-22, -100, 44, 60, col, 10)
            + R(-20, -46, 40, 160, W, 8)
            + R(-20, 20, 40, 40, col)
            + P("M-12 114H12L6 138H-6z", col)
        )

    return (
        at(marker("#ef4444"), 262, 310, 1, -14)
        + at(marker("#22c55e"), 378, 310, 1, 14)
        + at(marker("#3b82f6"), 320, 300)
    )


@art("pencils", "pencil-sharpener")
def pencils(c: Pal) -> str:
    def pencil(col: str) -> str:
        return (
            R(-16, -120, 32, 200, col)
            + R(-16, -140, 32, 22, "#f9a8d4", 6)
            + R(-16, -122, 32, 10, SILD)
            + P("M-16 80H16L0 124z", "#f3d9a6")
            + P("M-5 110H5L0 124z", INK)
            + L("M-5-110V76", shade(col, 0.15), 4)
        )

    return (
        at(pencil(YELLOW), 270, 300, 1, -10)
        + at(pencil(c.A), 370, 300, 1, 10)
        + at(pencil(YELLOW), 320, 290)
    )


@art("copy-paper", "sheet-protectors")
def copy_paper(c: Pal) -> str:
    return (
        P("M226 250L276 210H436L386 250z", W)
        + box3d(196, 260, 200, 150, 60, W, W, "#e2e8f0")
        + R(196, 300, 200, 70, c.I)
        + label_em(em_letter("A4", W, 34), c, 296, 335, 1)
        + L("M196 410H396", "#cbd5e1", 4)
    )


@art("calculator", "label-maker")
def calculator(c: Pal) -> str:
    keys = "".join(
        R(250 + i * 38, 290 + j * 36, 30, 28, W if (i, j) != (3, 3) else c.A, 6)
        for i in range(4)
        for j in range(4)
    )
    return (
        R(236, 190, 168, 250, INK, 22)
        + R(252, 210, 136, 60, "#d9f99d", 8)
        + T(370, 256, "42", INK, 40)
        + keys
    )


@art("sticky-notes", "labels")
def sticky_notes(c: Pal) -> str:
    return (
        at(R(-90, -90, 180, 180, "#f9a8d4", 4), 350, 300, 1, 10)
        + box3d(200, 290, 180, 130, 40, YELLOW, "#fde68a", YELLOW_D)
        + P("M380 290L360 330L340 290z", "#fde68a")
        + L("M222 330H340M222 356H320", YELLOW_D, 5)
    )


@art("scissors")
def scissors(c: Pal) -> str:
    return (
        L("M320 320L420 186M320 320L220 186", SILD, 22)
        + C(260, 386, 40, "none", stroke=c.A, stroke_width=18, stroke_opacity=1)
        + C(380, 386, 40, "none", stroke=c.A, stroke_width=18, stroke_opacity=1)
        + L("M280 352L320 320L360 352", c.A, 18)
        + C(320, 320, 8, INK)
    )


@art("folders", "file-organizer", "desk-organizer")
def folders(c: Pal) -> str:
    return (
        P("M200 230H290L310 252H440V430H200z", c.A)
        + R(220, 262, 200, 150, W)
        + L("M240 290H400M240 314H380", c.T, 5)
        + P("M186 290H454L436 440H204z", c.I)
    )


@art("envelopes", "mailers")
def envelopes(c: Pal) -> str:
    return (
        at(R(-120, -80, 240, 160, c.T, 10), 340, 290, 0.9, 8)
        + R(196, 300, 248, 140, W, 10)
        + P("M196 310L320 380L444 310", "none", stroke="#cbd5e1", stroke_width=6, stroke_opacity=1)
        + R(396, 316, 32, 36, c.A, 3)
    )


@art("binder")
def binder(c: Pal) -> str:
    return (
        R(236, 196, 190, 244, c.I, 12)
        + R(236, 196, 40, 244, c.D, 12)
        + R(300, 250, 100, 70, W, 8)
        + L("M314 272H386M314 290H360", c.T, 5)
        + C(256, 260, 8, SILD)
        + C(256, 318, 8, SILD)
        + C(256, 376, 8, SILD)
    )


@art("backpack")
def backpack(c: Pal) -> str:
    return (
        P(
            "M286 216Q286 176 320 176Q354 176 354 216",
            "none",
            stroke=c.D,
            stroke_width=14,
            stroke_opacity=1,
        )
        + R(230, 210, 180, 230, c.I, 50)
        + R(254, 326, 132, 90, c.D, 24)
        + L("M270 344H370", c.A, 6)
        + R(300, 222, 40, 12, c.A, 6)
    )


@art("stapler", "staples")
def stapler(c: Pal) -> str:
    return (
        R(190, 410, 260, 30, INK, 12)
        + P("M200 404Q200 340 260 336H440Q456 336 456 352V380Q456 396 440 396H220z", c.I)
        + R(420, 380, 30, 30, INK, 6)
        + shine("M240 356H420", 8, 0.35)
    )


# --- Outdoor & garden ------------------------------------------------------------------------


@art("tent")
def tent(c: Pal) -> str:
    return (
        P("M320 200L460 440H180z", c.I)
        + P("M320 200L460 440H390z", c.D)
        + P("M320 290L360 440H280z", shade(c.I, 0.5))
        + L("M320 200V170M180 440H460", INK, 6)
        + P("M320 172L350 184L320 196z", c.A)
    )


@art("sleeping-bag", "sleeping-pad", "air-mattress")
def sleeping_bag(c: Pal) -> str:
    return (
        R(180, 300, 240, 140, c.I, 30)
        + E(420, 370, 50, 70, c.D)
        + E(420, 370, 34, 50, c.T)
        + L("M420 320Q450 370 420 420", c.I, 4)
        + R(250, 300, 16, 140, c.A)
        + R(340, 300, 16, 140, c.A)
    )


@art("cooler")
def cooler(c: Pal) -> str:
    return (
        P(
            "M240 260Q240 220 280 220H360Q400 220 400 260",
            "none",
            stroke=INK,
            stroke_width=12,
            stroke_opacity=1,
        )
        + R(196, 256, 248, 56, W, 16)
        + R(196, 300, 248, 140, c.I, 18)
        + R(236, 330, 168, 40, W, 10)
        + L("M254 350H386", c.T, 6)
    )


@art("grill", "camp-stove")
def grill(c: Pal) -> str:
    return (
        L("M260 380L230 440M380 380L410 440M320 390V440", INK, 10)
        + C(230, 440, 10, INK)
        + P("M196 290H444A124 110 0 0 1 196 290z", INK)
        + P("M204 290A116 100 0 0 1 436 290z", "#334155")
        + R(304, 184, 32, 20, c.A, 8)
        + L("M196 290H444", c.I, 10)
    )


@art("garden-tools")
def garden_tools(c: Pal) -> str:
    return at(
        R(-12, -70, 24, 120, "#d9a066", 10) + P("M-40 40H40L30 130Q0 160-30 130z", SIL),
        270,
        290,
        1,
        -14,
    ) + at(
        R(-12, -70, 24, 110, "#d9a066", 10)
        + P("M-40 30H40V60H-40z", SIL)
        + L("M-30 60V140M-10 60V140M10 60V140M30 60V140", SIL, 8),
        380,
        290,
        1,
        14,
    )


@art("garden-gloves")
def garden_gloves(c: Pal) -> str:
    glove = P(
        "M-50 100V-40Q-60-60-50-80Q-40-94-30-80V-110Q-30-124-18-124Q-6-124-6-110V-124Q-6-138 6-138Q18-138 18-124V-110Q18-122 30-122Q42-122 42-108V-40Q60-60 70-50Q78-40 64-20L40 30V100z",
        c.A,
    )
    cuff = R(-54, 60, 98, 40, c.I, 8)
    return at(glove + cuff, 280, 330, 1, -12) + at(glove + cuff, 380, 340, 0.9, 16)


@art("seeds")
def seeds(c: Pal) -> str:
    return (
        R(240, 190, 160, 250, W, 10)
        + R(240, 190, 160, 30, c.I, 10)
        + R(256, 234, 128, 120, c.P, 8)
        + label_em(em_flower("#f472b6"), c, 320, 294, 2)
        + L("M262 380H378M262 404H340", c.T, 6)
    )


reg("soil", lambda c: sack(c, em_leaf(GREEN_L), body="#5b3a24", band=c.I, w=200))
reg("mulch", lambda c: sack(c, em_leaf(YELLOW), body="#7c4a2a", band=c.A, w=200), accent="#b45309")
reg("bird-seed", lambda c: sack(c, em_grains(YELLOW), body=c.I, band=W, w=190))


@art("planter")
def planter(c: Pal) -> str:
    return (
        L("M320 340V240", GREEN_D, 8)
        + at(em_leaf(GREEN)(c), 280, 250, 2.2, -60)
        + at(em_leaf(GREEN_L)(c), 364, 230, 2.2, 10)
        + at(em_leaf(GREEN)(c), 320, 200, 2, -30)
        + P("M236 330H404L384 440H256z", "#d97757")
        + R(226, 318, 188, 32, "#c2643f", 8)
    )


@art("patio-set", "patio-chair")
def patio_chair(c: Pal) -> str:
    return (
        L("M230 340L214 440M396 340L420 440M250 380L240 440M380 380L396 440", INK, 10)
        + R(222, 330, 196, 30, c.I, 10)
        + P("M238 330L222 196H418L402 330z", c.I)
        + L("M246 230H394M250 264H390M254 298H386", c.D, 6)
    )


@art("patio-umbrella")
def patio_umbrella(c: Pal) -> str:
    return (
        L("M320 180V440", INK, 10)
        + E(320, 436, 60, 10, INK)
        + P(
            "M170 280Q320 150 470 280Q440 270 420 286Q395 268 370 286Q345 268 320 286Q295 268 270 286Q245 268 220 286Q200 270 170 280z",
            c.I,
        )
        + P(
            "M320 180Q280 220 270 286M320 180Q360 220 370 286",
            "none",
            stroke=c.D,
            stroke_width=5,
            stroke_opacity=1,
        )
    )


@art("lantern")
def lantern(c: Pal) -> str:
    return (
        P(
            "M290 196Q290 166 320 166Q350 166 350 196",
            "none",
            stroke=INK,
            stroke_width=8,
            stroke_opacity=1,
        )
        + R(270, 196, 100, 30, c.I, 10)
        + R(278, 226, 84, 160, "#fef3c7")
        + C(320, 306, 30, YELLOW)
        + L("M278 226V386M362 226V386", INK, 8)
        + R(262, 386, 116, 50, c.I, 12)
    )


@art("bird-feeder")
def bird_feeder(c: Pal) -> str:
    return (
        L("M320 150V200", INK, 5)
        + P("M230 250L320 196L410 250z", c.I)
        + R(260, 250, 120, 140, "#e0f2fe", 6, fill_opacity=0.9)
        + R(264, 310, 112, 80, "#e2b872")
        + R(236, 390, 168, 20, c.D, 6)
        + L("M300 410V430", INK, 6)
    )


@art("garden-hose", "hose-nozzle", "sprinkler")
def garden_hose(c: Pal) -> str:
    return (
        C(310, 330, 100, "none", stroke=c.I, stroke_width=22, stroke_opacity=1)
        + C(310, 330, 64, "none", stroke=c.I, stroke_width=22, stroke_opacity=1)
        + C(310, 330, 28, c.D)
        + L("M400 380Q440 420 460 400", c.I, 22)
        + at(R(-10, -20, 60, 40, YELLOW, 10), 462, 396, 1, -30)
    )


# --- Sports & fitness ------------------------------------------------------------------------


@art("water-bottle")
def water_bottle(c: Pal) -> str:
    return (
        C(356, 176, 18, "none", stroke=INK, stroke_width=8, stroke_opacity=1)
        + R(284, 166, 72, 44, INK, 12)
        + R(262, 204, 116, 236, c.I, 30)
        + R(262, 280, 116, 90, c.A)
        + shine("M280 224V264", 9, 0.5)
    )


@art("bike", "balance-bike")
def bike(c: Pal) -> str:
    return (
        C(220, 380, 60, "none", stroke=INK, stroke_width=12, stroke_opacity=1)
        + C(420, 380, 60, "none", stroke=INK, stroke_width=12, stroke_opacity=1)
        + L(
            "M220 380L290 300H390L420 380M290 300L330 380H220M330 380L390 300M280 280H310M390 300L380 260H406",
            c.I,
            12,
        )
        + C(330, 380, 10, INK)
    )


@art("yoga-block")
def yoga_block(c: Pal) -> str:
    return box3d(206, 310, 190, 120, 60, c.I, c.T, c.D) + box3d(
        236, 236, 130, 74, 40, c.A, mix(c.A, 0.4), shade(c.A, 0.2)
    )


@art("swim-goggles", "swim-cap")
def swim_goggles(c: Pal) -> str:
    return (
        P(
            "M180 330Q180 270 320 270Q460 270 460 330",
            "none",
            stroke=INK,
            stroke_width=10,
            stroke_opacity=1,
        )
        + E(262, 336, 60, 44, c.I)
        + E(378, 336, 60, 44, c.I)
        + E(262, 336, 44, 30, "#bae6fd")
        + E(378, 336, 44, 30, "#bae6fd")
        + L("M310 336H330", INK, 10)
        + E(248, 324, 12, 8, W)
    )


@art("resistance-bands")
def resistance_bands(c: Pal) -> str:
    return (
        E(300, 340, 110, 66, "none", stroke=c.A, stroke_width=20, stroke_opacity=1)
        + E(340, 360, 110, 66, "none", stroke=c.I, stroke_width=20, stroke_opacity=1)
        + E(320, 320, 90, 54, "none", stroke=GREEN, stroke_width=16, stroke_opacity=1)
    )


@art("fitness-tracker")
def fitness_tracker(c: Pal) -> str:
    return (
        R(280, 170, 80, 300, c.I, 30)
        + R(260, 260, 120, 120, INK, 28)
        + R(272, 272, 96, 96, "#0f172a", 20)
        + T(320, 330, "10k", "#a3e635", 30)
        + L("M290 346h60", c.A, 5)
    )


@art("tennis-racquet", "pickleball-paddle", "badminton-set")
def tennis_racquet(c: Pal) -> str:
    strings = "".join(f"M{x} 190V350" for x in range(262, 380, 20)) + "".join(
        f"M242 {y}H398" for y in range(210, 340, 20)
    )
    return (
        at(
            L("M0 80V200", INK, 20)
            + R(-12, 130, 24, 80, c.I, 10)
            + E(0, -20, 90, 110, "#e0f2fe")
            + G(L(strings, "#94a3b8", 2), "translate(-320 -270)")
            + E(0, -20, 90, 110, "none", stroke=c.I, stroke_width=16, stroke_opacity=1),
            300,
            270,
            1,
            20,
        )
        + C(424, 400, 34, "#c6e14b")
        + L("M398 388q26 12 52 0", W, 5)
    )


@art("dumbbells")
def dumbbells(c: Pal) -> str:
    def db() -> str:
        return (
            R(-80, -10, 160, 20, SILD, 6)
            + R(-100, -40, 34, 80, INK, 10)
            + R(66, -40, 34, 80, INK, 10)
            + R(-70, -30, 16, 60, c.I, 6)
            + R(54, -30, 16, 60, c.I, 6)
        )

    return at(db(), 320, 400) + at(db(), 330, 330, 1, -10)


@art("bike-helmet", "bike-light")
def bike_helmet(c: Pal) -> str:
    return (
        P("M190 380Q190 230 330 230Q450 230 450 350Q450 380 420 380z", c.I)
        + P(
            "M240 290Q280 256 330 254L336 290Q290 294 262 312zM350 254Q400 258 424 294L396 312Q380 294 352 290z",
            "#0f172a",
            fill_opacity=0.6,
        )
        + L("M200 380H440", INK, 12)
        + L("M260 380Q270 420 320 430", INK, 6)
    )


def ball(c: Pal, col: str, lines: str, line_col: str) -> str:
    return (
        C(320, 340, 100, col)
        + L(lines, line_col, 7)
        + E(284, 300, 22, 12, W, fill_opacity=0.35, transform="rotate(-35 284 300)")
    )


reg(
    "basketball",
    lambda c: ball(
        c,
        "#f97316",
        "M220 340H420M320 240V440M250 270Q300 340 250 410M390 270Q340 340 390 410",
        "#7c2d12",
    ),
)
reg(
    "volleyball",
    lambda c: ball(
        c,
        "#fef3c7",
        "M320 340L320 240M320 340L230 390M320 340L410 390M320 240Q260 300 274 420M230 390Q320 360 410 290",
        "#2563eb",
    ),
)
reg(
    "soccer-ball",
    lambda c: (
        ball(
            c,
            W,
            "M320 300L350 322L338 356H302L290 322zM320 300V244M350 322L410 300M338 356L370 410M302 356L270 410M290 322L230 300",
            INK,
        )
        + P("M320 300L350 322L338 356H302L290 322z", INK)
    ),
)
reg(
    "tennis-balls",
    lambda c: ball(c, "#c6e14b", "M236 290Q320 340 236 400M404 290Q320 340 404 400", W),
)
reg("exercise-ball", lambda c: ball(c, c.A, "M230 300Q320 360 410 300", W), accent="#8b5cf6")


@art("football")
def football(c: Pal) -> str:
    return at(
        E(0, 0, 130, 76, "#8b4513")
        + L("M-60 0H60", W, 6)
        + L("M-40-12V12M-20-12V12M0-12V12M20-12V12M40-12V12", W, 5)
        + L("M-100-30Q-110 0-100 30M100-30Q110 0 100 30", W, 6),
        320,
        340,
        1,
        -30,
    )


# --- Toys & games ----------------------------------------------------------------------------


@art("puzzle")
def puzzle(c: Pal) -> str:
    piece = "M-70-70H-20Q-24-100 0-100Q24-100 20-70H70V-20Q100-24 100 0Q100 24 70 20V70H20Q24 40 0 40Q-24 40-20 70H-70V20Q-40 24-40 0Q-40-24-70-20z"
    return at(P(piece, c.A), 380, 300, 0.8, 16) + at(P(piece, c.I), 290, 360)


@art("building-blocks")
def building_blocks(c: Pal) -> str:
    def brick(col: str, w: int) -> str:
        studs = "".join(
            R(x - 16, -60, 32, 16, shade(col, 0.1), 5) for x in range(-w // 2 + 28, w // 2, 48)
        )
        return studs + R(-w // 2, -48, w, 96, col, 8) + shine(f"M{-w // 2 + 14}-30V30", 8, 0.35)

    return (
        at(brick(YELLOW, 192), 320, 392)
        + at(brick(RED, 144), 290, 292)
        + at(brick("#3b82f6", 96), 390, 292)
    )


@art("board-game", "party-game")
def board_game(c: Pal) -> str:
    return (
        box3d(186, 330, 240, 90, 60, c.I, c.T, c.D)
        + R(206, 350, 200, 50, W, 8)
        + L("M226 376H386", c.A, 8)
        + at(
            R(-34, -34, 68, 68, W, 12) + C(-16, -16, 7, INK) + C(16, 16, 7, INK) + C(0, 0, 7, INK),
            330,
            256,
            1,
            16,
        )
    )


@art("card-game")
def card_game(c: Pal) -> str:
    card = R(-60, -90, 120, 180, W, 12) + R(-48, -78, 96, 156, c.I, 8)
    return (
        at(card, 270, 330, 1, -16)
        + at(card, 370, 330, 1, 16)
        + at(R(-60, -90, 120, 180, W, 12) + label_em(em_heart(RED), c, 0, 0, 1.8), 320, 320)
    )


@art("stem-kit", "microscope", "telescope")
def stem_kit(c: Pal) -> str:
    return (
        P("M290 190H350V270L420 410Q430 440 400 440H240Q210 440 220 410L290 270z", "#e0f2fe")
        + P("M262 350H378L416 420Q424 436 402 436H238Q216 436 224 420z", c.A)
        + R(280, 180, 80, 20, INK, 6)
        + C(300, 390, 8, W)
        + C(340, 404, 5, W)
        + C(316, 320, 6, c.A)
    )


@art("baby-toy")
def baby_toy(c: Pal) -> str:
    return (
        R(312, 190, 16, 230, "#d9a066", 8)
        + E(320, 420, 100, 22, RED)
        + E(320, 380, 84, 20, ORANGE)
        + E(320, 344, 68, 18, YELLOW)
        + E(320, 310, 54, 16, GREEN)
        + E(320, 280, 42, 14, "#3b82f6")
        + C(320, 244, 26, c.A)
    )


@art("plush-toy", "doll")
def plush_toy(c: Pal) -> str:
    fur, light = "#c98a48", "#ecc494"
    return (
        E(320, 390, 80, 60, fur)
        + C(252, 420, 26, fur)
        + C(388, 420, 26, fur)
        + C(262, 222, 30, fur)
        + C(378, 222, 30, fur)
        + C(262, 222, 16, light)
        + C(378, 222, 16, light)
        + C(320, 272, 72, fur)
        + E(320, 298, 34, 26, light)
        + C(294, 258, 8, INK)
        + C(346, 258, 8, INK)
        + E(320, 290, 10, 7, INK)
        + E(320, 390, 44, 36, light)
        + R(290, 330, 60, 18, c.A, 8)
    )


@art("action-figure", "drone")
def action_figure(c: Pal) -> str:
    return (
        L("M320 196V170", INK, 6)
        + C(320, 164, 10, c.A)
        + R(266, 196, 108, 90, c.I, 20)
        + C(298, 240, 14, W)
        + C(342, 240, 14, W)
        + C(298, 240, 6, INK)
        + C(342, 240, 6, INK)
        + R(256, 292, 128, 100, c.D, 16)
        + R(292, 312, 56, 40, c.A, 8)
        + R(216, 300, 34, 80, c.I, 14)
        + R(390, 300, 34, 80, c.I, 14)
        + R(272, 392, 40, 48, INK, 8)
        + R(328, 392, 40, 48, INK, 8)
    )


@art("rc-car", "scooter")
def rc_car(c: Pal) -> str:
    return (
        P(
            "M176 390V350Q176 330 196 326L250 300Q268 280 300 280H370Q400 280 420 310L452 326Q468 332 468 352V390z",
            c.I,
        )
        + P("M262 318L286 294H320V318zM336 294H370L392 318H336z", "#bae6fd")
        + C(240, 398, 36, INK)
        + C(404, 398, 36, INK)
        + C(240, 398, 14, SILD)
        + C(404, 398, 14, SILD)
        + L("M430 300L456 230", INK, 4)
        + C(456, 228, 6, c.A)
    )


@art("outdoor-toy")
def outdoor_toy(c: Pal) -> str:
    return (
        L("M320 400Q280 420 300 440M320 400Q360 430 400 420", INK, 3)
        + P("M320 170L420 280L320 400L220 280z", c.I)
        + P("M320 170L420 280H320z", c.A)
        + P("M320 400L220 280H320z", c.A)
        + L("M320 170V400M220 280H420", W, 4)
    )


@art("crayons", "colored-pencils", "sidewalk-chalk")
def crayons(c: Pal) -> str:
    s = ""
    for i, col in enumerate(("#ef4444", "#f59e0b", "#22c55e", "#3b82f6", "#8b5cf6")):
        x = 240 + i * 40
        s += P(f"M{x - 14} 250L{x} 210L{x + 14} 250z", col) + R(x - 16, 248, 32, 130, col, 4)
    return (
        s
        + R(212, 300, 216, 140, c.I, 10)
        + R(236, 330, 168, 60, W, 30)
        + label_em(em_star(YELLOW), c, 320, 360, 1)
    )


@art("paint", "modeling-dough")
def paint(c: Pal) -> str:
    wells = "".join(
        C(x, y, 16, col)
        for x, y, col in (
            (250, 320, RED),
            (296, 290, YELLOW),
            (350, 286, "#3b82f6"),
            (398, 306, GREEN),
            (262, 372, "#8b5cf6"),
        )
    )
    return (
        P(
            "M200 350C180 280 260 240 330 250C420 262 470 320 440 380C420 420 380 400 360 420C330 450 220 430 200 350z",
            "#f3d9a6",
        )
        + C(340, 380, 22, c.P)
        + wells
        + L("M440 180L360 330", "#d9a066", 10)
        + P("M356 326l-10 30 22-14z", INK)
    )


@art("dollhouse")
def dollhouse(c: Pal) -> str:
    return (
        P("M200 270L320 180L440 270z", c.I)
        + R(220, 270, 200, 170, "#fde2ef")
        + R(300, 360, 40, 80, c.D, 6)
        + R(240, 300, 44, 40, "#bae6fd", 4)
        + R(356, 300, 44, 40, "#bae6fd", 4)
        + R(240, 370, 44, 40, "#bae6fd", 4)
        + R(356, 370, 44, 40, "#bae6fd", 4)
    )


# --- Refinements: siblings that deserve their own silhouette ---------------------------------


@art("leggings")
def leggings(c: Pal) -> str:
    return (
        P("M244 196H396L398 440H336L320 270L304 440H242z", INK)
        + R(244, 196, 152, 30, c.I)
        + L("M320 230V266", "#475569", 4)
    )


def cuffed_pants(c: Pal, body: str, dots: bool) -> str:
    s = (
        P("M228 196H412L420 410H340L320 270L300 410H220z", body)
        + R(222, 404, 80, 32, shade(body, 0.2), 10)
        + R(338, 404, 80, 32, shade(body, 0.2), 10)
        + R(228, 196, 184, 30, c.I)
        + L("M304 226l-8 36M336 226l8 36", W, 5)
    )
    if dots:
        s += "".join(
            C(x, y, 7, W)
            for x, y in (
                (252, 260),
                (288, 300),
                (256, 350),
                (382, 262),
                (352, 304),
                (386, 352),
                (284, 390),
                (356, 392),
            )
        )
    return s


reg("joggers", lambda c: cuffed_pants(c, "#94a3b8", False))
reg("pajamas", lambda c: cuffed_pants(c, c.M, True))


@art("rain-jacket")
def rain_jacket(c: Pal) -> str:
    y = YELLOW
    return (
        P(
            "M262 206L196 238L170 410L220 418L238 300V440H402V300L420 418L470 410L444 238L378 206z",
            y,
        )
        + P("M262 206C262 150 378 150 378 206C378 246 352 262 320 262S262 246 262 206z", YELLOW_D)
        + P(
            "M282 212C286 184 354 184 358 212C354 236 340 246 320 246S286 236 282 212z",
            shade(y, 0.45),
        )
        + L("M320 262V440", INK, 6)
        + R(252, 350, 50, 10, YELLOW_D, 4)
        + R(338, 350, 50, 10, YELLOW_D, 4)
    )


@art("tank-top", "sports-bra")
def tank_top(c: Pal) -> str:
    return P(
        "M262 190H290Q296 236 320 236Q344 236 350 190H378Q378 250 404 290V440H236V290Q262 250 262 190z",
        c.A,
    ) + L("M250 300H390", W, 6, stroke_opacity=0.5)


@art("sweatshirt")
def sweatshirt(c: Pal) -> str:
    return (
        P(
            "M262 196L196 232L170 400L218 408L236 300V440H404V300L422 408L470 400L444 232L378 196Q360 224 320 224Q280 224 262 196z",
            c.T,
        )
        + P(
            "M262 196Q280 224 320 224Q360 224 378 196L364 190Q352 210 320 210Q288 210 276 190z", c.I
        )
        + R(236, 420, 168, 20, c.I)
        + R(170, 392, 48, 16, c.I, 4)
        + R(422, 392, 48, 16, c.I, 4)
    )


@art("pens")
def pens(c: Pal) -> str:
    def pen(col: str) -> str:
        return (
            R(-14, -130, 28, 200, col, 10)
            + R(-14, -130, 28, 50, shade(col, 0.2), 10)
            + R(10, -124, 8, 70, SILD, 4)
            + P("M-14 70H14L4 116H-4z", SIL)
            + C(0, 118, 3, INK)
        )

    return (
        at(pen("#1d4ed8"), 280, 310, 1, -18)
        + at(pen(INK), 360, 310, 1, 18)
        + at(pen(RED), 320, 300)
    )


@art("lunch-box")
def lunch_box(c: Pal) -> str:
    return (
        P(
            "M280 250V224Q280 208 296 208H344Q360 208 360 224V250",
            "none",
            stroke=INK,
            stroke_width=14,
            stroke_opacity=1,
        )
        + R(196, 250, 248, 190, c.A, 26)
        + R(196, 250, 248, 60, shade(c.A, 0.18), 26)
        + R(196, 290, 248, 20, shade(c.A, 0.18))
        + R(300, 296, 40, 24, SILD, 6)
        + label_em(em_star(W), c, 320, 376, 1.6)
    )


@art("grill-accessory")
def grill_accessory(c: Pal) -> str:
    return at(
        R(-10, -40, 20, 150, INK, 8)
        + R(-38, -130, 76, 96, SIL, 12)
        + L("M-18-110V-60M0-110V-60M18-110V-60", "#94a3b8", 6),
        270,
        320,
        1,
        -14,
    ) + at(
        L("M-10 110L-20-120M10 110L20-120", SIL, 10) + R(-18, 40, 36, 70, INK, 8), 380, 320, 1, 12
    )


@art("jump-rope")
def jump_rope(c: Pal) -> str:
    return (
        P(
            "M236 250Q200 460 320 440Q440 460 404 250",
            "none",
            stroke=c.A,
            stroke_width=8,
            stroke_opacity=1,
        )
        + at(R(-14, -70, 28, 90, c.I, 14) + R(-10, 20, 20, 14, INK, 4), 236, 240, 1, -10)
        + at(R(-14, -70, 28, 90, c.I, 14) + R(-10, 20, 20, 14, INK, 4), 404, 240, 1, 10)
    )


@art("kettlebell", "medicine-ball")
def kettlebell(c: Pal) -> str:
    return (
        P(
            "M262 300Q250 200 320 200Q390 200 378 300",
            "none",
            stroke=INK,
            stroke_width=26,
            stroke_opacity=1,
        )
        + C(320, 360, 92, INK)
        + E(286, 330, 18, 26, W, fill_opacity=0.25)
        + R(292, 350, 56, 36, c.I, 8)
        + T(320, 378, "16", W, 28)
    )


@art("bike-lock")
def bike_lock(c: Pal) -> str:
    return (
        P(
            "M250 340V260Q250 190 320 190Q390 190 390 260V340",
            "none",
            stroke=SILD,
            stroke_width=26,
            stroke_opacity=1,
        )
        + R(214, 320, 212, 70, c.I, 20)
        + C(390, 355, 12, INK)
        + R(236, 346, 110, 18, c.D, 9)
    )


@art("yoga-mat", "yoga-strap")
def yoga_mat(c: Pal) -> str:
    return (
        R(180, 300, 250, 110, c.I)
        + E(180, 355, 40, 55, c.I)
        + E(430, 355, 40, 55, c.D)
        + E(430, 355, 22, 32, c.T)
        + R(250, 296, 16, 118, c.A)
        + R(350, 296, 16, 118, c.A)
    )


reg(
    "volleyball",
    lambda c: ball(
        c,
        "#fef3c7",
        "M320 340Q360 280 330 240M320 340Q250 330 226 380M320 340Q350 400 404 404M300 244Q250 290 244 350M246 396Q320 420 380 424M412 300Q400 360 350 400",
        "#2563eb",
    ),
)


@art("game-controller")
def game_controller(c: Pal) -> str:
    return (
        P(
            "M230 290H410Q460 290 470 350L482 410Q488 440 460 440Q440 440 420 410L400 384H240L220 410Q200 440 180 440Q152 440 158 410L170 350Q180 290 230 290z",
            INK,
        )
        + L("M232 328V372M210 350H254", "#94a3b8", 12, stroke_linecap="butt")
        + C(396, 330, 11, "#ef4444")
        + C(420, 354, 11, YELLOW)
        + C(372, 354, 11, "#22c55e")
        + C(396, 378, 11, c.I)
        + C(290, 380, 16, "#475569")
        + C(350, 380, 16, "#475569")
    )


@art("pillow", "mattress-protector", "bath-mat")
def pillow(c: Pal) -> str:
    shape = "M196 262Q320 236 444 262Q430 346 444 430Q320 404 196 430Q210 346 196 262z"
    return (
        P(shape, c.T)
        + P(
            "M220 284Q320 264 420 284Q408 346 420 408Q320 388 220 408Q232 346 220 284z",
            "none",
            stroke=W,
            stroke_width=5,
            stroke_dasharray="10 8",
            stroke_opacity=0.9,
        )
        + E(280, 300, 40, 12, W, fill_opacity=0.4, transform="rotate(-8 280 300)")
    )


@art("vacuum")
def vacuum(c: Pal) -> str:
    return (
        L("M404 176L280 410", INK, 12)
        + R(388, 160, 50, 30, c.I, 12, transform="rotate(28 413 175)")
        + at(R(-30, -66, 60, 132, c.I, 28) + R(-18, -40, 36, 50, c.P, 14), 350, 296, 1, 28)
        + P("M206 404H320Q340 404 340 424V440H206Q190 440 190 424Q190 404 206 404z", INK)
        + R(196, 432, 140, 8, c.A, 4)
    )


@art("robot-vacuum")
def robot_vacuum(c: Pal) -> str:
    return (
        E(320, 404, 140, 40, INK)
        + E(320, 386, 140, 40, "#334155")
        + E(320, 380, 50, 14, c.I)
        + C(380, 376, 7, "#22c55e")
        + L("M204 410L176 430M436 410L464 430", "#94a3b8", 4)
    )


@art("air-purifier", "humidifier", "air-purifier-filter")
def air_purifier(c: Pal) -> str:
    return (
        L(
            "M290 180c-10-16 10-24 0-40M330 180c-10-16 10-24 0-40M370 180c-10-16 10-24 0-40",
            "#cbd5e1",
            6,
        )
        + R(252, 190, 136, 250, W, 30)
        + R(252, 190, 136, 40, c.T, 20)
        + "".join(L(f"M272 {y}H368", c.P, 6) for y in range(262, 420, 20))
        + C(320, 210, 7, c.I)
    )


@art("mixing-bowls", "measuring-cups")
def mixing_bowls(c: Pal) -> str:
    return (
        P("M186 320H454Q448 440 320 440Q192 440 186 320z", c.I)
        + E(320, 320, 134, 18, c.D)
        + P("M230 290H410Q404 380 320 380Q236 380 230 290z", c.A)
        + E(320, 290, 90, 12, shade(c.A, 0.2))
        + shine("M210 344Q220 400 260 420", 9, 0.35)
    )


@art("dinnerware-set")
def dinnerware(c: Pal) -> str:
    return (
        E(320, 420, 150, 26, W)
        + E(320, 410, 150, 26, c.P)
        + E(320, 398, 150, 26, W)
        + E(320, 398, 100, 16, c.P)
        + P("M232 330H408Q402 390 320 390Q238 390 232 330z", c.I)
        + E(320, 330, 88, 14, c.D)
    )


@art("drinking-glasses", "tumbler")
def drinking_glasses(c: Pal) -> str:
    def glass(h: int) -> str:
        return (
            P(f"M-50-{h}H50L40 90Q38 100 28 100H-28Q-38 100-40 90z", "#e0f2fe", fill_opacity=0.9)
            + P("M-44-10H44L40 90Q38 100 28 100H-28Q-38 100-40 90z", c.T)
            + L(f"M-34-{h - 16}L-28 80", W, 6)
        )

    return at(glass(120), 390, 340, 0.85) + at(glass(140), 270, 340)


@art("electric-kettle")
def electric_kettle(c: Pal) -> str:
    return (
        E(310, 432, 110, 12, INK)
        + P("M232 250H388L400 420H220z", c.I)
        + P("M236 250Q310 214 384 250z", c.D)
        + P(
            "M388 270Q440 270 440 330Q440 390 396 400",
            "none",
            stroke=INK,
            stroke_width=18,
            stroke_opacity=1,
        )
        + P("M232 270L192 244L200 232L236 250z", c.I)
        + R(258, 290, 18, 100, "#bae6fd", 9)
    )


@art("package")
def package(c: Pal) -> str:
    """The universal fallback: a department-colored parcel."""
    return (
        box3d(214, 280, 190, 160, 56, c.I, c.T, c.D)
        + R(292, 280, 34, 160, c.A)
        + P("M292 280l56-28h34l-56 28z", c.AL)
        + R(232, 300, 50, 30, W, 6)
    )


# ---------------------------------------------------------------------------------------------
# Resolution for types without a drawing of their own (new seed types): a keyword rule on the
# type's hyphenated words, then the department's default glyph, then a plain parcel.

KEYWORDS: tuple[tuple[str, str], ...] = (
    ("vitamin", "multivitamin"),
    ("supplement", "multivitamin"),
    ("cleaner", "all-purpose-cleaner"),
    ("detergent", "laundry-detergent"),
    ("wipes", "disinfecting-wipes"),
    ("cable", "usb-c-cable"),
    ("charger", "usb-c-charger"),
    ("speaker", "bluetooth-speaker"),
    ("camera", "security-camera"),
    ("juice", "juice"),
    ("tea", "tea"),
    ("coffee", "coffee"),
    ("water", "water"),
    ("soda", "soda"),
    ("chips", "chips"),
    ("bar", "granola-bar"),
    ("cookies", "cookies"),
    ("candy", "candy"),
    ("sauce", "pasta-sauce"),
    ("canned", "canned-beans"),
    ("soup", "soup"),
    ("cereal", "cereal"),
    ("cheese", "cheese"),
    ("milk", "milk"),
    ("yogurt", "yogurt"),
    ("bread", "bread"),
    ("frozen", "frozen-vegetables"),
    ("ice", "ice-cream"),
    ("chicken", "chicken"),
    ("beef", "ground-beef"),
    ("fish", "salmon"),
    ("shampoo", "shampoo"),
    ("lotion", "body-lotion"),
    ("soap", "bar-soap"),
    ("shirt", "t-shirt"),
    ("jacket", "puffer-jacket"),
    ("pants", "jeans"),
    ("shoes", "sneakers"),
    ("ball", "basketball"),
    ("bike", "bike"),
    ("toy", "plush-toy"),
    ("game", "board-game"),
    ("dog", "dog-food"),
    ("cat", "cat-food"),
    ("baby", "baby-food"),
    ("knife", "kitchen-knife"),
    ("pan", "skillet"),
    ("pot", "cookware-set"),
    ("towel", "bath-towels"),
    ("blanket", "comforter"),
    ("lamp", "light-bulbs"),
    ("paper", "copy-paper"),
    ("pen", "pens"),
    ("bag", "backpack"),
)

DEPT_DEFAULT: dict[str, str] = {
    "dairy-eggs": "milk",
    "produce": "apples",
    "meat-seafood": "steak",
    "bakery": "bread",
    "frozen": "frozen-vegetables",
    "pantry": "food-can",
    "snacks": "chips",
    "beverages": "soda",
    "household": "all-purpose-cleaner",
    "health-wellness": "multivitamin",
    "baby": "baby-food",
    "pet": "dog-food",
    "electronics": "power-bank",
    "home-kitchen": "storage-bins",
    "clothing-shoes": "t-shirt",
    "outdoor": "planter",
    "sports": "water-bottle",
    "toys": "building-blocks",
    "beauty": "flip-bottle",
    "office": "notebook",
}
reg("food-can", lambda c: food_can(c, em_star(W), band=c.A))
reg("flip-bottle", lambda c: flip_bottle(c, c.I, em_drop(c.I)))


def resolve(product_type: str, category: str) -> str:
    """The name of the drawing used for a product type (a key of ``ART``)."""
    if product_type in ART:
        return product_type
    words = product_type.split("-")
    for word, target in KEYWORDS:
        if word in words:
            return target
    return DEPT_DEFAULT.get(category, "package")


def accent_for(product_type: str) -> str:
    return ACCENTS[zlib.crc32(product_type.encode()) % len(ACCENTS)]


def art_for(product_type: str, category: str, color: str) -> str:
    """The glyph markup for a product type, in the department color."""
    name = resolve(product_type, category)
    draw, pinned = ART[name]
    # A pinned accent belongs to the drawn types; fallbacks get the type's own accent.
    accent = pinned if (pinned and name == product_type) else accent_for(product_type)
    return draw(Pal.make(color, accent))
