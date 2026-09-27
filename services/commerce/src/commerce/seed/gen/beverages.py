"""Beverages: coffee, cold brew, tea, juice, soda, sparkling and still water, sports and
electrolyte drinks, kombucha, protein shakes, and energy drinks. No alcohol.

Every caffeinated drink states its caffeine in specs. Pairs to tell apart: regular vs decaf
coffee, herbal (caffeine-free) vs decaf tea, 100% juice vs juice cocktail, regular vs zero
sugar vs caffeine-free soda, unsweetened vs sweetened sparkling water, and regular vs zero
sugar sports and energy drinks.
"""

from __future__ import annotations

from commerce.seed.data import Nutrition, ProductSeed
from commerce.seed.gen.common import PANTRY, REFRIGERATED, STORE_BRAND, Size, cents, food

CAT = "beverages"
RIDGELINE = "Ridgeline Roasters"  # premium, organic, fair trade coffee
MESA = "Morning Mesa Coffee"  # mainstream coffee
STILLWATER = "Stillwater Tea Co."
PORCH = "Porch Swing Tea Co."  # bottled iced tea
BRIGHTGROVE = "Bright Grove Juice Co."
CEDAR = "Cedar Hollow Farms"  # organic
LONESTAR = "Lone Star Harvest"  # Texas grown
CRESTLINE = "Crestline Soda Co."
OLDPECAN = "Old Pecan Craft Soda Co."  # cane sugar craft soda
GLASSWATER = "Glasswater"  # sparkling water
PINECREST = "Pinecrest Springs"  # still water
PACER = "Pacer Sport"  # sports and electrolyte drinks
PALMGROVE = "Palmgrove"  # coconut water
BRIGHTCULTURE = "Bright Culture Kombucha"
IRONPEAK = "Ironpeak Nutrition"  # protein shakes
GREENSTRIDE = "Greenstride"  # plant-based shakes
VOLTLINE = "Voltline"  # energy drinks

AFTER_OPENING = "Store in a cool, dry place. Refrigerate after opening."
C8 = "8 fl oz (240 mL)"
CAN = "1 can (12 fl oz / 355 mL)"
DRINK_CLAIMS = ("sugar-free", "zero-calorie", "no-added-sugar", "low-sugar")
# Coffee beans, grounds, pods and tea bags: nobody shops them as "zero calorie" (the facts are
# for the brewed cup), so they carry no nutrition claims; ready-to-drink versions use DRINK_CLAIMS.
BREWED_CLAIMS: tuple[str, ...] = ()


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


def Z(serving: str, sodium: int = 0) -> Nutrition:
    """A zero-calorie drink."""
    return N(serving, 0, 0, 0, sodium, 0, 0, 0, 0, 0)


# (brand, title, type, facts, sizes, ingredients, allergens, tags, specs, intro)
Row = tuple[
    str, str, str, Nutrition, list[Size], str, tuple[str, ...], tuple[str, ...], dict[str, str], str
]


def _rows(rows: list[Row], claims: tuple[str, ...], storage: str = PANTRY) -> list[ProductSeed]:
    out = []
    for brand, title, ptype, n, sizes, ing, allergens, tags, specs, intro in rows:
        organic = title.startswith("Organic") or " Organic " in title
        out.append(food(
            category=CAT, product_type=ptype, brand=brand, title=title, sizes=sizes, nutrition=n,
            ingredients=ing, allergens=allergens, tags=[*(["organic"] if organic else []), *tags],
            claims=claims, specs=specs, intro=intro, storage=storage,
        ))  # fmt: skip
    return out


# --- Coffee and tea -----------------------------------------------------------------------------

BREWED = N("8 fl oz brewed (240 mL)", 2, 0, 0, 5, 0, 0, 0, 0, 0)
CAFF = "About 95 mg per 8 fl oz cup"
DECAF = "About 2-5 mg per 8 fl oz cup (at least 97% caffeine removed)"


def coffee() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    blends = [  # name, roast, origin, organic, fair trade, decaf, forms
        ("Organic Breakfast Blend", "Light", "Central and South America", True, True, False, ("Ground", "Whole Bean")),
        ("Organic French Roast", "Dark", "Central and South America", True, True, False, ("Ground", "Whole Bean")),
        ("Organic Decaf House Blend", "Medium", "Colombia and Peru", True, True, True, ("Ground", "Whole Bean")),
        ("Colombia Supremo", "Medium", "Colombia", False, True, False, ("Ground", "Whole Bean")),
        ("Ethiopia Yirgacheffe", "Light", "Ethiopia", False, True, False, ("Whole Bean",)),
        ("Espresso Roast", "Dark", "Brazil and Indonesia", False, False, False, ("Whole Bean",)),
        ("Guatemala Antigua", "Medium", "Guatemala", False, False, False, ("Whole Bean",)),
        ("Organic Decaf French Roast", "Dark", "Peru", True, True, True, ("Ground",)),
    ]  # fmt: skip
    for name, roast, origin, organic, fair, decaf, forms in blends:
        for form in forms:
            bean = f"{'Organic ' if organic else '100% '}{'decaffeinated ' if decaf else ''}arabica coffee{' (Swiss Water Process decaffeinated)' if decaf else ''}."
            out += _rows([(
                RIDGELINE, f"{name} {form} Coffee", "coffee", BREWED,
                [S("12OZ", "12 oz bag", 10.99, 12), S("2LB", "2 lb bag", 24.99, 32)] if form == "Whole Bean" else [S("12OZ", "12 oz bag", 10.99, 12)],
                bean[0].upper() + bean[1:], (),
                tuple(["kosher", *(["fair-trade"] if fair else []), *(["decaf"] if decaf else []), *(["non-gmo"] if organic else [])]),
                {"Roast": roast, "Form": form, "Origin": origin, "Caffeine": DECAF if decaf else CAFF,
                 **({"Decaf process": "Swiss Water Process (chemical free)"} if decaf else {})},
                f"{roast} roast {form.lower()} coffee from {origin}{', decaffeinated with the chemical-free Swiss Water Process' if decaf else ''}."
                f"{' Certified organic.' if organic else ''}{' Fair Trade Certified.' if fair else ''}",
            )], BREWED_CLAIMS)  # fmt: skip
    mesa_rows = [  # title, roast, form, decaf, flavored, sizes, caffeine, intro
        ("Original Medium Roast Ground Coffee", "Medium", "Ground", False, False, "can", CAFF, "Smooth, balanced medium roast ground coffee."),
        ("Dark Roast Ground Coffee", "Dark", "Ground", False, False, "can", CAFF, "Bold, rich dark roast ground coffee."),
        ("Decaf Medium Roast Ground Coffee", "Medium", "Ground", True, False, "can", DECAF, "Medium roast ground coffee, decaffeinated with ethyl acetate."),
        ("Half Caff Medium Roast Ground Coffee", "Medium", "Ground", False, False, "can", "About 45-50 mg per 8 fl oz cup",
         "A blend of regular and decaf beans with about half the caffeine. Not decaf."),
        ("Hazelnut Flavored Ground Coffee", "Medium", "Ground", False, True, "bag", CAFF, "Medium roast coffee with natural hazelnut flavor. No sugar; contains no nuts."),
        ("Breakfast Blend Single-Serve Coffee Pods", "Light", "Pods", False, False, "pods", CAFF, "Light roast breakfast blend in single-serve pods for pod brewers."),
        ("Dark Roast Single-Serve Coffee Pods", "Dark", "Pods", False, False, "pods", CAFF, "Dark roast single-serve pods."),
        ("Decaf Single-Serve Coffee Pods", "Medium", "Pods", True, False, "pods", DECAF, "Decaf medium roast single-serve pods."),
        ("French Vanilla Flavored Coffee Pods", "Light", "Pods", False, True, "pods", CAFF, "Light roast coffee pods with French vanilla flavor and no sugar."),
        ("Classic Roast Instant Coffee", "Medium", "Instant", False, False, "instant", "About 60 mg per 8 fl oz cup", "Instant coffee crystals; just add hot water."),
        ("Decaf Instant Coffee", "Medium", "Instant", True, False, "instant", "About 2 mg per 8 fl oz cup", "Decaffeinated instant coffee crystals."),
    ]  # fmt: skip
    size_sets = {
        "can": [
            S("11OZ", "11.3 oz canister", 6.99, 11.3),
            S("30OZ", "30.5 oz canister", 12.99, 30.5),
        ],
        "bag": [S("12OZ", "12 oz bag", 7.99, 12)],
        "pods": [S("12CT", "12 pods", 7.99, 4.4), S("24CT", "24 pods", 14.99, 8.8)],
        "instant": [S("8OZ", "8 oz jar", 8.99, 8)],
    }
    for title, roast, form, decaf, flavored, sizes, caffeine, intro in mesa_rows:
        n = (
            N("1 tsp (2 g) in 8 fl oz water", 5, 0, 0, 0, 1, 0, 0, 0, 0)
            if form == "Instant"
            else BREWED
        )
        ing = f"{'Decaffeinated ' if decaf else ''}{'instant coffee' if form == 'Instant' else 'arabica and robusta coffee'}{', natural and artificial flavors' if flavored else ''}."
        out += _rows([(
            MESA, title, "coffee", n, size_sets[sizes], ing[0].upper() + ing[1:], (), ("decaf",) if decaf else (),
            {"Roast": roast, "Form": form, "Caffeine": caffeine, **({"Flavor": title.split(" Flavored")[0]} if flavored else {})}, intro,
        )], BREWED_CLAIMS)  # fmt: skip
    rows: list[Row] = [
        (STORE_BRAND, "Medium Roast Ground Coffee", "coffee", BREWED, [S("30OZ", "30.5 oz canister", 9.99, 30.5)], "100% arabica coffee.", (), (),
         {"Roast": "Medium", "Form": "Ground", "Caffeine": CAFF}, "Everyday medium roast ground coffee."),
        (STORE_BRAND, "Colombian Ground Coffee", "coffee", BREWED, [S("24OZ", "24.2 oz canister", 9.99, 24.2)], "100% Colombian arabica coffee.", (), (),
         {"Roast": "Medium", "Form": "Ground", "Origin": "Colombia", "Caffeine": CAFF}, "Medium roast 100% Colombian coffee."),
        (STORE_BRAND, "Decaf Classic Roast Ground Coffee", "coffee", BREWED, [S("24OZ", "24.2 oz canister", 9.99, 24.2)], "Decaffeinated arabica coffee.", (), ("decaf",),
         {"Roast": "Medium", "Form": "Ground", "Caffeine": DECAF}, "Decaf medium roast ground coffee."),
        (STORE_BRAND, "French Roast Whole Bean Coffee", "coffee", BREWED, [S("32OZ", "2 lb bag", 14.99, 32)], "100% arabica coffee.", (), (),
         {"Roast": "Dark", "Form": "Whole Bean", "Caffeine": CAFF}, "Smoky dark French roast whole beans."),
        (STORE_BRAND, "Breakfast Blend Coffee Pods", "coffee", BREWED, [S("48CT", "48 pods", 19.99, 17.6)], "100% arabica coffee.", (), (),
         {"Roast": "Light", "Form": "Pods", "Caffeine": CAFF}, "Light roast single-serve pods, value size."),
        (STORE_BRAND, "Decaf Coffee Pods", "coffee", BREWED, [S("24CT", "24 pods", 11.99, 8.8)], "Decaffeinated arabica coffee.", (), ("decaf",),
         {"Roast": "Medium", "Form": "Pods", "Caffeine": DECAF}, "Decaf medium roast single-serve pods."),
        (STORE_BRAND, "Organic Fair Trade Medium Roast Ground Coffee", "coffee", BREWED, [S("12OZ", "12 oz bag", 7.99, 12)], "Organic arabica coffee.", (), ("fair-trade",),
         {"Roast": "Medium", "Form": "Ground", "Caffeine": CAFF}, "Organic, Fair Trade Certified medium roast coffee."),
        (STORE_BRAND, "Pecan Praline Flavored Ground Coffee", "coffee", BREWED, [S("12OZ", "12 oz bag", 6.99, 12)], "Arabica coffee, natural and artificial flavors.", (), (),
         {"Roast": "Medium", "Form": "Ground", "Caffeine": CAFF, "Flavor": "Pecan praline"}, "Medium roast coffee with Texas-style pecan praline flavor. Contains no nuts or sugar."),
        # Cold brew
        (RIDGELINE, "Unsweetened Black Cold Brew Coffee", "cold-brew", N(C8, 5, 0, 0, 15, 1, 0, 0, 0, 1), [S("48OZ", "48 fl oz carton", 5.99, 48)],
         "Cold brewed coffee (filtered water, arabica coffee).", (), ("unsweetened", "vegan", "dairy-free", "fair-trade"),
         {"Caffeine": "About 150 mg per 8 fl oz", "Sweetened": "No"}, "Smooth, slow-steeped black cold brew with nothing added. Ready to drink."),
        (RIDGELINE, "Unsweetened Cold Brew Concentrate", "cold-brew", N("2 fl oz concentrate (60 mL)", 5, 0, 0, 10, 1, 0, 0, 0, 0), [S("32OZ", "32 fl oz bottle", 9.99, 32)],
         "Cold brewed coffee concentrate (filtered water, arabica coffee).", (), ("unsweetened", "vegan", "dairy-free", "fair-trade"),
         {"Caffeine": "About 200 mg per 2 fl oz (dilute 1:1)", "Sweetened": "No"}, "Cold brew concentrate to mix 1:1 with water or milk."),
        (RIDGELINE, "Sweet Cream Cold Brew Coffee", "cold-brew", N("1 bottle (11 fl oz / 325 mL)", 130, 5, 3, 65, 17, 0, 16, 14, 3), [S("11OZ", "11 fl oz bottle", 3.49, 11), S("4PK", "4 x 11 fl oz bottles", 11.99, 44)],
         "Cold brewed coffee, cream, milk, cane sugar, natural vanilla flavor.", ("milk",), ("gluten-free",),
         {"Caffeine": "About 180 mg per bottle", "Sweetened": "Yes, cane sugar"}, "Cold brew with sweet vanilla cream. Contains milk and 14 g added sugar."),
        (RIDGELINE, "Oat Milk Latte Cold Brew", "cold-brew", N("1 can (11 fl oz / 325 mL)", 120, 5, 0.5, 110, 17, 1, 11, 9, 2), [S("4PK", "4 x 11 fl oz cans", 11.99, 44)],
         "Cold brewed coffee, oatmilk (water, oats), cane sugar, sunflower oil, sea salt, gellan gum.", (), ("vegan", "dairy-free", "plant-based"),
         {"Caffeine": "About 150 mg per can", "Sweetened": "Yes, cane sugar"}, "Dairy-free cold brew latte made with oat milk. Lightly sweetened."),
        (MESA, "Vanilla Cold Brew Coffee, Lightly Sweetened", "cold-brew", N(C8, 50, 0, 0, 15, 12, 0, 12, 12, 0), [S("48OZ", "48 fl oz carton", 4.99, 48)],
         "Cold brewed coffee, cane sugar, natural vanilla flavor.", (), ("vegan", "dairy-free"), {"Caffeine": "About 130 mg per 8 fl oz", "Sweetened": "Yes"},
         "Black cold brew with a touch of vanilla and cane sugar."),
        (STORE_BRAND, "Black Cold Brew Coffee, Unsweetened", "cold-brew", N(C8, 5, 0, 0, 15, 1, 0, 0, 0, 1), [S("48OZ", "48 fl oz carton", 3.99, 48)],
         "Cold brewed coffee (water, coffee).", (), ("unsweetened", "vegan", "dairy-free"), {"Caffeine": "About 150 mg per 8 fl oz", "Sweetened": "No"},
         "Unsweetened black cold brew."),
    ]  # fmt: skip
    out += _rows(rows[:8], BREWED_CLAIMS)
    out += _rows(rows[8:], DRINK_CLAIMS, REFRIGERATED)
    return out


def tea() -> list[ProductSeed]:
    bag = Z("1 tea bag, brewed (240 mL)")
    box20 = [S("20CT", "20 tea bags", 4.49)]
    black = "About 40-50 mg per cup"
    green = "About 25-35 mg per cup"
    none = "Caffeine free"
    decaf = "About 2-5 mg per cup"
    rows: list[Row] = [
        (STILLWATER, "English Breakfast Black Tea", "tea", bag, box20, "Black tea.", (), ("kosher",), {"Tea type": "Black", "Caffeine": black}, "Robust English breakfast black tea."),
        (STILLWATER, "Earl Grey Black Tea", "tea", bag, box20, "Black tea, natural bergamot flavor.", (), ("kosher",), {"Tea type": "Black", "Caffeine": black},
         "Black tea scented with bergamot orange."),
        (STILLWATER, "Organic Green Tea", "tea", bag, box20, "Organic green tea.", (), ("kosher",), {"Tea type": "Green", "Caffeine": green}, "Smooth organic green tea."),
        (STILLWATER, "Jasmine Green Tea", "tea", bag, box20, "Green tea, jasmine flowers.", (), ("kosher",), {"Tea type": "Green", "Caffeine": green}, "Green tea scented with jasmine."),
        (STILLWATER, "Decaf English Breakfast Tea", "tea", bag, box20, "Decaffeinated black tea.", (), ("kosher", "decaf"), {"Tea type": "Black (decaf)", "Caffeine": decaf},
         "Decaffeinated black tea. Decaf still contains a trace of caffeine; choose an herbal tea for caffeine free."),
        (STILLWATER, "Decaf Green Tea", "tea", bag, box20, "Decaffeinated green tea.", (), ("kosher", "decaf"), {"Tea type": "Green (decaf)", "Caffeine": decaf},
         "Decaffeinated green tea with a trace of caffeine."),
        (STILLWATER, "Chamomile Herbal Tea", "tea", bag, box20, "Chamomile flowers.", (), ("kosher", "caffeine-free"), {"Tea type": "Herbal", "Caffeine": none},
         "Naturally caffeine-free chamomile tea for evenings."),
        (STILLWATER, "Peppermint Herbal Tea", "tea", bag, box20, "Peppermint leaves.", (), ("kosher", "caffeine-free"), {"Tea type": "Herbal", "Caffeine": none},
         "Naturally caffeine-free peppermint tea."),
        (STILLWATER, "Organic Rooibos Herbal Tea", "tea", bag, box20, "Organic rooibos.", (), ("kosher", "caffeine-free"), {"Tea type": "Herbal", "Caffeine": none},
         "Naturally caffeine-free organic South African red rooibos."),
        (STILLWATER, "Hibiscus Berry Herbal Tea", "tea", bag, box20, "Hibiscus, rose hips, blackberry leaves, natural berry flavor.", (), ("kosher", "caffeine-free"),
         {"Tea type": "Herbal", "Caffeine": none}, "Tart, caffeine-free hibiscus and berry tea. Great iced."),
        (STILLWATER, "Organic Chai Black Tea", "tea", bag, box20, "Organic black tea, organic cinnamon, organic ginger, organic cardamom, organic cloves, organic black pepper.",
         (), ("kosher",), {"Tea type": "Black (spiced)", "Caffeine": black}, "Spiced organic chai black tea."),
        (STILLWATER, "Ginger Turmeric Herbal Tea", "tea", bag, box20, "Ginger, turmeric, lemongrass, black pepper.", (), ("kosher", "caffeine-free"),
         {"Tea type": "Herbal", "Caffeine": none}, "Warming, caffeine-free ginger turmeric tea."),
        (STILLWATER, "Ceremonial Matcha Green Tea Powder", "tea", N("1 tsp (2 g)", 5, 0, 0, 0, 1, 1, 0, 0, 0), [S("1OZ", "1 oz tin", 14.99, 1)],
         "Stone-ground green tea (matcha).", (), ("kosher", "unsweetened"), {"Tea type": "Green (matcha)", "Caffeine": "About 70 mg per teaspoon"},
         "Vibrant stone-ground Japanese matcha. Unsweetened."),
        (STORE_BRAND, "Black Tea Bags", "tea", bag, [S("100CT", "100 tea bags", 3.49)], "Black tea.", (), (), {"Tea type": "Black", "Caffeine": black}, "Everyday black tea bags."),
        (STORE_BRAND, "Decaf Black Tea Bags", "tea", bag, [S("100CT", "100 tea bags", 4.49)], "Decaffeinated black tea.", (), ("decaf",), {"Tea type": "Black (decaf)", "Caffeine": decaf},
         "Decaffeinated black tea bags."),
        (STORE_BRAND, "Family-Size Iced Tea Bags", "tea", Z("8 fl oz brewed (240 mL)"), [S("24CT", "24 family-size bags", 3.49)], "Black tea.", (), (),
         {"Tea type": "Black", "Caffeine": "About 30 mg per 8 fl oz"}, "Family-size black tea bags; each brews a quart of iced tea."),
        (STORE_BRAND, "Green Tea Bags", "tea", bag, [S("40CT", "40 tea bags", 2.99)], "Green tea.", (), (), {"Tea type": "Green", "Caffeine": green}, "Everyday green tea bags."),
    ]  # fmt: skip
    out = _rows(rows, BREWED_CLAIMS)
    rows = [
        (PORCH, "Southern Sweet Tea", "iced-tea", N(C8, 90, 0, 0, 15, 23, 0, 22, 22, 0), [S("GAL", "1 gallon jug", 3.49, 128), S("59OZ", "59 fl oz bottle", 2.99, 59)],
         "Brewed black tea (filtered water, black tea), cane sugar, citric acid.", (), ("vegan", "gluten-free"), {"Caffeine": "About 20 mg per 8 fl oz", "Sweetened": "Yes, cane sugar"},
         "Classic Southern-style sweet tea brewed fresh and sweetened with cane sugar. 22 g added sugar per cup."),
        (PORCH, "Unsweetened Black Iced Tea", "iced-tea", Z(C8, 15), [S("GAL", "1 gallon jug", 3.49, 128), S("59OZ", "59 fl oz bottle", 2.99, 59)],
         "Brewed black tea (filtered water, black tea), citric acid.", (), ("vegan", "gluten-free", "unsweetened"), {"Caffeine": "About 20 mg per 8 fl oz", "Sweetened": "No"},
         "Fresh-brewed black iced tea with no sugar or sweeteners."),
        (PORCH, "Zero Sugar Sweet Tea", "iced-tea", Z(C8, 15), [S("59OZ", "59 fl oz bottle", 3.29, 59)],
         "Brewed black tea (filtered water, black tea), erythritol, citric acid, stevia leaf extract.", (), ("vegan", "gluten-free"),
         {"Caffeine": "About 20 mg per 8 fl oz", "Sweetened": "Yes, stevia and erythritol"}, "Sweet tea taste with zero sugar and zero calories, sweetened with stevia."),
        (PORCH, "Half & Half Lemonade Iced Tea", "iced-tea", N(C8, 90, 0, 0, 15, 23, 0, 22, 22, 0), [S("59OZ", "59 fl oz bottle", 2.99, 59)],
         "Brewed black tea, water, cane sugar, lemon juice concentrate, citric acid.", (), ("vegan", "gluten-free"), {"Caffeine": "About 15 mg per 8 fl oz", "Sweetened": "Yes"},
         "Half sweet tea, half lemonade."),
        (STILLWATER, "Unsweetened Green Iced Tea", "iced-tea", Z("1 bottle (16.9 fl oz / 500 mL)", 20), [S("EA", "16.9 fl oz bottle", 1.99, 16.9), S("12PK", "12 x 16.9 fl oz bottles", 17.99, 202.8)],
         "Brewed green tea (filtered water, green tea), ascorbic acid.", (), ("vegan", "gluten-free", "unsweetened"), {"Caffeine": "About 50 mg per bottle", "Sweetened": "No"},
         "Bottled unsweetened green tea with zero calories."),
        (STILLWATER, "Green Tea with Honey", "iced-tea", N("1 bottle (16.9 fl oz / 500 mL)", 140, 0, 0, 20, 35, 0, 34, 34, 0), [S("EA", "16.9 fl oz bottle", 1.99, 16.9)],
         "Brewed green tea, cane sugar, honey, citric acid, ascorbic acid.", (), ("gluten-free",), {"Caffeine": "About 50 mg per bottle", "Sweetened": "Yes, cane sugar and honey"},
         "Bottled green tea sweetened with cane sugar and honey. 34 g added sugar per bottle."),
    ]  # fmt: skip
    out += _rows(rows, DRINK_CLAIMS, REFRIGERATED)
    return out


# --- Juice ------------------------------------------------------------------------------------


def juice() -> list[ProductSeed]:
    oj = N(C8, 110, 0, 0, 0, 26, 0, 22, 0, 2)
    apple = N(C8, 110, 0, 0, 10, 28, 0, 26, 0, 0)
    carton = [S("52OZ", "52 fl oz carton", 4.49, 52), S("89OZ", "89 fl oz carton", 6.99, 89)]
    bottle = [S("64OZ", "64 fl oz bottle", 3.49, 64)]
    NFC = "Not from concentrate"
    FC = "From concentrate"
    J100 = ("vegan", "gluten-free", "unsweetened")
    J = ("vegan", "gluten-free")
    chilled: list[Row] = [
        (BRIGHTGROVE, "100% Orange Juice, No Pulp", "juice", oj, carton, "100% pure squeezed orange juice.", (), J100,
         {"Juice content": "100% juice", "Concentrate": NFC, "Pulp": "No pulp"}, "100% orange juice, not from concentrate, with no sugar added."),
        (BRIGHTGROVE, "100% Orange Juice, Some Pulp", "juice", oj, carton, "100% pure squeezed orange juice.", (), J100,
         {"Juice content": "100% juice", "Concentrate": NFC, "Pulp": "Some pulp"}, "100% orange juice with some pulp, not from concentrate."),
        (BRIGHTGROVE, "100% Orange Juice with Calcium & Vitamin D", "juice", oj, carton, "100% pure squeezed orange juice, tricalcium phosphate, calcium lactate, vitamin D3.", (), J100,
         {"Juice content": "100% juice", "Concentrate": NFC, "Pulp": "No pulp"}, "Not-from-concentrate orange juice fortified with calcium and vitamin D."),
        (BRIGHTGROVE, "Light Orange Juice Beverage", "juice", N(C8, 50, 0, 0, 10, 12, 0, 10, 0, 1), [S("52OZ", "52 fl oz carton", 4.49, 52)],
         "Filtered water, orange juice, citric acid, natural flavors, stevia leaf extract.", (), J, {"Juice content": "42% juice", "Concentrate": NFC},
         "Orange juice beverage with half the sugar and calories of 100% juice, sweetened with stevia. Not 100% juice."),
        (CEDAR, "Organic 100% Orange Juice, No Pulp", "juice", oj, [S("52OZ", "52 fl oz carton", 5.99, 52)], "100% organic orange juice.", (), (*J100, "non-gmo"),
         {"Juice content": "100% juice", "Concentrate": NFC, "Pulp": "No pulp"}, "Organic not-from-concentrate orange juice."),
        (STORE_BRAND, "100% Orange Juice from Concentrate", "juice", oj, [S("52OZ", "52 fl oz carton", 2.99, 52), S("GAL", "1 gallon jug", 5.49, 128)],
         "Orange juice from concentrate (filtered water, orange juice concentrate).", (), J100, {"Juice content": "100% juice", "Concentrate": FC, "Pulp": "No pulp"},
         "100% orange juice made from concentrate, no sugar added."),
        (STORE_BRAND, "Orange Drink", "juice", N(C8, 120, 0, 0, 40, 30, 0, 29, 27, 0), [S("GAL", "1 gallon jug", 2.99, 128)],
         "Water, high fructose corn syrup, orange juice concentrate, citric acid, natural flavors, yellow 6.", (), J, {"Juice content": "10% juice"},
         "Orange-flavored drink with 10% juice and 27 g added sugar. Not orange juice."),
        (LONESTAR, "Texas Rio Star Grapefruit Juice", "juice", N(C8, 90, 0, 0, 0, 22, 0, 18, 0, 1), [S("52OZ", "52 fl oz bottle", 5.49, 52)],
         "100% Rio Star grapefruit juice.", (), (*J100, "local"), {"Juice content": "100% juice", "Concentrate": NFC},
         "Sweet-tart 100% juice pressed from Texas Rio Star grapefruit. Grapefruit interacts with some medications."),
    ]  # fmt: skip
    shelf: list[Row] = [
        (BRIGHTGROVE, "100% Apple Juice", "juice", apple, bottle, "Apple juice from concentrate (filtered water, apple juice concentrate), ascorbic acid.", (), J100,
         {"Juice content": "100% juice", "Concentrate": FC}, "100% apple juice with no sugar added."),
        (CEDAR, "Organic 100% Apple Juice", "juice", apple, bottle, "Organic apple juice.", (), (*J100, "non-gmo"), {"Juice content": "100% juice", "Concentrate": NFC},
         "Organic 100% apple juice, not from concentrate."),
        (STORE_BRAND, "100% Apple Juice", "juice", apple, [S("64OZ", "64 fl oz bottle", 2.49, 64)], "Apple juice from concentrate (filtered water, apple juice concentrate), ascorbic acid.",
         (), J100, {"Juice content": "100% juice", "Concentrate": FC}, "100% apple juice."),
        (STORE_BRAND, "100% Apple Juice Boxes", "juice", N("1 box (6.75 fl oz / 200 mL)", 90, 0, 0, 10, 23, 0, 21, 0, 0), [S("8PK", "8 x 6.75 fl oz boxes", 3.49, 54)],
         "Apple juice from concentrate (filtered water, apple juice concentrate), ascorbic acid.", (), (*J100, "kids"), {"Juice content": "100% juice", "Concentrate": FC},
         "Lunchbox-size 100% apple juice boxes."),
        (BRIGHTGROVE, "Cranberry Juice Cocktail", "juice", N(C8, 110, 0, 0, 5, 28, 0, 26, 22, 0), bottle,
         "Filtered water, cranberry juice concentrate, sugar, fruit and vegetable juice (color), ascorbic acid.", (), J, {"Juice content": "27% juice", "Concentrate": FC},
         "Tart cranberry juice cocktail sweetened with sugar: 22 g added sugar per cup. Not 100% juice."),
        (BRIGHTGROVE, "Light Cranberry Juice Cocktail", "juice", N(C8, 50, 0, 0, 10, 12, 0, 11, 3, 0), bottle,
         "Filtered water, cranberry juice concentrate, sugar, citric acid, sucralose, acesulfame potassium.", (), J, {"Juice content": "27% juice", "Concentrate": FC},
         "Cranberry juice cocktail with half the calories, partly sweetened with sucralose."),
        (BRIGHTGROVE, "100% Cranberry Juice Blend, No Sugar Added", "juice", N(C8, 120, 0, 0, 15, 30, 0, 28, 0, 0), bottle,
         "Filtered water, cranberry juice concentrate, grape juice concentrate, apple juice concentrate, ascorbic acid.", (), J,
         {"Juice content": "100% juice", "Concentrate": FC}, "A 100% juice blend of cranberry, grape, and apple with no sugar added. Still 28 g natural sugar."),
        (BRIGHTGROVE, "Unsweetened 100% Pure Cranberry Juice", "juice", N(C8, 50, 0, 0, 5, 12, 0, 9, 0, 0), [S("32OZ", "32 fl oz bottle", 5.99, 32)],
         "Cranberry juice from concentrate (filtered water, cranberry juice concentrate).", (), J100, {"Juice content": "100% juice", "Concentrate": FC},
         "Very tart 100% pure cranberry juice with nothing added. Dilute to taste."),
        (BRIGHTGROVE, "100% Concord Grape Juice", "juice", N(C8, 150, 0, 0, 10, 37, 0, 36, 0, 1), bottle,
         "Grape juice from concentrate (filtered water, Concord grape juice concentrate), ascorbic acid.", (), J100, {"Juice content": "100% juice", "Concentrate": FC},
         "100% Concord grape juice with no sugar added."),
        (BRIGHTGROVE, "Classic Lemonade", "juice", N(C8, 110, 0, 0, 15, 29, 0, 28, 27, 0), [S("59OZ", "59 fl oz bottle", 3.29, 59)],
         "Filtered water, cane sugar, lemon juice concentrate, natural flavors.", (), J, {"Juice content": "10% juice"}, "Old-fashioned lemonade sweetened with cane sugar."),
        (BRIGHTGROVE, "Zero Sugar Lemonade", "juice", N(C8, 5, 0, 0, 15, 2, 0, 0, 0, 0), [S("59OZ", "59 fl oz bottle", 3.29, 59)],
         "Filtered water, lemon juice concentrate, citric acid, natural flavors, sucralose.", (), J, {"Juice content": "5% juice"}, "Lemonade with zero sugar, sweetened with sucralose."),
        (BRIGHTGROVE, "Fruit Punch Juice Drink", "juice", N(C8, 120, 0, 0, 25, 31, 0, 30, 29, 0), bottle,
         "Water, high fructose corn syrup, pear and grape juice concentrates, citric acid, natural flavors, red 40.", (), (*J, "kids"), {"Juice content": "5% juice"},
         "Fruit punch drink with 5% juice and 29 g added sugar."),
        (BRIGHTGROVE, "Original Vegetable Juice", "juice", N(C8, 50, 0, 0, 640, 10, 2, 7, 0, 2), [S("46OZ", "46 fl oz bottle", 3.99, 46)],
         "Vegetable juices from concentrate (tomatoes, carrots, celery, beets, parsley, lettuce, watercress, spinach), salt, ascorbic acid.", (), J100,
         {"Juice content": "100% vegetable juice", "Concentrate": FC}, "100% vegetable juice blend. High in sodium: 640 mg per cup."),
        (BRIGHTGROVE, "Low Sodium Vegetable Juice", "juice", N(C8, 50, 0, 0, 140, 10, 2, 7, 0, 2), [S("46OZ", "46 fl oz bottle", 3.99, 46)],
         "Vegetable juices from concentrate (tomatoes, carrots, celery, beets, parsley, lettuce, watercress, spinach), potassium chloride, ascorbic acid.", (), J100,
         {"Juice content": "100% vegetable juice", "Concentrate": FC}, "Low sodium vegetable juice with 140 mg sodium per cup, 78% less than our original."),
    ]  # fmt: skip
    claims = (*DRINK_CLAIMS, "low-sodium")
    return _rows(chilled, claims, REFRIGERATED) + _rows(shelf, claims, AFTER_OPENING)


# --- Soda and water -------------------------------------------------------------------------------

SUGARY = "Carbonated water, high fructose corn syrup"
DIET = "Carbonated water"


def soda() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    # title, facts, sweetener, flavor ingredients, caffeine mg
    crest = [
        ("Cola", N(CAN, 140, 0, 0, 45, 39, 0, 39, 39, 0), "sugar", "caramel color, phosphoric acid, natural flavors", 34),
        ("Zero Sugar Cola", Z(CAN, 40), "zero", "caramel color, phosphoric acid, natural flavors", 34),
        ("Diet Cola", Z(CAN, 40), "diet", "caramel color, phosphoric acid, natural flavors", 46),
        ("Caffeine-Free Cola", N(CAN, 140, 0, 0, 45, 39, 0, 39, 39, 0), "sugar", "caramel color, phosphoric acid, natural flavors", 0),
        ("Caffeine-Free Diet Cola", Z(CAN, 40), "diet", "caramel color, phosphoric acid, natural flavors", 0),
        ("Cherry Cola", N(CAN, 150, 0, 0, 35, 42, 0, 42, 42, 0), "sugar", "caramel color, phosphoric acid, natural cherry flavor", 34),
        ("Lemon-Lime Soda", N(CAN, 140, 0, 0, 65, 38, 0, 38, 38, 0), "sugar", "citric acid, natural lemon and lime flavors, sodium citrate", 0),
        ("Zero Sugar Lemon-Lime Soda", Z(CAN, 65), "zero", "citric acid, natural lemon and lime flavors, sodium citrate", 0),
        ("Root Beer", N(CAN, 160, 0, 0, 55, 44, 0, 44, 44, 0), "sugar", "caramel color, sodium benzoate, natural and artificial flavors, quillaia extract", 0),
        ("Diet Root Beer", Z(CAN, 55), "diet", "caramel color, sodium benzoate, natural and artificial flavors, quillaia extract", 0),
        ("Ginger Ale", N(CAN, 120, 0, 0, 35, 33, 0, 33, 33, 0), "sugar", "citric acid, natural ginger flavor, sodium benzoate", 0),
        ("Zero Sugar Ginger Ale", Z(CAN, 35), "zero", "citric acid, natural ginger flavor, sodium benzoate", 0),
        ("Orange Soda", N(CAN, 160, 0, 0, 55, 44, 0, 44, 44, 0), "sugar", "citric acid, natural flavors, sodium benzoate, yellow 6, red 40", 0),
        ("Spiced Cherry Pepper Soda", N(CAN, 150, 0, 0, 55, 40, 0, 40, 40, 0), "sugar", "caramel color, phosphoric acid, natural and artificial flavors", 41),
        ("Zero Sugar Spiced Cherry Pepper Soda", Z(CAN, 55), "zero", "caramel color, phosphoric acid, natural and artificial flavors", 41),
        ("Citrus Mountain Soda", N(CAN, 170, 0, 0, 60, 46, 0, 46, 46, 0), "sugar", "concentrated orange juice, citric acid, natural flavors, sodium benzoate, yellow 5", 54),
    ]  # fmt: skip
    sweeteners = {
        "sugar": SUGARY,
        "zero": f"{DIET}, aspartame, acesulfame potassium",
        "diet": f"{DIET}, aspartame",
    }
    for title, n, sweet, flav, mg in crest:
        caffeine = ", caffeine" if mg else ""
        ing = f"{sweeteners[sweet]}, {flav}{caffeine}."
        if sweet != "sugar":
            ing += " Phenylketonurics: contains phenylalanine."
        tags = ["vegan", "gluten-free", *(["caffeine-free"] if not mg else [])]
        out += _rows([(
            CRESTLINE, title, "soda", n, [S("12PK", "12 x 12 fl oz cans", 7.99, 144), S("2L", "2 liter bottle", 2.79, 67.6)], ing, (), tuple(tags),
            {"Caffeine": f"{mg} mg per 12 fl oz can" if mg else "Caffeine free", "Sweetener": {"sugar": "High fructose corn syrup", "zero": "Aspartame, acesulfame K", "diet": "Aspartame"}[sweet]},
            f"{title} in cans and bottles. "
            + ("Zero sugar and zero calories, sweetened with aspartame." if sweet != "sugar" else f"Regular soda with {n.added_sugars_g:g} g added sugar per can.")
            + ("" if mg else " Caffeine free."),
        )], DRINK_CLAIMS)  # fmt: skip
    craft = [
        ("Cane Sugar Root Beer", "sassafras bark extract, vanilla, wintergreen, caramel color"),
        ("Cane Sugar Cream Soda", "natural vanilla flavor"),
        (
            "Cane Sugar Black Cherry Soda",
            "natural black cherry flavor, citric acid, fruit and vegetable juice (color)",
        ),
    ]
    for title, flav in craft:
        out += _rows([(
            OLDPECAN, title, "soda", N("1 bottle (12 fl oz / 355 mL)", 170, 0, 0, 40, 45, 0, 45, 45, 0), [S("4PK", "4 x 12 fl oz glass bottles", 5.99, 48)],
            f"Carbonated water, cane sugar, {flav}.", (), ("vegan", "gluten-free", "caffeine-free"), {"Caffeine": "Caffeine free", "Sweetener": "Cane sugar"},
            "Small-batch craft soda made with pure cane sugar in glass bottles. Caffeine free; 45 g added sugar per bottle.",
        )], DRINK_CLAIMS)  # fmt: skip
    store = [
        ("Cola", N(CAN, 140, 0, 0, 45, 39, 0, 39, 39, 0), SUGARY, "caramel color, phosphoric acid, natural flavors, caffeine", 34),
        ("Diet Cola", Z(CAN, 40), f"{DIET}, aspartame", "caramel color, phosphoric acid, natural flavors, caffeine", 46),
        ("Lemon-Lime Soda", N(CAN, 140, 0, 0, 65, 38, 0, 38, 38, 0), SUGARY, "citric acid, natural flavors, sodium citrate", 0),
        ("Ginger Ale", N(CAN, 120, 0, 0, 35, 33, 0, 33, 33, 0), SUGARY, "citric acid, natural ginger flavor", 0),
    ]  # fmt: skip
    for title, n, sweet, flav, mg in store:
        out += _rows([(
            STORE_BRAND, title, "soda", n, [S("12PK", "12 x 12 fl oz cans", 4.99, 144), S("2L", "2 liter bottle", 1.49, 67.6)], f"{sweet}, {flav}.", (),
            ("vegan", "gluten-free", *(["caffeine-free"] if not mg else [])), {"Caffeine": f"{mg} mg per 12 fl oz can" if mg else "Caffeine free"},
            f"Larkspur Kitchen {title.lower()}." + ("" if mg else " Caffeine free."),
        )], DRINK_CLAIMS)  # fmt: skip
    return out


def water() -> list[ProductSeed]:
    can8 = [S("8PK", "8 x 12 fl oz cans", 4.99, 96)]
    flavors = [
        "Original",
        "Lime",
        "Lemon",
        "Grapefruit",
        "Black Cherry",
        "Watermelon",
        "Mango",
        "Raspberry Lime",
    ]
    rows: list[Row] = []
    for flavor in flavors:
        flav = "" if flavor == "Original" else f", natural {flavor.lower()} flavor"
        rows.append((
            GLASSWATER, f"{flavor} Sparkling Water", "sparkling-water", Z(CAN), can8, f"Carbonated water{flav}.", (),
            ("unsweetened", "vegan", "gluten-free", "caffeine-free"), {"Flavor": "Unflavored" if flavor == "Original" else flavor, "Sweetened": "No"},
            ("Unflavored sparkling water" if flavor == "Original" else f"Sparkling water with a hint of {flavor.lower()}")
            + ": zero calories, zero sugar, and no sweeteners.",
        ))  # fmt: skip
    rows += [
        (GLASSWATER, "Sweetened Black Cherry Sparkling Water", "sparkling-water", Z("1 bottle (17 fl oz / 503 mL)", 10), [S("EA", "17 fl oz bottle", 1.29, 17), S("12PK", "12 x 17 fl oz bottles", 12.99, 204)],
         "Carbonated water, natural flavor, citric acid, sucralose, potassium benzoate.", (), ("vegan", "gluten-free", "caffeine-free"),
         {"Flavor": "Black cherry", "Sweetened": "Yes, sucralose"}, "Zero-calorie sparkling water sweetened with sucralose. Not unsweetened."),
        (GLASSWATER, "Sweetened Kiwi Strawberry Sparkling Water", "sparkling-water", Z("1 bottle (17 fl oz / 503 mL)", 10), [S("EA", "17 fl oz bottle", 1.29, 17), S("12PK", "12 x 17 fl oz bottles", 12.99, 204)],
         "Carbonated water, natural flavor, citric acid, sucralose, potassium benzoate.", (), ("vegan", "gluten-free", "caffeine-free"),
         {"Flavor": "Kiwi strawberry", "Sweetened": "Yes, sucralose"}, "Zero-calorie kiwi strawberry sparkling water sweetened with sucralose."),
        (GLASSWATER, "Sparkling Mineral Water", "sparkling-water", Z("1 bottle (12 fl oz / 355 mL)", 15), [S("12PK", "12 x 12 fl oz glass bottles", 11.99, 144)],
         "Carbonated natural mineral water.", (), ("unsweetened", "vegan", "gluten-free", "caffeine-free"), {"Flavor": "Unflavored", "Sweetened": "No"},
         "Naturally mineral-rich sparkling water in glass bottles."),
        (STORE_BRAND, "Club Soda", "sparkling-water", Z(C8, 75), [S("1L", "1 liter bottle", 0.99, 33.8)], "Carbonated water, sodium bicarbonate, potassium sulfate.", (),
         ("unsweetened", "vegan", "gluten-free", "caffeine-free"), {"Flavor": "Unflavored", "Sweetened": "No"}, "Club soda for mixing, with added minerals."),
        (STORE_BRAND, "Tonic Water", "sparkling-water", N(C8, 90, 0, 0, 35, 24, 0, 24, 24, 0), [S("1L", "1 liter bottle", 1.29, 33.8)],
         "Carbonated water, high fructose corn syrup, citric acid, natural flavors, quinine.", (), ("vegan", "gluten-free", "caffeine-free"), {"Sweetened": "Yes"},
         "Tonic water with quinine. Unlike club soda or seltzer, tonic has 24 g added sugar per cup."),
        (STORE_BRAND, "Diet Tonic Water", "sparkling-water", Z(C8, 35), [S("1L", "1 liter bottle", 1.29, 33.8)],
         "Carbonated water, citric acid, natural flavors, quinine, aspartame.", (), ("vegan", "gluten-free", "caffeine-free"), {"Sweetened": "Yes, aspartame"},
         "Zero-calorie tonic water sweetened with aspartame."),
    ]  # fmt: skip
    for flavor in ("Original", "Lime", "Lemon", "Black Cherry"):
        flav = "" if flavor == "Original" else f", natural {flavor.lower()} flavor"
        rows.append((
            STORE_BRAND, f"{flavor} Sparkling Water", "sparkling-water", Z(CAN), [S("12PK", "12 x 12 fl oz cans", 3.99, 144)], f"Carbonated water{flav}.", (),
            ("unsweetened", "vegan", "gluten-free", "caffeine-free"), {"Flavor": "Unflavored" if flavor == "Original" else flavor, "Sweetened": "No"},
            f"{'Unflavored' if flavor == 'Original' else flavor} sparkling water with zero calories and no sweeteners.",
        ))  # fmt: skip
    bottle = "1 bottle (16.9 fl oz / 500 mL)"
    rows += [
        (STORE_BRAND, "Purified Drinking Water", "water", Z(bottle), [S("24PK", "24 x 16.9 fl oz bottles", 4.49, 405.6), S("40PK", "40 x 16.9 fl oz bottles", 6.99, 676)],
         "Purified water.", (), ("vegan", "gluten-free", "caffeine-free"), {"Source": "Purified municipal water"}, "Purified bottled water."),
        (PINECREST, "Natural Spring Water", "water", Z(bottle), [S("24PK", "24 x 16.9 fl oz bottles", 5.99, 405.6), S("GAL", "1 gallon jug", 1.49, 128)],
         "Natural spring water.", (), ("vegan", "gluten-free", "caffeine-free"), {"Source": "Natural spring"}, "Crisp natural spring water."),
        (PINECREST, "Alkaline Water, pH 9.5+", "water", Z("1 bottle (1 L)", 10), [S("1L", "1 liter bottle", 1.99, 33.8), S("6PK", "6 x 1 liter bottles", 9.99, 202.8)],
         "Purified water, potassium bicarbonate, magnesium chloride.", (), ("vegan", "gluten-free", "caffeine-free"), {"Source": "Purified, ionized", "pH": "9.5 or higher"},
         "Ionized alkaline water with added electrolytes for taste."),
        (STORE_BRAND, "Distilled Water", "water", Z("8 fl oz (240 mL)"), [S("GAL", "1 gallon jug", 1.29, 128)], "Distilled water.", (), ("vegan", "gluten-free", "caffeine-free"),
         {"Source": "Steam distilled"}, "Steam-distilled water for drinking, CPAP machines, and appliances."),
        (PINECREST, "Electrolyte Enhanced Water", "water", Z("1 bottle (1 L)", 10), [S("1L", "1 liter bottle", 1.99, 33.8)],
         "Purified water, calcium chloride, magnesium chloride, potassium bicarbonate.", (), ("vegan", "gluten-free", "caffeine-free"), {"Source": "Purified"},
         "Purified water with electrolytes added for taste. Not a rehydration drink."),
    ]  # fmt: skip
    return _rows(rows, DRINK_CLAIMS)


# --- Sports, electrolyte, kombucha, shakes, energy -----------------------------------------------


def functional() -> list[ProductSeed]:
    b20 = "1 bottle (20 fl oz / 591 mL)"
    sport_sizes = [
        S("20OZ", "20 fl oz bottle", 1.79, 20),
        S("8PK", "8 x 20 fl oz bottles", 8.99, 160),
    ]
    rows: list[Row] = []
    for flavor, color in (
        ("Fruit Punch", "red 40"),
        ("Lemon-Lime", "yellow 5"),
        ("Orange", "yellow 6"),
        ("Glacier Berry", "blue 1"),
        ("Grape", "red 40, blue 1"),
    ):
        rows.append((
            PACER, f"{flavor} Sports Drink", "sports-drink", N(b20, 140, 0, 0, 270, 36, 0, 34, 34, 0), sport_sizes,
            f"Water, sugar, dextrose, citric acid, salt, sodium citrate, monopotassium phosphate, natural flavor, {color}.", (), ("vegan", "gluten-free", "caffeine-free"),
            {"Flavor": flavor, "Electrolytes": "270 mg sodium, 75 mg potassium per bottle"},
            f"{flavor} sports drink with electrolytes and carbs to refuel during exercise. 34 g added sugar per bottle.",
        ))  # fmt: skip
    for flavor, color in (
        ("Fruit Punch", "red 40"),
        ("Lemon-Lime", "yellow 5"),
        ("Glacier Berry", "blue 1"),
        ("Orange", "yellow 6"),
    ):
        rows.append((
            PACER, f"Zero Sugar {flavor} Sports Drink", "sports-drink", N(b20, 10, 0, 0, 270, 2, 0, 0, 0, 0), sport_sizes,
            f"Water, citric acid, salt, sodium citrate, monopotassium phosphate, natural flavor, sucralose, acesulfame potassium, {color}.", (),
            ("vegan", "gluten-free", "caffeine-free"), {"Flavor": flavor, "Electrolytes": "270 mg sodium, 75 mg potassium per bottle"},
            "The same electrolytes as our regular sports drink with zero sugar and 10 calories. Sweetened with sucralose.",
        ))  # fmt: skip
    rows += [
        (STORE_BRAND, "Fruit Punch Sports Drink", "sports-drink", N(b20, 140, 0, 0, 270, 36, 0, 34, 34, 0), [S("8PK", "8 x 20 fl oz bottles", 6.99, 160)],
         "Water, sugar, dextrose, citric acid, salt, sodium citrate, monopotassium phosphate, natural flavor, red 40.", (), ("vegan", "gluten-free", "caffeine-free"),
         {"Flavor": "Fruit Punch"}, "Fruit punch sports drink with electrolytes."),
        (STORE_BRAND, "Lemon-Lime Sports Drink", "sports-drink", N(b20, 140, 0, 0, 270, 36, 0, 34, 34, 0), [S("8PK", "8 x 20 fl oz bottles", 6.99, 160)],
         "Water, sugar, dextrose, citric acid, salt, sodium citrate, monopotassium phosphate, natural flavor, yellow 5.", (), ("vegan", "gluten-free", "caffeine-free"),
         {"Flavor": "Lemon-Lime"}, "Lemon-lime sports drink with electrolytes."),
        (STORE_BRAND, "Zero Sugar Lemon-Lime Sports Drink", "sports-drink", N(b20, 10, 0, 0, 270, 2, 0, 0, 0, 0), [S("8PK", "8 x 20 fl oz bottles", 6.99, 160)],
         "Water, citric acid, salt, sodium citrate, monopotassium phosphate, natural flavor, sucralose, yellow 5.", (), ("vegan", "gluten-free", "caffeine-free"),
         {"Flavor": "Lemon-Lime"}, "Zero sugar lemon-lime sports drink."),
        (PACER, "Electrolyte Rehydration Solution, Mixed Fruit", "electrolyte-drink", N("12 fl oz (360 mL)", 35, 0, 0, 370, 9, 0, 8, 8, 0), [S("1L", "1 liter bottle", 5.49, 33.8)],
         "Water, dextrose, citric acid, potassium citrate, salt, sodium citrate, natural flavor, sucralose, acesulfame potassium, red 40.", (), ("gluten-free", "caffeine-free"),
         {"Electrolytes": "370 mg sodium, 280 mg potassium per 12 fl oz"}, "Oral rehydration solution with more electrolytes and less sugar than sports drinks."),
        (PACER, "Zero Sugar Electrolyte Drink Mix, Lemon Lime", "electrolyte-drink", N("1 stick (4 g), mixed with 16 fl oz water", 5, 0, 0, 500, 1, 0, 0, 0, 0),
         [S("10CT", "10 stick packs", 6.99, 1.4)], "Citric acid, sodium citrate, potassium citrate, magnesium lactate, natural flavor, stevia leaf extract.", (),
         ("vegan", "gluten-free", "caffeine-free"), {"Electrolytes": "500 mg sodium, 200 mg potassium per stick"}, "Zero sugar electrolyte powder sticks sweetened with stevia."),
        (PACER, "Electrolyte Drink Mix, Lemon Lime", "electrolyte-drink", N("1 stick (16 g), mixed with 16 fl oz water", 45, 0, 0, 500, 11, 0, 11, 11, 0),
         [S("10CT", "10 stick packs", 6.99, 5.6)], "Cane sugar, dextrose, citric acid, salt, potassium citrate, sodium citrate, natural flavor.", (),
         ("vegan", "gluten-free", "caffeine-free"), {"Electrolytes": "500 mg sodium, 370 mg potassium per stick"}, "Electrolyte powder sticks with 11 g cane sugar."),
        (PALMGROVE, "100% Coconut Water", "electrolyte-drink", N("1 carton (11.1 fl oz / 330 mL)", 60, 0, 0, 45, 15, 0, 14, 0, 0),
         [S("EA", "11.1 fl oz carton", 2.29, 11.1), S("6PK", "6 x 11.1 fl oz cartons", 11.99, 66.6)], "100% coconut water.", (),
         ("vegan", "gluten-free", "caffeine-free", "unsweetened"), {"Electrolytes": "45 mg sodium, 470 mg potassium per carton"},
         "Pure coconut water with no sugar added; naturally rich in potassium."),
        (PALMGROVE, "Organic Coconut Water", "electrolyte-drink", N("1 carton (11.1 fl oz / 330 mL)", 60, 0, 0, 45, 15, 0, 14, 0, 0), [S("EA", "11.1 fl oz carton", 2.79, 11.1)],
         "Organic coconut water.", (), ("vegan", "gluten-free", "caffeine-free", "unsweetened", "non-gmo"), {"Electrolytes": "45 mg sodium, 470 mg potassium per carton"},
         "Organic pure coconut water with nothing added."),
    ]  # fmt: skip
    out = _rows(rows, DRINK_CLAIMS)
    kombucha = [
        ("Organic Ginger Lemon Kombucha", "organic ginger juice, organic lemon juice"),
        ("Organic Original Kombucha", ""),
        ("Organic Mixed Berry Kombucha", "organic raspberry juice, organic blueberry juice"),
        ("Organic Guava Kombucha", "organic guava puree"),
    ]
    krows: list[Row] = [
        (BRIGHTCULTURE, title, "kombucha", N(C8, 30, 0, 0, 10, 7, 0, 6, 4, 0), [S("16OZ", "16 fl oz bottle", 3.49, 16)],
         f"Organic kombucha (filtered water, organic black tea, organic green tea, organic cane sugar, kombucha culture){', ' + extra if extra else ''}.", (),
         ("vegan", "gluten-free", "non-gmo"), {"Caffeine": "About 10 mg per 8 fl oz", "Alcohol": "Non-alcoholic (less than 0.5% ABV)", "Live cultures": "Yes"},
         "Raw, organic, naturally fizzy fermented tea with live cultures. Non-alcoholic. Keep cold.")
        for title, extra in kombucha
    ]  # fmt: skip
    out += _rows(krows, DRINK_CLAIMS, REFRIGERATED)
    b11 = "1 bottle (11 fl oz / 325 mL)"
    shake_sizes = [
        S("4PK", "4 x 11 fl oz bottles", 6.99, 44),
        S("12PK", "12 x 11 fl oz bottles", 17.99, 132),
    ]
    shake_ing = "Filtered water, milk protein concentrate, cellulose gel, natural flavors, salt, potassium citrate, sucralose, acesulfame potassium, vitamin and mineral blend"
    rows = [
        (IRONPEAK, "Chocolate High Protein Shake", "protein-shake", N(b11, 160, 4.5, 1, 280, 6, 1, 1, 0, 30), shake_sizes,
         f"{shake_ing.replace('natural flavors', 'cocoa, natural flavors')}.", ("milk",), ("gluten-free", "lactose-free"), {"Protein": "30 g per bottle"},
         "Shelf-stable chocolate protein shake with 30 g protein and 1 g sugar. Lactose free, but contains milk protein."),
        (IRONPEAK, "Vanilla High Protein Shake", "protein-shake", N(b11, 150, 3.5, 0.5, 250, 5, 1, 1, 0, 30), shake_sizes, f"{shake_ing}.", ("milk",), ("gluten-free", "lactose-free"),
         {"Protein": "30 g per bottle"}, "Vanilla protein shake with 30 g protein and 1 g sugar."),
        (IRONPEAK, "Strawberry High Protein Shake", "protein-shake", N(b11, 150, 3.5, 0.5, 250, 5, 1, 1, 0, 30), shake_sizes, f"{shake_ing}.", ("milk",), ("gluten-free", "lactose-free"),
         {"Protein": "30 g per bottle"}, "Strawberry protein shake with 30 g protein."),
        (IRONPEAK, "Coffee High Protein Shake", "protein-shake", N(b11, 160, 3.5, 0.5, 260, 6, 1, 1, 0, 30), shake_sizes,
         f"{shake_ing.replace('natural flavors', 'coffee extract, natural flavors')}.", ("milk",), ("gluten-free", "lactose-free"),
         {"Protein": "30 g per bottle", "Caffeine": "About 100 mg per bottle"}, "Coffee protein shake with 30 g protein and 100 mg caffeine."),
        (GREENSTRIDE, "Plant-Based Protein Shake, Chocolate", "protein-shake", N(b11, 160, 7, 1, 340, 9, 3, 1, 0, 20), [S("4PK", "4 x 11 fl oz bottles", 7.99, 44)],
         "Filtered water, pea protein, cocoa, sunflower oil, gellan gum, sea salt, natural flavors, monk fruit extract, stevia leaf extract.", (),
         ("vegan", "dairy-free", "gluten-free", "plant-based", "lactose-free"), {"Protein": "20 g per bottle"}, "Vegan pea protein shake with 20 g protein and no dairy."),
        (GREENSTRIDE, "Plant-Based Protein Shake, Vanilla", "protein-shake", N(b11, 150, 7, 1, 320, 7, 2, 1, 0, 20), [S("4PK", "4 x 11 fl oz bottles", 7.99, 44)],
         "Filtered water, pea protein, sunflower oil, gellan gum, sea salt, natural vanilla flavor, monk fruit extract, stevia leaf extract.", (),
         ("vegan", "dairy-free", "gluten-free", "plant-based", "lactose-free"), {"Protein": "20 g per bottle"}, "Vegan vanilla protein shake with 20 g protein."),
        (STORE_BRAND, "High Protein Nutrition Shake, Chocolate", "protein-shake", N(b11, 160, 4.5, 1, 280, 6, 1, 1, 0, 30), [S("12PK", "12 x 11 fl oz bottles", 14.99, 132)],
         f"{shake_ing.replace('natural flavors', 'cocoa, natural flavors')}.", ("milk",), ("gluten-free", "lactose-free"), {"Protein": "30 g per bottle"},
         "Chocolate protein shake with 30 g protein, value pack."),
        (STORE_BRAND, "Complete Nutrition Shake, Vanilla", "protein-shake", N("1 bottle (8 fl oz / 237 mL)", 220, 6, 1, 200, 33, 1, 15, 14, 9), [S("6PK", "6 x 8 fl oz bottles", 8.99, 48)],
         "Water, corn maltodextrin, sugar, milk protein concentrate, canola oil, soy protein isolate, vitamin and mineral blend, natural flavor.", ("milk", "soy"), ("gluten-free",),
         {"Protein": "9 g per bottle"}, "Meal-replacement nutrition shake with vitamins and minerals. Only 9 g protein and 15 g sugar, so not a high-protein shake."),
    ]  # fmt: skip
    out += _rows(rows, (*DRINK_CLAIMS, "high-protein"), AFTER_OPENING)
    c16 = "1 can (16 fl oz / 473 mL)"
    esizes = [S("16OZ", "16 fl oz can", 2.49, 16), S("4PK", "4 x 16 fl oz cans", 8.49, 64)]
    energy_base = "taurine, sodium citrate, citric acid, natural flavors, caffeine, niacinamide, vitamin B6, vitamin B12"
    rows = [
        (VOLTLINE, "Original Energy Drink", "energy-drink", N(c16, 210, 0, 0, 370, 54, 0, 54, 54, 0), esizes, f"Carbonated water, sugar, glucose, {energy_base}.", (), ("gluten-free",),
         {"Caffeine": "160 mg per 16 fl oz can"}, "Classic energy drink with 160 mg caffeine and 54 g added sugar. Not recommended for children or pregnant women."),
        (VOLTLINE, "Zero Sugar Energy Drink", "energy-drink", N(c16, 10, 0, 0, 370, 3, 0, 0, 0, 0), esizes, f"Carbonated water, erythritol, {energy_base}, sucralose, acesulfame potassium.",
         (), ("gluten-free",), {"Caffeine": "160 mg per 16 fl oz can"}, "Zero sugar energy drink with 160 mg caffeine and 10 calories."),
        (VOLTLINE, "Zero Sugar Tropical Energy Drink", "energy-drink", N(c16, 10, 0, 0, 370, 3, 0, 0, 0, 0), esizes, f"Carbonated water, erythritol, {energy_base}, sucralose.",
         (), ("gluten-free",), {"Caffeine": "160 mg per 16 fl oz can"}, "Tropical zero sugar energy drink, 160 mg caffeine."),
        (VOLTLINE, "Zero Sugar Berry Blast Energy Drink", "energy-drink", Z(CAN, 40), [S("12OZ", "12 fl oz can", 2.29, 12), S("12PK", "12 x 12 fl oz cans", 22.99, 144)],
         "Carbonated water, citric acid, natural flavors, caffeine, sodium benzoate, sucralose, vitamin C, vitamin B6, vitamin B12.", (), ("gluten-free", "vegan"),
         {"Caffeine": "200 mg per 12 fl oz can"}, "High-caffeine fitness energy drink: 200 mg caffeine, zero sugar, zero calories."),
        (VOLTLINE, "Organic Sparkling Green Tea Energy, Pomegranate", "energy-drink", N(CAN, 50, 0, 0, 15, 13, 0, 12, 12, 0), [S("4PK", "4 x 12 fl oz cans", 9.99, 48)],
         "Carbonated water, organic cane sugar, organic green tea extract, organic pomegranate juice concentrate, citric acid.", (), ("vegan", "gluten-free", "non-gmo"),
         {"Caffeine": "120 mg per 12 fl oz can (from green tea)"}, "Organic sparkling energy drink with 120 mg caffeine from green tea and 12 g cane sugar."),
        (VOLTLINE, "Berry Energy Shot", "energy-drink", N("1 bottle (2 fl oz / 59 mL)", 5, 0, 0, 15, 0, 0, 0, 0, 0), [S("6PK", "6 x 2 fl oz shots", 14.99, 12)],
         "Water, glucuronolactone, malic acid, caffeine, taurine, natural flavors, sucralose, niacinamide, vitamin B6, vitamin B12.", (), ("gluten-free",),
         {"Caffeine": "200 mg per 2 fl oz shot"}, "Two-ounce energy shot with 200 mg caffeine and zero sugar. Do not exceed two per day."),
        (STORE_BRAND, "Zero Sugar Energy Drink", "energy-drink", N(c16, 10, 0, 0, 370, 3, 0, 0, 0, 0), [S("16OZ", "16 fl oz can", 1.79, 16)],
         f"Carbonated water, erythritol, {energy_base}, sucralose.", (), ("gluten-free",), {"Caffeine": "160 mg per 16 fl oz can"}, "Zero sugar energy drink with 160 mg caffeine."),
    ]  # fmt: skip
    out += _rows(rows, DRINK_CLAIMS)
    return out


def products() -> list[ProductSeed]:
    return [*coffee(), *tea(), *juice(), *soda(), *water(), *functional()]


__all__ = ["products"]
