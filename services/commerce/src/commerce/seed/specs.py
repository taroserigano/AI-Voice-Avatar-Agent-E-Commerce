"""Specification rows for general merchandise, filled in from what each product already says.

Grocery products carry nutrition panels; everything else is compared on its spec table, and a
table with only brand and type gives a shopper (or the assistant) nothing to go on. This fills
in the rows a product's own title, description, tags and options already state, so nothing
here can contradict the listing:

- facts written in the text ("20,000 mAh", "SPF 30", "ages 10+", "12-pack", "400-lumen")
- facts the tags assert (waterproof, Bluetooth, fragrance free, BPA free, ...)
- the options it's sold in (colors, apparel sizes, shades)
- what every product of its type has in common (a sunscreen is a lotion or spray; a tablet
  has a warranty), and a model number for equipment people register or look up.

Rows a product already has always win; a derived row is added only when no row already covers
that fact. Everything is a pure function of the product, so every run gives the same specs.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Iterator
from dataclasses import replace

from commerce.seed.data import ProductSeed
from commerce.seed.spec_notes import DESCRIPTION_SPECS

# Spec rows that already cover a fact under another name: don't add "Charging" when there's
# an "Input" row, or "Power" next to "Battery".
_COVERS: dict[str, tuple[str, ...]] = {
    "Battery life": ("Battery life", "Runtime", "Play time", "Run time", "Flight time"),
    "Capacity": ("Capacity", "Tank", "Reservoir", "Bin capacity", "Cans", "Volume"),
    "Charging": ("Charging", "Input", "Power", "Charging port"),
    "Connection": ("Connection", "Connectivity", "Interface", "Connectors"),
    "Count": ("Count", "Pieces", "Pairs", "Sheets", "Pages", "Bulbs", "Compartments"),
    "Fragrance": ("Fragrance", "Scent"),
    "Pieces": ("Pieces", "Count", "Includes"),
    "Oven safe": ("Oven safe", "Oven safe to"),
    "Power": (
        "Power",
        "Battery",
        "Charging",
        "Batteries",
        "Ports",
        "Fast charging",
        "USB-C",
        "Chemistry",
    ),
    "Size": ("Size", "Sizes", "Dimensions", "Finished size", "Screen size", "Diameter"),
    "Use": ("Use", "For", "Use on", "Surfaces", "Uses"),
    "Water resistance": ("Water resistance", "Waterproof", "Weather rating"),
}

# Words that name a product's form. A type's default "Form" is skipped when the title names a
# different one ("Shampoo Bar" isn't a liquid; "Floss Picks" aren't floss in a dispenser).
_FORM_WORDS = (
    "aerosol", "balm", "bar", "butter", "cream", "foam", "gel", "liquid", "lotion", "mousse",
    "oil", "paste", "picks", "pods", "powder", "roll", "serum", "sheets", "spray", "stick",
    "wipes", "wand",
)  # fmt: skip

# Toys that light up, make sounds or run on batteries don't get "Batteries: None required".
_POWERED = re.compile(r"batter|lights?\b|sounds?\b|electronic|circuit|motor|remote", re.I)

# (row, pattern over title + description, format of the captured value)
_TEXT_FACTS: tuple[tuple[str, str, Callable[[re.Match[str]], str]], ...] = (
    ("Capacity", r"\b(\d{1,3}(?:,\d{3})+|\d{4,6})\s?mAh\b", lambda m: f"{m[1]} mAh"),
    ("SPF", r"\bSPF\s?(\d{2,3})\b", lambda m: m[1]),
    ("Brightness", r"\b(\d{2,5})[- ]lumens?\b", lambda m: f"{m[1]} lumens"),
    (
        "Battery life",
        r"\b(\d{1,3})[- ]hours? (?:of )?(?:battery|playback|play time|runtime)\b",
        lambda m: f"Up to {m[1]} hours",
    ),
    ("Volume limit", r"\b(\d{2,3}) ?dB volume limit\b", lambda m: f"{m[1]} dB"),
    ("Top speed", r"\b(\d{1,2}) mph top speed\b", lambda m: f"{m[1]} mph"),
    ("Burn time", r"\babout (\d{2,3}) hours of burn time\b", lambda m: f"About {m[1]} hours"),
    ("Ages", r"\bages (\d{1,2})\s?(?:\+|and up|and older)", lambda m: f"{m[1]}+"),
    ("Players", r"\b(\d)\s?(?:-|to)\s?(\d{1,2}) players\b", lambda m: f"{m[1]}-{m[2]}"),
    ("Play time", r"\bplays in (?:about )?(\d{2,3}) minutes\b", lambda m: f"About {m[1]} minutes"),
    ("Pieces", r"\b(\d{1,4})[- ]pieces?\b", lambda m: m[1]),
    ("Pieces", r"\bset of (\d{1,3})\b", lambda m: m[1]),
    ("Count", r"\b(\d{1,3})[- ]pack\b", lambda m: m[1]),
    ("Count", r"\b(\d{1,2})[- ]pairs?\b", lambda m: f"{m[1]} pairs"),
)

# Facts a tag asserts: tag -> (row, value).
_TAG_FACTS: dict[str, tuple[str, str]] = {
    "waterproof": ("Water resistance", "Waterproof"),
    "water-resistant": ("Water resistance", "Water-resistant"),
    "bluetooth": ("Connection", "Bluetooth"),
    "noise-cancelling": ("Noise cancelling", "Active"),
    "rechargeable": ("Power", "Rechargeable battery"),
    "cordless": ("Power", "Cordless, rechargeable"),
    "fragrance-free": ("Fragrance", "Fragrance-free"),
    "sulfate-free": ("Sulfates", "None"),
    "aluminum-free": ("Aluminum", "None"),
    "dye-free": ("Dyes", "None"),
    "hypoallergenic": ("Hypoallergenic", "Yes"),
    "sensitive-skin": ("Skin type", "Sensitive"),
    "tear-free": ("Tear-free", "Yes"),
    "cruelty-free": ("Cruelty-free", "Yes"),
    "bpa-free": ("BPA-free", "Yes"),
    "dishwasher-safe": ("Dishwasher safe", "Yes"),
    "oven-safe": ("Oven safe", "Yes"),
    "machine-washable": ("Care", "Machine washable"),
    "moisture-wicking": ("Moisture-wicking", "Yes"),
    "he-compatible": ("Machine type", "HE and standard washers"),
    "biodegradable": ("Biodegradable", "Yes"),
    "recycled-materials": ("Recycled materials", "Yes"),
    "smart-home": ("Smart home", "Works with the app and voice assistants"),
}

# Option attributes worth a row: attribute -> row.
_OPTION_ROWS = {
    "color": "Colors available", "shade": "Shades available", "fits": "Fits", "value": "Amounts",
}  # fmt: skip

# Warranty by product type (then by department). Consumables and soft goods have none.
_WARRANTY_BY_TYPE: dict[str, str] = {
    **dict.fromkeys(
        (
            "skillet", "dutch-oven", "saucepan", "stockpot", "cookware-set", "griddle",
            "kitchen-knife", "knife-set", "flatware",
        ),
        "Limited lifetime",
    ),
    **dict.fromkeys(
        (
            "air-fryer", "air-purifier", "blender", "coffee-maker", "electric-kettle",
            "espresso-machine", "fan", "food-processor", "hand-mixer", "humidifier",
            "pressure-cooker", "rice-cooker", "robot-vacuum", "slow-cooker", "stand-mixer",
            "toaster", "vacuum", "heating-pad", "thermometer", "electric-toothbrush",
            "hair-dryer", "flat-iron", "beard-trimmer", "fitness-tracker", "calculator",
            "label-maker", "desk-lamp", "camp-stove", "grill", "lantern", "headlamp",
            "battery-charger", "bike-light", "drone", "rc-car", "telescope", "microscope",
        ),
        "1-year limited",
    ),
    **dict.fromkeys(("tent", "sleeping-bag", "sleeping-pad", "backpack", "cooler"), "Limited lifetime"),
}  # fmt: skip
_WARRANTY_BY_CATEGORY = {"electronics": "1-year limited"}
_NO_WARRANTY_TYPES = {"printer-ink", "screen-protector", "phone-case", "hdmi-cable", "usb-c-cable"}

# What comes in the box, for equipment where shoppers ask. Keep to things any product of the
# type ships with; product-specific extras belong in the product's own specs.
_IN_THE_BOX: dict[str, str] = {
    "power-bank": "Power bank, USB-C charging cable",
    "bluetooth-speaker": "Speaker, USB-C charging cable",
    "tablet": "Tablet, USB-C cable, power adapter",
    "e-reader": "E-reader, USB-C cable",
    "streaming-device": "Streaming device, voice remote with batteries, power adapter",
    "tv": "TV, stand, remote with batteries, power cord",
    "monitor": "Monitor, stand, power cable, HDMI cable",
    "soundbar": "Soundbar, remote, power cord, HDMI cable",
    "keyboard": "Keyboard, quick-start guide",
    "mouse": "Mouse, quick-start guide",
    "webcam": "Webcam with attached USB cable",
    "security-camera": "Camera, mounting kit",
    "video-doorbell": "Doorbell, mounting kit",
    "smart-thermostat": "Thermostat, wall plate, mounting screws, wire labels",
    "game-controller": "Controller, USB-C cable",
    "printer": "Printer, starter ink or toner, power cord",
    "fitness-tracker": "Tracker, charging cable",
    "electric-toothbrush": "Toothbrush handle, brush head, charger",
    "beard-trimmer": "Trimmer, guide combs, charging cable",
    "hair-dryer": "Hair dryer, attachments",
    "drone": "Drone, controller, battery, spare propellers",
    "rc-car": "Vehicle, remote control, rechargeable battery, charging cable",
}

# Defaults shared by every product of a type (only where the type name alone settles it).
_TYPE_DEFAULTS: dict[str, dict[str, str]] = {
    "bar-soap": {"Form": "Bar"},
    "body-wash": {"Form": "Liquid gel"},
    "body-lotion": {"Form": "Lotion"},
    "baby-lotion": {"Form": "Lotion", "Use": "Daily moisturizing after bath"},
    "baby-oil": {"Form": "Oil", "Use": "Massage and moisturizing"},
    "baby-wash": {"Form": "Liquid"},
    "baby-wipes": {"Use": "Diaper changes, hands, and face"},
    "shampoo": {"Form": "Liquid"},
    "conditioner": {"Form": "Liquid", "Use": "Rinse out after shampoo"},
    "dry-shampoo": {"Form": "Aerosol spray", "Use": "Between washes"},
    "face-wash": {"Use": "Morning and night"},
    "face-serum": {"Form": "Serum"},
    "face-moisturizer": {"Form": "Lotion", "Use": "Daily, morning and night"},
    "eye-cream": {"Form": "Cream", "Use": "Morning and night, under the eyes"},
    "after-sun": {"Form": "Gel", "Use": "After sun exposure"},
    "hand-cream": {"Form": "Cream"},
    "lip-balm": {"Form": "Stick"},
    "lip-color": {"Form": "Bullet lipstick"},
    "mascara": {"Form": "Wand"},
    "foundation": {"Form": "Liquid"},
    "nail-polish": {"Form": "Bottle with brush"},
    "nail-polish-remover": {"Form": "Liquid"},
    "makeup-remover": {"Form": "Pre-moistened wipes"},
    "makeup-sponges": {"Use": "Foundation, concealer, and cream blush", "Care": "Rinse after use"},
    "makeup-brushes": {"Use": "Powder, blush, foundation, and eyeshadow"},
    "shaving-cream": {"Use": "Wet shaving"},
    "razor-cartridges": {"Use": "Replacement cartridges"},
    "toothpaste": {"Form": "Paste"},
    "toothbrush-heads": {"Use": "Replace every 3 months"},
    "mouthwash": {"Form": "Rinse"},
    "dental-floss": {"Form": "Waxed floss in a dispenser"},
    "deodorant": {"Form": "Stick"},
    "hair-styling": {"Use": "Styling damp or dry hair"},
    "nail-care": {"Use": "Manicure and pedicure"},
    "diaper-cream": {"Form": "Cream", "Use": "Treats and prevents diaper rash"},
    "diapers": {"Use": "Day and night"},
    "training-pants": {"Style": "Pull-on"},
    "swim-diapers": {"Style": "Pull-on"},
    "bibs": {"Care": "Wipe clean or machine washable"},
    "bottle-brush": {"Use": "Bottles, nipples, and sippy cups"},
    "pacifier": {"BPA-free": "Yes"},
    "sippy-cup": {"Lid": "Spill-proof"},
    "baby-towel": {"Style": "Hooded"},
    "swaddle": {"Use": "Newborn swaddling and sleep"},
    "baby-bottles": {"BPA-free": "Yes"},
    "all-purpose-cleaner": {"Use": "Kitchen and bathroom surfaces"},
    "bathroom-cleaner": {"Use": "Tubs, tile, sinks, and fixtures"},
    "glass-cleaner": {"Use": "Glass, mirrors, and chrome"},
    "toilet-bowl-cleaner": {"Use": "Toilet bowls"},
    "dish-soap": {"Use": "Hand-washing dishes"},
    "dishwasher-detergent": {"Use": "Automatic dishwashers"},
    "rinse-aid": {"Use": "Automatic dishwashers, for spot-free drying"},
    "laundry-detergent": {"Use": "Machine laundry"},
    "fabric-softener": {"Use": "Add to the rinse cycle"},
    "dryer-sheets": {"Form": "Sheets", "Use": "One sheet per dryer load"},
    "dryer-balls": {"Use": "Reusable in the dryer"},
    "stain-remover": {"Use": "Pretreat before washing"},
    "cleaning-wipes": {"Form": "Pre-moistened wipes"},
    "disinfecting-wipes": {"Form": "Pre-moistened wipes"},
    "sponges": {"Use": "Dishes and countertops"},
    "facial-tissues": {"Form": "Boxed tissues"},
    "paper-towels": {"Form": "Rolls"},
    "toilet-paper": {"Form": "Rolls"},
    "aluminum-foil": {"Material": "Aluminum", "Use": "Cooking, grilling, and wrapping"},
    "plastic-wrap": {"Use": "Covering and wrapping food", "Microwave safe": "Yes, vented"},
    "parchment-paper": {"Form": "Roll", "Use": "Baking and roasting"},
    "food-storage-bags": {"Use": "Food storage"},
    "trash-bags": {"Use": "Kitchen and household trash"},
    "light-bulbs": {"Technology": "LED"},
    "batteries": {"Use": "Remotes, toys, and household devices"},
    "bandages": {"Use": "Minor cuts and scrapes"},
    "gauze": {"Use": "Wound dressing"},
    "medical-tape": {"Use": "Securing gauze and dressings"},
    "elastic-bandage": {"Use": "Sprains and strains", "Reusable": "Yes, washable"},
    "first-aid-kit": {"Use": "Home, car, and travel"},
    "ice-pack": {"Use": "Swelling, sprains, and aches"},
    "pill-organizer": {"Use": "Weekly pills and vitamins"},
    "cat-collar": {"Use": "ID tags and bells"},
    "cat-toy": {"Use": "Solo and interactive play"},
    "cat-scratcher": {"Use": "Scratching and stretching"},
    "dog-collar": {"Use": "Everyday wear and ID tags"},
    "dog-harness": {"Use": "Walks without pulling on the neck"},
    "dog-leash": {"Use": "Daily walks"},
    "dog-toy": {"Use": "Play and chewing"},
    "pet-bed": {"Use": "Sleep and rest"},
    "pet-bowl": {"Use": "Food or water", "Dishwasher safe": "Yes"},
    "litter-box": {"Use": "Indoor cats"},
    "poop-bags": {"Use": "Dog walks"},
    "puppy-pads": {"Use": "House training and indoor accidents"},
    "notebook": {"Use": "School, work, and journaling"},
    "pens": {"Use": "Everyday writing"},
    "pencils": {"Use": "Writing and drawing"},
    "highlighters": {"Ink": "Water-based"},
    "markers": {"Use": "Drawing, coloring, and labeling"},
    "folders": {"Use": "Holding loose papers"},
    "binder": {"Use": "Letter-size papers"},
    "envelopes": {"Use": "Mailing letters and documents"},
    "mailers": {"Use": "Shipping small items"},
    "sticky-notes": {"Adhesive": "Repositionable"},
    "sheet-protectors": {"Use": "3-ring binders"},
    "staples": {"Use": "Standard desktop staplers"},
    "stapler": {"Use": "Home and office documents"},
    "scissors": {"Use": "Paper, crafts, and packages"},
    "labels": {"Use": "Mailing and file labels"},
    "legal-pad": {"Binding": "Top-bound, perforated"},
    "copy-paper": {"Use": "Printers and copiers"},
    "desk-organizer": {"Use": "Desk supplies"},
    "file-organizer": {"Use": "Folders and papers"},
    "pencil-sharpener": {"Use": "Standard wood pencils"},
    "lunch-box": {"Use": "School and work lunches"},
    "action-figure": {"Batteries": "None required"},
    "board-game": {"Batteries": "None required"},
    "card-game": {"Batteries": "None required"},
    "party-game": {"Batteries": "None required"},
    "puzzle": {"Batteries": "None required"},
    "building-blocks": {"Batteries": "None required"},
    "doll": {"Batteries": "None required"},
    "dollhouse": {"Batteries": "None required"},
    "plush-toy": {"Batteries": "None required", "Care": "Surface washable"},
    "crayons": {"Batteries": "None required"},
    "colored-pencils": {"Pre-sharpened": "Yes"},
    "sidewalk-chalk": {"Use": "Outdoor drawing; washes off with water"},
    "paint": {"Use": "Kids' arts and crafts"},
    "modeling-dough": {"Use": "Kids' arts and crafts"},
    "stem-kit": {"Use": "Hands-on science and building"},
    "outdoor-toy": {"Use": "Outdoor play"},
    "baby-toy": {"Use": "Sensory play"},
    "yoga-mat": {"Use": "Yoga, pilates, and floor exercise"},
    "yoga-block": {"Use": "Support and alignment in yoga poses"},
    "yoga-strap": {"Use": "Stretching and yoga"},
    "foam-roller": {"Use": "Muscle recovery"},
    "resistance-bands": {"Use": "Strength training and stretching"},
    "jump-rope": {"Use": "Cardio"},
    "dumbbells": {"Use": "Strength training"},
    "kettlebell": {"Use": "Swings, squats, and strength training"},
    "medicine-ball": {"Use": "Core training and slams"},
    "exercise-ball": {"Use": "Core work, stretching, and seated posture"},
    "football": {"Use": "Backyard and park play"},
    "soccer-ball": {"Use": "Practice and play on grass"},
    "volleyball": {"Use": "Indoor and outdoor play"},
    "tennis-balls": {"Use": "Practice and match play"},
    "tennis-racquet": {"Use": "Recreational play"},
    "pickleball-paddle": {"Use": "Recreational play"},
    "badminton-set": {"Use": "Backyard play"},
    "swim-cap": {"Use": "Lap swimming"},
    "swim-goggles": {"Strap": "Adjustable"},
    "bike-helmet": {"Use": "Cycling and scooters"},
    "bike-lock": {"Use": "Bikes and scooters"},
    "bike": {"Assembly": "Partial assembly required"},
    "balance-bike": {"Pedals": "None (balance bike)"},
    "bird-feeder": {"Use": "Wild birds"},
    "bird-seed": {"Use": "Wild bird feeders"},
    "mulch": {"Use": "Garden beds and landscaping"},
    "soil": {"Form": "Bagged"},
    "seeds": {"Use": "Home gardens"},
    "planter": {"Use": "Indoor or outdoor plants"},
    "garden-gloves": {"Use": "Gardening and yard work"},
    "garden-tools": {"Use": "Gardening and yard work"},
    "hose-nozzle": {"Fits": "Standard garden hoses"},
    "sprinkler": {"Fits": "Standard garden hoses"},
    "grill-accessory": {"Use": "Grilling"},
    "air-mattress": {"Use": "Guests and camping"},
    "patio-chair": {"Use": "Outdoor seating"},
    "patio-set": {"Use": "Outdoor seating"},
    "patio-umbrella": {"Use": "Shade for patio tables"},
    "bath-mat": {"Backing": "Non-slip", "Care": "Machine washable"},
    "bath-towels": {"Care": "Machine washable"},
    "mattress-protector": {"Care": "Machine washable"},
    "pillow": {"Care": "Spot clean or follow the care label"},
    "comforter": {"Care": "Machine washable (large-capacity washer)"},
    "duvet-cover": {"Care": "Machine washable"},
    "weighted-blanket": {"Care": "Removable cover is machine washable"},
    "measuring-cups": {"Use": "Dry and liquid ingredients"},
    "mugs": {"Microwave safe": "Yes", "Dishwasher safe": "Yes"},
    "drinking-glasses": {"Dishwasher safe": "Yes"},
    "cutting-board": {"Use": "Food prep"},
    "kitchen-utensils": {"Use": "Cooking and serving"},
    "knife-sharpener": {"Use": "Straight-edge kitchen knives"},
    "air-purifier-filter": {"Use": "Replacement filter"},
    "storage-bins": {"Use": "Closets, shelves, and garages"},
    "food-storage": {"Use": "Leftovers, meal prep, and lunches"},
    "bakeware": {"Use": "Baking and roasting"},
    "phone-case": {"Wireless charging": "Compatible"},
    "printer-ink": {"Type": "Replacement cartridge"},
    "flash-drive": {"Compatible with": "Windows, macOS, ChromeOS"},
    "memory-card": {"Adapter": "Full-size SD adapter included"},
    "hdmi-cable": {"Connectors": "HDMI to HDMI"},
    "gift-card": {"Format": "Digital, delivered by email", "Returns": "Final sale"},
}

# Clothing: the size row and fabric care everyone asks about.
_APPAREL_SIZES = {"clothing-shoes"}

# Equipment people register or look up by model; soft goods and consumables don't have one.
_MODEL_CATEGORIES = {"electronics"}
_MODEL_TYPES = set(_IN_THE_BOX) | {t for t, w in _WARRANTY_BY_TYPE.items() if w == "1-year limited"}


def _covered(specs: dict[str, str], row: str) -> bool:
    return any(k in specs for k in _COVERS.get(row, (row,)))


def _text_facts(text: str) -> Iterator[tuple[str, str]]:
    for row, pattern, fmt in _TEXT_FACTS:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            yield row, fmt(m)


def _options(p: ProductSeed) -> Iterator[tuple[str, str]]:
    for attr, row in _OPTION_ROWS.items():
        values = list(
            dict.fromkeys(str(v.attributes[attr]) for v in p.variants if attr in v.attributes)
        )
        if len(values) > 1:
            yield row, ", ".join(values)
        elif len(values) == 1 and attr == "color":
            yield "Color", values[0]
    if p.category in _APPAREL_SIZES:
        sizes = list(
            dict.fromkeys(str(v.attributes["size"]) for v in p.variants if "size" in v.attributes)
        )
        if len(sizes) > 1:
            yield "Sizes available", _size_range(sizes)


def _sizes(p: ProductSeed) -> Iterator[tuple[str, str]]:
    """The size or pack it's sold in, from the option names ("12 oz bottle", "24 pods")."""
    if p.category in _APPAREL_SIZES or any(
        a in v.attributes for v in p.variants for a in (*_OPTION_ROWS, "value")
    ):
        return
    names = [v.name for v in p.variants if v.name.lower() not in _PLAIN_NAMES]
    if len(names) == 1 and len(p.variants) == 1:
        yield "Size", names[0]
    elif 1 < len(names) <= 6:
        yield "Sizes available", ", ".join(names)


_PLAIN_NAMES = {"each", "standard", "default", "one size"}


def _restates_count(size: str, specs: dict[str, str]) -> bool:
    """'150 picks' says nothing a 'Count: 150' row doesn't."""
    m = re.match(r"[\d,]+\b", size)
    if m is None:
        return False
    counts = (specs.get(k, "") for k in ("Count", "Pieces"))
    return any(c.split()[:1] == [m[0]] for c in counts if c)


def _names_other_form(title: str, form: str) -> bool:
    words = set(re.findall(r"[a-z]+", title.lower()))
    own = set(re.findall(r"[a-z]+", form.lower()))
    return any(w in words and w not in own for w in _FORM_WORDS)


def _size_range(sizes: list[str]) -> str:
    """'Size 5' ... 'Size 11' -> 'Size 5 to 11'; short lists are written out."""
    if len(sizes) <= 5:
        return ", ".join(sizes)
    first, last = sizes[0], sizes[-1]
    prefix = "Size "
    if first.startswith(prefix) and last.startswith(prefix):
        return f"{first} to {last.removeprefix(prefix)}"
    return f"{first} to {last}"


def _warranty(p: ProductSeed) -> str | None:
    if p.product_type in _NO_WARRANTY_TYPES:
        return None
    return _WARRANTY_BY_TYPE.get(p.product_type) or _WARRANTY_BY_CATEGORY.get(p.category)


def model_number(p: ProductSeed) -> str:
    """A stable, invented model number: brand initials plus four characters of the slug hash."""
    initials = "".join(w[0] for w in re.findall(r"[A-Za-z]+", p.brand))[:3].upper()
    digest = hashlib.sha1(p.slug.encode(), usedforsecurity=False).hexdigest()[:4].upper()
    return f"{initials}-{digest}"


def derived_specs(p: ProductSeed) -> dict[str, str]:
    """The rows :func:`with_specs` would add to ``p`` (never ones it already has)."""
    specs = dict(p.specs)
    added: dict[str, str] = {}

    def add(row: str, value: str | None) -> None:
        if value and not _covered(specs, row):
            specs[row] = added[row] = value

    text = f"{p.title}. {p.description}"
    for row, value in _text_facts(text):
        add(row, value)
    tags = set(p.tags)
    if {"rechargeable", "usb-c"} <= tags:
        add("Power", "Rechargeable battery, USB-C charging")
    for tag, (row, value) in _TAG_FACTS.items():
        if tag in tags:
            add(row, value)
    for row, value in _options(p):
        add(row, value)
    for row, value in _TYPE_DEFAULTS.get(p.product_type, {}).items():
        if row == "Form" and _names_other_form(p.title, value):
            continue
        if row == "Batteries" and _POWERED.search(text):
            continue
        add(row, value)
    for row, value in _sizes(p):
        if not _restates_count(value, specs):
            add(row, value)
    if (box := _IN_THE_BOX.get(p.product_type)) and not _covered(specs, "In the box"):
        add("In the box", box)
    add("Warranty", _warranty(p))
    if p.category in _MODEL_CATEGORIES or p.product_type in _MODEL_TYPES:
        add("Model", model_number(p))
    return added


def with_specs(p: ProductSeed) -> ProductSeed:
    """``p`` with its derived spec rows appended. Food (anything with nutrition) is unchanged."""
    if p.nutrition is not None:
        return p
    notes = DESCRIPTION_SPECS.get(p.slug, {})
    own = replace(p, specs={**p.specs, **{k: v for k, v in notes.items() if k not in p.specs}})
    added = derived_specs(own)
    return replace(own, specs={**own.specs, **added})
