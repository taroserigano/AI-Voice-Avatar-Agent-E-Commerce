"""Clothing & Shoes: men's, women's, and kids' basics, activewear, sleepwear, outerwear, and
shoes.

Sizes are same-price variants (XS-XXL, kids' sizes, waist x inseam, or shoe sizes); colors
live in the title so each colorway is its own listing. Specs always state material, fit,
and care.
"""

from __future__ import annotations

from collections.abc import Iterable

from commerce.seed.data import ProductSeed
from commerce.seed.gen.common import cents, item, options, slugify

CAT = "clothing-shoes"
OWN_BRAND = "Serigan Mart Basics"  # store brand, value
DRIFTWOOD = "Driftwood Apparel"  # organic and premium basics, outerwear
TEMPO = "Tempo Athletics"  # activewear
STRIDEWELL = "Stridewell"  # shoes
PUDDLEJUMP = "Puddlejump"  # kids

ADULT = ["XS", "S", "M", "L", "XL", "XXL"]
MEN = ["S", "M", "L", "XL", "XXL"]
KIDS = ["XS (4-5)", "S (6-7)", "M (8)", "L (10-12)", "XL (14-16)"]
TODDLER = ["2T", "3T", "4T", "5T"]
MEN_JEANS = [
    "30W x 30L",
    "32W x 30L",
    "32W x 32L",
    "34W x 30L",
    "34W x 32L",
    "36W x 32L",
    "38W x 32L",
    "40W x 32L",
]
WOMEN_JEANS = ["0", "2", "4", "6", "8", "10", "12", "14", "16", "18"]
MEN_SHOES = [f"Size {s:g}" for s in (7, 7.5, 8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5, 12, 13)]
WOMEN_SHOES = [f"Size {s:g}" for s in (5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10, 11)]
KIDS_SHOES = ["Size 10 Toddler", "Size 11 Toddler", "Size 12 Little Kid", "Size 13 Little Kid",
              "Size 1 Big Kid", "Size 2 Big Kid", "Size 3 Big Kid", "Size 4 Big Kid"]  # fmt: skip

WASH = "Machine washable (cold, tumble dry low)"
MW = ["machine-washable"]
WICK = ["machine-washable", "moisture-wicking"]


def A(
    brand: str,
    product_type: str,
    title: str,
    description: str,
    sizes: list[str],
    dollars: float,
    tags: Iterable[str],
    material: str,
    fit: str,
    care: str = WASH,
    **extra: str,
) -> ProductSeed:
    """An apparel or shoe listing with same-price size variants."""
    slug = slugify(brand, title)
    specs = {
        "Material": material,
        "Fit": fit,
        "Care": care,
        **{k.replace("_", " ").capitalize(): v for k, v in extra.items()},
    }
    return item(
        category=CAT, product_type=product_type, brand=brand, title=title,
        description=description, variants_=options(CAT, slug, sizes, cents(dollars), "size"),
        tags=tags, specs=specs, slug=slug,
    )  # fmt: skip


def shoe(
    brand: str,
    product_type: str,
    title: str,
    description: str,
    sizes: list[str],
    dollars: float,
    tags: Iterable[str],
    upper: str,
    fit: str = "True to size, medium width",
    **extra: str,
) -> ProductSeed:
    return A(
        brand,
        product_type,
        title,
        description,
        sizes,
        dollars,
        tags,
        upper,
        fit,
        care="Spot clean",
        **extra,
    )


# fmt: off
def mens() -> list[ProductSeed]:
    return [
        A(OWN_BRAND, "t-shirt", "Men's Crewneck T-Shirts, 3-Pack, White", "Three everyday 100% cotton crewneck tees with a tag-free neck and a regular fit.", MEN, 14.99, MW, "100% cotton jersey", "Regular fit"),
        A(OWN_BRAND, "t-shirt", "Men's Crewneck T-Shirts, 3-Pack, Black", "Three everyday 100% cotton crewneck tees with a tag-free neck and a regular fit.", MEN, 14.99, MW, "100% cotton jersey", "Regular fit"),
        A(DRIFTWOOD, "t-shirt", "Men's Organic Cotton Pocket Tee, Navy", "Heavyweight organic cotton tee with a chest pocket and a relaxed fit that holds its shape.", MEN, 24.99, ["organic", *MW], "100% organic cotton", "Relaxed fit"),
        A(TEMPO, "t-shirt", "Men's Quick-Dry Training Tee, Charcoal", "Lightweight, moisture-wicking training tee with anti-odor treatment and flatlock seams.", MEN, 19.99, WICK, "100% recycled polyester", "Athletic fit"),
        A(OWN_BRAND, "polo", "Men's Pique Polo Shirt, Navy", "Classic cotton pique polo with a two-button placket and ribbed collar.", MEN, 12.99, MW, "100% cotton pique", "Regular fit"),
        A(OWN_BRAND, "polo", "Men's Pique Polo Shirt, White", "Classic cotton pique polo with a two-button placket and ribbed collar.", MEN, 12.99, MW, "100% cotton pique", "Regular fit"),
        A(TEMPO, "polo", "Men's Performance Golf Polo, Black", "Stretchy, moisture-wicking polo with UPF 30 sun protection for golf and warm days.", MEN, 29.99, WICK, "92% polyester, 8% spandex", "Athletic fit", sun_protection="UPF 30"),
        A(OWN_BRAND, "hoodie", "Men's Fleece Pullover Hoodie, Heather Gray", "Midweight fleece pullover hoodie with a kangaroo pocket and a lined hood.", MEN, 19.99, MW, "60% cotton, 40% polyester fleece", "Regular fit"),
        A(OWN_BRAND, "hoodie", "Men's Fleece Pullover Hoodie, Black", "Midweight fleece pullover hoodie with a kangaroo pocket and a lined hood.", MEN, 19.99, MW, "60% cotton, 40% polyester fleece", "Regular fit"),
        A(DRIFTWOOD, "hoodie", "Men's Organic Cotton French Terry Hoodie, Olive", "Garment-dyed organic cotton French terry hoodie that gets softer with every wash.", MEN, 59.99, ["organic", *MW], "100% organic cotton French terry", "Relaxed fit"),
        A(TEMPO, "joggers", "Men's Tech Joggers, Black", "Stretch-woven, moisture-wicking joggers with zip pockets and tapered cuffs for training and travel.", MEN, 39.99, WICK, "88% polyester, 12% spandex", "Tapered fit", inseam="30 in"),
        A(OWN_BRAND, "joggers", "Men's Fleece Joggers, Charcoal", "Soft fleece joggers with an elastic drawstring waist, pockets, and ribbed cuffs.", MEN, 16.99, MW, "60% cotton, 40% polyester fleece", "Regular fit", inseam="30 in"),
        A(OWN_BRAND, "jeans", "Men's Straight Fit Jeans, Medium Wash", "Five-pocket straight fit jeans in sturdy cotton denim with a little stretch.", MEN_JEANS, 24.99, MW, "98% cotton, 2% elastane denim", "Straight fit, sits at waist"),
        A(DRIFTWOOD, "jeans", "Men's Slim Fit Stretch Jeans, Dark Wash", "Slim fit jeans in premium stretch denim that recovers its shape all day.", MEN_JEANS, 59.99, MW, "92% cotton, 6% polyester, 2% elastane denim", "Slim fit, sits below waist"),
        A(TEMPO, "shorts", "Men's 7-Inch Running Shorts with Liner", "Lightweight, moisture-wicking running shorts with a brief liner, reflective trim, and a zip back pocket.", MEN, 24.99, WICK, "100% recycled polyester", "Regular fit", inseam="7 in"),
        A(OWN_BRAND, "socks", "Men's Cushioned Athletic Crew Socks, 6-Pair", "Cushioned cotton-blend crew socks with arch support and moisture-wicking yarns.", ["Men's shoe 6-12", "Men's shoe 12-16"], 12.99, WICK, "75% cotton, 23% polyester, 2% spandex", "Crew height"),
        A(OWN_BRAND, "underwear", "Men's Cotton Stretch Boxer Briefs, 5-Pack", "Soft cotton-stretch boxer briefs with a comfort waistband and a 5-inch inseam.", MEN, 19.99, MW, "95% cotton, 5% spandex", "Fitted", inseam="5 in"),
        A(OWN_BRAND, "pajamas", "Men's Flannel Pajama Pants, Blue Plaid", "Brushed cotton flannel sleep pants with an elastic drawstring waist and pockets.", MEN, 14.99, MW, "100% cotton flannel", "Relaxed fit"),
        A(DRIFTWOOD, "puffer-jacket", "Men's Packable Puffer Jacket, Black", "Lightweight, water-resistant puffer jacket with warm recycled synthetic insulation that packs into its own pocket.", MEN, 89.99, ["water-resistant", "recycled-materials", *MW], "Recycled nylon shell, recycled polyester insulation", "Regular fit", warmth="Midweight"),
        A(OWN_BRAND, "fleece-jacket", "Men's Full-Zip Fleece Jacket, Navy", "Warm polar fleece jacket with a full zip and zippered hand pockets.", MEN, 24.99, MW, "100% polyester fleece", "Regular fit"),
        A(OWN_BRAND, "rain-jacket", "Men's Waterproof Rain Jacket, Black", "Waterproof, breathable rain jacket with sealed seams, an adjustable hood, and pit zips.", MEN, 39.99, ["waterproof", *MW], "Polyester with waterproof coating", "Regular fit"),
    ]


def womens() -> list[ProductSeed]:
    legging = "Buttery-soft, moisture-wicking high-waisted leggings with a hidden waistband pocket and side pockets; squat-proof, 25-inch inseam."
    return [
        A(DRIFTWOOD, "t-shirt", "Women's Organic Cotton V-Neck Tee, White", "Soft organic cotton jersey V-neck with a relaxed drape.", ADULT, 22.99, ["organic", *MW], "100% organic cotton", "Relaxed fit"),
        A(OWN_BRAND, "t-shirt", "Women's Crewneck Tees, 2-Pack, Black & White", "Two stretchy cotton crewneck tees with a classic fit.", ADULT, 12.99, MW, "95% cotton, 5% spandex", "Classic fit"),
        A(TEMPO, "leggings", "Women's High-Waisted Leggings, 25 in, Black", legging, ADULT, 34.99, WICK, "75% nylon, 25% spandex", "High rise, compressive", inseam="25 in"),
        A(TEMPO, "leggings", "Women's High-Waisted Leggings, 25 in, Navy", legging, ADULT, 34.99, WICK, "75% nylon, 25% spandex", "High rise, compressive", inseam="25 in"),
        A(OWN_BRAND, "leggings", "Women's Cotton Stretch Leggings, Black", "Everyday cotton-stretch leggings with an elastic waist for lounging and layering. Not moisture wicking.", ADULT, 9.99, MW, "92% cotton, 8% spandex", "Mid rise", inseam="28 in"),
        A(TEMPO, "sports-bra", "Women's Medium-Support Sports Bra", "Medium-support racerback sports bra with removable pads and moisture-wicking fabric.", ADULT, 24.99, WICK, "80% nylon, 20% spandex", "Medium support"),
        A(TEMPO, "tank-top", "Women's Racerback Training Tank, Moisture-Wicking", "Lightweight, moisture-wicking racerback tank with a relaxed drape for workouts.", ADULT, 19.99, WICK, "100% recycled polyester", "Relaxed fit"),
        A(TEMPO, "shorts", "Women's 3-Inch Running Shorts", "Lightweight, moisture-wicking running shorts with a built-in brief liner and a zip pocket.", ADULT, 22.99, WICK, "100% recycled polyester", "Regular fit", inseam="3 in"),
        A(OWN_BRAND, "hoodie", "Women's Fleece Pullover Hoodie, Oatmeal", "Cozy midweight fleece hoodie with a kangaroo pocket.", ADULT, 19.99, MW, "60% cotton, 40% polyester fleece", "Relaxed fit"),
        A(DRIFTWOOD, "sweatshirt", "Women's Organic Cotton Crewneck Sweatshirt, Sage", "Relaxed crewneck sweatshirt in brushed organic cotton fleece.", ADULT, 49.99, ["organic", *MW], "100% organic cotton fleece", "Relaxed fit"),
        A(OWN_BRAND, "joggers", "Women's Fleece Joggers, Heather Gray", "Soft fleece joggers with a drawstring waist and cuffed ankles.", ADULT, 16.99, MW, "60% cotton, 40% polyester fleece", "Relaxed fit", inseam="28 in"),
        A(OWN_BRAND, "jeans", "Women's High-Rise Skinny Jeans, Dark Wash", "High-rise skinny jeans in stretch denim that holds its shape.", WOMEN_JEANS, 24.99, MW, "70% cotton, 28% polyester, 2% spandex denim", "Skinny, high rise", inseam="29 in"),
        A(DRIFTWOOD, "jeans", "Women's Straight Leg Jeans, Light Wash", "Rigid-look straight leg jeans with a touch of stretch and a vintage light wash.", WOMEN_JEANS, 59.99, MW, "98% cotton, 2% elastane denim", "Straight leg, high rise", inseam="28 in"),
        A(DRIFTWOOD, "shirt", "Women's Linen Button-Down Shirt, White", "Breezy washed linen button-down with a relaxed fit and roll-tab sleeves.", ADULT, 44.99, MW, "100% linen", "Relaxed fit"),
        A(OWN_BRAND, "socks", "Women's Ankle Socks, 6-Pair", "Cushioned cotton-blend low-cut socks with a heel tab.", ["Women's shoe 4-10"], 9.99, MW, "78% cotton, 20% polyester, 2% spandex", "Ankle height"),
        A(OWN_BRAND, "underwear", "Women's Cotton Hipster Underwear, 5-Pack", "Breathable cotton-stretch hipsters with a soft waistband.", ADULT, 14.99, MW, "95% cotton, 5% spandex", "Hipster"),
        A(OWN_BRAND, "pajamas", "Women's Jersey Pajama Set, Short Sleeve", "Soft jersey tee and pants pajama set with a drawstring waist.", ADULT, 19.99, MW, "60% cotton, 40% polyester", "Relaxed fit"),
        A(DRIFTWOOD, "puffer-jacket", "Women's Packable Puffer Jacket, Black", "Lightweight, water-resistant puffer with recycled synthetic insulation that packs into its own pocket.", ADULT, 89.99, ["water-resistant", "recycled-materials", *MW], "Recycled nylon shell, recycled polyester insulation", "Regular fit", warmth="Midweight"),
        A(DRIFTWOOD, "puffer-jacket", "Women's Long Hooded Puffer Coat, Camel", "Knee-length, water-resistant puffer coat with a hood and a two-way zipper for the coldest days.", ADULT, 129.99, ["water-resistant", *MW], "Nylon shell, polyester insulation", "Regular fit", warmth="Heavyweight"),
        A(OWN_BRAND, "rain-jacket", "Women's Waterproof Rain Jacket, Yellow", "Waterproof, breathable rain jacket with sealed seams and an adjustable hood.", ADULT, 39.99, ["waterproof", *MW], "Polyester with waterproof coating", "Regular fit"),
        A(OWN_BRAND, "fleece-jacket", "Women's Sherpa Fleece Jacket, Cream", "Cozy high-pile sherpa fleece jacket with a full zip and pockets.", ADULT, 29.99, MW, "100% polyester sherpa", "Relaxed fit"),
    ]


def kids() -> list[ProductSeed]:
    return [
        A(PUDDLEJUMP, "t-shirt", "Kids' Organic Cotton Tees, 3-Pack, Assorted", "Three soft organic cotton crewneck tees in bright solid colors.", KIDS, 19.99, ["organic", "kids", *MW], "100% organic cotton", "Regular fit"),
        A(OWN_BRAND, "t-shirt", "Kids' Short Sleeve Graphic Tee, Dinosaurs", "Cotton-blend graphic tee with a dinosaur print.", KIDS, 6.99, ["kids", *MW], "60% cotton, 40% polyester", "Regular fit"),
        A(PUDDLEJUMP, "t-shirt", "Toddler Short Sleeve Tees, 4-Pack", "Four soft cotton tees for toddlers with easy-on shoulder snaps.", TODDLER, 16.99, ["kids", *MW], "100% cotton", "Regular fit"),
        A(OWN_BRAND, "hoodie", "Kids' Fleece Pullover Hoodie, Navy", "Warm fleece hoodie with a kangaroo pocket for school and play.", KIDS, 12.99, ["kids", *MW], "60% cotton, 40% polyester fleece", "Regular fit"),
        A(OWN_BRAND, "joggers", "Kids' Fleece Joggers, Gray", "Soft fleece joggers with an elastic waist and cuffs.", KIDS, 9.99, ["kids", *MW], "60% cotton, 40% polyester fleece", "Regular fit"),
        A(PUDDLEJUMP, "jeans", "Kids' Stretch Jeans with Adjustable Waist, Medium Wash", "Durable stretch denim jeans with reinforced knees and an adjustable inner waistband.", KIDS, 16.99, ["kids", *MW], "98% cotton, 2% spandex denim", "Straight fit"),
        A(OWN_BRAND, "leggings", "Girls' Cotton Leggings, 2-Pack", "Two pairs of soft cotton-stretch leggings, black and heather gray.", KIDS, 11.99, ["kids", *MW], "92% cotton, 8% spandex", "Slim fit"),
        A(TEMPO, "shorts", "Kids' Athletic Shorts, Moisture-Wicking", "Lightweight, moisture-wicking mesh shorts with an elastic waist for sports and recess.", KIDS, 12.99, ["kids", *WICK], "100% polyester mesh", "Regular fit"),
        A(OWN_BRAND, "socks", "Kids' Crew Socks, 10-Pair", "Ten pairs of cushioned cotton-blend crew socks.", ["Kids' S (shoe 7-10)", "Kids' M (shoe 10.5-4)", "Kids' L (shoe 4-8)"], 11.99, ["kids", *MW], "75% cotton, 23% polyester, 2% spandex", "Crew height"),
        A(PUDDLEJUMP, "pajamas", "Kids' Snug-Fit Cotton Pajama Set, Space Print", "Two-piece long-sleeve pajama set in soft cotton. Snug fitting (not flame resistant) as required for children's cotton sleepwear.", KIDS, 14.99, ["kids", *MW], "100% cotton", "Snug fit"),
        A(PUDDLEJUMP, "puffer-jacket", "Kids' Water-Resistant Puffer Jacket", "Warm, water-resistant puffer jacket with a fleece-lined hood and reflective details.", KIDS, 39.99, ["kids", "water-resistant", *MW], "Nylon shell, polyester insulation", "Regular fit", warmth="Midweight"),
        A(PUDDLEJUMP, "rain-jacket", "Kids' Waterproof Rain Jacket", "Waterproof rain jacket with sealed seams, a brimmed hood, and reflective trim.", KIDS, 29.99, ["kids", "waterproof", *MW], "Polyester with waterproof coating", "Regular fit"),
    ]


def shoes() -> list[ProductSeed]:
    return [
        shoe(STRIDEWELL, "running-shoes", "Men's Cushioned Running Shoes, Black", "Daily running shoes with plush foam cushioning, a breathable engineered mesh upper, and a durable rubber outsole.", MEN_SHOES, 79.99, [], "Engineered mesh", cushioning="Max", drop="10 mm", weight="10.2 oz"),
        shoe(STRIDEWELL, "running-shoes", "Women's Cushioned Running Shoes, Gray & Coral", "Daily running shoes with plush foam cushioning, a breathable engineered mesh upper, and a durable rubber outsole.", WOMEN_SHOES, 79.99, [], "Engineered mesh", cushioning="Max", drop="10 mm", weight="8.4 oz"),
        shoe(STRIDEWELL, "running-shoes", "Men's Lightweight Road Racing Shoes", "Lightweight, responsive road shoes with a nylon plate and energy-return foam for tempo runs and race day.", MEN_SHOES, 119.99, [], "Recycled mesh", cushioning="Responsive", drop="8 mm", weight="7.9 oz"),
        shoe(STRIDEWELL, "running-shoes", "Women's Lightweight Road Racing Shoes", "Lightweight, responsive road shoes with a nylon plate and energy-return foam for tempo runs and race day.", WOMEN_SHOES, 119.99, [], "Recycled mesh", cushioning="Responsive", drop="8 mm", weight="6.6 oz"),
        shoe(OWN_BRAND, "running-shoes", "Men's Athletic Running Shoes, Black", "Value lightweight running and gym shoes with a knit upper and cushioned sole.", MEN_SHOES, 29.99, [], "Knit textile", cushioning="Moderate"),
        shoe(OWN_BRAND, "running-shoes", "Women's Athletic Running Shoes, White", "Value lightweight running and gym shoes with a knit upper and cushioned sole.", WOMEN_SHOES, 29.99, [], "Knit textile", cushioning="Moderate"),
        A(STRIDEWELL, "sneakers", "Women's Slip-On Knit Walking Shoes", "Slip-on walking shoes with a stretchy knit upper and a memory foam insole. Machine washable on gentle.", WOMEN_SHOES, 59.99, MW, "Recycled knit textile", "True to size", care="Machine washable (gentle, air dry)"),
        shoe(STRIDEWELL, "sneakers", "Men's Leather Court Sneakers, White", "Minimal low-top sneakers in full-grain leather with a cushioned footbed and a stitched cupsole.", MEN_SHOES, 69.99, [], "Full-grain leather"),
        shoe(OWN_BRAND, "sneakers", "Women's Canvas Slip-On Sneakers, Navy", "Classic canvas slip-ons with elastic side gores and a padded insole.", WOMEN_SHOES, 19.99, [], "Cotton canvas"),
        shoe(OWN_BRAND, "sandals", "Men's Slide Sandals", "Cushioned one-piece EVA slides for the pool, gym, and around the house. Waterproof.", MEN_SHOES, 14.99, ["waterproof"], "EVA foam"),
        shoe(STRIDEWELL, "sandals", "Women's Strappy Footbed Sandals", "Adjustable strappy sandals with a contoured cork footbed and a suede lining.", WOMEN_SHOES, 39.99, [], "Leather straps, cork footbed"),
        shoe(STRIDEWELL, "sandals", "Men's Sport Sandals", "Quick-drying, water-friendly sport sandals with adjustable webbing straps and a grippy outsole for hikes and river crossings.", MEN_SHOES, 49.99, ["waterproof"], "Polyester webbing"),
        shoe(STRIDEWELL, "boots", "Men's Waterproof Hiking Boots", "Mid-height hiking boots with a waterproof breathable membrane, ankle support, and a lugged rubber outsole.", MEN_SHOES, 99.99, ["waterproof"], "Leather and mesh", waterproof="Waterproof membrane"),
        shoe(STRIDEWELL, "boots", "Women's Waterproof Hiking Boots", "Mid-height hiking boots with a waterproof breathable membrane, ankle support, and a lugged rubber outsole.", WOMEN_SHOES, 99.99, ["waterproof"], "Leather and mesh", waterproof="Waterproof membrane"),
        shoe(STRIDEWELL, "boots", "Women's Chelsea Boots, Brown", "Pull-on leather Chelsea boots with elastic side panels and a lug sole.", WOMEN_SHOES, 79.99, ["water-resistant"], "Water-resistant leather"),
        shoe(STRIDEWELL, "boots", "Women's Waterproof Winter Snow Boots", "Insulated waterproof snow boots rated to -20°F with a faux-fur collar and a slip-resistant outsole.", WOMEN_SHOES, 69.99, ["waterproof"], "Waterproof nylon and rubber", temperature_rating="-20°F"),
        shoe(STRIDEWELL, "boots", "Men's Steel Toe Work Boots", "Water-resistant leather work boots with a steel safety toe, electrical hazard protection, and an oil-resistant outsole.", MEN_SHOES, 109.99, ["water-resistant"], "Water-resistant leather", safety_toe="Steel"),
        shoe(OWN_BRAND, "slippers", "Women's Memory Foam Slippers", "Plush faux-fur slippers with memory foam and an indoor/outdoor sole.", WOMEN_SHOES[2::2], 12.99, [], "Polyester faux fur"),
        shoe(OWN_BRAND, "slippers", "Men's Moccasin Slippers", "Suede-look moccasin slippers with a warm fleece lining and a rubber sole.", MEN_SHOES[2::2], 19.99, [], "Microsuede, fleece lining"),
        shoe(PUDDLEJUMP, "sneakers", "Kids' Light-Up Sneakers", "Sneakers with LED lights in the sole that flash with every step and easy hook-and-loop straps.", KIDS_SHOES, 29.99, ["kids"], "Synthetic leather and mesh"),
        shoe(PUDDLEJUMP, "sneakers", "Kids' Hook-and-Loop Sneakers", "Durable everyday sneakers with hook-and-loop straps kids can do themselves and a toe bumper.", KIDS_SHOES, 24.99, ["kids"], "Synthetic leather and mesh"),
        shoe(PUDDLEJUMP, "boots", "Kids' Rain Boots", "Waterproof rubber rain boots with pull-on handles and a grippy sole.", KIDS_SHOES, 19.99, ["kids", "waterproof"], "Natural rubber"),
        shoe(PUDDLEJUMP, "sandals", "Kids' Water Shoes", "Quick-dry slip-on water shoes that protect feet at the beach, pool, and splash pad.", KIDS_SHOES, 14.99, ["kids", "waterproof"], "Stretch mesh, rubber sole"),
        shoe(PUDDLEJUMP, "boots", "Kids' Waterproof Snow Boots", "Insulated waterproof snow boots rated to -25°F with a hook-and-loop closure.", KIDS_SHOES, 34.99, ["kids", "waterproof"], "Waterproof nylon and rubber", temperature_rating="-25°F"),
    ]
# fmt: on


def products() -> list[ProductSeed]:
    return [*mens(), *womens(), *kids(), *shoes()]
