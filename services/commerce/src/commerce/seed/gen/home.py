"""Home & Kitchen: cookware, bakeware, knives, prep tools, food storage, small appliances,
dinnerware, drinkware, bedding, bath, candles, storage, and floor care, fans, and air
purifiers.

Specs carry the numbers shoppers compare: pan diameter, oven-safe temperature, quarts,
watts, thread count, square footage.
"""

from __future__ import annotations

from collections.abc import Iterable

from commerce.seed.data import ProductSeed
from commerce.seed.gen.common import Size, cents, item, options, slugify

CAT = "home-kitchen"
KETTLEWORTH = "Kettleworth"  # cookware, knives, prep: premium
HARBOR = "Harbor Home"  # bedding, bath, dinnerware, candles: mid to premium
OWN_BRAND = "Serigan Mart Home"  # store brand, value
CRISPWELL = "Crispwell"  # small kitchen appliances
AIRLOFT = "Airloft"  # vacuums, fans, air purifiers

BED_SIZES = ("Twin", "Full", "Queen", "King")


def one(dollars: float, label: str = "Each", code: str = "EA") -> list[Size]:
    return [Size(code, label, cents(dollars))]


def sz(*rows: tuple[str, str, float]) -> list[Size]:
    return [Size(code, label, cents(price)) for code, label, price in rows]


def bed(*prices: float, names: Iterable[str] = BED_SIZES) -> list[Size]:
    """Bed-size variants, e.g. bed(29.99, 34.99, 39.99, 44.99) for Twin-King."""
    return [
        Size(n.upper().replace("/", "")[:6], n, cents(p))
        for n, p in zip(names, prices, strict=True)
    ]


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


def colors(
    brand: str,
    product_type: str,
    title: str,
    description: str,
    names: list[str],
    dollars: float,
    tags: Iterable[str] = (),
    specs: dict[str, str] | None = None,
) -> ProductSeed:
    slug = slugify(brand, title)
    return item(
        category=CAT, product_type=product_type, brand=brand, title=title,
        description=description, variants_=options(CAT, slug, names, cents(dollars), "color"),
        tags=tags, specs=specs, slug=slug,
    )  # fmt: skip


# fmt: off
def cookware() -> list[ProductSeed]:
    return [
        P(KETTLEWORTH, "skillet", "Nonstick Frying Pan",
          "Hard-anodized aluminum frying pan with a PFOA-free nonstick coating and a stay-cool stainless handle. Oven safe to 400°F; works on gas, electric, and induction.",
          sz(("8IN", "8 in", 29.99), ("10IN", "10 in", 39.99), ("12IN", "12 in", 49.99)), ["oven-safe"],
          {"Material": "Hard-anodized aluminum, nonstick", "Oven safe to": "400°F", "Dishwasher safe": "No, hand wash recommended", "Induction compatible": "Yes"}),
        P(KETTLEWORTH, "skillet", "Tri-Ply Stainless Steel Skillet",
          "Fully clad tri-ply stainless steel skillet for searing and pan sauces. Oven safe to 600°F, dishwasher safe, and induction ready.",
          sz(("10IN", "10 in", 59.99), ("12IN", "12 in", 74.99)), ["oven-safe", "dishwasher-safe"],
          {"Material": "Tri-ply stainless steel", "Oven safe to": "600°F", "Dishwasher safe": "Yes", "Induction compatible": "Yes"}),
        P(KETTLEWORTH, "skillet", "Pre-Seasoned Cast Iron Skillet, 10 in",
          "Heavy 10-inch cast iron skillet, pre-seasoned with vegetable oil and ready for stove, oven, grill, or campfire. Hand wash and dry.",
          one(24.99), ["oven-safe"],
          {"Material": "Cast iron", "Diameter": "10 in", "Oven safe to": "Any oven temperature", "Dishwasher safe": "No", "Induction compatible": "Yes"}),
        P(KETTLEWORTH, "skillet", "Ceramic Nonstick Skillet, 10 in",
          "PTFE-free ceramic nonstick skillet that releases eggs with little oil. Oven safe to 450°F.",
          one(39.99), ["oven-safe"],
          {"Material": "Aluminum with ceramic nonstick", "Diameter": "10 in", "Oven safe to": "450°F", "Dishwasher safe": "No, hand wash recommended", "Coating": "PTFE and PFAS free"}),
        P(OWN_BRAND, "skillet", "Nonstick Frying Pan Set, 8 & 10 in",
          "Value set of two aluminum nonstick frying pans with soft-grip handles. Oven safe to 350°F.",
          one(19.99, "2 pans", "2PC"), ["oven-safe"],
          {"Material": "Aluminum, nonstick", "Oven safe to": "350°F", "Dishwasher safe": "Yes", "Induction compatible": "No"}),
        P(KETTLEWORTH, "dutch-oven", "Enameled Cast Iron Dutch Oven, 5.5 qt",
          "Round enameled cast iron Dutch oven for braises, soups, and bread. Oven safe to 500°F; no seasoning needed.",
          sz(("5_5QT", "5.5 qt", 79.99)), ["oven-safe"],
          {"Material": "Enameled cast iron", "Capacity": "5.5 qt", "Oven safe to": "500°F", "Dishwasher safe": "Yes (hand wash recommended)"}),
        P(KETTLEWORTH, "saucepan", "Tri-Ply Stainless Steel Saucepan with Lid",
          "Tri-ply stainless saucepan with a tight-fitting lid and pour rims. Oven safe to 600°F and dishwasher safe.",
          sz(("2QT", "2 qt", 49.99), ("3QT", "3 qt", 59.99)), ["oven-safe", "dishwasher-safe"],
          {"Material": "Tri-ply stainless steel", "Oven safe to": "600°F", "Dishwasher safe": "Yes", "Induction compatible": "Yes"}),
        P(OWN_BRAND, "stockpot", "Stainless Steel Stockpot with Lid, 8 qt",
          "Value 8-quart stainless stockpot with an encapsulated base for pasta, soups, and stocks. Dishwasher safe.",
          sz(("8QT", "8 qt", 29.99)), ["dishwasher-safe", "oven-safe"],
          {"Material": "Stainless steel", "Capacity": "8 qt", "Oven safe to": "500°F", "Dishwasher safe": "Yes"}),
        P(KETTLEWORTH, "cookware-set", "Tri-Ply Stainless Steel Cookware Set, 10-Piece",
          "Ten-piece fully clad stainless cookware set: 8 and 10 in skillets, 1.5 and 3 qt saucepans, 3.5 qt sauté pan, 8 qt stockpot, and lids. Oven safe to 600°F.",
          one(249.99, "10 pieces", "10PC"), ["oven-safe", "dishwasher-safe"],
          {"Material": "Tri-ply stainless steel", "Pieces": "10", "Oven safe to": "600°F", "Dishwasher safe": "Yes", "Induction compatible": "Yes"}),
        P(KETTLEWORTH, "cookware-set", "Hard-Anodized Nonstick Cookware Set, 10-Piece",
          "Ten-piece hard-anodized nonstick set with glass lids. Oven safe to 400°F (lids to 350°F).",
          one(179.99, "10 pieces", "10PC"), ["oven-safe"],
          {"Material": "Hard-anodized aluminum, nonstick", "Pieces": "10", "Oven safe to": "400°F", "Dishwasher safe": "No, hand wash recommended"}),
        P(OWN_BRAND, "cookware-set", "Nonstick Cookware Set, 12-Piece",
          "Value 12-piece aluminum nonstick cookware set with pans, pots, lids, and utensils. Oven safe to 350°F.",
          one(69.99, "12 pieces", "12PC"), ["oven-safe", "dishwasher-safe"],
          {"Material": "Aluminum, nonstick", "Pieces": "12", "Oven safe to": "350°F", "Dishwasher safe": "Yes"}),
        P(KETTLEWORTH, "griddle", "Reversible Cast Iron Grill/Griddle, 20 x 10 in",
          "Reversible pre-seasoned cast iron plate with a flat griddle side and a ridged grill side that spans two burners.",
          one(39.99), ["oven-safe"], {"Material": "Cast iron", "Size": "20 x 10 in", "Oven safe to": "Any oven temperature"}),
        # Bakeware
        P(OWN_BRAND, "bakeware", "Nonstick Half Sheet Pans, 2-Pack",
          "Two 18 x 13 in nonstick steel baking sheets for cookies and sheet-pan dinners. Oven safe to 450°F.",
          one(14.99, "2 pans", "2PK"), ["oven-safe", "dishwasher-safe"], {"Material": "Carbon steel, nonstick", "Size": "18 x 13 in", "Oven safe to": "450°F"}),
        P(KETTLEWORTH, "bakeware", "Aluminum Half Sheet Pan with Cooling Rack",
          "Commercial-grade uncoated aluminum half sheet pan that won't warp, with a fitted stainless cooling rack.",
          one(29.99), ["oven-safe"], {"Material": "Aluminum, stainless rack", "Size": "18 x 13 in", "Oven safe to": "500°F", "Dishwasher safe": "No"}),
        P(OWN_BRAND, "bakeware", "Glass Baking Dish with Lid, 9 x 13 in",
          "Tempered glass 9 x 13 in baking dish with a snap-on lid for casseroles, lasagna, and leftovers. Oven, microwave, and dishwasher safe (lid is not oven safe).",
          one(17.99), ["oven-safe", "dishwasher-safe", "bpa-free"], {"Material": "Tempered glass, BPA-free lid", "Size": "9 x 13 in (3 qt)", "Oven safe to": "425°F"}),
        P(OWN_BRAND, "bakeware", "Nonstick 12-Cup Muffin Pan",
          "Nonstick steel muffin and cupcake pan with 12 standard cups. Oven safe to 450°F.",
          one(9.99), ["oven-safe", "dishwasher-safe"], {"Material": "Carbon steel, nonstick", "Cups": "12 standard", "Oven safe to": "450°F"}),
        P(KETTLEWORTH, "bakeware", "Nonstick Loaf Pan, 9 x 5 in",
          "Heavy-gauge nonstick loaf pan for sandwich bread, banana bread, and meatloaf.",
          one(14.99), ["oven-safe"], {"Material": "Aluminized steel, nonstick", "Size": "9 x 5 in", "Oven safe to": "450°F"}),
        P(KETTLEWORTH, "bakeware", "Silicone Baking Mats, 2-Pack",
          "Reusable half-sheet silicone baking mats that replace parchment paper. Oven safe to 480°F and dishwasher safe.",
          one(15.99, "2 mats", "2PK"), ["oven-safe", "dishwasher-safe", "bpa-free"], {"Material": "Food-grade silicone", "Oven safe to": "480°F"}),
    ]


def prep() -> list[ProductSeed]:
    return [
        P(KETTLEWORTH, "knife-set", "14-Piece Knife Block Set",
          "Forged high-carbon stainless knife set with chef's, bread, santoku, utility, and paring knives, six steak knives, shears, and a honing steel in an acacia block.",
          one(149.99, "14 pieces", "14PC"), [], {"Pieces": "14", "Blade": "Forged high-carbon stainless steel", "Dishwasher safe": "No, hand wash"}),
        P(OWN_BRAND, "knife-set", "6-Piece Knife Set with Blade Covers",
          "Value set of six color-coded nonstick-coated knives with matching blade guards.",
          one(19.99, "6 pieces", "6PC"), [], {"Pieces": "6", "Blade": "Stainless steel, nonstick coated", "Dishwasher safe": "No, hand wash"}),
        P(KETTLEWORTH, "kitchen-knife", "7-inch Santoku Knife",
          "Forged high-carbon stainless santoku with a hollow-edge blade that keeps slices from sticking.",
          one(39.99), [], {"Blade length": "7 in", "Blade": "Forged high-carbon stainless steel"}),
        P(KETTLEWORTH, "kitchen-knife", "3.5-inch Paring Knife",
          "Forged high-carbon stainless paring knife for peeling and detail work.",
          one(19.99), [], {"Blade length": "3.5 in", "Blade": "Forged high-carbon stainless steel"}),
        P(KETTLEWORTH, "kitchen-knife", "9-inch Serrated Bread Knife",
          "Serrated bread knife that slices crusty loaves and tomatoes without crushing.",
          one(29.99), [], {"Blade length": "9 in", "Blade": "High-carbon stainless steel, serrated"}),
        P(KETTLEWORTH, "knife-sharpener", "Two-Stage Knife Sharpener",
          "Manual two-stage sharpener with coarse and fine slots for straight-edge knives.",
          one(14.99), [], {"Stages": "Coarse, fine", "For": "Straight-edge knives"}),
        P(KETTLEWORTH, "cutting-board", "End-Grain Acacia Cutting Board, 18 x 12 in",
          "Thick end-grain acacia board that is gentle on knife edges, with a juice groove. Hand wash and oil occasionally.",
          one(59.99), [], {"Material": "Acacia wood, end grain", "Size": "18 x 12 x 1.5 in", "Dishwasher safe": "No"}),
        P(OWN_BRAND, "cutting-board", "Plastic Cutting Boards, Set of 3",
          "Three BPA-free plastic cutting boards in small, medium, and large with non-slip edges. Dishwasher safe.",
          one(14.99, "3 boards", "3PC"), ["bpa-free", "dishwasher-safe"], {"Material": "BPA-free polypropylene", "Pieces": "3"}),
        P(OWN_BRAND, "cutting-board", "Bamboo Cutting Board, 15 x 10 in",
          "Lightweight bamboo cutting and serving board. Hand wash.",
          one(11.99), [], {"Material": "Bamboo", "Size": "15 x 10 in", "Dishwasher safe": "No"}),
        P(OWN_BRAND, "kitchen-utensils", "Silicone Cooking Utensil Set, 6-Piece",
          "Heat-resistant silicone spatulas, spoons, and a turner with stainless cores, safe on nonstick pans to 450°F. BPA free and dishwasher safe.",
          one(17.99, "6 pieces", "6PC"), ["bpa-free", "dishwasher-safe"], {"Material": "Silicone, stainless core", "Heat resistant to": "450°F", "Pieces": "6"}),
        P(KETTLEWORTH, "kitchen-utensils", "Stainless Steel Locking Tongs, 9 & 12 in",
          "Two stainless steel locking tongs with silicone tips for grilling and serving. Dishwasher safe.",
          one(15.99, "2 tongs", "2PC"), ["dishwasher-safe"], {"Material": "Stainless steel, silicone tips", "Lengths": "9 in, 12 in"}),
        P(KETTLEWORTH, "measuring-cups", "Stainless Steel Measuring Cups and Spoons Set",
          "Eleven-piece stainless measuring set with engraved markings that won't wear off: 6 cups and 5 spoons.",
          one(19.99, "11 pieces", "11PC"), ["dishwasher-safe"], {"Material": "Stainless steel", "Pieces": "11"}),
        P(OWN_BRAND, "mixing-bowls", "Glass Mixing Bowls, Set of 3",
          "Three nesting tempered glass bowls (1, 1.5, and 2.5 qt) that are microwave, oven, and dishwasher safe.",
          one(19.99, "3 bowls", "3PC"), ["dishwasher-safe", "oven-safe"], {"Material": "Tempered glass", "Sizes": "1, 1.5, 2.5 qt"}),
        P(OWN_BRAND, "kitchen-utensils", "Smooth-Edge Can Opener",
          "Manual can opener that cuts below the rim for smooth, safe edges, with soft grips.",
          one(11.99), [], {"Type": "Manual, side cut"}),
        # Food storage
        P(OWN_BRAND, "food-storage", "Plastic Food Storage Containers with Lids, 24-Piece",
          "Twelve BPA-free plastic containers with snap lids in assorted sizes. Microwave, freezer, and dishwasher safe.",
          one(14.99, "24 pieces (12 containers)", "24PC"), ["bpa-free", "dishwasher-safe"], {"Material": "BPA-free polypropylene", "Pieces": "24"}),
        P(HARBOR, "food-storage", "Glass Meal Prep Containers, 2-Compartment, 5-Pack",
          "Five borosilicate glass meal prep containers with two compartments and locking lids. Oven safe (without lids), microwave, and dishwasher safe.",
          one(29.99, "5 containers", "5PK"), ["bpa-free", "dishwasher-safe", "oven-safe"], {"Material": "Borosilicate glass, BPA-free lids", "Capacity": "30 oz each", "Oven safe to": "450°F (without lid)"}),
        P(OWN_BRAND, "food-storage", "Reusable Silicone Food Storage Bags, 6-Pack",
          "Leak-proof reusable silicone bags in gallon, sandwich, and snack sizes. BPA free, freezer and dishwasher safe.",
          one(19.99, "6 bags", "6PK"), ["bpa-free", "dishwasher-safe"], {"Material": "Food-grade silicone", "Sizes": "2 gallon, 2 sandwich, 2 snack"}),
    ]


def appliances() -> list[ProductSeed]:
    return [
        P(CRISPWELL, "air-fryer", "Compact Air Fryer, 4 qt",
          "Compact 4-quart air fryer for 1-3 people with four presets and a nonstick, dishwasher-safe basket.",
          one(59.99), ["dishwasher-safe"], {"Capacity": "4 qt", "Wattage": "1400 W", "Max temperature": "400°F", "Presets": "4"}),
        P(CRISPWELL, "air-fryer", "Digital Air Fryer, 6 qt",
          "6-quart digital air fryer with a viewing window, shake reminder, and eight presets. Dishwasher-safe basket; family size.",
          sz(("6QT", "6 qt", 89.99)), ["dishwasher-safe"], {"Capacity": "6 qt", "Wattage": "1700 W", "Max temperature": "400°F", "Presets": "8"}),
        P(CRISPWELL, "air-fryer", "Dual Basket Air Fryer, 8 qt",
          "Two independent 4-quart baskets that cook two foods at different settings and finish together. Dishwasher-safe baskets.",
          one(149.99), ["dishwasher-safe"], {"Capacity": "8 qt (2 x 4 qt)", "Wattage": "1700 W", "Max temperature": "450°F", "Presets": "6"}),
        P(CRISPWELL, "air-fryer", "Air Fryer Toaster Oven, 26 qt",
          "Countertop convection oven that air fries, bakes, broils, and toasts 6 slices or a 12-inch pizza.",
          one(129.99), [], {"Capacity": "26 qt", "Wattage": "1800 W", "Functions": "Air fry, bake, broil, toast, roast, reheat"}),
        P(CRISPWELL, "blender", "Personal Blender with 2 To-Go Cups",
          "Single-serve blender for smoothies and shakes with two 20 oz BPA-free to-go cups. Dishwasher-safe cups.",
          one(29.99), ["bpa-free", "dishwasher-safe"], {"Wattage": "300 W", "Capacity": "2 x 20 oz cups"}),
        P(CRISPWELL, "blender", "Countertop Blender, 1200W, 64 oz",
          "1200-watt blender with a 64 oz BPA-free pitcher that crushes ice and makes frozen drinks, with three presets.",
          one(89.99), ["bpa-free", "dishwasher-safe"], {"Wattage": "1200 W", "Capacity": "64 oz", "Presets": "Smoothie, ice crush, pulse"}),
        P(CRISPWELL, "blender", "High-Performance Blender, 2.0 HP",
          "Professional-grade blender with variable speed, a tamper, and a 64 oz container that makes hot soup and nut butter. 7-year warranty.",
          one(299.99), ["bpa-free"], {"Wattage": "1500 W (2.0 HP)", "Capacity": "64 oz", "Warranty": "7 years"}),
        P(CRISPWELL, "coffee-maker", "12-Cup Programmable Drip Coffee Maker",
          "Programmable 12-cup drip coffee maker with a glass carafe, brew-strength control, 24-hour timer, and auto shutoff.",
          one(49.99), [], {"Capacity": "12 cups", "Carafe": "Glass", "Programmable": "Yes", "Auto shutoff": "2 hours"}),
        P(CRISPWELL, "coffee-maker", "Single-Serve Coffee Maker for Pods and Grounds",
          "Single-serve brewer that works with standard coffee pods or ground coffee in the included reusable filter; brews 6-12 oz.",
          one(79.99), [], {"Capacity": "6, 8, 10, or 12 oz", "Brews": "Pods or ground coffee", "Reservoir": "48 oz"}),
        P(CRISPWELL, "espresso-machine", "Espresso Machine with Milk Frother",
          "15-bar pump espresso machine with a steam wand for lattes and cappuccinos and a removable 1.5 L tank.",
          one(199.99), [], {"Pressure": "15 bar", "Milk frother": "Steam wand", "Reservoir": "1.5 L"}),
        P(CRISPWELL, "toaster", "2-Slice Wide-Slot Toaster",
          "Two-slice toaster with extra-wide slots for bagels, seven shade settings, and cancel/defrost/bagel buttons.",
          one(24.99), [], {"Slots": "2 wide", "Shade settings": "7", "Wattage": "900 W"}),
        P(CRISPWELL, "toaster", "4-Slice Stainless Steel Toaster",
          "Four-slice stainless toaster with independent controls for each pair of slots.",
          one(44.99), [], {"Slots": "4", "Shade settings": "7", "Wattage": "1500 W"}),
        P(CRISPWELL, "electric-kettle", "Glass Electric Kettle, 1.7 L",
          "1.7-liter glass electric kettle with a blue LED, auto shutoff, and boil-dry protection. BPA free.",
          one(29.99), ["bpa-free"], {"Capacity": "1.7 L", "Wattage": "1500 W", "Temperature control": "No", "Auto shutoff": "Yes"}),
        P(CRISPWELL, "slow-cooker", "Manual Slow Cooker, 4 qt",
          "Simple 4-quart slow cooker with low, high, and warm settings and a dishwasher-safe stoneware crock.",
          one(29.99), ["dishwasher-safe"], {"Capacity": "4 qt", "Settings": "Low, high, warm", "Programmable": "No"}),
        P(CRISPWELL, "slow-cooker", "Programmable Slow Cooker, 6 qt",
          "Programmable 6-quart slow cooker with a digital timer that switches to warm, and a locking lid for travel.",
          one(44.99), ["dishwasher-safe"], {"Capacity": "6 qt", "Settings": "Low, high, warm", "Programmable": "Yes, up to 20 hours"}),
        P(CRISPWELL, "pressure-cooker", "Electric Pressure Cooker, 6 qt",
          "7-in-1 electric pressure cooker that pressure cooks, slow cooks, sautés, steams, and makes rice and yogurt. Stainless inner pot is dishwasher safe.",
          one(89.99), ["dishwasher-safe"], {"Capacity": "6 qt", "Functions": "7-in-1", "Wattage": "1000 W"}),
        P(CRISPWELL, "rice-cooker", "Rice Cooker and Steamer, 6 Cups",
          "Rice cooker that makes up to 6 cups of cooked rice, with a steam basket and automatic keep-warm.",
          one(24.99), ["dishwasher-safe"], {"Capacity": "6 cups cooked (3 uncooked)", "Keep warm": "Yes"}),
        colors(CRISPWELL, "stand-mixer", "Tilt-Head Stand Mixer, 5 qt",
               "Tilt-head stand mixer with a 5-quart stainless bowl, 10 speeds, and a flat beater, dough hook, and whisk.",
               ["White", "Red", "Sage"], 249.99, [], {"Capacity": "5 qt", "Wattage": "325 W", "Speeds": "10", "Attachments": "Flat beater, dough hook, wire whisk"}),
        P(CRISPWELL, "hand-mixer", "5-Speed Hand Mixer",
          "Lightweight 5-speed hand mixer with beaters and dough hooks and a snap-on storage case.",
          one(29.99), [], {"Speeds": "5", "Wattage": "250 W"}),
        P(CRISPWELL, "food-processor", "Food Processor, 10 Cup",
          "10-cup food processor with slicing and shredding discs and a chopping blade.",
          one(69.99), ["dishwasher-safe", "bpa-free"], {"Capacity": "10 cups", "Wattage": "600 W"}),
    ]


def tabletop() -> list[ProductSeed]:
    return [
        colors(HARBOR, "dinnerware-set", "Stoneware Dinnerware Set, 16-Piece",
               "Service for four in reactive-glaze stoneware: dinner plates, salad plates, bowls, and mugs. Microwave and dishwasher safe.",
               ["Oat", "Slate Blue"], 79.99, ["dishwasher-safe"], {"Material": "Stoneware", "Pieces": "16 (service for 4)", "Microwave safe": "Yes"}),
        P(OWN_BRAND, "dinnerware-set", "White Porcelain Dinnerware Set, 12-Piece",
          "Classic white porcelain dishes, service for four: dinner plates, salad plates, and bowls. Microwave, oven, and dishwasher safe.",
          one(39.99, "12 pieces", "12PC"), ["dishwasher-safe", "oven-safe"], {"Material": "Porcelain", "Pieces": "12 (service for 4)", "Microwave safe": "Yes"}),
        P(OWN_BRAND, "flatware", "Stainless Steel Flatware Set, 20-Piece",
          "18/0 stainless flatware, service for four, with a mirror finish. Dishwasher safe.",
          one(24.99, "20 pieces", "20PC"), ["dishwasher-safe"], {"Material": "18/0 stainless steel", "Pieces": "20 (service for 4)"}),
        P(OWN_BRAND, "drinking-glasses", "Drinking Glasses, Set of 8",
          "Everyday glass tumblers, four 17 oz and four 13 oz. Dishwasher safe.",
          one(19.99, "8 glasses", "8PC"), ["dishwasher-safe"], {"Material": "Glass", "Capacity": "17 oz and 13 oz"}),
        P(HARBOR, "drinking-glasses", "Stemless Wine Glasses, Set of 4",
          "Thin-rim stemless wine glasses, 15 oz each. Dishwasher safe.",
          one(24.99, "4 glasses", "4PC"), ["dishwasher-safe"], {"Material": "Glass", "Capacity": "15 oz"}),
        P(HARBOR, "mugs", "Stoneware Coffee Mugs, Set of 4",
          "Large 16 oz reactive-glaze stoneware mugs. Microwave and dishwasher safe.",
          one(29.99, "4 mugs", "4PC"), ["dishwasher-safe"], {"Material": "Stoneware", "Capacity": "16 oz"}),
        colors(OWN_BRAND, "tumbler", "Insulated Tumbler with Straw, 30 oz",
               "Double-wall vacuum-insulated stainless tumbler that keeps drinks cold 24 hours, with a leak-resistant lid and reusable straw. BPA free; lid dishwasher safe.",
               ["Black", "White", "Lilac", "Sage"], 19.99, ["bpa-free"], {"Material": "Stainless steel", "Capacity": "30 oz", "Keeps cold": "24 hours", "Keeps hot": "6 hours"}),
    ]


def bedding_and_bath() -> list[ProductSeed]:
    out: list[ProductSeed] = []
    sheets = [  # (brand, name, colors, prices Twin-King, material, weave/thread, tags, note)
        (HARBOR, "Organic Cotton Percale Sheet Set", ("White", "Sage", "Slate"), (69.99, 89.99, 99.99, 119.99), "100% GOTS organic cotton", "Percale, 300 thread count", ["organic", "machine-washable"], "Crisp, cool, breathable percale that suits hot sleepers."),
        (HARBOR, "Cotton Sateen Sheet Set, 400 Thread Count", ("Ivory", "Charcoal"), (79.99, 99.99, 109.99, 129.99), "100% long-staple cotton", "Sateen, 400 thread count", ["machine-washable"], "Silky, smooth sateen with a subtle sheen."),
        (OWN_BRAND, "Microfiber Sheet Set", ("White", "Gray", "Navy"), (19.99, 24.99, 29.99, 34.99), "Brushed polyester microfiber", "Microfiber", ["machine-washable", "hypoallergenic"], "Soft, wrinkle-resistant brushed microfiber at a value price."),
        (HARBOR, "Flannel Sheet Set", ("Heather Gray", "Red Plaid"), (49.99, 59.99, 69.99, 79.99), "100% cotton flannel", "Flannel, 5 oz", ["machine-washable"], "Warm, brushed cotton flannel for cold nights."),
    ]  # fmt: skip
    for brand, name, color_names, prices, material, weave, tags, note in sheets:
        for color in color_names:
            out.append(P(
                brand, "sheet-set", f"{name}, {color}",
                f"{note} Includes a flat sheet, a fitted sheet with 16-inch deep pockets, and pillowcases (one with Twin, two with other sizes). Machine washable.",
                bed(*prices), tags,
                {"Material": material, "Weave": weave, "Color": color, "Pocket depth": "Fits mattresses up to 16 in"},
            ))
    out += [
        P(HARBOR, "comforter", "Down Alternative Comforter, White",
          "All-season down alternative comforter with hypoallergenic microfiber fill, box stitching, and corner loops for a duvet cover. Machine washable.",
          bed(49.99, 69.99, 79.99, names=("Twin", "Full/Queen", "King")), ["hypoallergenic", "machine-washable"],
          {"Fill": "Hypoallergenic polyester microfiber", "Warmth": "All season", "Color": "White"}),
        P(OWN_BRAND, "comforter", "Reversible Microfiber Comforter Set, Gray",
          "Value reversible comforter set with shams in soft gray microfiber. Machine washable.",
          bed(29.99, 39.99, 49.99, names=("Twin", "Full/Queen", "King")), ["machine-washable"],
          {"Fill": "Polyester", "Includes": "Comforter and 1-2 shams", "Color": "Gray / light gray"}),
        P(HARBOR, "duvet-cover", "Washed Cotton Duvet Cover Set",
          "Relaxed garment-washed cotton duvet cover with button closure and matching shams. Machine washable.",
          bed(79.99, 99.99, 119.99, names=("Twin", "Full/Queen", "King")), ["machine-washable"],
          {"Material": "100% cotton", "Closure": "Buttons", "Color": "Oat"}),
        P(HARBOR, "pillow", "Hypoallergenic Down Alternative Pillows, 2-Pack",
          "Medium-firm down alternative bed pillows with a cotton cover and hypoallergenic gel-fiber fill for back and side sleepers. Machine washable.",
          sz(("STD", "Standard/Queen, 2-pack", 39.99), ("KING", "King, 2-pack", 49.99)), ["hypoallergenic", "machine-washable"],
          {"Fill": "Gel fiber (down alternative)", "Firmness": "Medium firm", "Sleep position": "Back and side"}),
        P(HARBOR, "pillow", "Shredded Memory Foam Pillow, Adjustable",
          "Adjustable pillow filled with shredded memory foam you can add or remove for your ideal loft. Washable bamboo-derived cover.",
          sz(("QUEEN", "Queen", 49.99), ("KING", "King", 59.99)), ["hypoallergenic", "machine-washable"],
          {"Fill": "Shredded memory foam", "Firmness": "Adjustable", "Sleep position": "All"}),
        P(OWN_BRAND, "pillow", "Bed Pillows, 4-Pack",
          "Value standard-size polyester fiber pillows with medium support.",
          sz(("STD4", "Standard, 4-pack", 24.99)), ["machine-washable"],
          {"Fill": "Polyester fiber", "Firmness": "Medium"}),
        P(OWN_BRAND, "mattress-protector", "Waterproof Mattress Protector",
          "Quiet waterproof mattress protector with a soft terry top and deep-pocket skirt. Machine washable.",
          bed(19.99, 22.99, 24.99, 29.99), ["waterproof", "hypoallergenic", "machine-washable"],
          {"Material": "Cotton terry top, polyurethane backing", "Pocket depth": "Up to 18 in"}),
        P(HARBOR, "weighted-blanket", "Weighted Blanket, 15 lb",
          "Evenly weighted 15 lb blanket with glass beads in small stitched pockets and a removable, machine-washable cover. For adults 140-190 lb.",
          sz(("15LB", "60 x 80 in, 15 lb", 69.99)), ["machine-washable"],
          {"Weight": "15 lb", "Size": "60 x 80 in", "Fill": "Glass beads"}),
    ]
    for color in ("White", "Stone", "Navy"):
        out.append(P(
            HARBOR, "bath-towels", f"Turkish Cotton Bath Towels, {color}",
            "Plush, absorbent 650 GSM Turkish cotton towels that get softer with washing. Machine washable.",
            sz(("2BATH", "2 bath towels", 34.99), ("6PC", "6-piece set (2 bath, 2 hand, 2 washcloths)", 49.99)),
            ["machine-washable"], {"Material": "100% Turkish cotton", "Weight": "650 GSM", "Color": color},
        ))
    out += [
        colors(OWN_BRAND, "bath-towels", "Quick-Dry Cotton Bath Towel Set, 6-Piece",
               "Value 6-piece set of lightweight quick-dry cotton towels: 2 bath, 2 hand, 2 washcloths. Machine washable.",
               ["White", "Gray", "Aqua"], 19.99, ["machine-washable"], {"Material": "100% cotton", "Weight": "500 GSM"}),
        colors(HARBOR, "bath-mat", "Memory Foam Bath Mat",
               "Soft memory foam bath mat with a non-slip backing, 17 x 24 in. Machine washable.",
               ["White", "Gray"], 14.99, ["machine-washable"], {"Size": "17 x 24 in"}),
        P(HARBOR, "shower-curtain", "Waffle Weave Fabric Shower Curtain, 72 x 72 in",
          "Textured waffle-weave cotton blend shower curtain. Machine washable; use with a liner.",
          one(29.99), ["machine-washable"], {"Material": "Cotton/polyester blend", "Size": "72 x 72 in", "Liner needed": "Yes"}),
        P(OWN_BRAND, "shower-curtain", "PEVA Shower Curtain Liner, Clear",
          "Waterproof, PVC-free PEVA shower liner with magnets and rust-proof grommets.",
          one(6.99), ["waterproof"], {"Material": "PEVA (PVC free)", "Size": "72 x 72 in"}),
    ]
    return out


def decor_and_cleaning() -> list[ProductSeed]:
    candle_specs = {"Wax": "Soy blend", "Wick": "Cotton"}
    return [
        P(HARBOR, "candle", "Lavender & Eucalyptus Soy Candle",
          "Hand-poured soy wax candle with a calming lavender and eucalyptus scent, about 45 hours of burn time.",
          sz(("8OZ", "8 oz jar", 18.99)), [], {**candle_specs, "Scent": "Lavender & Eucalyptus", "Burn time": "About 45 hours"}),
        P(HARBOR, "candle", "Vanilla Bean Soy Candle",
          "Hand-poured soy wax candle with a warm vanilla bean scent, about 45 hours of burn time.",
          sz(("8OZ", "8 oz jar", 18.99)), [], {**candle_specs, "Scent": "Vanilla Bean", "Burn time": "About 45 hours"}),
        P(HARBOR, "candle", "Fresh Linen 3-Wick Candle",
          "Large three-wick candle with a clean fresh linen scent, about 40 hours of burn time.",
          sz(("14OZ", "14.5 oz jar", 24.99)), [], {**candle_specs, "Scent": "Fresh Linen", "Burn time": "About 40 hours"}),
        P(OWN_BRAND, "candle", "Unscented Pillar Candles, 3-Pack",
          "Dripless, unscented ivory pillar candles in 4, 6, and 8 in heights for the table or lanterns.",
          sz(("3PK", "3 candles", 14.99)), ["fragrance-free"], {"Wax": "Paraffin blend", "Scent": "Unscented", "Burn time": "40-80 hours each"}),
        P(OWN_BRAND, "candle", "Flameless LED Candles with Timer, 3-Pack",
          "Real-wax flameless LED pillar candles with a flickering glow and 6-hour timer. Batteries not included.",
          sz(("3PK", "3 candles", 19.99)), ["fragrance-free"], {"Power": "2 AA each (not included)", "Timer": "6 hours on, 18 off"}),
        P(OWN_BRAND, "storage-bins", "Fabric Storage Cubes, 6-Pack",
          "Collapsible 11-inch fabric cubes with handles that fit most cube shelves.",
          sz(("6PK", "6 cubes", 19.99)), [], {"Size": "11 x 11 x 11 in", "Material": "Non-woven fabric"}),
        P(OWN_BRAND, "storage-bins", "Clear Plastic Storage Bins with Latching Lids, 66 qt",
          "Stackable clear storage totes with latching lids for closets, garages, and under beds.",
          sz(("1PK", "1 bin", 12.99), ("4PK", "4 bins", 44.99)), [], {"Capacity": "66 qt", "Material": "Polypropylene", "Stackable": "Yes"}),
        P(HARBOR, "storage-bins", "Woven Seagrass Storage Baskets, Set of 3",
          "Handwoven seagrass baskets with handles in three nesting sizes.",
          sz(("3PC", "3 baskets", 44.99)), [], {"Material": "Seagrass", "Pieces": "3"}),
        P(AIRLOFT, "vacuum", "Cordless Stick Vacuum",
          "Lightweight cordless stick vacuum with up to 40 minutes of runtime, a LED brush head for carpets and hard floors, and a handheld mode.",
          one(149.99), ["cordless", "rechargeable"], {"Type": "Cordless stick", "Runtime": "Up to 40 minutes", "Filter": "Washable HEPA", "Weight": "5.5 lb", "Bin capacity": "0.6 L"}),
        P(AIRLOFT, "vacuum", "Cordless Stick Vacuum Pro with Self-Empty Base",
          "Powerful cordless stick vacuum with a self-emptying base, anti-tangle brush roll, and 60 minutes of runtime.",
          one(349.99), ["cordless", "rechargeable"], {"Type": "Cordless stick", "Runtime": "Up to 60 minutes", "Filter": "Sealed HEPA", "Weight": "6.2 lb", "Self-emptying": "Yes"}),
        P(AIRLOFT, "vacuum", "Bagless Upright Vacuum",
          "Corded bagless upright vacuum with strong suction for carpets, a 25 ft cord, and on-board tools.",
          one(129.99), [], {"Type": "Corded upright", "Cord length": "25 ft", "Filter": "HEPA", "Weight": "14 lb"}),
        P(AIRLOFT, "vacuum", "Cordless Handheld Vacuum",
          "Compact cordless handheld vacuum for cars, stairs, and crumbs, with a crevice tool and USB-C charging.",
          one(49.99), ["cordless", "rechargeable", "usb-c"], {"Type": "Handheld", "Runtime": "Up to 20 minutes", "Weight": "2.4 lb"}),
        P(AIRLOFT, "robot-vacuum", "Robot Vacuum with App Control",
          "Wi-Fi robot vacuum with lidar mapping, no-go zones, and 150 minutes of runtime that returns to its dock to recharge.",
          one(229.99), ["cordless", "rechargeable", "smart-home", "wireless"], {"Runtime": "Up to 150 minutes", "Navigation": "Lidar mapping", "Self-emptying": "No"}),
        P(AIRLOFT, "fan", "16-Inch Oscillating Pedestal Fan",
          "Adjustable-height pedestal fan with three speeds, 90-degree oscillation, and a remote.",
          one(39.99), [], {"Type": "Pedestal", "Blade size": "16 in", "Speeds": "3", "Remote": "Yes"}),
        P(AIRLOFT, "fan", "42-Inch Tower Fan with Remote",
          "Slim oscillating tower fan with four modes, an 8-hour timer, and a quiet sleep setting.",
          one(59.99), ["energy-efficient"], {"Type": "Tower", "Height": "42 in", "Speeds": "3", "Timer": "8 hours", "Remote": "Yes"}),
        P(OWN_BRAND, "fan", "20-Inch Box Fan",
          "Value three-speed box fan for windows and floors.",
          one(24.99), [], {"Type": "Box", "Blade size": "20 in", "Speeds": "3", "Remote": "No"}),
        P(AIRLOFT, "fan", "USB Desk Fan",
          "Quiet 6-inch desk fan powered by USB with a tilting head.",
          one(14.99), [], {"Type": "Desk", "Blade size": "6 in", "Power": "USB"}),
        P(AIRLOFT, "air-purifier", "HEPA Air Purifier for Small Rooms",
          "True HEPA air purifier for bedrooms and offices up to 200 sq ft that captures 99.97% of dust, pollen, and pet dander. Quiet sleep mode.",
          one(79.99), ["energy-efficient"], {"Room size": "Up to 200 sq ft", "Filter": "True HEPA + carbon", "CADR": "135 cfm", "Noise": "24 dB on sleep"}),
        P(AIRLOFT, "air-purifier", "Smart HEPA Air Purifier for Large Rooms",
          "Wi-Fi air purifier for rooms up to 1,000 sq ft with an air quality sensor, auto mode, and app control.",
          one(219.99), ["energy-efficient", "smart-home", "wireless"], {"Room size": "Up to 1,000 sq ft", "Filter": "True HEPA + carbon", "CADR": "300 cfm", "Air quality sensor": "Yes"}),
        P(AIRLOFT, "air-purifier-filter", "Replacement True HEPA Filter for Small-Room Air Purifier",
          "Replacement True HEPA and carbon filter for the Airloft small-room purifier. Replace every 6-8 months.",
          one(24.99), [], {"Fits": "Airloft HEPA Air Purifier for Small Rooms", "Replace every": "6-8 months"}),
        P(AIRLOFT, "humidifier", "Cool Mist Humidifier, 1 Gallon",
          "Ultrasonic cool mist humidifier with a 1-gallon tank that runs up to 30 hours, with a night light and auto shutoff.",
          one(39.99), [], {"Tank": "1 gal", "Runtime": "Up to 30 hours", "Room size": "Up to 400 sq ft"}),
    ]
# fmt: on


def products() -> list[ProductSeed]:
    return [
        *cookware(), *prep(), *appliances(), *tabletop(), *bedding_and_bath(),
        *decor_and_cleaning(),
    ]  # fmt: skip
