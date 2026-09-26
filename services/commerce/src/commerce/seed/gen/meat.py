"""Meat & Seafood: chicken, beef, pork, turkey, bacon, deli meats, sausage, fish, and
plant-based proteins.

Dense in what shoppers filter on: lean ratio, organic, grass-fed, antibiotic-free,
wild-caught vs farm-raised, sodium, and nitrates. Values are typical raw label values
per 4 oz unless the serving says otherwise.
"""

from __future__ import annotations

from commerce.seed.data import Nutrition, ProductSeed
from commerce.seed.gen.common import REFRIGERATED, STORE_BRAND, Size, cents, food

CAT = "meat-seafood"
PRAIRIE = "Prairie Ridge Meats"  # mainstream beef and pork
BLUESTEM = "Bluestem Ranch"  # grass-fed beef raised in Texas
WILLOW = "Willow Bend Poultry"  # antibiotic-free, air-chilled chicken and turkey
CEDAR = "Cedar Hollow Farms"  # organic
HICKORY = "Hickory Lane Smokehouse"  # bacon, deli, sausage
NORTHCAPE = "Northcape Seafood"
GULFLINE = "Gulfline Seafood"  # wild-caught Texas Gulf seafood
ROOTWELL = "Rootwell Plant Foods"  # plant-based

OZ4 = "4 oz (112 g)"
SEAFOOD = "Keep refrigerated at or below 40°F; cook within 2 days of purchase or freeze."
MEAT_CLAIMS = ("high-protein", "low-fat", "keto")
CURED_CLAIMS = ("low-sodium", "high-protein", "low-fat", "keto")


def N(
    serving: str,
    cal: int,
    fat: float,
    sat: float,
    sodium: int,
    carbs: float,
    fiber: float,
    sugar: float,
    added: float,
    protein: float,
) -> Nutrition:
    return Nutrition(serving, cal, fat, sat, sodium, carbs, fiber, sugar, added, protein)


def S(code: str, label: str, price: float, oz: float | None = None) -> Size:
    return Size(code, label, cents(price), oz)


def M(protein: float, cal: int, fat: float, sat: float, sodium: int = 70) -> Nutrition:
    """Plain raw meat or fish per 4 oz: no carbs or sugar."""
    return N(OZ4, cal, fat, sat, sodium, 0, 0, 0, 0, protein)


def _meat(
    brand: str,
    title: str,
    ptype: str,
    n: Nutrition,
    sizes: list[Size],
    ingredients: str,
    intro: str,
    *,
    allergens: tuple[str, ...] = (),
    tags: list[str] | None = None,
    specs: dict[str, str] | None = None,
    claims: tuple[str, ...] = MEAT_CLAIMS,
    storage: str = REFRIGERATED,
) -> ProductSeed:
    return food(
        category=CAT, product_type=ptype, brand=brand, title=title, sizes=sizes, nutrition=n,
        ingredients=ingredients, allergens=allergens, tags=tags or [], claims=claims,
        specs=specs, intro=intro, storage=storage,
    )  # fmt: skip


def _per_lb(price: float, pack: str) -> list[Size]:
    if pack == "whole":
        return [S("EA", "Whole, about 5 lb", price * 5, 80)]
    if pack == "ground":
        return [S("1LB", "1 lb", price, 16), S("3LB", "3 lb", price * 2.85, 48)]
    return [
        S("2LB", "About 2 lb tray", price * 2, 32),
        S("FP", "Family pack, about 4.5 lb", price * 4.2, 72),
    ]


# --- Chicken --------------------------------------------------------------------------------

CHICKEN = {  # cut: (facts, spec, store price per lb, pack)
    "Boneless Skinless Chicken Breasts": (M(26, 120, 2.5, 0.5), "Boneless skinless breast", 3.49, "tray"),
    "Boneless Skinless Chicken Thighs": (M(21, 170, 9, 2.5, 80), "Boneless skinless thigh", 2.99, "tray"),
    "Bone-In Skin-On Chicken Thighs": (M(19, 240, 18, 5, 85), "Bone-in, skin-on thigh", 1.79, "tray"),
    "Chicken Drumsticks": (M(19, 190, 12, 3.5, 95), "Drumstick", 1.49, "tray"),
    "Chicken Wings": (M(19, 220, 16, 4.5, 90), "Whole wings", 3.99, "tray"),
    "Whole Chicken": (M(19, 210, 15, 4, 75), "Whole bird", 1.69, "whole"),
    "Ground Chicken": (M(20, 170, 10, 3, 75), "Ground (92% lean)", 4.49, "ground"),
}  # fmt: skip


def chicken() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    lines = [  # brand, cuts, price multiple, title prefix, tags, chilling
        (STORE_BRAND, list(CHICKEN), 1.0, "", [], "Water-chilled"),
        (WILLOW, ["Boneless Skinless Chicken Breasts", "Boneless Skinless Chicken Thighs", "Whole Chicken", "Ground Chicken"],
         1.35, "Air-Chilled ", ["antibiotic-free"], "Air-chilled"),
        (CEDAR, ["Boneless Skinless Chicken Breasts", "Boneless Skinless Chicken Thighs", "Whole Chicken"],
         2.1, "Organic Free-Range ", ["organic", "free-range", "antibiotic-free", "non-gmo"], "Air-chilled"),
    ]  # fmt: skip
    for brand, cuts, mult, prefix, tags, chilling in lines:
        for cut in cuts:
            n, spec, price, pack = CHICKEN[cut]
            title = f"{prefix}{cut}"
            organic = "organic" in tags
            raised = (
                "Certified organic chicken raised free-range with outdoor access, fed organic non-GMO feed, never given antibiotics."
                if organic
                else "Raised with no antibiotics ever and air-chilled for better texture."
                if brand == WILLOW
                else "Conventionally raised US chicken with no added solution."
            )
            out.append(_meat(
                brand, title, "chicken" if "Ground" not in cut else "ground-chicken", n, _per_lb(price * mult, pack),
                "Organic chicken." if organic else "Chicken.",
                f"Fresh, never frozen {cut.lower()}. {raised}",
                tags=[*tags, "gluten-free"],
                specs={"Cut": spec, "Chilling": chilling, "Antibiotics": "No antibiotics ever" if tags else "Not specified"},
            ))  # fmt: skip
    return out


# --- Beef -----------------------------------------------------------------------------------

LEAN = {
    "80/20": M(19, 280, 22, 9, 75),
    "85/15": M(21, 240, 17, 7, 75),
    "90/10": M(23, 200, 11, 4.5, 75),
    "93/7": M(23, 170, 8, 3.5, 75),
    "96/4": M(24, 140, 4.5, 2, 75),
}


def beef() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    grinds = [  # brand, ratio, title, price per lb, tags
        (STORE_BRAND, "80/20", "80% Lean / 20% Fat Ground Beef", 4.49, []),
        (STORE_BRAND, "85/15", "85% Lean / 15% Fat Ground Beef", 5.29, []),
        (STORE_BRAND, "90/10", "90% Lean / 10% Fat Ground Beef", 5.99, []),
        (STORE_BRAND, "93/7", "93% Lean / 7% Fat Ground Beef", 6.49, []),
        (PRAIRIE, "80/20", "80% Lean Ground Chuck", 4.99, []),
        (PRAIRIE, "90/10", "90% Lean Ground Sirloin", 6.49, []),
        (PRAIRIE, "96/4", "96% Lean Extra Lean Ground Beef", 7.29, []),
        (BLUESTEM, "85/15", "Grass-Fed 85% Lean Ground Beef", 7.99, ["grass-fed", "antibiotic-free", "local"]),
        (BLUESTEM, "90/10", "Grass-Fed 90% Lean Ground Beef", 8.49, ["grass-fed", "antibiotic-free", "local"]),
        (BLUESTEM, "93/7", "Grass-Fed 93% Lean Ground Beef", 8.99, ["grass-fed", "antibiotic-free", "local"]),
        (CEDAR, "85/15", "Organic Grass-Fed 85% Lean Ground Beef", 9.99, ["organic", "grass-fed", "antibiotic-free"]),
    ]  # fmt: skip
    for brand, ratio, title, price, tags in grinds:
        lean, fat = ratio.split("/")
        where = (
            " From 100% grass-fed cattle raised on Texas ranches, no antibiotics or added hormones." if brand == BLUESTEM
            else " Certified organic and 100% grass-fed." if brand == CEDAR else ""
        )  # fmt: skip
        out.append(_meat(
            brand, title, "ground-beef", LEAN[ratio], _per_lb(price, "ground"),
            "Organic grass-fed beef." if brand == CEDAR else "Grass-fed beef." if brand == BLUESTEM else "Ground beef.",
            f"Fresh ground beef, {lean}% lean and {fat}% fat.{where}",
            tags=[*tags, "gluten-free"], specs={"Lean ratio": ratio, "Grade": "USDA inspected"},
        ))  # fmt: skip
    steaks = {  # cut: (facts, price per lb)
        "Ribeye Steak": (M(20, 280, 22, 9, 60), 14.99),
        "New York Strip Steak": (M(23, 230, 15, 6, 60), 12.99),
        "Top Sirloin Steak": (M(25, 160, 6, 2.5, 60), 8.99),
        "Filet Mignon": (M(23, 180, 9, 3.5, 55), 21.99),
        "Flank Steak": (M(24, 170, 7, 3, 60), 10.99),
    }
    for cut, (n, price) in steaks.items():
        out.append(_meat(
            PRAIRIE, f"USDA Choice {cut}", "steak", n, [S("1LB", "About 1 lb (2 steaks)", price, 16)], "Beef.",
            f"USDA Choice {cut.lower()}, well marbled and ready for the grill or cast iron.",
            tags=["gluten-free"], specs={"Cut": cut, "Grade": "USDA Choice", "Feed": "Grain-finished"},
        ))  # fmt: skip
    for cut in ("Ribeye Steak", "Top Sirloin Steak"):
        n, price = steaks[cut]
        out.append(_meat(
            BLUESTEM, f"Grass-Fed {cut}", "steak", n, [S("1LB", "About 1 lb (2 steaks)", price * 1.3, 16)], "Grass-fed beef.",
            f"100% grass-fed and grass-finished {cut.lower()} from cattle raised on Texas ranches. Leaner than grain-finished beef.",
            tags=["grass-fed", "antibiotic-free", "local", "gluten-free"], specs={"Cut": cut, "Feed": "100% grass-fed"},
        ))  # fmt: skip
    out.append(_meat(
        PRAIRIE, "Beef Chuck Roast", "beef-roast", M(21, 210, 14, 5.5), [S("3LB", "About 3 lb", 6.99 * 3, 48)], "Beef.",
        "Boneless beef chuck roast for pot roast and slow cooking.", tags=["gluten-free"], specs={"Cut": "Chuck roast", "Grade": "USDA Choice"},
    ))  # fmt: skip
    out.append(_meat(
        BLUESTEM, "Texas Grass-Fed Beef Brisket Flat", "beef-roast", M(19, 250, 19, 7), [S("3LB", "About 3 lb", 8.99 * 3, 48)], "Grass-fed beef.",
        "Grass-fed brisket flat from Texas ranches, trimmed and ready for low-and-slow smoking.",
        tags=["grass-fed", "antibiotic-free", "local", "gluten-free"], specs={"Cut": "Brisket flat", "Feed": "100% grass-fed"},
    ))  # fmt: skip
    return out


# --- Pork and turkey --------------------------------------------------------------------------


def pork_turkey() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    pork = [  # brand, title, facts, price per lb, cut
        (PRAIRIE, "Boneless Pork Loin Chops", M(23, 140, 5, 1.5, 50), 3.99, "Boneless loin chop"),
        (PRAIRIE, "Pork Tenderloin", M(24, 120, 3, 1, 55), 4.49, "Tenderloin"),
        (PRAIRIE, "Bone-In Pork Shoulder Butt Roast", M(19, 200, 14, 5), 2.29, "Shoulder (Boston butt)"),
        (PRAIRIE, "Pork Baby Back Ribs", M(18, 290, 24, 8, 85), 4.99, "Baby back ribs"),
        (PRAIRIE, "Ground Pork", M(18, 290, 24, 9), 3.99, "Ground"),
        (STORE_BRAND, "Boneless Pork Loin Chops", M(23, 140, 5, 1.5, 50), 3.49, "Boneless loin chop"),
    ]  # fmt: skip
    for brand, title, n, price, cut in pork:
        out.append(_meat(
            brand, title, "pork", n, _per_lb(price, "ground" if cut == "Ground" else "tray"), "Pork.",
            f"Fresh {title.lower()} with no added solution.", tags=["gluten-free"], specs={"Cut": cut},
        ))  # fmt: skip
    turkey = [  # brand, ratio, facts, price per lb, tags
        (WILLOW, "85/15", M(19, 230, 17, 4.5, 95), 4.49, ["antibiotic-free"]),
        (WILLOW, "93/7", M(22, 170, 9, 2.5, 80), 5.49, ["antibiotic-free"]),
        (WILLOW, "99/1", M(28, 120, 1.5, 0.5, 55), 6.99, ["antibiotic-free"]),
        (STORE_BRAND, "93/7", M(22, 170, 9, 2.5, 80), 4.79, []),
        (STORE_BRAND, "99/1", M(28, 120, 1.5, 0.5, 55), 5.99, []),
        (CEDAR, "93/7", M(22, 170, 9, 2.5, 80), 7.99, ["organic", "antibiotic-free", "free-range"]),
    ]  # fmt: skip
    for brand, ratio, n, price, tags in turkey:
        lean = ratio.split("/")[0]
        if ratio == "99/1":
            title = "99% Fat Free Ground Turkey Breast"
        else:
            title = f"{lean}% Lean / {100 - int(lean)}% Fat Ground Turkey"
        if "organic" in tags:
            title = f"Organic {title}"
        out.append(_meat(
            brand, title, "ground-turkey", n, _per_lb(price, "ground"),
            "Organic turkey." if "organic" in tags else "Turkey breast." if ratio == "99/1" else "Turkey.",
            f"Fresh ground turkey, {lean}% lean.{' All white breast meat.' if ratio == '99/1' else ''}",
            tags=[*tags, "gluten-free"], specs={"Lean ratio": ratio},
        ))  # fmt: skip
    return out


# --- Bacon, deli, sausage ---------------------------------------------------------------------

CURED = "sodium phosphate, sodium erythorbate, sodium nitrite"
NITRITE = "Contains sodium nitrite"
UNCURED = "No nitrates or nitrites added except those naturally occurring in celery powder"


def bacon() -> list[ProductSeed]:
    s2 = "2 pan-fried slices (15 g)"
    rows = [  # brand, title, facts, ingredients, price, size, cure, tags, intro
        (STORE_BRAND, "Hickory Smoked Bacon", N(s2, 80, 6, 2, 290, 0, 0, 0, 0, 6),
         f"Pork cured with water, salt, sugar, smoke flavoring, {CURED}.", [S("12OZ", "12 oz", 4.99, 12), S("24OZ", "24 oz", 9.49, 24)],
         NITRITE, [], "Classic hickory smoked, regular-cut bacon."),
        (STORE_BRAND, "Low Sodium Center Cut Bacon", N("2 pan-fried slices (12 g)", 60, 4.5, 1.5, 135, 0, 0, 0, 0, 5),
         f"Pork cured with water, potassium lactate, salt, sugar, smoke flavoring, {CURED}.", [S("12OZ", "12 oz", 5.99, 12)],
         NITRITE, [], "Leaner center cut bacon with 135 mg sodium per serving, less than half the sodium of our regular bacon."),
        (HICKORY, "Thick Cut Applewood Smoked Bacon", N("1 pan-fried slice (15 g)", 80, 6, 2.5, 300, 0, 0, 0, 0, 6),
         f"Pork cured with water, salt, sugar, natural applewood smoke, {CURED}.", [S("24OZ", "24 oz", 11.99, 24), S("1LB", "1 lb", 7.99, 16)],
         NITRITE, [], "Thick-cut bacon slow smoked over applewood."),
        (HICKORY, "Uncured Applewood Smoked Bacon", N(s2, 80, 6, 2.5, 270, 0, 0, 0, 0, 6),
         "Pork, water, sea salt, cane sugar, celery powder, cherry powder.", [S("12OZ", "12 oz", 6.99, 12)],
         UNCURED, [], "Uncured applewood smoked bacon with no nitrates or nitrites added (except those naturally occurring in celery powder)."),
        (HICKORY, "Lower Sodium Hickory Smoked Bacon", N(s2, 80, 6, 2, 190, 0, 0, 0, 0, 6),
         f"Pork cured with water, salt, potassium lactate, sugar, smoke flavoring, {CURED}.", [S("12OZ", "12 oz", 6.49, 12)],
         NITRITE, [], "Hickory smoked bacon with 35% less sodium than regular bacon (190 mg vs 290 mg per 2 slices). Lower sodium, but not a low sodium food."),
        (WILLOW, "Turkey Bacon", N("1 pan-fried slice (14 g)", 30, 2, 0.5, 170, 0, 0, 0, 0, 2.5),
         f"Turkey cured with water, salt, sugar, canola oil, smoke flavor, {CURED}.", [S("12OZ", "12 oz", 4.49, 12)],
         NITRITE, ["antibiotic-free"], "Smoked turkey bacon with about 60% less fat than pork bacon."),
        (CEDAR, "Organic Uncured Hickory Smoked Bacon", N(s2, 80, 6, 2.5, 280, 0, 0, 0, 0, 6),
         "Organic pork, water, sea salt, organic cane sugar, organic celery powder.", [S("8OZ", "8 oz", 7.99, 8)],
         UNCURED, ["organic"], "Organic uncured bacon from humanely raised pigs, with no nitrates or nitrites added except those naturally occurring in celery powder."),
    ]  # fmt: skip
    return [
        _meat(brand, title, "bacon", n, sizes, ing, intro, tags=[*tags, "gluten-free"],
              specs={"Cure": cure, "Nitrates": "Contains sodium nitrite" if cure == NITRITE else "No nitrates or nitrites added*"},
              claims=("low-sodium", "keto"))
        for brand, title, n, ing, sizes, cure, tags, intro in rows
    ]  # fmt: skip


def deli() -> list[ProductSeed]:
    oz2 = "2 oz (56 g)"
    rows = [  # brand, title, facts, ingredients, price, cure, tags, intro
        (HICKORY, "Oven Roasted Turkey Breast", N(oz2, 60, 1, 0, 500, 1, 0, 1, 1, 12),
         "Turkey breast, water, salt, cane sugar, sodium phosphate, natural flavor.", 5.49, "Not cured", [],
         "Thin-sliced oven roasted turkey breast."),
        (HICKORY, "No Salt Added Oven Roasted Turkey Breast", N(oz2, 60, 1, 0, 55, 0, 0, 0, 0, 13),
         "Turkey breast, water, natural flavor.", 5.99, "Not cured", ["no-salt-added"],
         "Oven roasted turkey breast with no salt added, just 55 mg of naturally occurring sodium per serving."),
        (HICKORY, "Honey Ham", N(oz2, 60, 1.5, 0.5, 560, 3, 0, 3, 3, 9),
         f"Ham cured with water, honey, salt, sugar, {CURED}.", 5.49, NITRITE, [],
         "Sweet honey-cured sliced ham."),
        (HICKORY, "Black Forest Ham", N(oz2, 60, 1.5, 0.5, 520, 1, 0, 1, 1, 10),
         f"Ham cured with water, salt, sugar, smoke flavoring, {CURED}, caramel color.", 5.49, NITRITE, [],
         "Smoked Black Forest ham, sliced thin."),
        (HICKORY, "Lower Sodium Black Forest Ham", N(oz2, 60, 1.5, 0.5, 340, 1, 0, 1, 1, 10),
         f"Ham cured with water, potassium lactate, salt, sugar, smoke flavoring, {CURED}.", 5.79, NITRITE, [],
         "Black Forest ham with 35% less sodium than our regular Black Forest ham. Lower sodium, but not low sodium."),
        (HICKORY, "Top Round Roast Beef", N(oz2, 70, 2, 1, 350, 0, 0, 0, 0, 12),
         "Beef, water, salt, sodium phosphate, natural flavor.", 7.49, "Not cured", [],
         "Medium-rare seasoned top round roast beef, sliced thin."),
        (HICKORY, "Genoa Salami", N("1 oz (28 g)", 110, 9, 3.5, 480, 0, 0, 0, 0, 6),
         "Pork, salt, dextrose, spices, garlic, lactic acid starter culture, sodium nitrite.", 4.99, NITRITE, [],
         "Dry-cured Genoa salami with garlic and black pepper."),
        (STORE_BRAND, "Smoked Turkey Breast", N(oz2, 60, 1, 0, 540, 1, 0, 1, 1, 11),
         "Turkey breast, water, salt, sugar, sodium phosphate, smoke flavoring.", 3.99, "Not cured", [],
         "Hickory smoked sliced turkey breast."),
        (STORE_BRAND, "Sliced Pepperoni", N("1 oz (28 g)", 140, 13, 5, 490, 0, 0, 0, 0, 5),
         "Pork, beef, salt, spices, dextrose, lactic acid starter culture, paprika, sodium nitrite.", 3.49, NITRITE, [],
         "Sliced pepperoni for pizza and snacking."),
        (CEDAR, "Organic Uncured Oven Roasted Turkey Breast", N(oz2, 50, 1, 0, 380, 0, 0, 0, 0, 10),
         "Organic turkey breast, water, sea salt, organic cultured celery powder, organic vinegar.", 6.99, UNCURED, ["organic"],
         "Organic sliced turkey breast with no nitrates or nitrites added except those naturally occurring in celery powder."),
        (CEDAR, "Organic Uncured Black Forest Ham", N(oz2, 60, 2, 0.5, 450, 1, 0, 1, 1, 10),
         "Organic pork, water, sea salt, organic cane sugar, organic celery powder.", 6.99, UNCURED, ["organic"],
         "Organic uncured Black Forest ham with no nitrates or nitrites added except those naturally occurring in celery powder."),
    ]  # fmt: skip
    return [
        _meat(brand, title, "deli-meat", n, [S("8OZ", "8 oz package", price, 8)], ing, intro,
              tags=[*tags, "gluten-free"],
              specs={"Nitrates": "Contains sodium nitrite" if cure == NITRITE else "No nitrates or nitrites added*" if cure == UNCURED else "No nitrites added",
                     "Sliced": "Thin sliced"},
              claims=CURED_CLAIMS)
        for brand, title, n, ing, price, cure, tags, intro in rows
    ]  # fmt: skip


def sausage() -> list[ProductSeed]:
    rows = [  # brand, title, type, facts, ingredients, size, tags, intro
        (HICKORY, "Smoked Pork Sausage", "sausage", N("2 oz (56 g)", 180, 16, 6, 540, 2, 0, 1, 1, 7),
         "Pork, water, corn syrup, salt, spices, dextrose, monosodium glutamate, sodium erythorbate, sodium nitrite.",
         S("14OZ", "14 oz rope", 3.99, 14), [], "Fully cooked smoked pork sausage rope."),
        (HICKORY, "Hill Country Style Beef Smoked Sausage", "sausage", N("2 oz (56 g)", 190, 17, 7, 560, 1, 0, 0, 0, 8),
         "Beef, water, salt, black pepper, garlic, paprika, sodium erythorbate, sodium nitrite, in a beef collagen casing.",
         S("12OZ", "12 oz", 5.49, 12), [], "Coarse-ground, oak-smoked all-beef sausage in the Texas Hill Country style."),
        (HICKORY, "Original Pork Breakfast Sausage Links", "sausage", N("3 links (57 g)", 190, 17, 6, 390, 1, 0, 0, 0, 8),
         "Pork, water, salt, spices, sage, natural flavors.", S("12OZ", "12 oz (about 16 links)", 4.49, 12), [], "Fresh pork breakfast sausage links seasoned with sage."),
        (STORE_BRAND, "Mild Italian Pork Sausage Links", "sausage", N("1 link (76 g)", 220, 18, 6, 600, 1, 0, 0, 0, 14),
         "Pork, water, salt, spices, paprika, garlic powder, natural flavors, in a pork casing.", S("19OZ", "19 oz (5 links)", 4.49, 19), [],
         "Fresh, uncooked mild Italian sausage links."),
        (WILLOW, "Chicken Apple Sausage", "sausage", N("1 link (85 g)", 140, 7, 2, 480, 5, 0, 4, 2, 14),
         "Chicken, dried apples, apple juice concentrate, sea salt, spices, in a pork casing.", S("12OZ", "12 oz (4 links)", 5.99, 12),
         ["antibiotic-free"], "Fully cooked chicken sausage with sweet apple."),
        (HICKORY, "Beef Franks", "hot-dogs", N("1 frank (45 g)", 150, 14, 6, 480, 1, 0, 0, 0, 5),
         "Beef, water, salt, corn syrup, dextrose, spices, sodium phosphate, sodium erythorbate, sodium nitrite.",
         S("8CT", "8 franks (14 oz)", 4.99, 14), [], "Classic all-beef hot dogs."),
        (CEDAR, "Organic Uncured Beef Hot Dogs", "hot-dogs", N("1 frank (45 g)", 110, 9, 3.5, 350, 0, 0, 0, 0, 7),
         "Organic grass-fed beef, water, sea salt, organic spices, organic celery powder.", S("8CT", "8 franks (10 oz)", 6.99, 10),
         ["organic", "grass-fed"], "Organic grass-fed beef hot dogs with no nitrates or nitrites added except those naturally occurring in celery powder."),
    ]  # fmt: skip
    return [
        _meat(brand, title, ptype, n, [size], ing, intro, tags=[*tags, "gluten-free"], claims=CURED_CLAIMS,
              specs={"Nitrates": "No nitrates or nitrites added*" if "celery" in ing else "Contains sodium nitrite" if "nitrite" in ing else "No nitrites added"})
        for brand, title, ptype, n, ing, size, tags, intro in rows
    ]  # fmt: skip


# --- Seafood ----------------------------------------------------------------------------------


def seafood() -> list[ProductSeed]:
    rows = [  # brand, title, type, facts, ingredients, allergens, price per lb, source, origin, tags, intro
        (NORTHCAPE, "Wild-Caught Sockeye Salmon Fillets", "salmon", M(24, 150, 6, 1, 85), "Sockeye salmon.", ("fish",), 13.99,
         "Wild-caught", "Alaska, USA", ["wild-caught"], "Deep red wild-caught Alaska sockeye salmon, skin on. Leaner than farm-raised salmon."),
        (NORTHCAPE, "Wild-Caught Coho Salmon Fillets", "salmon", M(23, 140, 5, 1, 55), "Coho salmon.", ("fish",), 11.99,
         "Wild-caught", "Alaska, USA", ["wild-caught"], "Mild wild-caught Alaska coho salmon fillets, skin on."),
        (NORTHCAPE, "Farm-Raised Atlantic Salmon Fillets", "salmon", M(23, 230, 15, 3), "Atlantic salmon (color added via feed).", ("fish",), 10.99,
         "Farm-raised", "Norway", [], "Rich, buttery farm-raised Atlantic salmon fillets. Not wild-caught."),
        (STORE_BRAND, "Farm-Raised Atlantic Salmon Fillet", "salmon", M(23, 230, 15, 3), "Atlantic salmon (color added via feed).", ("fish",), 8.99,
         "Farm-raised", "Chile", [], "Farm-raised Atlantic salmon fillet, previously frozen. Not wild-caught."),
        (NORTHCAPE, "Wild-Caught Smoked Sockeye Salmon", "salmon", N("2 oz (56 g)", 70, 2.5, 0.5, 600, 0, 0, 0, 0, 12), "Sockeye salmon, salt, natural hardwood smoke.",
         ("fish",), 17.99, "Wild-caught", "Alaska, USA", ["wild-caught"], "Cold-smoked wild sockeye salmon, thinly sliced. Ready to eat."),
        (GULFLINE, "Wild-Caught Texas Gulf Shrimp, Peeled & Deveined", "shrimp", M(20, 90, 1, 0, 135), "Shrimp.", ("shellfish",), 13.99,
         "Wild-caught", "Gulf of Mexico, Texas", ["wild-caught", "local"], "Sweet wild-caught Texas Gulf brown shrimp, 26-30 per pound, with no added phosphates or salt."),
        (STORE_BRAND, "Farm-Raised Raw Shrimp, Peeled & Deveined", "shrimp", M(18, 80, 0.5, 0, 560), "Shrimp, water, salt, sodium tripolyphosphate (to retain moisture).",
         ("shellfish",), 8.99, "Farm-raised", "Thailand", [], "Farm-raised raw shrimp, 31-40 per pound, treated with salt and sodium tripolyphosphate, so higher in sodium."),
        (GULFLINE, "Wild-Caught Gulf Red Snapper Fillets", "fish", M(23, 110, 1.5, 0.5), "Red snapper.", ("fish",), 16.99,
         "Wild-caught", "Gulf of Mexico, Texas", ["wild-caught", "local"], "Mild, flaky wild-caught red snapper landed on the Texas coast."),
        (STORE_BRAND, "Farm-Raised Tilapia Fillets", "fish", M(23, 110, 2, 0.5, 50), "Tilapia.", ("fish",), 5.99,
         "Farm-raised", "Colombia", [], "Mild, boneless farm-raised tilapia fillets."),
        (NORTHCAPE, "Wild-Caught Pacific Cod Fillets", "fish", M(20, 90, 1, 0), "Pacific cod.", ("fish",), 10.99,
         "Wild-caught", "Alaska, USA", ["wild-caught"], "Flaky white wild-caught Pacific cod fillets."),
        (NORTHCAPE, "Wild-Caught Yellowfin Tuna Steaks", "fish", M(27, 120, 0.5, 0, 50), "Yellowfin tuna.", ("fish",), 15.99,
         "Wild-caught", "Pacific Ocean", ["wild-caught"], "Sushi-grade wild-caught yellowfin tuna steaks for searing."),
        (NORTHCAPE, "Wild-Caught Sea Scallops", "scallops", N(OZ4, 90, 0.5, 0, 330, 4, 0, 0, 0, 16), "Sea scallops.", ("shellfish",), 19.99,
         "Wild-caught", "Atlantic Ocean, USA", ["wild-caught"], "Large dry-packed wild-caught sea scallops."),
    ]  # fmt: skip
    return [
        _meat(brand, title, ptype, n, [S("1LB", "1 lb", price, 16)] if "Smoked" not in title else [S("4OZ", "4 oz", price * 0.45, 4)],
              ing, intro, allergens=allergens, tags=[*tags, "gluten-free"],
              specs={"Source": source, "Origin": origin}, claims=("high-protein", "low-fat", "low-sodium"),
              storage=SEAFOOD)
        for brand, title, ptype, n, ing, allergens, price, source, origin, tags, intro in rows
    ]  # fmt: skip


def plant_based() -> list[ProductSeed]:
    vegan = ["vegan", "plant-based", "dairy-free", "non-gmo"]
    rows = [  # title, type, facts, ingredients, allergens, sizes, extra tags, form, intro
        ("Plant-Based Burger Patties", "plant-based-meat", N("1 patty (113 g)", 230, 14, 5, 370, 7, 3, 0, 0, 20),
         "Water, pea protein, expeller-pressed canola oil, refined coconut oil, rice protein, natural flavors, methylcellulose, potato starch, "
         "apple extract, salt, beet juice extract (for color).", (), [S("2PK", "2 x 4 oz patties", 5.99, 8), S("4PK", "4 x 4 oz patties", 10.49, 16)],
         ["gluten-free"], "Burger patties", "Juicy pea-protein burger patties that cook like beef. Soy free and gluten free."),
        ("Plant-Based Ground", "plant-based-meat", N("4 oz (113 g)", 230, 14, 5, 390, 7, 3, 0, 0, 19),
         "Water, pea protein, expeller-pressed canola oil, refined coconut oil, rice protein, natural flavors, methylcellulose, potato starch, salt, "
         "beet juice extract (for color).", (), [S("16OZ", "16 oz", 7.99, 16)], ["gluten-free"], "Ground",
         "Pea-protein ground for tacos, pasta sauce, and meatballs."),
        ("Plant-Based Italian Sausage", "plant-based-meat", N("1 link (76 g)", 190, 12, 4, 500, 5, 3, 0, 0, 15),
         "Water, pea protein, coconut oil, rice protein, spices, fennel, garlic, salt, methylcellulose, alginate casing.", (),
         [S("14OZ", "14 oz (4 links)", 6.99, 14)], ["gluten-free"], "Sausage links", "Fennel-spiced plant-based Italian sausage links."),
        ("Seasoned Seitan Strips", "plant-based-meat", N("3 oz (85 g)", 120, 2, 0, 440, 6, 1, 1, 0, 21),
         "Wheat gluten, water, soy sauce (water, soybeans, wheat, salt), garlic, onion, spices.", ("wheat", "soy"),
         [S("8OZ", "8 oz", 4.49, 8)], [], "Strips", "High-protein seitan strips made from wheat gluten. Vegan, but NOT gluten free."),
        ("Organic Extra Firm Tofu", "tofu", N("3 oz (85 g)", 80, 4.5, 0.5, 10, 2, 1, 0, 0, 9),
         "Water, organic soybeans, calcium sulfate, magnesium chloride (nigari).", ("soy",), [S("14OZ", "14 oz block", 2.49, 14)],
         ["organic", "gluten-free"], "Block", "Organic extra firm tofu for stir-fries and baking. Press before cooking."),
    ]  # fmt: skip
    return [
        _meat(ROOTWELL, title, ptype, n, sizes, ing, intro, allergens=allergens, tags=[*vegan, *extra],
              specs={"Form": form, "Protein source": "Soy" if "soy" in allergens and "wheat" not in allergens else "Wheat gluten" if "wheat" in allergens else "Pea"},
              claims=("high-protein", "low-sodium", "keto"))
        for title, ptype, n, ing, allergens, sizes, extra, form, intro in rows
    ]  # fmt: skip


def products() -> list[ProductSeed]:
    return [
        *chicken(),
        *beef(),
        *pork_turkey(),
        *bacon(),
        *deli(),
        *sausage(),
        *seafood(),
        *plant_based(),
    ]


__all__ = ["products"]
