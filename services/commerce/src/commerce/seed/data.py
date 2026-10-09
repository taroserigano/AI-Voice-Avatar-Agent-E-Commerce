"""Original seed catalog. Every brand and product here is invented for this project.

Images are generated placeholders in ``apps/web/public/images/products/`` (see
``scripts/generate_placeholders.py``); nothing links to another website.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any

from commerce.catalog.models import PolicyClass


@dataclass(frozen=True)
class CategorySeed:
    slug: str
    name: str
    policy_class: PolicyClass
    color: str  # placeholder image colour


@dataclass(frozen=True)
class VariantSeed:
    code: str
    name: str
    stock: int
    price_cents: int | None = None  # None: use the product's base price
    attributes: dict[str, Any] = field(default_factory=dict)
    sku: str | None = None  # None: derived from the product slug with make_sku()


@dataclass(frozen=True)
class Nutrition:
    """Per labeled serving, as on a US nutrition facts panel."""

    serving_size: str
    calories: int
    total_fat_g: float
    saturated_fat_g: float
    sodium_mg: int
    total_carbs_g: float
    fiber_g: float
    total_sugars_g: float
    added_sugars_g: float
    protein_g: float

    @property
    def net_carbs_g(self) -> float:
        return max(0.0, self.total_carbs_g - self.fiber_g)


@dataclass(frozen=True)
class ProductSeed:
    slug: str
    title: str
    brand: str
    category: str
    price_cents: int
    description: str
    variants: tuple[VariantSeed, ...]
    product_type: str = "general"  # e.g. "milk", "greek-yogurt", "headphones"
    tags: tuple[str, ...] = ()  # slugs from commerce.catalog.tags.TAGS
    nutrition: Nutrition | None = None
    ingredients: str | None = None
    allergens: tuple[str, ...] = ()  # e.g. ("milk", "soy"), the major US food allergens
    specs: dict[str, str] = field(default_factory=dict)  # e.g. {"Milkfat": "0%"}
    image_path: str | None = None  # None: /images/products/<slug>.svg

    def details(self) -> dict[str, Any]:
        """The ``products.details`` JSON document."""
        return {
            "nutrition": asdict(self.nutrition) if self.nutrition else None,
            "ingredients": self.ingredients,
            "allergens": list(self.allergens),
            "specs": dict(self.specs),
        }


CATEGORIES: tuple[CategorySeed, ...] = (
    # Grocery. Fresh and frozen food isn't sent back (see the "perishable" policy class).
    CategorySeed("dairy-eggs", "Dairy & Eggs", PolicyClass.PERISHABLE, "#0369a1"),
    CategorySeed("produce", "Fresh Produce", PolicyClass.PERISHABLE, "#4d7c0f"),
    CategorySeed("meat-seafood", "Meat & Seafood", PolicyClass.PERISHABLE, "#b91c1c"),
    CategorySeed("bakery", "Bakery & Bread", PolicyClass.PERISHABLE, "#92400e"),
    CategorySeed("frozen", "Frozen", PolicyClass.PERISHABLE, "#0e7490"),
    CategorySeed("pantry", "Pantry", PolicyClass.STANDARD, "#a16207"),
    CategorySeed("snacks", "Snacks", PolicyClass.STANDARD, "#c2410c"),
    CategorySeed("beverages", "Beverages", PolicyClass.STANDARD, "#1d4ed8"),
    CategorySeed("household", "Household Essentials", PolicyClass.STANDARD, "#0f766e"),
    CategorySeed("health-wellness", "Health & Wellness", PolicyClass.STANDARD, "#15803d"),
    CategorySeed("baby", "Baby", PolicyClass.STANDARD, "#db2777"),
    CategorySeed("pet", "Pet Supplies", PolicyClass.STANDARD, "#7c2d12"),
    # General merchandise
    CategorySeed("electronics", "Electronics", PolicyClass.INSPECTION, "#2563eb"),
    CategorySeed("home-kitchen", "Home & Kitchen", PolicyClass.STANDARD, "#b45309"),
    CategorySeed("clothing-shoes", "Clothing & Shoes", PolicyClass.STANDARD, "#be185d"),
    CategorySeed("outdoor", "Outdoor & Garden", PolicyClass.STANDARD, "#15803d"),
    CategorySeed("sports", "Sports & Fitness", PolicyClass.STANDARD, "#c2410c"),
    CategorySeed("toys", "Toys & Games", PolicyClass.STANDARD, "#7c3aed"),
    CategorySeed("beauty", "Beauty & Personal Care", PolicyClass.STANDARD, "#0f766e"),
    CategorySeed("office", "Office & School", PolicyClass.STANDARD, "#475569"),
    CategorySeed("gift-cards", "Gift Cards", PolicyClass.FINAL_SALE, "#a16207"),
)


def _one(stock: int, code: str = "STD", name: str = "Standard") -> tuple[VariantSeed, ...]:
    return (VariantSeed(code, name, stock),)


def _colors(*pairs: tuple[str, int]) -> tuple[VariantSeed, ...]:
    return tuple(
        VariantSeed(name[:3].upper(), name, stock, attributes={"color": name})
        for name, stock in pairs
    )


def _sizes(sizes: tuple[str, ...], stock: int, color: str | None = None) -> tuple[VariantSeed, ...]:
    out = []
    for s in sizes:
        attrs: dict[str, Any] = {"size": s}
        label = s
        if color:
            attrs["color"] = color
            label = f"{color} / {s}"
        out.append(VariantSeed(s.replace(".", "_"), label, stock, attributes=attrs))
    return tuple(out)


def _values(*dollars: int) -> tuple[VariantSeed, ...]:
    """Gift card amounts. Gift cards are digital, so they never run out."""
    return tuple(
        VariantSeed(str(d), f"${d}", 999, price_cents=d * 100, attributes={"value": f"${d}"})
        for d in dollars
    )


_HANDWRITTEN: tuple[ProductSeed, ...] = (
    # --- Electronics (returns need inspection) ---
    ProductSeed(
        "sonora-arc-wireless-headphones",
        "Arc Wireless Over-Ear Headphones",
        "Sonora Audio",
        "electronics",
        12999,
        "Over-ear Bluetooth headphones with active noise cancelling, 40-hour battery, and "
        "soft memory-foam cushions. Folds flat for travel; includes a braided USB-C cable.",
        _colors(("Midnight", 14), ("Sand", 6)),
    ),
    ProductSeed(
        "sonora-pulse-wireless-earbuds",
        "Pulse Wireless Earbuds",
        "Sonora Audio",
        "electronics",
        7999,
        "True wireless in-ear earbuds with a pocket charging case, sweat resistance for "
        "workouts, and transparency mode so you can hear traffic on a run.",
        _colors(("Graphite", 25), ("Frost", 10)),
    ),
    ProductSeed(
        "sonora-studio-wired-headphones",
        "Studio Wired Headphones",
        "Sonora Audio",
        "electronics",
        5499,
        "Closed-back wired headphones for home recording and focused listening, with a "
        "detachable coiled cable and a 3.5 mm to 6.35 mm adapter.",
        _one(9),
    ),
    ProductSeed(
        "lumen-beam-bluetooth-speaker",
        "Beam Portable Bluetooth Speaker",
        "Lumen Labs",
        "electronics",
        4999,
        "Rugged, waterproof portable speaker that floats. Twelve hours of playback, a "
        "clip-on strap, and pairing with a second speaker for stereo sound at the beach.",
        _colors(("Ocean", 18), ("Coral", 0)),
    ),
    ProductSeed(
        "lumen-glow-smart-bulb-4pk",
        "Glow Smart LED Bulbs, 4-Pack",
        "Lumen Labs",
        "electronics",
        3999,
        "Wi-Fi colour bulbs you can dim and schedule from your phone or voice assistant. "
        "Warm white to daylight plus 16 million colours; no hub required.",
        _one(40),
    ),
    ProductSeed(
        "lumen-tablet-10",
        "Lumen Tab 10 Tablet, 64 GB",
        "Lumen Labs",
        "electronics",
        18999,
        "Ten-inch HD tablet for streaming, reading, and video calls, with a quad-core "
        "processor, 64 GB of storage, microSD expansion, and a kid-safe profile mode.",
        (
            VariantSeed("64", "64 GB", 7, attributes={"storage": "64 GB"}),
            VariantSeed("128", "128 GB", 3, price_cents=22999, attributes={"storage": "128 GB"}),
        ),
    ),
    ProductSeed(
        "lumen-power-bank-20k",
        "Charge 20K Power Bank",
        "Lumen Labs",
        "electronics",
        3499,
        "20,000 mAh portable charger with USB-C fast charging in and out. Charges a phone "
        "about four times; airline carry-on friendly.",
        _one(30),
    ),
    ProductSeed(
        "lumen-hd-webcam",
        "Clearview 1080p Webcam",
        "Lumen Labs",
        "electronics",
        4499,
        "Full-HD webcam with auto light correction, dual noise-reducing microphones, and a "
        "privacy shutter. Clips onto monitors and laptops.",
        _one(2),
    ),
    ProductSeed(
        "sonora-kids-headphones",
        "Mini Volume-Limited Kids Headphones",
        "Sonora Audio",
        "electronics",
        2499,
        "Lightweight on-ear headphones for kids with an 85 dB volume limit, a bendable "
        "headband, and a sharing port so two children can listen together.",
        _colors(("Lime", 20), ("Grape", 15)),
    ),
    # --- Home & Kitchen ---
    ProductSeed(
        "kettleworth-gooseneck-kettle",
        "Gooseneck Electric Kettle",
        "Kettleworth",
        "home-kitchen",
        5999,
        "Variable-temperature electric kettle with a precise pour spout for pour-over "
        "coffee and tea, a keep-warm setting, and a stainless steel body.",
        _colors(("Matte Black", 12), ("Brushed Steel", 8)),
    ),
    ProductSeed(
        "kettleworth-cast-iron-skillet",
        "Pre-Seasoned Cast Iron Skillet, 12 in",
        "Kettleworth",
        "home-kitchen",
        3299,
        "Heavy cast iron frying pan, pre-seasoned and ready for the stove, oven, grill, or "
        "campfire. Holds heat for searing steaks and baking cornbread.",
        _one(22),
    ),
    ProductSeed(
        "kettleworth-chef-knife",
        "8-inch Chef's Knife",
        "Kettleworth",
        "home-kitchen",
        4499,
        "Forged high-carbon stainless steel chef's knife with a full tang and a balanced, "
        "non-slip handle. Comes with a blade guard.",
        _one(16),
    ),
    ProductSeed(
        "harbor-home-linen-sheets",
        "Washed Linen Sheet Set",
        "Harbor Home",
        "home-kitchen",
        11999,
        "Breathable stone-washed linen sheets that get softer with every wash. Includes a "
        "fitted sheet, flat sheet, and two pillowcases.",
        _sizes(("Queen", "King"), 6, "Oat"),
    ),
    ProductSeed(
        "harbor-home-throw-blanket",
        "Chunky Knit Throw Blanket",
        "Harbor Home",
        "home-kitchen",
        4999,
        "Oversized chunky knit throw for the couch, made from soft acrylic yarn that "
        "doesn't shed. Machine washable on gentle.",
        _colors(("Cream", 14), ("Sage", 9)),
    ),
    ProductSeed(
        "harbor-home-glass-containers",
        "Glass Food Storage Containers, 10-Piece",
        "Harbor Home",
        "home-kitchen",
        2999,
        "Oven-safe borosilicate glass meal-prep containers with leak-proof locking lids. "
        "Microwave, freezer, and dishwasher safe.",
        _one(35),
    ),
    ProductSeed(
        "kettleworth-french-press",
        "Double-Wall French Press, 34 oz",
        "Kettleworth",
        "home-kitchen",
        2799,
        "Insulated stainless steel French press that keeps coffee hot for an hour, with a "
        "four-level filter for a clean cup.",
        _one(19),
    ),
    ProductSeed(
        "harbor-home-scented-candle",
        "Cedar & Sea Salt Soy Candle",
        "Harbor Home",
        "home-kitchen",
        1899,
        "Hand-poured soy wax candle with a cotton wick and a calm cedar and sea salt scent. "
        "About 45 hours of burn time.",
        _one(50),
    ),
    ProductSeed(
        "kettleworth-mixing-bowls",
        "Nesting Stainless Mixing Bowls, Set of 5",
        "Kettleworth",
        "home-kitchen",
        2499,
        "Five nesting stainless steel mixing bowls with non-slip bases and pouring lips, "
        "from 1 to 5 quarts.",
        _one(0),
    ),
    # --- Clothing & Shoes ---
    ProductSeed(
        "stridewell-rain-boots",
        "Puddle Waterproof Rain Boots",
        "Stridewell",
        "clothing-shoes",
        5499,
        "Fully waterproof rubber rain boots with a cushioned insole and a grippy outsole for "
        "wet sidewalks. Mid-calf height, easy pull-on tabs.",
        _sizes(("7", "8", "9", "10", "11"), 5, "Navy"),
    ),
    ProductSeed(
        "stridewell-trail-runner-gtx",
        "Ridge Waterproof Trail Running Shoes",
        "Stridewell",
        "clothing-shoes",
        11999,
        "Trail running shoes with a waterproof breathable membrane, lugged outsole, and "
        "rock plate. Keeps feet dry through puddles, rain, and muddy trails.",
        _sizes(("8", "9", "10", "11", "12"), 4, "Slate"),
    ),
    ProductSeed(
        "stridewell-everyday-sneaker",
        "Everyday Canvas Sneakers",
        "Stridewell",
        "clothing-shoes",
        4499,
        "Classic low-top canvas sneakers with a vulcanized rubber sole and a cushioned "
        "footbed for all-day wear.",
        _sizes(("7", "8", "9", "10", "11"), 8, "White"),
    ),
    ProductSeed(
        "driftwood-rain-shell",
        "Packable Rain Shell Jacket",
        "Driftwood Apparel",
        "clothing-shoes",
        7999,
        "Lightweight waterproof rain jacket with taped seams and an adjustable hood. Packs "
        "into its own pocket for commutes and travel.",
        _sizes(("S", "M", "L", "XL"), 6, "Olive"),
    ),
    ProductSeed(
        "driftwood-merino-crew",
        "Merino Wool Crew Sweater",
        "Driftwood Apparel",
        "clothing-shoes",
        8999,
        "Soft, itch-free merino wool sweater that regulates temperature and resists odor. "
        "A layering staple from fall to spring.",
        _sizes(("S", "M", "L", "XL"), 7, "Heather Grey"),
    ),
    ProductSeed(
        "driftwood-organic-tee",
        "Organic Cotton Tee",
        "Driftwood Apparel",
        "clothing-shoes",
        2200,
        "Midweight organic cotton crewneck T-shirt with a relaxed fit that holds its shape "
        "after washing.",
        _sizes(("S", "M", "L", "XL"), 20, "Black"),
    ),
    ProductSeed(
        "driftwood-wool-socks-3pk",
        "Hiking Wool Socks, 3-Pair",
        "Driftwood Apparel",
        "clothing-shoes",
        2400,
        "Cushioned merino-blend hiking socks that wick moisture and prevent blisters on long "
        "walks. Three pairs.",
        _sizes(("M", "L"), 30),
    ),
    # --- Outdoor & Garden ---
    ProductSeed(
        "summit-forge-2p-tent",
        "Basecamp 2-Person Backpacking Tent",
        "Summit Forge",
        "outdoor",
        18999,
        "Lightweight freestanding tent for two with a full rain fly, two doors, and "
        "color-coded poles for quick setup in wind and rain.",
        _one(5),
    ),
    ProductSeed(
        "summit-forge-sleeping-bag",
        "Ember 30°F Sleeping Bag",
        "Summit Forge",
        "outdoor",
        8999,
        "Synthetic-fill mummy sleeping bag rated to 30°F that stays warm when damp. "
        "Compresses into an included stuff sack.",
        _one(8),
    ),
    ProductSeed(
        "summit-forge-headlamp",
        "Trailbeam Rechargeable Headlamp",
        "Summit Forge",
        "outdoor",
        2999,
        "400-lumen rechargeable headlamp with red night mode, a tilting beam, and a "
        "water-resistant housing for camping and night runs.",
        _one(28),
    ),
    ProductSeed(
        "summit-forge-water-bottle",
        "Insulated Water Bottle, 32 oz",
        "Summit Forge",
        "outdoor",
        2999,
        "Vacuum-insulated stainless steel bottle that keeps drinks cold for 24 hours. "
        "Leak-proof lid with a carry loop.",
        _colors(("Glacier", 40), ("Pine", 25), ("Sunset", 12)),
    ),
    ProductSeed(
        "verdant-raised-garden-bed",
        "Cedar Raised Garden Bed, 4 x 2 ft",
        "Verdant Grounds",
        "outdoor",
        7499,
        "Untreated cedar raised bed kit for vegetables and herbs. Tool-free assembly with "
        "slide-in corner posts.",
        _one(10),
    ),
    ProductSeed(
        "verdant-garden-hose",
        "Kink-Free Garden Hose, 50 ft",
        "Verdant Grounds",
        "outdoor",
        3999,
        "Flexible, lightweight hose that doesn't kink or tangle, with crush-proof brass "
        "fittings and an 8-pattern spray nozzle.",
        _one(15),
    ),
    ProductSeed(
        "summit-forge-camp-chair",
        "Folding Camp Chair",
        "Summit Forge",
        "outdoor",
        3499,
        "Sturdy folding chair with a cup holder and side pocket; packs into a shoulder bag "
        "for camping, beach days, and sports sidelines.",
        _one(1),
    ),
    # --- Sports & Fitness ---
    ProductSeed(
        "tempo-yoga-mat",
        "Grip Yoga Mat, 6 mm",
        "Tempo Athletics",
        "sports",
        3999,
        "Non-slip, cushioned 6 mm yoga mat with alignment lines. Easy to wipe clean; "
        "includes a carry strap.",
        _colors(("Plum", 20), ("Seafoam", 18)),
    ),
    ProductSeed(
        "tempo-adjustable-dumbbells",
        "Adjustable Dumbbells, 5-25 lb Pair",
        "Tempo Athletics",
        "sports",
        14999,
        "A pair of space-saving adjustable dumbbells that switch from 5 to 25 pounds with a "
        "turn of the dial. Replaces ten sets of weights.",
        _one(4),
    ),
    ProductSeed(
        "tempo-jump-rope",
        "Speed Jump Rope",
        "Tempo Athletics",
        "sports",
        1499,
        "Adjustable ball-bearing speed rope for cardio and double-unders, with comfortable "
        "foam handles.",
        _one(45),
    ),
    ProductSeed(
        "tempo-resistance-bands",
        "Resistance Band Set, 5 Levels",
        "Tempo Athletics",
        "sports",
        1999,
        "Five latex-free loop bands from extra light to extra heavy for strength training, "
        "physical therapy, and stretching.",
        _one(38),
    ),
    ProductSeed(
        "tempo-foam-roller",
        "High-Density Foam Roller",
        "Tempo Athletics",
        "sports",
        2499,
        "Firm foam roller for post-workout muscle recovery and myofascial release. 18 inches long.",
        _one(21),
    ),
    # --- Toys & Games ---
    ProductSeed(
        "pebble-pine-wooden-blocks",
        "Wooden Building Blocks, 60 Pieces",
        "Pebble & Pine",
        "toys",
        3499,
        "Smooth, sustainably sourced hardwood blocks in classic shapes, finished with "
        "child-safe paint. For ages 2 and up.",
        _one(17),
    ),
    ProductSeed(
        "pebble-pine-puzzle-1000",
        "Harbor Lights 1000-Piece Puzzle",
        "Pebble & Pine",
        "toys",
        1999,
        "A 1000-piece jigsaw puzzle of a harbor at dusk, printed on thick recycled board with "
        "a poster for reference.",
        _one(26),
    ),
    ProductSeed(
        "pebble-pine-board-game",
        "Lighthouse Keepers Strategy Board Game",
        "Pebble & Pine",
        "toys",
        3999,
        "A cooperative strategy game for 2-5 players ages 10+: guide ships safely home "
        "before the storm. Plays in 45 minutes.",
        _one(11),
    ),
    ProductSeed(
        "pebble-pine-plush-otter",
        "Plush Otter Stuffed Animal",
        "Pebble & Pine",
        "toys",
        1799,
        "Soft 12-inch plush otter with embroidered eyes, safe for all ages and surface washable.",
        _one(33),
    ),
    ProductSeed(
        "pebble-pine-rc-car",
        "All-Terrain Remote Control Car",
        "Pebble & Pine",
        "toys",
        4999,
        "Rechargeable remote control truck with rubber tires, 20 mph top speed, and a "
        "splash-proof body for grass, dirt, and puddles.",
        _one(6),
    ),
    # --- Beauty & Personal Care ---
    ProductSeed(
        "verdant-botanicals-face-moisturizer",
        "Daily Face Moisturizer SPF 30",
        "Verdant Botanicals",
        "beauty",
        2400,
        "Lightweight, fragrance-free daily moisturizer with broad-spectrum SPF 30 and "
        "hyaluronic acid. Suitable for sensitive skin.",
        _one(29),
    ),
    ProductSeed(
        "verdant-botanicals-shampoo-bar",
        "Rosemary Mint Shampoo Bar",
        "Verdant Botanicals",
        "beauty",
        1200,
        "Plastic-free solid shampoo bar with rosemary and peppermint oils. Lasts about 80 washes.",
        _one(60),
    ),
    ProductSeed(
        "verdant-botanicals-electric-toothbrush",
        "Sonic Electric Toothbrush",
        "Verdant Botanicals",
        "beauty",
        4999,
        "Rechargeable sonic toothbrush with three modes, a two-minute timer, and a travel "
        "case. Includes two brush heads.",
        _one(13),
    ),
    ProductSeed(
        "verdant-botanicals-hand-cream",
        "Shea Butter Hand Cream Trio",
        "Verdant Botanicals",
        "beauty",
        1600,
        "Three travel-size hand creams with shea butter in lavender, citrus, and unscented.",
        _one(41),
    ),
    # --- Office & School ---
    ProductSeed(
        "quillmark-dotted-notebook",
        "Dotted Hardcover Notebook, A5",
        "Quillmark",
        "office",
        1499,
        "A5 hardcover notebook with 192 pages of dotted, fountain-pen friendly paper, a "
        "ribbon marker, and an elastic closure.",
        _colors(("Forest", 34), ("Terracotta", 22)),
    ),
    ProductSeed(
        "quillmark-gel-pens-12pk",
        "Quick-Dry Gel Pens, 12-Pack",
        "Quillmark",
        "office",
        1199,
        "Smooth 0.5 mm gel pens in assorted colours with smear-resistant, quick-dry ink.",
        _one(55),
    ),
    ProductSeed(
        "quillmark-desk-lamp",
        "Adjustable LED Desk Lamp",
        "Quillmark",
        "office",
        3999,
        "Dimmable LED desk lamp with five colour temperatures, a USB charging port, and a "
        "flexible arm.",
        _one(14),
    ),
    ProductSeed(
        "quillmark-laptop-backpack",
        "Commuter Laptop Backpack",
        "Quillmark",
        "office",
        6999,
        "Water-resistant backpack with a padded 16-inch laptop sleeve, luggage pass-through, "
        "and hidden anti-theft pocket.",
        _colors(("Charcoal", 12), ("Navy", 9)),
    ),
    # --- Gift Cards (final sale) ---
    ProductSeed(
        "serigan-mart-gift-card",
        "Serigan Mart Gift Card",
        "Serigan Mart",
        "gift-cards",
        2500,
        "A digital Serigan Mart gift card delivered by email. Gift cards are final sale and "
        "can't be returned.",
        (
            VariantSeed("25", "$25", 999, price_cents=2500, attributes={"value": "$25"}),
            VariantSeed("50", "$50", 999, price_cents=5000, attributes={"value": "$50"}),
            VariantSeed("100", "$100", 999, price_cents=10000, attributes={"value": "$100"}),
        ),
    ),
    ProductSeed(
        "serigan-mart-birthday-gift-card",
        "Happy Birthday Gift Card",
        "Serigan Mart",
        "gift-cards",
        2500,
        "A digital Serigan Mart gift card with a birthday design, delivered by email. Good for "
        "groceries and everything else in the store. Gift cards are final sale and can't be "
        "returned.",
        _values(25, 50, 100),
    ),
    ProductSeed(
        "serigan-mart-thank-you-gift-card",
        "Thank You Gift Card",
        "Serigan Mart",
        "gift-cards",
        1500,
        "A digital Serigan Mart gift card with a thank-you design, delivered by email: an easy "
        "thanks for a teacher, neighbor, or host. Gift cards are final sale and can't be "
        "returned.",
        _values(15, 25, 50),
    ),
    ProductSeed(
        "serigan-mart-holiday-gift-card",
        "Holiday Gift Card",
        "Serigan Mart",
        "gift-cards",
        2500,
        "A digital Serigan Mart gift card with a winter holiday design, delivered by email. Good "
        "for holiday groceries, gifts, and everything else in the store. Gift cards are final "
        "sale and can't be returned.",
        _values(25, 50, 100, 200),
    ),
)


# Product type and tags for the hand-written products above.
_ENRICHMENT: dict[str, tuple[str, tuple[str, ...]]] = {
    "sonora-arc-wireless-headphones": (
        "headphones",
        ("wireless", "bluetooth", "noise-cancelling", "rechargeable", "usb-c"),
    ),
    "sonora-pulse-wireless-earbuds": (
        "earbuds",
        ("wireless", "bluetooth", "water-resistant", "rechargeable"),
    ),
    "sonora-studio-wired-headphones": ("headphones", ()),
    "lumen-beam-bluetooth-speaker": (
        "bluetooth-speaker",
        ("wireless", "bluetooth", "waterproof", "rechargeable"),
    ),
    "lumen-glow-smart-bulb-4pk": ("smart-bulb", ("smart-home", "energy-efficient", "wireless")),
    "lumen-tablet-10": ("tablet", ("wireless", "rechargeable", "usb-c")),
    "lumen-power-bank-20k": ("power-bank", ("rechargeable", "usb-c")),
    "lumen-hd-webcam": ("webcam", ()),
    "sonora-kids-headphones": ("headphones", ("kids",)),
    "kettleworth-gooseneck-kettle": ("electric-kettle", ()),
    "kettleworth-cast-iron-skillet": ("skillet", ()),
    "kettleworth-chef-knife": ("kitchen-knife", ()),
    "harbor-home-linen-sheets": ("sheet-set", ("machine-washable",)),
    "harbor-home-throw-blanket": ("throw-blanket", ("machine-washable",)),
    "harbor-home-glass-containers": ("food-storage", ("bpa-free", "dishwasher-safe")),
    "kettleworth-french-press": ("coffee-maker", ("dishwasher-safe",)),
    "harbor-home-scented-candle": ("candle", ()),
    "kettleworth-mixing-bowls": ("mixing-bowls", ("dishwasher-safe",)),
    "stridewell-rain-boots": ("boots", ("waterproof",)),
    "stridewell-trail-runner-gtx": ("running-shoes", ("waterproof",)),
    "stridewell-everyday-sneaker": ("sneakers", ()),
    "driftwood-rain-shell": ("rain-jacket", ("waterproof",)),
    "driftwood-merino-crew": ("sweater", ()),
    "driftwood-organic-tee": ("t-shirt", ("organic", "machine-washable")),
    "driftwood-wool-socks-3pk": ("socks", ("moisture-wicking",)),
    "summit-forge-2p-tent": ("tent", ("waterproof",)),
    "summit-forge-sleeping-bag": ("sleeping-bag", ()),
    "summit-forge-headlamp": ("headlamp", ("rechargeable", "water-resistant", "usb-c")),
    "summit-forge-water-bottle": ("water-bottle", ("bpa-free",)),
    "verdant-raised-garden-bed": ("garden-bed", ()),
    "verdant-garden-hose": ("garden-hose", ()),
    "summit-forge-camp-chair": ("camp-chair", ()),
    "tempo-yoga-mat": ("yoga-mat", ()),
    "tempo-adjustable-dumbbells": ("dumbbells", ()),
    "tempo-jump-rope": ("jump-rope", ()),
    "tempo-resistance-bands": ("resistance-bands", ()),
    "tempo-foam-roller": ("foam-roller", ()),
    "pebble-pine-wooden-blocks": ("building-blocks", ("kids",)),
    "pebble-pine-puzzle-1000": ("puzzle", ()),
    "pebble-pine-board-game": ("board-game", ()),
    "pebble-pine-plush-otter": ("plush-toy", ("kids",)),
    "pebble-pine-rc-car": ("rc-car", ("rechargeable", "kids")),
    "verdant-botanicals-face-moisturizer": (
        "face-moisturizer",
        ("fragrance-free", "sensitive-skin", "cruelty-free"),
    ),
    "verdant-botanicals-shampoo-bar": ("shampoo", ("cruelty-free", "vegan", "sulfate-free")),
    "verdant-botanicals-electric-toothbrush": ("electric-toothbrush", ("rechargeable",)),
    "verdant-botanicals-hand-cream": ("hand-cream", ("cruelty-free",)),
    "quillmark-dotted-notebook": ("notebook", ()),
    "quillmark-gel-pens-12pk": ("pens", ()),
    "quillmark-desk-lamp": ("desk-lamp", ("energy-efficient", "usb-c")),
    "quillmark-laptop-backpack": ("backpack", ("water-resistant",)),
    "serigan-mart-gift-card": ("gift-card", ()),
    "serigan-mart-birthday-gift-card": ("gift-card", ()),
    "serigan-mart-thank-you-gift-card": ("gift-card", ()),
    "serigan-mart-holiday-gift-card": ("gift-card", ()),
}

_WARRANTY_1Y = "1-year limited"
_GIFT_CARD = {
    "Format": "Digital, delivered by email",
    "Redeemable for": "Anything sold at Serigan Mart",
    "Returns": "Final sale: can't be returned, exchanged, or refunded",
    "Cash value": "None, except where the law requires it",
}

# Specification rows for the hand-written products, taken from what each description says.
# commerce.seed.specs adds the rest (options, sizes, model numbers) on the way out.
_SPECS: dict[str, dict[str, str]] = {
    "sonora-arc-wireless-headphones": {
        "Type": "Over-ear", "Connection": "Bluetooth", "Noise cancelling": "Active",
        "Battery life": "Up to 40 hours", "Charging": "USB-C (braided cable included)",
        "Ear cushions": "Memory foam", "Folds flat": "Yes, for travel",
        "In the box": "Headphones, braided USB-C cable", "Warranty": _WARRANTY_1Y,
    },
    "sonora-pulse-wireless-earbuds": {
        "Type": "True wireless, in-ear", "Connection": "Bluetooth",
        "Water resistance": "Sweat-resistant", "Transparency mode": "Yes",
        "Charging case": "Pocket-size", "In the box": "Earbuds, charging case",
        "Warranty": _WARRANTY_1Y,
    },
    "sonora-studio-wired-headphones": {
        "Type": "Over-ear, closed back", "Connection": "Wired, 3.5 mm",
        "Cable": "Detachable, coiled", "Adapter": "3.5 mm to 6.35 mm, included",
        "Use": "Home recording and focused listening",
        "In the box": "Headphones, coiled cable, 6.35 mm adapter", "Warranty": _WARRANTY_1Y,
    },
    "lumen-beam-bluetooth-speaker": {
        "Connection": "Bluetooth", "Battery life": "Up to 12 hours",
        "Water resistance": "Waterproof, floats", "Stereo pairing": "With a second Beam speaker",
        "Strap": "Clip-on", "Warranty": _WARRANTY_1Y,
    },
    "lumen-glow-smart-bulb-4pk": {
        "Count": "4 bulbs", "Connection": "Wi-Fi (no hub required)",
        "Colors": "Warm white to daylight, plus 16 million colors", "Dimmable": "Yes",
        "Control": "Phone app or voice assistant, with schedules", "Warranty": _WARRANTY_1Y,
    },
    "lumen-tablet-10": {
        "Screen size": "10 in, HD", "Processor": "Quad-core", "Storage": "64 GB or 128 GB",
        "Expandable storage": "microSD card slot", "Charging": "USB-C",
        "Profiles": "Kid-safe profile mode", "Use": "Streaming, reading, and video calls",
        "Warranty": _WARRANTY_1Y,
    },
    "lumen-power-bank-20k": {
        "Capacity": "20,000 mAh", "USB-C": "Fast charging, in and out",
        "Phone charges": "About 4 full charges",
        "Air travel": "Carry-on friendly (74 Wh, under the 100 Wh airline limit)",
        "In the box": "Power bank, USB-C to USB-C cable", "Warranty": _WARRANTY_1Y,
    },
    "lumen-hd-webcam": {
        "Resolution": "1080p Full HD", "Microphone": "Dual, noise-reducing",
        "Light correction": "Automatic", "Privacy cover": "Built-in shutter",
        "Mount": "Clips onto monitors and laptops", "Warranty": _WARRANTY_1Y,
    },
    "sonora-kids-headphones": {
        "Type": "On-ear", "Connection": "Wired, 3.5 mm", "Volume limit": "85 dB",
        "Headband": "Bendable", "Sharing port": "Yes, for a second pair of headphones",
        "Weight": "Lightweight", "Warranty": _WARRANTY_1Y,
    },
    "kettleworth-gooseneck-kettle": {
        "Temperature control": "Variable, with keep-warm setting", "Spout": "Gooseneck",
        "Body": "Stainless steel", "Use": "Pour-over coffee and tea", "Warranty": _WARRANTY_1Y,
    },
    "kettleworth-cast-iron-skillet": {
        "Diameter": "12 in", "Material": "Cast iron", "Seasoning": "Pre-seasoned",
        "Use on": "Stove, oven, grill, or campfire",
        "Care": "Hand wash, dry right away, and oil lightly", "Warranty": "Limited lifetime",
    },
    "kettleworth-chef-knife": {
        "Blade length": "8 in", "Blade": "Forged high-carbon stainless steel",
        "Construction": "Full tang", "Handle": "Balanced, non-slip",
        "Includes": "Blade guard", "Care": "Hand wash", "Warranty": "Limited lifetime",
    },
    "harbor-home-linen-sheets": {
        "Material": "Stone-washed linen",
        "Includes": "Fitted sheet, flat sheet, and two pillowcases",
        "Feel": "Breathable; softens with every wash",
    },
    "harbor-home-throw-blanket": {
        "Material": "Acrylic chunky knit yarn", "Size": "Oversized throw",
        "Shedding": "Doesn't shed", "Care": "Machine washable on gentle",
    },
    "harbor-home-glass-containers": {
        "Pieces": "10", "Material": "Borosilicate glass", "Lids": "Leak-proof, locking",
        "Oven safe": "Glass containers", "Microwave, freezer, and dishwasher safe": "Yes",
        "Use": "Meal prep and leftovers",
    },
    "kettleworth-french-press": {
        "Capacity": "34 oz", "Material": "Double-wall insulated stainless steel",
        "Keeps hot": "About 1 hour", "Filter": "Four-level", "Warranty": "Limited lifetime",
    },
    "harbor-home-scented-candle": {
        "Scent": "Cedar and sea salt", "Wax": "Soy", "Wick": "Cotton",
        "Burn time": "About 45 hours", "Made": "Hand-poured",
    },
    "kettleworth-mixing-bowls": {
        "Pieces": "5 nesting bowls", "Sizes": "1 to 5 quarts", "Material": "Stainless steel",
        "Base": "Non-slip", "Rim": "Pouring lips",
    },
    "stridewell-rain-boots": {
        "Material": "Rubber", "Waterproof": "Fully waterproof", "Height": "Mid-calf",
        "Insole": "Cushioned", "Outsole": "Grippy, for wet sidewalks",
        "Closure": "Pull-on, with tabs",
    },
    "stridewell-trail-runner-gtx": {
        "Waterproof": "Breathable waterproof membrane", "Outsole": "Lugged",
        "Protection": "Rock plate", "Use": "Trail running in rain and mud",
        "Closure": "Lace-up",
    },
    "stridewell-everyday-sneaker": {
        "Upper": "Canvas", "Sole": "Vulcanized rubber", "Footbed": "Cushioned",
        "Style": "Low-top", "Closure": "Lace-up",
    },
    "driftwood-rain-shell": {
        "Waterproof": "Yes, with taped seams", "Hood": "Adjustable",
        "Packable": "Into its own pocket", "Weight": "Lightweight",
        "Use": "Commutes and travel",
    },
    "driftwood-merino-crew": {
        "Material": "Merino wool", "Neckline": "Crew",
        "Features": "Itch-free, temperature-regulating, odor-resistant",
        "Season": "Fall to spring",
    },
    "driftwood-organic-tee": {
        "Material": "Organic cotton", "Weight": "Midweight", "Fit": "Relaxed",
        "Neckline": "Crew", "Care": "Machine washable; holds its shape after washing",
    },
    "driftwood-wool-socks-3pk": {
        "Material": "Merino wool blend", "Count": "3 pairs", "Cushioning": "Cushioned",
        "Moisture-wicking": "Yes", "Use": "Hiking and long walks",
    },
    "summit-forge-2p-tent": {
        "Capacity": "2 people", "Doors": "2", "Rain fly": "Full coverage",
        "Setup": "Freestanding, color-coded poles", "Use": "Backpacking",
        "Warranty": "Limited lifetime",
    },
    "summit-forge-sleeping-bag": {
        "Temperature rating": "30°F", "Fill": "Synthetic (stays warm when damp)",
        "Shape": "Mummy", "Stuff sack": "Included", "Warranty": "Limited lifetime",
    },
    "summit-forge-headlamp": {
        "Brightness": "400 lumens", "Night mode": "Red light", "Beam": "Tilting",
        "Water resistance": "Water-resistant", "Power": "Rechargeable, USB-C",
        "Warranty": _WARRANTY_1Y,
    },
    "summit-forge-water-bottle": {
        "Capacity": "32 oz", "Material": "Vacuum-insulated stainless steel",
        "Keeps cold": "24 hours", "Lid": "Leak-proof, with carry loop", "BPA-free": "Yes",
    },
    "verdant-raised-garden-bed": {
        "Size": "4 x 2 ft", "Material": "Untreated cedar",
        "Assembly": "Tool-free, slide-in corner posts", "Use": "Vegetables and herbs",
    },
    "verdant-garden-hose": {
        "Length": "50 ft", "Fittings": "Crush-proof brass", "Kink-free": "Yes",
        "Nozzle included": "Yes, 8 spray patterns",
    },
    "summit-forge-camp-chair": {
        "Style": "Folding", "Cup holder": "Yes", "Storage": "Side pocket",
        "Carry bag": "Shoulder bag, included", "Use": "Camping, beach days, and sidelines",
    },
    "tempo-yoga-mat": {
        "Thickness": "6 mm", "Surface": "Non-slip, cushioned", "Alignment lines": "Yes",
        "Carry strap": "Included", "Care": "Wipe clean",
    },
    "tempo-adjustable-dumbbells": {
        "Weight range": "5 to 25 lb per dumbbell", "Sold as": "Pair",
        "Adjustment": "Turn-dial selector", "Replaces": "10 sets of weights",
    },
    "tempo-jump-rope": {
        "Type": "Speed rope", "Bearings": "Ball-bearing", "Length": "Adjustable",
        "Handles": "Foam", "Use": "Cardio and double-unders",
    },
    "tempo-resistance-bands": {
        "Pieces": "5", "Resistance": "Extra light to extra heavy", "Type": "Loop bands",
        "Latex": "Latex-free", "Use": "Strength training, physical therapy, and stretching",
    },
    "tempo-foam-roller": {
        "Length": "18 in", "Firmness": "Firm", "Material": "High-density foam",
        "Use": "Post-workout recovery and myofascial release",
    },
    "pebble-pine-wooden-blocks": {
        "Pieces": "60", "Material": "Sustainably sourced hardwood",
        "Finish": "Child-safe paint", "Ages": "2+",
    },
    "pebble-pine-puzzle-1000": {
        "Pieces": "1000", "Image": "A harbor at dusk", "Material": "Thick recycled board",
        "Includes": "Reference poster",
    },
    "pebble-pine-board-game": {
        "Players": "2-5", "Ages": "10+", "Play time": "About 45 minutes",
        "Style": "Cooperative strategy",
    },
    "pebble-pine-plush-otter": {
        "Size": "12 in", "Eyes": "Embroidered", "Ages": "All ages", "Care": "Surface washable",
    },
    "pebble-pine-rc-car": {
        "Top speed": "20 mph", "Power": "Rechargeable battery", "Tires": "Rubber",
        "Body": "Splash-proof", "Terrain": "Grass, dirt, and puddles",
    },
    "verdant-botanicals-face-moisturizer": {
        "SPF": "30, broad spectrum", "Key ingredients": "Hyaluronic acid",
        "Fragrance": "Fragrance-free", "Skin type": "All, including sensitive",
        "Form": "Lightweight lotion", "Use": "Every morning",
    },
    "verdant-botanicals-shampoo-bar": {
        "Form": "Solid bar", "Scent": "Rosemary mint (rosemary and peppermint oils)",
        "Washes": "About 80", "Packaging": "Plastic-free", "Sulfates": "None",
    },
    "verdant-botanicals-electric-toothbrush": {
        "Type": "Sonic", "Modes": "3", "Timer": "2 minutes", "Power": "Rechargeable",
        "Brush heads": "2 included", "Case": "Travel case", "Warranty": _WARRANTY_1Y,
    },
    "verdant-botanicals-hand-cream": {
        "Count": "3 travel-size tubes", "Key ingredients": "Shea butter",
        "Scents": "Lavender, citrus, and unscented", "Form": "Cream",
    },
    "quillmark-dotted-notebook": {
        "Size": "A5", "Pages": "192", "Paper": "Dotted, fountain-pen friendly",
        "Cover": "Hardcover", "Extras": "Ribbon marker and elastic closure",
    },
    "quillmark-gel-pens-12pk": {
        "Count": "12", "Point": "0.5 mm", "Ink": "Gel, quick-dry and smear-resistant",
        "Colors": "Assorted",
    },
    "quillmark-desk-lamp": {
        "Light": "LED, dimmable", "Color temperatures": "5",
        "Charging port": "USB-C, for a phone", "Arm": "Flexible", "Warranty": _WARRANTY_1Y,
    },
    "quillmark-laptop-backpack": {
        "Laptop sleeve": "Padded, fits up to 16 in", "Water resistance": "Water-resistant",
        "Luggage pass-through": "Yes", "Security": "Hidden anti-theft pocket",
    },
    "serigan-mart-gift-card": {**_GIFT_CARD, "Design": "Serigan Mart flower"},
    "serigan-mart-birthday-gift-card": {**_GIFT_CARD, "Design": "Happy birthday"},
    "serigan-mart-thank-you-gift-card": {**_GIFT_CARD, "Design": "Thank you"},
    "serigan-mart-holiday-gift-card": {**_GIFT_CARD, "Design": "Winter holiday"},
}  # fmt: skip

# Products with a photoreal 3D render (apps/web/public/images/products-3d/, made with the
# scripts in docs/design). Everything else uses its illustration in images/products/.
_RENDERED_3D = frozenset(
    {
        "verdant-botanicals-face-moisturizer",
        "verdant-botanicals-shampoo-bar",
        "verdant-botanicals-electric-toothbrush",
        "verdant-botanicals-hand-cream",
    }
)

HANDWRITTEN_PRODUCTS: tuple[ProductSeed, ...] = tuple(
    replace(
        p,
        product_type=_ENRICHMENT[p.slug][0],
        tags=_ENRICHMENT[p.slug][1],
        specs=_SPECS.get(p.slug, {}),
        image_path=f"/images/products-3d/{p.slug}.webp" if p.slug in _RENDERED_3D else None,
    )
    for p in _HANDWRITTEN
)


@dataclass(frozen=True)
class UserSeed:
    email: str
    display_name: str
    role: str
    password: str


# Development-only accounts. Seeded only when APP_ENV is dev, test, or ci.
DEV_USERS: tuple[UserSeed, ...] = (
    UserSeed("alice@example.com", "Alice Rivera", "customer", "alice-dev-password"),
    UserSeed("bob@example.com", "Bob Chen", "customer", "bob-dev-password"),
    # A third shopper with different orders, for Xena's customer-support holdout eval.
    UserSeed("dana@example.com", "Dana Brooks", "customer", "dana-dev-password"),
    UserSeed("staff@example.com", "Sam Staff", "staff", "staff-dev-password"),
)
