"""Baby: diapers, training pants, wipes, bath and skin care, bottles, pacifiers, feeding, and
baby food. No infant formula.

Diapers come in size variants (Newborn, 1-6) with the count for each size in the label.
Baby food uses nutrition facts so "no added sugar" and allergen questions are checkable.
"""

from __future__ import annotations

from collections.abc import Iterable

from commerce.seed.data import Nutrition, ProductSeed
from commerce.seed.gen.common import PANTRY, Size, cents, food, item, options, slugify

CAT = "baby"
SNUGGLEBEE = "Snugglebee"  # mainstream
LITTLE_FERN = "Little Fern"  # sensitive, plant-based, premium
OWN_BRAND = "Serigan Mart Baby"  # store brand, value
SPROUT = "Sprout & Spoon"  # organic baby food

GENTLE = ["hypoallergenic", "fragrance-free", "sensitive-skin"]
POUCH_STORAGE = "Store at room temperature. Refrigerate after opening and use within 24 hours."

# size code -> (label, weight range)
DIAPER_SIZES = {
    "NB": ("Newborn", "up to 10 lb"),
    "S1": ("Size 1", "8-14 lb"),
    "S2": ("Size 2", "12-18 lb"),
    "S3": ("Size 3", "16-28 lb"),
    "S4": ("Size 4", "22-37 lb"),
    "S5": ("Size 5", "27+ lb"),
    "S6": ("Size 6", "35+ lb"),
}
# diapers per pack by size, for a "big pack"
BIG_PACK = {"NB": 76, "S1": 92, "S2": 84, "S3": 78, "S4": 68, "S5": 60, "S6": 52}


def N(serving: str, cal: int, fat: float, sat: float, sodium: int, carbs: float, fiber: float,
      sugar: float, added: float, protein: float) -> Nutrition:  # fmt: skip
    return Nutrition(serving, cal, fat, sat, sodium, carbs, fiber, sugar, added, protein)


def one(dollars: float, label: str = "Each", code: str = "EA") -> list[Size]:
    return [Size(code, label, cents(dollars))]


def sz(*rows: tuple[str, str, float]) -> list[Size]:
    return [Size(code, label, cents(price)) for code, label, price in rows]


def diaper_sizes(
    price: float, codes: Iterable[str] = DIAPER_SIZES, scale: float = 1.0
) -> list[Size]:
    """One variant per diaper size; the count shrinks as the size grows at the same pack price."""
    out = []
    for code in codes:
        name, weight = DIAPER_SIZES[code]
        count = round(BIG_PACK[code] * scale)
        out.append(Size(code, f"{name} ({weight}), {count} diapers", cents(price)))
    return out


def P(
    brand: str,
    product_type: str,
    title: str,
    description: str,
    sizes: list[Size],
    tags: Iterable[str] = (),
    specs: dict[str, str] | None = None,
) -> ProductSeed:
    return item(
        category=CAT, product_type=product_type, brand=brand, title=title,
        description=description, sizes=sizes, tags=tags, specs=specs,
    )  # fmt: skip


def with_options(
    brand: str,
    product_type: str,
    title: str,
    description: str,
    names: list[str],
    dollars: float,
    attribute: str,
    tags: Iterable[str] = (),
    specs: dict[str, str] | None = None,
) -> ProductSeed:
    slug = slugify(brand, title)
    return item(
        category=CAT, product_type=product_type, brand=brand, title=title,
        description=description, variants_=options(CAT, slug, names, cents(dollars), attribute),
        tags=tags, specs=specs, slug=slug,
    )  # fmt: skip


# fmt: off
def diapering() -> list[ProductSeed]:
    training = ["2T-3T", "3T-4T", "4T-5T"]
    return [
        P(SNUGGLEBEE, "diapers", "Comfort Dry Diapers",
          "Soft, absorbent disposable diapers with up to 12 hours of leak protection, a wetness indicator, and an aloe lotion liner.",
          diaper_sizes(26.99), [],
          {"Wetness indicator": "Yes", "Lotion": "Aloe lotion liner", "Protection": "Up to 12 hours"}),
        P(SNUGGLEBEE, "diapers", "Overnight Diapers",
          "Extra-absorbent overnight diapers with a double leak guard for up to 12 hours of dry sleep. Sizes 3 to 6.",
          diaper_sizes(29.99, ("S3", "S4", "S5", "S6"), 0.8), [],
          {"Wetness indicator": "No", "Lotion": "None", "Protection": "Overnight, up to 12 hours"}),
        P(LITTLE_FERN, "diapers", "Sensitive Skin Diapers, Fragrance-Free",
          "Hypoallergenic diapers made with plant-based materials and no fragrance, lotion, latex, or chlorine bleaching. Dermatologist tested for sensitive skin.",
          diaper_sizes(34.99, scale=0.9), [*GENTLE, "dye-free"],
          {"Wetness indicator": "Yes", "Lotion": "None", "Fragrance": "None", "Chlorine": "Totally chlorine-free processing", "Latex": "Latex free"}),
        P(OWN_BRAND, "diapers", "Everyday Diapers",
          "Value disposable diapers with a wetness indicator and stretchy sides. Hypoallergenic and fragrance free.",
          diaper_sizes(19.99), ["hypoallergenic", "fragrance-free"],
          {"Wetness indicator": "Yes", "Lotion": "None", "Fragrance": "None"}),
        P(SNUGGLEBEE, "swim-diapers", "Little Splashers Swim Diapers",
          "Disposable swim diapers that hold in solids without swelling in the pool. Tear-away sides for easy changes.",
          sz(("SM", "Small (16-26 lb), 12 diapers", 10.99), ("MD", "Medium (24-34 lb), 11 diapers", 10.99), ("LG", "Large (32+ lb), 10 diapers", 10.99)),
          [], {"Use": "Swimming only (not absorbent)"}),
        P(SNUGGLEBEE, "training-pants", "Easy-Up Training Pants",
          "Pull-on potty training pants with stretchy sides, fading graphics that show when they are wet, and tear-away seams.",
          [Size(s.replace("-", ""), f"{s}, {n} pants", cents(14.99)) for s, n in zip(training, (26, 23, 20), strict=True)],
          [], {"Wetness graphics": "Yes", "Fragrance": "None"}),
        P(LITTLE_FERN, "training-pants", "Sensitive Training Pants, Fragrance-Free",
          "Plant-based pull-on training pants with no fragrance, lotion, or chlorine bleaching. Hypoallergenic.",
          [Size(s.replace("-", ""), f"{s}, {n} pants", cents(17.99)) for s, n in zip(training, (24, 22, 20), strict=True)],
          [*GENTLE], {"Wetness graphics": "No", "Fragrance": "None"}),
        P(OWN_BRAND, "training-pants", "Training Pants",
          "Value pull-on training pants with easy tear-away sides for potty training.",
          [Size(s.replace("-", ""), f"{s}, {n} pants", cents(11.99)) for s, n in zip(training, (26, 23, 20), strict=True)],
          ["fragrance-free"], {"Wetness graphics": "No", "Fragrance": "None"}),
        P(SNUGGLEBEE, "training-pants", "Nighttime Youth Pants",
          "Absorbent pull-on underwear for nighttime bedwetting in older kids, discreet under pajamas.",
          sz(("SM", "Small/Medium (38-65 lb), 14 pants", 13.99), ("LX", "Large/XL (60-125 lb), 11 pants", 13.99)),
          [], {"Use": "Overnight"}),
        # Wipes
        P(SNUGGLEBEE, "baby-wipes", "Fresh Scent Baby Wipes",
          "Thick, soft baby wipes with a light fresh scent for diaper changes and sticky hands.",
          sz(("3PK", "3 packs of 72 (216 wipes)", 6.99), ("9PK", "9 packs of 72 (648 wipes)", 17.99)),
          [], {"Scent": "Fresh", "Alcohol": "Alcohol free"}),
        P(SNUGGLEBEE, "baby-wipes", "Sensitive Baby Wipes, Unscented",
          "Unscented baby wipes for sensitive skin with no fragrance, alcohol, or parabens. Hypoallergenic.",
          sz(("3PK", "3 packs of 72 (216 wipes)", 6.99), ("9PK", "9 packs of 72 (648 wipes)", 17.99)),
          [*GENTLE], {"Scent": "Unscented", "Alcohol": "Alcohol free"}),
        P(LITTLE_FERN, "baby-wipes", "99% Water Baby Wipes, Fragrance-Free",
          "Baby wipes made of 99% purified water and a drop of fruit extract on plant-based fibers. Fragrance free, hypoallergenic, and gentle enough for newborns.",
          sz(("4PK", "4 packs of 60 (240 wipes)", 11.99), ("12PK", "12 packs of 60 (720 wipes)", 31.99)),
          [*GENTLE, "plant-based", "biodegradable"], {"Scent": "Unscented", "Ingredients": "99% water, fruit extract", "Fiber": "Plant-based"}),
        P(OWN_BRAND, "baby-wipes", "Fragrance-Free Baby Wipes",
          "Value baby wipes with no fragrance or alcohol for sensitive skin.",
          sz(("3PK", "3 packs of 80 (240 wipes)", 4.99), ("8PK", "8 packs of 80 (640 wipes)", 12.99)),
          [*GENTLE], {"Scent": "Unscented", "Alcohol": "Alcohol free"}),
        P(OWN_BRAND, "baby-wipes", "Baby Wipes, Cucumber & Aloe",
          "Value baby wipes with aloe and a light cucumber scent.",
          sz(("3PK", "3 packs of 80 (240 wipes)", 4.99)),
          [], {"Scent": "Cucumber", "Alcohol": "Alcohol free"}),
    ]


def bath_and_skin() -> list[ProductSeed]:
    return [
        P(SNUGGLEBEE, "baby-wash", "Tear-Free Baby Wash & Shampoo, Lavender",
          "Tear-free 2-in-1 baby wash and shampoo with a calming lavender scent for bedtime baths.",
          sz(("16OZ", "16 fl oz", 7.99)), ["tear-free"], {"Scent": "Lavender", "Use": "Hair and body"}),
        P(LITTLE_FERN, "baby-wash", "Tear-Free Baby Wash & Shampoo, Fragrance-Free",
          "Tear-free, sulfate-free 2-in-1 wash with oat and no fragrance, dyes, or parabens. Hypoallergenic and pediatrician tested for sensitive skin.",
          sz(("12OZ", "12 fl oz", 10.99)), ["tear-free", "sulfate-free", "cruelty-free", "vegan", *GENTLE],
          {"Scent": "Unscented", "Use": "Hair and body"}),
        P(OWN_BRAND, "baby-wash", "Tear-Free Baby Shampoo",
          "Value tear-free baby shampoo that is as gentle to eyes as pure water.",
          sz(("15OZ", "15 fl oz", 3.99)), ["tear-free"], {"Scent": "Classic baby", "Use": "Hair"}),
        P(SNUGGLEBEE, "baby-lotion", "Daily Moisture Baby Lotion",
          "Lightweight daily baby lotion with a light classic baby scent that absorbs quickly.",
          sz(("16OZ", "16 fl oz", 6.99)), [], {"Scent": "Classic baby"}),
        P(LITTLE_FERN, "baby-lotion", "Fragrance-Free Baby Lotion with Colloidal Oat",
          "Rich baby lotion with oat and shea butter and no fragrance, dyes, or parabens. Hypoallergenic for dry, sensitive skin.",
          sz(("12OZ", "12 fl oz", 10.99)), ["cruelty-free", *GENTLE], {"Scent": "Unscented"}),
        P(OWN_BRAND, "baby-lotion", "Baby Lotion, Fragrance-Free",
          "Value fragrance-free baby lotion for daily moisture.",
          sz(("15OZ", "15 fl oz", 4.49)), ["fragrance-free", "hypoallergenic"], {"Scent": "Unscented"}),
        P(OWN_BRAND, "baby-oil", "Pure Baby Oil",
          "Mineral oil baby oil for massage and dry skin, with a light baby scent.",
          sz(("14OZ", "14 fl oz", 3.99)), [], {"Scent": "Classic baby"}),
        P(SNUGGLEBEE, "diaper-cream", "Maximum Strength Diaper Rash Cream, 40% Zinc Oxide",
          "Thick paste with 40% zinc oxide that treats and prevents diaper rash and seals out wetness.",
          sz(("4OZ", "4 oz tube", 8.99)), [], {"Zinc oxide": "40%", "Strength": "Maximum"}),
        P(LITTLE_FERN, "diaper-cream", "Daily Diaper Cream, 10% Zinc Oxide, Fragrance-Free",
          "Everyday diaper cream with 10% zinc oxide and calendula that wipes on and off easily. No fragrance or dyes.",
          sz(("3OZ", "3 oz tube", 9.99)), ["cruelty-free", *GENTLE], {"Zinc oxide": "10%", "Strength": "Daily"}),
        P(OWN_BRAND, "diaper-cream", "Baby Healing Ointment",
          "Petrolatum ointment that protects chapped skin, cheeks, and diaper areas. Fragrance free.",
          sz(("7OZ", "7 oz jar", 7.99)), ["fragrance-free"], {"Zinc oxide": "None (petrolatum based)"}),
    ]


def feeding_and_gear() -> list[ProductSeed]:
    return [
        P(LITTLE_FERN, "baby-bottles", "Anti-Colic Baby Bottles, 3-Pack",
          "Vented anti-colic baby bottles that reduce air intake, with slow-flow nipples. BPA free and top-rack dishwasher safe.",
          sz(("5OZ", "5 oz, 3-pack (slow flow)", 19.99), ("9OZ", "9 oz, 3-pack (medium flow)", 22.99)),
          ["bpa-free", "dishwasher-safe"], {"Material": "BPA-free polypropylene", "Anti-colic": "Yes", "Nipple": "Silicone"}),
        P(SNUGGLEBEE, "baby-bottles", "Glass Baby Bottles, 8 oz, 4-Pack",
          "Tempered glass baby bottles with silicone sleeves and slow-flow nipples. Dishwasher and sterilizer safe.",
          sz(("4PK", "4 bottles", 24.99)),
          ["bpa-free", "dishwasher-safe"], {"Material": "Tempered glass", "Anti-colic": "No", "Nipple": "Silicone"}),
        P(OWN_BRAND, "baby-bottles", "Baby Bottles, 9 oz, 3-Pack",
          "Value BPA-free baby bottles with medium-flow nipples. Top-rack dishwasher safe.",
          sz(("3PK", "3 bottles", 9.99)),
          ["bpa-free", "dishwasher-safe"], {"Material": "BPA-free polypropylene", "Anti-colic": "No", "Nipple": "Silicone"}),
        P(LITTLE_FERN, "baby-bottles", "Silicone Baby Bottle, 8 oz",
          "Squeezable, unbreakable medical-grade silicone bottle with a wide neck for easy cleaning. BPA free and dishwasher safe.",
          sz(("8OZ", "8 oz bottle", 16.99)),
          ["bpa-free", "dishwasher-safe"], {"Material": "Medical-grade silicone", "Anti-colic": "Yes"}),
        P(OWN_BRAND, "bottle-brush", "Bottle Brush Set with Nipple Cleaner",
          "Bottle brush with a built-in nipple cleaner and drying stand.",
          one(6.99), ["bpa-free"], {"Material": "BPA-free plastic, nylon bristles"}),
        with_options(SNUGGLEBEE, "pacifier", "Orthodontic Pacifiers, 2-Pack",
                     "Orthodontic pacifiers with a symmetrical silicone nipple and a ventilated shield. BPA free.",
                     ["0-6 months", "6-18 months"], 6.99, "age", ["bpa-free"], {"Material": "Silicone nipple, polypropylene shield"}),
        with_options(LITTLE_FERN, "pacifier", "One-Piece Silicone Pacifiers, 2-Pack",
                     "One-piece pacifiers made of food-grade silicone with no seams where germs can hide. BPA free and dishwasher safe.",
                     ["0-6 months", "6-18 months"], 9.99, "age", ["bpa-free", "dishwasher-safe"], {"Material": "Food-grade silicone"}),
        P(SNUGGLEBEE, "sippy-cup", "Spill-Proof Sippy Cups, 9 oz, 2-Pack",
          "Spill-proof sippy cups with soft spouts and easy-grip handles for ages 6 months and up. BPA free and top-rack dishwasher safe.",
          sz(("2PK", "2 cups", 7.99)), ["bpa-free", "dishwasher-safe"], {"Age": "6 months+", "Capacity": "9 oz"}),
        P(OWN_BRAND, "bibs", "Waterproof Silicone Bibs, 2-Pack",
          "Soft silicone bibs with a food-catching pocket that wipe clean. BPA free and dishwasher safe.",
          sz(("2PK", "2 bibs", 9.99)), ["bpa-free", "dishwasher-safe", "waterproof"], {"Material": "Silicone"}),
        P(LITTLE_FERN, "swaddle", "Organic Cotton Muslin Swaddle Blankets, 3-Pack",
          "Breathable 47 x 47 in organic cotton muslin swaddles that get softer with each wash. Machine washable.",
          sz(("3PK", "3 blankets", 29.99)), ["organic", "machine-washable"], {"Material": "100% organic cotton muslin", "Size": "47 x 47 in"}),
        P(OWN_BRAND, "baby-towel", "Hooded Baby Towels, 2-Pack",
          "Soft cotton terry hooded towels for after bath time. Machine washable.",
          sz(("2PK", "2 towels", 12.99)), ["machine-washable"], {"Material": "100% cotton terry", "Size": "30 x 30 in"}),
    ]


def baby_food() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    pouch = "1 pouch (113 g)"
    # (title, nutrition, ingredients)
    pouches = [
        ("Organic Baby Food Pouch, Apple, Banana & Spinach", N(pouch, 70, 0, 0, 10, 16, 2, 11, 0, 1), "Organic apples, organic bananas, organic spinach, lemon juice concentrate."),
        ("Organic Baby Food Pouch, Pear, Mango & Kale", N(pouch, 70, 0, 0, 5, 17, 2, 12, 0, 1), "Organic pears, organic mangoes, organic kale, lemon juice concentrate."),
        ("Organic Baby Food Pouch, Sweet Potato, Carrot & Apple", N(pouch, 60, 0, 0, 25, 14, 2, 8, 0, 1), "Organic sweet potatoes, organic carrots, organic apples, lemon juice concentrate."),
        ("Organic Baby Food Pouch, Butternut Squash & Pear", N(pouch, 60, 0, 0, 5, 15, 2, 9, 0, 1), "Organic butternut squash, organic pears, lemon juice concentrate."),
        ("Organic Baby Food Pouch, Blueberry, Banana & Oat", N(pouch, 90, 0.5, 0, 5, 19, 2, 10, 0, 2), "Organic bananas, organic blueberries, organic apples, organic whole grain oats, lemon juice concentrate."),
    ]  # fmt: skip
    for title, n, ing in pouches:
        out.append(food(
            category=CAT, product_type="baby-food", brand=SPROUT, title=title,
            sizes=sz(("1PK", "1 pouch (4 oz)", 1.79), ("6PK", "6 pouches (4 oz each)", 9.99)),
            nutrition=n, ingredients=ing,
            tags=["organic", "vegan", "non-gmo"], claims=("no-added-sugar", "fat-free", "low-sodium"),
            specs={"Stage": "Stage 2 (6+ months)", "Texture": "Smooth puree", "Package": "BPA-free pouch"},
            intro=f"{title.removeprefix('Organic Baby Food Pouch, ')} puree made with organic fruits and vegetables and nothing else: no added sugar, salt, or juice concentrates for sweetness.",
            storage=POUCH_STORAGE,
        ))
    out.append(food(
        category=CAT, product_type="baby-food", brand=SPROUT, title="Organic Toddler Pouch, Whole Milk Greek Yogurt & Mixed Berry",
        sizes=sz(("1PK", "1 pouch (3.5 oz)", 1.99), ("6PK", "6 pouches (3.5 oz each)", 10.99)),
        nutrition=N("1 pouch (99 g)", 90, 2.5, 1.5, 35, 14, 1, 10, 0, 3),
        ingredients="Organic whole milk Greek yogurt, organic bananas, organic strawberries, organic blueberries, lemon juice concentrate.",
        allergens=["milk"], tags=["organic", "whole-milk", "gluten-free"], claims=("no-added-sugar", "low-sodium"),
        specs={"Stage": "Toddler (12+ months)", "Texture": "Smooth puree", "Package": "BPA-free pouch"},
        intro="Whole milk Greek yogurt blended with organic bananas and berries for toddlers. No added sugar. Shelf stable until opened.",
        storage=POUCH_STORAGE,
    ))
    jars = [  # (title, nutrition, ingredients, stage)
        ("Stage 1 Baby Food, Carrots", N("1 tub (57 g)", 20, 0, 0, 40, 5, 1, 3, 0, 0), "Carrots, water.", "Stage 1 (4+ months)"),
        ("Stage 1 Baby Food, Sweet Peas", N("1 tub (57 g)", 35, 0, 0, 0, 6, 2, 2, 0, 2), "Peas, water.", "Stage 1 (4+ months)"),
        ("Stage 1 Baby Food, Bananas", N("1 tub (57 g)", 50, 0, 0, 0, 13, 1, 8, 0, 1), "Bananas, ascorbic acid (vitamin C).", "Stage 1 (4+ months)"),
        ("Stage 2 Baby Food, Apple & Chicken", N("1 tub (113 g)", 80, 1.5, 0.5, 30, 12, 1, 7, 0, 5), "Water, apples, chicken, rice flour.", "Stage 2 (6+ months)"),
    ]  # fmt: skip
    for title, n, ing, stage in jars:
        big = "Stage 2" in title
        out.append(food(
            category=CAT, product_type="baby-food", brand=OWN_BRAND, title=title,
            sizes=sz(("2PK", f"2 tubs ({'4' if big else '2'} oz each)", 1.99 if big else 1.49)),
            nutrition=n, ingredients=ing, tags=["gluten-free", "non-gmo"],
            claims=("no-added-sugar", "fat-free", "low-sodium"),
            specs={"Stage": stage, "Texture": "Smooth puree", "Package": "BPA-free plastic tubs"},
            intro=f"Simple {title.split(', ')[1].lower()} puree for babies, with no added sugar or salt. Not organic.",
            storage=POUCH_STORAGE,
        ))
    snacks = [  # (brand, title, nutrition, ingredients, allergens, tags, stage, price, label)
        (SPROUT, "Organic Veggie Puffs, Sweet Potato & Carrot", N("1/4 cup (7 g)", 25, 0, 0, 5, 6, 0, 0, 0, 0),
         "Organic brown rice flour, organic sorghum flour, organic sweet potato powder, organic carrot powder, tocopherols.",
         (), ["organic", "gluten-free", "vegan", "non-gmo"], "Crawler (8+ months)", 3.99, "1.5 oz canister"),
        (SPROUT, "Organic Whole Grain Puffs, Banana", N("1/4 cup (7 g)", 25, 0, 0, 0, 6, 0, 0, 0, 0),
         "Organic whole wheat flour, organic brown rice flour, organic banana puree powder, tocopherols.",
         ("wheat",), ["organic", "whole-grain", "vegan"], "Crawler (8+ months)", 3.99, "1.5 oz canister"),
        (SPROUT, "Organic Yogurt Melts, Mixed Berry", N("1/4 cup (7 g)", 30, 0.5, 0.5, 10, 5, 0, 3, 1, 1),
         "Organic yogurt (organic cultured nonfat milk), organic tapioca starch, organic cane sugar, organic strawberry and blueberry powder, live cultures.",
         ("milk",), ["organic", "gluten-free"], "Crawler (8+ months)", 3.79, "1 oz bag"),
        (SPROUT, "Organic Teething Wafers, Apple", N("2 wafers (4 g)", 15, 0, 0, 0, 3, 0, 0, 0, 0),
         "Organic jasmine rice flour, organic apple juice powder, organic sweet potato powder.",
         (), ["organic", "gluten-free", "vegan", "non-gmo"], "Sitter (6+ months)", 3.99, "12 packs of 2 wafers"),
        (OWN_BRAND, "Teething Biscuits", N("1 biscuit (11 g)", 45, 1, 0, 25, 8, 0, 2, 2, 1),
         "Wheat flour, sugar, palm oil, whole wheat flour, baking soda, thiamine, iron.",
         ("wheat",), [], "Crawler (8+ months)", 2.99, "24 biscuits"),
    ]  # fmt: skip
    for brand, title, n, ing, allergens, tags, stage, price, label in snacks:
        out.append(food(
            category=CAT, product_type="baby-snacks", brand=brand, title=title,
            sizes=[Size("PK", label, cents(price))], nutrition=n, ingredients=ing,
            allergens=allergens, tags=tags, claims=("sugar-free", "no-added-sugar", "low-sodium"),
            specs={"Stage": stage, "Texture": "Dissolves easily"},
            intro=f"{title}: a finger food for babies learning to self-feed that melts in the mouth.",
            storage=PANTRY,
        ))
    return out
# fmt: on


def products() -> list[ProductSeed]:
    return [*diapering(), *bath_and_skin(), *feeding_and_gear(), *baby_food()]
