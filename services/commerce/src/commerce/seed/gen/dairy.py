"""Dairy & Eggs: milk, plant milk, yogurt, cheese, butter, eggs, cream, and kefir.

Deliberately dense in the attributes shoppers ask about: fat level, organic, lactose-free,
dairy-free, sugar content, sourcing. Nutrition values are typical label values.
"""

from __future__ import annotations

from dataclasses import dataclass

from commerce.seed.data import Nutrition, ProductSeed
from commerce.seed.gen.common import REFRIGERATED, STORE_BRAND, Size, cents, food, slugify

CAT = "dairy-eggs"
FERNBROOK = "Fernbrook Dairy"
CEDAR = "Cedar Hollow Farms"  # organic
BRAMBLE = "Bramblewood Creamery"  # organic, grass-fed, premium
CLEARPEAK = "Clearpeak Dairy"  # ultra-filtered
SILVERLEAF = "Silverleaf"  # almond, cashew
ROLLING = "Rolling Acre Oat Co."
PALMGROVE = "Palmgrove"  # coconut
NORTHWIND = "Northwind Skyr Co."
KALOS = "Kalos Greek Yogurt Co."
ALDER = "Alder Creek Cheese Co."
HENHOUSE = "Hollis Hen Farm"  # eggs


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


CUP = "1 cup (240 mL)"
FAT_CLAIMS = ("fat-free", "low-fat")
SUGAR_CLAIMS = ("sugar-free", "no-added-sugar", "low-sugar")
PROTEIN_CLAIMS = ("high-protein",)


# --- Milk -----------------------------------------------------------------------------------


@dataclass(frozen=True)
class MilkFat:
    key: str
    name: str  # as in the title
    milkfat: str
    tag: str
    facts: Nutrition
    uf_facts: Nutrition  # ultra-filtered version


MILK_FATS = (
    MilkFat("whole", "Whole Milk", "3.25%", "whole-milk",
            N(CUP, 150, 8, 5, 120, 12, 0, 12, 0, 8), N(CUP, 150, 8, 5, 120, 6, 0, 6, 0, 13)),
    MilkFat("2pct", "2% Reduced Fat Milk", "2%", "reduced-fat",
            N(CUP, 120, 5, 3, 120, 12, 0, 12, 0, 8), N(CUP, 120, 4.5, 3, 125, 6, 0, 6, 0, 13)),
    MilkFat("1pct", "1% Low Fat Milk", "1%", "low-fat",
            N(CUP, 100, 2.5, 1.5, 125, 12, 0, 12, 0, 8), N(CUP, 100, 2.5, 1.5, 125, 6, 0, 6, 0, 13)),
    MilkFat("skim", "Fat Free Skim Milk", "0%", "fat-free",
            N(CUP, 90, 0, 0, 130, 13, 0, 12, 0, 8), N(CUP, 80, 0, 0, 130, 6, 0, 6, 0, 13)),
)  # fmt: skip


def _milk_ingredients(fat: MilkFat, organic: bool, lactose_free: bool) -> str:
    milk = f"{'Organic grade A' if organic else 'Grade A'} {'milk' if fat.key == 'whole' else fat.name.split(' Milk')[0].lower() + ' milk'}"
    parts = [milk]
    if lactose_free:
        parts.append("lactase enzyme")
    if fat.key != "whole":
        parts.append("vitamin A palmitate")
    parts.append("vitamin D3")
    text = ", ".join(parts)
    return text[0].upper() + text[1:] + "."


def milks() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    # (brand, organic, lactose_free, fats, sizes as (code, label, oz, price per gallon-equivalent))
    lines = [
        (STORE_BRAND, False, False, "all", [("GAL", "1 gallon", 128, 3.29), ("HG", "Half gallon", 64, 2.19)]),
        (FERNBROOK, False, False, "all", [("GAL", "1 gallon", 128, 3.89), ("HG", "Half gallon", 64, 2.49)]),
        (CEDAR, True, False, "all", [("GAL", "1 gallon", 128, 6.99), ("HG", "Half gallon", 64, 4.49)]),
        (STORE_BRAND, False, True, "all", [("HG", "Half gallon", 64, 3.79)]),
        (FERNBROOK, False, True, ("whole", "2pct", "skim"), [("HG", "Half gallon", 64, 4.29)]),
        (CEDAR, True, True, ("whole", "2pct", "skim"), [("HG", "Half gallon", 64, 5.49)]),
        (BRAMBLE, True, False, ("whole", "2pct", "skim"), [("HG", "Half gallon", 64, 5.79), ("QT", "1 quart", 32, 3.49)]),
    ]  # fmt: skip
    for brand, organic, lactose_free, fats, sizes in lines:
        for fat in MILK_FATS:
            if fats != "all" and fat.key not in fats:
                continue
            name = fat.name.replace(" Milk", " Lactose-Free Milk") if lactose_free else fat.name
            title = f"{'Organic ' if organic else ''}{name}"
            grass_fed = brand == BRAMBLE
            tags = [fat.tag, "kosher"] + (["organic"] if organic else [])
            tags += ["lactose-free"] if lactose_free else []
            tags += ["grass-fed", "pasture-raised"] if grass_fed else []
            intro = (
                f"{title} ({fat.milkfat} milkfat)"
                f"{' with the lactose already broken down, so it is easy to digest' if lactose_free else ''}"
                f"{' from grass-fed, pasture-raised cows' if grass_fed else ''}."
                f"{' Ultra-pasteurized for a longer shelf life.' if organic else ''}"
                " Cow's milk."
            )
            out.append(
                food(
                    category=CAT, product_type="milk", brand=brand, title=title,
                    sizes=[Size(c, lbl, cents(p), oz) for c, lbl, oz, p in sizes],
                    nutrition=fat.facts,
                    ingredients=_milk_ingredients(fat, organic, lactose_free),
                    allergens=("milk",), tags=tags, claims=("no-added-sugar",),
                    specs={
                        "Milkfat": fat.milkfat,
                        "Pasteurization": "Ultra-pasteurized" if organic else "Pasteurized",
                        "Lactose": "Lactose free" if lactose_free else "Contains lactose",
                    },
                    intro=intro, storage=REFRIGERATED,
                )
            )  # fmt: skip
    # Ultra-filtered: more protein, half the sugar, lactose free.
    for fat in MILK_FATS:
        if fat.key == "1pct":
            continue
        title = f"Ultra-Filtered {fat.name.replace(' Milk', ' Lactose-Free Milk')}"
        out.append(
            food(
                category=CAT, product_type="milk", brand=CLEARPEAK, title=title,
                sizes=[Size("52OZ", "52 fl oz", cents(4.69), 52)],
                nutrition=fat.uf_facts,
                ingredients=_milk_ingredients(fat, False, True).replace("milk,", "ultra-filtered milk,", 1),
                allergens=("milk",), tags=[fat.tag, "lactose-free"],
                claims=("high-protein", "low-sugar", "no-added-sugar"),
                specs={"Milkfat": fat.milkfat, "Pasteurization": "Ultra-pasteurized", "Lactose": "Lactose free"},
                intro=(
                    f"{fat.milkfat} milkfat milk filtered for 50% more protein and half the sugar "
                    "of regular milk, with the lactose removed."
                ),
                storage=REFRIGERATED,
            )
        )  # fmt: skip
    # Flavored milk
    flavored = [
        (FERNBROOK, "1% Low Fat Chocolate Milk", "low-fat", "1%", N(CUP, 160, 2.5, 1.5, 150, 26, 1, 24, 11, 8), "chocolate"),
        (FERNBROOK, "Whole Chocolate Milk", "whole-milk", "3.25%", N(CUP, 210, 8, 5, 150, 26, 1, 24, 12, 8), "chocolate"),
        (FERNBROOK, "1% Low Fat Strawberry Milk", "low-fat", "1%", N(CUP, 170, 2.5, 1.5, 125, 27, 0, 26, 13, 8), "strawberry"),
        (STORE_BRAND, "1% Low Fat Chocolate Milk", "low-fat", "1%", N(CUP, 160, 2.5, 1.5, 150, 26, 1, 24, 11, 8), "chocolate"),
        (CEDAR, "Organic 2% Reduced Fat Chocolate Milk", "reduced-fat", "2%", N(CUP, 190, 5, 3, 150, 27, 1, 25, 13, 8), "chocolate"),
        (CLEARPEAK, "Ultra-Filtered Reduced Fat Chocolate Milk", "reduced-fat", "2%", N(CUP, 140, 4.5, 3, 190, 13, 1, 12, 6, 13), "chocolate"),
    ]  # fmt: skip
    for brand, title, fat_tag, milkfat, n, flavor in flavored:
        organic = title.startswith("Organic")
        flavor_ing = (
            "cocoa (processed with alkali)"
            if flavor == "chocolate"
            else "natural strawberry flavor, beet juice (color)"
        )
        out.append(
            food(
                category=CAT, product_type="milk", brand=brand, title=title,
                sizes=[Size("HG", "Half gallon", cents(3.29 if not organic else 4.99), 64),
                       Size("QT", "1 quart", cents(2.19 if not organic else 3.29), 32)],
                nutrition=n,
                ingredients=f"{'Organic ' if organic else ''}{milkfat} milk, cane sugar, {flavor_ing}, salt, gellan gum, vitamin A palmitate, vitamin D3.",
                allergens=("milk",), tags=[fat_tag, *(["organic"] if organic else []),
                                           *(["lactose-free"] if brand == CLEARPEAK else [])],
                claims=PROTEIN_CLAIMS,
                specs={"Milkfat": milkfat, "Flavor": flavor.capitalize()},
                intro=f"Creamy {flavor} milk sweetened with cane sugar. Contains added sugar.",
                storage=REFRIGERATED,
            )
        )  # fmt: skip
    return out


# --- Plant-based milk -------------------------------------------------------------------------


def plant_milks() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    # base: (allergens, base ingredient, brands, {flavor: nutrition})
    catalog = {
        "Almond": (("tree nuts",), "almondmilk (filtered water, almonds)", (SILVERLEAF, STORE_BRAND), {
            "Unsweetened Original": N(CUP, 30, 2.5, 0, 170, 1, 0, 0, 0, 1),
            "Original": N(CUP, 60, 2.5, 0, 150, 8, 0, 7, 7, 1),
            "Unsweetened Vanilla": N(CUP, 30, 2.5, 0, 150, 1, 0, 0, 0, 1),
            "Vanilla": N(CUP, 80, 2.5, 0, 150, 13, 0, 12, 12, 1),
            "Chocolate": N(CUP, 110, 3, 0, 150, 21, 1, 20, 20, 1),
        }),
        "Oat": ((), "oatmilk (filtered water, oats)", (ROLLING, STORE_BRAND), {
            "Unsweetened Original": N(CUP, 90, 4.5, 0.5, 115, 11, 2, 0, 0, 2),
            "Original": N(CUP, 120, 5, 0.5, 100, 16, 2, 7, 4, 3),
            "Vanilla": N(CUP, 130, 5, 0.5, 100, 19, 2, 10, 7, 3),
            "Barista Edition": N(CUP, 140, 7, 1, 100, 16, 2, 7, 4, 3),
        }),
        "Soy": (("soy",), "soymilk (filtered water, whole soybeans)", (STORE_BRAND, SILVERLEAF), {
            "Unsweetened Original": N(CUP, 80, 4, 0.5, 75, 4, 2, 1, 0, 7),
            "Original": N(CUP, 110, 4.5, 0.5, 95, 9, 2, 6, 5, 8),
            "Vanilla": N(CUP, 100, 3.5, 0.5, 95, 10, 1, 8, 7, 6),
        }),
        "Coconut": ((), "coconutmilk (filtered water, coconut cream)", (PALMGROVE,), {
            "Unsweetened Original": N(CUP, 45, 4.5, 4, 20, 1, 0, 0, 0, 0),
            "Original": N(CUP, 80, 5, 4.5, 20, 7, 0, 7, 7, 0),
        }),
        "Cashew": (("tree nuts",), "cashewmilk (filtered water, cashews)", (SILVERLEAF,), {
            "Unsweetened Original": N(CUP, 25, 2, 0, 160, 1, 0, 0, 0, 1),
            "Unsweetened Vanilla": N(CUP, 25, 2, 0, 160, 1, 0, 0, 0, 1),
        }),
    }  # fmt: skip
    for base, (allergens, base_ing, brands, flavors) in catalog.items():
        for brand in brands:
            for flavor, n in flavors.items():
                if brand == STORE_BRAND and flavor in (
                    "Chocolate",
                    "Barista Edition",
                    "Unsweetened Vanilla",
                ):
                    continue
                unsweetened = flavor.startswith("Unsweetened")
                title = f"{flavor} {base} Milk"
                sweet = "" if unsweetened else "cane sugar, "
                vanilla = "natural vanilla flavor, " if "Vanilla" in flavor else ""
                cocoa = "cocoa, " if flavor == "Chocolate" else ""
                barista = "sunflower oil, " if flavor == "Barista Edition" else ""
                price = {SILVERLEAF: 3.99, ROLLING: 4.49, PALMGROVE: 3.79, STORE_BRAND: 2.99}[brand]
                sizes = [Size("64OZ", "64 fl oz", cents(price), 64)]
                if flavor == "Barista Edition":
                    sizes = [Size("32OZ", "32 fl oz", cents(3.99), 32)]
                out.append(
                    food(
                        category=CAT, product_type="plant-milk", brand=brand, title=title,
                        sizes=sizes, nutrition=n,
                        ingredients=(
                            f"{base_ing.capitalize()}, {sweet}{cocoa}{vanilla}{barista}calcium carbonate, "
                            "sea salt, gellan gum, vitamin A palmitate, vitamin D2."
                        ),
                        allergens=allergens,
                        tags=["dairy-free", "lactose-free", "vegan", "plant-based",
                              *(["unsweetened"] if unsweetened else []),
                              *(["non-gmo"] if base in ("Oat", "Soy") else [])],
                        claims=("sugar-free", "no-added-sugar", "low-sugar", "keto", "low-fat"),
                        specs={"Milk type": f"{base} (plant-based)", "Flavor": flavor},
                        intro=(
                            f"{flavor.lower()} {base.lower()} milk, a dairy-free, plant-based "
                            f"alternative to cow's milk{' with no sugar or sweeteners added' if unsweetened else ''}. "
                            "Shake well."
                        ).capitalize(),
                        storage=REFRIGERATED,
                    )
                )  # fmt: skip
    return out


# --- Yogurt ----------------------------------------------------------------------------------

CUP53 = "1 container (150 g)"
CUP6 = "1 container (170 g)"
FRUIT = (
    "Strawberry",
    "Blueberry",
    "Peach",
    "Mixed Berry",
    "Black Cherry",
    "Key Lime",
    "Mango",
    "Lemon",
)


def _yogurt(
    brand: str,
    title: str,
    n: Nutrition,
    *,
    style: str,
    flavor: str,
    milk: str,
    tags: list[str],
    sweetener: str,
    tub: bool,
    single_price: float,
    allergens: tuple[str, ...] = ("milk",),
) -> ProductSeed:
    sizes = [Size("CUP", "5.3 oz cup", cents(single_price), 5.3),
             Size("4PK", "4 x 5.3 oz cups", cents(single_price * 3.6), 21.2)]  # fmt: skip
    if tub:
        sizes.append(Size("32OZ", "32 oz tub", cents(single_price * 5), 32))
    flavor_ing = (
        ""
        if flavor == "Plain"
        else f"{flavor.lower()} {'flavor' if flavor in ('Vanilla', 'Honey') else 'fruit preparation'}, "
    )
    ing = f"{milk}, {flavor_ing}{sweetener + ', ' if sweetener else ''}live and active cultures."
    if "lactose-free" in tags and "dairy-free" not in tags:  # lactase only matters in dairy
        ing = ing.replace("live and active cultures.", "lactase enzyme, live and active cultures.")
    sugar_note = (
        "No sugar at all."
        if n.total_sugars_g < 0.5
        else "No added sugar; the sugar is naturally occurring."
        if n.added_sugars_g == 0
        else "Sweetened with cane sugar."
    )
    return food(
        category=CAT, product_type="yogurt", brand=brand, title=title,
        sizes=sizes, nutrition=n, ingredients=ing[0].upper() + ing[1:], allergens=allergens,
        tags=tags, claims=(*FAT_CLAIMS, *SUGAR_CLAIMS, *PROTEIN_CLAIMS, "keto"),
        specs={"Style": style, "Flavor": flavor},
        intro=f"{style} yogurt, {flavor.lower()}, with live and active cultures. {sugar_note}",
        storage=REFRIGERATED,
    )  # fmt: skip


def yogurts() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    greek = {  # fat: (plain, flavored, milk ingredient, fat tag)
        "Nonfat": (N(CUP53, 80, 0, 0, 55, 5, 0, 4, 0, 15), N(CUP53, 120, 0, 0, 55, 15, 0, 12, 8, 12), "cultured nonfat milk", []),
        "Low Fat": (N(CUP53, 110, 3, 2, 55, 5, 0, 4, 0, 15), N(CUP53, 140, 3, 2, 55, 15, 0, 12, 8, 12), "cultured reduced fat milk", []),
        "Whole Milk": (N(CUP53, 170, 9, 6, 55, 6, 0, 5, 0, 15), N(CUP53, 200, 8, 5, 55, 17, 0, 14, 9, 12), "cultured whole milk", ["whole-milk"]),
    }  # fmt: skip
    for brand, organic, price in (
        (KALOS, False, 1.49),
        (FERNBROOK, False, 1.29),
        (STORE_BRAND, False, 0.99),
        (CEDAR, True, 1.79),
    ):
        for fat, (plain_n, flav_n, milk, fat_tags) in greek.items():
            if organic and fat == "Low Fat":
                continue
            flavors = ["Plain", "Vanilla", "Honey", *FRUIT[: (6 if brand == KALOS else 3)]]
            if fat == "Whole Milk" and brand != KALOS:
                flavors = flavors[:3]
            for flavor in flavors:
                n = plain_n if flavor == "Plain" else flav_n
                org = "Organic " if organic else ""
                out.append(_yogurt(
                    brand, f"{org}{fat} Greek Yogurt, {flavor}", n, style="Greek", flavor=flavor,
                    milk=f"{org.lower()}{milk}".strip(), tags=[*fat_tags, *(["organic"] if organic else []), "kosher"],
                    sweetener="" if flavor == "Plain" else "cane sugar", tub=flavor in ("Plain", "Vanilla"),
                    single_price=price + (0.2 if organic else 0),
                ))  # fmt: skip
    # Zero sugar and light Greek yogurt: sweetened without sugar.
    zero = N(CUP53, 90, 0, 0, 60, 5, 0, 0, 0, 11)
    light = N(CUP53, 80, 0, 0, 55, 9, 0, 6, 0, 12)
    for brand, price in ((KALOS, 1.59), (FERNBROOK, 1.39), (STORE_BRAND, 1.09)):
        for flavor in (
            "Vanilla",
            "Strawberry",
            "Blueberry",
            "Peach",
            "Black Cherry",
            "Mixed Berry",
        ):
            out.append(_yogurt(
                brand, f"Zero Sugar Greek Yogurt, {flavor}", zero, style="Greek", flavor=flavor,
                milk="ultra-filtered nonfat milk", tags=["lactose-free", "kosher"],
                sweetener="allulose, stevia leaf extract, monk fruit extract", tub=False, single_price=price,
            ))  # fmt: skip
        for flavor in ("Vanilla", "Strawberry", "Key Lime", "Cherry"):
            out.append(_yogurt(
                brand, f"Light Nonfat Greek Yogurt, {flavor}", light, style="Greek", flavor=flavor,
                milk="cultured nonfat milk", tags=["kosher"], sweetener="stevia leaf extract",
                tub=False, single_price=price - 0.1,
            ))  # fmt: skip
    # Traditional (smooth, not strained)
    trad = [
        ("Low Fat", "Plain", N(CUP6, 110, 2.5, 1.5, 125, 16, 0, 16, 0, 9), "cultured low fat milk", []),
        ("Low Fat", "Vanilla", N(CUP6, 150, 2, 1, 95, 26, 0, 22, 15, 6), "cultured low fat milk", []),
        ("Nonfat", "Plain", N(CUP6, 90, 0, 0, 130, 13, 0, 12, 0, 9), "cultured nonfat milk", []),
        ("Whole Milk", "Plain", N(CUP6, 150, 8, 5, 115, 11, 0, 11, 0, 8), "cultured whole milk", ["whole-milk"]),
        ("Whole Milk", "Vanilla", N(CUP6, 180, 7, 4.5, 110, 22, 0, 19, 9, 7), "cultured whole milk", ["whole-milk"]),
    ] + [("Low Fat", f, N(CUP6, 150, 2, 1, 95, 26, 0, 22, 15, 6), "cultured low fat milk", []) for f in FRUIT[:6]]  # fmt: skip
    for brand, organic, price in (
        (FERNBROOK, False, 0.89),
        (STORE_BRAND, False, 0.69),
        (CEDAR, True, 1.29),
    ):
        for fat, flavor, n, milk, fat_tags in trad:
            if organic and fat == "Nonfat":
                continue
            org = "Organic " if organic else ""
            out.append(_yogurt(
                brand, f"{org}{fat} Yogurt, {flavor}", n, style="Traditional", flavor=flavor,
                milk=f"{org.lower()}{milk}".strip(), tags=[*fat_tags, *(["organic"] if organic else [])],
                sweetener="" if flavor == "Plain" else "cane sugar", tub=flavor in ("Plain", "Vanilla"),
                single_price=price,
            ))  # fmt: skip
    # Icelandic skyr
    for fat, flavor, n in [
        ("Nonfat", "Plain", N(CUP53, 90, 0, 0, 65, 6, 0, 4, 0, 16)),
        ("Nonfat", "Vanilla", N(CUP53, 110, 0, 0, 65, 12, 0, 9, 5, 15)),
        ("Nonfat", "Strawberry", N(CUP53, 110, 0, 0, 65, 12, 0, 9, 5, 15)),
        ("Nonfat", "Blueberry", N(CUP53, 110, 0, 0, 65, 12, 0, 9, 5, 15)),
        ("Nonfat", "Raspberry", N(CUP53, 110, 0, 0, 65, 12, 0, 9, 5, 15)),
        ("Whole Milk", "Plain", N(CUP53, 150, 6, 4, 65, 6, 0, 5, 0, 15)),
        ("Whole Milk", "Vanilla", N(CUP53, 170, 5, 3.5, 65, 13, 0, 10, 6, 14)),
    ]:
        out.append(_yogurt(
            NORTHWIND, f"{fat} Icelandic Skyr, {flavor}", n, style="Icelandic skyr", flavor=flavor,
            milk=f"cultured {'skim' if fat == 'Nonfat' else 'whole'} milk",
            tags=["whole-milk"] if fat == "Whole Milk" else [],
            sweetener="" if flavor == "Plain" else "cane sugar", tub=flavor == "Plain", single_price=1.89,
        ))  # fmt: skip
    # Plant-based yogurt
    plant = [
        (SILVERLEAF, "Almond", "Unsweetened Plain", N(CUP53, 130, 11, 1, 10, 5, 2, 0, 0, 5), ("tree nuts",), "almondmilk (water, almonds)", ""),
        (SILVERLEAF, "Almond", "Vanilla", N(CUP53, 160, 10, 1, 10, 15, 2, 8, 8, 4), ("tree nuts",), "almondmilk (water, almonds)", "cane sugar"),
        (SILVERLEAF, "Almond", "Strawberry", N(CUP53, 160, 10, 1, 10, 16, 2, 9, 8, 4), ("tree nuts",), "almondmilk (water, almonds)", "cane sugar"),
        (ROLLING, "Oat", "Plain", N(CUP53, 130, 6, 0.5, 20, 17, 2, 3, 2, 2), (), "oatmilk (water, oats)", "cane sugar"),
        (ROLLING, "Oat", "Strawberry", N(CUP53, 150, 5, 0.5, 20, 24, 2, 12, 11, 2), (), "oatmilk (water, oats)", "cane sugar"),
        (ROLLING, "Oat", "Blueberry", N(CUP53, 150, 5, 0.5, 20, 24, 2, 12, 11, 2), (), "oatmilk (water, oats)", "cane sugar"),
        (PALMGROVE, "Coconut", "Unsweetened Plain", N(CUP53, 110, 9, 8, 15, 6, 1, 1, 0, 1), (), "coconut cream, water", ""),
        (PALMGROVE, "Coconut", "Vanilla", N(CUP53, 130, 8, 7, 15, 15, 1, 10, 9, 1), (), "coconut cream, water", "cane sugar"),
        (PALMGROVE, "Coconut", "Mango", N(CUP53, 130, 8, 7, 15, 15, 1, 11, 9, 1), (), "coconut cream, water", "cane sugar"),
    ]  # fmt: skip
    for brand, base, flavor, n, allergens, milk, sweetener in plant:
        out.append(_yogurt(
            brand, f"{base}milk Yogurt Alternative, {flavor}", n, style="Plant-based", flavor=flavor.replace("Unsweetened ", ""),
            milk=milk, tags=["dairy-free", "lactose-free", "vegan", "plant-based",
                             *(["unsweetened"] if flavor.startswith("Unsweetened") else [])],
            sweetener=sweetener, tub=False, single_price=1.99, allergens=allergens,
        ))  # fmt: skip
    return out


# --- Cheese ----------------------------------------------------------------------------------

OZ1 = "1 oz (28 g)"


def cheeses() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    # name: (nutrition, forms, brands, extra tags)
    types = {
        "Sharp Cheddar": (N(OZ1, 110, 9, 5, 180, 1, 0, 0, 0, 7), ("Block", "Shredded", "Sliced"), (STORE_BRAND, FERNBROOK, CEDAR), []),
        "Mild Cheddar": (N(OZ1, 110, 9, 5, 180, 1, 0, 0, 0, 7), ("Block", "Shredded"), (STORE_BRAND, FERNBROOK), []),
        "Extra Sharp White Cheddar": (N(OZ1, 110, 9, 6, 170, 0, 0, 0, 0, 7), ("Block",), (ALDER, CEDAR), []),
        "2% Milk Reduced Fat Sharp Cheddar": (N(OZ1, 90, 6, 3.5, 240, 1, 0, 0, 0, 8), ("Block", "Shredded"), (FERNBROOK,), ["reduced-fat"]),
        "Part-Skim Mozzarella": (N(OZ1, 80, 6, 3.5, 180, 1, 0, 0, 0, 7), ("Block", "Shredded", "Sliced"), (STORE_BRAND, FERNBROOK, CEDAR), []),
        "Whole Milk Mozzarella": (N(OZ1, 90, 7, 4, 180, 1, 0, 0, 0, 6), ("Shredded",), (FERNBROOK,), ["whole-milk"]),
        "Fat Free Mozzarella": (N(OZ1, 45, 0, 0, 250, 3, 0, 0, 0, 9), ("Shredded",), (STORE_BRAND,), []),
        "Swiss": (N(OZ1, 110, 9, 5, 55, 1, 0, 0, 0, 8), ("Sliced", "Block"), (STORE_BRAND, FERNBROOK), []),
        "Provolone": (N(OZ1, 100, 8, 5, 250, 1, 0, 0, 0, 7), ("Sliced",), (STORE_BRAND, FERNBROOK), []),
        "Pepper Jack": (N(OZ1, 110, 9, 5, 170, 0, 0, 0, 0, 7), ("Block", "Sliced", "Shredded"), (STORE_BRAND, FERNBROOK), []),
        "Colby Jack": (N(OZ1, 110, 9, 5, 180, 1, 0, 0, 0, 7), ("Block", "Shredded", "Sliced"), (STORE_BRAND, FERNBROOK), []),
        "Muenster": (N(OZ1, 100, 8, 5, 180, 0, 0, 0, 0, 7), ("Sliced",), (FERNBROOK,), []),
        "Smoked Gouda": (N(OZ1, 100, 8, 5, 230, 1, 0, 0, 0, 7), ("Block", "Sliced"), (ALDER,), []),
        "Mexican Blend": (N(OZ1, 110, 9, 5, 190, 1, 0, 0, 0, 6), ("Shredded",), (STORE_BRAND, FERNBROOK), []),
        "Italian Blend": (N(OZ1, 90, 7, 4, 200, 1, 0, 0, 0, 7), ("Shredded",), (STORE_BRAND,), []),
        "American Singles": (N("1 slice (21 g)", 70, 5, 3, 300, 2, 0, 2, 0, 4), ("Sliced",), (STORE_BRAND, FERNBROOK), []),
    }  # fmt: skip
    for name, (n, forms, brands, extra) in types.items():
        for brand in brands:
            organic = brand == CEDAR
            for form in forms:
                title = f"{'Organic ' if organic else ''}{name} Cheese, {form}"
                if name == "American Singles":
                    title = f"{'Organic ' if organic else ''}American Cheese Singles"
                base = 3.29 if brand == STORE_BRAND else 4.29 if brand in (FERNBROOK,) else 5.99
                sizes = [Size("8OZ", "8 oz", cents(base), 8)]
                if form == "Shredded":
                    sizes.append(Size("16OZ", "16 oz", cents(base * 1.8), 16))
                milk = f"{'organic ' if organic else ''}pasteurized {'part-skim ' if 'Part-Skim' in name else ''}milk"
                anti = (
                    ", potato starch and powdered cellulose (to prevent caking), natamycin (a natural mold inhibitor)"
                    if form == "Shredded"
                    else ""
                )
                ing = f"{milk.capitalize()}, cheese culture, salt, enzymes{', annatto (color)' if 'Cheddar' in name and 'White' not in name else ''}{anti}."
                if name == "American Singles":
                    ing = "Cheddar cheese (milk, cheese culture, salt, enzymes), water, cream, sodium citrate, salt, sorbic acid, annatto (color)."
                out.append(
                    food(
                        category=CAT, product_type="cheese", brand=brand, title=title, sizes=sizes, nutrition=n,
                        ingredients=ing, allergens=("milk",),
                        tags=[*extra, *(["organic"] if organic else []), "gluten-free"],
                        claims=("fat-free", "low-fat", "high-protein", "low-sodium", "keto"),
                        specs={"Cheese": name, "Form": form},
                        intro=f"{name} cheese, {form.lower()}. Naturally gluten free.",
                        storage=REFRIGERATED,
                    )
                )  # fmt: skip
    specialty = [
        (ALDER, "Grated Parmesan Cheese", N("1 tbsp (5 g)", 20, 1.5, 1, 75, 0, 0, 0, 0, 2), 4.99, "8OZ", "8 oz", 8, []),
        (ALDER, "Crumbled Feta Cheese", N("1/4 cup (28 g)", 70, 5, 3.5, 320, 1, 0, 0, 0, 4), 3.99, "6OZ", "6 oz", 6, []),
        (ALDER, "Reduced Fat Crumbled Feta Cheese", N("1/4 cup (28 g)", 50, 3, 2, 330, 1, 0, 0, 0, 5), 3.99, "6OZ", "6 oz", 6, ["reduced-fat"]),
        (ALDER, "Fresh Mozzarella Ball", N(OZ1, 70, 5, 3, 85, 0, 0, 0, 0, 5), 4.49, "8OZ", "8 oz", 8, ["whole-milk"]),
        (FERNBROOK, "Part-Skim String Cheese, 12 Sticks", N("1 stick (28 g)", 80, 6, 3.5, 200, 1, 0, 0, 0, 7), 4.99, "12CT", "12 sticks", 12, []),
        (FERNBROOK, "Light String Cheese, 12 Sticks", N("1 stick (28 g)", 50, 2.5, 1.5, 200, 1, 0, 0, 0, 6), 5.29, "12CT", "12 sticks", 12, []),
        (STORE_BRAND, "Part-Skim String Cheese, 24 Sticks", N("1 stick (28 g)", 80, 6, 3.5, 200, 1, 0, 0, 0, 7), 7.99, "24CT", "24 sticks", 24, []),
        (FERNBROOK, "4% Milkfat Small Curd Cottage Cheese", N("1/2 cup (113 g)", 110, 5, 3, 400, 4, 0, 3, 0, 12), 3.49, "16OZ", "16 oz", 16, ["whole-milk"]),
        (FERNBROOK, "2% Low Fat Cottage Cheese", N("1/2 cup (113 g)", 90, 2.5, 1.5, 390, 4, 0, 4, 0, 13), 3.49, "16OZ", "16 oz", 16, []),
        (FERNBROOK, "Nonfat Cottage Cheese", N("1/2 cup (113 g)", 80, 0, 0, 380, 6, 0, 4, 0, 12), 3.49, "16OZ", "16 oz", 16, []),
        (STORE_BRAND, "2% Low Fat No Salt Added Cottage Cheese", N("1/2 cup (113 g)", 90, 2.5, 1.5, 60, 4, 0, 4, 0, 13), 3.29, "16OZ", "16 oz", 16, ["no-salt-added"]),
        (CEDAR, "Organic 4% Cottage Cheese", N("1/2 cup (113 g)", 120, 5, 3, 360, 5, 0, 4, 0, 13), 4.99, "16OZ", "16 oz", 16, ["organic", "whole-milk"]),
        (FERNBROOK, "Original Cream Cheese", N("2 tbsp (29 g)", 90, 9, 5, 90, 1, 0, 1, 0, 2), 2.99, "8OZ", "8 oz brick", 8, []),
        (FERNBROOK, "1/3 Less Fat Neufchatel Cream Cheese", N("2 tbsp (29 g)", 70, 6, 3.5, 115, 1, 0, 1, 0, 2), 2.99, "8OZ", "8 oz brick", 8, ["reduced-fat"]),
        (FERNBROOK, "Fat Free Cream Cheese", N("2 tbsp (29 g)", 30, 0, 0, 200, 2, 0, 1, 0, 4), 2.99, "8OZ", "8 oz brick", 8, []),
        (FERNBROOK, "Whipped Strawberry Cream Cheese", N("2 tbsp (22 g)", 60, 4.5, 3, 75, 4, 0, 3, 3, 1), 3.29, "8OZ", "8 oz tub", 8, []),
        (STORE_BRAND, "Original Cream Cheese", N("2 tbsp (29 g)", 90, 9, 5, 90, 1, 0, 1, 0, 2), 1.99, "8OZ", "8 oz brick", 8, []),
    ]  # fmt: skip
    for brand, title, n, price, code, label, oz, extra in specialty:
        out.append(
            food(
                category=CAT, product_type="cheese", brand=brand, title=title,
                sizes=[Size(code, label, cents(price), oz)], nutrition=n,
                ingredients=f"{'Organic c' if 'organic' in extra else 'C'}ultured pasteurized milk, cream, salt, enzymes"
                + (", strawberries, sugar" if "Strawberry" in title else "") + ".",
                allergens=("milk",), tags=[*extra, "gluten-free"],
                claims=("fat-free", "low-fat", "high-protein", "low-sodium", "no-added-sugar", "keto"),
                specs={"Cheese": title.split(",")[0]},
                intro=f"{title}.", storage=REFRIGERATED,
            )
        )  # fmt: skip
    for title, n in (
        ("Dairy-Free Cheddar Style Shreds", N("1/4 cup (28 g)", 90, 7, 6, 200, 6, 0, 0, 0, 0)),
        ("Dairy-Free Mozzarella Style Shreds", N("1/4 cup (28 g)", 90, 7, 6, 210, 6, 0, 0, 0, 0)),
        (
            "Dairy-Free Almond Milk Cream Cheese Spread",
            N("2 tbsp (28 g)", 80, 7, 1, 150, 3, 0, 0, 0, 2),
        ),
    ):
        almond = "Almond" in title
        out.append(
            food(
                category=CAT, product_type="cheese", brand=SILVERLEAF, title=title,
                sizes=[Size("8OZ", "8 oz", cents(4.99), 8)], nutrition=n,
                ingredients=(
                    "Almondmilk (water, almonds), coconut oil, tapioca starch, sea salt, cultures."
                    if almond else "Water, coconut oil, tapioca starch, potato starch, sea salt, natural flavor, olive extract."
                ),
                allergens=("tree nuts",) if almond else (),
                tags=["dairy-free", "lactose-free", "vegan", "plant-based", "gluten-free"],
                claims=("sugar-free",),
                specs={"Cheese": "Plant-based cheese alternative"},
                intro=f"{title}: a vegan cheese alternative made without milk.",
                storage=REFRIGERATED,
            )
        )  # fmt: skip
    return out


# --- Butter, eggs, cream, kefir -------------------------------------------------------------


def butter_eggs_cream() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    tbsp = "1 tbsp (14 g)"
    butters = [
        (STORE_BRAND, "Salted Butter Sticks", N(tbsp, 100, 11, 7, 90, 0, 0, 0, 0, 0), 4.29, "Cream, salt", []),
        (STORE_BRAND, "Unsalted Butter Sticks", N(tbsp, 100, 11, 7, 0, 0, 0, 0, 0, 0), 4.29, "Cream", ["no-salt-added"]),
        (FERNBROOK, "Salted Sweet Cream Butter", N(tbsp, 100, 11, 7, 90, 0, 0, 0, 0, 0), 5.29, "Sweet cream, salt", []),
        (FERNBROOK, "Unsalted Sweet Cream Butter", N(tbsp, 100, 11, 7, 0, 0, 0, 0, 0, 0), 5.29, "Sweet cream", ["no-salt-added"]),
        (FERNBROOK, "Light Butter with Canola Oil", N(tbsp, 50, 5.5, 2.5, 70, 0, 0, 0, 0, 0), 4.49, "Butter (cream, salt), water, canola oil, tapioca maltodextrin, natural flavor", ["reduced-fat"]),
        (CEDAR, "Organic Salted Butter", N(tbsp, 100, 11, 7, 90, 0, 0, 0, 0, 0), 6.99, "Organic pasteurized cream, salt", ["organic"]),
        (CEDAR, "Organic Unsalted Butter", N(tbsp, 100, 11, 7, 0, 0, 0, 0, 0, 0), 6.99, "Organic pasteurized cream", ["organic", "no-salt-added"]),
        (BRAMBLE, "Grass-Fed Salted Butter", N(tbsp, 100, 11, 8, 100, 0, 0, 0, 0, 0), 5.49, "Pasteurized cream from grass-fed cows, salt", ["grass-fed"]),
        (BRAMBLE, "Grass-Fed Unsalted Butter", N(tbsp, 100, 11, 8, 0, 0, 0, 0, 0, 0), 5.49, "Pasteurized cream from grass-fed cows", ["grass-fed", "no-salt-added"]),
    ]  # fmt: skip
    for brand, title, n, price, ing, extra in butters:
        sizes = (
            [Size("1LB", "1 lb (4 sticks)", cents(price), 16)]
            if "Sticks" in title or brand in (FERNBROOK, CEDAR)
            else [Size("8OZ", "8 oz", cents(price), 8)]
        )
        out.append(food(
            category=CAT, product_type="butter", brand=brand, title=title, sizes=sizes, nutrition=n,
            ingredients=ing + ".", allergens=("milk",), tags=[*extra, "gluten-free"],
            claims=("low-sodium", "keto"), specs={"Salt": "Unsalted" if "Unsalted" in title else "Salted"},
            intro=f"{title}.", storage=REFRIGERATED,
        ))  # fmt: skip
    for brand, title in (
        (SILVERLEAF, "Plant Butter Sticks with Avocado Oil"),
        (ROLLING, "Oat Milk Plant Butter Spread"),
    ):
        out.append(food(
            category=CAT, product_type="butter", brand=brand, title=title,
            sizes=[Size("1LB", "1 lb", cents(5.49), 16)] if "Sticks" in title else [Size("15OZ", "15 oz tub", cents(4.99), 15)],
            nutrition=N(tbsp, 100, 11, 3.5, 80, 0, 0, 0, 0, 0),
            ingredients="Plant oil blend (palm fruit, canola, avocado oils), water, salt, sunflower lecithin, natural flavor.",
            tags=["dairy-free", "lactose-free", "vegan", "plant-based", "gluten-free"],
            claims=("low-sodium",), specs={"Salt": "Salted"},
            intro=f"{title}: a vegan, dairy-free butter alternative for spreading and baking.",
            storage=REFRIGERATED,
        ))  # fmt: skip

    # Eggs
    large = N("1 large egg (50 g)", 70, 5, 1.5, 70, 0, 0, 0, 0, 6)
    xl = N("1 extra large egg (56 g)", 80, 5, 1.5, 80, 0, 0, 0, 0, 7)
    eggs = [  # brand, title, facts, dozen price, tags, how raised
        (STORE_BRAND, "Grade A Large White Eggs", large, 2.49, [], "Conventional"),
        (STORE_BRAND, "Grade A Extra Large White Eggs", xl, 2.89, [], "Conventional"),
        (STORE_BRAND, "Cage-Free Large Brown Eggs", large, 3.99, ["cage-free"], "Cage free"),
        (HENHOUSE, "Cage-Free Large Brown Eggs", large, 4.49, ["cage-free"], "Cage free"),
        (HENHOUSE, "Free-Range Large Brown Eggs", large, 5.29, ["cage-free", "free-range"], "Free range"),
        (HENHOUSE, "Pasture-Raised Large Brown Eggs", large, 6.49, ["cage-free", "free-range", "pasture-raised"], "Pasture raised"),
        (HENHOUSE, "Pasture-Raised Extra Large Eggs", xl, 6.99, ["cage-free", "free-range", "pasture-raised"], "Pasture raised"),
        (CEDAR, "Organic Free-Range Large Brown Eggs", large, 5.99, ["organic", "cage-free", "free-range"], "Free range"),
        (HENHOUSE, "Omega-3 Cage-Free Large Eggs", large, 4.99, ["cage-free"], "Cage free"),
    ]  # fmt: skip
    for brand, title, n, price, tags, raised in eggs:
        out.append(food(
            category=CAT, product_type="eggs", brand=brand, title=title,
            sizes=[Size("12CT", "12 eggs", cents(price), None), Size("18CT", "18 eggs", cents(price * 1.45), None)],
            nutrition=n, ingredients="Eggs." if "Omega" not in title else "Eggs from hens fed a diet with flaxseed.",
            allergens=("egg",), tags=[*tags, "gluten-free", "local"] if brand == HENHOUSE else [*tags, "gluten-free"],
            claims=("keto", "low-sodium"), specs={"Hens": raised},
            intro=f"{title} from {'Texas farms' if brand == HENHOUSE else 'US farms'}. {raised} hens.",
            storage=REFRIGERATED,
        ))  # fmt: skip
    whites = N("3 tbsp (46 g)", 25, 0, 0, 75, 0, 0, 0, 0, 5)
    out.append(food(
        category=CAT, product_type="eggs", brand=STORE_BRAND, title="100% Liquid Egg Whites",
        sizes=[Size("16OZ", "16 oz carton", cents(3.49), 16), Size("32OZ", "32 oz carton", cents(5.99), 32)],
        nutrition=whites, ingredients="Egg whites.", allergens=("egg",), tags=["gluten-free"],
        claims=("fat-free", "keto", "low-sodium"), specs={"Hens": "Conventional"},
        intro="Pasteurized liquid egg whites, ready to pour.", storage=REFRIGERATED,
    ))  # fmt: skip
    out.append(food(
        category=CAT, product_type="eggs", brand=SILVERLEAF, title="Plant-Based Scramble Egg Alternative",
        sizes=[Size("12OZ", "12 fl oz bottle", cents(4.99), 12)],
        nutrition=N("3 tbsp (44 g)", 70, 5, 0, 170, 1, 0, 0, 0, 5),
        ingredients="Water, mung bean protein isolate, canola oil, salt, natural flavors, turmeric, transglutaminase.",
        tags=["vegan", "plant-based", "dairy-free"], claims=("sugar-free",), specs={"Hens": "Egg-free"},
        intro="A vegan, egg-free scramble made from mung bean protein. Contains no eggs.",
        storage=REFRIGERATED,
    ))  # fmt: skip

    # Cream, creamer, sour cream
    creams = [
        (FERNBROOK, "Half & Half", "cream", N("2 tbsp (30 mL)", 40, 3.5, 2, 15, 1, 0, 1, 0, 1), 2.49, "Milk, cream.", ("milk",), []),
        (FERNBROOK, "Fat Free Half & Half", "cream", N("2 tbsp (30 mL)", 20, 0, 0, 30, 3, 0, 2, 1, 1), 2.49, "Nonfat milk, corn syrup, cream, carrageenan, vitamin A palmitate.", ("milk",), []),
        (FERNBROOK, "Heavy Whipping Cream", "cream", N("1 tbsp (15 mL)", 50, 5, 3.5, 5, 0, 0, 0, 0, 0), 3.99, "Cream, gellan gum.", ("milk",), []),
        (CEDAR, "Organic Heavy Whipping Cream", "cream", N("1 tbsp (15 mL)", 50, 5, 3.5, 5, 0, 0, 0, 0, 0), 4.99, "Organic cream.", ("milk",), ["organic"]),
        (STORE_BRAND, "Half & Half", "cream", N("2 tbsp (30 mL)", 40, 3.5, 2, 15, 1, 0, 1, 0, 1), 1.99, "Milk, cream.", ("milk",), []),
        (FERNBROOK, "French Vanilla Coffee Creamer", "creamer", N("1 tbsp (15 mL)", 35, 1.5, 1, 5, 5, 0, 5, 5, 0), 3.99, "Nonfat milk, cane sugar, cream, natural flavor, gellan gum.", ("milk",), []),
        (FERNBROOK, "Hazelnut Coffee Creamer", "creamer", N("1 tbsp (15 mL)", 35, 1.5, 1, 5, 5, 0, 5, 5, 0), 3.99, "Nonfat milk, cane sugar, cream, natural flavor, gellan gum.", ("milk",), []),
        (FERNBROOK, "Zero Sugar French Vanilla Coffee Creamer", "creamer", N("1 tbsp (15 mL)", 15, 1, 0.5, 5, 1, 0, 0, 0, 0), 4.29, "Nonfat milk, cream, natural flavor, sucralose, gellan gum.", ("milk",), []),
        (FERNBROOK, "Zero Sugar Caramel Coffee Creamer", "creamer", N("1 tbsp (15 mL)", 15, 1, 0.5, 5, 1, 0, 0, 0, 0), 4.29, "Nonfat milk, cream, natural flavor, sucralose, gellan gum.", ("milk",), []),
        (ROLLING, "Oat Milk Coffee Creamer, Sweet & Creamy", "creamer", N("1 tbsp (15 mL)", 25, 1, 0, 5, 3, 0, 3, 3, 0), 4.49, "Oatmilk (water, oats), cane sugar, sunflower oil, sea salt, gellan gum.", (), ["dairy-free", "lactose-free", "vegan", "plant-based"]),
        (SILVERLEAF, "Unsweetened Almond Milk Creamer", "creamer", N("1 tbsp (15 mL)", 10, 1, 0, 10, 0, 0, 0, 0, 0), 4.49, "Almondmilk (water, almonds), coconut cream, sunflower lecithin, gellan gum.", ("tree nuts",), ["dairy-free", "lactose-free", "vegan", "plant-based", "unsweetened"]),
        (FERNBROOK, "Sour Cream", "sour-cream", N("2 tbsp (30 g)", 60, 5, 3.5, 15, 1, 0, 1, 0, 1), 2.29, "Cultured cream.", ("milk",), []),
        (FERNBROOK, "Light Sour Cream", "sour-cream", N("2 tbsp (30 g)", 40, 2.5, 1.5, 25, 2, 0, 1, 0, 2), 2.29, "Cultured milk, cream, modified corn starch.", ("milk",), ["reduced-fat"]),
        (FERNBROOK, "Fat Free Sour Cream", "sour-cream", N("2 tbsp (30 g)", 25, 0, 0, 30, 4, 0, 1, 0, 1), 2.29, "Cultured nonfat milk, modified corn starch, gelatin.", ("milk",), []),
        (STORE_BRAND, "Sour Cream", "sour-cream", N("2 tbsp (30 g)", 60, 5, 3.5, 15, 1, 0, 1, 0, 1), 1.79, "Cultured cream.", ("milk",), []),
        (FERNBROOK, "Whipped Cream Topping", "cream", N("2 tbsp (5 g)", 15, 1, 0.5, 0, 1, 0, 1, 1, 0), 3.49, "Cream, sugar, nonfat milk, natural flavor, mono and diglycerides, carrageenan, nitrous oxide (propellant).", ("milk",), []),
    ]  # fmt: skip
    for brand, title, ptype, n, price, ing, allergens, tags in creams:
        out.append(food(
            category=CAT, product_type=ptype, brand=brand, title=title,
            sizes=[Size("16OZ", "16 fl oz" if ptype != "sour-cream" else "16 oz", cents(price), 16)],
            nutrition=n, ingredients=ing, allergens=allergens, tags=[*tags, "gluten-free"],
            claims=("fat-free", "low-fat", "sugar-free", "no-added-sugar", "keto", "low-sodium"),
            specs={}, intro=f"{title}.", storage=REFRIGERATED,
        ))  # fmt: skip

    # Kefir
    kefirs = [
        ("Low Fat Plain Kefir", N(CUP, 110, 2, 1.5, 125, 12, 0, 11, 0, 11), []),
        ("Low Fat Strawberry Kefir", N(CUP, 140, 2, 1.5, 125, 20, 0, 18, 7, 10), []),
        ("Low Fat Blueberry Kefir", N(CUP, 140, 2, 1.5, 125, 20, 0, 18, 7, 10), []),
        ("Whole Milk Plain Kefir", N(CUP, 160, 8, 5, 120, 12, 0, 12, 0, 10), ["whole-milk"]),
        ("Nonfat Unsweetened Kefir", N(CUP, 90, 0, 0, 125, 12, 0, 11, 0, 11), ["unsweetened"]),
    ]
    for title, n, tags in kefirs:
        flavored = "Strawberry" in title or "Blueberry" in title
        for brand, organic in ((NORTHWIND, False), (CEDAR, True)):
            if organic and "Nonfat" in title:
                continue
            t = f"{'Organic ' if organic else ''}{title}"
            out.append(food(
                category=CAT, product_type="kefir", brand=brand, title=t,
                sizes=[Size("32OZ", "32 fl oz", cents(4.49 if not organic else 5.29), 32)], nutrition=n,
                ingredients=f"{'Organic c' if organic else 'C'}ultured {'whole' if 'Whole' in title else 'nonfat' if 'Nonfat' in title else 'low fat'} milk"
                + (", cane sugar, fruit puree" if flavored else "") + ", live and active kefir cultures.",
                allergens=("milk",), tags=[*tags, *(["organic"] if organic else []), "gluten-free"],
                claims=("fat-free", "low-fat", "high-protein", "no-added-sugar"),
                specs={"Style": "Drinkable kefir"},
                intro=f"{t}: a tangy drinkable yogurt with 12 live and active cultures. About 99% lactose free.",
                storage=REFRIGERATED,
            ))  # fmt: skip
    return out


def products() -> list[ProductSeed]:
    return [*milks(), *plant_milks(), *yogurts(), *cheeses(), *butter_eggs_cream()]


__all__ = ["products", "slugify"]
