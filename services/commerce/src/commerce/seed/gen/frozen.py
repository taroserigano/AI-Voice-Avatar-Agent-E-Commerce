"""Frozen: ice cream and frozen desserts, frozen vegetables and fruit, frozen meals, pizza,
waffles, breakfast sandwiches, seafood, chicken nuggets, and potatoes.

Contrasting pairs on purpose: regular vs light vs no-sugar-added vs dairy-free ice cream,
plain (no salt added) vs sauced vegetables, unsweetened vs sugared fruit, and classic vs
high-protein, low-sodium, keto, vegan, and gluten-free meals and pizza.
"""

from __future__ import annotations

from commerce.seed.data import Nutrition, ProductSeed
from commerce.seed.gen.common import FROZEN, STORE_BRAND, Size, cents, food

CAT = "frozen"
MOONLIT = "Moonlit Creamery"  # premium ice cream
FROSTLINE = "Frostline"  # light and no-sugar-added frozen desserts
SILVERLEAF = "Silverleaf"  # almond milk (also in dairy)
ROLLING = "Rolling Acre Oat Co."  # oat milk (also in dairy)
PALMGROVE = "Palmgrove"  # coconut (also in dairy)
KALOS = "Kalos Greek Yogurt Co."  # (also in dairy)
EVERGREEN = "Evergreen Valley"  # frozen vegetables
CEDAR = "Cedar Hollow Farms"  # organic
HEARTHSIDE = "Hearthside Kitchen"  # classic frozen meals
LEAN = "Lean Table"  # high protein, low sodium, keto meals
HARVEST = "Harvest Bowl Co."  # organic, vegan, gluten-free bowls
BRICKYARD = "Brickyard Pizza Co."
VEGGIECRUST = "Veggiecrust Kitchen"  # cauliflower crust, gluten free
SUNUP = "Sunup Kitchen"  # breakfast
NORTHCAPE = "Northcape Seafood"
WILLOW = "Willow Bend Poultry"
ROOTWELL = "Rootwell Plant Foods"
RUSSET = "Russet Ridge"  # frozen potatoes

C23 = "2/3 cup (90 g)"
DESSERT_CLAIMS = ("fat-free", "low-fat", "sugar-free", "no-added-sugar", "low-sugar")
VEG_CLAIMS = ("low-sodium", "keto", "high-fiber")
MEAL_CLAIMS = ("high-protein", "low-sodium", "keto", "high-fiber")


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


def _frz(
    brand: str,
    title: str,
    ptype: str,
    n: Nutrition,
    sizes: list[Size],
    ingredients: str,
    intro: str,
    *,
    allergens: tuple[str, ...] = (),
    tags: tuple[str, ...] | list[str] = (),
    specs: dict[str, str] | None = None,
    claims: tuple[str, ...] = (),
) -> ProductSeed:
    organic = title.startswith("Organic")
    return food(
        category=CAT, product_type=ptype, brand=brand, title=title, sizes=sizes, nutrition=n,
        ingredients=ingredients, allergens=allergens, tags=[*(["organic"] if organic else []), *tags],
        claims=claims, specs=specs, intro=intro, storage=FROZEN,
    )  # fmt: skip


# --- Ice cream and frozen desserts ---------------------------------------------------------------

# flavor: (facts, flavor ingredients, extra allergens)
PREMIUM = {
    "Vanilla Bean": (N(C23, 280, 17, 11, 70, 27, 0, 25, 21, 5), "vanilla extract, ground vanilla beans", ()),
    "Dark Chocolate": (N(C23, 300, 17, 11, 75, 32, 2, 28, 24, 5), "cocoa (processed with alkali)", ()),
    "Strawberry": (N(C23, 260, 15, 9, 60, 28, 0, 26, 22, 4), "strawberries, lemon juice", ()),
    "Mint Chocolate Chip": (N(C23, 300, 18, 12, 70, 31, 1, 28, 25, 4), "chocolate chips (sugar, chocolate, cocoa butter, soy lecithin), peppermint extract", ("soy",)),
    "Cookies & Cream": (N(C23, 300, 17, 10, 120, 34, 1, 27, 23, 5), "chocolate sandwich cookies (wheat flour, sugar, cocoa, palm oil, soy lecithin, salt)", ("wheat", "soy")),
    "Butter Pecan": (N(C23, 310, 21, 11, 120, 26, 0, 23, 20, 5), "pecans roasted in butter, salt", ("tree nuts",)),
    "Coffee": (N(C23, 270, 16, 10, 70, 27, 0, 25, 21, 5), "coffee extract", ()),
    "Salted Caramel": (N(C23, 300, 16, 10, 190, 35, 0, 32, 28, 4), "caramel (sugar, cream, butter, salt), sea salt", ()),
    "Chocolate Chip Cookie Dough": (N(C23, 310, 17, 10, 110, 36, 0, 28, 25, 4), "cookie dough (wheat flour, brown sugar, butter, chocolate chips, soy lecithin, salt)", ("wheat", "soy")),
    "Rocky Road": (N(C23, 310, 18, 10, 80, 34, 1, 28, 24, 5), "cocoa, almonds, marshmallows (corn syrup, sugar, gelatin)", ("tree nuts",)),
}  # fmt: skip
STORE_FLAVORS = (
    "Vanilla Bean",
    "Dark Chocolate",
    "Strawberry",
    "Cookies & Cream",
    "Butter Pecan",
    "Mint Chocolate Chip",
)
LIGHT = {  # flavor: extra ingredient, extra allergens
    "Vanilla Bean": ("vanilla extract, vanilla bean specks", ()),
    "Chocolate": ("cocoa (processed with alkali)", ()),
    "Birthday Cake": ("cake pieces (wheat flour, sugar, palm oil, soy lecithin), sprinkles", ("wheat", "soy")),
    "Peanut Butter Cup": ("peanut butter swirl (peanuts, salt), chocolate pieces (sugar, chocolate, soy lecithin)", ("peanuts", "soy")),
    "Sea Salt Caramel": ("caramel swirl (sugar, milk, butter), sea salt", ()),
    "Mint Chip": ("chocolate chips (sugar, chocolate, soy lecithin), peppermint extract", ("soy",)),
    "Cookies & Cream": ("chocolate cookie pieces (wheat flour, sugar, cocoa, palm oil, soy lecithin)", ("wheat", "soy")),
}  # fmt: skip


def ice_cream() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    for flavor, (n, flav_ing, extra) in PREMIUM.items():
        out.append(_frz(
            MOONLIT, f"{flavor} Ice Cream", "ice-cream", n, [S("PT", "1 pint (16 fl oz)", 5.49, 16)],
            f"Cream, skim milk, cane sugar, egg yolks, {flav_ing}.",
            f"Super-premium {flavor.lower()} ice cream made with cream and egg yolks. Full fat and full sugar.",
            allergens=("milk", "egg", *extra), specs={"Flavor": flavor, "Style": "Premium ice cream", "Base": "Dairy"},
            claims=DESSERT_CLAIMS,
        ))  # fmt: skip
    for flavor in STORE_FLAVORS:
        pn, flav_ing, extra = PREMIUM[flavor]
        n = N(C23, round(pn.calories * 0.7), round(pn.total_fat_g * 0.6), round(pn.saturated_fat_g * 0.6), pn.sodium_mg,
              pn.total_carbs_g - 4, pn.fiber_g, pn.total_sugars_g - 5, pn.added_sugars_g - 5, 3)  # fmt: skip
        name = flavor.replace("Vanilla Bean", "Vanilla").replace("Dark Chocolate", "Chocolate")
        out.append(_frz(
            STORE_BRAND, f"{name} Ice Cream", "ice-cream", n, [S("48OZ", "1.5 quarts (48 fl oz)", 3.99, 48)],
            f"Milk, cream, sugar, corn syrup, whey, {flav_ing}, mono and diglycerides, guar gum, carrageenan.",
            f"Classic {name.lower()} ice cream in a family-size carton.",
            allergens=("milk", *extra), specs={"Flavor": name, "Style": "Regular ice cream", "Base": "Dairy"},
            claims=DESSERT_CLAIMS,
        ))  # fmt: skip
    light = N(C23, 100, 2.5, 1.5, 110, 20, 4, 6, 4, 6)
    for flavor, (flav_ing, extra) in LIGHT.items():
        out.append(_frz(
            FROSTLINE, f"Light {flavor} Ice Cream", "ice-cream", light, [S("PT", "1 pint (16 fl oz)", 4.99, 16)],
            f"Skim milk, eggs, erythritol, milk protein concentrate, prebiotic fiber, cane sugar, {flav_ing}, vegetable glycerin, "
            "sea salt, carob gum, guar gum, stevia leaf extract.",
            f"Light {flavor.lower()} ice cream: 100 calories and 6 g sugar per serving, with 75% less fat than regular ice cream. "
            "Sweetened partly with erythritol and stevia.",
            allergens=("milk", "egg", *extra), tags=("reduced-fat",),
            specs={"Flavor": flavor, "Style": "Light ice cream", "Base": "Dairy"}, claims=DESSERT_CLAIMS,
        ))  # fmt: skip
    nsa = {
        "Vanilla": ("natural vanilla flavor", (), N(C23, 120, 5, 3, 70, 17, 4, 4, 0, 3)),
        "Chocolate": ("cocoa (processed with alkali)", (), N(C23, 130, 5, 3, 80, 19, 5, 4, 0, 3)),
        "Butter Pecan": (
            "pecans, butter, salt",
            ("tree nuts",),
            N(C23, 140, 7, 3, 110, 17, 4, 4, 0, 3),
        ),
        "Neapolitan": (
            "cocoa, strawberry puree, natural vanilla flavor",
            (),
            N(C23, 120, 5, 3, 75, 18, 4, 4, 0, 3),
        ),
    }
    for flavor, (flav_ing, extra, n) in nsa.items():
        out.append(_frz(
            STORE_BRAND, f"No Sugar Added {flavor} Ice Cream", "ice-cream", n, [S("48OZ", "1.5 quarts (48 fl oz)", 4.49, 48)],
            f"Milk, cream, polydextrose, maltodextrin, sorbitol, whey protein concentrate, {flav_ing}, mono and diglycerides, "
            "guar gum, sucralose, acesulfame potassium.",
            f"Reduced fat {flavor.lower()} ice cream with no sugar added, sweetened with sucralose. It still has about 4 g of "
            "naturally occurring milk sugar per serving, so it is not sugar free.",
            allergens=("milk", *extra), tags=("reduced-fat",),
            specs={"Flavor": flavor, "Style": "No sugar added ice cream", "Base": "Dairy"}, claims=DESSERT_CLAIMS,
        ))  # fmt: skip
    plant = [  # brand, base, flavor, facts, base ingredient, allergens, extra ingredient
        (SILVERLEAF, "Almondmilk", "Vanilla", N(C23, 220, 12, 1.5, 80, 26, 2, 18, 18, 3), "almondmilk (filtered water, almonds)", ("tree nuts",), "vanilla extract"),
        (SILVERLEAF, "Almondmilk", "Chocolate", N(C23, 230, 13, 2, 90, 27, 3, 19, 19, 3), "almondmilk (filtered water, almonds)", ("tree nuts",), "cocoa"),
        (SILVERLEAF, "Almondmilk", "Mint Chip", N(C23, 240, 14, 3, 80, 27, 2, 20, 20, 3), "almondmilk (filtered water, almonds)", ("tree nuts",), "dark chocolate chips (cocoa, sugar, cocoa butter), peppermint oil"),
        (SILVERLEAF, "Almondmilk", "Salted Caramel", N(C23, 240, 12, 1.5, 150, 30, 2, 23, 23, 3), "almondmilk (filtered water, almonds)", ("tree nuts",), "caramel (sugar, coconut cream), sea salt"),
        (ROLLING, "Oatmilk", "Vanilla", N(C23, 230, 11, 7, 60, 30, 1, 22, 20, 2), "oatmilk (water, oats)", (), "vanilla extract"),
        (ROLLING, "Oatmilk", "Chocolate", N(C23, 240, 11, 7, 70, 32, 2, 23, 21, 2), "oatmilk (water, oats)", (), "cocoa"),
        (ROLLING, "Oatmilk", "Strawberry", N(C23, 220, 10, 7, 55, 30, 1, 23, 20, 2), "oatmilk (water, oats)", (), "strawberries"),
        (PALMGROVE, "Coconut Milk", "Vanilla Bean", N(C23, 250, 15, 13, 40, 26, 1, 21, 20, 1), "coconut milk (water, coconut cream)", (), "vanilla extract, vanilla bean specks"),
        (PALMGROVE, "Coconut Milk", "Chocolate", N(C23, 260, 16, 14, 40, 27, 2, 21, 20, 1), "coconut milk (water, coconut cream)", (), "cocoa (processed with alkali)"),
    ]  # fmt: skip
    for brand, base, flavor, n, base_ing, allergens, flav_ing in plant:
        out.append(_frz(
            brand, f"{flavor} {base} Frozen Dessert", "ice-cream", n, [S("PT", "1 pint (16 fl oz)", 5.99, 16)],
            f"{base_ing[0].upper()}{base_ing[1:]}, cane sugar, coconut oil, pea protein, tapioca starch, {flav_ing}, sunflower lecithin, locust bean gum, guar gum.",
            f"Dairy-free, vegan {flavor.lower()} frozen dessert made with {base.lower()} instead of cream. Contains no milk.",
            allergens=allergens, tags=("dairy-free", "lactose-free", "vegan", "plant-based"),
            specs={"Flavor": flavor, "Style": "Non-dairy frozen dessert", "Base": f"{base} (plant-based)"}, claims=DESSERT_CLAIMS,
        ))  # fmt: skip
    out.append(_frz(
        PALMGROVE, "No Sugar Added Vanilla Coconut Milk Frozen Dessert", "ice-cream", N(C23, 120, 9, 8, 40, 15, 6, 1, 0, 1),
        [S("PT", "1 pint (16 fl oz)", 5.99, 16)],
        "Coconut milk (water, coconut cream), erythritol, chicory root fiber, vanilla extract, guar gum, monk fruit extract.",
        "Dairy-free, vegan vanilla frozen dessert with no sugar added, sweetened with erythritol and monk fruit.",
        tags=("dairy-free", "lactose-free", "vegan", "plant-based"),
        specs={"Flavor": "Vanilla", "Style": "Non-dairy frozen dessert", "Base": "Coconut milk (plant-based)"}, claims=DESSERT_CLAIMS,
    ))  # fmt: skip
    extras = [  # brand, title, type, facts, sizes, ingredients, allergens, tags, intro
        (STORE_BRAND, "Nonfat Vanilla Frozen Yogurt", "frozen-yogurt", N(C23, 140, 0, 0, 80, 29, 0, 24, 19, 5), [S("48OZ", "1.5 quarts (48 fl oz)", 4.29, 48)],
         "Cultured nonfat milk, sugar, corn syrup, whey protein concentrate, natural vanilla flavor, guar gum, live and active cultures.", ("milk",), (),
         "Fat free vanilla frozen yogurt with live and active cultures. Sweetened with sugar."),
        (STORE_BRAND, "Low Fat Chocolate Frozen Yogurt", "frozen-yogurt", N(C23, 150, 3, 2, 90, 28, 1, 23, 18, 5), [S("48OZ", "1.5 quarts (48 fl oz)", 4.29, 48)],
         "Cultured low fat milk, sugar, corn syrup, cocoa, whey protein concentrate, guar gum, live and active cultures.", ("milk",), (),
         "Low fat chocolate frozen yogurt with live and active cultures."),
        (KALOS, "Greek Frozen Yogurt Bars, Strawberry", "frozen-yogurt", N("1 bar (65 g)", 90, 2, 1, 30, 14, 0, 12, 10, 5), [S("4CT", "4 bars", 4.99, 9)],
         "Cultured low fat milk, strawberries, cane sugar, milk protein concentrate, guar gum, live and active cultures.", ("milk",), ("kosher",),
         "Creamy Greek frozen yogurt bars with strawberry, 5 g protein each."),
        (KALOS, "Greek Frozen Yogurt Bars, Mixed Berry", "frozen-yogurt", N("1 bar (65 g)", 90, 2, 1, 30, 14, 0, 12, 10, 5), [S("4CT", "4 bars", 4.99, 9)],
         "Cultured low fat milk, blueberries, raspberries, cane sugar, milk protein concentrate, guar gum, live and active cultures.", ("milk",), ("kosher",),
         "Creamy Greek frozen yogurt bars with mixed berries."),
        (STORE_BRAND, "Vanilla Ice Cream Sandwiches", "frozen-novelty", N("1 sandwich (63 g)", 160, 5, 3, 125, 26, 1, 14, 11, 3), [S("12CT", "12 sandwiches", 4.49, 27)],
         "Vanilla ice cream (milk, cream, sugar, corn syrup, whey), chocolate wafers (wheat flour, sugar, cocoa, palm oil, soy lecithin, salt).", ("milk", "wheat", "soy"), (),
         "Vanilla ice cream between two soft chocolate wafers."),
        (STORE_BRAND, "Strawberry Fruit Bars", "frozen-novelty", N("1 bar (70 g)", 70, 0, 0, 0, 17, 0, 15, 13, 0), [S("6CT", "6 bars", 3.49, 15)],
         "Water, strawberries, cane sugar, lemon juice, guar gum.", (), ("vegan", "dairy-free", "gluten-free"),
         "Frozen fruit bars made with real strawberries and cane sugar."),
        (FROSTLINE, "No Sugar Added Strawberry Fruit Bars", "frozen-novelty", N("1 bar (70 g)", 25, 0, 0, 0, 7, 1, 4, 0, 0), [S("6CT", "6 bars", 3.99, 15)],
         "Water, strawberries, erythritol, lemon juice, guar gum, stevia leaf extract.", (), ("vegan", "dairy-free", "gluten-free"),
         "Strawberry fruit bars with no sugar added, sweetened with erythritol and stevia. 25 calories each."),
        (STORE_BRAND, "Sugar Free Ice Pops", "frozen-novelty", N("1 pop (47 g)", 15, 0, 0, 0, 4, 0, 0, 0, 0), [S("20CT", "20 pops", 3.49, 33)],
         "Water, sorbitol, maltodextrin, citric acid, natural and artificial flavors, aspartame, acesulfame potassium, red 40, blue 1.", (), ("vegan", "gluten-free"),
         "Sugar free cherry, grape, and orange ice pops, 15 calories each."),
        (MOONLIT, "Chocolate-Dipped Vanilla Ice Cream Bars", "frozen-novelty", N("1 bar (79 g)", 260, 17, 12, 50, 24, 1, 21, 18, 3), [S("3CT", "3 bars", 5.49, 9)],
         "Vanilla ice cream (cream, skim milk, sugar, egg yolks, vanilla extract), milk chocolate coating (sugar, cocoa butter, chocolate, milk, soy lecithin).",
         ("milk", "egg", "soy"), (), "Premium vanilla ice cream bars dipped in milk chocolate."),
        (SILVERLEAF, "Dairy-Free Chocolate Almond Bars", "frozen-novelty", N("1 bar (74 g)", 240, 16, 6, 40, 22, 2, 16, 15, 3), [S("4CT", "4 bars", 5.99, 10)],
         "Almondmilk (water, almonds), cane sugar, coconut oil, dark chocolate (cocoa, sugar, cocoa butter), almonds, tapioca starch, sunflower lecithin.",
         ("tree nuts",), ("vegan", "dairy-free", "lactose-free", "plant-based"), "Vegan almondmilk frozen dessert bars dipped in dark chocolate and almonds."),
    ]  # fmt: skip
    for brand, title, ptype, n, sizes, ing, allergens, tags, intro in extras:
        out.append(
            _frz(
                brand,
                title,
                ptype,
                n,
                sizes,
                ing,
                intro,
                allergens=allergens,
                tags=tags,
                claims=DESSERT_CLAIMS,
            )
        )
    return out


# --- Vegetables and fruit -----------------------------------------------------------------------

VEG = {  # name: (facts, ingredients, allergens)
    "Broccoli Florets": (N("1 cup (85 g)", 25, 0, 0, 20, 4, 2, 1, 0, 2), "broccoli", ()),
    "Sweet Peas": (N("2/3 cup (89 g)", 70, 0, 0, 5, 12, 4, 5, 0, 5), "peas", ()),
    "Cut Sweet Corn": (N("2/3 cup (89 g)", 80, 0.5, 0, 0, 17, 2, 3, 0, 3), "corn", ()),
    "Cut Green Beans": (N("1 cup (85 g)", 25, 0, 0, 0, 5, 2, 2, 0, 1), "green beans", ()),
    "Mixed Vegetables": (N("2/3 cup (89 g)", 60, 0, 0, 40, 12, 3, 3, 0, 2), "carrots, corn, peas, green beans, lima beans", ()),
    "California Blend": (N("1 cup (85 g)", 25, 0, 0, 30, 5, 2, 2, 0, 2), "broccoli, cauliflower, carrots", ()),
    "Chopped Spinach": (N("1 cup (85 g)", 25, 0, 0, 95, 3, 3, 0, 0, 3), "spinach", ()),
    "Riced Cauliflower": (N("1 cup (85 g)", 20, 0, 0, 15, 4, 2, 2, 0, 2), "cauliflower", ()),
    "Stir-Fry Vegetables": (N("1 cup (85 g)", 30, 0, 0, 20, 6, 2, 3, 0, 1), "broccoli, carrots, snap peas, red peppers, water chestnuts, onions", ()),
    "Brussels Sprouts": (N("1 cup (85 g)", 35, 0, 0, 15, 7, 3, 2, 0, 3), "Brussels sprouts", ()),
    "Shelled Edamame": (N("1/2 cup (75 g)", 100, 4, 0.5, 5, 7, 4, 2, 0, 9), "shelled soybeans (edamame)", ("soy",)),
}  # fmt: skip
FRUIT = {  # name: (facts, ingredients)
    "Whole Strawberries": (N("1 cup (140 g)", 50, 0, 0, 0, 12, 3, 7, 0, 1), "strawberries"),
    "Blueberries": (N("1 cup (140 g)", 70, 0.5, 0, 0, 17, 4, 12, 0, 1), "blueberries"),
    "Mixed Berries": (N("1 cup (140 g)", 60, 0.5, 0, 0, 15, 5, 9, 0, 1), "strawberries, blueberries, raspberries, blackberries"),
    "Mango Chunks": (N("1 cup (140 g)", 90, 0.5, 0, 0, 23, 2, 20, 0, 1), "mango"),
    "Sliced Peaches": (N("1 cup (140 g)", 60, 0, 0, 0, 15, 2, 13, 0, 1), "peaches, ascorbic acid (to protect color)"),
    "Dark Sweet Cherries": (N("1 cup (140 g)", 90, 0, 0, 0, 22, 3, 18, 0, 1), "pitted dark sweet cherries"),
    "Pineapple Chunks": (N("1 cup (140 g)", 70, 0, 0, 0, 18, 2, 14, 0, 1), "pineapple"),
    "Tropical Fruit Blend": (N("1 cup (140 g)", 80, 0, 0, 0, 20, 2, 17, 0, 1), "pineapple, mango, papaya, strawberries"),
}  # fmt: skip


def _cap(text: str) -> str:
    return text[0].upper() + text[1:]


def vegetables_fruit() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    lines = [  # brand, vegetables, title prefix, sizes, organic
        (STORE_BRAND, ["Broccoli Florets", "Sweet Peas", "Cut Sweet Corn", "Cut Green Beans", "Mixed Vegetables", "California Blend", "Chopped Spinach", "Riced Cauliflower"],
         "Frozen ", [S("12OZ", "12 oz bag", 1.29, 12), S("32OZ", "32 oz bag", 3.49, 32)], False),
        (EVERGREEN, ["Broccoli Florets", "Sweet Peas", "Cut Green Beans", "Riced Cauliflower", "Stir-Fry Vegetables", "Brussels Sprouts", "Shelled Edamame"],
         "Steamable ", [S("10OZ", "10 oz microwave bag", 2.29, 10)], False),
        (CEDAR, ["Broccoli Florets", "Sweet Peas", "Cut Sweet Corn", "Mixed Vegetables", "Chopped Spinach", "Riced Cauliflower"],
         "Organic ", [S("10OZ", "10 oz bag", 2.99, 10)], True),
    ]  # fmt: skip
    for brand, names, prefix, sizes, organic in lines:
        for name in names:
            n, ing, allergens = VEG[name]
            ingredients = (
                _cap(", ".join(f"organic {i.strip()}" for i in ing.split(",")) if organic else ing)
                + "."
            )
            steam = " Steams in the bag in the microwave." if prefix == "Steamable " else ""
            out.append(_frz(
                brand, f"{prefix}{name}", "frozen-vegetables", n, sizes, ingredients,
                f"Frozen {name.lower()} with nothing added: no salt, no sauce.{steam}",
                allergens=allergens, tags=["no-salt-added", "vegan", "gluten-free"], specs={"Vegetable": name, "Sauce": "None"},
                claims=VEG_CLAIMS,
            ))  # fmt: skip
    sauced = [
        ("Steamable Broccoli & Cheese Sauce", N("1 cup (99 g)", 70, 3, 1.5, 380, 8, 2, 3, 1, 3),
         "Broccoli, water, cheddar cheese (milk, salt, cultures, enzymes), whey, modified corn starch, butter, salt, sugar, annatto."),
        ("Steamable Garlic Butter Green Beans", N("1 cup (85 g)", 60, 3.5, 2, 290, 6, 2, 2, 0, 1),
         "Green beans, butter (cream, salt), water, garlic, salt, modified corn starch, parsley."),
    ]  # fmt: skip
    for title, n, ing in sauced:
        out.append(_frz(
            EVERGREEN, title, "frozen-vegetables", n, [S("10OZ", "10 oz microwave bag", 2.49, 10)], ing,
            "Frozen vegetables in a buttery sauce, ready in the microwave. Contains added salt and milk.",
            allergens=("milk",), tags=["gluten-free"], specs={"Sauce": "Yes"}, claims=VEG_CLAIMS,
        ))  # fmt: skip
    for name, (n, ing) in FRUIT.items():
        out.append(_frz(
            STORE_BRAND, f"Frozen {name}", "frozen-fruit", n, [S("16OZ", "16 oz bag", 3.49, 16), S("48OZ", "48 oz bag", 8.99, 48)],
            _cap(ing) + ".", f"Unsweetened frozen {name.lower()} with no sugar added, for smoothies and baking.",
            tags=["unsweetened", "vegan", "gluten-free"], claims=("no-added-sugar", "low-sugar", "high-fiber"),
        ))  # fmt: skip
    for name in ("Whole Strawberries", "Blueberries", "Mixed Berries", "Mango Chunks"):
        n, ing = FRUIT[name]
        out.append(_frz(
            CEDAR, f"Organic Frozen {name}", "frozen-fruit", n, [S("10OZ", "10 oz bag", 4.49, 10)],
            _cap(", ".join(f"organic {i.strip()}" for i in ing.split(","))) + ".",
            f"Organic unsweetened frozen {name.lower()}, no sugar added.",
            tags=["unsweetened", "vegan", "gluten-free", "non-gmo"], claims=("no-added-sugar", "low-sugar", "high-fiber"),
        ))  # fmt: skip
    out.append(_frz(
        STORE_BRAND, "Sliced Strawberries in Sugar", "frozen-fruit", N("1/2 cup (128 g)", 120, 0, 0, 5, 30, 2, 27, 20, 1),
        [S("16OZ", "16 oz tub", 3.29, 16)], "Strawberries, sugar.",
        "Sliced strawberries packed with sugar for shortcake and desserts. Sweetened: 20 g added sugar per serving.",
        tags=["vegan", "gluten-free"], claims=("no-added-sugar", "low-sugar"),
    ))  # fmt: skip
    return out


# --- Meals and pizza ----------------------------------------------------------------------------

PASTA = "cooked pasta (water, durum wheat semolina)"


def meals() -> list[ProductSeed]:
    GF = ("gluten-free",)
    VGF = ("vegan", "dairy-free", "gluten-free", "plant-based")
    rows = [  # brand, title, type, facts, price, ingredients, allergens, tags, diet spec, intro
        (HEARTHSIDE, "Chicken Alfredo with Fettuccine", "frozen-meal", N("1 package (283 g)", 390, 14, 7, 780, 44, 3, 4, 0, 21), 3.49,
         f"{PASTA}, water, cooked white meat chicken, cream, parmesan cheese (milk), butter, egg whites, garlic, salt, modified corn starch, spices.",
         ("milk", "egg", "wheat"), (), "Classic", "Fettuccine and grilled chicken in a creamy parmesan Alfredo sauce."),
        (HEARTHSIDE, "Lasagna with Meat Sauce", "frozen-meal", N("1 package (297 g)", 400, 14, 6, 860, 46, 4, 8, 3, 22), 3.99,
         f"{PASTA}, tomato puree, cooked beef, ricotta cheese (milk), mozzarella cheese (milk), eggs, sugar, salt, garlic, spices.",
         ("milk", "egg", "wheat"), (), "Classic", "Layers of pasta, seasoned beef, ricotta, and mozzarella in tomato sauce."),
        (HEARTHSIDE, "Salisbury Steak with Mashed Potatoes", "frozen-meal", N("1 meal (312 g)", 380, 17, 7, 1010, 36, 4, 10, 4, 19), 3.49,
         "Beef patty (beef, water, bread crumbs (wheat flour, yeast, salt), textured soy protein, onions, salt), mashed potatoes (potatoes, milk, butter), gravy (water, wheat flour, beef stock, sugar, salt).",
         ("milk", "wheat", "soy"), (), "Classic", "Salisbury steak in brown gravy with mashed potatoes. High in sodium (1010 mg)."),
        (HEARTHSIDE, "Macaroni & Cheese", "frozen-meal", N("1 package (340 g)", 470, 19, 9, 1050, 55, 2, 6, 0, 20), 3.29,
         f"{PASTA}, milk, cheddar cheese (milk, salt, cultures, enzymes), butter, modified corn starch, salt, annatto.",
         ("milk", "wheat"), (), "Classic", "Elbow macaroni baked in a creamy cheddar cheese sauce."),
        (HEARTHSIDE, "Chicken Pot Pie", "frozen-meal", N("1 pie (283 g)", 620, 34, 13, 900, 59, 3, 6, 2, 16), 2.99,
         "Crust (wheat flour, palm oil, water, salt, sugar), water, cooked chicken, carrots, peas, potatoes, cream, modified corn starch, butter, salt, soy protein.",
         ("milk", "wheat", "soy"), (), "Classic", "Flaky pastry crust filled with chicken and vegetables in a creamy sauce."),
        (HEARTHSIDE, "Beef Enchiladas with Spanish Rice", "frozen-meal", N("1 meal (312 g)", 460, 17, 7, 1100, 56, 6, 6, 1, 19), 3.49,
         "Corn tortillas, cooked rice, cooked beef, water, cheddar cheese (milk), tomato puree, wheat flour, chili pepper, onions, salt, sugar, spices.",
         ("milk", "wheat"), (), "Classic", "Beef enchiladas in red chili sauce with cheese and Spanish rice."),
        (HEARTHSIDE, "Orange Chicken with Fried Rice", "frozen-meal", N("1 bowl (340 g)", 490, 12, 2, 920, 74, 2, 24, 21, 19), 3.99,
         "Cooked rice, battered chicken (chicken, wheat flour, water, corn starch, egg whites), sugar, orange juice concentrate, soy sauce (water, soybeans, wheat, salt), vinegar, peas, carrots.",
         ("wheat", "soy", "egg"), (), "Classic", "Crispy chicken in a sweet orange glaze with fried rice. 21 g added sugar."),
        (STORE_BRAND, "Lasagna with Meat Sauce", "frozen-meal", N("1 cup (227 g)", 330, 12, 6, 780, 35, 3, 7, 2, 19), 10.99,
         f"{PASTA}, tomato puree, cooked beef, ricotta cheese (milk), mozzarella cheese (milk), eggs, sugar, salt, spices.",
         ("milk", "egg", "wheat"), (), "Classic", "Family-size meat lasagna that serves six."),
        (STORE_BRAND, "Macaroni & Cheese", "frozen-meal", N("1 cup (227 g)", 360, 15, 8, 830, 40, 1, 5, 0, 15), 7.99,
         f"{PASTA}, milk, cheddar cheese (milk), butter, modified corn starch, salt.", ("milk", "wheat"), (), "Classic",
         "Family-size baked macaroni and cheese that serves five."),
        (LEAN, "Grilled Chicken & Broccoli Power Bowl", "frozen-meal", N("1 bowl (283 g)", 280, 8, 2, 580, 24, 5, 4, 1, 27), 4.49,
         "Cooked brown rice, grilled white meat chicken, broccoli, red quinoa, water, olive oil, garlic, lemon juice, sea salt, spices.",
         (), GF, "High protein", "Grilled chicken with broccoli, brown rice, and quinoa. 27 g protein."),
        (LEAN, "Turkey Meatballs Marinara with Whole Wheat Penne", "frozen-meal", N("1 bowl (255 g)", 300, 10, 3, 620, 30, 5, 7, 3, 24), 4.49,
         "Cooked whole wheat penne (water, whole wheat flour), turkey meatballs (turkey, bread crumbs (wheat), egg, parmesan cheese (milk), spices), tomato puree, olive oil, salt.",
         ("milk", "egg", "wheat"), (), "High protein", "Turkey meatballs in marinara over whole wheat penne. 24 g protein."),
        (LEAN, "Steak & Roasted Vegetable Bowl", "frozen-meal", N("1 bowl (269 g)", 290, 9, 3, 640, 24, 4, 4, 0, 28), 4.99,
         "Grilled beef, roasted potatoes, green beans, red peppers, onions, water, olive oil, garlic, salt, black pepper, rosemary.",
         (), GF, "High protein, gluten free", "Grilled steak with roasted potatoes and vegetables. 28 g protein, gluten free."),
        (LEAN, "Low Sodium Lemon Herb Chicken & Brown Rice", "frozen-meal", N("1 meal (283 g)", 280, 6, 1.5, 135, 32, 5, 3, 0, 24), 4.49,
         "Cooked brown rice, grilled white meat chicken, green beans, carrots, water, olive oil, lemon juice, garlic, herbs, black pepper.",
         (), (*GF, "no-salt-added"), "Low sodium", "Lemon herb chicken with brown rice and vegetables, made with no added salt: 135 mg sodium per meal."),
        (LEAN, "Low Sodium Turkey & Sweet Potato Bowl", "frozen-meal", N("1 bowl (283 g)", 270, 6, 1.5, 130, 34, 6, 9, 0, 20), 4.49,
         "Roasted turkey breast, sweet potatoes, kale, cranberries (cranberries, apple juice), water, olive oil, sage, thyme, black pepper.",
         (), (*GF, "no-salt-added"), "Low sodium", "Roasted turkey with sweet potatoes and kale, no salt added: 130 mg sodium per bowl."),
        (LEAN, "Keto Chicken Florentine", "frozen-meal", N("1 bowl (255 g)", 360, 24, 10, 780, 8, 3, 3, 0, 28), 5.49,
         "Grilled chicken, spinach, cream, parmesan cheese (milk), cauliflower, butter, garlic, salt, spices.",
         ("milk",), GF, "Keto", "Chicken in a creamy spinach parmesan sauce over cauliflower: 5 g net carbs."),
        (LEAN, "Keto Beef & Cauliflower Mash", "frozen-meal", N("1 bowl (255 g)", 380, 26, 12, 720, 9, 4, 4, 0, 26), 5.49,
         "Braised beef, cauliflower, cream, cheddar cheese (milk), butter, beef stock, onions, garlic, salt, thyme.",
         ("milk",), GF, "Keto", "Braised beef with cheesy cauliflower mash: 5 g net carbs."),
        (LEAN, "Chicken Tikka Masala with Basmati Rice", "frozen-meal", N("1 bowl (283 g)", 360, 10, 4, 690, 44, 3, 6, 2, 22), 4.49,
         "Cooked basmati rice, chicken, tomato puree, cream, yogurt (milk), onions, butter, ginger, garlic, cane sugar, salt, garam masala.",
         ("milk",), GF, "High protein, gluten free", "Chicken tikka masala in a spiced tomato cream sauce with basmati rice."),
        (HARVEST, "Organic Vegan Burrito Bowl", "frozen-meal", N("1 bowl (283 g)", 330, 8, 1, 590, 52, 10, 4, 0, 11), 4.99,
         "Organic brown rice, organic black beans, organic corn, organic tomatoes, organic peppers, organic onions, organic sunflower oil, sea salt, organic spices.",
         (), (*VGF, "non-gmo"), "Vegan, gluten free", "Organic black beans, brown rice, roasted corn, and salsa. 10 g fiber, vegan and gluten free."),
        (HARVEST, "Organic Chickpea Tikka Masala", "frozen-meal", N("1 bowl (283 g)", 340, 10, 3, 680, 50, 9, 8, 2, 11), 4.99,
         "Organic basmati rice, organic chickpeas, organic tomatoes, organic coconut milk, organic onions, organic cane sugar, organic ginger, sea salt, organic spices.",
         (), (*VGF, "non-gmo"), "Vegan, gluten free", "Chickpeas in a creamy coconut tikka masala sauce with basmati rice. Vegan."),
        (HARVEST, "Vegan Pad Thai with Tofu", "frozen-meal", N("1 bowl (269 g)", 410, 14, 2, 720, 58, 4, 14, 10, 14), 4.99,
         "Rice noodles (rice, water), tofu (soybeans, water, calcium sulfate), cane sugar, peanuts, tamari (water, soybeans, salt), tamarind, carrots, green onions, lime juice, sunflower oil.",
         ("soy", "peanuts"), VGF, "Vegan, gluten free", "Rice noodles and tofu in a tangy tamarind sauce with peanuts. Vegan and gluten free."),
        (HARVEST, "Organic Lentil Bolognese with Penne", "frozen-meal", N("1 bowl (283 g)", 350, 7, 1, 560, 56, 10, 8, 2, 15), 4.99,
         "Organic cooked penne (water, organic durum wheat semolina), organic tomatoes, organic lentils, organic carrots, organic onions, organic olive oil, organic cane sugar, sea salt, organic basil.",
         ("wheat",), ("vegan", "dairy-free", "plant-based", "non-gmo"), "Vegan", "Hearty lentil bolognese over penne. Vegan, with 15 g plant protein; contains wheat."),
        (HARVEST, "Vegan Mac & Cheeze", "frozen-meal", N("1 bowl (255 g)", 390, 15, 3, 610, 52, 4, 4, 1, 11), 4.99,
         f"{PASTA}, water, cashews, nutritional yeast, coconut oil, potato starch, sea salt, cane sugar, onion powder, turmeric, paprika.",
         ("wheat", "tree nuts"), ("vegan", "dairy-free", "plant-based"), "Vegan", "Elbow pasta in a creamy cashew-based cheese sauce, made without dairy. Contains tree nuts."),
        (HARVEST, "Gluten-Free Cheese Enchiladas", "frozen-meal", N("1 meal (255 g)", 370, 17, 8, 720, 38, 5, 4, 1, 15), 4.99,
         "Corn tortillas (corn, water, lime), Monterey Jack cheese (milk), black beans, tomatoes, onions, chili peppers, sunflower oil, sea salt, spices.",
         ("milk",), GF, "Gluten free, vegetarian", "Cheese enchiladas in corn tortillas with red sauce and black beans. Gluten free."),
        (STORE_BRAND, "Bean & Cheese Burritos", "burritos", N("1 burrito (142 g)", 300, 8, 3.5, 600, 45, 5, 2, 0, 11), 7.99,
         "Flour tortilla (wheat flour, water, palm oil, salt), refried beans (pinto beans, water, salt), cheddar cheese (milk), onions, spices.",
         ("wheat", "milk"), (), "Classic", "Microwaveable bean and cheese burritos."),
        (STORE_BRAND, "Beef & Bean Burritos", "burritos", N("1 burrito (142 g)", 320, 11, 4, 660, 43, 5, 2, 0, 12), 7.99,
         "Flour tortilla (wheat flour, water, palm oil, salt), refried beans, cooked beef, textured soy protein, cheddar cheese (milk), spices, salt.",
         ("wheat", "milk", "soy"), (), "Classic", "Microwaveable beef and bean burritos."),
        (STORE_BRAND, "Egg, Sausage & Cheese Breakfast Burritos", "burritos", N("1 burrito (113 g)", 280, 13, 5, 640, 28, 1, 1, 0, 12), 8.49,
         "Flour tortilla (wheat flour, water, palm oil, salt), scrambled eggs, pork sausage, cheddar cheese (milk), potatoes, salt, spices.",
         ("wheat", "milk", "egg"), (), "Classic", "Breakfast burritos with scrambled eggs, sausage, and cheese."),
    ]  # fmt: skip
    out: list[ProductSeed] = []
    for brand, title, ptype, n, price, ing, allergens, tags, diet, intro in rows:
        if ptype == "burritos":
            sizes = [S("8PK", "8 burritos", price)]
        elif brand == STORE_BRAND:
            sizes = [S("FAM", "Family size (about 40 oz)", price, 40)]
        else:
            sizes = [S("EA", "1 meal", price)]
        out.append(
            _frz(
                brand,
                title,
                ptype,
                n,
                sizes,
                ing,
                intro,
                allergens=allergens,
                tags=tags,
                specs={"Diet": diet},
                claims=MEAL_CLAIMS,
            )
        )
    return out


def pizza() -> list[ProductSeed]:
    crust = "crust (enriched wheat flour, water, soybean oil, yeast, sugar, salt)"
    sauce = "tomato sauce (tomato paste, water, sugar, salt, spices)"
    mozz = "mozzarella cheese (milk, cultures, salt, enzymes)"
    pepperoni = "pepperoni (pork, beef, salt, spices, dextrose, sodium nitrite)"
    cauli = "cauliflower crust (cauliflower, mozzarella cheese (milk), rice flour, egg whites, cornstarch, olive oil, salt)"
    WMS = ("wheat", "milk", "soy")
    rows = [  # brand, title, facts, price, ingredients, allergens, tags, crust spec, intro
        (BRICKYARD, "Rising Crust Pepperoni Pizza", N("1/6 pizza (132 g)", 340, 14, 6, 790, 38, 2, 5, 3, 15), 7.49,
         f"{crust.capitalize()}, {mozz}, {sauce}, {pepperoni}.", WMS, (), "Rising crust", "Thick, rising-crust pepperoni pizza that bakes up fresh."),
        (BRICKYARD, "Rising Crust Four Cheese Pizza", N("1/6 pizza (125 g)", 310, 11, 6, 640, 38, 2, 5, 3, 15), 7.49,
         f"{crust.capitalize()}, {mozz}, {sauce}, provolone, parmesan and asiago cheeses (milk).", WMS, (), "Rising crust", "Rising-crust pizza with mozzarella, provolone, parmesan, and asiago."),
        (BRICKYARD, "Rising Crust Supreme Pizza", N("1/6 pizza (140 g)", 330, 14, 6, 780, 38, 2, 5, 3, 14), 7.99,
         f"{crust.capitalize()}, {mozz}, {sauce}, {pepperoni}, cooked sausage, green peppers, onions, black olives.", WMS, (), "Rising crust",
         "Rising-crust pizza with pepperoni, sausage, peppers, onions, and olives."),
        (BRICKYARD, "Thin Crust Margherita Pizza", N("1/3 pizza (124 g)", 300, 13, 6, 560, 33, 2, 4, 2, 13), 6.99,
         f"{crust.capitalize()}, {mozz}, tomatoes, olive oil, basil, garlic, salt.", WMS, (), "Thin crust", "Crispy thin-crust pizza with mozzarella, tomatoes, and basil."),
        (BRICKYARD, "BBQ Chicken Pizza", N("1/6 pizza (130 g)", 320, 10, 5, 720, 42, 2, 9, 7, 15), 7.99,
         f"{crust.capitalize()}, {mozz}, barbecue sauce (tomato paste, sugar, molasses, vinegar, salt), cooked chicken, red onions, cilantro.", WMS, (), "Rising crust",
         "Pizza with barbecue sauce, grilled chicken, red onion, and cilantro."),
        (STORE_BRAND, "Thin Crust Pepperoni Pizza", N("1/4 pizza (121 g)", 340, 17, 7, 780, 31, 2, 4, 2, 14), 3.99,
         f"{crust.capitalize()}, {mozz}, {sauce}, {pepperoni}.", WMS, (), "Thin crust", "Crispy thin-crust pepperoni pizza."),
        (STORE_BRAND, "Thin Crust Cheese Pizza", N("1/4 pizza (115 g)", 300, 13, 6, 580, 31, 2, 4, 2, 13), 3.99,
         f"{crust.capitalize()}, {mozz}, {sauce}.", WMS, (), "Thin crust", "Crispy thin-crust cheese pizza."),
        (VEGGIECRUST, "Cauliflower Crust Margherita Pizza", N("1/3 pizza (113 g)", 230, 10, 5, 480, 24, 2, 3, 1, 10), 8.99,
         f"{cauli.capitalize()}, {mozz}, tomatoes, basil, olive oil, garlic, salt.", ("milk", "egg"), ("gluten-free",), "Cauliflower (gluten free)",
         "Margherita pizza on a gluten-free cauliflower crust. Contains milk and egg."),
        (VEGGIECRUST, "Cauliflower Crust Pepperoni Pizza", N("1/3 pizza (118 g)", 260, 13, 6, 610, 24, 2, 3, 1, 12), 8.99,
         f"{cauli.capitalize()}, {mozz}, {sauce}, {pepperoni}.", ("milk", "egg"), ("gluten-free",), "Cauliflower (gluten free)",
         "Pepperoni pizza on a gluten-free cauliflower crust."),
        (VEGGIECRUST, "Cauliflower Crust Roasted Veggie Pizza", N("1/3 pizza (120 g)", 220, 9, 4, 450, 26, 3, 4, 1, 9), 8.99,
         f"{cauli.capitalize()}, {mozz}, {sauce}, roasted red peppers, spinach, mushrooms, red onions.", ("milk", "egg"), ("gluten-free",), "Cauliflower (gluten free)",
         "Roasted vegetable pizza on a gluten-free cauliflower crust."),
        (VEGGIECRUST, "Vegan Cauliflower Crust Pizza", N("1/3 pizza (113 g)", 230, 11, 4, 430, 29, 3, 3, 1, 4), 9.49,
         "Cauliflower crust (cauliflower, rice flour, chickpea flour, cornstarch, olive oil, salt), dairy-free mozzarella-style shreds (water, coconut oil, "
         "tapioca starch, potato starch, sea salt), tomato sauce, spinach, basil.", (), ("gluten-free", "vegan", "dairy-free", "plant-based"), "Cauliflower (gluten free)",
         "Vegan pizza with dairy-free cheese on an egg-free, gluten-free cauliflower crust."),
        (VEGGIECRUST, "Gluten-Free Cheese Pizza", N("1/3 pizza (120 g)", 300, 12, 6, 560, 37, 1, 3, 2, 11), 7.99,
         f"Gluten-free crust (rice flour, tapioca starch, water, egg whites, olive oil, yeast, salt), {mozz}, {sauce}.", ("milk", "egg"), ("gluten-free",), "Rice flour (gluten free)",
         "Cheese pizza on a gluten-free rice flour crust."),
    ]  # fmt: skip
    return [
        _frz(brand, title, "pizza", n, [S("EA", "1 pizza", price)], ing, intro, allergens=allergens, tags=tags,
             specs={"Crust": crust_spec}, claims=("high-protein",))
        for brand, title, n, price, ing, allergens, tags, crust_spec, intro in rows
    ]  # fmt: skip


# --- Breakfast, seafood, chicken, potatoes ----------------------------------------------------------


def breakfast_and_more() -> list[ProductSeed]:
    WEMS = ("wheat", "egg", "milk", "soy")
    rows = [  # brand, title, type, facts, sizes, ingredients, allergens, tags, intro
        (STORE_BRAND, "Homestyle Waffles", "waffles", N("2 waffles (70 g)", 180, 6, 1, 390, 28, 1, 3, 3, 4), [S("10CT", "10 waffles", 2.49, 12.3)],
         "Enriched wheat flour, water, soybean oil, eggs, sugar, leavening, whey (milk), salt, soy lecithin.", WEMS, (), "Toaster-ready homestyle waffles."),
        (STORE_BRAND, "Buttermilk Waffles", "waffles", N("2 waffles (70 g)", 190, 6, 1.5, 400, 29, 1, 3, 3, 4), [S("10CT", "10 waffles", 2.49, 12.3)],
         "Enriched wheat flour, water, buttermilk, soybean oil, eggs, sugar, leavening, salt, soy lecithin.", WEMS, (), "Toaster-ready buttermilk waffles."),
        (SUNUP, "Blueberry Waffles", "waffles", N("2 waffles (70 g)", 190, 6, 1, 380, 31, 1, 6, 5, 4), [S("10CT", "10 waffles", 3.29, 12.3)],
         "Enriched wheat flour, water, blueberries, soybean oil, eggs, sugar, leavening, whey (milk), salt, soy lecithin.", WEMS, (), "Waffles with real blueberries."),
        (SUNUP, "Whole Grain Waffles", "waffles", N("2 waffles (70 g)", 170, 6, 1, 380, 26, 3, 3, 3, 4), [S("10CT", "10 waffles", 3.29, 12.3)],
         "Whole wheat flour, water, soybean oil, eggs, sugar, oat fiber, leavening, whey (milk), salt, soy lecithin.", WEMS, ("whole-grain",), "Waffles made with whole grain wheat flour."),
        (SUNUP, "Protein Waffles", "waffles", N("2 waffles (76 g)", 220, 7, 1.5, 430, 26, 3, 4, 3, 12), [S("8CT", "8 waffles", 4.49, 10.7)],
         "Whole wheat flour, water, whey protein concentrate (milk), eggs, pea protein, soybean oil, sugar, leavening, salt.", ("wheat", "milk", "egg"), (),
         "High-protein waffles with 12 g protein per serving."),
        (SUNUP, "Gluten-Free Homestyle Waffles", "waffles", N("2 waffles (70 g)", 190, 7, 1, 380, 29, 1, 3, 3, 2), [S("6CT", "6 waffles", 3.99, 7.4)],
         "Water, rice flour, canola oil, eggs, potato starch, sugar, tapioca starch, leavening, salt, xanthan gum.", ("egg",), ("gluten-free", "dairy-free"),
         "Gluten-free waffles made with rice flour. Contains egg."),
        (SUNUP, "Sausage, Egg & Cheese Croissant Sandwiches", "breakfast-sandwich", N("1 sandwich (128 g)", 400, 26, 11, 780, 27, 1, 4, 2, 14), [S("4CT", "4 sandwiches", 7.99, 18)],
         "Croissant (enriched wheat flour, butter, water, sugar, yeast), pork sausage, eggs, American cheese (milk), soybean oil, salt, soy lecithin.", WEMS, (),
         "Microwaveable croissant sandwiches with pork sausage, egg, and cheese."),
        (SUNUP, "Sausage, Egg & Cheese English Muffin Sandwiches", "breakfast-sandwich", N("1 sandwich (136 g)", 360, 19, 8, 850, 28, 1, 2, 1, 17), [S("4CT", "4 sandwiches", 7.49, 19)],
         "English muffin (enriched wheat flour, water, yeast, cornmeal, salt), pork sausage, eggs, American cheese (milk), soybean oil, soy lecithin.", WEMS, (),
         "English muffin sandwiches with pork sausage, egg, and cheese."),
        (SUNUP, "Turkey Sausage, Egg White & Cheese English Muffin Sandwiches", "breakfast-sandwich", N("1 sandwich (113 g)", 230, 7, 3, 640, 27, 3, 2, 1, 17), [S("4CT", "4 sandwiches", 7.99, 16)],
         "Whole wheat English muffin (whole wheat flour, water, yeast, salt), egg whites, turkey sausage, reduced fat cheddar cheese (milk), soy lecithin.", WEMS, (),
         "Lighter breakfast sandwiches with turkey sausage and egg whites: 230 calories and 17 g protein."),
        (SUNUP, "Bacon, Egg & Cheese Biscuit Sandwiches", "breakfast-sandwich", N("1 sandwich (125 g)", 420, 25, 11, 960, 33, 1, 3, 2, 14), [S("4CT", "4 sandwiches", 7.49, 17.6)],
         "Biscuit (enriched wheat flour, buttermilk, palm oil, leavening, salt), eggs, bacon (pork, salt, sugar, sodium nitrite), American cheese (milk), soy lecithin.", WEMS, (),
         "Buttermilk biscuit sandwiches with bacon, egg, and cheese."),
        (ROOTWELL, "Plant-Based Sausage & Egg-Free Breakfast Sandwiches", "breakfast-sandwich", N("1 sandwich (132 g)", 300, 13, 5, 690, 31, 4, 3, 2, 16), [S("4CT", "4 sandwiches", 8.99, 18.6)],
         "English muffin (enriched wheat flour, water, yeast, cornmeal, salt), plant-based sausage patty (water, soy protein, coconut oil, spices), "
         "mung bean egg-style patty, dairy-free cheese (coconut oil, potato starch).", ("wheat", "soy"), ("vegan", "dairy-free", "plant-based"),
         "Vegan breakfast sandwiches with plant-based sausage, an egg-free patty, and dairy-free cheese."),
        (NORTHCAPE, "Breaded Fish Sticks", "fish-sticks", N("6 sticks (95 g)", 240, 11, 1.5, 340, 22, 1, 2, 1, 11), [S("24OZ", "24 oz box (about 44 sticks)", 6.99, 24)],
         "Wild Alaska pollock, bread crumbs (wheat flour, water, yeast, salt), soybean oil, wheat flour, corn starch, salt.", ("fish", "wheat"), ("wild-caught",),
         "Crispy breaded fish sticks made with wild-caught Alaska pollock."),
        (NORTHCAPE, "Crispy Battered Cod Fillets", "fish-sticks", N("1 fillet (100 g)", 230, 12, 2, 450, 19, 1, 1, 0, 11), [S("19OZ", "19 oz box (6 fillets)", 7.99, 19)],
         "Wild Pacific cod, water, wheat flour, soybean oil, corn flour, whey (milk), salt, leavening.", ("fish", "wheat", "milk"), ("wild-caught",),
         "Beer-free, crispy battered wild-caught cod fillets."),
        (NORTHCAPE, "Gluten-Free Battered Haddock Fillets", "fish-sticks", N("1 fillet (100 g)", 220, 11, 1.5, 380, 18, 1, 1, 0, 11), [S("10OZ", "10 oz box (4 fillets)", 7.99, 10)],
         "Wild haddock, water, rice flour, sunflower oil, corn starch, salt, leavening.", ("fish",), ("wild-caught", "gluten-free", "dairy-free"),
         "Crispy gluten-free battered haddock made with rice flour."),
        (NORTHCAPE, "Breaded Popcorn Shrimp", "frozen-shrimp", N("3 oz (85 g)", 210, 10, 1.5, 570, 20, 1, 2, 1, 9), [S("16OZ", "16 oz bag", 8.99, 16)],
         "Shrimp, bread crumbs (wheat flour, sugar, yeast, salt), soybean oil, water, wheat flour, corn starch, salt.", ("shellfish", "wheat"), (),
         "Bite-size breaded shrimp for the oven or air fryer."),
        (STORE_BRAND, "Raw Peeled & Deveined Shrimp, Tail-On", "frozen-shrimp", N("4 oz (112 g)", 70, 0.5, 0, 560, 0, 0, 0, 0, 16), [S("2LB", "2 lb bag (31-40 per lb)", 14.99, 32)],
         "Shrimp, water, salt, sodium tripolyphosphate (to retain moisture).", ("shellfish",), (),
         "Individually frozen farm-raised raw shrimp, treated with salt and sodium tripolyphosphate."),
        (WILLOW, "Breaded Chicken Nuggets", "chicken-nuggets", N("5 nuggets (85 g)", 230, 13, 3, 430, 13, 1, 0, 0, 13), [S("32OZ", "32 oz bag", 8.99, 32)],
         "Chicken, water, wheat flour, soybean oil, corn starch, salt, spices, leavening, yeast extract.", ("wheat",), ("antibiotic-free",),
         "Fully cooked breaded chicken nuggets from chickens raised without antibiotics."),
        (WILLOW, "Gluten-Free Chicken Breast Nuggets", "chicken-nuggets", N("5 nuggets (85 g)", 200, 10, 2, 360, 11, 0, 0, 0, 14), [S("20OZ", "20 oz bag", 8.99, 20)],
         "Chicken breast, water, rice flour, sunflower oil, corn starch, salt, spices, yellow corn flour.", (), ("antibiotic-free", "gluten-free", "dairy-free"),
         "Fully cooked white meat nuggets breaded with rice flour, gluten free."),
        (CEDAR, "Organic Chicken Breast Nuggets", "chicken-nuggets", N("5 nuggets (85 g)", 190, 9, 2, 390, 13, 1, 1, 0, 14), [S("16OZ", "16 oz bag", 9.99, 16)],
         "Organic chicken breast, organic wheat flour, water, organic sunflower oil, sea salt, organic spices.", ("wheat",), ("antibiotic-free",),
         "Fully cooked organic white meat chicken nuggets."),
        (ROOTWELL, "Plant-Based Chicken-Style Nuggets", "chicken-nuggets", N("5 nuggets (86 g)", 200, 10, 1, 480, 14, 4, 0, 0, 13), [S("13OZ", "13 oz bag", 6.99, 13)],
         "Water, soy protein concentrate, wheat flour, canola oil, wheat gluten, corn starch, salt, spices, yeast extract.", ("soy", "wheat"),
         ("vegan", "dairy-free", "plant-based"), "Crispy vegan nuggets made from soy and wheat protein. Contains no chicken."),
        (STORE_BRAND, "Breaded Chicken Breast Strips", "chicken-nuggets", N("3 pieces (84 g)", 190, 9, 2, 450, 12, 0, 1, 0, 14), [S("25OZ", "25 oz bag", 7.99, 25)],
         "Chicken breast with rib meat, water, wheat flour, soybean oil, salt, spices, leavening.", ("wheat",), (), "Fully cooked breaded chicken strips."),
        (WILLOW, "Fully Cooked Grilled Chicken Breast Strips", "frozen-chicken", N("3 oz (84 g)", 90, 2, 0.5, 410, 1, 0, 1, 0, 18), [S("22OZ", "22 oz bag", 9.99, 22)],
         "Chicken breast, water, salt, sugar, natural flavors, spices.", (), ("antibiotic-free", "gluten-free", "dairy-free"),
         "Grilled, fully cooked chicken breast strips for salads and wraps. 18 g protein."),
        (RUSSET, "Straight Cut French Fries", "frozen-potatoes", N("3 oz (84 g)", 120, 4.5, 0.5, 20, 19, 2, 0, 0, 2), [S("32OZ", "32 oz bag", 3.99, 32)],
         "Potatoes, vegetable oil (canola, soybean), dextrose, sodium acid pyrophosphate (to retain color).", (), ("vegan", "gluten-free", "dairy-free"),
         "Unsalted straight cut fries; salt them yourself."),
        (RUSSET, "Crinkle Cut Fries", "frozen-potatoes", N("3 oz (84 g)", 120, 4, 0.5, 280, 19, 2, 0, 0, 2), [S("32OZ", "32 oz bag", 3.99, 32)],
         "Potatoes, vegetable oil (canola, soybean), salt, dextrose, sodium acid pyrophosphate.", (), ("vegan", "gluten-free", "dairy-free"), "Classic salted crinkle cut fries."),
        (RUSSET, "Seasoned Curly Fries", "frozen-potatoes", N("3 oz (84 g)", 160, 8, 1.5, 420, 19, 2, 0, 0, 2), [S("28OZ", "28 oz bag", 4.29, 28)],
         "Potatoes, vegetable oil, wheat flour, salt, spices, onion powder, garlic powder, paprika, leavening.", ("wheat",), ("vegan", "dairy-free"),
         "Spiral-cut fries in a seasoned batter. Contains wheat."),
        (RUSSET, "Crispy Potato Tots", "frozen-potatoes", N("9 pieces (86 g)", 170, 8, 1.5, 420, 21, 2, 0, 0, 2), [S("32OZ", "32 oz bag", 4.29, 32)],
         "Potatoes, vegetable oil, salt, corn flour, dehydrated onions, dextrose.", (), ("vegan", "gluten-free", "dairy-free"), "Crispy shredded potato tots."),
        (RUSSET, "Hash Brown Patties", "frozen-potatoes", N("1 patty (64 g)", 150, 9, 1.5, 270, 15, 1, 0, 0, 1), [S("10CT", "10 patties", 3.99, 22.5)],
         "Potatoes, vegetable oil, salt, corn flour, dextrose.", (), ("vegan", "gluten-free", "dairy-free"), "Golden shredded hash brown patties."),
        (RUSSET, "Sweet Potato Fries", "frozen-potatoes", N("3 oz (84 g)", 150, 7, 0.5, 190, 21, 3, 6, 4, 1), [S("20OZ", "20 oz bag", 4.49, 20)],
         "Sweet potatoes, vegetable oil, corn starch, cane sugar, salt.", (), ("vegan", "gluten-free", "dairy-free"), "Crispy sweet potato fries, lightly sweetened."),
        (STORE_BRAND, "Shredded Hash Browns, No Salt Added", "frozen-potatoes", N("1 cup (84 g)", 70, 0, 0, 15, 15, 1, 0, 0, 2), [S("30OZ", "30 oz bag", 2.99, 30)],
         "Potatoes, dextrose, sodium acid pyrophosphate.", (), ("vegan", "gluten-free", "dairy-free", "no-salt-added"),
         "Plain shredded potatoes with no oil and no salt added."),
    ]  # fmt: skip
    return [
        _frz(brand, title, ptype, n, sizes, ing, intro, allergens=allergens, tags=tags,
             claims=("high-protein", "low-sodium", "fat-free", "low-fat"))
        for brand, title, ptype, n, sizes, ing, allergens, tags, intro in rows
    ]  # fmt: skip


def products() -> list[ProductSeed]:
    return [*ice_cream(), *vegetables_fruit(), *meals(), *pizza(), *breakfast_and_more()]


__all__ = ["products"]
