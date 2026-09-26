"""Fresh Produce: fruit, vegetables, bagged salads, fresh herbs, and cut fruit.

Conventional and organic versions of the staples, Texas-grown seasonal items tagged
"local", and nutrition from typical FDA raw-produce label values.
"""

from __future__ import annotations

from dataclasses import dataclass

from commerce.seed.data import Nutrition, ProductSeed
from commerce.seed.gen.common import REFRIGERATED, STORE_BRAND, Size, cents, food

CAT = "produce"
CEDAR = "Cedar Hollow Farms"  # organic
LONESTAR = "Lone Star Harvest"  # Texas grown
GREENMESA = "Green Mesa Salad Co."  # bagged salads and kits

ROOM = "Store at room temperature."
COOL_DARK = "Store in a cool, dark, dry place; do not refrigerate."
RIPEN = "Ripen at room temperature, then refrigerate."
CLAIMS = ("low-sugar", "high-fiber", "keto")


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


@dataclass(frozen=True)
class Crop:
    name: str  # title for the conventional version
    ptype: str
    facts: Nutrition
    sizes: tuple[Size, ...]
    storage: str
    about: str  # first sentence of the description
    origin: str
    organic: bool = False  # also sold as a Cedar Hollow Farms organic version


APPLE = N("1 medium apple (154 g)", 80, 0, 0, 0, 22, 5, 16, 0, 0)
GRAPE = N("3/4 cup (126 g)", 90, 0, 0, 0, 23, 1, 20, 0, 0)
PEACH = N("1 medium peach (147 g)", 60, 0.5, 0, 0, 15, 2, 13, 0, 1)
MELON = N("1/4 medium melon (134 g)", 50, 0, 0, 20, 12, 1, 11, 0, 1)
WATERMELON = N("2 cups diced (280 g)", 80, 0, 0, 0, 21, 1, 17, 0, 1)
GRAPEFRUIT = N("1/2 medium grapefruit (154 g)", 60, 0, 0, 0, 16, 2, 11, 0, 1)
ONION = N("1 medium onion (148 g)", 45, 0, 0, 5, 11, 3, 9, 0, 1)
POTATO = N("1 medium potato (148 g)", 110, 0, 0, 0, 26, 2, 1, 0, 3)
TOMATO = N("1 medium tomato (148 g)", 25, 0, 0, 20, 5, 1, 3, 0, 1)
PEPPER = N("1 medium pepper (148 g)", 25, 0, 0, 40, 6, 2, 4, 0, 1)
SQUASH = N("1 cup sliced (113 g)", 20, 0, 0, 10, 4, 1, 3, 0, 1)
MUSHROOM = N("5 medium mushrooms (84 g)", 20, 0, 0, 0, 3, 1, 2, 0, 3)

FRUIT: tuple[Crop, ...] = (
    Crop("Gala Apples", "apples", APPLE, (S("1LB", "1 lb (about 3 apples)", 1.69, 16), S("3LB", "3 lb bag", 4.49, 48)), REFRIGERATED,
         "Crisp, mildly sweet Gala apples for snacking and lunchboxes.", "Washington", True),
    Crop("Honeycrisp Apples", "apples", APPLE, (S("1LB", "1 lb (about 2 apples)", 2.99, 16), S("3LB", "3 lb bag", 7.99, 48)), REFRIGERATED,
         "Extra crisp, juicy Honeycrisp apples with a sweet-tart flavor.", "Washington", True),
    Crop("Granny Smith Apples", "apples", APPLE, (S("1LB", "1 lb (about 3 apples)", 1.79, 16), S("3LB", "3 lb bag", 4.99, 48)), REFRIGERATED,
         "Tart green Granny Smith apples, firm enough for pies and baking.", "Washington", True),
    Crop("Fuji Apples", "apples", APPLE, (S("1LB", "1 lb (about 3 apples)", 1.79, 16), S("3LB", "3 lb bag", 4.99, 48)), REFRIGERATED,
         "Sweet, dense Fuji apples that keep well in the fridge.", "Washington"),
    Crop("Bananas", "bananas", N("1 medium banana (126 g)", 110, 0, 0, 0, 30, 3, 19, 0, 1), (S("BN", "1 bunch (about 2.5 lb)", 1.49, 40),), ROOM,
         "Yellow Cavendish bananas sold by the bunch; they ripen on the counter.", "Guatemala", True),
    Crop("Strawberries", "berries", N("8 medium strawberries (147 g)", 50, 0, 0, 0, 11, 2, 8, 0, 1), (S("1LB", "1 lb clamshell", 3.49, 16), S("2LB", "2 lb clamshell", 5.99, 32)), REFRIGERATED,
         "Sweet, ripe whole strawberries. Rinse just before eating.", "California", True),
    Crop("Blueberries", "berries", N("1 cup (148 g)", 80, 0.5, 0, 0, 21, 4, 15, 0, 1), (S("6OZ", "6 oz clamshell", 2.99, 6), S("18OZ", "18 oz clamshell", 6.49, 18)), REFRIGERATED,
         "Plump fresh blueberries for snacking, cereal, and baking.", "Chile", True),
    Crop("Raspberries", "berries", N("1 cup (123 g)", 60, 1, 0, 0, 15, 8, 5, 0, 1), (S("6OZ", "6 oz clamshell", 3.99, 6),), REFRIGERATED,
         "Delicate red raspberries, one of the highest-fiber, lowest-sugar fruits.", "Mexico", True),
    Crop("Blackberries", "berries", N("1 cup (144 g)", 60, 0.5, 0, 0, 14, 8, 7, 0, 2), (S("6OZ", "6 oz clamshell", 2.99, 6),), REFRIGERATED,
         "Juicy fresh blackberries, naturally high in fiber.", "Mexico"),
    Crop("Red Seedless Grapes", "grapes", GRAPE, (S("1LB", "1 lb", 2.49, 16), S("2LB", "About 2 lb bag", 4.99, 32)), REFRIGERATED,
         "Crunchy, sweet red seedless grapes.", "California", True),
    Crop("Green Seedless Grapes", "grapes", GRAPE, (S("1LB", "1 lb", 2.49, 16), S("2LB", "About 2 lb bag", 4.99, 32)), REFRIGERATED,
         "Crisp green seedless grapes with a bright, tangy flavor.", "California"),
    Crop("Navel Oranges", "citrus", N("1 medium orange (154 g)", 80, 0, 0, 0, 19, 3, 14, 0, 1), (S("EA", "Each", 1.09), S("4LB", "4 lb bag", 5.99, 64)), ROOM,
         "Seedless, easy-to-peel navel oranges.", "California", True),
    Crop("Clementines", "citrus", N("2 clementines (148 g)", 70, 0, 0, 0, 18, 2, 14, 0, 1), (S("3LB", "3 lb bag", 4.99, 48),), ROOM,
         "Small, seedless, easy-peel clementine mandarins.", "Spain"),
    Crop("Lemons", "citrus", N("1 medium lemon (58 g)", 15, 0, 0, 0, 5, 2, 1, 0, 0), (S("EA", "Each", 0.99), S("2LB", "2 lb bag", 3.99, 32)), ROOM,
         "Juicy lemons for cooking, baking, and drinks.", "California", True),
    Crop("Limes", "citrus", N("1 medium lime (67 g)", 20, 0, 0, 0, 7, 2, 1, 0, 0), (S("2LB", "2 lb bag", 2.99, 32),), ROOM,
         "Persian limes for guacamole, tacos, and drinks.", "Mexico"),
    Crop("Hass Avocados", "avocados", N("1/3 medium avocado (50 g)", 80, 8, 1, 0, 4, 3, 0, 0, 1), (S("EA", "Each", 1.29), S("4CT", "4 count bag", 4.99)), RIPEN,
         "Creamy Hass avocados; ready to eat when they yield to gentle pressure.", "Mexico", True),
    Crop("Yellow Peaches", "stone-fruit", PEACH, (S("1LB", "1 lb", 2.49, 16),), RIPEN,
         "Juicy yellow peaches. Ripen on the counter until fragrant.", "California"),
    Crop("Whole Pineapple", "pineapple", N("2 slices, 3 in diameter (112 g)", 50, 0, 0, 0, 13, 1, 10, 0, 1), (S("EA", "Each", 2.99),), ROOM,
         "A whole golden pineapple, sweet and ready to cut.", "Costa Rica", True),
    Crop("Mangoes", "mangoes", N("1 cup pieces (165 g)", 100, 0.5, 0, 0, 25, 3, 23, 0, 1), (S("EA", "Each", 1.29),), RIPEN,
         "Sweet, fragrant mangoes.", "Mexico"),
    Crop("Seedless Watermelon", "melons", WATERMELON, (S("EA", "Each, whole (about 15 lb)", 6.99),), ROOM,
         "A whole seedless watermelon.", "Mexico"),
    Crop("Cantaloupe", "melons", MELON, (S("EA", "Each", 2.99),), ROOM,
         "Sweet, orange-fleshed cantaloupe.", "California"),
    Crop("Bartlett Pears", "pears", N("1 medium pear (166 g)", 100, 0, 0, 0, 26, 6, 16, 0, 1), (S("1LB", "1 lb", 1.79, 16), S("3LB", "3 lb bag", 4.99, 48)), RIPEN,
         "Sweet, buttery Bartlett pears with 6 g fiber each.", "Oregon", True),
    Crop("Kiwifruit", "kiwi", N("2 medium kiwifruit (148 g)", 90, 1, 0, 0, 20, 4, 13, 0, 2), (S("1LB", "1 lb (about 5)", 2.49, 16),), REFRIGERATED,
         "Tangy green kiwifruit.", "New Zealand"),
    Crop("Dark Sweet Cherries", "cherries", N("1 cup (140 g)", 90, 0, 0, 0, 22, 3, 18, 0, 2), (S("1LB", "1 lb bag", 5.99, 16),), REFRIGERATED,
         "Dark red sweet cherries with pits.", "Washington"),
)  # fmt: skip

VEGETABLES: tuple[Crop, ...] = (
    Crop("Broccoli Crowns", "broccoli", N("1 medium stalk (148 g)", 45, 0.5, 0, 80, 8, 3, 2, 0, 4), (S("1LB", "1 lb", 1.99, 16),), REFRIGERATED,
         "Fresh broccoli crowns with the thick stems trimmed.", "California", True),
    Crop("Cauliflower", "cauliflower", N("1/6 medium head (99 g)", 25, 0, 0, 30, 5, 2, 2, 0, 2), (S("EA", "Each, whole head", 3.49),), REFRIGERATED,
         "A whole head of white cauliflower.", "California", True),
    Crop("Carrots", "carrots", N("1 medium carrot (78 g)", 30, 0, 0, 60, 7, 2, 5, 0, 1), (S("1LB", "1 lb bag", 1.29, 16), S("2LB", "2 lb bag", 1.99, 32)), REFRIGERATED,
         "Whole carrots, tops removed.", "California", True),
    Crop("Baby Carrots", "carrots", N("3 oz (85 g)", 35, 0, 0, 65, 8, 2, 5, 0, 1), (S("1LB", "1 lb bag", 1.49, 16), S("2LB", "2 lb bag", 2.69, 32)), REFRIGERATED,
         "Washed, peeled baby-cut carrots, ready to snack on.", "California"),
    Crop("Russet Potatoes", "potatoes", POTATO, (S("5LB", "5 lb bag", 3.99, 80), S("10LB", "10 lb bag", 6.49, 160)), COOL_DARK,
         "Starchy russet potatoes for baking, mashing, and fries.", "Idaho", True),
    Crop("Red Potatoes", "potatoes", POTATO, (S("3LB", "3 lb bag", 3.99, 48),), COOL_DARK,
         "Waxy red potatoes that hold their shape when roasted or boiled.", "Colorado"),
    Crop("Yukon Gold Potatoes", "potatoes", POTATO, (S("3LB", "3 lb bag", 4.29, 48), S("5LB", "5 lb bag", 5.99, 80)), COOL_DARK,
         "Buttery yellow-fleshed potatoes.", "Colorado", True),
    Crop("Sweet Potatoes", "sweet-potatoes", N("1 medium sweet potato (130 g)", 100, 0, 0, 70, 23, 4, 7, 0, 2), (S("1LB", "1 lb", 1.29, 16), S("3LB", "3 lb bag", 3.49, 48)), COOL_DARK,
         "Orange-fleshed sweet potatoes.", "North Carolina", True),
    Crop("Yellow Onions", "onions", ONION, (S("3LB", "3 lb bag", 2.99, 48),), COOL_DARK,
         "All-purpose yellow cooking onions.", "Idaho", True),
    Crop("Red Onions", "onions", ONION, (S("1LB", "1 lb", 1.49, 16),), COOL_DARK,
         "Mild red onions for salads, salsa, and grilling.", "Washington"),
    Crop("Garlic", "garlic", N("1 clove (3 g)", 5, 0, 0, 0, 1, 0, 0, 0, 0), (S("3CT", "3 bulbs", 1.99),), COOL_DARK,
         "Whole garlic bulbs.", "California", True),
    Crop("Tomatoes on the Vine", "tomatoes", TOMATO, (S("1LB", "1 lb", 2.49, 16),), ROOM,
         "Ripe red tomatoes still on the vine. Keep them out of the fridge for the best flavor.", "Mexico", True),
    Crop("Roma Tomatoes", "tomatoes", TOMATO, (S("1LB", "1 lb", 1.49, 16),), ROOM,
         "Meaty Roma plum tomatoes for sauces and salsa.", "Mexico"),
    Crop("Grape Tomatoes", "tomatoes", N("5 tomatoes (85 g)", 15, 0, 0, 5, 3, 1, 2, 0, 1), (S("10OZ", "10 oz clamshell", 2.99, 10),), ROOM,
         "Sweet, bite-size grape tomatoes.", "Mexico", True),
    Crop("Cucumbers", "cucumbers", N("1/3 medium cucumber (99 g)", 10, 0, 0, 0, 2, 1, 1, 0, 1), (S("EA", "Each", 0.99),), REFRIGERATED,
         "Crisp slicing cucumbers.", "Mexico", True),
    Crop("Green Bell Peppers", "peppers", PEPPER, (S("EA", "Each", 0.99),), REFRIGERATED,
         "Crunchy green bell peppers.", "Mexico"),
    Crop("Red Bell Peppers", "peppers", N("1 medium pepper (148 g)", 30, 0, 0, 5, 7, 2, 5, 0, 1), (S("EA", "Each", 1.49), S("3CT", "3 count bag", 4.49)), REFRIGERATED,
         "Sweet red bell peppers.", "Mexico", True),
    Crop("Zucchini", "squash", SQUASH, (S("1LB", "1 lb", 1.69, 16),), REFRIGERATED,
         "Green zucchini squash for grilling, roasting, and noodles.", "Mexico", True),
    Crop("Yellow Squash", "squash", SQUASH, (S("1LB", "1 lb", 1.69, 16),), REFRIGERATED,
         "Tender yellow summer squash.", "Mexico"),
    Crop("Romaine Hearts", "lettuce", N("1 1/2 cups shredded (85 g)", 15, 0, 0, 5, 3, 2, 1, 0, 1), (S("3CT", "3 hearts", 3.49),), REFRIGERATED,
         "Three crisp romaine lettuce hearts.", "Arizona", True),
    Crop("Iceberg Lettuce", "lettuce", N("1/6 medium head (89 g)", 10, 0, 0, 10, 3, 1, 2, 0, 1), (S("EA", "Each head", 1.79),), REFRIGERATED,
         "A crunchy head of iceberg lettuce.", "Arizona"),
    Crop("Celery", "celery", N("2 medium stalks (110 g)", 15, 0, 0, 115, 4, 2, 2, 0, 0), (S("EA", "Each bunch", 1.99),), REFRIGERATED,
         "A whole bunch of crisp celery.", "California", True),
    Crop("Curly Kale", "leafy-greens", N("2 cups chopped (42 g)", 20, 0.5, 0, 15, 4, 2, 1, 0, 1), (S("EA", "Each bunch", 1.99),), REFRIGERATED,
         "A bunch of curly green kale.", "California", True),
    Crop("White Mushrooms, Sliced", "mushrooms", MUSHROOM, (S("8OZ", "8 oz package", 2.29, 8),), REFRIGERATED,
         "Pre-sliced white button mushrooms.", "Pennsylvania", True),
    Crop("Baby Bella Mushrooms", "mushrooms", MUSHROOM, (S("8OZ", "8 oz package", 2.49, 8),), REFRIGERATED,
         "Whole baby bella (cremini) mushrooms with an earthy flavor.", "Pennsylvania"),
    Crop("Trimmed Green Beans", "green-beans", N("3/4 cup cut (83 g)", 20, 0, 0, 0, 5, 3, 2, 0, 1), (S("12OZ", "12 oz bag", 2.49, 12),), REFRIGERATED,
         "Washed and trimmed fresh green beans.", "Florida"),
    Crop("Asparagus", "asparagus", N("5 spears (93 g)", 20, 0, 0, 0, 4, 2, 2, 0, 2), (S("1LB", "1 lb bunch", 3.99, 16),), REFRIGERATED,
         "Green asparagus spears.", "Peru", True),
    Crop("Green Cabbage", "cabbage", N("1/12 medium head (84 g)", 20, 0, 0, 15, 5, 2, 3, 0, 1), (S("EA", "Each head", 1.99),), REFRIGERATED,
         "A firm head of green cabbage.", "Georgia"),
    Crop("Brussels Sprouts", "brussels-sprouts", N("1 cup (88 g)", 40, 0, 0, 20, 8, 3, 2, 0, 3), (S("12OZ", "12 oz bag", 3.49, 12),), REFRIGERATED,
         "Fresh Brussels sprouts for roasting.", "California"),
)  # fmt: skip

LOCAL: tuple[Crop, ...] = (
    Crop("Texas Rio Star Grapefruit", "citrus", GRAPEFRUIT, (S("EA", "Each", 1.29), S("5LB", "5 lb bag", 5.99, 80)), ROOM,
         "Deep red, sweet Rio Star grapefruit from the Rio Grande Valley.", "Texas", True),
    Crop("Hill Country Peaches", "stone-fruit", PEACH, (S("1LB", "1 lb", 3.49, 16), S("5LB", "Half peck (about 5 lb)", 13.99, 80)), RIPEN,
         "Seasonal tree-ripened peaches from Texas Hill Country orchards.", "Texas"),
    Crop("Texas 1015 Sweet Onions", "onions", N("1 medium onion (148 g)", 45, 0, 0, 5, 11, 2, 8, 0, 1), (S("1LB", "1 lb", 1.49, 16), S("3LB", "3 lb bag", 3.99, 48)), COOL_DARK,
         "Mild, sweet Texas 1015 onions, so mild you can eat them raw.", "Texas"),
    Crop("Texas Sweet Corn", "corn", N("1 medium ear (90 g)", 90, 1.5, 0, 15, 18, 2, 5, 0, 3), (S("4CT", "4 ears", 2.99),), REFRIGERATED,
         "Fresh bicolor sweet corn on the cob.", "Texas"),
    Crop("Texas Jalapeno Peppers", "peppers", N("1 pepper (14 g)", 5, 0, 0, 0, 1, 0, 1, 0, 0), (S("1LB", "1 lb", 1.49, 16),), REFRIGERATED,
         "Fresh green jalapeno peppers with medium heat.", "Texas"),
    Crop("Pecos Cantaloupe", "melons", MELON, (S("EA", "Each", 3.49),), ROOM,
         "Famously sweet cantaloupe grown around Pecos, Texas.", "Texas"),
    Crop("Texas Hothouse Tomatoes", "tomatoes", TOMATO, (S("1LB", "1 lb", 2.99, 16),), ROOM,
         "Greenhouse-grown red tomatoes from Texas.", "Texas"),
    Crop("Texas Seedless Watermelon", "melons", WATERMELON, (S("EA", "Each, whole (about 15 lb)", 5.99),), ROOM,
         "A whole seedless watermelon grown in Texas.", "Texas"),
)  # fmt: skip


def _ingredient(name: str, organic: bool) -> str:
    text = f"{'Organic ' if organic else ''}{name.split(',')[0]}"
    return text[0].upper() + text[1:].lower() + "."


def _crop(crop: Crop, brand: str, *, organic: bool, local: bool) -> ProductSeed:
    title = f"Organic {crop.name}" if organic else crop.name
    sizes = crop.sizes
    if organic:
        sizes = tuple(Size(s.code, s.label, cents(s.price_cents / 100 * 1.5), s.oz) for s in sizes)
    how = (
        "Certified organic, grown without synthetic pesticides or fertilizers."
        if organic
        else "Conventionally grown (not organic)."
    )
    where = " Grown in Texas." if local else ""
    return food(
        category=CAT, product_type=crop.ptype, brand=brand, title=title, sizes=sizes,
        nutrition=crop.facts, ingredients=_ingredient(crop.name, organic),
        tags=[*(["organic"] if organic else []), *(["local"] if local else [])],
        claims=CLAIMS,
        specs={"Growing method": "Organic" if organic else "Conventional", "Origin": crop.origin},
        intro=f"{crop.about} {how}{where}", storage=crop.storage,
    )  # fmt: skip


def crops() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    for crop in (*FRUIT, *VEGETABLES):
        out.append(_crop(crop, STORE_BRAND, organic=False, local=False))
        if crop.organic:
            out.append(_crop(crop, CEDAR, organic=True, local=False))
    for crop in LOCAL:
        out.append(_crop(crop, LONESTAR, organic=False, local=True))
        if crop.organic:
            out.append(_crop(crop, LONESTAR, organic=True, local=True))
    return out


def _packaged(
    brand: str,
    title: str,
    ptype: str,
    n: Nutrition,
    sizes: list[Size],
    ingredients: str,
    intro: str,
    *,
    allergens: tuple[str, ...] = (),
    tags: tuple[str, ...] = (),
    specs: dict[str, str] | None = None,
    claims: tuple[str, ...] = CLAIMS,
) -> ProductSeed:
    organic = title.startswith("Organic")
    return food(
        category=CAT, product_type=ptype, brand=brand, title=title, sizes=sizes, nutrition=n,
        ingredients=ingredients, allergens=allergens,
        tags=[*(["organic"] if organic else []), *tags], claims=claims,
        specs={"Growing method": "Organic" if organic else "Conventional", **(specs or {})},
        intro=intro, storage=REFRIGERATED,
    )  # fmt: skip


def salads() -> list[ProductSeed]:
    spinach = N("3 cups (85 g)", 20, 0, 0, 65, 3, 2, 0, 0, 2)
    spring = N("3 1/2 cups (85 g)", 20, 0, 0, 95, 3, 2, 1, 0, 2)
    kale = N("2 1/2 cups (85 g)", 25, 0, 0, 40, 4, 2, 1, 0, 2)
    romaine = N("1 1/2 cups (85 g)", 15, 0, 0, 5, 3, 2, 1, 0, 1)
    washed = "Washed and ready to eat."
    out = [
        _packaged(CEDAR, "Organic Baby Spinach", "salad-greens", spinach, [S("5OZ", "5 oz clamshell", 3.49, 5), S("16OZ", "1 lb clamshell", 6.99, 16)],
                  "Organic baby spinach.", f"Tender organic baby spinach leaves. {washed}"),
        _packaged(CEDAR, "Organic Spring Mix", "salad-greens", spring, [S("5OZ", "5 oz clamshell", 3.99, 5), S("16OZ", "1 lb clamshell", 6.99, 16)],
                  "Organic baby lettuces (red and green romaine, red and green oak leaf, lollo rosso), organic radicchio, organic frisee.",
                  f"A mix of organic baby lettuces and greens. {washed}"),
        _packaged(CEDAR, "Organic Baby Kale", "salad-greens", kale, [S("5OZ", "5 oz clamshell", 3.99, 5)],
                  "Organic baby kale.", f"Tender organic baby kale for salads and smoothies. {washed}"),
        _packaged(CEDAR, "Organic Power Greens", "salad-greens", kale, [S("5OZ", "5 oz clamshell", 3.99, 5)],
                  "Organic baby spinach, organic baby chard, organic baby kale.", f"Organic baby spinach, chard, and kale. {washed}"),
        _packaged(CEDAR, "Organic Baby Arugula", "salad-greens", N("2 cups (40 g)", 10, 0, 0, 10, 1, 1, 1, 0, 1), [S("5OZ", "5 oz clamshell", 3.99, 5)],
                  "Organic baby arugula.", f"Peppery organic baby arugula. {washed}"),
        _packaged(GREENMESA, "Chopped Romaine", "salad-greens", romaine, [S("9OZ", "9 oz bag", 2.99, 9)],
                  "Romaine lettuce.", f"Chopped romaine lettuce. {washed}"),
        _packaged(GREENMESA, "Classic Iceberg Salad", "salad-greens", N("1 1/2 cups (85 g)", 15, 0, 0, 10, 3, 1, 2, 0, 1), [S("12OZ", "12 oz bag", 1.99, 12)],
                  "Iceberg lettuce, carrots, red cabbage.", f"Iceberg lettuce with shredded carrots and red cabbage. {washed}"),
        _packaged(GREENMESA, "Spring Mix", "salad-greens", spring, [S("5OZ", "5 oz clamshell", 2.99, 5)],
                  "Baby lettuces (red and green romaine, red and green oak leaf, lollo rosso), radicchio, frisee.",
                  f"A conventional (not organic) mix of baby lettuces. {washed}"),
        _packaged(GREENMESA, "Shredded Coleslaw Mix", "salad-greens", N("1 1/2 cups (85 g)", 20, 0, 0, 15, 5, 2, 3, 0, 1), [S("14OZ", "14 oz bag", 1.99, 14)],
                  "Green cabbage, red cabbage, carrots.", "Shredded cabbage and carrots for coleslaw (dressing not included)."),
        _packaged(STORE_BRAND, "Baby Spinach", "salad-greens", spinach, [S("6OZ", "6 oz bag", 2.49, 6)],
                  "Baby spinach.", f"Conventionally grown baby spinach. {washed}"),
        _packaged(STORE_BRAND, "Italian Salad Blend", "salad-greens", romaine, [S("10OZ", "10 oz bag", 2.49, 10)],
                  "Romaine lettuce, radicchio.", f"Romaine and radicchio. {washed}"),
        # Salad kits: dressing and toppings included, so these are no longer just vegetables.
        _packaged(GREENMESA, "Caesar Salad Kit", "salad-kit", N("1 1/2 cups (85 g)", 170, 14, 2.5, 300, 7, 1, 2, 1, 4), [S("10OZ", "10.5 oz kit", 3.99, 10.5)],
                  "Romaine lettuce, Caesar dressing (soybean oil, water, parmesan cheese (milk), egg yolk, vinegar, anchovies, garlic, salt), "
                  "croutons (wheat flour, canola oil, salt, yeast), shredded parmesan cheese (milk).",
                  "Romaine with creamy Caesar dressing, croutons, and parmesan. The dressing contains anchovies and egg.",
                  allergens=("milk", "egg", "fish", "wheat"), claims=()),
        _packaged(GREENMESA, "Southwest Chopped Salad Kit", "salad-kit", N("1 1/2 cups (85 g)", 120, 9, 1.5, 230, 9, 2, 3, 2, 3), [S("10OZ", "10.5 oz kit", 3.99, 10.5)],
                  "Iceberg and romaine lettuce, cabbage, carrots, tortilla strips (corn, sunflower oil, salt), cheddar cheese (milk), "
                  "chipotle ranch dressing (soybean oil, buttermilk, egg yolk, cane sugar, chipotle peppers, salt).",
                  "Chopped greens with tortilla strips, cheddar, and chipotle ranch dressing.",
                  allergens=("milk", "egg"), tags=("gluten-free",), claims=()),
        _packaged(GREENMESA, "Asian Sesame Chopped Salad Kit", "salad-kit", N("1 1/2 cups (85 g)", 140, 9, 1, 270, 13, 2, 7, 6, 3), [S("12OZ", "12 oz kit", 3.99, 12)],
                  "Cabbage, carrots, green onions, wonton strips (wheat flour, soybean oil, salt), sliced almonds, sesame ginger dressing "
                  "(canola oil, rice vinegar, cane sugar, soy sauce (water, soybeans, wheat, salt), sesame oil, ginger).",
                  "Crunchy cabbage slaw with wonton strips, almonds, and sesame ginger dressing.",
                  allergens=("wheat", "soy", "sesame", "tree nuts"), claims=()),
        _packaged(GREENMESA, "Vegan Avocado Ranch Salad Kit", "salad-kit", N("1 1/2 cups (85 g)", 110, 9, 1, 190, 7, 2, 2, 1, 2), [S("10OZ", "10 oz kit", 4.29, 10)],
                  "Green leaf lettuce, kale, red cabbage, roasted pepitas, avocado ranch dressing (avocado oil, water, pea protein, "
                  "distilled vinegar, cane sugar, garlic, salt, dill).",
                  "Greens and pepitas with a creamy, egg-free and dairy-free avocado ranch dressing.",
                  tags=("vegan", "dairy-free", "plant-based", "gluten-free"), claims=()),
    ]  # fmt: skip
    return out


def herbs_and_cut() -> list[ProductSeed]:
    herb = N("1/4 cup (4 g)", 1, 0, 0, 2, 0, 0, 0, 0, 0)
    out = [
        _packaged(LONESTAR, "Texas Cilantro", "fresh-herbs", herb, [S("EA", "Each bunch", 0.99)], "Cilantro.",
                  "A fresh bunch of cilantro grown in Texas.", tags=("local",), claims=()),
        _packaged(STORE_BRAND, "Flat-Leaf Parsley", "fresh-herbs", herb, [S("EA", "Each bunch", 0.99)], "Italian flat-leaf parsley.",
                  "A fresh bunch of Italian flat-leaf parsley.", claims=()),
        _packaged(CEDAR, "Organic Basil", "fresh-herbs", herb, [S("75OZ", "0.75 oz clamshell", 2.49, 0.75)], "Organic basil.",
                  "Fragrant organic sweet basil. Store basil at cool room temperature, not in the fridge.", claims=()),
        _packaged(CEDAR, "Organic Mint", "fresh-herbs", herb, [S("75OZ", "0.75 oz clamshell", 2.49, 0.75)], "Organic spearmint.",
                  "Fresh organic spearmint.", claims=()),
        _packaged(STORE_BRAND, "Fresh Rosemary", "fresh-herbs", herb, [S("75OZ", "0.75 oz clamshell", 1.99, 0.75)], "Rosemary.",
                  "Fresh rosemary sprigs.", claims=()),
        _packaged(CEDAR, "Organic Thyme", "fresh-herbs", herb, [S("75OZ", "0.75 oz clamshell", 2.49, 0.75)], "Organic thyme.",
                  "Fresh organic thyme sprigs.", claims=()),
        # Cut fruit and vegetables
        _packaged(STORE_BRAND, "Fresh Cut Pineapple Chunks", "cut-fruit", N("1 cup (165 g)", 80, 0, 0, 0, 22, 2, 16, 0, 1), [S("16OZ", "16 oz container", 4.99, 16)],
                  "Pineapple.", "Freshly cut golden pineapple chunks with no added sugar."),
        _packaged(STORE_BRAND, "Fresh Cut Watermelon Chunks", "cut-fruit", N("1 cup diced (152 g)", 45, 0, 0, 0, 12, 1, 9, 0, 1), [S("32OZ", "32 oz container", 6.99, 32)],
                  "Watermelon.", "Seedless watermelon cut into bite-size chunks."),
        _packaged(STORE_BRAND, "Fresh Cut Fruit Medley", "cut-fruit", N("1 cup (150 g)", 70, 0, 0, 15, 18, 1, 15, 0, 1), [S("16OZ", "16 oz container", 5.49, 16)],
                  "Pineapple, cantaloupe, honeydew melon, red grapes.", "Pineapple, cantaloupe, honeydew, and grapes, cut and ready to eat."),
        _packaged(STORE_BRAND, "Fresh Cut Mango Chunks", "cut-fruit", N("1 cup pieces (165 g)", 100, 0.5, 0, 0, 25, 3, 23, 0, 1), [S("10OZ", "10 oz container", 3.99, 10)],
                  "Mango.", "Ripe mango chunks, cut fresh."),
        _packaged(STORE_BRAND, "Fresh Cut Berry Medley", "cut-fruit", N("1 cup (145 g)", 60, 0, 0, 0, 15, 3, 10, 0, 1), [S("10OZ", "10 oz container", 5.99, 10)],
                  "Strawberries, blueberries, blackberries.", "Strawberries, blueberries, and blackberries, washed and ready."),
        _packaged(STORE_BRAND, "Sliced Apples Snack Packs", "cut-fruit", N("1 bag (56 g)", 30, 0, 0, 0, 8, 1, 6, 0, 0), [S("6PK", "6 x 2 oz bags", 3.99, 12)],
                  "Apples, calcium ascorbate (to maintain freshness).", "Sliced apples in grab-and-go bags; treated with calcium ascorbate (vitamin C) to prevent browning."),
        _packaged(STORE_BRAND, "Veggie Tray with Ranch Dip", "vegetable-tray", N("3 oz vegetables with 2 tbsp dip (115 g)", 130, 11, 2, 250, 6, 2, 3, 1, 1), [S("28OZ", "28 oz tray", 9.99, 28)],
                  "Carrots, celery, broccoli, grape tomatoes, ranch dip (soybean oil, buttermilk, egg yolk, vinegar, salt, garlic, onion, spices).",
                  "Carrots, celery, broccoli, and grape tomatoes with a ranch dip cup in the center.",
                  allergens=("milk", "egg"), claims=()),
        _packaged(STORE_BRAND, "Butternut Squash Cubes", "cut-vegetables", N("1 cup (140 g)", 60, 0, 0, 5, 16, 3, 3, 0, 1), [S("16OZ", "16 oz container", 3.99, 16)],
                  "Butternut squash.", "Peeled, cubed butternut squash ready for roasting."),
        _packaged(STORE_BRAND, "Fresh Riced Cauliflower", "cut-vegetables", N("1 cup (85 g)", 20, 0, 0, 25, 4, 2, 2, 0, 2), [S("12OZ", "12 oz bag", 3.49, 12)],
                  "Cauliflower.", "Fresh cauliflower cut into rice-size pieces, a low-carb swap for rice."),
    ]  # fmt: skip
    return out


def products() -> list[ProductSeed]:
    return [*crops(), *salads(), *herbs_and_cut()]


__all__ = ["products"]
