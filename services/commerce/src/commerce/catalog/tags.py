"""The controlled vocabulary of product tags: dietary facts, sourcing claims, and features.

Tags are what let a shopper (or the assistant) ask for "organic fat-free milk, not whole
milk" as exact filters instead of hoping keywords line up. Every seeded tag must be listed
here, and the food tags have fixed meanings that the seed data is tested against
(``tests/unit/test_catalog_data.py``). Amounts are per labeled serving.
"""

from __future__ import annotations

# slug -> label shown to shoppers
TAGS: dict[str, str] = {
    # Diet and nutrition (food)
    "organic": "Organic",
    "non-gmo": "Non-GMO",
    "whole-milk": "Whole milk",  # full-fat dairy
    "reduced-fat": "Reduced fat",  # e.g. 2% milk
    "low-fat": "Low fat",  # 3 g fat or less
    "fat-free": "Fat free",  # under 0.5 g fat (nonfat, skim)
    "sugar-free": "Sugar free",  # under 0.5 g total sugars
    "no-added-sugar": "No added sugar",  # 0 g added sugars
    "low-sugar": "Low sugar",  # 6 g total sugars or less
    "unsweetened": "Unsweetened",  # 0 g added sugars and no sweeteners
    "zero-calorie": "Zero calorie",  # under 5 calories
    "lactose-free": "Lactose free",  # may still contain milk protein
    "dairy-free": "Dairy free",  # no milk ingredients at all
    "gluten-free": "Gluten free",
    "vegan": "Vegan",
    "plant-based": "Plant based",
    "high-protein": "High protein",  # 10 g protein or more
    "high-fiber": "High fiber",  # 5 g fiber or more
    "keto": "Keto friendly",  # 5 g net carbs or less
    "low-sodium": "Low sodium",  # 140 mg sodium or less
    "no-salt-added": "No salt added",
    "whole-grain": "Whole grain",
    "caffeine-free": "Caffeine free",
    "decaf": "Decaf",
    "kosher": "Kosher",
    "nut-free": "Nut free",
    "grain-free": "Grain free",
    # Sourcing
    "grass-fed": "Grass fed",
    "cage-free": "Cage free",
    "free-range": "Free range",
    "pasture-raised": "Pasture raised",
    "wild-caught": "Wild caught",
    "antibiotic-free": "No antibiotics ever",
    "fair-trade": "Fair trade",
    "local": "Texas grown",
    # Personal care and household
    "fragrance-free": "Fragrance free",
    "hypoallergenic": "Hypoallergenic",
    "sensitive-skin": "For sensitive skin",
    "cruelty-free": "Cruelty free",
    "sulfate-free": "Sulfate free",
    "aluminum-free": "Aluminum free",
    "he-compatible": "HE compatible",
    "biodegradable": "Biodegradable",
    "recycled-materials": "Made with recycled materials",
    "tear-free": "Tear free",
    "dye-free": "Dye free",
    "limited-ingredient": "Limited ingredient",
    # Products
    "bpa-free": "BPA free",
    "dishwasher-safe": "Dishwasher safe",
    "oven-safe": "Oven safe",
    "cordless": "Cordless",
    "machine-washable": "Machine washable",
    "moisture-wicking": "Moisture wicking",
    "waterproof": "Waterproof",
    "water-resistant": "Water resistant",
    "wireless": "Wireless",
    "bluetooth": "Bluetooth",
    "noise-cancelling": "Noise cancelling",
    "rechargeable": "Rechargeable",
    "usb-c": "USB-C",
    "energy-efficient": "Energy efficient",
    "smart-home": "Smart home",
    "kids": "For kids",
}


def tag_label(slug: str) -> str:
    return TAGS.get(slug, slug.replace("-", " ").capitalize())
