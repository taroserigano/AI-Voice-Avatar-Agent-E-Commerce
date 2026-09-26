"""Snacks: chips, tortilla chips and salsa, crackers, pretzels, popcorn, nuts and trail mix,
protein and granola bars, cookies, candy and chocolate, fruit snacks, rice cakes, jerky,
and seaweed.

Contrasts shoppers ask about: classic vs lightly salted vs unsalted, baked and reduced fat,
regular vs sugar-free candy and cookies, high-protein vs low-sugar bars, and allergens
(peanuts vs tree nuts vs nut-free seeds).
"""

from __future__ import annotations

from commerce.seed.data import Nutrition, ProductSeed
from commerce.seed.gen.common import PANTRY, STORE_BRAND, Size, cents, food

CAT = "snacks"
CRISPFIELD = "Crispfield"  # mainstream chips
REDOAK = "Red Oak Kettle Co."  # kettle chips
GARDENCRISP = "Garden Crisp Snacks"  # veggie and legume chips
OAKMEADOW = "Oakmeadow Organics"
MESQUITE = "Mesquite Hill Tortilleria"  # tortilla chips, salsa, queso
HICKORY = "Hickory Lane Smokehouse"  # jerky, pork rinds
BLUESTEM = "Bluestem Ranch"  # grass-fed jerky
WHEATFIELD = "Wheatfield Bakers"  # crackers
FREESTONE = "Freestone Gluten Free"
TWISTWELL = "Twistwell"  # pretzels
POPHARBOR = "Pop Harbor"  # popcorn
OLDMILL = "Old Mill Nut Co."
LONESTAR = "Lone Star Harvest"  # Texas pecans
TRAILMARK = "Trailmark"  # trail mix and granola bars
IRONPEAK = "Ironpeak Nutrition"  # protein and keto bars
GREENSTRIDE = "Greenstride"  # vegan bars and shakes
SWEETHOLLOW = "Sweet Hollow Bakery"  # packaged cookies
COCOALANE = "Cocoa Lane Chocolatiers"
SUGARBIRD = "Sugarbird Candy"
JOLLY = "Jolly Orchard"  # fruit snacks
SEAGLASS = "Seaglass Snacks"  # seaweed

OZ1 = "1 oz (28 g)"
VG = ("vegan", "dairy-free")
VGF = ("vegan", "dairy-free", "gluten-free")
SALTY_CLAIMS = ("low-sodium", "low-fat", "fat-free", "high-fiber", "high-protein", "keto")
SWEET_CLAIMS = ("sugar-free", "no-added-sugar", "low-sugar", "high-protein", "high-fiber", "keto")


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


Row = tuple[str, str, str, Nutrition, list[Size], str, tuple[str, ...], tuple[str, ...], str]


def _rows(rows: list[Row], claims: tuple[str, ...]) -> list[ProductSeed]:
    """(brand, title, type, facts, sizes, ingredients, allergens, tags, intro) rows."""
    out = []
    for brand, title, ptype, n, sizes, ing, allergens, tags, intro in rows:
        organic = title.startswith("Organic")
        out.append(food(
            category=CAT, product_type=ptype, brand=brand, title=title, sizes=sizes, nutrition=n,
            ingredients=ing, allergens=allergens, tags=[*(["organic"] if organic else []), *tags],
            claims=claims, intro=intro, storage=PANTRY,
        ))  # fmt: skip
    return out


def chips() -> list[ProductSeed]:
    bag = [S("8OZ", "8 oz bag", 4.29, 8), S("13OZ", "13 oz party size", 5.99, 13)]
    kbag = [S("8OZ", "8 oz bag", 4.49, 8)]
    sbag = [S("10OZ", "10 oz bag", 2.99, 10)]
    potato = "Potatoes, vegetable oil (sunflower, corn, canola)"
    classic = N(OZ1, 160, 10, 1.5, 170, 15, 1, 0, 0, 2)
    kettle = N(OZ1, 150, 9, 1, 110, 16, 1, 0, 0, 2)
    rows: list[Row] = [
        (CRISPFIELD, "Classic Potato Chips", "chips", classic, bag, f"{potato}, salt.", (), VGF, "Thin, crispy classic salted potato chips."),
        (CRISPFIELD, "Lightly Salted Potato Chips", "chips", N(OZ1, 160, 10, 1.5, 75, 15, 1, 0, 0, 2), bag, f"{potato}, salt.", (), VGF,
         "Classic potato chips with about half the salt: 75 mg sodium per ounce."),
        (CRISPFIELD, "Unsalted Potato Chips", "chips", N(OZ1, 160, 10, 1.5, 0, 15, 1, 0, 0, 2), bag, f"{potato}.", (), (*VGF, "no-salt-added"),
         "Classic potato chips with no salt at all."),
        (CRISPFIELD, "Reduced Fat Potato Chips", "chips", N(OZ1, 140, 6, 0.5, 150, 18, 1, 0, 0, 2), bag, f"{potato}, salt.", (), (*VGF, "reduced-fat"),
         "Potato chips with 40% less fat than our classic chips."),
        (CRISPFIELD, "Baked Potato Crisps, Original", "chips", N(OZ1, 120, 3, 0.5, 190, 22, 2, 2, 1, 2), [S("7OZ", "7 oz bag", 4.29, 7)],
         "Dried potatoes, corn starch, sugar, corn oil, soy lecithin, salt, dextrose.", ("soy",), ("gluten-free", "dairy-free"),
         "Oven-baked potato crisps with 3 g fat per ounce, 65% less fat than fried chips."),
        (CRISPFIELD, "Sour Cream & Onion Potato Chips", "chips", N(OZ1, 160, 10, 1.5, 190, 15, 1, 1, 0, 2), bag,
         f"{potato}, sour cream and onion seasoning (whey, onion powder, sour cream (milk), salt, buttermilk, parsley, natural flavors).", ("milk",), ("gluten-free",),
         "Potato chips with tangy sour cream and onion seasoning. Contains milk."),
        (CRISPFIELD, "Barbecue Potato Chips", "chips", N(OZ1, 150, 9, 1.5, 210, 16, 1, 2, 2, 2), bag,
         f"{potato}, barbecue seasoning (sugar, salt, paprika, onion powder, garlic powder, tomato powder, natural smoke flavor).", (), VGF,
         "Sweet and smoky barbecue potato chips."),
        (CRISPFIELD, "Salt & Vinegar Potato Chips", "chips", N(OZ1, 160, 10, 1.5, 300, 15, 1, 0, 0, 2), bag,
         f"{potato}, salt and vinegar seasoning (maltodextrin, sodium diacetate, salt, malic acid).", (), VGF, "Tart salt and vinegar potato chips."),
        (CRISPFIELD, "Cheddar & Sour Cream Ridged Chips", "chips", N(OZ1, 160, 10, 1.5, 210, 15, 1, 1, 1, 2), bag,
         f"{potato}, seasoning (cheddar cheese (milk), whey, sour cream, salt, sugar, onion powder).", ("milk",), ("gluten-free",), "Ridged chips with cheddar and sour cream seasoning."),
        (REDOAK, "Sea Salt Kettle Cooked Potato Chips", "chips", kettle, kbag, "Potatoes, sunflower oil, sea salt.", (), VGF,
         "Thick, crunchy kettle cooked chips made in small batches, lightly seasoned with sea salt."),
        (REDOAK, "Unsalted Kettle Cooked Potato Chips", "chips", N(OZ1, 150, 9, 1, 5, 16, 1, 0, 0, 2), kbag, "Potatoes, sunflower oil.", (), (*VGF, "no-salt-added"),
         "Kettle cooked chips with no salt added."),
        (REDOAK, "Reduced Fat Sea Salt Kettle Chips", "chips", N(OZ1, 130, 6, 0.5, 110, 18, 1, 0, 0, 2), kbag, "Potatoes, sunflower oil, sea salt.", (), (*VGF, "reduced-fat"),
         "Kettle cooked chips with 40% less fat than our original."),
        (REDOAK, "Jalapeno Kettle Cooked Chips", "chips", N(OZ1, 150, 9, 1, 200, 16, 1, 1, 0, 2), kbag,
         "Potatoes, sunflower oil, jalapeno seasoning (salt, maltodextrin, jalapeno pepper, onion, garlic, vinegar powder).", (), VGF, "Spicy jalapeno kettle chips."),
        (REDOAK, "Sea Salt & Vinegar Kettle Chips", "chips", N(OZ1, 150, 9, 1, 280, 16, 1, 0, 0, 2), kbag,
         "Potatoes, sunflower oil, sea salt, vinegar powder, malic acid.", (), VGF, "Kettle chips with bold sea salt and vinegar."),
        (REDOAK, "Honey Barbecue Kettle Chips", "chips", N(OZ1, 150, 8, 1, 180, 17, 1, 3, 3, 2), kbag,
         "Potatoes, sunflower oil, honey barbecue seasoning (sugar, honey, salt, paprika, tomato powder, spices).", (), ("gluten-free", "dairy-free"), "Sweet honey barbecue kettle chips."),
        (REDOAK, "Avocado Oil Sea Salt Kettle Chips", "chips", kettle, kbag, "Potatoes, avocado oil, sea salt.", (), VGF, "Kettle chips cooked in 100% avocado oil."),
        (OAKMEADOW, "Organic Sea Salt Potato Chips", "chips", N(OZ1, 150, 9, 1, 120, 16, 1, 0, 0, 2), [S("5OZ", "5 oz bag", 3.99, 5)],
         "Organic potatoes, organic sunflower oil, sea salt.", (), (*VGF, "non-gmo"), "Organic kettle potato chips."),
        (GARDENCRISP, "Sea Salt Veggie Sticks", "chips", N(OZ1, 130, 7, 0.5, 250, 17, 0, 1, 0, 1), [S("7OZ", "7 oz bag", 3.99, 7)],
         "Potato starch, potato flour, canola oil, spinach powder, tomato paste, salt, beetroot powder, turmeric.", (), VGF,
         "Crunchy veggie sticks. Made mostly from potato, with vegetable powders for color."),
        (GARDENCRISP, "Beet & Sweet Potato Chips", "chips", N(OZ1, 150, 9, 1, 95, 16, 3, 4, 0, 1), [S("5OZ", "5 oz bag", 4.49, 5)],
         "Sweet potatoes, beets, parsnips, sunflower oil, sea salt.", (), VGF, "Sliced root vegetable chips with a pinch of sea salt."),
        (GARDENCRISP, "Sea Salt Lentil Chips", "chips", N(OZ1, 130, 5, 0.5, 200, 19, 3, 1, 0, 4), [S("4OZ", "4 oz bag", 3.99, 4)],
         "Lentil flour, rice flour, sunflower oil, potato starch, sea salt.", (), VGF, "Light, crispy lentil chips with 4 g protein."),
        (GARDENCRISP, "Lightly Salted Plantain Chips", "chips", N(OZ1, 150, 9, 4, 65, 16, 1, 1, 0, 1), [S("5OZ", "5 oz bag", 2.99, 5)],
         "Plantains, palm oil, sea salt.", (), VGF, "Crunchy green plantain chips, lightly salted."),
        (GARDENCRISP, "Sea Salt Kale Chips", "chips", N(OZ1, 140, 9, 1, 250, 10, 3, 1, 0, 4), [S("2OZ", "2 oz bag", 5.99, 2)],
         "Kale, cashews, sunflower seeds, nutritional yeast, lemon juice, sea salt.", ("tree nuts",), VGF, "Dehydrated kale chips with a cashew coating. Contains tree nuts."),
        (STORE_BRAND, "Classic Potato Chips", "chips", classic, sbag, f"{potato}, salt.", (), VGF, "Classic salted potato chips."),
        (STORE_BRAND, "Wavy Potato Chips", "chips", classic, sbag, f"{potato}, salt.", (), VGF, "Thick-cut wavy potato chips for dipping."),
        (STORE_BRAND, "Kettle Cooked Sea Salt Chips", "chips", kettle, [S("8OZ", "8 oz bag", 2.99, 8)], "Potatoes, sunflower oil, sea salt.", (), VGF, "Crunchy kettle cooked chips."),
        (STORE_BRAND, "Sour Cream & Onion Chips", "chips", N(OZ1, 160, 10, 1.5, 190, 15, 1, 1, 0, 2), sbag,
         f"{potato}, seasoning (whey, onion powder, sour cream (milk), salt, buttermilk, parsley).", ("milk",), ("gluten-free",), "Sour cream and onion potato chips."),
        (STORE_BRAND, "Baked Potato Crisps", "chips", N(OZ1, 120, 3, 0.5, 190, 22, 2, 2, 1, 2), [S("7OZ", "7 oz bag", 2.99, 7)],
         "Dried potatoes, corn starch, sugar, corn oil, soy lecithin, salt, dextrose.", ("soy",), ("gluten-free", "dairy-free"), "Baked potato crisps with 3 g fat."),
        (CRISPFIELD, "Cheese Curls", "cheese-puffs", N(OZ1, 160, 10, 1.5, 270, 15, 0, 1, 0, 2), [S("8OZ", "8 oz bag", 4.29, 8)],
         "Corn meal, vegetable oil, cheese seasoning (whey, cheddar cheese (milk), salt, buttermilk, yellow 6).", ("milk",), ("gluten-free",), "Crunchy cheddar cheese curls."),
        (CRISPFIELD, "Baked Cheese Puffs", "cheese-puffs", N(OZ1, 130, 5, 1, 250, 19, 0, 1, 0, 2), [S("8OZ", "8 oz bag", 4.29, 8)],
         "Corn meal, sunflower oil, cheese seasoning (whey, cheddar cheese (milk), salt, buttermilk).", ("milk",), ("gluten-free",), "Baked, airy cheese puffs with 50% less fat than fried."),
        (CRISPFIELD, "Original Corn Chips", "corn-chips", N(OZ1, 160, 10, 1.5, 170, 16, 1, 0, 0, 2), [S("10OZ", "10 oz bag", 4.29, 10)],
         "Corn, corn oil, salt.", (), VGF, "Crunchy corn chips made from three ingredients."),
        (HICKORY, "Original Pork Rinds", "pork-rinds", N("1/2 oz (14 g)", 80, 5, 2, 270, 0, 0, 0, 0, 9), [S("3OZ", "3 oz bag", 2.99, 3)],
         "Pork skins, salt.", (), ("gluten-free", "dairy-free"), "Light, crunchy fried pork rinds with 0 g carbs. Keto friendly."),
        (HICKORY, "Chili Lime Pork Rinds", "pork-rinds", N("1/2 oz (14 g)", 80, 5, 2, 290, 0, 0, 0, 0, 8), [S("3OZ", "3 oz bag", 2.99, 3)],
         "Pork skins, salt, chili powder, lime juice powder, citric acid.", (), ("gluten-free", "dairy-free"), "Pork rinds with chili lime seasoning."),
    ]  # fmt: skip
    out = _rows(rows, SALTY_CLAIMS)
    tchip = N("1 oz (28 g), about 7 chips", 140, 7, 1, 110, 19, 1, 0, 0, 2)
    tbag = [S("13OZ", "13 oz bag", 3.99, 13)]
    rows = [
        (MESQUITE, "Restaurant Style White Corn Tortilla Chips", "tortilla-chips", tchip, tbag, "White corn, vegetable oil, salt, lime.", (), VGF,
         "Thin, crispy restaurant-style tortilla chips made from stone-ground white corn."),
        (MESQUITE, "Lightly Salted Tortilla Chips", "tortilla-chips", N(OZ1, 140, 7, 1, 55, 19, 1, 0, 0, 2), tbag, "White corn, vegetable oil, salt, lime.", (), VGF,
         "Tortilla chips with half the salt: 55 mg sodium per ounce."),
        (MESQUITE, "No Salt Added Yellow Corn Tortilla Chips", "tortilla-chips", N(OZ1, 140, 7, 1, 0, 19, 2, 0, 0, 2), tbag, "Yellow corn, vegetable oil, lime.", (),
         (*VGF, "no-salt-added"), "Yellow corn tortilla chips with no salt added."),
        (MESQUITE, "Tortilla Rounds", "tortilla-chips", N(OZ1, 140, 7, 1, 120, 19, 1, 0, 0, 2), tbag, "White corn, vegetable oil, salt, lime.", (), VGF,
         "Bite-size round tortilla chips for nachos."),
        (MESQUITE, "Hint of Lime Tortilla Chips", "tortilla-chips", N(OZ1, 140, 7, 1, 160, 18, 1, 0, 0, 2), tbag,
         "White corn, vegetable oil, salt, lime juice powder, citric acid.", (), VGF, "Tortilla chips with a zesty hint of lime."),
        (MESQUITE, "Organic Blue Corn Tortilla Chips", "tortilla-chips", N(OZ1, 140, 7, 0.5, 80, 18, 2, 0, 0, 2), [S("10OZ", "10 oz bag", 4.49, 10)],
         "Organic blue corn, organic sunflower oil, sea salt, lime.", (), (*VGF, "non-gmo"), "Organic blue corn tortilla chips."),
        (MESQUITE, "Multigrain Tortilla Chips", "tortilla-chips", N(OZ1, 140, 6, 0.5, 90, 19, 2, 0, 0, 3), [S("10OZ", "10 oz bag", 4.29, 10)],
         "Corn, sunflower oil, brown rice, flaxseed, quinoa, chia seeds, sea salt.", (), VGF, "Tortilla chips with brown rice, flax, quinoa, and chia."),
        (MESQUITE, "Baked Tortilla Scoops", "tortilla-chips", N(OZ1, 120, 3, 0, 130, 21, 2, 0, 0, 3), [S("10OZ", "10 oz bag", 3.99, 10)],
         "Corn, corn oil, salt.", (), VGF, "Baked scoop-shaped tortilla chips with 3 g fat per ounce."),
        (MESQUITE, "Grain-Free Cassava Tortilla Chips", "tortilla-chips", N(OZ1, 140, 7, 0.5, 80, 19, 1, 0, 0, 0), [S("5OZ", "5 oz bag", 4.99, 5)],
         "Cassava flour, avocado oil, coconut flour, sea salt, lime.", (), (*VGF, "grain-free"), "Grain-free tortilla chips made from cassava."),
        (MESQUITE, "Spicy Nacho Tortilla Chips", "tortilla-chips", N(OZ1, 140, 7, 1, 200, 18, 1, 1, 0, 2), tbag,
         "Corn, vegetable oil, nacho seasoning (cheddar cheese (milk), salt, whey, onion, tomato powder, chili pepper).", ("milk",), ("gluten-free",),
         "Tortilla chips with spicy nacho cheese seasoning."),
        (STORE_BRAND, "Restaurant Style Tortilla Chips", "tortilla-chips", tchip, [S("13OZ", "13 oz bag", 2.49, 13)], "White corn, vegetable oil, salt, lime.", (), VGF,
         "Restaurant-style white corn tortilla chips."),
        (STORE_BRAND, "Tortilla Strips", "tortilla-chips", tchip, [S("12OZ", "12 oz bag", 2.49, 12)], "White corn, vegetable oil, salt, lime.", (), VGF,
         "Thin tortilla strips for dipping and salads."),
    ]  # fmt: skip
    out += _rows(rows, SALTY_CLAIMS)
    salsa = N("2 tbsp (32 g)", 10, 0, 0, 230, 2, 0, 1, 0, 0)
    jar = [S("16OZ", "16 oz jar", 3.49, 16), S("24OZ", "24 oz jar", 4.49, 24)]
    salsa_ing = "Tomatoes, water, jalapeno peppers, onions, tomato paste, vinegar, salt, garlic, cilantro, spices"
    rows = [
        (MESQUITE, "Mild Chunky Salsa", "salsa", salsa, jar, f"{salsa_ing}.", (), VGF, "Chunky mild tomato salsa. Refrigerate after opening."),
        (MESQUITE, "Medium Chunky Salsa", "salsa", salsa, jar, f"{salsa_ing}.", (), VGF, "Chunky medium-heat tomato salsa. Refrigerate after opening."),
        (MESQUITE, "Hot Salsa Roja", "salsa", N("2 tbsp (32 g)", 10, 0, 0, 250, 2, 0, 1, 0, 0), jar, "Tomatoes, water, arbol chiles, onions, vinegar, salt, garlic, cumin.", (), VGF,
         "Smooth, fiery red salsa with arbol chiles."),
        (MESQUITE, "Salsa Verde", "salsa", N("2 tbsp (32 g)", 10, 0, 0, 200, 2, 0, 1, 0, 0), jar, "Tomatillos, water, jalapeno peppers, onions, cilantro, vinegar, salt, garlic.",
         (), VGF, "Tangy green tomatillo salsa."),
        (MESQUITE, "No Salt Added Chunky Salsa", "salsa", N("2 tbsp (32 g)", 10, 0, 0, 10, 2, 0, 1, 0, 0), [S("16OZ", "16 oz jar", 3.49, 16)],
         "Tomatoes, water, jalapeno peppers, onions, tomato paste, vinegar, garlic, cilantro, spices.", (), (*VGF, "no-salt-added"),
         "Medium chunky salsa with no salt added: 10 mg sodium per serving."),
        (MESQUITE, "Queso Blanco Dip", "queso", N("2 tbsp (33 g)", 45, 3, 1.5, 300, 4, 0, 1, 0, 1), [S("15OZ", "15 oz jar", 4.49, 15)],
         "Water, white cheddar cheese (milk), whey, canola oil, green chiles, modified corn starch, sodium phosphate, salt, jalapeno.", ("milk",), ("gluten-free",),
         "Creamy white queso dip with green chiles. Shelf-stable; refrigerate after opening."),
        (MESQUITE, "Salsa con Queso", "queso", N("2 tbsp (33 g)", 40, 2.5, 1, 290, 4, 0, 1, 0, 1), [S("15OZ", "15 oz jar", 4.49, 15)],
         "Water, cheddar cheese (milk), tomatoes, jalapeno peppers, whey, canola oil, modified corn starch, sodium phosphate, salt.", ("milk",), ("gluten-free",),
         "Cheese dip blended with chunky salsa. Refrigerate after opening."),
        (MESQUITE, "Black Bean Dip", "bean-dip", N("2 tbsp (32 g)", 35, 0, 0, 180, 6, 2, 0, 0, 2), [S("15OZ", "15 oz can", 2.99, 15)],
         "Black beans, water, jalapeno peppers, onions, salt, garlic, cumin.", (), VGF, "Smooth, spicy black bean dip."),
        (STORE_BRAND, "Medium Thick & Chunky Salsa", "salsa", salsa, [S("16OZ", "16 oz jar", 1.99, 16), S("24OZ", "24 oz jar", 2.79, 24)], f"{salsa_ing}.", (), VGF,
         "Thick and chunky medium salsa."),
    ]  # fmt: skip
    out += _rows(rows, ("low-sodium", "fat-free", "sugar-free"))
    return out


def crackers_pretzels_popcorn() -> list[ProductSeed]:
    box = [S("BOX", "Box, about 13 oz", 3.99, 13)]
    sbox = [S("BOX", "Box, about 13 oz", 2.49, 13)]
    WS = ("wheat", "soy")
    butter_ing = "Enriched wheat flour, soybean oil, sugar, salt, leavening, high fructose corn syrup, soy lecithin, natural flavor."
    saltine_ing = "Enriched wheat flour, soybean oil, salt, yeast, baking soda."
    woven_ing = "Whole grain wheat, canola oil, salt."
    cheddar_ing = "Enriched wheat flour, cheddar cheese (milk, cultures, salt, enzymes), sunflower oil, salt, paprika, yeast, soy lecithin."
    rows: list[Row] = [
        (WHEATFIELD, "Original Butter Crackers", "crackers", N("5 crackers (16 g)", 80, 4.5, 1, 135, 10, 0, 1, 1, 1), box, butter_ing, WS, VG,
         "Buttery-tasting round crackers. Made with vegetable oil; contains no milk."),
        (WHEATFIELD, "Reduced Fat Butter Crackers", "crackers", N("5 crackers (16 g)", 70, 2, 0, 160, 11, 0, 1, 1, 1), box, butter_ing, WS, (*VG, "reduced-fat"),
         "Round butter-flavored crackers with 50% less fat."),
        (WHEATFIELD, "Saltine Crackers", "crackers", N("5 crackers (15 g)", 60, 1.5, 0, 135, 11, 0, 0, 0, 1), [S("16OZ", "16 oz box", 3.49, 16)], saltine_ing, ("wheat",), VG,
         "Classic crisp saltine crackers with salted tops."),
        (WHEATFIELD, "Unsalted Tops Saltine Crackers", "crackers", N("5 crackers (15 g)", 60, 1.5, 0, 80, 11, 0, 0, 0, 1), [S("16OZ", "16 oz box", 3.49, 16)], saltine_ing,
         ("wheat",), VG, "Saltines without salt on top: 80 mg sodium per serving. The dough still contains salt."),
        (WHEATFIELD, "100% Whole Grain Woven Wheat Crackers", "crackers", N("6 crackers (28 g)", 120, 3.5, 0, 140, 20, 3, 0, 0, 3), [S("9OZ", "9 oz box", 3.99, 9)],
         woven_ing, ("wheat",), (*VG, "whole-grain"), "Crunchy woven crackers made from just whole grain wheat, oil, and salt."),
        (WHEATFIELD, "Hint of Salt Woven Wheat Crackers", "crackers", N("6 crackers (28 g)", 120, 3.5, 0, 50, 20, 3, 0, 0, 3), [S("9OZ", "9 oz box", 3.99, 9)],
         woven_ing, ("wheat",), (*VG, "whole-grain"), "Whole grain woven wheat crackers with 65% less sodium: 50 mg per serving."),
        (WHEATFIELD, "Cheddar Cheese Crackers", "crackers", N("27 crackers (30 g)", 150, 8, 2, 230, 17, 1, 0, 0, 3), [S("12OZ", "12 oz box", 4.29, 12)],
         cheddar_ing, ("wheat", "milk", "soy"), (), "Bite-size crackers baked with real cheddar cheese."),
        (WHEATFIELD, "Reduced Fat Cheddar Cheese Crackers", "crackers", N("29 crackers (30 g)", 130, 4.5, 1, 250, 19, 1, 0, 0, 3), [S("12OZ", "11.5 oz box", 4.29, 11.5)],
         cheddar_ing, ("wheat", "milk", "soy"), ("reduced-fat",), "Cheddar cheese crackers with 40% less fat."),
        (WHEATFIELD, "Honey Graham Crackers", "crackers", N("2 full sheets (31 g)", 130, 3, 0, 150, 24, 1, 8, 8, 2), [S("14OZ", "14.4 oz box", 3.99, 14.4)],
         "Unbleached enriched wheat flour, whole grain wheat flour, sugar, canola oil, honey, leavening, salt, soy lecithin.", WS, ("dairy-free",),
         "Honey graham crackers for s'mores and snacking."),
        (WHEATFIELD, "Rosemary Water Crackers", "crackers", N("4 crackers (14 g)", 60, 1, 0, 95, 11, 0, 0, 0, 1), [S("4OZ", "4.4 oz box", 3.29, 4.4)],
         "Wheat flour, canola oil, rosemary, salt, yeast.", ("wheat",), VG, "Thin, crisp water crackers with rosemary, for cheese boards."),
        (FREESTONE, "Gluten-Free Sea Salt Rice Crackers", "crackers", N("18 crackers (30 g)", 130, 3, 0, 150, 23, 0, 0, 0, 2), [S("4OZ", "3.5 oz box", 3.49, 3.5)],
         "Brown rice, white rice, sunflower oil, sea salt.", (), VGF, "Light, crunchy rice crackers, gluten free."),
        (FREESTONE, "Gluten-Free Seed Crackers, Original", "crackers", N("16 crackers (30 g)", 150, 7, 0.5, 190, 19, 3, 0, 0, 3), [S("4OZ", "4.25 oz box", 4.49, 4.25)],
         "Brown rice flour, sesame seeds, flaxseed, quinoa, tapioca starch, sunflower oil, sea salt.", ("sesame",), VGF, "Crunchy gluten-free crackers packed with seeds."),
        (FREESTONE, "Gluten-Free Almond Flour Crackers, Sea Salt", "crackers", N("17 crackers (30 g)", 150, 7, 0.5, 240, 19, 2, 1, 0, 3), [S("4OZ", "4.25 oz box", 4.99, 4.25)],
         "Almond flour, cassava flour, flaxseed, sunflower oil, sea salt, onion, garlic.", ("tree nuts",), (*VGF, "grain-free"),
         "Grain-free crackers made with almond and cassava flour. Contains tree nuts."),
        (FREESTONE, "Gluten-Free Cheddar Crackers", "crackers", N("30 crackers (30 g)", 140, 6, 1.5, 230, 20, 1, 1, 0, 2), [S("5OZ", "5 oz box", 4.49, 5)],
         "Rice flour, cheddar cheese (milk), tapioca starch, sunflower oil, salt, paprika.", ("milk",), ("gluten-free",), "Gluten-free cheddar crackers."),
        (STORE_BRAND, "Saltine Crackers", "crackers", N("5 crackers (15 g)", 60, 1.5, 0, 135, 11, 0, 0, 0, 1), [S("16OZ", "16 oz box", 1.99, 16)], saltine_ing, ("wheat",), VG,
         "Classic saltine crackers."),
        (STORE_BRAND, "Butter Crackers", "crackers", N("5 crackers (16 g)", 80, 4.5, 1, 135, 10, 0, 1, 1, 1), sbox, butter_ing, WS, VG, "Round butter-flavored crackers."),
        (STORE_BRAND, "Woven Wheat Crackers", "crackers", N("6 crackers (28 g)", 120, 3.5, 0, 140, 20, 3, 0, 0, 3), [S("9OZ", "9 oz box", 2.49, 9)], woven_ing, ("wheat",),
         (*VG, "whole-grain"), "Whole grain woven wheat crackers."),
        (STORE_BRAND, "Cheddar Cheese Crackers", "crackers", N("27 crackers (30 g)", 150, 8, 2, 230, 17, 1, 0, 0, 3), [S("12OZ", "12 oz box", 2.99, 12)], cheddar_ing,
         ("wheat", "milk", "soy"), (), "Bite-size cheddar cheese crackers."),
    ]  # fmt: skip
    out = _rows(rows, SALTY_CLAIMS)
    pretzel = N(OZ1, 110, 1, 0, 450, 23, 1, 1, 1, 3)
    pbag = [S("16OZ", "16 oz bag", 3.49, 16)]
    rows = [
        (TWISTWELL, "Classic Mini Twist Pretzels", "pretzels", pretzel, pbag, "Enriched wheat flour, salt, corn syrup, canola oil, yeast, baking soda.", ("wheat",), VG,
         "Crunchy mini twist pretzels, low fat and salted."),
        (TWISTWELL, "Unsalted Mini Pretzels", "pretzels", N(OZ1, 110, 1, 0, 90, 23, 1, 1, 1, 3), pbag, "Enriched wheat flour, corn syrup, canola oil, yeast, baking soda.",
         ("wheat",), (*VG, "no-salt-added"), "Mini pretzels with no salt on top or in the dough; 90 mg sodium comes from baking soda."),
        (TWISTWELL, "Pretzel Rods", "pretzels", N(OZ1, 110, 1, 0, 400, 23, 1, 1, 1, 3), [S("12OZ", "12 oz bag", 3.49, 12)],
         "Enriched wheat flour, salt, corn syrup, canola oil, yeast, baking soda.", ("wheat",), VG, "Long, crunchy pretzel rods."),
        (TWISTWELL, "Sourdough Hard Pretzels", "pretzels", N(OZ1, 110, 0.5, 0, 380, 23, 1, 0, 0, 3), [S("16OZ", "16 oz bag", 3.99, 16)],
         "Enriched wheat flour, water, sourdough culture, salt, yeast, baking soda.", ("wheat",), VG, "Big, extra-crunchy sourdough pretzels."),
        (TWISTWELL, "Gluten-Free Pretzel Twists", "pretzels", N(OZ1, 120, 3, 0, 290, 24, 1, 1, 1, 1), [S("8OZ", "8 oz bag", 4.49, 8)],
         "Corn starch, potato starch, tapioca starch, palm oil, sugar, salt, xanthan gum, baking soda.", (), VGF, "Gluten-free pretzel twists made without wheat."),
        (TWISTWELL, "Peanut Butter Filled Pretzels", "pretzels", N(OZ1, 130, 6, 1, 210, 15, 1, 3, 2, 4), [S("24OZ", "24 oz bag", 6.99, 24)],
         "Enriched wheat flour, peanut butter (peanuts, dextrose, salt), palm oil, salt, soy lecithin.", ("wheat", "peanuts", "soy"), VG, "Pretzel nuggets filled with peanut butter."),
        (STORE_BRAND, "Mini Pretzels", "pretzels", pretzel, [S("16OZ", "16 oz bag", 2.29, 16)], "Enriched wheat flour, salt, corn syrup, canola oil, yeast, baking soda.",
         ("wheat",), VG, "Crunchy mini twist pretzels."),
    ]  # fmt: skip
    out += _rows(rows, SALTY_CLAIMS)
    mw = "2 tbsp unpopped (about 4 cups popped)"
    mbox = [S("3PK", "3 bags", 3.49, 9.9), S("6PK", "6 bags", 5.99, 19.7)]
    WG = ("whole-grain", "gluten-free")
    rows = [
        (POPHARBOR, "Butter Microwave Popcorn", "popcorn", N(mw, 170, 11, 5, 290, 17, 3, 0, 0, 2), mbox,
         "Whole grain popcorn, palm oil, salt, natural butter flavor (milk), color.", ("milk",), WG, "Classic butter microwave popcorn."),
        (POPHARBOR, "Light Butter Microwave Popcorn", "popcorn", N("5 cups popped (29 g)", 120, 4.5, 2, 230, 19, 4, 0, 0, 2), mbox,
         "Whole grain popcorn, palm oil, salt, natural butter flavor (milk).", ("milk",), (*WG, "reduced-fat"), "Light butter microwave popcorn with 60% less fat."),
        (POPHARBOR, "Movie Theater Butter Microwave Popcorn", "popcorn", N(mw, 180, 12, 6, 320, 17, 3, 0, 0, 2), mbox,
         "Whole grain popcorn, palm oil, salt, natural and artificial butter flavor (milk), color.", ("milk",), WG, "Extra-buttery movie theater-style popcorn."),
        (POPHARBOR, "Kettle Corn Microwave Popcorn", "popcorn", N(mw, 160, 9, 4, 190, 19, 3, 4, 4, 2), mbox,
         "Whole grain popcorn, palm oil, sugar, salt, sucralose.", (), (*WG, *VG), "Sweet and salty kettle corn."),
        (POPHARBOR, "94% Fat Free Microwave Popcorn", "popcorn", N("6 1/2 cups popped (33 g)", 110, 2, 0, 220, 24, 5, 0, 0, 3), mbox,
         "Whole grain popcorn, salt, palm oil, natural flavor.", (), (*WG, *VG), "Lightly salted microwave popcorn that is 94% fat free, with 5 g fiber."),
        (POPHARBOR, "Sea Salt Popcorn", "popcorn", N("3 1/2 cups (28 g)", 140, 8, 1, 150, 15, 3, 0, 0, 2), [S("6OZ", "6 oz bag", 3.99, 6)],
         "Popcorn, sunflower oil, sea salt.", (), (*WG, *VG), "Ready-to-eat popcorn with sunflower oil and sea salt."),
        (POPHARBOR, "White Cheddar Popcorn", "popcorn", N("2 1/2 cups (28 g)", 160, 10, 2, 280, 14, 2, 1, 0, 3), [S("6OZ", "6 oz bag", 3.99, 6)],
         "Popcorn, sunflower oil, white cheddar cheese (milk), whey, salt, buttermilk.", ("milk",), WG, "Ready-to-eat popcorn with white cheddar."),
        (POPHARBOR, "Sweet & Salty Kettle Corn", "popcorn", N("2 1/2 cups (28 g)", 130, 6, 0.5, 120, 19, 2, 7, 7, 1), [S("7OZ", "7 oz bag", 3.99, 7)],
         "Popcorn, cane sugar, sunflower oil, sea salt.", (), (*WG, *VG), "Ready-to-eat kettle corn with cane sugar."),
        (POPHARBOR, "Lightly Salted Air-Popped Popcorn", "popcorn", N("4 cups (28 g)", 120, 4, 0.5, 55, 19, 4, 0, 0, 3), [S("5OZ", "5 oz bag", 3.99, 5)],
         "Popcorn, sunflower oil, sea salt.", (), (*WG, *VG), "Air-popped popcorn with a light touch of oil and salt."),
        (STORE_BRAND, "Yellow Popcorn Kernels", "popcorn", N("2 tbsp unpopped (33 g)", 130, 1.5, 0, 0, 26, 5, 0, 0, 4), [S("32OZ", "32 oz jar", 3.49, 32)],
         "Whole grain popcorn.", (), (*WG, *VG, "no-salt-added"), "Plain whole grain popcorn kernels for stovetop or air popping."),
    ]  # fmt: skip
    out += _rows(rows, SALTY_CLAIMS)
    return out


def nuts() -> list[ProductSeed]:
    can = [S("16OZ", "16 oz canister", 4.99, 16)]
    bag = [S("8OZ", "8 oz bag", 5.99, 8), S("16OZ", "16 oz bag", 10.99, 16)]
    PN = ("peanuts",)
    TN = ("tree nuts",)
    rows: list[Row] = [
        (OLDMILL, "Dry Roasted Peanuts, Lightly Salted", "nuts", N(OZ1, 170, 14, 2, 95, 5, 2, 1, 0, 7), can, "Peanuts, sea salt.", PN, VGF,
         "Dry roasted peanuts with half the salt of our regular."),
        (OLDMILL, "Dry Roasted Peanuts, Unsalted", "nuts", N(OZ1, 170, 14, 2, 0, 6, 2, 1, 0, 7), can, "Peanuts.", PN, (*VGF, "no-salt-added", "unsweetened"),
         "Dry roasted peanuts with no salt added."),
        (OLDMILL, "Honey Roasted Peanuts", "nuts", N(OZ1, 160, 12, 2, 95, 8, 2, 5, 4, 6), can, "Peanuts, sugar, honey, salt, corn starch, peanut oil.", PN,
         ("gluten-free", "dairy-free"), "Sweet honey roasted peanuts."),
        (OLDMILL, "Roasted & Salted Cashews", "nuts", N(OZ1, 160, 13, 2.5, 160, 9, 1, 1, 0, 5), bag, "Cashews, peanut oil, salt.", ("tree nuts", "peanuts"), VGF,
         "Whole cashews roasted in peanut oil and salted."),
        (OLDMILL, "Unsalted Roasted Cashews", "nuts", N(OZ1, 160, 13, 2.5, 0, 9, 1, 1, 0, 5), bag, "Cashews.", TN, (*VGF, "no-salt-added", "unsweetened"),
         "Dry roasted whole cashews with no salt."),
        (OLDMILL, "Whole Natural Almonds", "nuts", N(OZ1, 160, 14, 1, 0, 6, 4, 1, 0, 6), bag, "Almonds.", TN, (*VGF, "no-salt-added", "unsweetened"),
         "Raw whole almonds, nothing added."),
        (OLDMILL, "Roasted Salted Almonds", "nuts", N(OZ1, 170, 15, 1, 150, 6, 3, 1, 0, 6), bag, "Almonds, sea salt.", TN, VGF, "Dry roasted, salted whole almonds."),
        (OLDMILL, "Lightly Salted Roasted Almonds", "nuts", N(OZ1, 170, 15, 1, 55, 6, 3, 1, 0, 6), bag, "Almonds, sea salt.", TN, VGF,
         "Dry roasted almonds with a light sprinkle of salt: 55 mg sodium per ounce."),
        (OLDMILL, "Deluxe Mixed Nuts, Lightly Salted", "nuts", N(OZ1, 170, 15, 2, 55, 6, 2, 1, 0, 5), [S("15OZ", "15 oz canister", 10.99, 15)],
         "Cashews, almonds, pecans, Brazil nuts, hazelnuts, sunflower oil, sea salt.", TN, VGF, "Mixed tree nuts with no peanuts, lightly salted."),
        (OLDMILL, "Mixed Nuts with Peanuts", "nuts", N(OZ1, 170, 15, 2, 150, 6, 2, 1, 0, 6), [S("16OZ", "16 oz canister", 6.99, 16)],
         "Peanuts, cashews, almonds, pecans, Brazil nuts, peanut oil, salt.", ("peanuts", "tree nuts"), VGF, "Salted mixed nuts with peanuts."),
        (OLDMILL, "Roasted & Salted Pistachios", "nuts", N(OZ1, 160, 13, 1.5, 160, 8, 3, 2, 0, 6), [S("12OZ", "12 oz bag", 7.99, 12)],
         "Pistachios, salt.", TN, VGF, "Shelled pistachio kernels, roasted and salted."),
        (OLDMILL, "Walnut Halves & Pieces", "nuts", N(OZ1, 190, 18, 1.5, 0, 4, 2, 1, 0, 4), [S("16OZ", "16 oz bag", 8.99, 16)], "Walnuts.", TN,
         (*VGF, "no-salt-added", "unsweetened"), "Raw walnut halves and pieces for baking and snacking."),
        (LONESTAR, "Texas Pecan Halves", "nuts", N(OZ1, 200, 20, 2, 0, 4, 3, 1, 0, 3), [S("12OZ", "12 oz bag", 9.99, 12)], "Pecans.", TN,
         (*VGF, "no-salt-added", "unsweetened", "local"), "Raw pecan halves grown in Texas orchards."),
        (LONESTAR, "Cinnamon Glazed Texas Pecans", "nuts", N(OZ1, 170, 13, 1, 45, 12, 2, 9, 9, 2), [S("8OZ", "8 oz bag", 7.99, 8)],
         "Pecans, cane sugar, cinnamon, salt.", TN, (*VGF, "local"), "Texas-grown pecans glazed with cinnamon sugar."),
        (OLDMILL, "Roasted & Salted Sunflower Kernels", "nuts", N("1/4 cup (30 g)", 190, 16, 1.5, 125, 6, 3, 1, 0, 6), [S("16OZ", "16 oz bag", 3.99, 16)],
         "Sunflower kernels, salt, sunflower oil.", (), (*VGF, "nut-free"), "Shelled sunflower seeds, a nut-free snack. Packed in a peanut-free facility."),
        (OLDMILL, "Roasted & Salted Pepitas", "nuts", N(OZ1, 170, 14, 2.5, 115, 4, 2, 0, 0, 9), [S("12OZ", "12 oz bag", 5.49, 12)],
         "Pumpkin seeds, salt, sunflower oil.", (), (*VGF, "nut-free"), "Roasted green pumpkin seeds, a nut-free snack with 9 g protein."),
        (TRAILMARK, "Classic Trail Mix", "trail-mix", N("3 tbsp (30 g)", 140, 9, 2, 55, 12, 1, 8, 4, 4), [S("26OZ", "26 oz bag", 8.99, 26)],
         "Peanuts, raisins, candy-coated chocolate pieces (sugar, chocolate, milk, cocoa butter, soy lecithin, corn syrup, colors), almonds, cashews, peanut oil, salt.",
         ("peanuts", "tree nuts", "milk", "soy"), ("gluten-free",), "Peanuts, raisins, chocolate candies, almonds, and cashews."),
        (TRAILMARK, "Unsalted Mountain Trail Mix", "trail-mix", N(OZ1, 150, 10, 1.5, 0, 11, 2, 7, 0, 5), [S("14OZ", "14 oz bag", 6.99, 14)],
         "Peanuts, raisins, almonds, cashews, sunflower kernels.", ("peanuts", "tree nuts"), (*VGF, "no-salt-added", "unsweetened"),
         "Trail mix with no salt or sugar added; the sweetness is from raisins."),
        (TRAILMARK, "Nut & Chocolate Trail Mix", "trail-mix", N(OZ1, 160, 11, 3, 40, 12, 2, 8, 6, 4), [S("14OZ", "14 oz bag", 6.99, 14)],
         "Peanuts, dark chocolate chunks (sugar, chocolate, cocoa butter, milkfat, soy lecithin), almonds, cashews, salt.", ("peanuts", "tree nuts", "milk", "soy"),
         ("gluten-free",), "Roasted nuts with dark chocolate chunks."),
        (TRAILMARK, "Keto Trail Mix", "trail-mix", N(OZ1, 170, 15, 3, 65, 5, 3, 1, 0, 5), [S("10OZ", "10 oz bag", 8.99, 10)],
         "Almonds, pecans, pumpkin seeds, coconut, sugar-free dark chocolate chips (unsweetened chocolate, erythritol, cocoa butter), sea salt.",
         ("tree nuts",), ("gluten-free", "dairy-free", "vegan"), "Low-carb trail mix with nuts, seeds, coconut, and sugar-free chocolate. 2 g net carbs."),
        (STORE_BRAND, "Lightly Salted Mixed Nuts", "nuts", N(OZ1, 170, 15, 2, 55, 6, 2, 1, 0, 6), [S("16OZ", "16 oz canister", 5.99, 16)],
         "Peanuts, cashews, almonds, pecans, peanut oil, sea salt.", ("peanuts", "tree nuts"), VGF, "Mixed nuts with peanuts, lightly salted."),
        (STORE_BRAND, "Salted Dry Roasted Peanuts", "nuts", N(OZ1, 170, 14, 2, 190, 5, 2, 1, 0, 7), [S("16OZ", "16 oz jar", 2.99, 16)],
         "Peanuts, salt, paprika, onion, garlic.", PN, VGF, "Salted dry roasted peanuts."),
    ]  # fmt: skip
    return _rows(
        rows, ("low-sodium", "keto", "high-protein", "high-fiber", "no-added-sugar", "low-sugar")
    )


def bars() -> list[ProductSeed]:
    bar60 = "1 bar (60 g)"
    box12 = [S("4CT", "4 bars", 9.99, 8.5), S("12CT", "12 bars", 26.99, 25)]
    gbox = [S("8CT", "8 bars", 3.49, 6.7)]
    protein_ing = "Protein blend (milk protein isolate, whey protein isolate), soluble corn fiber, almonds, erythritol, water, natural flavors, sea salt, sucralose, stevia leaf extract"
    rows: list[Row] = [
        (IRONPEAK, "Chocolate Chip Cookie Dough Protein Bar", "protein-bar", N(bar60, 190, 8, 3, 190, 22, 14, 1, 1, 21), box12,
         f"{protein_ing}, chocolate chips (unsweetened chocolate, erythritol, cocoa butter).", ("milk", "tree nuts"), ("gluten-free",),
         "High-protein bar with 21 g protein, 14 g fiber, and 1 g sugar."),
        (IRONPEAK, "Birthday Cake Protein Bar", "protein-bar", N(bar60, 180, 7, 3, 200, 23, 13, 1, 1, 20), box12,
         f"{protein_ing}, sprinkles (sugar, corn starch, colors).", ("milk", "tree nuts"), ("gluten-free",), "Birthday cake protein bar: 20 g protein, 1 g sugar."),
        (IRONPEAK, "Peanut Butter Chocolate Protein Bar", "protein-bar", N(bar60, 200, 9, 3, 220, 21, 12, 1, 1, 21), box12,
         "Protein blend (milk protein isolate, whey protein isolate), soluble corn fiber, peanuts, erythritol, cocoa, natural flavors, sea salt, sucralose.",
         ("milk", "peanuts"), ("gluten-free",), "Peanut butter chocolate protein bar with 21 g protein."),
        (IRONPEAK, "Chocolate Brownie Protein Bar", "protein-bar", N(bar60, 190, 7, 3, 240, 23, 13, 1, 1, 20), box12,
         "Protein blend (milk protein isolate, whey protein isolate), soluble corn fiber, cocoa, almonds, erythritol, natural flavors, sea salt, sucralose.",
         ("milk", "tree nuts"), ("gluten-free",), "Fudgy chocolate brownie protein bar with 20 g protein."),
        (IRONPEAK, "Crisp Protein Bar, Chocolate Caramel", "protein-bar", N("1 bar (58 g)", 230, 9, 5, 150, 25, 1, 16, 15, 15), [S("5CT", "5 bars", 8.99, 10.2)],
         "Protein crisps (soy protein isolate, rice flour), milk chocolate coating (sugar, cocoa butter, milk, soy lecithin), caramel (corn syrup, sugar, milk), whey protein.",
         ("milk", "soy"), (), "Candy-bar-style crisp protein bar with 15 g protein but 16 g sugar, so not low sugar."),
        (IRONPEAK, "Crisp Protein Bar, Peanut Butter", "protein-bar", N("1 bar (58 g)", 240, 10, 4, 180, 24, 2, 14, 13, 16), [S("5CT", "5 bars", 8.99, 10.2)],
         "Protein crisps (soy protein isolate, rice flour), peanut butter, milk chocolate coating (sugar, cocoa butter, milk, soy lecithin), corn syrup, whey protein.",
         ("milk", "soy", "peanuts"), (), "Crisp peanut butter protein bar with 16 g protein and 14 g sugar."),
        (IRONPEAK, "Keto Bar, Chocolate Almond", "protein-bar", N("1 bar (40 g)", 190, 15, 6, 110, 15, 11, 1, 0, 8), [S("12CT", "12 bars", 24.99, 16.9)],
         "Almonds, coconut, cocoa butter, collagen, soluble corn fiber, erythritol, cocoa, sea salt, stevia leaf extract.", ("tree nuts",), ("gluten-free", "dairy-free"),
         "Keto bar with 4 g net carbs and 1 g sugar, made with nuts and collagen."),
        (IRONPEAK, "Keto Bar, Peanut Butter Chocolate Chip", "protein-bar", N("1 bar (40 g)", 200, 16, 5, 120, 14, 10, 1, 0, 9), [S("12CT", "12 bars", 24.99, 16.9)],
         "Peanuts, cocoa butter, collagen, soluble corn fiber, erythritol, unsweetened chocolate, sea salt, stevia leaf extract.", ("peanuts",), ("gluten-free", "dairy-free"),
         "Keto peanut butter bar with 4 g net carbs."),
        (IRONPEAK, "Keto Chocolate Chip Cookies", "cookies", N("1 cookie (21 g)", 100, 9, 4, 65, 7, 4, 1, 0, 3), [S("6CT", "6 cookies", 6.99, 4.4)],
         "Almond flour, butter, eggs, erythritol, sugar-free chocolate chips (unsweetened chocolate, erythritol), baking soda, sea salt, monk fruit extract.",
         ("tree nuts", "milk", "egg"), ("gluten-free", "grain-free"), "Grain-free keto cookies with 3 g net carbs and no added sugar."),
        (GREENSTRIDE, "Vegan Protein Bar, Chocolate Peanut Butter", "protein-bar", N(bar60, 250, 11, 3, 200, 24, 6, 9, 8, 15), box12,
         "Pea protein, peanut butter, brown rice syrup, cane sugar, cocoa, chicory root fiber, sunflower oil, sea salt.", ("peanuts",), ("vegan", "dairy-free", "gluten-free", "plant-based"),
         "Plant-based protein bar with 15 g pea protein."),
        (GREENSTRIDE, "Vegan Protein Bar, Salted Caramel", "protein-bar", N(bar60, 240, 10, 3, 230, 26, 6, 10, 9, 15), box12,
         "Pea protein, cashew butter, brown rice syrup, cane sugar, chicory root fiber, coconut oil, sea salt, natural flavors.", ("tree nuts",),
         ("vegan", "dairy-free", "gluten-free", "plant-based"), "Salted caramel vegan protein bar with 15 g protein."),
        (GREENSTRIDE, "Vegan Low Sugar Protein Bar, Chocolate Chip", "protein-bar", N("1 bar (50 g)", 200, 10, 3, 140, 21, 10, 3, 2, 12), box12,
         "Pea protein, almond butter, chicory root fiber, allulose, dark chocolate chips (cocoa, cane sugar), coconut oil, sea salt, monk fruit extract.",
         ("tree nuts",), ("vegan", "dairy-free", "gluten-free", "plant-based"), "Vegan protein bar with 12 g protein, 10 g fiber, and just 3 g sugar."),
        (GREENSTRIDE, "Fruit & Nut Bar, Cashew Cookie", "fruit-nut-bar", N("1 bar (48 g)", 230, 13, 2.5, 0, 24, 3, 18, 0, 6), [S("5CT", "5 bars", 6.49, 8.5)],
         "Dates, cashews.", ("tree nuts",), ("vegan", "dairy-free", "gluten-free", "unsweetened"),
         "Two-ingredient bar of dates and cashews. No added sugar, though dates make it 18 g sugar."),
        (GREENSTRIDE, "Fruit & Nut Bar, Peanut Butter Cookie", "fruit-nut-bar", N("1 bar (48 g)", 220, 12, 2, 125, 23, 4, 18, 0, 7), [S("5CT", "5 bars", 6.49, 8.5)],
         "Dates, peanuts, sea salt.", ("peanuts",), ("vegan", "dairy-free", "gluten-free", "unsweetened"), "Date and peanut bar with no added sugar."),
        (GREENSTRIDE, "Fruit & Nut Bar, Blueberry Muffin", "fruit-nut-bar", N("1 bar (45 g)", 190, 9, 1, 5, 26, 4, 19, 0, 4), [S("5CT", "5 bars", 6.49, 8)],
         "Dates, almonds, cashews, unsweetened blueberries, natural flavor.", ("tree nuts",), ("vegan", "dairy-free", "gluten-free", "unsweetened"),
         "Fruit and nut bar with blueberries and no added sugar."),
        (STORE_BRAND, "High Protein Bar, Chocolate Peanut Butter", "protein-bar", N(bar60, 210, 8, 3, 200, 24, 10, 2, 1, 20), [S("5CT", "5 bars", 7.99, 10.6)],
         "Protein blend (whey protein isolate, milk protein isolate), soluble corn fiber, peanuts, erythritol, cocoa, sea salt, sucralose.", ("milk", "peanuts"), ("gluten-free",),
         "High-protein bar with 20 g protein and 2 g sugar."),
        (STORE_BRAND, "High Protein Bar, Cookie Dough", "protein-bar", N(bar60, 200, 8, 3, 190, 23, 10, 2, 1, 20), [S("5CT", "5 bars", 7.99, 10.6)],
         "Protein blend (whey protein isolate, milk protein isolate), soluble corn fiber, almonds, erythritol, chocolate chips, sea salt, sucralose.", ("milk", "tree nuts"),
         ("gluten-free",), "Cookie dough protein bar with 20 g protein."),
        (TRAILMARK, "Chewy Chocolate Chip Granola Bars", "granola-bar", N("1 bar (24 g)", 100, 3, 1, 70, 17, 1, 7, 7, 1), gbox,
         "Whole grain rolled oats, brown rice syrup, chocolate chips (sugar, chocolate, cocoa butter, milkfat, soy lecithin), sugar, canola oil, glycerin, salt.",
         ("milk", "soy"), ("whole-grain",), "Soft, chewy granola bars with chocolate chips."),
        (TRAILMARK, "Chewy Peanut Butter Granola Bars", "granola-bar", N("1 bar (24 g)", 110, 4, 1, 85, 16, 1, 7, 7, 2), gbox,
         "Whole grain rolled oats, peanut butter, brown rice syrup, sugar, canola oil, glycerin, salt, soy lecithin.", ("peanuts", "soy"), ("whole-grain", "dairy-free"),
         "Chewy peanut butter granola bars."),
        (TRAILMARK, "Crunchy Oats & Honey Granola Bars", "granola-bar", N("2 bars (42 g)", 190, 7, 1, 160, 29, 2, 11, 11, 3), [S("12CT", "12 bars (6 pouches)", 3.99, 8.9)],
         "Whole grain oats, sugar, canola oil, rice flour, honey, salt, brown sugar syrup, soy lecithin, baking soda.", ("soy",), ("whole-grain", "dairy-free"),
         "Crunchy oat bars sweetened with honey."),
        (TRAILMARK, "Low Sugar Chewy Granola Bars, Chocolate Chip", "granola-bar", N("1 bar (24 g)", 100, 4, 1.5, 70, 17, 3, 1, 1, 1), gbox,
         "Whole grain rolled oats, chicory root fiber, allulose, chocolate chips (sugar, chocolate, cocoa butter), sunflower oil, salt, monk fruit extract.", (),
         ("whole-grain", "gluten-free", "vegan", "dairy-free"), "Chewy chocolate chip granola bars with 1 g sugar."),
        (TRAILMARK, "Nut & Seed Bar, Dark Chocolate Sea Salt", "granola-bar", N("1 bar (40 g)", 200, 15, 3, 125, 16, 7, 5, 5, 6), [S("6CT", "6 bars", 6.99, 8.4)],
         "Almonds, peanuts, chicory root fiber, dark chocolate (sugar, chocolate, cocoa butter, soy lecithin), honey, sea salt.", ("tree nuts", "peanuts", "soy"),
         ("gluten-free", "dairy-free"), "Whole nut bar drizzled with dark chocolate, 5 g sugar."),
        (TRAILMARK, "Kids' Strawberry Fruit & Oat Bars", "granola-bar", N("1 bar (24 g)", 90, 2, 0, 60, 18, 1, 8, 7, 1), gbox,
         "Whole grain oats, brown rice syrup, strawberry filling (sugar, strawberry puree), rice flour, sunflower oil, salt.", (), ("whole-grain", "vegan", "dairy-free", "kids"),
         "Soft oat bars with strawberry filling for lunchboxes."),
        (FREESTONE, "Gluten-Free Blueberry Oat Bars", "granola-bar", N("1 bar (35 g)", 140, 5, 0.5, 80, 23, 2, 9, 8, 2), [S("5CT", "5 bars", 4.99, 6.2)],
         "Gluten-free oats, brown rice syrup, dried blueberries, sunflower oil, cane sugar, sea salt.", (), ("gluten-free", "vegan", "dairy-free", "whole-grain"),
         "Soft baked gluten-free oat bars with blueberries."),
        (OAKMEADOW, "Organic Chewy Granola Bars, Chocolate Chip", "granola-bar", N("1 bar (28 g)", 110, 3.5, 1.5, 65, 19, 1, 7, 7, 1), [S("6CT", "6 bars", 4.49, 6)],
         "Organic rolled oats, organic brown rice syrup, organic chocolate chips (organic cane sugar, organic chocolate, organic milk), organic sunflower oil, sea salt.",
         ("milk",), ("whole-grain", "non-gmo"), "Organic chewy granola bars."),
        (STORE_BRAND, "Chewy Chocolate Chip Granola Bars", "granola-bar", N("1 bar (24 g)", 100, 3, 1, 70, 17, 1, 7, 7, 1), [S("12CT", "12 bars", 3.49, 10)],
         "Whole grain rolled oats, brown rice syrup, chocolate chips (sugar, chocolate, milkfat, soy lecithin), sugar, canola oil, salt.", ("milk", "soy"), ("whole-grain",),
         "Chewy chocolate chip granola bars."),
        (STORE_BRAND, "Crunchy Oats & Honey Granola Bars", "granola-bar", N("2 bars (42 g)", 190, 7, 1, 160, 29, 2, 11, 11, 3), [S("12CT", "12 bars (6 pouches)", 2.79, 8.9)],
         "Whole grain oats, sugar, canola oil, rice flour, honey, salt, soy lecithin.", ("soy",), ("whole-grain", "dairy-free"), "Crunchy oats and honey bars."),
    ]  # fmt: skip
    return _rows(rows, SWEET_CLAIMS)


def sweets() -> list[ProductSeed]:
    pack = [S("13OZ", "13 oz package", 3.99, 13)]
    spack = [S("13OZ", "13 oz package", 2.79, 13)]
    WS = ("wheat", "soy")
    WMES = ("wheat", "milk", "egg", "soy")
    choc_bar = [S("EA", "3.5 oz bar", 3.49, 3.5)]
    rows: list[Row] = [
        (SWEETHOLLOW, "Chocolate Sandwich Cookies", "cookies", N("3 cookies (34 g)", 160, 7, 2, 135, 25, 1, 14, 13, 1), pack,
         "Sugar, enriched wheat flour, palm oil, cocoa, high fructose corn syrup, leavening, salt, soy lecithin, vanillin.", WS, VG,
         "Crunchy chocolate cookies with vanilla creme filling. Made without milk or eggs."),
        (SWEETHOLLOW, "Extra Creme Chocolate Sandwich Cookies", "cookies", N("2 cookies (29 g)", 140, 7, 2, 105, 21, 1, 13, 12, 1), pack,
         "Sugar, enriched wheat flour, palm oil, cocoa, high fructose corn syrup, leavening, salt, soy lecithin, vanillin.", WS, VG, "Chocolate sandwich cookies with double the creme."),
        (SWEETHOLLOW, "Crispy Chocolate Chip Cookies", "cookies", N("3 cookies (34 g)", 160, 8, 2.5, 110, 22, 1, 11, 10, 2), pack,
         "Enriched wheat flour, semisweet chocolate chips (sugar, chocolate, cocoa butter, milkfat, soy lecithin), sugar, palm oil, brown sugar, whey, salt, eggs.", WMES, (),
         "Crunchy chocolate chip cookies."),
        (SWEETHOLLOW, "Chewy Chocolate Chip Cookies", "cookies", N("2 cookies (29 g)", 140, 6, 2.5, 95, 20, 1, 11, 10, 1), pack,
         "Enriched wheat flour, chocolate chips (sugar, chocolate, milkfat, soy lecithin), sugar, soybean oil, corn syrup, eggs, salt, baking soda.", WMES, (),
         "Soft-baked chewy chocolate chip cookies."),
        (SWEETHOLLOW, "Oatmeal Raisin Cookies", "cookies", N("2 cookies (30 g)", 130, 5, 1.5, 100, 20, 1, 10, 9, 2), pack,
         "Rolled oats, enriched wheat flour, raisins, sugar, soybean oil, brown sugar, eggs, cinnamon, salt, baking soda.", ("wheat", "egg"), ("dairy-free",),
         "Soft oatmeal raisin cookies."),
        (SWEETHOLLOW, "Butter Shortbread Cookies", "cookies", N("4 cookies (32 g)", 160, 8, 4, 110, 20, 0, 6, 6, 2), [S("10OZ", "10 oz tin", 4.49, 10)],
         "Enriched wheat flour, butter (cream, salt), sugar, corn starch, salt.", ("wheat", "milk"), (), "Rich, crumbly all-butter shortbread."),
        (SWEETHOLLOW, "Vanilla Wafers", "cookies", N("8 wafers (30 g)", 140, 6, 1.5, 100, 21, 0, 11, 11, 1), [S("11OZ", "11 oz box", 3.49, 11)],
         "Enriched wheat flour, sugar, soybean oil, eggs, whey (milk), salt, leavening, natural vanilla flavor, soy lecithin.", WMES, (), "Crisp vanilla wafers for snacking and banana pudding."),
        (SWEETHOLLOW, "Fig Bars", "cookies", N("2 bars (32 g)", 110, 1.5, 0, 110, 22, 1, 12, 10, 1), [S("10OZ", "10 oz package", 3.49, 10)],
         "Figs, enriched wheat flour, sugar, corn syrup, soybean oil, salt, baking soda.", ("wheat",), VG, "Soft cake cookies filled with fig paste."),
        (SWEETHOLLOW, "Sugar Free Chocolate Chip Cookies", "cookies", N("3 cookies (30 g)", 130, 7, 3, 85, 19, 1, 0, 0, 2), [S("8OZ", "8 oz package", 3.99, 8)],
         "Enriched wheat flour, maltitol, sugar-free chocolate chips (maltitol, chocolate, cocoa butter, milkfat, soy lecithin), palm oil, eggs, salt, sucralose.", WMES, (),
         "Chocolate chip cookies with 0 g sugar, sweetened with maltitol and sucralose. Maltitol may cause digestive upset."),
        (SWEETHOLLOW, "Sugar Free Vanilla Creme Sandwich Cookies", "cookies", N("3 cookies (30 g)", 140, 6, 2, 75, 21, 1, 0, 0, 1), [S("8OZ", "8 oz package", 3.99, 8)],
         "Enriched wheat flour, maltitol, palm oil, polydextrose, salt, soy lecithin, natural vanilla flavor, sucralose.", WS, VG,
         "Sugar free vanilla sandwich cookies sweetened with maltitol and sucralose."),
        (FREESTONE, "Gluten-Free Chocolate Chip Cookies", "cookies", N("3 cookies (30 g)", 150, 7, 3, 110, 21, 1, 10, 10, 1), [S("7OZ", "7 oz box", 4.49, 7)],
         "Rice flour, cane sugar, chocolate chips (cane sugar, chocolate, cocoa butter), palm oil, tapioca starch, eggs, baking soda, sea salt.", ("egg",),
         ("gluten-free", "dairy-free"), "Crunchy gluten-free chocolate chip cookies. Contains egg."),
        (FREESTONE, "Gluten-Free Chocolate Sandwich Cookies", "cookies", N("2 cookies (27 g)", 130, 5, 1.5, 95, 20, 1, 10, 10, 1), [S("10OZ", "10 oz box", 4.99, 10)],
         "Rice flour, cane sugar, palm oil, cocoa, tapioca starch, corn starch, sea salt, sunflower lecithin.", (), ("gluten-free", "vegan", "dairy-free"),
         "Gluten-free and vegan chocolate sandwich cookies."),
        (FREESTONE, "Grain-Free Almond Flour Chocolate Chip Cookies", "cookies", N("3 cookies (28 g)", 140, 9, 3, 85, 13, 1, 7, 7, 2), [S("5OZ", "4.5 oz box", 5.49, 4.5)],
         "Almond flour, coconut sugar, chocolate chips (cane sugar, chocolate, cocoa butter), coconut oil, eggs, tapioca starch, baking soda, sea salt.", ("tree nuts", "egg"),
         ("gluten-free", "grain-free", "dairy-free"), "Grain-free crunchy cookies made with almond flour."),
        (STORE_BRAND, "Chocolate Sandwich Cookies", "cookies", N("3 cookies (34 g)", 160, 7, 2, 135, 25, 1, 14, 13, 1), spack,
         "Sugar, enriched wheat flour, palm oil, cocoa, high fructose corn syrup, leavening, salt, soy lecithin.", WS, VG, "Chocolate sandwich cookies with creme filling."),
        (STORE_BRAND, "Chocolate Chip Cookies", "cookies", N("3 cookies (34 g)", 160, 8, 2.5, 110, 22, 1, 11, 10, 2), spack,
         "Enriched wheat flour, chocolate chips (sugar, chocolate, milkfat, soy lecithin), sugar, palm oil, whey, salt, eggs.", WMES, (), "Crunchy chocolate chip cookies."),
        (STORE_BRAND, "Animal Crackers", "cookies", N("16 crackers (30 g)", 130, 4, 1, 115, 22, 0, 6, 6, 2), [S("16OZ", "16 oz tub", 3.49, 16)],
         "Enriched wheat flour, sugar, soybean oil, corn syrup, salt, leavening, soy lecithin.", WS, (*VG, "kids"), "Lightly sweet animal-shaped crackers kids love."),
        (COCOALANE, "Milk Chocolate Bar", "chocolate", N("1/3 bar (34 g)", 180, 10, 6, 30, 20, 1, 19, 18, 2), choc_bar,
         "Sugar, cocoa butter, whole milk powder, chocolate, soy lecithin, vanilla.", ("milk", "soy"), ("gluten-free",), "Creamy milk chocolate bar."),
        (COCOALANE, "Dark Chocolate Bar, 55% Cacao", "chocolate", N("1/3 bar (34 g)", 180, 12, 7, 5, 19, 3, 14, 14, 2), choc_bar,
         "Chocolate, sugar, cocoa butter, milkfat, soy lecithin, vanilla.", ("milk", "soy"), ("gluten-free",), "Semi-sweet 55% cacao dark chocolate. Contains milkfat, so not vegan."),
        (COCOALANE, "Dark Chocolate Bar, 72% Cacao", "chocolate", N("1/3 bar (34 g)", 190, 15, 9, 0, 14, 4, 8, 8, 3), choc_bar,
         "Chocolate, cane sugar, cocoa butter, vanilla.", (), ("vegan", "dairy-free", "gluten-free"), "Bittersweet 72% cacao dark chocolate, made without milk."),
        (COCOALANE, "Extra Dark Chocolate Bar, 85% Cacao", "chocolate", N("1/3 bar (34 g)", 200, 17, 10, 0, 11, 5, 4, 4, 4), choc_bar,
         "Chocolate, cocoa butter, cane sugar, vanilla.", (), ("vegan", "dairy-free", "gluten-free"), "Intense 85% cacao chocolate with only 4 g sugar."),
        (COCOALANE, "Organic Dark Chocolate Sea Salt Bar, 70% Cacao", "chocolate", N("1/3 bar (34 g)", 190, 14, 8, 60, 15, 4, 9, 9, 3), choc_bar,
         "Organic chocolate, organic cane sugar, organic cocoa butter, sea salt.", (), ("vegan", "dairy-free", "gluten-free", "fair-trade", "non-gmo"),
         "Organic, fair trade 70% dark chocolate with sea salt."),
        (COCOALANE, "Sugar Free Dark Chocolate Bar, 55% Cacao", "chocolate", N("1/3 bar (34 g)", 150, 13, 8, 0, 17, 9, 0, 0, 2), choc_bar,
         "Unsweetened chocolate, erythritol, inulin, cocoa butter, sunflower lecithin, stevia leaf extract, vanilla.", (), ("vegan", "dairy-free", "gluten-free"),
         "Dark chocolate with 0 g sugar, sweetened with stevia and erythritol."),
        (COCOALANE, "No Sugar Added Milk Chocolate Bar", "chocolate", N("1/3 bar (34 g)", 170, 12, 7, 35, 19, 6, 4, 0, 3), choc_bar,
         "Cocoa butter, erythritol, whole milk powder, inulin, chocolate, sunflower lecithin, stevia leaf extract.", ("milk",), ("gluten-free",),
         "Creamy milk chocolate with no sugar added; about 4 g of natural milk sugar."),
        (COCOALANE, "Milk Chocolate Peanut Butter Cups", "candy", N("1 package (42 g)", 210, 13, 4.5, 150, 24, 1, 22, 21, 5), [S("EA", "1.5 oz (2 cups)", 1.49, 1.5), S("8PK", "8 packs", 9.99, 12)],
         "Milk chocolate (sugar, cocoa butter, chocolate, milk, soy lecithin), peanuts, sugar, dextrose, salt.", ("milk", "peanuts", "soy"), ("gluten-free",),
         "Milk chocolate cups filled with peanut butter."),
        (COCOALANE, "Sugar Free Peanut Butter Cups", "candy", N("4 pieces (37 g)", 170, 13, 6, 70, 19, 4, 0, 0, 3), [S("3OZ", "3 oz bag", 3.99, 3)],
         "Sugar free milk chocolate (maltitol, cocoa butter, chocolate, milk, soy lecithin), peanuts, maltitol, salt.", ("milk", "peanuts", "soy"), ("gluten-free",),
         "Peanut butter cups with 0 g sugar, sweetened with maltitol."),
        (COCOALANE, "Milk Chocolate Covered Almonds", "candy", N(OZ1, 150, 10, 4, 15, 13, 2, 11, 10, 3), [S("10OZ", "10 oz bag", 5.99, 10)],
         "Milk chocolate (sugar, cocoa butter, chocolate, milk, soy lecithin), almonds, confectioner's glaze.", ("milk", "tree nuts", "soy"), ("gluten-free",),
         "Roasted almonds covered in milk chocolate."),
        (SUGARBIRD, "Gummy Bears", "candy", N("17 pieces (40 g)", 130, 0, 0, 15, 31, 0, 21, 21, 3), [S("12OZ", "12 oz bag", 2.99, 12)],
         "Corn syrup, sugar, gelatin, citric acid, natural and artificial flavors, pectin, colors.", (), ("gluten-free", "dairy-free"),
         "Fruity gummy bears. Made with gelatin, so not vegetarian or vegan."),
        (SUGARBIRD, "Vegan Gummy Bears", "candy", N("17 pieces (40 g)", 130, 0, 0, 10, 32, 0, 20, 20, 0), [S("8OZ", "8 oz bag", 3.49, 8)],
         "Tapioca syrup, cane sugar, pectin, citric acid, natural flavors, fruit and vegetable juice (color).", (), ("vegan", "gluten-free", "dairy-free"),
         "Gelatin-free gummy bears made with fruit pectin. Vegan."),
        (SUGARBIRD, "Sour Gummy Worms", "candy", N("7 pieces (40 g)", 130, 0, 0, 20, 31, 0, 22, 22, 2), [S("9OZ", "9 oz bag", 2.99, 9)],
         "Corn syrup, sugar, gelatin, citric acid, malic acid, natural and artificial flavors, colors.", (), ("gluten-free", "dairy-free"), "Tangy, sugar-coated gummy worms."),
        (SUGARBIRD, "Sugar Free Gummy Bears", "candy", N("17 pieces (40 g)", 90, 0, 0, 10, 31, 0, 0, 0, 3), [S("5OZ", "5 oz bag", 3.49, 5)],
         "Maltitol syrup, gelatin, citric acid, natural and artificial flavors, colors.", (), ("gluten-free", "dairy-free"),
         "Gummy bears with 0 g sugar, sweetened with maltitol. Contains gelatin. Eat in moderation."),
        (SUGARBIRD, "Sugar Free Peppermint Hard Candies", "candy", N("3 pieces (15 g)", 25, 0, 0, 0, 14, 0, 0, 0, 0), [S("6OZ", "6 oz bag", 2.99, 6)],
         "Isomalt, natural peppermint oil, acesulfame potassium, red 40.", (), ("vegan", "gluten-free", "dairy-free"), "Sugar free peppermint candies sweetened with isomalt."),
        (SUGARBIRD, "Butterscotch Hard Candies", "candy", N("3 pieces (16 g)", 60, 0.5, 0, 65, 15, 0, 11, 11, 0), [S("7OZ", "7 oz bag", 2.49, 7)],
         "Sugar, corn syrup, butter (cream, salt), salt, natural flavor.", ("milk",), ("gluten-free",), "Classic buttery butterscotch discs."),
        (SUGARBIRD, "Strawberry Licorice Twists", "candy", N("4 pieces (40 g)", 140, 0.5, 0, 110, 33, 0, 16, 16, 1), [S("16OZ", "16 oz bag", 2.99, 16)],
         "Corn syrup, enriched wheat flour, sugar, corn starch, palm oil, citric acid, artificial flavor, red 40.", ("wheat",), VG, "Chewy strawberry licorice twists. Contains wheat."),
        (SUGARBIRD, "Texas Pecan Pralines", "candy", N("1 praline (43 g)", 200, 9, 2.5, 50, 28, 1, 26, 25, 1), [S("6CT", "6 pralines", 8.99, 9)],
         "Sugar, pecans, cream, butter, corn syrup, vanilla, salt.", ("milk", "tree nuts"), ("gluten-free",), "Creamy Southern pralines made with Texas pecans."),
    ]  # fmt: skip
    return _rows(rows, SWEET_CLAIMS)


def other_snacks() -> list[ProductSeed]:
    pouches = [S("10CT", "10 pouches", 3.29, 8)]
    rows: list[Row] = [
        (JOLLY, "Mixed Fruit Snacks", "fruit-snacks", N("1 pouch (23 g)", 80, 0, 0, 15, 19, 0, 11, 10, 1), pouches,
         "Fruit puree, corn syrup, sugar, modified corn starch, gelatin, citric acid, natural flavors, colors.", (), ("gluten-free", "dairy-free", "kids"),
         "Fruit-flavored gummy snacks for kids. Contains gelatin."),
        (JOLLY, "Organic Berry Patch Fruit Snacks", "fruit-snacks", N("1 pouch (23 g)", 70, 0, 0, 10, 17, 0, 11, 10, 0), pouches,
         "Organic tapioca syrup, organic cane sugar, organic fruit juice concentrate, pectin, citric acid, natural flavors.", (),
         ("vegan", "gluten-free", "dairy-free", "kids", "non-gmo"), "Organic, vegan fruit snacks made with pectin instead of gelatin."),
        (JOLLY, "Reduced Sugar Fruit Snacks", "fruit-snacks", N("1 pouch (20 g)", 60, 0, 0, 15, 17, 3, 5, 4, 1), pouches,
         "Soluble corn fiber, fruit puree, sugar, gelatin, citric acid, natural flavors, colors.", (), ("gluten-free", "dairy-free", "kids"),
         "Fruit snacks with 5 g sugar, about half the sugar of our regular."),
        (JOLLY, "100% Fruit Strawberry Leathers", "fruit-snacks", N("1 bar (14 g)", 45, 0, 0, 0, 11, 1, 8, 0, 0), [S("12CT", "12 bars", 5.49, 6)],
         "Apple puree, strawberry puree, lemon juice concentrate.", (), ("vegan", "gluten-free", "dairy-free", "unsweetened", "kids"),
         "Fruit leather made only from fruit, with no sugar added."),
        (STORE_BRAND, "Mixed Berry Fruit Snacks", "fruit-snacks", N("1 pouch (23 g)", 80, 0, 0, 15, 19, 0, 11, 10, 1), [S("22CT", "22 pouches", 5.49, 17.6)],
         "Fruit puree, corn syrup, sugar, modified corn starch, gelatin, citric acid, natural flavors, colors.", (), ("gluten-free", "dairy-free", "kids"), "Mixed berry fruit snacks."),
        (STORE_BRAND, "Unsweetened Dried Mango", "dried-fruit", N("1/4 cup (40 g)", 120, 0, 0, 10, 31, 2, 26, 0, 1), [S("6OZ", "6 oz bag", 4.49, 6)],
         "Mango.", (), ("vegan", "gluten-free", "dairy-free", "unsweetened"), "Chewy dried mango slices with no sugar added."),
        (STORE_BRAND, "Seedless Raisins", "dried-fruit", N("1/4 cup (40 g)", 130, 0, 0, 10, 31, 2, 29, 0, 1), [S("20OZ", "20 oz canister", 3.99, 20), S("6PK", "6 x 1 oz boxes", 2.49, 6)],
         "Raisins.", (), ("vegan", "gluten-free", "dairy-free", "unsweetened"), "Sun-dried seedless raisins."),
        (STORE_BRAND, "Sweetened Dried Cranberries", "dried-fruit", N("1/3 cup (40 g)", 130, 0, 0, 0, 33, 2, 29, 26, 0), [S("6OZ", "6 oz bag", 2.99, 6)],
         "Cranberries, sugar, sunflower oil.", (), ("vegan", "gluten-free", "dairy-free"), "Dried cranberries sweetened with sugar."),
        (STORE_BRAND, "Lightly Salted Brown Rice Cakes", "rice-cakes", N("1 cake (9 g)", 35, 0, 0, 20, 7, 0, 0, 0, 1), [S("4OZ", "4.5 oz package", 1.99, 4.5)],
         "Whole grain brown rice, salt.", (), ("vegan", "gluten-free", "dairy-free", "whole-grain"), "Crunchy whole grain rice cakes with a little salt."),
        (STORE_BRAND, "Unsalted Brown Rice Cakes", "rice-cakes", N("1 cake (9 g)", 35, 0, 0, 0, 7, 0, 0, 0, 1), [S("4OZ", "4.5 oz package", 1.99, 4.5)],
         "Whole grain brown rice.", (), ("vegan", "gluten-free", "dairy-free", "whole-grain", "no-salt-added", "unsweetened"), "Plain rice cakes with no salt added."),
        (OAKMEADOW, "Organic Unsalted Brown Rice Cakes", "rice-cakes", N("1 cake (19 g)", 70, 0.5, 0, 0, 15, 1, 0, 0, 1), [S("8OZ", "8.5 oz package", 3.99, 8.5)],
         "Organic whole grain brown rice.", (), ("vegan", "gluten-free", "dairy-free", "whole-grain", "no-salt-added", "unsweetened", "non-gmo"), "Organic unsalted rice cakes."),
        (STORE_BRAND, "Caramel Corn Rice Cakes", "rice-cakes", N("1 cake (13 g)", 50, 0, 0, 35, 11, 0, 4, 4, 1), [S("6OZ", "6.5 oz package", 2.49, 6.5)],
         "Whole grain brown rice, corn, sugar, fructose, salt, natural caramel flavor.", (), ("vegan", "gluten-free", "dairy-free"), "Sweet caramel-flavored rice cakes."),
        (STORE_BRAND, "White Cheddar Mini Rice Cakes", "rice-cakes", N("9 cakes (15 g)", 70, 2, 0, 140, 11, 0, 0, 0, 1), [S("6OZ", "6 oz bag", 2.99, 6)],
         "Whole grain brown rice, white cheddar seasoning (cheddar cheese (milk), whey, salt), sunflower oil.", ("milk",), ("gluten-free", "whole-grain"),
         "Bite-size rice cakes with white cheddar."),
        (HICKORY, "Original Beef Jerky", "jerky", N(OZ1, 80, 1, 0.5, 590, 6, 0, 5, 5, 11), [S("3OZ", "3.25 oz bag", 7.99, 3.25)],
         "Beef, water, sugar, soy sauce (water, soybeans, wheat, salt), salt, natural flavors, sodium nitrite.", ("soy", "wheat"), ("dairy-free",),
         "Tender marinated beef jerky with 11 g protein."),
        (HICKORY, "Teriyaki Beef Jerky", "jerky", N(OZ1, 80, 1, 0, 550, 8, 0, 7, 7, 10), [S("3OZ", "3.25 oz bag", 7.99, 3.25)],
         "Beef, sugar, soy sauce (water, soybeans, wheat, salt), pineapple juice, garlic, ginger, sodium nitrite.", ("soy", "wheat"), ("dairy-free",), "Sweet teriyaki beef jerky."),
        (HICKORY, "Peppered Beef Jerky", "jerky", N(OZ1, 80, 1, 0.5, 560, 5, 0, 4, 4, 11), [S("3OZ", "3.25 oz bag", 7.99, 3.25)],
         "Beef, water, sugar, cracked black pepper, soy sauce (water, soybeans, wheat, salt), salt, sodium nitrite.", ("soy", "wheat"), ("dairy-free",), "Beef jerky coated in black pepper."),
        (HICKORY, "Zero Sugar Beef Jerky", "jerky", N(OZ1, 70, 1.5, 0.5, 510, 1, 0, 0, 0, 13), [S("2OZ", "2.5 oz bag", 7.99, 2.5)],
         "Beef, water, tamari (water, soybeans, salt), sea salt, black pepper, garlic, celery powder.", ("soy",), ("gluten-free", "dairy-free"),
         "Keto-friendly beef jerky with 0 g sugar and 13 g protein. Made with gluten-free tamari."),
        (BLUESTEM, "Grass-Fed Beef Jerky, Original", "jerky", N(OZ1, 70, 1, 0, 450, 4, 0, 3, 3, 12), [S("2OZ", "2.5 oz bag", 8.99, 2.5)],
         "Grass-fed beef, water, coconut aminos, cane sugar, sea salt, garlic, black pepper.", (), ("grass-fed", "local", "gluten-free", "dairy-free"),
         "Jerky made from 100% grass-fed Texas beef, soy free and gluten free."),
        (HICKORY, "Turkey Jerky", "jerky", N(OZ1, 70, 1, 0, 530, 6, 0, 5, 5, 11), [S("3OZ", "3.25 oz bag", 7.49, 3.25)],
         "Turkey, water, sugar, soy sauce (water, soybeans, wheat, salt), salt, natural flavors, sodium nitrite.", ("soy", "wheat"), ("dairy-free",), "Lean, marinated turkey jerky."),
        (SEAGLASS, "Roasted Seaweed Snacks, Sea Salt", "seaweed-snacks", N("1 package (5 g)", 25, 2, 0, 40, 1, 1, 0, 0, 1), [S("6PK", "6 x 0.17 oz packs", 4.99, 1)],
         "Seaweed, sunflower oil, sea salt.", (), ("vegan", "gluten-free", "dairy-free"), "Crispy roasted seaweed sheets with a light sprinkle of sea salt."),
        (SEAGLASS, "Roasted Seaweed Snacks, Wasabi", "seaweed-snacks", N("1 package (5 g)", 25, 2, 0, 55, 1, 1, 0, 0, 1), [S("6PK", "6 x 0.17 oz packs", 4.99, 1)],
         "Seaweed, sunflower oil, sea salt, wasabi powder.", (), ("vegan", "gluten-free", "dairy-free"), "Roasted seaweed with a kick of wasabi."),
        (SEAGLASS, "Organic Roasted Seaweed Snacks, Teriyaki", "seaweed-snacks", N("1 package (5 g)", 30, 2, 0, 80, 2, 1, 1, 1, 1), [S("6PK", "6 x 0.17 oz packs", 5.49, 1)],
         "Organic seaweed, organic sunflower oil, organic tamari (water, organic soybeans, salt), organic cane sugar, sea salt.", ("soy",),
         ("vegan", "gluten-free", "dairy-free", "non-gmo"), "Organic roasted seaweed with a sweet teriyaki glaze."),
    ]  # fmt: skip
    return _rows(rows, (*SWEET_CLAIMS, "low-sodium"))


def products() -> list[ProductSeed]:
    return [*chips(), *crackers_pretzels_popcorn(), *nuts(), *bars(), *sweets(), *other_snacks()]


__all__ = ["products"]
