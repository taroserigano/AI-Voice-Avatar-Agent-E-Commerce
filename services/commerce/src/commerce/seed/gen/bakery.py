"""Bakery & Bread: sandwich breads, bagels, English muffins, tortillas, buns, pita and naan,
muffins, croissants, cakes, pies, and cookies.

Built around the questions shoppers ask of bread: 100% whole wheat vs multigrain, gluten
free vs keto (low-carb breads are usually made with wheat), sprouted, low sodium, and
sugar free. Values are typical label values per serving.
"""

from __future__ import annotations

from commerce.seed.data import Nutrition, ProductSeed
from commerce.seed.gen.common import FROZEN, REFRIGERATED, STORE_BRAND, Size, cents, food

CAT = "bakery"
HEARTH = "Hearthstone Bakery"  # mainstream and artisan
OAKMEADOW = "Oakmeadow Organics"  # organic, sprouted
FREESTONE = "Freestone Gluten Free"
LEANLOAF = "Lean Loaf Co."  # keto and low-carb
MESQUITE = "Mesquite Hill Tortilleria"

BREADBOX = "Store at room temperature in a cool, dry place; freeze to keep longer."
BREAD_CLAIMS = ("high-fiber", "high-protein", "keto", "low-sodium", "sugar-free", "no-added-sugar")
SWEET_CLAIMS = ("fat-free", "sugar-free", "no-added-sugar", "low-sugar")
ENRICHED = "enriched wheat flour (wheat flour, niacin, reduced iron, thiamin mononitrate, riboflavin, folic acid)"


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


def _bake(
    brand: str,
    title: str,
    ptype: str,
    n: Nutrition,
    sizes: list[Size],
    ingredients: str,
    allergens: tuple[str, ...],
    intro: str,
    *,
    tags: tuple[str, ...] = (),
    specs: dict[str, str] | None = None,
    claims: tuple[str, ...] = BREAD_CLAIMS,
    storage: str = BREADBOX,
) -> ProductSeed:
    organic = title.startswith("Organic")
    text = ingredients[0].upper() + ingredients[1:]
    return food(
        category=CAT, product_type=ptype, brand=brand, title=title, sizes=sizes, nutrition=n,
        ingredients=text, allergens=allergens, tags=[*(["organic"] if organic else []), *tags],
        claims=claims, specs=specs, intro=intro, storage=storage,
    )  # fmt: skip


def breads() -> list[ProductSeed]:
    W = ("wheat",)
    VG = ("vegan", "dairy-free")
    GF = ("gluten-free", "dairy-free")
    rows = [  # brand, title, facts, ingredients, allergens, tags, style, size, intro, storage
        (STORE_BRAND, "Classic White Sandwich Bread", N("1 slice (28 g)", 70, 1, 0, 130, 13, 0, 1, 1, 2),
         f"{ENRICHED}, water, sugar, yeast, soybean oil, salt, wheat gluten, calcium propionate (preservative).", W, VG, "White",
         S("20OZ", "20 oz loaf", 1.49, 20), "Soft white sandwich bread made with enriched flour. Not whole grain.", BREADBOX),
        (STORE_BRAND, "100% Whole Wheat Bread", N("1 slice (38 g)", 100, 1.5, 0, 170, 19, 3, 3, 3, 5),
         "whole wheat flour, water, sugar, wheat gluten, yeast, soybean oil, salt, cultured wheat flour, vinegar.", W, (*VG, "whole-grain"), "100% whole wheat",
         S("20OZ", "20 oz loaf", 2.49, 20), "Sandwich bread made with 100% whole wheat flour and no refined flour.", BREADBOX),
        (STORE_BRAND, "Honey Wheat Bread", N("1 slice (32 g)", 80, 1, 0, 140, 15, 1, 3, 3, 3),
         f"{ENRICHED}, water, whole wheat flour, honey, sugar, yeast, soybean oil, salt, wheat gluten.", W, ("dairy-free",), "Wheat (enriched flour blend)",
         S("20OZ", "20 oz loaf", 1.99, 20), "Soft wheat bread sweetened with honey. Made mostly with enriched white flour, so it is not 100% whole wheat.", BREADBOX),
        (STORE_BRAND, "Multigrain Bread", N("1 slice (43 g)", 110, 2, 0, 180, 20, 3, 3, 3, 5),
         f"{ENRICHED}, water, whole wheat flour, oats, cracked wheat, rye flour, millet, flaxseed, sunflower seeds, brown sugar, yeast, salt, wheat gluten.",
         W, VG, "Multigrain (not 100% whole grain)", S("24OZ", "24 oz loaf", 2.99, 24),
         "Hearty bread with seven grains and seeds. Multigrain means several grains, not all whole grain; the first ingredient is enriched flour.", BREADBOX),
        (HEARTH, "San Francisco Style Sourdough", N("1 slice (50 g)", 130, 0.5, 0, 270, 25, 1, 1, 0, 5),
         f"{ENRICHED}, water, sourdough culture (wheat), salt.", W, VG, "Sourdough",
         S("24OZ", "24 oz loaf", 4.49, 24), "Tangy, naturally leavened sourdough with a chewy crust. Just flour, water, culture, and salt.", BREADBOX),
        (HEARTH, "Seeded Rye Bread", N("1 slice (32 g)", 80, 1, 0, 210, 15, 2, 1, 1, 3),
         f"{ENRICHED}, water, rye flour, caraway seeds, molasses, salt, yeast.", W, VG, "Rye",
         S("16OZ", "16 oz loaf", 3.99, 16), "Deli-style rye bread with caraway seeds. Rye contains gluten.", BREADBOX),
        (HEARTH, "Italian Bread", N("1 slice (43 g)", 110, 1, 0, 230, 21, 1, 1, 0, 4),
         f"{ENRICHED}, water, yeast, salt, olive oil.", W, VG, "Italian",
         S("16OZ", "16 oz loaf", 2.99, 16), "Soft Italian loaf with a light, crisp crust.", BREADBOX),
        (HEARTH, "French Baguette", N("1/4 baguette (57 g)", 150, 0.5, 0, 330, 31, 1, 0, 0, 5),
         f"{ENRICHED}, water, salt, yeast.", W, VG, "French baguette",
         S("12OZ", "12 oz baguette", 2.49, 12), "Crusty French baguette baked fresh daily.", BREADBOX),
        (HEARTH, "Whole Grain Oat Bread", N("1 slice (43 g)", 110, 1.5, 0, 170, 20, 3, 3, 2, 5),
         "whole wheat flour, water, rolled oats, wheat gluten, honey, yeast, canola oil, salt.", W, ("whole-grain", "dairy-free"), "Whole grain",
         S("24OZ", "24 oz loaf", 3.99, 24), "Whole grain bread topped with rolled oats and lightly sweetened with honey.", BREADBOX),
        (HEARTH, "Butter Top Potato Bread", N("1 slice (34 g)", 90, 1.5, 0.5, 160, 16, 1, 3, 3, 3),
         f"{ENRICHED}, water, potato flour, sugar, butter (cream, salt), nonfat milk, yeast, salt.", ("wheat", "milk"), (), "Potato",
         S("20OZ", "20 oz loaf", 3.49, 20), "Soft, slightly sweet potato bread with a buttery top.", BREADBOX),
        (HEARTH, "Brioche Loaf", N("1 slice (38 g)", 120, 4, 2, 125, 17, 1, 4, 4, 3),
         f"{ENRICHED}, eggs, butter (cream), sugar, water, yeast, whole milk, salt.", ("wheat", "egg", "milk"), (), "Brioche",
         S("17OZ", "17.6 oz loaf", 4.99, 17.6), "Rich French brioche made with eggs and butter.", BREADBOX),
        (HEARTH, "Cinnamon Raisin Swirl Bread", N("1 slice (38 g)", 100, 1.5, 0, 110, 19, 1, 7, 5, 3),
         f"{ENRICHED}, raisins, water, sugar, cinnamon, nonfat milk, yeast, soybean oil, salt.", ("wheat", "milk"), (), "Cinnamon raisin",
         S("16OZ", "16 oz loaf", 3.79, 16), "Raisin bread with a cinnamon-sugar swirl.", BREADBOX),
        (OAKMEADOW, "Organic Sprouted Whole Grain Bread", N("1 slice (34 g)", 80, 0.5, 0, 75, 15, 3, 0, 0, 5),
         "organic sprouted whole wheat, filtered water, organic sprouted barley, organic sprouted millet, organic sprouted lentils, organic sprouted soybeans, "
         "organic sprouted spelt, fresh yeast, organic wheat gluten, sea salt.", ("wheat", "soy"), (*VG, "whole-grain", "non-gmo"), "Sprouted whole grain (flourless)",
         S("24OZ", "24 oz loaf", 6.49, 24), "Flourless bread made from sprouted whole grains and legumes, with no added sugar. Sold frozen.", FROZEN),
        (OAKMEADOW, "Organic Sprouted Low Sodium Bread", N("1 slice (34 g)", 80, 0.5, 0, 0, 15, 3, 0, 0, 4),
         "organic sprouted whole wheat, filtered water, organic sprouted barley, organic sprouted millet, organic sprouted lentils, organic sprouted soybeans, "
         "organic sprouted spelt, fresh yeast, organic wheat gluten.", ("wheat", "soy"), (*VG, "whole-grain", "non-gmo", "no-salt-added"), "Sprouted whole grain (flourless)",
         S("24OZ", "24 oz loaf", 6.49, 24), "Our sprouted whole grain bread made with no salt at all and no added sugar. Sold frozen.", FROZEN),
        (OAKMEADOW, "Organic Seeded Whole Grain Bread", N("1 slice (45 g)", 120, 2, 0, 170, 22, 5, 5, 5, 6),
         "organic whole wheat flour, water, organic cane sugar, organic seed mix (sunflower, flax, pumpkin, sesame), organic wheat gluten, organic oats, sea salt, yeast.",
         ("wheat", "sesame"), (*VG, "whole-grain", "non-gmo"), "Whole grain, seeded",
         S("27OZ", "27 oz loaf", 5.99, 27), "Organic whole grain bread loaded with seeds, 5 g fiber per slice.", BREADBOX),
        (OAKMEADOW, "Organic Thin-Sliced Whole Wheat Bread", N("1 slice (28 g)", 70, 1, 0, 120, 13, 2, 2, 2, 3),
         "organic whole wheat flour, water, organic cane sugar, organic wheat gluten, sea salt, yeast, organic sunflower oil.", W, (*VG, "whole-grain", "non-gmo"), "100% whole wheat",
         S("20OZ", "20 oz loaf", 5.49, 20), "Organic 100% whole wheat bread cut in thin slices, 70 calories each.", BREADBOX),
        (FREESTONE, "Gluten-Free White Sandwich Bread", N("1 slice (32 g)", 80, 2.5, 0, 150, 14, 1, 2, 2, 1),
         "water, tapioca starch, brown rice flour, egg whites, canola oil, sugar, potato starch, yeast, xanthan gum, salt, cellulose.", ("egg",), GF, "Gluten-free white",
         S("18OZ", "18 oz loaf", 5.99, 18), "Soft gluten-free sandwich bread made with rice flour and tapioca. Contains egg. Sold frozen.", FROZEN),
        (FREESTONE, "Gluten-Free Multigrain Seeded Bread", N("1 slice (35 g)", 90, 3, 0, 140, 15, 2, 2, 2, 2),
         "water, tapioca starch, brown rice flour, egg whites, sorghum flour, sunflower seeds, flaxseed, millet, canola oil, cane sugar, yeast, xanthan gum, salt.",
         ("egg",), GF, "Gluten-free multigrain", S("18OZ", "18 oz loaf", 6.49, 18), "Gluten-free multigrain bread with sunflower and flax seeds. Contains egg. Sold frozen.", FROZEN),
        (FREESTONE, "Gluten-Free Vegan Sandwich Bread", N("1 slice (34 g)", 90, 2.5, 0, 160, 16, 2, 2, 2, 1),
         "water, tapioca starch, brown rice flour, potato starch, sunflower oil, psyllium husk, cane sugar, yeast, salt, apple cider vinegar.",
         (), (*GF, "vegan"), "Gluten-free white", S("18OZ", "18 oz loaf", 6.49, 18), "Gluten-free and vegan sandwich bread, made without eggs, dairy, or wheat. Sold frozen.", FROZEN),
        (LEANLOAF, "Keto White Bread", N("1 slice (32 g)", 45, 1.5, 0, 150, 9, 7, 0, 0, 5),
         "water, wheat protein isolate, resistant wheat starch, oat fiber, yeast, avocado oil, vinegar, salt, cultured wheat starch.", W, VG, "Keto / low-carb",
         S("16OZ", "16 oz loaf", 5.99, 16), "Low-carb keto bread with 2 g net carbs and 0 g sugar per slice. Made with wheat protein, so it is NOT gluten free.", BREADBOX),
        (LEANLOAF, "Keto Seeded Bread", N("1 slice (34 g)", 50, 2.5, 0, 140, 9, 7, 0, 0, 5),
         "water, wheat protein isolate, resistant wheat starch, oat fiber, sesame seeds, flaxseed, sunflower seeds, yeast, salt.", ("wheat", "sesame"), VG, "Keto / low-carb",
         S("16OZ", "16 oz loaf", 6.29, 16), "Seeded keto bread with 2 g net carbs per slice. Contains wheat; not gluten free.", BREADBOX),
        (LEANLOAF, "Low-Carb Multigrain Bread", N("1 slice (32 g)", 60, 1.5, 0, 160, 10, 6, 1, 0, 5),
         "water, wheat protein isolate, oat fiber, whole wheat flour, flaxseed, rye flour, yeast, salt, sunflower oil.", W, VG, "Keto / low-carb",
         S("16OZ", "16 oz loaf", 5.99, 16), "Multigrain low-carb bread with 4 g net carbs per slice. Contains wheat.", BREADBOX),
    ]  # fmt: skip
    return [
        _bake(brand, title, "bread", n, [size], ing, allergens, intro, tags=tags, specs={"Style": style}, storage=storage)
        for brand, title, n, ing, allergens, tags, style, size, intro, storage in rows
    ]  # fmt: skip


def bagels_muffins_tortillas() -> list[ProductSeed]:
    W = ("wheat",)
    bagel = "1 bagel (95 g)"
    rows = [  # brand, title, type, facts, ingredients, allergens, tags, sizes, intro, storage
        (STORE_BRAND, "Plain Bagels", "bagels", N(bagel, 250, 1.5, 0, 420, 50, 2, 5, 4, 10),
         f"{ENRICHED}, water, sugar, yeast, salt, malted barley flour.", W, ("vegan", "dairy-free"), [S("6CT", "6 bagels", 2.99, 20)],
         "New York-style plain bagels, boiled then baked.", BREADBOX),
        (STORE_BRAND, "Everything Bagels", "bagels", N(bagel, 260, 2.5, 0, 480, 50, 2, 5, 4, 10),
         f"{ENRICHED}, water, sugar, yeast, sesame seeds, poppy seeds, dried onion, dried garlic, salt.", ("wheat", "sesame"), ("vegan", "dairy-free"),
         [S("6CT", "6 bagels", 2.99, 20)], "Bagels topped with sesame, poppy seed, onion, and garlic.", BREADBOX),
        (HEARTH, "Cinnamon Raisin Bagels", "bagels", N(bagel, 260, 1.5, 0, 340, 55, 2, 11, 8, 9),
         f"{ENRICHED}, water, raisins, sugar, cinnamon, yeast, salt.", W, ("vegan", "dairy-free"), [S("6CT", "6 bagels", 3.99, 20)],
         "Chewy bagels studded with raisins and cinnamon.", BREADBOX),
        (HEARTH, "100% Whole Wheat Bagels", "bagels", N(bagel, 240, 2, 0, 410, 48, 7, 5, 4, 11),
         "whole wheat flour, water, sugar, wheat gluten, yeast, salt.", W, ("vegan", "dairy-free", "whole-grain"), [S("6CT", "6 bagels", 3.99, 20)],
         "Bagels made with 100% whole wheat flour, with 7 g fiber each.", BREADBOX),
        (HEARTH, "Blueberry Bagels", "bagels", N(bagel, 270, 1.5, 0, 380, 56, 2, 12, 10, 9),
         f"{ENRICHED}, water, dried blueberries, sugar, yeast, salt, natural flavor.", W, ("vegan", "dairy-free"), [S("6CT", "6 bagels", 3.99, 20)],
         "Sweet bagels with dried blueberries.", BREADBOX),
        (FREESTONE, "Gluten-Free Plain Bagels", "bagels", N(bagel, 260, 6, 1, 450, 48, 3, 5, 4, 4),
         "water, tapioca starch, brown rice flour, egg whites, sugar, canola oil, yeast, psyllium husk, xanthan gum, salt.", ("egg",), ("gluten-free", "dairy-free"),
         [S("4CT", "4 bagels", 6.49, 14)], "Gluten-free bagels made with rice flour. Contains egg. Sold frozen.", FROZEN),
        (LEANLOAF, "Keto Everything Bagels", "bagels", N("1 bagel (85 g)", 130, 5, 0.5, 300, 20, 17, 1, 0, 12),
         "water, wheat protein isolate, oat fiber, resistant wheat starch, sesame seeds, poppy seeds, dried onion, dried garlic, yeast, salt.", ("wheat", "sesame"),
         ("vegan", "dairy-free"), [S("4CT", "4 bagels", 6.99, 12)], "Low-carb everything bagels with 3 g net carbs and 12 g protein each. Contains wheat; not gluten free.", BREADBOX),
        (STORE_BRAND, "Original English Muffins", "english-muffins", N("1 muffin (57 g)", 120, 1, 0, 220, 25, 1, 1, 1, 4),
         f"{ENRICHED}, water, farina, yeast, sugar, salt, cornmeal, calcium propionate.", W, ("vegan", "dairy-free"), [S("6CT", "6 muffins", 1.99, 12)],
         "Classic nooks-and-crannies English muffins.", BREADBOX),
        (HEARTH, "100% Whole Wheat English Muffins", "english-muffins", N("1 muffin (57 g)", 120, 1, 0, 210, 23, 4, 1, 1, 5),
         "whole wheat flour, water, yeast, wheat gluten, sugar, salt, cornmeal.", W, ("vegan", "dairy-free", "whole-grain"), [S("6CT", "6 muffins", 3.49, 12)],
         "English muffins made with 100% whole wheat.", BREADBOX),
        (HEARTH, "Sourdough English Muffins", "english-muffins", N("1 muffin (57 g)", 130, 1, 0, 230, 26, 1, 1, 1, 4),
         f"{ENRICHED}, water, sourdough culture, yeast, salt, cornmeal.", W, ("vegan", "dairy-free"), [S("6CT", "6 muffins", 3.49, 12)],
         "Tangy sourdough English muffins.", BREADBOX),
        (FREESTONE, "Gluten-Free English Muffins", "english-muffins", N("1 muffin (65 g)", 150, 4, 0.5, 290, 27, 2, 3, 3, 2),
         "water, brown rice flour, tapioca starch, egg whites, sugar, canola oil, yeast, xanthan gum, salt.", ("egg",), ("gluten-free", "dairy-free"),
         [S("4CT", "4 muffins", 5.99, 9)], "Gluten-free English muffins. Contains egg. Sold frozen.", FROZEN),
        (MESQUITE, "Flour Tortillas, Soft Taco Size", "tortillas", N("1 tortilla (45 g)", 140, 3.5, 1.5, 380, 23, 1, 1, 0, 4),
         f"{ENRICHED}, water, palm oil shortening, salt, baking powder, sugar, calcium propionate.", W, ("vegan", "dairy-free"),
         [S("10CT", "10 tortillas", 2.99, 16), S("20CT", "20 tortillas", 4.99, 32)], "Soft, pliable flour tortillas made with vegetable shortening (no lard).", BREADBOX),
        (MESQUITE, "Burrito Size Flour Tortillas", "tortillas", N("1 tortilla (71 g)", 210, 5, 2, 560, 36, 1, 1, 0, 6),
         f"{ENRICHED}, water, palm oil shortening, salt, baking powder, sugar, calcium propionate.", W, ("vegan", "dairy-free"),
         [S("8CT", "8 tortillas", 3.49, 20)], "Large 10-inch flour tortillas for burritos.", BREADBOX),
        (MESQUITE, "Yellow Corn Tortillas", "tortillas", N("2 tortillas (52 g)", 110, 1.5, 0, 20, 23, 3, 0, 0, 3),
         "ground corn treated with lime, water, cellulose gum, propionic acid.", (), ("vegan", "dairy-free", "gluten-free", "whole-grain"),
         [S("30CT", "30 tortillas", 2.49, 26)], "Traditional stone-ground corn tortillas, naturally gluten free and very low in sodium.", BREADBOX),
        (MESQUITE, "White Corn Tortillas", "tortillas", N("2 tortillas (52 g)", 110, 1.5, 0, 25, 23, 3, 0, 0, 3),
         "ground white corn treated with lime, water, cellulose gum, propionic acid.", (), ("vegan", "dairy-free", "gluten-free", "whole-grain"),
         [S("30CT", "30 tortillas", 2.49, 26)], "Soft white corn tortillas, naturally gluten free.", BREADBOX),
        (MESQUITE, "Whole Wheat Flour Tortillas", "tortillas", N("1 tortilla (45 g)", 130, 3.5, 1.5, 310, 21, 3, 1, 0, 4),
         "whole wheat flour, water, palm oil shortening, salt, baking powder, sugar.", W, ("vegan", "dairy-free", "whole-grain"),
         [S("10CT", "10 tortillas", 3.29, 16)], "Flour tortillas made with whole wheat.", BREADBOX),
        (LEANLOAF, "Low-Carb Flour Tortillas", "tortillas", N("1 tortilla (45 g)", 50, 2, 0, 280, 14, 11, 0, 0, 5),
         "water, modified wheat starch, wheat protein isolate, oat fiber, palm oil shortening, baking powder, salt.", W, ("vegan", "dairy-free"),
         [S("8CT", "8 tortillas", 4.49, 12)], "Low-carb tortillas with 3 g net carbs and 11 g fiber each. Contains wheat; not gluten free.", BREADBOX),
        (STORE_BRAND, "Flour Tortillas, Fajita Size", "tortillas", N("1 tortilla (32 g)", 100, 2.5, 1, 260, 16, 1, 1, 0, 3),
         f"{ENRICHED}, water, palm oil shortening, salt, baking powder, sugar.", W, ("vegan", "dairy-free"),
         [S("20CT", "20 tortillas", 2.99, 22)], "Small 6-inch flour tortillas for fajitas and tacos.", BREADBOX),
        (FREESTONE, "Grain-Free Almond Flour Tortillas", "tortillas", N("2 tortillas (42 g)", 140, 8, 1, 260, 13, 3, 1, 0, 4),
         "almond flour, tapioca flour, water, cassava flour, apple cider vinegar, sea salt, xanthan gum.", ("tree nuts",),
         ("vegan", "dairy-free", "gluten-free", "grain-free"), [S("8CT", "8 tortillas", 7.99, 7)],
         "Grain-free tortillas made with almond and cassava flour. Contains tree nuts. Sold refrigerated.", REFRIGERATED),
    ]  # fmt: skip
    return [
        _bake(brand, title, ptype, n, sizes, ing, allergens, intro, tags=tags, storage=storage)
        for brand, title, ptype, n, ing, allergens, tags, sizes, intro, storage in rows
    ]  # fmt: skip


def buns_flatbreads() -> list[ProductSeed]:
    W = ("wheat",)
    rows = [  # brand, title, type, facts, ingredients, allergens, tags, sizes, intro, storage
        (STORE_BRAND, "Hamburger Buns", "buns", N("1 bun (53 g)", 140, 2, 0.5, 220, 26, 1, 3, 3, 4),
         f"{ENRICHED}, water, sugar, yeast, soybean oil, salt, wheat gluten, calcium propionate.", W, ("vegan", "dairy-free"),
         [S("8CT", "8 buns", 1.49, 15)], "Soft white hamburger buns.", BREADBOX),
        (STORE_BRAND, "Hot Dog Buns", "buns", N("1 bun (50 g)", 130, 2, 0.5, 210, 24, 1, 3, 3, 4),
         f"{ENRICHED}, water, sugar, yeast, soybean oil, salt, wheat gluten, calcium propionate.", W, ("vegan", "dairy-free"),
         [S("8CT", "8 buns", 1.49, 14)], "Soft white hot dog buns.", BREADBOX),
        (HEARTH, "Brioche Hamburger Buns", "buns", N("1 bun (70 g)", 210, 6, 3, 280, 33, 1, 6, 6, 6),
         f"{ENRICHED}, eggs, sugar, butter (cream), water, yeast, whole milk, salt.", ("wheat", "egg", "milk"), (),
         [S("8CT", "8 buns", 4.49, 20)], "Golden, buttery brioche buns made with eggs and butter.", BREADBOX),
        (HEARTH, "100% Whole Wheat Hamburger Buns", "buns", N("1 bun (57 g)", 140, 2, 0, 210, 24, 4, 3, 3, 6),
         "whole wheat flour, water, sugar, wheat gluten, yeast, soybean oil, salt.", W, ("vegan", "dairy-free", "whole-grain"),
         [S("8CT", "8 buns", 3.49, 16)], "Hamburger buns made with 100% whole wheat.", BREADBOX),
        (FREESTONE, "Gluten-Free Hamburger Buns", "buns", N("1 bun (80 g)", 200, 6, 1, 370, 33, 3, 4, 4, 3),
         "water, tapioca starch, brown rice flour, egg whites, canola oil, sugar, yeast, psyllium husk, xanthan gum, salt.", ("egg",), ("gluten-free", "dairy-free"),
         [S("4CT", "4 buns", 6.49, 11)], "Gluten-free hamburger buns. Contains egg. Sold frozen.", FROZEN),
        (LEANLOAF, "Keto Hamburger Buns", "buns", N("1 bun (57 g)", 90, 3, 0.5, 260, 15, 11, 1, 0, 9),
         "water, wheat protein isolate, oat fiber, resistant wheat starch, sesame seeds, yeast, avocado oil, salt.", ("wheat", "sesame"), ("vegan", "dairy-free"),
         [S("4CT", "4 buns", 5.99, 8)], "Low-carb sesame hamburger buns with 4 g net carbs each. Contains wheat; not gluten free.", BREADBOX),
        (HEARTH, "White Pita Bread", "pita", N("1 pita (57 g)", 150, 1, 0, 300, 32, 1, 1, 0, 5),
         f"{ENRICHED}, water, yeast, salt, sugar.", W, ("vegan", "dairy-free"), [S("6CT", "6 pitas", 2.49, 12)],
         "Soft pocket pita bread.", BREADBOX),
        (HEARTH, "Whole Wheat Pita Bread", "pita", N("1 pita (57 g)", 150, 1.5, 0, 290, 30, 5, 1, 0, 6),
         "whole wheat flour, water, yeast, salt, sugar.", W, ("vegan", "dairy-free", "whole-grain"), [S("6CT", "6 pitas", 2.79, 12)],
         "Whole wheat pocket pita with 5 g fiber each.", BREADBOX),
        (HEARTH, "Original Naan", "naan", N("1 piece (90 g)", 250, 5, 1.5, 470, 43, 1, 4, 3, 8),
         f"{ENRICHED}, water, yogurt (cultured milk), sugar, soybean oil, eggs, yeast, salt, baking powder.", ("wheat", "milk", "egg"), (),
         [S("2PK", "2 pieces", 3.49, 6.3)], "Soft, pillowy tandoor-style naan flatbread made with yogurt.", BREADBOX),
        (HEARTH, "Garlic Naan", "naan", N("1 piece (90 g)", 260, 6, 1.5, 480, 42, 1, 4, 3, 8),
         f"{ENRICHED}, water, yogurt (cultured milk), sugar, soybean oil, eggs, garlic, cilantro, yeast, salt, baking powder.", ("wheat", "milk", "egg"), (),
         [S("2PK", "2 pieces", 3.49, 6.3)], "Naan flatbread brushed with garlic and cilantro.", BREADBOX),
    ]  # fmt: skip
    return [
        _bake(brand, title, ptype, n, sizes, ing, allergens, intro, tags=tags, storage=storage)
        for brand, title, ptype, n, ing, allergens, tags, sizes, intro, storage in rows
    ]  # fmt: skip


def sweets() -> list[ProductSeed]:
    WEM = ("wheat", "egg", "milk")
    rows = [  # brand, title, type, facts, ingredients, allergens, tags, sizes, intro, storage
        (HEARTH, "Blueberry Muffins", "muffins", N("1 muffin (113 g)", 420, 20, 3.5, 380, 54, 1, 31, 29, 6),
         f"{ENRICHED}, sugar, blueberries, soybean oil, eggs, water, buttermilk, baking powder, salt, natural flavor.", (*WEM, "soy"), (),
         [S("4CT", "4 muffins", 5.49, 16)], "Jumbo bakery muffins bursting with blueberries.", BREADBOX),
        (HEARTH, "Double Chocolate Chip Muffins", "muffins", N("1 muffin (113 g)", 460, 22, 6, 390, 60, 2, 36, 34, 6),
         f"{ENRICHED}, sugar, chocolate chips (sugar, chocolate, cocoa butter, soy lecithin), soybean oil, eggs, cocoa, buttermilk, baking soda, salt.",
         (*WEM, "soy"), (), [S("4CT", "4 muffins", 5.49, 16)], "Rich chocolate muffins loaded with chocolate chips.", BREADBOX),
        (HEARTH, "Banana Nut Muffins", "muffins", N("1 muffin (113 g)", 430, 21, 3, 360, 55, 2, 30, 26, 6),
         f"{ENRICHED}, bananas, sugar, soybean oil, walnuts, eggs, buttermilk, baking soda, salt.", (*WEM, "tree nuts", "soy"), (),
         [S("4CT", "4 muffins", 5.49, 16)], "Moist banana muffins with walnuts. Contains tree nuts.", BREADBOX),
        (HEARTH, "Sugar Free Blueberry Muffins", "muffins", N("1 muffin (71 g)", 200, 11, 2, 280, 26, 2, 0, 0, 4),
         f"{ENRICHED}, maltitol, blueberries, canola oil, eggs, water, nonfat milk, baking powder, salt, sucralose.", WEM, (),
         [S("4CT", "4 muffins", 5.99, 10)], "Blueberry muffins sweetened with maltitol and sucralose instead of sugar. Maltitol is a sugar alcohol that can affect blood sugar.", BREADBOX),
        (HEARTH, "All-Butter Croissants", "croissants", N("1 croissant (57 g)", 230, 12, 7, 260, 26, 1, 5, 4, 5),
         f"{ENRICHED}, butter (cream), water, sugar, eggs, yeast, milk, salt.", WEM, (), [S("4CT", "4 croissants", 4.99, 8)],
         "Flaky, layered croissants made with all butter.", BREADBOX),
        (STORE_BRAND, "Mini Butter Croissants", "croissants", N("2 croissants (56 g)", 220, 11, 7, 250, 26, 1, 5, 4, 5),
         f"{ENRICHED}, butter (cream), water, sugar, eggs, yeast, milk, salt.", WEM, (), [S("12CT", "12 mini croissants", 4.99, 12)],
         "Bite-size butter croissants.", BREADBOX),
        (HEARTH, "Chocolate Fudge Layer Cake", "cake", N("1/8 cake (100 g)", 390, 18, 6, 330, 55, 2, 40, 38, 4),
         f"sugar, {ENRICHED}, soybean oil, eggs, cocoa, butter, buttermilk, corn syrup, baking soda, salt, soy lecithin.", (*WEM, "soy"), (),
         [S("EA", "7 in two-layer cake", 14.99, 28)], "Two layers of chocolate cake with fudge frosting.", REFRIGERATED),
        (HEARTH, "Carrot Cake with Cream Cheese Frosting", "cake", N("1/8 cake (110 g)", 430, 23, 5, 340, 53, 1, 38, 34, 4),
         f"sugar, carrots, {ENRICHED}, soybean oil, cream cheese (milk), eggs, walnuts, butter, cinnamon, baking soda, salt.", (*WEM, "tree nuts"), (),
         [S("EA", "7 in cake", 15.99, 31)], "Spiced carrot cake with walnuts and cream cheese frosting. Contains tree nuts.", REFRIGERATED),
        (STORE_BRAND, "Yellow Sheet Cake with Chocolate Frosting", "cake", N("1/24 cake (85 g)", 340, 15, 4, 260, 49, 0, 36, 35, 3),
         f"sugar, {ENRICHED}, palm oil, water, eggs, corn syrup, cocoa, nonfat milk, soy lecithin, baking powder, salt.", (*WEM, "soy"), (),
         [S("QS", "1/4 sheet cake (serves 24)", 19.99, 72)], "Classic birthday sheet cake with chocolate frosting.", REFRIGERATED),
        (HEARTH, "Angel Food Cake", "cake", N("1/8 cake (50 g)", 130, 0, 0, 300, 29, 0, 20, 20, 3),
         f"sugar, egg whites, {ENRICHED}, cornstarch, cream of tartar, salt, natural flavor.", ("egg", "wheat"), ("dairy-free",),
         [S("EA", "1 cake (14 oz)", 5.49, 14)], "Light, airy angel food cake made with egg whites. Fat free, but not low in sugar.", BREADBOX),
        (HEARTH, "No Sugar Added New York Cheesecake", "cake", N("1/8 cake (100 g)", 300, 24, 13, 280, 20, 0, 3, 0, 6),
         "cream cheese (milk), eggs, maltitol, heavy cream, graham crust (wheat flour, butter, maltitol), sucralose, vanilla.", WEM, (),
         [S("EA", "7 in cheesecake", 14.99, 28)], "Creamy New York cheesecake sweetened with maltitol and sucralose, with no sugar added.", REFRIGERATED),
        (HEARTH, "Texas Pecan Pie", "pie", N("1/8 pie (113 g)", 480, 23, 5, 300, 65, 2, 40, 38, 5),
         f"corn syrup, pecans, sugar, eggs, {ENRICHED}, butter, palm oil, vanilla, salt.", (*WEM, "tree nuts"), (),
         [S("EA", "9 in pie", 12.99, 32)], "Classic pecan pie made with Texas pecans. Contains tree nuts.", BREADBOX),
        (HEARTH, "No Sugar Added Apple Pie", "pie", N("1/8 pie (117 g)", 250, 12, 5, 300, 33, 2, 7, 0, 2),
         f"apples, {ENRICHED}, palm oil, water, modified corn starch, cinnamon, salt, sucralose.", ("wheat",), ("dairy-free",),
         [S("EA", "9 in pie", 10.99, 33)], "Apple pie sweetened with sucralose; the only sugar is naturally occurring from the apples.", BREADBOX),
        (HEARTH, "Fresh-Baked Chocolate Chip Cookies", "cookies", N("1 cookie (40 g)", 190, 9, 5, 125, 26, 1, 15, 14, 2),
         f"{ENRICHED}, chocolate chips (sugar, chocolate, cocoa butter, milk fat, soy lecithin), brown sugar, butter, sugar, eggs, baking soda, salt.",
         (*WEM, "soy"), (), [S("12CT", "12 cookies", 5.99, 17)], "Soft, chewy chocolate chip cookies baked in store.", BREADBOX),
        (HEARTH, "Sugar Free Oatmeal Cookies", "cookies", N("1 cookie (30 g)", 120, 6, 2.5, 95, 17, 1, 0, 0, 2),
         f"oats, {ENRICHED}, maltitol, butter, eggs, cinnamon, baking soda, salt, sucralose.", WEM, (), [S("12CT", "12 cookies", 5.99, 13)],
         "Oatmeal cookies sweetened with maltitol and sucralose, with no sugar.", BREADBOX),
        (STORE_BRAND, "Frosted Sugar Cookies", "cookies", N("1 cookie (38 g)", 170, 7, 3, 90, 25, 0, 15, 15, 1),
         f"sugar, {ENRICHED}, palm oil, eggs, water, corn syrup, nonfat milk, soy lecithin, baking powder, artificial colors.", (*WEM, "soy"), (),
         [S("10CT", "10 cookies", 4.49, 13.5)], "Soft sugar cookies with pastel frosting and sprinkles.", BREADBOX),
        (STORE_BRAND, "Glazed Donuts", "donuts", N("1 donut (52 g)", 210, 11, 5, 200, 26, 1, 12, 11, 3),
         f"{ENRICHED}, water, palm oil, sugar, dextrose, soy flour, eggs, nonfat milk, yeast, salt.", (*WEM, "soy"), (),
         [S("6CT", "6 donuts", 4.49, 11)], "Light, yeast-raised glazed donuts.", BREADBOX),
        (STORE_BRAND, "Cinnamon Rolls with Icing", "pastries", N("1 roll (99 g)", 370, 14, 6, 380, 56, 1, 24, 22, 6),
         f"{ENRICHED}, sugar, water, butter, brown sugar, eggs, cinnamon, nonfat milk, yeast, salt.", WEM, (),
         [S("4CT", "4 rolls", 5.99, 14)], "Big, soft cinnamon rolls topped with vanilla icing.", BREADBOX),
    ]  # fmt: skip
    return [
        _bake(brand, title, ptype, n, sizes, ing, allergens, intro, tags=tags, claims=SWEET_CLAIMS, storage=storage)
        for brand, title, ptype, n, ing, allergens, tags, sizes, intro, storage in rows
    ]  # fmt: skip


def products() -> list[ProductSeed]:
    return [*breads(), *bagels_muffins_tortillas(), *buns_flatbreads(), *sweets()]


__all__ = ["products"]
