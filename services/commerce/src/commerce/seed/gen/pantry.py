"""Pantry: cereal, oatmeal, pasta, rice and grains, canned beans, tomatoes, vegetables and
fruit, soups and broth, nut butters, jams, honey and syrup, oils and vinegars, pasta sauce,
condiments, baking, spices, and canned fish.

Contrasting pairs everywhere: regular vs low sodium vs no salt added, sugary vs no sugar
added, natural vs regular peanut butter, whole wheat vs gluten-free vs legume pasta, pure
maple syrup vs sugar-free pancake syrup. Coffee and tea live in beverages.
"""

from __future__ import annotations

from commerce.seed.data import Nutrition, ProductSeed
from commerce.seed.gen.common import PANTRY, STORE_BRAND, Size, cents, food

CAT = "pantry"
SUNFIELD = "Sunfield Mills"  # mainstream cereal and oats
OAKMEADOW = "Oakmeadow Organics"  # organic
IRONPEAK = "Ironpeak Nutrition"  # high protein
FREESTONE = "Freestone Gluten Free"
VALLORA = "Vallora Pasta"
PULSE = "Pulse & Grain"  # chickpea and lentil pasta
LOTUS = "Lotus Field"  # rice, grains, Asian pantry
COPPER = "Copperfield Pantry"  # canned goods
CEDAR = "Cedar Hollow Farms"  # organic
KETTLE = "Kettle & Crock"  # soups and broth
GREENPOT = "Greenpot Organics"  # organic soups and broth
OLDMILL = "Old Mill Nut Co."
PUREGROVE = "Pure Grove"  # natural and organic nut butters, alt flours
ORCHARD = "Orchard Lane Preserves"
WILDFLOWER = "Wildflower Hill Apiary"  # Texas honey
NORTHWOODS = "Northwoods Sugarhouse"  # pure maple syrup
GRIDDLE = "Griddle House"  # pancake syrup
OLIVARA = "Olivara"  # olive oil and vinegar
PALMGROVE = "Palmgrove"  # coconut
NONNA = "Nonna Lucia's"  # premium pasta sauce
BRIGHTSIDE = "Brightside"  # condiments
ROOTWELL = "Rootwell Plant Foods"
GARDEN = "Garden Gate"  # salad dressings
MILLSTONE = "Millstone Flour Co."
MONARCH = "Monarch Sweet"  # sugar-free sweeteners
SUNDAY = "Sunday Oven"  # baking mixes
SAFFRON = "Saffron & Sage Spice Co."
NORTHCAPE = "Northcape Seafood"

AFTER_OPENING = "Store in a cool, dry place. Refrigerate after opening."
VG = ("vegan", "dairy-free")
VGF = ("vegan", "dairy-free", "gluten-free")
SUGAR_CLAIMS = ("sugar-free", "no-added-sugar", "low-sugar")


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


def _pan(
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
    storage: str = PANTRY,
) -> ProductSeed:
    organic = title.startswith("Organic") or " Organic " in title
    text = ingredients[0].upper() + ingredients[1:]
    return food(
        category=CAT, product_type=ptype, brand=brand, title=title, sizes=sizes, nutrition=n,
        ingredients=text, allergens=allergens, tags=[*(["organic"] if organic else []), *tags],
        claims=claims, specs=specs, intro=intro, storage=storage,
    )  # fmt: skip


Row = tuple[str, str, str, Nutrition, list[Size], str, tuple[str, ...], tuple[str, ...], str]


def _rows(rows: list[Row], claims: tuple[str, ...], storage: str = PANTRY) -> list[ProductSeed]:
    """(brand, title, type, facts, sizes, ingredients, allergens, tags, intro) rows."""
    return [
        _pan(brand, title, ptype, n, sizes, ing, intro, allergens=allergens, tags=tags, claims=claims, storage=storage)
        for brand, title, ptype, n, sizes, ing, allergens, tags, intro in rows
    ]  # fmt: skip


# --- Cereal and oatmeal ---------------------------------------------------------------------------

CEREAL_CLAIMS = (
    "sugar-free",
    "no-added-sugar",
    "low-sugar",
    "high-protein",
    "high-fiber",
    "low-sodium",
    "keto",
)
VITAMINS = "vitamin E (mixed tocopherols), iron, zinc, niacinamide, vitamin B6, vitamin A palmitate, folic acid, vitamin D3"


def cereal() -> list[ProductSeed]:
    box = [S("12OZ", "12 oz box", 4.29, 12), S("18OZ", "18 oz family size", 5.99, 18)]
    sbox = [S("12OZ", "12 oz box", 2.99, 12), S("18OZ", "18 oz family size", 3.99, 18)]
    obox = [S("10OZ", "10 oz box", 5.49, 10)]
    pbox = [S("7OZ", "7 oz box", 9.99, 7)]
    gbag = [S("16OZ", "16 oz bag", 5.49, 16)]
    rows: list[Row] = [
        (SUNFIELD, "Toasted Whole Grain Oat Rings", "cereal", N("1 1/2 cups (39 g)", 140, 2.5, 0.5, 190, 29, 4, 2, 2, 5), box,
         f"Whole grain oats, corn starch, sugar, salt, tripotassium phosphate, {VITAMINS}.", (), ("whole-grain", "gluten-free", "vegan"),
         "Crunchy toasted oat rings made from whole grain oats, with just 2 g sugar per serving."),
        (SUNFIELD, "Honey Nut Oat Rings", "cereal", N("1 cup (37 g)", 140, 2, 0, 190, 30, 3, 12, 12, 3), box,
         f"Whole grain oats, sugar, oat bran, corn starch, honey, brown sugar syrup, salt, natural almond flavor, {VITAMINS}.", (), ("whole-grain",),
         "Whole grain oat rings sweetened with honey. 12 g added sugar per serving."),
        (SUNFIELD, "Corn Flakes", "cereal", N("1 1/2 cups (42 g)", 150, 0, 0, 300, 36, 1, 4, 4, 3), box,
         f"Milled corn, sugar, malt flavor, salt, {VITAMINS}.", (), ("vegan",), "Classic toasted corn flakes. Malt flavor comes from barley, so not gluten free."),
        (SUNFIELD, "Frosted Corn Flakes", "cereal", N("1 cup (37 g)", 140, 0, 0, 180, 34, 0, 14, 14, 1), box,
         f"Milled corn, sugar, malt flavor, salt, {VITAMINS}.", (), ("vegan", "kids"), "Sugar-frosted corn flakes. 14 g added sugar per serving."),
        (SUNFIELD, "Crispy Rice Cereal", "cereal", N("1 1/2 cups (40 g)", 150, 0, 0, 190, 36, 0, 4, 4, 2), box,
         f"Rice, sugar, salt, malt flavor, {VITAMINS}.", (), ("vegan",), "Light, crispy toasted rice cereal. Contains barley malt; not gluten free."),
        (SUNFIELD, "Fruity Rainbow Rings", "cereal", N("1 1/3 cups (39 g)", 150, 1.5, 1, 210, 34, 3, 12, 12, 2), box,
         f"Corn flour, sugar, whole grain oat flour, wheat flour, modified corn starch, hydrogenated coconut oil, salt, natural fruit flavors, red 40, yellow 6, blue 1, {VITAMINS}.",
         ("wheat",), ("kids",), "Sweet, fruity multicolored rings for kids. 12 g added sugar per serving."),
        (SUNFIELD, "Cocoa Crunch Puffs", "cereal", N("1 1/3 cups (36 g)", 140, 2, 0, 140, 31, 2, 13, 13, 2), box,
         f"Whole grain corn, sugar, corn meal, cocoa processed with alkali, canola oil, salt, {VITAMINS}.", (), ("kids", "gluten-free"),
         "Chocolatey corn puffs kids love. 13 g added sugar per serving."),
        (SUNFIELD, "Cinnamon Swirl Squares", "cereal", N("1 cup (41 g)", 170, 4, 0.5, 230, 33, 2, 12, 12, 2), box,
         f"Whole grain wheat, sugar, rice flour, canola oil, fructose, cinnamon, salt, soy lecithin, {VITAMINS}.", ("wheat", "soy"), ("kids",),
         "Crunchy cinnamon-sugar squares. 12 g added sugar per serving."),
        (SUNFIELD, "Marshmallow Treasure Oats", "cereal", N("1 cup (36 g)", 140, 1.5, 0, 200, 30, 2, 13, 13, 2), box,
         f"Whole grain oats, marshmallows (sugar, modified corn starch, corn syrup, dextrose, gelatin, artificial colors), sugar, corn syrup, salt, {VITAMINS}.",
         (), ("kids",), "Frosted oat cereal with colorful marshmallows. Contains gelatin, so not vegetarian."),
        (SUNFIELD, "Frosted Shredded Wheat Bites", "cereal", N("25 biscuits (60 g)", 210, 1, 0, 10, 49, 6, 12, 12, 5), box,
         "Whole grain wheat, sugar, gelatin, BHT for freshness.", ("wheat",), ("whole-grain",),
         "Bite-size shredded whole wheat biscuits with a frosted coating. 6 g fiber, 12 g added sugar."),
        (SUNFIELD, "Original Shredded Wheat", "cereal", N("1 1/3 cups (60 g)", 210, 1, 0, 0, 48, 7, 0, 0, 7), box,
         "Whole grain wheat.", ("wheat",), ("whole-grain", "unsweetened", "no-salt-added", "vegan"),
         "Just one ingredient: 100% whole grain wheat, with no sugar and no salt added. 7 g fiber."),
        (SUNFIELD, "Raisin Bran", "cereal", N("1 cup (59 g)", 190, 1, 0, 200, 46, 7, 18, 9, 5), box,
         f"Whole grain wheat, raisins, wheat bran, sugar, brown sugar syrup, salt, malt flavor, {VITAMINS}.", ("wheat",), ("whole-grain", "vegan"),
         "Whole grain wheat and bran flakes with raisins. High in fiber, but 18 g total sugar (9 g added)."),
        (SUNFIELD, "Bran Flakes", "cereal", N("1 cup (40 g)", 140, 1, 0, 210, 32, 7, 6, 5, 4), box,
         f"Whole grain wheat, wheat bran, sugar, malted barley flour, salt, {VITAMINS}.", ("wheat",), ("whole-grain", "vegan"),
         "Toasted whole grain wheat bran flakes with 7 g fiber and 6 g sugar."),
        (SUNFIELD, "High Fiber Bran Buds", "cereal", N("1/2 cup (30 g)", 60, 1, 0, 150, 24, 13, 0, 0, 2), box,
         "Wheat bran, corn bran, modified wheat starch, salt, sucralose, BHT for freshness.", ("wheat",), ("vegan",),
         "Crunchy bran cereal with 13 g fiber and 0 g sugar per serving, sweetened with sucralose."),
        (SUNFIELD, "Granola with Almonds", "granola", N("2/3 cup (55 g)", 240, 7, 1, 120, 40, 3, 13, 12, 5), gbag,
         "Whole grain rolled oats, sugar, almonds, canola oil, rice flour, honey, salt, natural flavor.", ("tree nuts",), ("whole-grain",),
         "Crunchy oat granola clusters with sliced almonds."),
        (OAKMEADOW, "Organic Whole Grain O's", "cereal", N("1 1/4 cups (40 g)", 150, 2, 0, 140, 31, 4, 1, 1, 5), obox,
         "Organic whole grain oat flour, organic corn starch, organic cane sugar, sea salt, vitamin E.", (), ("whole-grain", "gluten-free", "vegan", "non-gmo"),
         "Organic whole grain oat O's with only 1 g sugar per serving."),
        (OAKMEADOW, "Organic Corn Flakes", "cereal", N("1 cup (35 g)", 130, 0.5, 0, 130, 30, 2, 4, 4, 2), obox,
         "Organic corn meal, organic fruit juice concentrate (pear, peach, grape), sea salt.", (), ("gluten-free", "vegan", "non-gmo"),
         "Organic corn flakes sweetened with fruit juice concentrate. Gluten free."),
        (OAKMEADOW, "Organic Ancient Grain Flakes", "cereal", N("1 cup (40 g)", 150, 2, 0, 150, 32, 4, 5, 5, 4), obox,
         "Organic whole grain wheat, organic whole grain spelt, organic quinoa, organic amaranth, organic cane sugar, sea salt.", ("wheat",), ("whole-grain", "vegan", "non-gmo"),
         "Organic flakes made from whole wheat, spelt, quinoa, and amaranth."),
        (OAKMEADOW, "Organic Sprouted Grain Cereal", "cereal", N("1/2 cup (57 g)", 190, 1, 0, 190, 40, 6, 0, 0, 8), obox,
         "Organic sprouted whole wheat, organic sprouted barley, organic sprouted millet, organic sprouted lentils, organic sprouted soybeans, sea salt.",
         ("wheat", "soy"), ("whole-grain", "vegan", "non-gmo"), "Crunchy flourless cereal from sprouted whole grains and legumes, with no added sugar."),
        (OAKMEADOW, "Organic Honey Almond Granola", "granola", N("2/3 cup (55 g)", 260, 10, 1.5, 60, 37, 4, 12, 11, 6), gbag,
         "Organic rolled oats, organic honey, organic almonds, organic sunflower oil, organic cane sugar, sea salt.", ("tree nuts",), ("whole-grain", "non-gmo"),
         "Organic oat granola baked with honey and almonds."),
        (OAKMEADOW, "Organic Grain-Free Granola, No Sugar Added", "granola", N("1/3 cup (30 g)", 170, 14, 3, 40, 8, 3, 1, 0, 5), [S("10OZ", "10 oz bag", 8.99, 10)],
         "Organic pecans, organic coconut, organic almonds, organic pumpkin seeds, organic sunflower seeds, organic coconut oil, cinnamon, sea salt.",
         ("tree nuts",), ("grain-free", "gluten-free", "vegan", "non-gmo"), "Keto-friendly, grain-free granola of nuts, seeds, and coconut with no added sugar."),
        (OAKMEADOW, "Organic Cocoa Rice Crisps", "cereal", N("1 cup (30 g)", 120, 1, 0, 140, 26, 1, 9, 9, 1), obox,
         "Organic brown rice flour, organic cane sugar, organic cocoa, sea salt.", (), ("gluten-free", "vegan", "kids", "non-gmo"),
         "Organic chocolate rice crisps for kids, gluten free."),
        (IRONPEAK, "High Protein Cereal, Frosted", "cereal", N("1 cup (37 g)", 140, 5, 1, 190, 14, 1, 0, 0, 13), pbox,
         "Milk protein isolate, whey protein isolate, allulose, sunflower oil, tapioca starch, natural flavor, salt, monk fruit extract.", ("milk",), ("gluten-free",),
         "Grain-free high protein cereal with 13 g protein and 0 g sugar, sweetened with allulose and monk fruit. Contains milk."),
        (IRONPEAK, "High Protein Cereal, Cocoa", "cereal", N("1 cup (37 g)", 140, 5, 1.5, 200, 15, 2, 0, 0, 13), pbox,
         "Milk protein isolate, whey protein isolate, allulose, cocoa, sunflower oil, tapioca starch, salt, monk fruit extract.", ("milk",), ("gluten-free",),
         "Cocoa high protein cereal with 13 g protein and 0 g sugar."),
        (IRONPEAK, "High Protein Cereal, Cinnamon", "cereal", N("1 cup (37 g)", 140, 5, 1, 190, 14, 1, 0, 0, 13), pbox,
         "Milk protein isolate, whey protein isolate, allulose, sunflower oil, cinnamon, tapioca starch, salt, monk fruit extract.", ("milk",), ("gluten-free",),
         "Cinnamon high protein cereal with 13 g protein and 0 g sugar."),
        (IRONPEAK, "Protein Granola, Dark Chocolate", "granola", N("1/2 cup (45 g)", 200, 8, 2, 150, 23, 5, 6, 5, 10), [S("11OZ", "11 oz bag", 6.99, 11)],
         "Whole grain oats, soy protein isolate, whey protein (milk), chicory root fiber, dark chocolate (sugar, cocoa), almonds, sunflower oil, cane sugar, salt.",
         ("soy", "milk", "tree nuts"), ("whole-grain",), "Crunchy granola with 10 g protein and 5 g fiber."),
        (STORE_BRAND, "Toasted Oat Rings", "cereal", N("1 1/2 cups (39 g)", 140, 2.5, 0.5, 190, 29, 4, 2, 2, 5), sbox,
         f"Whole grain oats, corn starch, sugar, salt, tripotassium phosphate, {VITAMINS}.", (), ("whole-grain", "gluten-free", "vegan"),
         "Toasted whole grain oat rings with 2 g sugar per serving."),
        (STORE_BRAND, "Frosted Corn Flakes", "cereal", N("1 cup (37 g)", 140, 0, 0, 180, 34, 0, 14, 14, 1), sbox,
         f"Milled corn, sugar, malt flavor, salt, {VITAMINS}.", (), ("vegan", "kids"), "Sugar-frosted corn flakes."),
        (STORE_BRAND, "Crispy Rice Cereal", "cereal", N("1 1/4 cups (33 g)", 130, 0, 0, 170, 29, 0, 3, 3, 2), sbox,
         f"Rice, sugar, salt, malt flavor, {VITAMINS}.", (), ("vegan",), "Toasted crispy rice cereal."),
        (STORE_BRAND, "Raisin Bran", "cereal", N("1 cup (59 g)", 190, 1, 0, 200, 46, 7, 18, 9, 5), sbox,
         f"Whole grain wheat, raisins, wheat bran, sugar, brown sugar syrup, salt, malt flavor, {VITAMINS}.", ("wheat",), ("whole-grain", "vegan"),
         "Bran flakes with raisins. 7 g fiber."),
        (STORE_BRAND, "Fruity Rainbow Rings", "cereal", N("1 1/3 cups (39 g)", 150, 1.5, 1, 210, 34, 3, 12, 12, 2), sbox,
         f"Corn flour, sugar, whole grain oat flour, wheat flour, hydrogenated coconut oil, salt, natural fruit flavors, red 40, yellow 6, blue 1, {VITAMINS}.",
         ("wheat",), ("kids",), "Sweet, fruity rings for kids."),
        (STORE_BRAND, "Honey Oat Clusters Cereal", "cereal", N("3/4 cup (30 g)", 120, 1.5, 0, 140, 24, 2, 6, 6, 2), sbox,
         f"Whole grain wheat, corn, sugar, whole grain oats, honey, canola oil, salt, {VITAMINS}.", ("wheat",), ("whole-grain",),
         "Crunchy flakes with honey-sweetened oat clusters."),
        (STORE_BRAND, "Frosted Shredded Wheat", "cereal", N("25 biscuits (60 g)", 210, 1, 0, 10, 49, 6, 12, 12, 5), sbox,
         "Whole grain wheat, sugar, gelatin, BHT for freshness.", ("wheat",), ("whole-grain",), "Frosted bite-size shredded whole wheat."),
        (STORE_BRAND, "Low Fat Granola with Raisins", "granola", N("2/3 cup (55 g)", 210, 3, 0.5, 110, 44, 3, 15, 11, 4), [S("16OZ", "16 oz bag", 3.99, 16)],
         "Whole grain rolled oats, sugar, raisins, rice flour, corn syrup, canola oil, salt.", (), ("whole-grain", "vegan"),
         "Low fat oat granola with raisins, 3 g fat per serving."),
    ]  # fmt: skip
    return _rows(rows, CEREAL_CLAIMS)


def oatmeal() -> list[ProductSeed]:
    rolled = N("1/2 cup dry (40 g)", 150, 3, 0.5, 0, 27, 4, 1, 0, 5)
    oats = [S("18OZ", "18 oz canister", 3.49, 18), S("42OZ", "42 oz canister", 5.99, 42)]
    pk10 = [S("10CT", "10 packets", 3.99)]
    rows: list[Row] = [
        (SUNFIELD, "Old Fashioned Rolled Oats", "oatmeal", rolled, oats, "Whole grain rolled oats.", (), ("whole-grain", "unsweetened", *VG),
         "100% whole grain old fashioned rolled oats with no sugar or salt added. Cooks in 5 minutes."),
        (SUNFIELD, "Quick 1-Minute Oats", "oatmeal", rolled, oats, "Whole grain rolled oats.", (), ("whole-grain", "unsweetened", *VG),
         "Thin-cut whole grain oats that cook in one minute. No sugar or salt added."),
        (SUNFIELD, "Steel Cut Oats", "oatmeal", N("1/4 cup dry (40 g)", 150, 2.5, 0.5, 0, 27, 4, 1, 0, 5), [S("24OZ", "24 oz canister", 4.99, 24)],
         "Whole grain steel cut oats.", (), ("whole-grain", "unsweetened", *VG), "Chewy, nutty steel cut oats. Cooks in 20 to 30 minutes."),
        (SUNFIELD, "Instant Oatmeal, Original", "oatmeal", N("1 packet (28 g)", 100, 2, 0, 75, 19, 3, 0, 0, 4), pk10,
         "Whole grain rolled oats, salt, calcium carbonate.", (), ("whole-grain", "unsweetened", *VG), "Plain instant oatmeal packets with no sugar added."),
        (SUNFIELD, "Instant Oatmeal, Maple & Brown Sugar", "oatmeal", N("1 packet (43 g)", 160, 2, 0, 260, 33, 3, 12, 12, 4), pk10,
         "Whole grain rolled oats, sugar, natural and artificial flavor, salt, calcium carbonate, guar gum.", (), ("whole-grain", *VG),
         "Instant oatmeal flavored with maple and brown sugar. 12 g added sugar per packet."),
        (SUNFIELD, "Instant Oatmeal, Lower Sugar Maple & Brown Sugar", "oatmeal", N("1 packet (33 g)", 120, 2, 0, 190, 24, 3, 4, 4, 4), pk10,
         "Whole grain rolled oats, sugar, natural flavor, salt, calcium carbonate, guar gum, stevia leaf extract.", (), ("whole-grain", *VG),
         "Maple and brown sugar instant oatmeal with 4 g sugar per packet, about 65% less than our regular."),
        (SUNFIELD, "Instant Oatmeal, Apples & Cinnamon", "oatmeal", N("1 packet (43 g)", 160, 2, 0, 160, 33, 3, 12, 11, 3), pk10,
         "Whole grain rolled oats, sugar, dehydrated apples, cinnamon, salt, natural flavor, calcium carbonate.", (), ("whole-grain", *VG),
         "Instant oatmeal with dried apples and cinnamon."),
        (IRONPEAK, "High Protein Instant Oatmeal, Maple", "oatmeal", N("1 packet (60 g)", 220, 3.5, 1, 200, 33, 4, 8, 7, 12), [S("6CT", "6 packets", 5.99)],
         "Whole grain rolled oats, whey protein concentrate (milk), cane sugar, natural maple flavor, salt.", ("milk",), ("whole-grain",),
         "Maple instant oatmeal with 12 g protein per packet from whey. Contains milk."),
        (FREESTONE, "Gluten-Free Old Fashioned Oats", "oatmeal", rolled, [S("24OZ", "24 oz bag", 5.99, 24)], "Whole grain rolled oats (certified gluten free).",
         (), ("whole-grain", "unsweetened", "gluten-free", *VG), "Certified gluten-free rolled oats, grown and milled away from wheat."),
        (OAKMEADOW, "Organic Old Fashioned Rolled Oats", "oatmeal", rolled, [S("18OZ", "18 oz canister", 4.49, 18)], "Organic whole grain rolled oats.",
         (), ("whole-grain", "unsweetened", "non-gmo", *VG), "Organic whole grain rolled oats with nothing added."),
        (OAKMEADOW, "Organic Instant Oatmeal, Original", "oatmeal", N("1 packet (28 g)", 100, 2, 0, 0, 19, 3, 0, 0, 4), [S("8CT", "8 packets", 4.49)],
         "Organic whole grain rolled oats.", (), ("whole-grain", "unsweetened", "non-gmo", *VG), "Organic plain instant oatmeal with no sugar or salt added."),
        (STORE_BRAND, "Old Fashioned Oats", "oatmeal", rolled, [S("18OZ", "18 oz canister", 2.49, 18), S("42OZ", "42 oz canister", 4.29, 42)],
         "Whole grain rolled oats.", (), ("whole-grain", "unsweetened", *VG), "Whole grain old fashioned oats."),
        (STORE_BRAND, "Instant Oatmeal Variety Pack", "oatmeal", N("1 packet (43 g)", 160, 2, 0, 240, 33, 3, 12, 12, 4), [S("10CT", "10 packets", 2.99)],
         "Whole grain rolled oats, sugar, dehydrated apples, cinnamon, natural and artificial flavors, salt, calcium carbonate.", (), ("whole-grain", *VG),
         "Maple & brown sugar, apples & cinnamon, and cinnamon spice instant oatmeal."),
    ]  # fmt: skip
    return _rows(rows, ("no-added-sugar", "low-sugar", "high-protein", "high-fiber", "low-sodium"))


# --- Pasta, rice, and grains --------------------------------------------------------------------

SEMOLINA = "semolina (wheat), durum wheat flour, niacin, iron (ferrous sulfate), thiamine mononitrate, riboflavin, folic acid"
OZ2 = "2 oz dry (56 g)"
REG_PASTA = N(OZ2, 200, 1, 0, 0, 42, 2, 2, 0, 7)
WW_PASTA = N(OZ2, 180, 1.5, 0, 0, 39, 6, 2, 0, 8)
GF_PASTA = N(OZ2, 200, 1, 0, 0, 44, 2, 0, 0, 4)


def pasta_rice() -> list[ProductSeed]:
    rows: list[Row] = []
    for brand, shapes, price in (
        (
            VALLORA,
            (
                "Spaghetti",
                "Penne Rigate",
                "Rotini",
                "Fettuccine",
                "Angel Hair",
                "Farfalle",
                "Elbow Macaroni",
            ),
            1.79,
        ),
        (STORE_BRAND, ("Spaghetti", "Penne Rigate", "Elbow Macaroni", "Thin Spaghetti"), 0.99),
    ):
        for shape in shapes:
            rows.append((brand, shape, "pasta", REG_PASTA, [S("16OZ", "16 oz box", price, 16)], SEMOLINA, ("wheat",), VG,
                         f"Enriched durum wheat {shape.lower()}. Cooks in about 10 minutes."))  # fmt: skip
    ww_lines: tuple[tuple[str, tuple[str, ...], float], ...] = (
        (VALLORA, ("Spaghetti", "Penne", "Rotini"), 2.29),
        (STORE_BRAND, ("Spaghetti",), 1.49),
    )
    for brand, ww_shapes, price in ww_lines:
        for shape in ww_shapes:
            rows.append((brand, f"100% Whole Wheat {shape}", "pasta", WW_PASTA, [S("16OZ", "16 oz box", price, 16)], "Whole durum wheat flour.",
                         ("wheat",), (*VG, "whole-grain"), f"100% whole wheat {shape.lower()} with 6 g fiber per serving."))  # fmt: skip
    for shape in ("Spaghetti", "Penne", "Elbows"):
        rows.append((FREESTONE, f"Gluten-Free {shape}", "pasta", GF_PASTA, [S("12OZ", "12 oz box", 2.99, 12)], "Brown rice flour, corn flour, quinoa flour.",
                     (), VGF, f"Gluten-free {shape.lower()} made from brown rice, corn, and quinoa."))  # fmt: skip
    legume = [
        (
            "Chickpea Rotini",
            N(OZ2, 190, 3.5, 0, 60, 32, 8, 5, 0, 11),
            "Chickpeas, pea protein, tapioca, xanthan gum.",
        ),
        (
            "Chickpea Penne",
            N(OZ2, 190, 3.5, 0, 60, 32, 8, 5, 0, 11),
            "Chickpeas, pea protein, tapioca, xanthan gum.",
        ),
        ("Red Lentil Penne", N(OZ2, 180, 1, 0, 0, 32, 6, 1, 0, 13), "Red lentil flour."),
        ("Red Lentil Rotini", N(OZ2, 180, 1, 0, 0, 32, 6, 1, 0, 13), "Red lentil flour."),
    ]
    for title, n, ing in legume:
        rows.append((PULSE, title, "pasta", n, [S("8OZ", "8 oz box", 2.99, 8)], ing, (), (*VGF, "non-gmo", "plant-based"),
                     f"High-protein, gluten-free {title.lower()} made from legumes, with {n.protein_g:g} g protein and {n.fiber_g:g} g fiber per serving."))  # fmt: skip
    rows += [
        (OAKMEADOW, "Organic Spaghetti", "pasta", REG_PASTA, [S("16OZ", "16 oz box", 2.49, 16)], "Organic durum wheat semolina.", ("wheat",), (*VG, "non-gmo"),
         "Bronze-cut organic durum wheat spaghetti."),
        (OAKMEADOW, "Organic Whole Wheat Penne", "pasta", WW_PASTA, [S("16OZ", "16 oz box", 2.79, 16)], "Organic whole durum wheat flour.", ("wheat",),
         (*VG, "whole-grain", "non-gmo"), "Organic 100% whole wheat penne."),
        (STORE_BRAND, "Wide Egg Noodles", "pasta", N(OZ2, 210, 2.5, 0.5, 20, 40, 2, 1, 0, 8), [S("12OZ", "12 oz bag", 1.79, 12)],
         f"{SEMOLINA}, egg yolks.", ("wheat", "egg"), ("dairy-free",), "Wide egg noodles for soups and stroganoff. Contains egg."),
        (STORE_BRAND, "Macaroni & Cheese Dinner", "mac-and-cheese", N("2.5 oz (70 g)", 250, 2.5, 1.5, 560, 48, 1, 6, 0, 9), [S("7OZ", "7.25 oz box", 0.99, 7.25), S("5PK", "5 x 7.25 oz boxes", 4.49, 36)],
         f"Enriched macaroni ({SEMOLINA}), cheese sauce mix (whey, milkfat, milk protein concentrate, salt, sodium phosphate, citric acid, yellow 5, yellow 6).",
         ("wheat", "milk"), (), "Boxed macaroni and cheese dinner. Prepare with butter and milk."),
        (OAKMEADOW, "Organic White Cheddar Shells", "mac-and-cheese", N("2.5 oz (71 g)", 260, 3.5, 2, 510, 47, 2, 3, 0, 10), [S("6OZ", "6 oz box", 2.29, 6)],
         "Organic wheat pasta, organic white cheddar cheese (cultured pasteurized organic milk, salt, enzymes), organic whey, salt.", ("wheat", "milk"), ("non-gmo",),
         "Organic pasta shells with real white cheddar and no artificial colors."),
        (FREESTONE, "Gluten-Free Macaroni & Cheese", "mac-and-cheese", N("2.5 oz (71 g)", 260, 3, 1.5, 560, 51, 1, 3, 0, 6), [S("6OZ", "6 oz box", 3.29, 6)],
         "Rice pasta (brown rice flour, rice flour), cheese sauce mix (whey, cheddar cheese (milk), salt, annatto).", ("milk",), ("gluten-free",),
         "Gluten-free rice pasta with cheddar cheese sauce."),
        # Rice and grains
        (STORE_BRAND, "Long Grain White Rice", "rice", N("1/4 cup dry (45 g)", 160, 0, 0, 0, 36, 0, 0, 0, 3), [S("2LB", "2 lb bag", 1.99, 32), S("5LB", "5 lb bag", 3.99, 80)],
         "Enriched long grain rice (rice, iron, niacin, thiamine mononitrate, folic acid).", (), VGF, "Fluffy enriched long grain white rice."),
        (STORE_BRAND, "Long Grain Brown Rice", "rice", N("1/4 cup dry (45 g)", 170, 1.5, 0, 0, 35, 2, 0, 0, 4), [S("2LB", "2 lb bag", 2.29, 32)],
         "Whole grain brown rice.", (), (*VGF, "whole-grain"), "Whole grain long grain brown rice."),
        (STORE_BRAND, "Instant White Rice", "rice", N("1/2 cup dry (48 g)", 170, 0, 0, 0, 38, 0, 0, 0, 3), [S("14OZ", "14 oz box", 2.29, 14)],
         "Precooked long grain rice, iron, niacin, thiamine mononitrate, folic acid.", (), VGF, "Instant rice that's ready in 5 minutes."),
        (STORE_BRAND, "Spanish Rice Mix", "rice", N("1/3 cup dry (56 g), about 1 cup prepared", 200, 1, 0, 780, 43, 1, 2, 1, 5), [S("6OZ", "6.8 oz box", 1.29, 6.8)],
         "Enriched long grain rice, salt, tomato powder, onion, sugar, garlic, spices, yeast extract.", (), VGF,
         "Seasoned Spanish-style rice mix. High in sodium (780 mg per serving)."),
        (LOTUS, "Thai Jasmine Rice", "rice", N("1/4 cup dry (45 g)", 160, 0, 0, 0, 36, 0, 0, 0, 3), [S("2LB", "2 lb bag", 3.49, 32), S("5LB", "5 lb bag", 6.99, 80)],
         "Jasmine rice.", (), VGF, "Fragrant long grain Thai jasmine rice."),
        (LOTUS, "Aged Basmati Rice", "rice", N("1/4 cup dry (45 g)", 160, 0, 0, 0, 36, 1, 0, 0, 4), [S("2LB", "2 lb bag", 4.49, 32)],
         "Basmati rice.", (), VGF, "Extra-long grain aged basmati rice from India."),
        (LOTUS, "Organic Brown Jasmine Rice", "rice", N("1/4 cup dry (45 g)", 170, 1.5, 0, 0, 35, 2, 0, 0, 4), [S("2LB", "2 lb bag", 4.99, 32)],
         "Organic brown jasmine rice.", (), (*VGF, "whole-grain", "non-gmo"), "Organic whole grain brown jasmine rice."),
        (LOTUS, "90-Second Brown Rice", "rice", N("1 cup (140 g)", 220, 4, 0.5, 10, 39, 2, 0, 0, 5), [S("8OZ", "8.8 oz pouch", 1.99, 8.8)],
         "Cooked whole grain brown rice, water, sunflower oil.", (), (*VGF, "whole-grain"), "Fully cooked brown rice pouch that microwaves in 90 seconds."),
        (LOTUS, "Organic White Quinoa", "grains", N("1/4 cup dry (45 g)", 170, 2.5, 0, 0, 30, 3, 1, 0, 6), [S("12OZ", "12 oz bag", 5.49, 12)],
         "Organic white quinoa.", (), (*VGF, "whole-grain", "non-gmo"), "Pre-rinsed organic white quinoa, a gluten-free whole grain."),
        (STORE_BRAND, "Tri-Color Quinoa", "grains", N("1/4 cup dry (45 g)", 170, 2.5, 0, 0, 30, 3, 1, 0, 6), [S("16OZ", "16 oz bag", 4.99, 16)],
         "White quinoa, red quinoa, black quinoa.", (), (*VGF, "whole-grain"), "A mix of white, red, and black quinoa."),
        (STORE_BRAND, "Pearled Couscous", "grains", N("1/3 cup dry (56 g)", 200, 1, 0, 0, 40, 2, 0, 0, 7), [S("8OZ", "8.8 oz box", 2.29, 8.8)],
         "Enriched wheat flour.", ("wheat",), VG, "Toasted Israeli-style pearled couscous. Contains wheat."),
        (STORE_BRAND, "Pearl Barley", "grains", N("1/4 cup dry (48 g)", 170, 0.5, 0, 5, 38, 8, 0, 0, 5), [S("16OZ", "16 oz bag", 1.99, 16)],
         "Pearled barley.", (), VG, "Quick-cooking pearl barley for soups, with 8 g fiber. Barley contains gluten."),
        (OAKMEADOW, "Organic Farro", "grains", N("1/4 cup dry (47 g)", 170, 1, 0, 0, 34, 5, 0, 0, 6), [S("16OZ", "16 oz bag", 5.99, 16)],
         "Organic semi-pearled farro (wheat).", ("wheat",), (*VG, "non-gmo"), "Nutty organic Italian farro, an ancient wheat."),
    ]  # fmt: skip
    return _rows(rows, ("high-protein", "high-fiber", "low-sodium", "sugar-free"))


# --- Canned beans, tomatoes, vegetables, fruit ------------------------------------------------------

HALF = "1/2 cup (130 g)"
BEANS = {  # name: (facts at regular sodium, bean ingredient)
    "Black Beans": (N(HALF, 110, 0.5, 0, 460, 20, 7, 1, 0, 7), "black beans"),
    "Pinto Beans": (N(HALF, 110, 0.5, 0, 450, 19, 6, 0, 0, 6), "pinto beans"),
    "Dark Red Kidney Beans": (N(HALF, 110, 0, 0, 390, 20, 7, 1, 0, 8), "dark red kidney beans"),
    "Garbanzo Beans (Chickpeas)": (N(HALF, 120, 2, 0, 380, 20, 5, 0, 0, 6), "garbanzo beans"),
    "Great Northern Beans": (N(HALF, 100, 0, 0, 420, 19, 6, 1, 0, 7), "great northern beans"),
    "Cannellini Beans": (N(HALF, 110, 0, 0, 400, 19, 6, 1, 0, 7), "cannellini beans"),
}  # fmt: skip
BEAN_CLAIMS = ("low-sodium", "high-fiber", "no-added-sugar")


def _with_sodium(n: Nutrition, sodium: int) -> Nutrition:
    return Nutrition(n.serving_size, n.calories, n.total_fat_g, n.saturated_fat_g, sodium, n.total_carbs_g,
                     n.fiber_g, n.total_sugars_g, n.added_sugars_g, n.protein_g)  # fmt: skip


def canned() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    can = [S("15OZ", "15.5 oz can", 1.19, 15.5)]
    scan = [S("15OZ", "15 oz can", 0.99, 15), S("4PK", "4 x 15 oz cans", 3.79, 60)]
    ocan = [S("15OZ", "15 oz can", 1.99, 15)]
    lines = [  # brand, names, title prefix, sodium (None: regular), salt ingredient, sizes, intro note
        (COPPER, list(BEANS), "", None, "salt", can, "Seasoned with salt."),
        (COPPER, ["Black Beans", "Pinto Beans", "Dark Red Kidney Beans", "Garbanzo Beans (Chickpeas)"], "Low Sodium ", "quarter", "sea salt", can,
         "Low sodium: about 75% less sodium than our regular canned beans."),
        (STORE_BRAND, ["Black Beans", "Pinto Beans", "Dark Red Kidney Beans", "Garbanzo Beans (Chickpeas)"], "", None, "salt", scan, "Seasoned with salt."),
        (STORE_BRAND, ["Black Beans", "Dark Red Kidney Beans", "Garbanzo Beans (Chickpeas)"], "No Salt Added ", "none", "", scan,
         "No salt added; only the sodium naturally present in beans."),
        (CEDAR, ["Black Beans", "Pinto Beans", "Garbanzo Beans (Chickpeas)"], "Organic ", "organic", "sea salt", ocan, "Seasoned with a little sea salt."),
        (CEDAR, ["Black Beans"], "Organic No Salt Added ", "none", "", ocan, "No salt added; only naturally occurring sodium."),
    ]  # fmt: skip
    for brand, names, prefix, level, salt, sizes, note in lines:
        for name in names:
            base, bean = BEANS[name]
            sodium = {
                None: base.sodium_mg,
                "quarter": round(base.sodium_mg * 0.25),
                "none": 15,
                "organic": 290,
            }[level]
            organic = "Organic" in prefix
            ing = f"{'Organic ' if organic else 'Prepared '}{bean}, water{', ' + salt if salt else ''}{', kombu seaweed' if organic else ', calcium chloride (firming agent)'}."
            tags = [
                *VGF,
                *(["no-salt-added"] if level == "none" else []),
                *(["non-gmo"] if organic else []),
            ]
            label = f"{prefix}{name.lower()}"
            out.append(_pan(
                brand, f"{prefix}{name}", "canned-beans", _with_sodium(base, sodium), sizes, ing,
                f"{label[0].upper()}{label[1:]}, fully cooked and ready to heat. {sodium} mg sodium per serving. {note}",
                tags=tags, specs={"Sodium level": {None: "Regular", "quarter": "Low sodium", "none": "No salt added", "organic": "Regular (sea salt)"}[level]},
                claims=BEAN_CLAIMS,
            ))  # fmt: skip
    rows: list[Row] = [
        (COPPER, "Traditional Refried Beans", "canned-beans", N(HALF, 130, 2, 1, 510, 19, 6, 1, 0, 7), [S("16OZ", "16 oz can", 1.49, 16)],
         "Cooked pinto beans, water, lard, salt, chili pepper, garlic powder.", (), ("gluten-free",),
         "Creamy refried pinto beans made the traditional way with lard. Not vegetarian."),
        (COPPER, "Vegetarian Refried Beans", "canned-beans", N(HALF, 110, 0.5, 0, 490, 18, 6, 1, 0, 6), [S("16OZ", "16 oz can", 1.49, 16)],
         "Cooked pinto beans, water, salt, canola oil, chili pepper, garlic powder, onion powder.", (), VGF, "Refried pinto beans made without lard. Vegan."),
        (COPPER, "Homestyle Baked Beans with Bacon", "canned-beans", N(HALF, 150, 1, 0.5, 550, 29, 5, 12, 9, 6), [S("28OZ", "28 oz can", 2.99, 28)],
         "Prepared navy beans, water, brown sugar, sugar, bacon, tomato paste, molasses, salt, corn starch, mustard, onion, spices.", (), ("gluten-free", "dairy-free"),
         "Slow-cooked baked beans with brown sugar and bacon. 9 g added sugar per serving."),
        (COPPER, "Vegetarian Baked Beans", "canned-beans", N(HALF, 140, 0.5, 0, 550, 29, 5, 12, 9, 6), [S("28OZ", "28 oz can", 2.99, 28)],
         "Prepared navy beans, water, brown sugar, sugar, tomato paste, molasses, salt, corn starch, mustard, onion, spices.", (), VGF,
         "Sweet baked beans in a tomato-molasses sauce, made without meat."),
    ]  # fmt: skip
    out += _rows(rows, BEAN_CLAIMS)
    tom = N("1/2 cup (121 g)", 25, 0, 0, 220, 5, 1, 3, 0, 1)
    sauce = N("1/4 cup (62 g)", 20, 0, 0, 330, 4, 1, 2, 0, 1)
    rows = [
        (COPPER, "Diced Tomatoes", "canned-tomatoes", tom, can, "Tomatoes, tomato juice, salt, calcium chloride, citric acid.", (), VGF, "Diced tomatoes in juice."),
        (COPPER, "No Salt Added Diced Tomatoes", "canned-tomatoes", _with_sodium(tom, 20), can, "Tomatoes, tomato juice, calcium chloride, citric acid.", (),
         (*VGF, "no-salt-added"), "Diced tomatoes in juice with no salt added, 20 mg sodium per serving."),
        (COPPER, "Crushed Tomatoes", "canned-tomatoes", N("1/4 cup (61 g)", 20, 0, 0, 180, 4, 1, 2, 0, 1), [S("28OZ", "28 oz can", 2.29, 28)],
         "Tomatoes, tomato puree, salt, citric acid.", (), VGF, "Thick crushed tomatoes for sauces and chili."),
        (COPPER, "Tomato Sauce", "canned-tomatoes", sauce, [S("8OZ", "8 oz can", 0.99, 8), S("15OZ", "15 oz can", 1.29, 15)],
         "Tomato puree (water, tomato paste), salt, citric acid, spices.", (), VGF, "Smooth, lightly seasoned tomato sauce."),
        (COPPER, "No Salt Added Tomato Sauce", "canned-tomatoes", _with_sodium(sauce, 15), [S("8OZ", "8 oz can", 0.99, 8)],
         "Tomato puree (water, tomato paste), citric acid.", (), (*VGF, "no-salt-added"), "Tomato sauce with no salt added."),
        (COPPER, "Tomato Paste", "canned-tomatoes", N("2 tbsp (33 g)", 30, 0, 0, 20, 6, 1, 4, 0, 1), [S("6OZ", "6 oz can", 0.99, 6)],
         "Tomato paste.", (), (*VGF, "no-salt-added"), "Rich tomato paste with no salt added."),
        (COPPER, "Whole Peeled Tomatoes", "canned-tomatoes", N("1/2 cup (121 g)", 25, 0, 0, 190, 4, 1, 3, 0, 1), [S("28OZ", "28 oz can", 2.29, 28)],
         "Tomatoes, tomato juice, salt, calcium chloride, citric acid.", (), VGF, "Whole peeled plum tomatoes in juice."),
        (COPPER, "Diced Tomatoes with Green Chilies", "canned-tomatoes", N("1/2 cup (121 g)", 20, 0, 0, 380, 4, 1, 2, 0, 1), [S("10OZ", "10 oz can", 1.19, 10)],
         "Tomatoes, water, green chile peppers, salt, calcium chloride, citric acid, spice.", (), VGF, "Diced tomatoes with zesty green chilies for queso and Tex-Mex."),
        (CEDAR, "Organic Diced Tomatoes", "canned-tomatoes", tom, ocan, "Organic tomatoes, organic tomato juice, sea salt, citric acid.", (), (*VGF, "non-gmo"),
         "Organic diced tomatoes in juice."),
        (CEDAR, "Organic Fire Roasted Diced Tomatoes", "canned-tomatoes", _with_sodium(tom, 250), ocan, "Organic fire roasted tomatoes, organic tomato juice, sea salt, citric acid.",
         (), (*VGF, "non-gmo"), "Organic tomatoes roasted over an open flame, then diced."),
        (CEDAR, "Organic Crushed Tomatoes", "canned-tomatoes", N("1/4 cup (61 g)", 20, 0, 0, 150, 4, 1, 2, 0, 1), [S("28OZ", "28 oz can", 3.49, 28)],
         "Organic tomatoes, organic tomato puree, sea salt, citric acid.", (), (*VGF, "non-gmo"), "Organic crushed tomatoes."),
        (STORE_BRAND, "Diced Tomatoes", "canned-tomatoes", tom, scan, "Tomatoes, tomato juice, salt, calcium chloride, citric acid.", (), VGF, "Diced tomatoes in juice."),
        (STORE_BRAND, "Tomato Sauce", "canned-tomatoes", sauce, [S("8OZ", "8 oz can", 0.99, 8)], "Tomato puree (water, tomato paste), salt, citric acid.", (), VGF,
         "Smooth tomato sauce."),
        # Canned vegetables and fruit
        (STORE_BRAND, "Whole Kernel Sweet Corn", "canned-vegetables", N("1/2 cup (125 g)", 70, 0.5, 0, 210, 15, 2, 5, 1, 2), scan,
         "Corn, water, salt, sugar.", (), VGF, "Canned sweet corn with added salt and a little sugar."),
        (STORE_BRAND, "No Salt Added Whole Kernel Corn", "canned-vegetables", N("1/2 cup (125 g)", 70, 0.5, 0, 10, 15, 2, 4, 0, 2), scan,
         "Corn, water.", (), (*VGF, "no-salt-added"), "Canned sweet corn with no salt or sugar added."),
        (STORE_BRAND, "Cut Green Beans", "canned-vegetables", N("1/2 cup (120 g)", 20, 0, 0, 380, 4, 2, 2, 0, 1), scan,
         "Green beans, water, salt.", (), VGF, "Canned cut green beans with salt."),
        (STORE_BRAND, "No Salt Added Cut Green Beans", "canned-vegetables", N("1/2 cup (120 g)", 20, 0, 0, 10, 4, 2, 2, 0, 1), scan,
         "Green beans, water.", (), (*VGF, "no-salt-added"), "Canned green beans with no salt added."),
        (COPPER, "Sliced Peaches in Heavy Syrup", "canned-fruit", N("1/2 cup (126 g)", 100, 0, 0, 10, 25, 1, 23, 15, 1), [S("15OZ", "15.25 oz can", 1.69, 15.25)],
         "Peaches, water, high fructose corn syrup, corn syrup.", (), VGF, "Yellow cling peaches in heavy syrup. 15 g added sugar per serving."),
        (COPPER, "Sliced Peaches in 100% Juice", "canned-fruit", N("1/2 cup (126 g)", 60, 0, 0, 10, 15, 1, 13, 0, 1), [S("15OZ", "15 oz can", 1.79, 15)],
         "Peaches, pear juice from concentrate, peach juice from concentrate, ascorbic acid.", (), VGF,
         "Peaches packed in fruit juice with no sugar added."),
        (COPPER, "No Sugar Added Sliced Peaches", "canned-fruit", N("1/2 cup (122 g)", 30, 0, 0, 10, 7, 1, 6, 0, 1), [S("15OZ", "14.5 oz can", 1.79, 14.5)],
         "Peaches, water, natural flavor, ascorbic acid, sucralose.", (), VGF, "Peaches in water sweetened with sucralose; 30 calories per serving."),
        (COPPER, "Pineapple Chunks in 100% Juice", "canned-fruit", N("1/2 cup (122 g)", 70, 0, 0, 0, 18, 1, 16, 0, 1), [S("20OZ", "20 oz can", 1.99, 20)],
         "Pineapple, pineapple juice.", (), VGF, "Pineapple chunks in their own juice, no sugar added."),
        (COPPER, "Mandarin Oranges in Light Syrup", "canned-fruit", N("1/2 cup (126 g)", 80, 0, 0, 10, 19, 1, 18, 8, 1), [S("15OZ", "15 oz can", 1.79, 15)],
         "Mandarin oranges, water, sugar, citric acid.", (), VGF, "Mandarin orange segments in light syrup."),
        (STORE_BRAND, "Unsweetened Applesauce", "applesauce", N("1/2 cup (122 g)", 50, 0, 0, 0, 13, 1, 11, 0, 0), [S("24OZ", "24 oz jar", 2.49, 24), S("6PK", "6 x 4 oz cups", 2.49, 24)],
         "Apples, water, ascorbic acid.", (), (*VGF, "unsweetened"), "Smooth applesauce with no sugar added."),
        (STORE_BRAND, "Original Applesauce", "applesauce", N("1/2 cup (122 g)", 90, 0, 0, 0, 23, 1, 21, 10, 0), [S("24OZ", "24 oz jar", 2.49, 24), S("6PK", "6 x 4 oz cups", 2.49, 24)],
         "Apples, high fructose corn syrup, water, ascorbic acid.", (), VGF, "Sweetened applesauce with 10 g added sugar per serving."),
    ]  # fmt: skip
    out += _rows(rows, (*BEAN_CLAIMS, "sugar-free", "low-sugar"))
    return out


# --- Soups and broth ----------------------------------------------------------------------------

CUP = "1 cup (245 g)"
CUPL = "1 cup (240 mL)"


def soups() -> list[ProductSeed]:
    can = [S("18OZ", "18.6 oz can", 2.49, 18.6)]
    carton = [S("32OZ", "32 fl oz carton", 2.49, 32)]
    rows: list[Row] = [
        (KETTLE, "Chicken Noodle Soup", "soup", N(CUP, 90, 2.5, 0.5, 890, 11, 1, 1, 0, 6), can,
         "Chicken stock, enriched egg noodles (wheat flour, eggs), cooked chicken, carrots, celery, salt, chicken fat, onion, spices.", ("wheat", "egg"), ("dairy-free",),
         "Ready-to-serve chicken noodle soup with white meat chicken. 890 mg sodium per cup."),
        (KETTLE, "Less Sodium Chicken Noodle Soup", "soup", N(CUP, 90, 2.5, 0.5, 480, 11, 1, 1, 0, 6), can,
         "Chicken stock, enriched egg noodles (wheat flour, eggs), cooked chicken, carrots, celery, sea salt, potassium chloride, onion, spices.", ("wheat", "egg"), ("dairy-free",),
         "Chicken noodle soup with 45% less sodium than our regular (480 mg per cup). Lower sodium, but not low sodium."),
        (KETTLE, "Low Sodium Chicken Noodle Soup", "soup", N(CUP, 90, 2.5, 0.5, 130, 12, 1, 1, 0, 5), can,
         "Unsalted chicken stock, enriched egg noodles (wheat flour, eggs), cooked chicken, carrots, celery, chicken fat, onion, spices.", ("wheat", "egg"), ("dairy-free",),
         "Chicken noodle soup made with no added salt: 130 mg sodium per cup."),
        (KETTLE, "Creamy Tomato Soup", "soup", N(CUP, 140, 3, 1.5, 680, 24, 2, 15, 9, 3), can,
         "Tomato puree, water, sugar, cream, butter, salt, onion, garlic, spices.", ("milk",), ("gluten-free",), "Smooth, creamy tomato soup made with cream."),
        (KETTLE, "Chicken & Wild Rice Soup", "soup", N(CUP, 110, 3, 1, 780, 15, 1, 2, 0, 6), can,
         "Chicken stock, cooked chicken, wild rice, carrots, celery, wheat flour, salt, chicken fat, spices.", ("wheat",), (), "Hearty chicken soup with wild rice."),
        (KETTLE, "Minestrone", "soup", N(CUP, 110, 1.5, 0, 690, 20, 4, 4, 1, 4), can,
         "Vegetable stock, tomatoes, ditalini pasta (wheat), kidney beans, carrots, zucchini, green beans, celery, salt, sugar, olive oil, spices.", ("wheat",), VG,
         "Italian vegetable soup with pasta and beans. Vegan."),
        (KETTLE, "Vegetable Beef Soup", "soup", N(CUP, 120, 2, 1, 820, 18, 3, 4, 0, 8), can,
         "Beef stock, potatoes, carrots, cooked beef, tomatoes, corn, peas, green beans, salt, spices.", (), ("gluten-free", "dairy-free"), "Beef and vegetable soup."),
        (KETTLE, "Split Pea with Ham Soup", "soup", N(CUP, 180, 2, 1, 850, 28, 5, 4, 0, 11), can,
         "Water, split peas, ham (pork, water, salt, sugar, sodium nitrite), carrots, onion, salt, spices.", (), ("gluten-free", "dairy-free"), "Thick split pea soup with smoked ham."),
        (KETTLE, "New England Clam Chowder", "soup", N(CUP, 220, 12, 4, 860, 21, 1, 2, 0, 6), can,
         "Clam stock, potatoes, cream, clams, wheat flour, butter, bacon, salt, onion, celery, spices.", ("shellfish", "milk", "wheat"), (), "Creamy clam chowder with potatoes."),
        (KETTLE, "Hearty Lentil Soup", "soup", N(CUP, 160, 1.5, 0, 750, 26, 7, 3, 0, 9), can,
         "Water, lentils, carrots, celery, tomatoes, onion, olive oil, salt, garlic, spices.", (), VGF, "Hearty vegan lentil and vegetable soup with 7 g fiber."),
        (KETTLE, "Chili with Beans", "chili", N("1 cup (247 g)", 270, 10, 4, 960, 26, 8, 4, 1, 18), [S("15OZ", "15 oz can", 2.29, 15)],
         "Water, cooked beef, kidney beans, tomato paste, chili powder, salt, modified corn starch, sugar, onion, spices.", (), ("gluten-free", "dairy-free"),
         "Beef chili with kidney beans. 18 g protein per cup."),
        (KETTLE, "Turkey Chili with Beans", "chili", N("1 cup (247 g)", 210, 3, 1, 870, 25, 7, 5, 1, 19), [S("15OZ", "15 oz can", 2.49, 15)],
         "Water, cooked turkey, kidney beans, tomato paste, chili powder, salt, sugar, onion, spices.", (), ("gluten-free", "dairy-free"), "Leaner chili made with turkey."),
        (GREENPOT, "Organic Vegan Tomato Basil Soup", "soup", N(CUPL, 100, 2.5, 0, 590, 17, 2, 11, 4, 2), carton,
         "Organic tomatoes, water, organic onions, organic cane sugar, organic olive oil, sea salt, organic basil, organic garlic.", (), (*VGF, "non-gmo"),
         "Organic tomato basil soup made without cream. Vegan."),
        (GREENPOT, "Organic Butternut Squash Soup", "soup", N(CUPL, 100, 2, 0.5, 550, 19, 3, 9, 4, 2), carton,
         "Organic butternut squash, water, organic onions, organic cane sugar, organic coconut milk, sea salt, organic spices.", (), (*VGF, "non-gmo"),
         "Silky organic butternut squash soup. Vegan."),
        (GREENPOT, "Organic Low Sodium Lentil Vegetable Soup", "soup", N(CUP, 150, 1.5, 0, 140, 24, 6, 3, 0, 8), [S("14OZ", "14.5 oz can", 3.29, 14.5)],
         "Water, organic lentils, organic carrots, organic celery, organic tomatoes, organic onions, organic olive oil, organic garlic, organic spices.", (), (*VGF, "non-gmo"),
         "Organic lentil vegetable soup that is low sodium: 140 mg per cup. Vegan."),
        (GREENPOT, "Organic Black Bean Soup", "soup", N(CUP, 170, 1.5, 0, 680, 30, 9, 3, 0, 9), [S("14OZ", "14.5 oz can", 3.29, 14.5)],
         "Water, organic black beans, organic onions, organic tomatoes, organic peppers, sea salt, organic spices.", (), (*VGF, "non-gmo"), "Organic black bean soup with 9 g fiber."),
        (GREENPOT, "Organic Chicken Noodle Soup", "soup", N(CUP, 90, 2, 0.5, 690, 12, 1, 1, 0, 6), [S("14OZ", "14.5 oz can", 3.29, 14.5)],
         "Organic chicken broth, organic noodles (organic wheat flour, organic eggs), organic chicken, organic carrots, organic celery, sea salt.", ("wheat", "egg"),
         ("dairy-free", "non-gmo"), "Organic chicken noodle soup."),
        (STORE_BRAND, "Condensed Chicken Noodle Soup", "soup", N("1/2 cup condensed (123 g)", 60, 2, 0.5, 890, 8, 1, 1, 0, 3), [S("10OZ", "10.75 oz can", 0.99, 10.75)],
         "Chicken stock, enriched egg noodles (wheat flour, eggs), chicken, salt, chicken fat, monosodium glutamate, spices.", ("wheat", "egg"), (),
         "Condensed chicken noodle soup; add one can of water."),
        (STORE_BRAND, "Condensed Cream of Mushroom Soup", "soup", N("1/2 cup condensed (123 g)", 100, 6, 1.5, 860, 9, 1, 1, 0, 1), [S("10OZ", "10.5 oz can", 0.99, 10.5)],
         "Water, mushrooms, vegetable oil, modified food starch, wheat flour, cream (milk), salt, soy protein, spices.", ("wheat", "milk", "soy"), (),
         "Condensed cream of mushroom soup for casseroles."),
        (STORE_BRAND, "Condensed Tomato Soup", "soup", N("1/2 cup condensed (123 g)", 90, 0, 0, 480, 20, 1, 12, 10, 2), [S("10OZ", "10.75 oz can", 0.99, 10.75)],
         "Tomato puree, high fructose corn syrup, wheat flour, salt, spices.", ("wheat",), VG, "Condensed tomato soup; add one can of water or milk."),
        (STORE_BRAND, "Chicken Flavor Ramen Noodle Soup", "ramen", N("1/2 block with seasoning (43 g)", 190, 7, 3.5, 830, 27, 1, 0, 0, 4), [S("12PK", "12 x 3 oz packages", 3.49, 36)],
         "Enriched wheat flour, palm oil, salt, soy sauce (soybeans, wheat), monosodium glutamate, dehydrated chicken, onion powder, garlic powder.", ("wheat", "soy"), (),
         "Instant ramen noodles with chicken seasoning. 830 mg sodium per half block."),
        # Broth
        (KETTLE, "Chicken Broth", "broth", N(CUPL, 10, 0.5, 0, 860, 1, 0, 1, 0, 1), carton, "Chicken stock, salt, chicken fat, natural flavor, onion, carrots, celery.", (),
         ("gluten-free", "dairy-free"), "Classic chicken broth, 860 mg sodium per cup."),
        (KETTLE, "Reduced Sodium Chicken Broth", "broth", N(CUPL, 10, 0, 0, 570, 1, 0, 1, 0, 1), carton, "Chicken stock, salt, natural flavor, onion, carrots, celery.", (),
         ("gluten-free", "dairy-free"), "Chicken broth with 33% less sodium than our regular (570 mg per cup). Not low sodium."),
        (KETTLE, "Low Sodium Chicken Broth", "broth", N(CUPL, 15, 0, 0, 140, 1, 0, 1, 0, 2), carton, "Chicken stock, sea salt, natural flavor, onion, carrots, celery.", (),
         ("gluten-free", "dairy-free"), "Low sodium chicken broth with 140 mg sodium per cup."),
        (KETTLE, "Unsalted Chicken Stock", "broth", N(CUPL, 20, 0, 0, 130, 1, 0, 1, 0, 3), carton, "Chicken stock, onion, carrots, celery, herbs.", (),
         ("gluten-free", "dairy-free", "no-salt-added"), "Rich chicken stock with no salt added; 130 mg naturally occurring sodium per cup."),
        (KETTLE, "Beef Broth", "broth", N(CUPL, 15, 0, 0, 810, 1, 0, 1, 0, 2), carton, "Beef stock, salt, yeast extract, natural flavor, onion, carrots.", (),
         ("gluten-free", "dairy-free"), "Savory beef broth."),
        (KETTLE, "Chicken Bone Broth", "broth", N(CUPL, 45, 0, 0, 460, 0, 0, 0, 0, 10), carton, "Chicken bone broth (water, chicken bones), onion, celery, carrots, sea salt.",
         (), ("gluten-free", "dairy-free"), "Slow-simmered chicken bone broth with 10 g protein per cup."),
        (GREENPOT, "Organic Vegetable Broth", "broth", N(CUPL, 10, 0, 0, 550, 2, 0, 1, 0, 0), carton,
         "Filtered water, organic carrots, organic celery, organic onions, sea salt, organic garlic, organic herbs.", (), (*VGF, "non-gmo"), "Organic vegan vegetable broth."),
        (GREENPOT, "Organic Low Sodium Vegetable Broth", "broth", N(CUPL, 10, 0, 0, 140, 2, 0, 1, 0, 0), carton,
         "Filtered water, organic carrots, organic celery, organic onions, sea salt, organic garlic, organic herbs.", (), (*VGF, "non-gmo"),
         "Organic vegan vegetable broth with 140 mg sodium per cup."),
        (GREENPOT, "Organic Free-Range Chicken Broth", "broth", N(CUPL, 10, 0, 0, 570, 1, 0, 1, 0, 1), carton,
         "Organic free-range chicken broth, sea salt, organic onions, organic celery, organic carrots.", (), ("gluten-free", "dairy-free", "free-range", "non-gmo"),
         "Organic broth from free-range chickens."),
        (STORE_BRAND, "Chicken Broth", "broth", N(CUPL, 10, 0, 0, 860, 1, 0, 0, 0, 1), [S("32OZ", "32 fl oz carton", 1.79, 32), S("14OZ", "14.5 oz can", 0.99, 14.5)],
         "Chicken stock, salt, natural flavor, onion, carrots, celery.", (), ("gluten-free", "dairy-free"), "Classic chicken broth."),
        (STORE_BRAND, "Vegetable Broth", "broth", N(CUPL, 10, 0, 0, 660, 2, 0, 1, 0, 0), [S("32OZ", "32 fl oz carton", 1.79, 32)],
         "Water, carrots, celery, onions, salt, tomato paste, garlic, spices.", (), VGF, "Vegan vegetable broth."),
    ]  # fmt: skip
    return _rows(rows, ("low-sodium", "high-protein", "high-fiber", "low-fat"))


# --- Spreads, sweeteners, oils, sauces ------------------------------------------------------------

T2 = "2 tbsp (32 g)"
T1 = "1 tbsp (20 g)"
REG_PB = N(T2, 190, 16, 3, 140, 8, 2, 3, 3, 7)
NAT_PB = N(T2, 190, 16, 2.5, 120, 7, 3, 2, 0, 8)
PB_ING = "Roasted peanuts, sugar, hydrogenated vegetable oils (rapeseed, soybean), salt."


def spreads() -> list[ProductSeed]:
    jar = [S("16OZ", "16 oz jar", 2.49, 16), S("40OZ", "40 oz jar", 5.49, 40)]
    ojar = [S("16OZ", "16 oz jar", 3.49, 16), S("28OZ", "28 oz jar", 5.79, 28)]
    njar = [S("12OZ", "12 oz jar", 8.99, 12)]
    PN = ("peanuts",)
    rows: list[Row] = [
        (STORE_BRAND, "Creamy Peanut Butter", "peanut-butter", REG_PB, jar, PB_ING, PN, VGF, "Smooth, no-stir peanut butter with a little added sugar."),
        (STORE_BRAND, "Crunchy Peanut Butter", "peanut-butter", REG_PB, jar, PB_ING, PN, VGF, "No-stir peanut butter with crunchy peanut pieces."),
        (STORE_BRAND, "Natural Creamy Peanut Butter", "peanut-butter", NAT_PB, jar, "Peanuts, salt.", PN, (*VGF, "unsweetened"),
         "Natural peanut butter made from just peanuts and salt, with no added sugar or hydrogenated oil. Stir before using."),
        (STORE_BRAND, "Reduced Fat Creamy Peanut Butter Spread", "peanut-butter", N(T2, 190, 12, 2.5, 190, 15, 2, 4, 4, 7), jar,
         "Roasted peanuts, corn syrup solids, sugar, pea protein, salt, hydrogenated vegetable oils (cottonseed, rapeseed), molasses.", PN, (*VGF, "reduced-fat"),
         "Peanut butter spread with 25% less fat than regular peanut butter. Contains more added sugar (4 g); same calories."),
        (OLDMILL, "Creamy Peanut Butter", "peanut-butter", REG_PB, ojar, PB_ING, PN, VGF, "Classic creamy, no-stir peanut butter."),
        (OLDMILL, "Crunchy Peanut Butter", "peanut-butter", REG_PB, ojar, PB_ING, PN, VGF, "Classic extra crunchy peanut butter."),
        (OLDMILL, "Natural Creamy Peanut Butter, No Salt Added", "peanut-butter", N(T2, 200, 17, 2.5, 0, 6, 3, 1, 0, 8), ojar, "Dry roasted peanuts.", PN,
         (*VGF, "unsweetened", "no-salt-added"), "One-ingredient natural peanut butter: just dry roasted peanuts, with no salt or sugar added."),
        (OLDMILL, "Natural Crunchy Peanut Butter", "peanut-butter", N(T2, 190, 16, 2.5, 110, 7, 3, 2, 0, 8), ojar, "Peanuts, salt.", PN, (*VGF, "unsweetened"),
         "Crunchy natural peanut butter made with peanuts and salt. Stir before using."),
        (OLDMILL, "Honey Roasted Peanut Butter", "peanut-butter", N(T2, 190, 15, 3, 110, 10, 2, 6, 5, 7), ojar,
         "Roasted peanuts, honey, sugar, palm oil, salt.", PN, ("gluten-free", "dairy-free"), "Creamy peanut butter sweetened with honey."),
        (OLDMILL, "Powdered Peanut Butter", "peanut-butter", N("2 tbsp (12 g)", 50, 1.5, 0, 95, 4, 2, 1, 1, 6), [S("6OZ", "6.5 oz jar", 4.99, 6.5)],
         "Roasted peanuts, sugar, salt.", PN, VGF, "Defatted peanut powder with 85% less fat than peanut butter. Mix with water."),
        (OLDMILL, "Creamy Almond Butter", "nut-butter", N(T2, 190, 17, 1.5, 0, 7, 3, 2, 0, 7), njar, "Dry roasted almonds.", ("tree nuts",),
         (*VGF, "unsweetened", "no-salt-added"), "Smooth almond butter made from just roasted almonds."),
        (OLDMILL, "Cashew Butter", "nut-butter", N(T2, 190, 16, 3, 5, 9, 1, 2, 0, 5), njar, "Roasted cashews.", ("tree nuts",), (*VGF, "unsweetened", "no-salt-added"),
         "Creamy cashew butter with nothing added."),
        (OLDMILL, "Chocolate Hazelnut Spread", "nut-butter", N("2 tbsp (37 g)", 200, 12, 4, 15, 22, 1, 21, 20, 2), [S("13OZ", "13 oz jar", 4.49, 13)],
         "Sugar, palm oil, hazelnuts, cocoa, skim milk powder, soy lecithin, vanillin.", ("tree nuts", "milk", "soy"), ("gluten-free",),
         "Sweet cocoa hazelnut spread. More sugar than nuts: 20 g added sugar per serving."),
        (PUREGROVE, "Organic Creamy Peanut Butter", "peanut-butter", N(T2, 190, 16, 2.5, 65, 7, 3, 2, 0, 8), [S("16OZ", "16 oz jar", 5.49, 16)],
         "Organic dry roasted peanuts, sea salt.", PN, (*VGF, "unsweetened", "non-gmo"), "Organic natural peanut butter with no added sugar. Stir before using."),
        (PUREGROVE, "Organic Crunchy Peanut Butter", "peanut-butter", N(T2, 190, 16, 2.5, 65, 7, 3, 2, 0, 8), [S("16OZ", "16 oz jar", 5.49, 16)],
         "Organic dry roasted peanuts, sea salt.", PN, (*VGF, "unsweetened", "non-gmo"), "Organic crunchy natural peanut butter."),
        (PUREGROVE, "Organic Creamy Almond Butter", "nut-butter", N(T2, 190, 17, 1.5, 0, 7, 3, 2, 0, 7), [S("12OZ", "12 oz jar", 10.99, 12)],
         "Organic dry roasted almonds.", ("tree nuts",), (*VGF, "unsweetened", "no-salt-added", "non-gmo"), "Organic almond butter, just almonds."),
        (PUREGROVE, "Sunflower Seed Butter", "nut-butter", N(T2, 200, 17, 1.5, 65, 7, 3, 2, 2, 7), [S("16OZ", "16 oz jar", 5.99, 16)],
         "Roasted sunflower seeds, cane sugar, salt.", (), (*VGF, "nut-free"),
         "Creamy sunflower seed butter, a peanut-free and tree-nut-free alternative for school lunches."),
    ]  # fmt: skip
    out = _rows(rows, ("no-added-sugar", "low-sugar", "keto", "high-protein"), AFTER_OPENING)
    fruit = N(T1, 50, 0, 0, 0, 13, 0, 12, 10, 0)
    jam = [S("18OZ", "18 oz jar", 3.99, 18)]
    sjam = [S("18OZ", "18 oz jar", 2.49, 18)]
    sugar_free = N(T1, 10, 0, 0, 0, 5, 0, 0, 0, 0)
    rows = [
        (ORCHARD, "Strawberry Preserves", "jam", fruit, jam, "Strawberries, sugar, corn syrup, fruit pectin, citric acid.", (), VGF, "Classic strawberry preserves with chunks of fruit."),
        (ORCHARD, "Seedless Raspberry Jam", "jam", fruit, jam, "Raspberries, sugar, corn syrup, fruit pectin, citric acid.", (), VGF, "Smooth seedless raspberry jam."),
        (ORCHARD, "Apricot Preserves", "jam", fruit, jam, "Apricots, sugar, corn syrup, fruit pectin, citric acid.", (), VGF, "Apricot preserves."),
        (ORCHARD, "Concord Grape Jelly", "jam", N(T1, 50, 0, 0, 10, 13, 0, 12, 11, 0), jam, "Concord grape juice, corn syrup, sugar, fruit pectin, citric acid.", (), VGF,
         "Concord grape jelly."),
        (ORCHARD, "Sugar Free Strawberry Preserves", "jam", sugar_free, [S("13OZ", "12.75 oz jar", 3.99, 12.75)],
         "Strawberries, water, polydextrose, maltitol syrup, fruit pectin, citric acid, sucralose.", (), VGF,
         "Strawberry preserves with 0 g sugar and 10 calories per tablespoon, sweetened with sucralose and maltitol."),
        (ORCHARD, "Sugar Free Seedless Raspberry Jam", "jam", sugar_free, [S("13OZ", "12.75 oz jar", 3.99, 12.75)],
         "Raspberries, water, polydextrose, maltitol syrup, fruit pectin, citric acid, sucralose.", (), VGF, "Sugar free seedless raspberry jam."),
        (ORCHARD, "Low Sugar Strawberry Spread", "jam", N(T1, 25, 0, 0, 0, 6, 0, 5, 4, 0), [S("16OZ", "15.5 oz jar", 3.99, 15.5)],
         "Strawberries, water, sugar, fruit pectin, calcium citrate, citric acid.", (), VGF, "Strawberry spread with half the sugar of regular preserves (5 g per tablespoon)."),
        (ORCHARD, "No Sugar Added Blueberry Spread", "jam", N(T1, 15, 0, 0, 0, 4, 0, 3, 0, 0), [S("10OZ", "10 oz jar", 4.49, 10)],
         "Blueberries, water, fruit pectin, citric acid, monk fruit extract.", (), VGF, "Blueberry spread with no sugar added, lightly sweetened with monk fruit."),
        (CEDAR, "Organic Strawberry Fruit Spread", "jam", N(T1, 40, 0, 0, 0, 10, 0, 8, 7, 0), [S("11OZ", "11 oz jar", 4.99, 11)],
         "Organic strawberries, organic cane sugar, organic lemon juice concentrate, fruit pectin.", (), (*VGF, "non-gmo"), "Organic strawberry fruit spread."),
        (STORE_BRAND, "Strawberry Jam", "jam", fruit, sjam, "Strawberries, high fructose corn syrup, corn syrup, fruit pectin, citric acid.", (), VGF, "Strawberry jam."),
        (STORE_BRAND, "Grape Jelly", "jam", N(T1, 50, 0, 0, 10, 13, 0, 12, 11, 0), sjam, "Grape juice, high fructose corn syrup, corn syrup, fruit pectin, citric acid.", (), VGF,
         "Grape jelly."),
        (STORE_BRAND, "Orange Marmalade", "jam", N(T1, 50, 0, 0, 5, 13, 0, 12, 11, 0), sjam, "Sugar, oranges, orange peel, water, fruit pectin, citric acid.", (), VGF,
         "Tangy orange marmalade with peel."),
        # Honey and syrup
        (WILDFLOWER, "Raw Texas Wildflower Honey", "honey", N("1 tbsp (21 g)", 60, 0, 0, 0, 17, 0, 17, 17, 0), [S("12OZ", "12 oz jar", 7.99, 12), S("32OZ", "32 oz jar", 16.99, 32)],
         "Raw wildflower honey.", (), ("gluten-free", "local"), "Raw, unfiltered wildflower honey from Texas beekeepers. Not for infants under one year."),
        (WILDFLOWER, "Raw Texas Mesquite Honey", "honey", N("1 tbsp (21 g)", 60, 0, 0, 0, 17, 0, 17, 17, 0), [S("12OZ", "12 oz jar", 8.99, 12)],
         "Raw mesquite honey.", (), ("gluten-free", "local"), "Light, smooth raw honey from mesquite blossoms in West Texas."),
        (STORE_BRAND, "Pure Clover Honey", "honey", N("1 tbsp (21 g)", 60, 0, 0, 0, 17, 0, 17, 17, 0), [S("12OZ", "12 oz bear", 4.49, 12), S("24OZ", "24 oz bottle", 7.99, 24)],
         "Pure clover honey.", (), ("gluten-free",), "Pure, filtered clover honey in a squeeze bottle."),
        (NORTHWOODS, "100% Pure Maple Syrup, Grade A Amber", "syrup", N("1/4 cup (60 mL)", 210, 0, 0, 10, 53, 0, 53, 53, 0), [S("12OZ", "12.5 fl oz bottle", 9.99, 12.5), S("32OZ", "32 fl oz jug", 21.99, 32)],
         "Pure maple syrup.", (), VGF, "100% pure Vermont maple syrup with a rich amber flavor. Pure maple syrup is itself sugar: 53 g per serving."),
        (NORTHWOODS, "Organic Pure Maple Syrup, Grade A Dark", "syrup", N("1/4 cup (60 mL)", 210, 0, 0, 10, 53, 0, 53, 53, 0), [S("12OZ", "12.5 fl oz bottle", 11.99, 12.5)],
         "Organic pure maple syrup.", (), (*VGF, "non-gmo"), "Organic pure maple syrup with a robust, dark taste."),
        (GRIDDLE, "Original Pancake Syrup", "syrup", N("1/4 cup (60 mL)", 210, 0, 0, 120, 53, 0, 32, 32, 0), [S("24OZ", "24 fl oz bottle", 3.49, 24)],
         "Corn syrup, high fructose corn syrup, water, cellulose gum, caramel color, salt, natural and artificial flavor, sodium benzoate.", (), VGF,
         "Classic maple-flavored pancake syrup made from corn syrup. Not pure maple syrup."),
        (GRIDDLE, "Lite Pancake Syrup", "syrup", N("1/4 cup (60 mL)", 100, 0, 0, 180, 26, 0, 17, 17, 0), [S("24OZ", "24 fl oz bottle", 3.49, 24)],
         "Water, corn syrup, high fructose corn syrup, cellulose gum, salt, natural and artificial flavor, sucralose.", (), VGF,
         "Pancake syrup with half the calories of our original. Still contains 17 g added sugar."),
        (GRIDDLE, "Sugar Free Pancake Syrup", "syrup", N("1/4 cup (60 mL)", 20, 0, 0, 150, 12, 0, 0, 0, 0), [S("24OZ", "24 fl oz bottle", 3.99, 24)],
         "Water, sorbitol, cellulose gum, natural and artificial flavor, salt, sucralose, acesulfame potassium.", (), VGF,
         "Sugar free, no sugar added maple-flavored syrup, 20 calories per serving. Sweetened with sorbitol and sucralose."),
    ]  # fmt: skip
    out += _rows(rows, SUGAR_CLAIMS, AFTER_OPENING)
    return out


def oils_sauces() -> list[ProductSeed]:
    tbsp = "1 tbsp (15 mL)"
    oil = N(tbsp, 120, 14, 2, 0, 0, 0, 0, 0, 0)
    zero = N(tbsp, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    rows: list[Row] = [
        (OLIVARA, "Extra Virgin Olive Oil", "cooking-oil", oil, [S("17OZ", "16.9 fl oz bottle", 8.99, 16.9), S("34OZ", "33.8 fl oz (1 L) bottle", 14.99, 33.8)],
         "Extra virgin olive oil.", (), VGF, "Cold-pressed extra virgin olive oil from Spain for dressings and finishing."),
        (OLIVARA, "Organic Extra Virgin Olive Oil", "cooking-oil", oil, [S("17OZ", "16.9 fl oz bottle", 11.99, 16.9)],
         "Organic extra virgin olive oil.", (), (*VGF, "non-gmo"), "Organic cold-pressed extra virgin olive oil."),
        (OLIVARA, "Light Tasting Olive Oil", "cooking-oil", oil, [S("17OZ", "16.9 fl oz bottle", 8.49, 16.9)],
         "Refined olive oil, virgin olive oil.", (), VGF,
         "Refined olive oil with a mild flavor for high-heat cooking. 'Light' refers to flavor, not calories: same 120 calories per tablespoon."),
        (OLIVARA, "Avocado Oil", "cooking-oil", N(tbsp, 120, 14, 1.5, 0, 0, 0, 0, 0, 0), [S("17OZ", "16.9 fl oz bottle", 9.99, 16.9)],
         "Refined avocado oil.", (), VGF, "Refined avocado oil with a high smoke point."),
        (OLIVARA, "Balsamic Vinegar of Modena", "vinegar", N(tbsp, 15, 0, 0, 5, 3, 0, 3, 0, 0), [S("17OZ", "16.9 fl oz bottle", 5.99, 16.9)],
         "Wine vinegar, grape must, caramel color. Contains sulfites.", (), VGF, "Aged balsamic vinegar from Modena, Italy."),
        (STORE_BRAND, "Vegetable Oil", "cooking-oil", oil, [S("48OZ", "48 fl oz bottle", 4.49, 48)], "Soybean oil.", (), VGF, "Pure soybean vegetable oil for frying and baking."),
        (STORE_BRAND, "Canola Oil", "cooking-oil", N(tbsp, 120, 14, 1, 0, 0, 0, 0, 0, 0), [S("48OZ", "48 fl oz bottle", 4.79, 48)], "Canola oil.", (), VGF,
         "Canola oil, low in saturated fat."),
        (STORE_BRAND, "Extra Virgin Olive Oil", "cooking-oil", oil, [S("17OZ", "16.9 fl oz bottle", 6.99, 16.9), S("51OZ", "51 fl oz bottle", 16.99, 51)],
         "Extra virgin olive oil.", (), VGF, "Everyday extra virgin olive oil."),
        (STORE_BRAND, "Canola Oil Cooking Spray", "cooking-oil", N("1/4 second spray (0.25 g)", 0, 0, 0, 0, 0, 0, 0, 0, 0), [S("8OZ", "8 oz can", 2.99, 8)],
         "Canola oil, soy lecithin, propellant.", ("soy",), VGF, "Nonstick canola oil spray. A 1/4-second spray has 0 calories."),
        (PALMGROVE, "Organic Virgin Coconut Oil", "cooking-oil", N("1 tbsp (14 g)", 120, 14, 12, 0, 0, 0, 0, 0, 0), [S("14OZ", "14 fl oz jar", 7.99, 14)],
         "Organic virgin coconut oil.", (), (*VGF, "non-gmo"), "Unrefined organic virgin coconut oil. High in saturated fat."),
        (LOTUS, "Toasted Sesame Oil", "cooking-oil", oil, [S("5OZ", "5 fl oz bottle", 4.49, 5)], "Toasted sesame oil.", ("sesame",), VGF,
         "Nutty toasted sesame oil for stir-fries and dressings."),
        (STORE_BRAND, "Distilled White Vinegar", "vinegar", zero, [S("32OZ", "32 fl oz bottle", 1.49, 32), S("GAL", "1 gallon", 3.49, 128)], "Distilled vinegar, water. 5% acidity.",
         (), VGF, "Distilled white vinegar for cooking, pickling, and cleaning."),
        (STORE_BRAND, "Apple Cider Vinegar", "vinegar", zero, [S("32OZ", "32 fl oz bottle", 1.99, 32)], "Apple cider vinegar, water. 5% acidity.", (), VGF,
         "Filtered apple cider vinegar."),
        (CEDAR, "Organic Raw Apple Cider Vinegar with the Mother", "vinegar", zero, [S("32OZ", "32 fl oz bottle", 4.99, 32)], "Organic raw apple cider vinegar. 5% acidity.",
         (), (*VGF, "non-gmo"), "Unfiltered, unpasteurized organic apple cider vinegar with the mother."),
    ]  # fmt: skip
    out = _rows(rows, ("sugar-free", "zero-calorie"))
    half = "1/2 cup (125 g)"
    jar = [S("24OZ", "24 oz jar", 7.99, 24)]
    sjar = [S("24OZ", "24 oz jar", 1.99, 24), S("45OZ", "45 oz jar", 3.49, 45)]
    nonna = "Italian whole peeled tomatoes, olive oil, onions, salt, garlic, basil, black pepper, oregano"
    rows = [
        (NONNA, "Marinara Sauce", "pasta-sauce", N(half, 70, 4, 0.5, 450, 7, 2, 4, 0, 1), jar, f"{nonna}.", (), VGF,
         "Slow-simmered marinara made with Italian tomatoes and olive oil, with no sugar added."),
        (NONNA, "Tomato Basil Sauce", "pasta-sauce", N(half, 70, 4, 0.5, 440, 7, 2, 4, 0, 1), jar, f"{nonna}, extra basil.", (), VGF,
         "Tomato basil sauce with no sugar added."),
        (NONNA, "Arrabbiata Sauce", "pasta-sauce", N(half, 70, 4, 0.5, 460, 7, 2, 4, 0, 1), jar, f"{nonna}, crushed red pepper.", (), VGF,
         "Spicy tomato sauce with crushed red pepper."),
        (NONNA, "Vodka Sauce", "pasta-sauce", N(half, 120, 8, 4, 480, 9, 2, 6, 0, 3), jar,
         "Italian tomatoes, cream, onions, parmesan cheese (milk), olive oil, butter, salt, garlic, basil. Vodka is cooked off (less than 0.5% alcohol).", ("milk",), ("gluten-free",),
         "Creamy tomato sauce finished with cream and parmesan."),
        (NONNA, "Low Sodium Marinara Sauce", "pasta-sauce", N(half, 70, 4, 0.5, 70, 7, 2, 4, 0, 1), jar,
         "Italian whole peeled tomatoes, olive oil, onions, garlic, basil, black pepper, oregano.", (), (*VGF, "no-salt-added"),
         "Our marinara made with no salt added: 70 mg sodium per serving."),
        (NONNA, "Basil Pesto", "pasta-sauce", N("2 tbsp (30 g)", 150, 15, 2.5, 280, 2, 1, 1, 0, 2), [S("7OZ", "6.7 oz jar", 6.49, 6.7)],
         "Basil, olive oil, parmesan cheese (milk), pine nuts, garlic, salt.", ("milk", "tree nuts"), ("gluten-free",), "Classic Genovese basil pesto with pine nuts and parmesan."),
        (STORE_BRAND, "Traditional Pasta Sauce", "pasta-sauce", N(half, 70, 1.5, 0, 480, 13, 2, 10, 6, 2), sjar,
         "Tomato puree, sugar, diced tomatoes, soybean oil, salt, dehydrated onions, garlic, spices.", (), VGF, "Smooth traditional pasta sauce. Contains 6 g added sugar per serving."),
        (STORE_BRAND, "Garden Vegetable Pasta Sauce", "pasta-sauce", N(half, 70, 1.5, 0, 460, 13, 3, 10, 5, 2), sjar,
         "Tomato puree, diced tomatoes, sugar, green peppers, mushrooms, onions, soybean oil, salt, spices.", (), VGF, "Chunky pasta sauce with peppers, mushrooms, and onions."),
        (STORE_BRAND, "Meat Flavored Pasta Sauce", "pasta-sauce", N(half, 80, 2.5, 1, 510, 12, 2, 9, 5, 2), sjar,
         "Tomato puree, sugar, beef, soybean oil, salt, onions, garlic, spices.", (), ("gluten-free", "dairy-free"), "Pasta sauce with seasoned beef."),
        (STORE_BRAND, "No Sugar Added Marinara Sauce", "pasta-sauce", N(half, 50, 1.5, 0, 380, 8, 2, 5, 0, 1), sjar,
         "Tomato puree, diced tomatoes, olive oil, salt, onions, garlic, basil, oregano.", (), VGF, "Marinara with no sugar added; the 5 g of sugar comes from tomatoes."),
        (STORE_BRAND, "Low Sodium Pasta Sauce", "pasta-sauce", N(half, 70, 1.5, 0, 95, 13, 2, 10, 6, 2), sjar,
         "Tomato puree, sugar, diced tomatoes, soybean oil, dehydrated onions, garlic, spices.", (), VGF,
         "Traditional pasta sauce with 80% less sodium (95 mg). Still contains 6 g added sugar."),
        (VALLORA, "Tomato Basil Pasta Sauce", "pasta-sauce", N(half, 90, 3, 0.5, 460, 13, 3, 9, 5, 2), [S("24OZ", "24 oz jar", 3.49, 24)],
         "Tomato puree, diced tomatoes, cane sugar, olive oil, salt, basil, garlic, onion powder.", (), VGF, "Tomato basil pasta sauce."),
        (VALLORA, "Alfredo Sauce", "pasta-sauce", N("1/4 cup (61 g)", 90, 8, 5, 390, 2, 0, 1, 0, 2), [S("15OZ", "15 oz jar", 3.49, 15)],
         "Water, cream, parmesan cheese (milk), butter, modified corn starch, salt, garlic, egg yolks.", ("milk", "egg"), ("gluten-free",), "Creamy parmesan Alfredo sauce."),
        (CEDAR, "Organic Marinara Sauce", "pasta-sauce", N(half, 60, 2, 0, 410, 9, 2, 6, 2, 2), [S("25OZ", "25 oz jar", 4.49, 25)],
         "Organic tomato puree, organic diced tomatoes, organic olive oil, organic cane sugar, sea salt, organic garlic, organic basil.", (), (*VGF, "non-gmo"),
         "Organic marinara sauce."),
        (CEDAR, "Organic Tomato Basil Pasta Sauce, No Sugar Added", "pasta-sauce", N(half, 50, 1.5, 0, 350, 8, 2, 5, 0, 1), [S("25OZ", "25 oz jar", 4.49, 25)],
         "Organic tomato puree, organic diced tomatoes, organic olive oil, sea salt, organic basil, organic garlic.", (), (*VGF, "non-gmo"),
         "Organic tomato basil sauce with no sugar added."),
    ]  # fmt: skip
    out += _rows(rows, ("no-added-sugar", "low-sugar", "low-sodium"), AFTER_OPENING)
    return out


# --- Condiments ---------------------------------------------------------------------------------

D2 = "2 tbsp (30 mL)"


def condiments() -> list[ProductSeed]:
    ketchup = N("1 tbsp (17 g)", 20, 0, 0, 160, 5, 0, 4, 4, 0)
    kbottle = [
        S("20OZ", "20 oz squeeze bottle", 2.99, 20),
        S("38OZ", "38 oz squeeze bottle", 4.49, 38),
    ]
    mustard = [S("14OZ", "14 oz squeeze bottle", 1.99, 14)]
    mayo = [S("30OZ", "30 fl oz jar", 5.49, 30)]
    dressing = [S("16OZ", "16 fl oz bottle", 3.49, 16)]
    EG = ("egg",)
    ME = ("milk", "egg")
    rows: list[Row] = [
        (BRIGHTSIDE, "Tomato Ketchup", "ketchup", ketchup, kbottle,
         "Tomato concentrate, distilled vinegar, high fructose corn syrup, corn syrup, salt, spice, onion powder, natural flavoring.", (), VGF,
         "Classic thick tomato ketchup. 4 g added sugar per tablespoon."),
        (BRIGHTSIDE, "No Sugar Added Tomato Ketchup", "ketchup", N("1 tbsp (17 g)", 5, 0, 0, 160, 1, 0, 1, 0, 0), [S("13OZ", "13 oz squeeze bottle", 3.29, 13)],
         "Tomato concentrate, distilled vinegar, salt, onion powder, spice, natural flavoring, sucralose.", (), VGF,
         "Ketchup with no sugar added, sweetened with sucralose. 5 calories and 1 g naturally occurring sugar per tablespoon."),
        (BRIGHTSIDE, "No Salt Added Tomato Ketchup", "ketchup", N("1 tbsp (17 g)", 20, 0, 0, 5, 5, 0, 4, 4, 0), [S("14OZ", "14 oz squeeze bottle", 3.29, 14)],
         "Tomato concentrate, distilled vinegar, high fructose corn syrup, corn syrup, spice, onion powder, natural flavoring.", (), (*VGF, "no-salt-added"),
         "Ketchup with no salt added: 5 mg sodium per tablespoon."),
        (BRIGHTSIDE, "Organic Tomato Ketchup", "ketchup", N("1 tbsp (17 g)", 20, 0, 0, 190, 5, 0, 4, 4, 0), [S("20OZ", "20 oz squeeze bottle", 3.99, 20)],
         "Organic tomato concentrate, organic distilled vinegar, organic cane sugar, salt, organic onion powder, organic spices.", (), (*VGF, "non-gmo"),
         "Organic ketchup sweetened with cane sugar instead of corn syrup."),
        (STORE_BRAND, "Tomato Ketchup", "ketchup", ketchup, [S("24OZ", "24 oz squeeze bottle", 1.99, 24), S("38OZ", "38 oz squeeze bottle", 2.99, 38)],
         "Tomato concentrate, distilled vinegar, high fructose corn syrup, corn syrup, salt, spice, onion powder, natural flavoring.", (), VGF, "Classic tomato ketchup."),
        (BRIGHTSIDE, "Classic Yellow Mustard", "mustard", N("1 tsp (5 g)", 0, 0, 0, 55, 0, 0, 0, 0, 0), mustard,
         "Distilled vinegar, water, mustard seed, salt, turmeric, paprika, spice, garlic powder.", (), VGF, "Tangy classic yellow mustard with zero calories."),
        (BRIGHTSIDE, "Spicy Brown Mustard", "mustard", N("1 tsp (5 g)", 5, 0, 0, 65, 0, 0, 0, 0, 0), mustard,
         "Vinegar, water, mustard seed, salt, spices.", (), VGF, "Coarse-ground spicy brown deli mustard."),
        (BRIGHTSIDE, "Dijon Mustard", "mustard", N("1 tsp (5 g)", 5, 0, 0, 120, 0, 0, 0, 0, 0), [S("12OZ", "12 oz jar", 2.99, 12)],
         "Water, mustard seed, vinegar, salt, white wine, citric acid. Contains sulfites.", (), VGF, "Smooth, sharp Dijon mustard."),
        (BRIGHTSIDE, "Honey Mustard", "mustard", N("1 tbsp (15 g)", 30, 0, 0, 120, 6, 0, 5, 5, 0), mustard,
         "Water, honey, mustard seed, sugar, vinegar, salt, turmeric.", (), ("gluten-free", "dairy-free"), "Sweet honey mustard for dipping and sandwiches."),
        (STORE_BRAND, "Yellow Mustard", "mustard", N("1 tsp (5 g)", 0, 0, 0, 55, 0, 0, 0, 0, 0), [S("20OZ", "20 oz squeeze bottle", 1.29, 20)],
         "Distilled vinegar, water, mustard seed, salt, turmeric, paprika, spice.", (), VGF, "Classic yellow mustard."),
        (BRIGHTSIDE, "Real Mayonnaise", "mayonnaise", N("1 tbsp (13 g)", 90, 10, 1.5, 90, 0, 0, 0, 0, 0), mayo,
         "Soybean oil, water, whole eggs, egg yolks, vinegar, salt, sugar, lemon juice concentrate, natural flavors.", EG, ("gluten-free", "dairy-free"),
         "Creamy real mayonnaise made with whole eggs. Mayo contains egg but no dairy."),
        (BRIGHTSIDE, "Light Mayonnaise", "mayonnaise", N("1 tbsp (15 g)", 35, 3.5, 0.5, 125, 1, 0, 1, 1, 0), mayo,
         "Water, soybean oil, vinegar, modified corn starch, eggs, sugar, salt, lemon juice concentrate, xanthan gum.", EG, ("gluten-free", "dairy-free", "reduced-fat"),
         "Light mayonnaise with 60% less fat and calories than real mayonnaise."),
        (BRIGHTSIDE, "Avocado Oil Mayonnaise", "mayonnaise", N("1 tbsp (13 g)", 100, 11, 1.5, 85, 0, 0, 0, 0, 0), [S("12OZ", "12 fl oz jar", 6.99, 12)],
         "Avocado oil, organic eggs, organic egg yolks, water, vinegar, salt, lemon juice concentrate.", EG, ("gluten-free", "dairy-free"),
         "Mayonnaise made with avocado oil and cage-free eggs, no sugar."),
        (ROOTWELL, "Vegan Mayo", "mayonnaise", N("1 tbsp (14 g)", 90, 10, 1, 90, 0, 0, 0, 0, 0), [S("30OZ", "30 fl oz jar", 5.99, 30)],
         "Expeller-pressed canola oil, water, pea protein, distilled vinegar, lemon juice concentrate, salt, mustard flour, spices.", (), (*VGF, "plant-based"),
         "Egg-free vegan mayo made with pea protein. Tastes like the real thing."),
        (STORE_BRAND, "Real Mayonnaise", "mayonnaise", N("1 tbsp (13 g)", 90, 10, 1.5, 90, 0, 0, 0, 0, 0), mayo,
         "Soybean oil, water, whole eggs, egg yolks, vinegar, salt, sugar, lemon juice concentrate.", EG, ("gluten-free", "dairy-free"), "Classic real mayonnaise."),
        (STORE_BRAND, "Fat Free Mayonnaise Dressing", "mayonnaise", N("1 tbsp (16 g)", 10, 0, 0, 120, 2, 0, 1, 1, 0), [S("30OZ", "30 fl oz jar", 3.99, 30)],
         "Water, corn syrup, modified corn starch, vinegar, cellulose gel, salt, egg whites, xanthan gum, lemon juice concentrate.", EG, ("gluten-free", "dairy-free"),
         "Fat free mayonnaise-style dressing with 10 calories per tablespoon."),
        (GARDEN, "Ranch Dressing", "salad-dressing", N(D2, 130, 13, 2, 260, 2, 0, 1, 1, 0), dressing,
         "Soybean oil, water, buttermilk, egg yolk, sugar, salt, vinegar, garlic, onion, spices, xanthan gum.", ME, ("gluten-free",), "Creamy buttermilk ranch dressing."),
        (GARDEN, "Light Ranch Dressing", "salad-dressing", N(D2, 70, 6, 1, 300, 3, 0, 2, 1, 0), dressing,
         "Water, soybean oil, buttermilk, vinegar, sugar, egg yolk, salt, modified food starch, garlic, onion, spices.", ME, ("gluten-free", "reduced-fat"),
         "Ranch dressing with half the fat of our original."),
        (GARDEN, "Fat Free Ranch Dressing", "salad-dressing", N(D2, 30, 0, 0, 300, 6, 0, 2, 2, 0), dressing,
         "Water, corn syrup, buttermilk, vinegar, modified food starch, salt, egg white, garlic, onion, spices.", ME, ("gluten-free",), "Fat free ranch dressing, 30 calories."),
        (GARDEN, "Italian Dressing", "salad-dressing", N(D2, 90, 8, 1, 460, 3, 0, 2, 2, 0), dressing,
         "Water, soybean oil, vinegar, sugar, salt, garlic, red bell pepper, spices, xanthan gum.", (), VGF, "Zesty Italian vinaigrette."),
        (GARDEN, "Fat Free Italian Dressing", "salad-dressing", N(D2, 15, 0, 0, 430, 3, 0, 2, 2, 0), dressing,
         "Water, vinegar, sugar, salt, garlic, red bell pepper, spices, xanthan gum.", (), VGF, "Fat free zesty Italian dressing, 15 calories."),
        (GARDEN, "Balsamic Vinaigrette", "salad-dressing", N(D2, 70, 6, 1, 260, 4, 0, 3, 3, 0), dressing,
         "Balsamic vinegar, soybean oil, water, sugar, salt, garlic, spices.", (), VGF, "Tangy balsamic vinaigrette."),
        (GARDEN, "Light Balsamic Vinaigrette", "salad-dressing", N(D2, 35, 2.5, 0, 280, 4, 0, 3, 2, 0), dressing,
         "Water, balsamic vinegar, soybean oil, sugar, salt, garlic, xanthan gum, spices.", (), VGF, "Light balsamic vinaigrette, 35 calories and 2.5 g fat."),
        (GARDEN, "Caesar Dressing", "salad-dressing", N(D2, 150, 16, 2.5, 290, 1, 0, 1, 0, 1), dressing,
         "Soybean oil, water, parmesan cheese (milk), vinegar, egg yolk, anchovies, garlic, salt, lemon juice, spices.", ("milk", "egg", "fish"), ("gluten-free",),
         "Creamy Caesar dressing made with parmesan and anchovies."),
        (GARDEN, "Chunky Blue Cheese Dressing", "salad-dressing", N(D2, 140, 15, 2.5, 280, 1, 0, 1, 1, 1), dressing,
         "Soybean oil, blue cheese (milk), water, buttermilk, egg yolk, vinegar, sugar, salt, garlic.", ME, ("gluten-free",), "Thick dressing with chunks of blue cheese."),
        (GARDEN, "Thousand Island Dressing", "salad-dressing", N(D2, 110, 10, 1.5, 280, 5, 0, 4, 4, 0), dressing,
         "Soybean oil, water, sugar, tomato paste, vinegar, pickle relish, egg yolk, salt, onion, spices.", EG, ("gluten-free", "dairy-free"), "Classic Thousand Island dressing."),
        (GARDEN, "Honey Mustard Dressing", "salad-dressing", N(D2, 130, 11, 1.5, 210, 8, 0, 7, 7, 0), dressing,
         "Soybean oil, water, honey, mustard, sugar, vinegar, egg yolk, salt.", EG, ("gluten-free", "dairy-free"), "Sweet and tangy honey mustard dressing."),
        (GARDEN, "Dairy-Free Ranch Dressing", "salad-dressing", N(D2, 110, 12, 1, 240, 1, 0, 0, 0, 0), dressing,
         "Avocado oil, water, pea protein, distilled vinegar, garlic, onion, salt, dill, parsley, spices.", (), (*VGF, "plant-based"),
         "Vegan ranch made without dairy or eggs, with 0 g sugar."),
        (STORE_BRAND, "Ranch Dressing", "salad-dressing", N(D2, 140, 14, 2, 270, 2, 0, 1, 1, 0), dressing,
         "Soybean oil, water, buttermilk, egg yolk, sugar, salt, vinegar, garlic, onion, spices.", ME, ("gluten-free",), "Classic ranch dressing."),
        (STORE_BRAND, "Italian Dressing", "salad-dressing", N(D2, 90, 8, 1, 470, 3, 0, 2, 2, 0), dressing,
         "Water, soybean oil, vinegar, sugar, salt, garlic, red bell pepper, spices.", (), VGF, "Zesty Italian dressing."),
        (STORE_BRAND, "Fat Free Raspberry Vinaigrette", "salad-dressing", N(D2, 50, 0, 0, 160, 11, 0, 10, 9, 0), dressing,
         "Water, sugar, raspberry juice concentrate, vinegar, salt, xanthan gum, natural flavor.", (), VGF,
         "Fat free raspberry vinaigrette. Fat free, but 9 g added sugar."),
        (BRIGHTSIDE, "Original BBQ Sauce", "bbq-sauce", N("2 tbsp (36 g)", 70, 0, 0, 300, 17, 0, 15, 15, 0), [S("18OZ", "18 oz bottle", 2.49, 18)],
         "High fructose corn syrup, tomato paste, vinegar, molasses, salt, natural smoke flavor, spices.", (), VGF, "Sweet and smoky barbecue sauce."),
        (BRIGHTSIDE, "No Sugar Added BBQ Sauce", "bbq-sauce", N("2 tbsp (35 g)", 15, 0, 0, 300, 4, 1, 2, 0, 0), [S("14OZ", "14 oz bottle", 3.49, 14)],
         "Tomato puree, vinegar, salt, natural smoke flavor, spices, onion, garlic, sucralose.", (), VGF,
         "Smoky barbecue sauce with no sugar added, sweetened with sucralose."),
        (LOTUS, "Soy Sauce", "soy-sauce", N("1 tbsp (15 mL)", 10, 0, 0, 920, 1, 0, 0, 0, 1), [S("15OZ", "15 fl oz bottle", 2.99, 15)],
         "Water, soybeans, wheat, salt.", ("soy", "wheat"), VG, "Naturally brewed soy sauce. Contains wheat."),
        (LOTUS, "Less Sodium Soy Sauce", "soy-sauce", N("1 tbsp (15 mL)", 10, 0, 0, 575, 1, 0, 0, 0, 1), [S("15OZ", "15 fl oz bottle", 2.99, 15)],
         "Water, soybeans, wheat, salt.", ("soy", "wheat"), VG, "Soy sauce with about 38% less sodium than our regular. Still high in sodium (575 mg)."),
        (LOTUS, "Gluten-Free Tamari", "soy-sauce", N("1 tbsp (15 mL)", 10, 0, 0, 980, 1, 0, 0, 0, 2), [S("10OZ", "10 fl oz bottle", 3.99, 10)],
         "Water, soybeans, salt, alcohol (to preserve freshness).", ("soy",), VGF, "Wheat-free tamari soy sauce, gluten free."),
        (STORE_BRAND, "Louisiana-Style Hot Sauce", "hot-sauce", N("1 tsp (5 mL)", 0, 0, 0, 190, 0, 0, 0, 0, 0), [S("12OZ", "12 fl oz bottle", 1.79, 12)],
         "Aged cayenne peppers, distilled vinegar, water, salt, garlic powder.", (), VGF, "Tangy cayenne pepper hot sauce."),
    ]  # fmt: skip
    return _rows(
        rows,
        (
            "fat-free",
            "low-fat",
            "sugar-free",
            "no-added-sugar",
            "low-sugar",
            "zero-calorie",
            "low-sodium",
        ),
        AFTER_OPENING,
    )


# --- Baking, spices, canned fish ------------------------------------------------------------------


def baking() -> list[ProductSeed]:
    q = "1/4 cup (30 g)"
    flour = N(q, 110, 0, 0, 0, 23, 1, 0, 0, 3)
    tsp = N("1 tsp (4 g)", 15, 0, 0, 0, 4, 0, 4, 4, 0)
    zero = N("1 packet (1 g)", 0, 0, 0, 0, 1, 0, 0, 0, 0)
    W = ("wheat",)
    rows: list[Row] = [
        (MILLSTONE, "Unbleached All-Purpose Flour", "flour", flour, [S("5LB", "5 lb bag", 3.49, 80)], "Unbleached enriched wheat flour, malted barley flour, niacin, iron, thiamin, riboflavin, folic acid.",
         W, VG, "Unbleached all-purpose wheat flour for everyday baking."),
        (MILLSTONE, "Unbleached Bread Flour", "flour", N(q, 110, 0.5, 0, 0, 22, 1, 0, 0, 4), [S("5LB", "5 lb bag", 4.49, 80)], "Unbleached enriched wheat flour, malted barley flour, niacin, iron.",
         W, VG, "High-protein bread flour for chewy yeast breads."),
        (MILLSTONE, "Whole Wheat Flour", "flour", N(q, 110, 0.5, 0, 0, 22, 4, 0, 0, 4), [S("5LB", "5 lb bag", 4.49, 80)], "Whole wheat flour.",
         W, (*VG, "whole-grain"), "Stone-ground 100% whole wheat flour."),
        (MILLSTONE, "Self-Rising Flour", "flour", N(q, 100, 0, 0, 350, 22, 1, 0, 0, 3), [S("5LB", "5 lb bag", 3.99, 80)], "Enriched bleached wheat flour, baking powder, salt.",
         W, VG, "Flour with baking powder and salt already mixed in, for biscuits."),
        (STORE_BRAND, "All-Purpose Flour", "flour", flour, [S("5LB", "5 lb bag", 2.49, 80)], "Bleached enriched wheat flour, niacin, iron, thiamin, riboflavin, folic acid.",
         W, VG, "All-purpose bleached wheat flour."),
        (FREESTONE, "Gluten-Free 1-to-1 Baking Flour", "flour", N("1/4 cup (35 g)", 120, 0, 0, 0, 27, 1, 0, 0, 2), [S("22OZ", "22 oz bag", 6.99, 22)],
         "Sweet white rice flour, whole grain brown rice flour, potato starch, whole grain sorghum flour, tapioca flour, xanthan gum.", (), VGF,
         "Gluten-free flour blend that swaps cup-for-cup for wheat flour in most recipes."),
        (PUREGROVE, "Blanched Almond Flour", "flour", N("1/4 cup (28 g)", 160, 14, 1, 0, 6, 3, 1, 0, 6), [S("16OZ", "16 oz bag", 9.99, 16)], "Blanched almonds.",
         ("tree nuts",), (*VGF, "grain-free"), "Finely ground blanched almond flour for grain-free and keto baking. Contains tree nuts."),
        (PUREGROVE, "Organic Coconut Flour", "flour", N("2 tbsp (15 g)", 60, 2, 1.5, 10, 9, 5, 1, 0, 2), [S("16OZ", "16 oz bag", 5.99, 16)], "Organic coconut flour.",
         (), (*VGF, "grain-free", "non-gmo"), "High-fiber organic coconut flour, grain free."),
        (STORE_BRAND, "Granulated Sugar", "sugar", tsp, [S("4LB", "4 lb bag", 3.49, 64)], "Sugar.", (), VGF, "Pure granulated cane sugar."),
        (STORE_BRAND, "Light Brown Sugar", "sugar", tsp, [S("2LB", "2 lb bag", 2.49, 32)], "Sugar, cane molasses.", (), VGF, "Soft light brown sugar."),
        (STORE_BRAND, "Powdered Sugar", "sugar", N("1/4 cup (30 g)", 120, 0, 0, 0, 30, 0, 29, 29, 0), [S("2LB", "2 lb bag", 2.49, 32)], "Sugar, corn starch.", (), VGF,
         "Confectioners' sugar for frosting and dusting."),
        (OAKMEADOW, "Organic Cane Sugar", "sugar", tsp, [S("4LB", "4 lb bag", 5.99, 64)], "Organic cane sugar.", (), (*VGF, "non-gmo"), "Organic granulated cane sugar."),
        (MONARCH, "Stevia Sweetener Packets", "sweetener", zero, [S("80CT", "80 packets", 4.99)], "Dextrose, stevia leaf extract (Reb A), natural flavors.", (), VGF,
         "Zero-calorie stevia sweetener packets; each is as sweet as 2 teaspoons of sugar."),
        (MONARCH, "Monk Fruit Sweetener, Granulated", "sweetener", N("1 tsp (4 g)", 0, 0, 0, 0, 4, 0, 0, 0, 0), [S("16OZ", "16 oz bag", 8.99, 16)],
         "Erythritol, monk fruit extract.", (), VGF, "Zero-calorie monk fruit and erythritol blend that measures cup-for-cup like sugar. Keto friendly."),
        (MONARCH, "Allulose & Monk Fruit Baking Blend", "sweetener", N("1 tsp (4 g)", 0, 0, 0, 0, 4, 0, 0, 0, 0), [S("12OZ", "12 oz bag", 9.99, 12)],
         "Allulose, erythritol, monk fruit extract.", (), VGF, "Sugar-free baking blend with allulose, which browns and caramelizes like sugar."),
        (MONARCH, "Liquid Stevia Drops", "sweetener", N("5 drops (0.2 mL)", 0, 0, 0, 0, 0, 0, 0, 0, 0), [S("2OZ", "2 fl oz bottle", 7.99, 2)],
         "Water, stevia leaf extract, natural flavors.", (), VGF, "Liquid stevia for coffee, tea, and smoothies."),
        (STORE_BRAND, "Zero Calorie Sucralose Sweetener Packets", "sweetener", zero, [S("100CT", "100 packets", 2.99)], "Dextrose, maltodextrin, sucralose.", (), VGF,
         "Zero-calorie sucralose sweetener packets."),
        (SUNDAY, "Classic Yellow Cake Mix", "baking-mix", N("1/10 package (43 g) dry mix", 160, 2, 1, 300, 35, 0, 19, 19, 2), [S("15OZ", "15.25 oz box", 1.99, 15.25)],
         "Sugar, enriched wheat flour, corn starch, leavening, palm oil, salt, soy lecithin, natural and artificial flavor.", ("wheat", "soy"), ("dairy-free",),
         "Moist yellow cake mix. Add eggs, oil, and water."),
        (SUNDAY, "Devil's Food Cake Mix", "baking-mix", N("1/10 package (43 g) dry mix", 160, 2.5, 1, 330, 34, 1, 18, 18, 2), [S("15OZ", "15.25 oz box", 1.99, 15.25)],
         "Sugar, enriched wheat flour, cocoa processed with alkali, palm oil, leavening, salt, soy lecithin.", ("wheat", "soy"), ("dairy-free",), "Rich chocolate cake mix."),
        (SUNDAY, "Fudge Brownie Mix", "baking-mix", N("1/20 package (28 g) dry mix", 120, 2, 1, 90, 24, 1, 17, 17, 1), [S("18OZ", "18.3 oz box", 2.49, 18.3)],
         "Sugar, enriched wheat flour, cocoa processed with alkali, palm oil, chocolate chips (sugar, chocolate, soy lecithin), salt.", ("wheat", "soy"), ("dairy-free",),
         "Chewy fudge brownie mix."),
        (SUNDAY, "Buttermilk Pancake & Waffle Mix", "pancake-mix", N("1/3 cup (40 g) dry mix", 150, 1.5, 0, 480, 30, 1, 4, 4, 4), [S("32OZ", "32 oz box", 3.49, 32)],
         "Enriched wheat flour, sugar, leavening, dextrose, buttermilk powder (milk), salt, soybean oil.", ("wheat", "milk"), (), "Complete buttermilk pancake mix; just add water."),
        (SUNDAY, "Protein Pancake & Waffle Mix", "pancake-mix", N("1/2 cup (53 g) dry mix", 200, 2, 0.5, 390, 30, 5, 3, 2, 14), [S("20OZ", "20 oz box", 5.99, 20)],
         "Whole grain wheat flour, whole grain oat flour, whey protein concentrate (milk), pea protein, leavening, cane sugar, salt.", ("wheat", "milk"), ("whole-grain",),
         "Whole grain pancake mix with 14 g protein per serving."),
        (FREESTONE, "Gluten-Free Pancake Mix", "pancake-mix", N("1/3 cup (43 g) dry mix", 160, 1, 0, 450, 35, 1, 5, 5, 2), [S("16OZ", "16 oz box", 4.99, 16)],
         "Rice flour, potato starch, tapioca starch, cane sugar, leavening, salt, xanthan gum.", (), VGF, "Gluten-free pancake mix. Add eggs, milk, and oil."),
        (FREESTONE, "Gluten-Free Chocolate Chip Cookie Mix", "baking-mix", N("1/16 package (26 g) dry mix", 110, 1.5, 1, 70, 22, 1, 14, 14, 1), [S("15OZ", "15 oz box", 4.99, 15)],
         "Cane sugar, rice flour, semi-sweet chocolate chips (sugar, chocolate, cocoa butter, soy lecithin), potato starch, tapioca starch, baking soda, salt, xanthan gum.",
         ("soy",), ("gluten-free", "dairy-free"), "Gluten-free chocolate chip cookie mix."),
        (MONARCH, "Sugar Free Brownie Mix", "baking-mix", N("1/16 package (22 g) dry mix", 70, 2.5, 1, 70, 16, 3, 0, 0, 2), [S("10OZ", "10.5 oz box", 6.99, 10.5)],
         "Almond flour, allulose, cocoa, erythritol, chocolate chips (unsweetened chocolate, erythritol, cocoa butter), baking soda, salt, monk fruit extract.", ("tree nuts",),
         ("gluten-free", "grain-free", "dairy-free"), "Sugar free, grain-free brownie mix sweetened with allulose and monk fruit."),
        (STORE_BRAND, "Cornbread Mix", "baking-mix", N("1/4 cup (31 g) dry mix", 120, 1.5, 0, 270, 24, 1, 7, 7, 2), [S("8OZ", "8.5 oz box", 0.99, 8.5)],
         "Enriched wheat flour, degermed yellow corn meal, sugar, lard, leavening, salt.", ("wheat",), (), "Sweet cornbread and muffin mix. Contains lard."),
        (STORE_BRAND, "Semi-Sweet Chocolate Chips", "baking-chips", N("1 tbsp (15 g)", 70, 4, 2.5, 0, 9, 1, 8, 8, 1), [S("12OZ", "12 oz bag", 2.99, 12)],
         "Sugar, chocolate, cocoa butter, milkfat, soy lecithin, vanilla extract.", ("milk", "soy"), ("gluten-free",), "Semi-sweet chocolate chips for baking."),
        (STORE_BRAND, "Dairy-Free Semi-Sweet Chocolate Chips", "baking-chips", N("1 tbsp (15 g)", 70, 4, 2.5, 0, 9, 1, 8, 8, 1), [S("10OZ", "10 oz bag", 3.99, 10)],
         "Cane sugar, unsweetened chocolate, cocoa butter.", (), VGF, "Vegan semi-sweet chocolate chips made without milk."),
        (MONARCH, "Sugar Free Dark Chocolate Baking Chips", "baking-chips", N("1 tbsp (15 g)", 60, 5, 3, 0, 9, 3, 0, 0, 1), [S("9OZ", "9 oz bag", 5.99, 9)],
         "Unsweetened chocolate, erythritol, inulin, cocoa butter, stevia leaf extract, vanilla extract.", (), VGF,
         "Dark chocolate baking chips with no sugar, sweetened with erythritol and stevia."),
    ]  # fmt: skip
    return _rows(rows, ("sugar-free", "zero-calorie", "keto", "high-fiber", "high-protein"))


def spices() -> list[ProductSeed]:
    zero = N("1/4 tsp (0.6 g)", 0, 0, 0, 0, 0, 0, 0, 0, 0)
    small = [S("3OZ", "3 oz", 2.49, 3)]
    rows: list[Row] = [
        (STORE_BRAND, "Ground Black Pepper", "spices", zero, [S("3OZ", "3 oz tin", 2.99, 3)], "Black pepper.", (), VGF, "Finely ground black pepper."),
        (STORE_BRAND, "Iodized Salt", "salt", N("1/4 tsp (1.5 g)", 0, 0, 0, 590, 0, 0, 0, 0, 0), [S("26OZ", "26 oz canister", 0.99, 26)],
         "Salt, calcium silicate, dextrose, potassium iodide.", (), VGF, "Table salt with iodine."),
        (STORE_BRAND, "Kosher Salt", "salt", N("1/4 tsp (1.2 g)", 0, 0, 0, 480, 0, 0, 0, 0, 0), [S("48OZ", "3 lb box", 3.49, 48)], "Salt.", (), (*VGF, "kosher"),
         "Coarse kosher salt for cooking and brining."),
        (STORE_BRAND, "Garlic Powder", "spices", zero, small, "Garlic.", (), VGF, "Ground dehydrated garlic."),
        (STORE_BRAND, "Onion Powder", "spices", zero, small, "Onion.", (), VGF, "Ground dehydrated onion."),
        (STORE_BRAND, "Chili Powder", "spices", N("1/4 tsp (0.7 g)", 0, 0, 0, 25, 0, 0, 0, 0, 0), small, "Chili pepper, cumin, salt, oregano, garlic.", (), VGF,
         "Classic chili powder blend."),
        (STORE_BRAND, "Ground Cinnamon", "spices", zero, small, "Cinnamon.", (), VGF, "Ground cassia cinnamon."),
        (STORE_BRAND, "Ground Cumin", "spices", zero, small, "Cumin.", (), VGF, "Earthy ground cumin."),
        (SAFFRON, "Organic Smoked Paprika", "spices", zero, [S("2OZ", "2 oz jar", 5.49, 2)], "Organic smoked paprika.", (), (*VGF, "non-gmo"), "Organic Spanish smoked paprika."),
        (SAFFRON, "Organic Ground Turmeric", "spices", zero, [S("2OZ", "2 oz jar", 5.49, 2)], "Organic turmeric.", (), (*VGF, "non-gmo"), "Organic ground turmeric."),
        (SAFFRON, "Italian Seasoning", "spices", zero, [S("1OZ", "1 oz jar", 4.49, 1)], "Marjoram, thyme, rosemary, savory, sage, oregano, basil.", (), (*VGF, "no-salt-added"),
         "Salt-free blend of Italian herbs."),
        (SAFFRON, "Everything Bagel Seasoning", "spices", N("1/4 tsp (1 g)", 5, 0, 0, 55, 0, 0, 0, 0, 0), [S("2OZ", "2.3 oz jar", 4.99, 2.3)],
         "Sesame seeds, dried garlic, dried onion, poppy seeds, sea salt.", ("sesame",), VGF, "Sesame, poppy seed, garlic, and onion topping."),
        (SAFFRON, "Salt-Free All-Purpose Seasoning", "spices", zero, [S("2OZ", "2.5 oz jar", 4.99, 2.5)],
         "Onion, garlic, black pepper, parsley, celery seed, basil, lemon peel, thyme, cayenne.", (), (*VGF, "no-salt-added"),
         "All-purpose herb and spice blend with no salt, for low sodium cooking."),
        (SAFFRON, "Taco Seasoning", "spices", N("2 tsp (5.6 g)", 15, 0, 0, 390, 3, 0, 1, 1, 0), [S("1OZ", "1 oz packet", 1.29, 1)],
         "Chili pepper, salt, maltodextrin, onion, garlic, cumin, sugar, paprika, oregano.", (), VGF, "Taco seasoning for 1 lb of meat. 390 mg sodium per serving."),
        (SAFFRON, "Low Sodium Taco Seasoning", "spices", N("2 tsp (5.6 g)", 15, 0, 0, 65, 3, 0, 1, 0, 0), [S("1OZ", "1 oz packet", 1.49, 1)],
         "Chili pepper, onion, garlic, cumin, paprika, oregano, sea salt.", (), VGF, "Taco seasoning with 85% less sodium than our regular."),
        (SAFFRON, "Texas Brisket Rub", "spices", N("1 tsp (4 g)", 10, 0, 0, 380, 2, 0, 1, 1, 0), [S("6OZ", "6 oz shaker", 6.99, 6)],
         "Salt, coarse black pepper, brown sugar, paprika, garlic, onion, chili pepper.", (), VGF, "Salt-and-pepper forward barbecue rub for brisket and ribs."),
        (SAFFRON, "Cajun Seasoning", "spices", N("1/4 tsp (0.6 g)", 0, 0, 0, 125, 0, 0, 0, 0, 0), [S("3OZ", "3 oz shaker", 3.99, 3)],
         "Salt, paprika, garlic, cayenne, black pepper, onion, thyme, oregano.", (), VGF, "Spicy Louisiana-style Cajun seasoning."),
    ]  # fmt: skip
    return _rows(rows, ("low-sodium",))


def canned_fish() -> list[ProductSeed]:
    oz2 = "2 oz drained (56 g)"
    can = [S("5OZ", "5 oz can", 1.49, 5), S("4PK", "4 x 5 oz cans", 5.49, 20)]
    FS = ("fish", "soy")
    WC = ("wild-caught", "gluten-free", "dairy-free")
    rows: list[Row] = [
        (NORTHCAPE, "Chunk Light Tuna in Water", "canned-fish", N(oz2, 50, 0.5, 0, 180, 0, 0, 0, 0, 11), can,
         "Light tuna, water, vegetable broth (contains soy), salt.", FS, WC, "Wild-caught chunk light skipjack tuna packed in water. 11 g protein, 50 calories."),
        (NORTHCAPE, "Chunk Light Tuna in Oil", "canned-fish", N(oz2, 90, 4.5, 1, 210, 0, 0, 0, 0, 12), can,
         "Light tuna, soybean oil, vegetable broth (contains soy), salt.", FS, WC, "Chunk light tuna packed in soybean oil; richer, with more fat and calories than tuna in water."),
        (NORTHCAPE, "Solid White Albacore Tuna in Water", "canned-fish", N(oz2, 70, 1, 0, 180, 0, 0, 0, 0, 15), [S("5OZ", "5 oz can", 2.29, 5)],
         "White tuna, water, vegetable broth (contains soy), salt.", FS, WC, "Firm, mild solid white albacore tuna in water."),
        (NORTHCAPE, "Solid White Albacore Tuna in Olive Oil", "canned-fish", N(oz2, 110, 6, 1, 180, 0, 0, 0, 0, 14), [S("5OZ", "5 oz can", 2.79, 5)],
         "White tuna, olive oil, salt.", ("fish",), WC, "Solid white albacore tuna packed in olive oil."),
        (NORTHCAPE, "Very Low Sodium Chunk Light Tuna in Water", "canned-fish", N(oz2, 50, 0.5, 0, 35, 0, 0, 0, 0, 12), [S("5OZ", "5 oz can", 1.79, 5)],
         "Light tuna, water.", ("fish",), (*WC, "no-salt-added"), "Chunk light tuna with no salt or broth added: 35 mg sodium per serving."),
        (NORTHCAPE, "Wild Alaskan Pink Salmon", "canned-fish", N("1/4 cup (63 g)", 90, 4, 1, 260, 0, 0, 0, 0, 13), [S("14OZ", "14.75 oz can", 4.99, 14.75)],
         "Pink salmon, salt.", ("fish",), WC, "Traditional canned wild pink salmon with skin and soft, edible bones."),
        (NORTHCAPE, "Wild Sockeye Red Salmon", "canned-fish", N("1/4 cup (63 g)", 110, 6, 1.5, 230, 0, 0, 0, 0, 14), [S("6OZ", "6 oz can", 5.49, 6)],
         "Sockeye salmon, salt.", ("fish",), WC, "Rich wild sockeye salmon, skinless and boneless."),
        (NORTHCAPE, "Sardines in Olive Oil", "canned-fish", N("1 can drained (85 g)", 190, 11, 2.5, 300, 0, 0, 0, 0, 21), [S("4OZ", "4.4 oz can", 2.49, 4.4)],
         "Sardines, olive oil, salt.", ("fish",), WC, "Wild-caught sardines in olive oil, 21 g protein per can."),
        (STORE_BRAND, "Chunk Light Tuna in Water", "canned-fish", N(oz2, 50, 0.5, 0, 200, 0, 0, 0, 0, 11), [S("5OZ", "5 oz can", 0.99, 5), S("4PK", "4 x 5 oz cans", 3.79, 20)],
         "Light tuna, water, vegetable broth (contains soy), salt.", FS, WC, "Chunk light tuna in water."),
        (STORE_BRAND, "Chunk Light Tuna in Oil", "canned-fish", N(oz2, 90, 4.5, 1, 220, 0, 0, 0, 0, 12), [S("5OZ", "5 oz can", 0.99, 5)],
         "Light tuna, soybean oil, vegetable broth (contains soy), salt.", FS, WC, "Chunk light tuna in soybean oil."),
    ]  # fmt: skip
    return _rows(rows, ("high-protein", "low-fat", "low-sodium", "keto"))


def products() -> list[ProductSeed]:
    return [
        *cereal(), *oatmeal(), *pasta_rice(), *canned(), *soups(), *spreads(), *oils_sauces(),
        *condiments(), *baking(), *spices(), *canned_fish(),
    ]  # fmt: skip


__all__ = ["products"]
