"""Beauty & Personal Care: hair care, body wash and soap, lotion, face care, sunscreen, lip,
deodorant, oral care, shaving, hair styling and tools, makeup basics, and nail care.

Tags are the filters shoppers use here (sulfate free, fragrance free, cruelty free, vegan,
aluminum free); specs hold hair type, SPF, filter type, water resistance, and alcohol.
"""

from __future__ import annotations

from collections.abc import Iterable

from commerce.seed.data import ProductSeed
from commerce.seed.gen.common import Size, cents, item, options, slugify

CAT = "beauty"
VERDANT = "Verdant Botanicals"  # natural, vegan, cruelty free
CLEARWELL = "Clearwell Skin"  # dermatologist-developed, sensitive skin
OWN_BRAND = "Serigan Mart Basics"  # store brand, value
PEARLWELL = "Pearlwell"  # oral care
KEENEDGE = "Keenedge"  # shaving and grooming
SOLSTICE = "Solstice Beauty"  # makeup, nails, hair tools

CLEAN = ["cruelty-free", "vegan"]
GENTLE = ["fragrance-free", "hypoallergenic", "sensitive-skin"]


def one(dollars: float, label: str = "Each", code: str = "EA") -> list[Size]:
    return [Size(code, label, cents(dollars))]


def floz(*rows: tuple[float, float]) -> list[Size]:
    """Bottle sizes from (fluid ounces, dollars) rows."""
    return [Size(f"{oz:g}OZ".replace(".", "_"), f"{oz:g} fl oz", cents(p)) for oz, p in rows]


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


def shades(
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
        description=description, variants_=options(CAT, slug, names, cents(dollars), "shade"),
        tags=tags, specs=specs, slug=slug,
    )  # fmt: skip


def sunscreen(
    brand: str,
    title: str,
    description: str,
    sizes: list[Size],
    tags: Iterable[str],
    spf: int,
    filter_: str,
    actives: str,
    water: str,
    form: str,
) -> ProductSeed:
    return P(brand, "sunscreen", title, description, sizes, tags, {
        "SPF": str(spf), "Filter": filter_, "Active ingredients": actives,
        "Broad spectrum": "Yes", "Water resistance": water, "Form": form,
    })  # fmt: skip


# fmt: off
def hair() -> list[ProductSeed]:
    sf = ["sulfate-free", *CLEAN]
    return [
        P(VERDANT, "shampoo", "Curl Defining Sulfate-Free Shampoo",
          "Sulfate-free, silicone-free shampoo with coconut oil and shea butter that cleanses curls without stripping moisture. For curly and coily hair.",
          floz((12, 12.99)), sf, {"Hair type": "Curly, coily", "Sulfates": "Sulfate free", "Silicones": "Silicone free", "Scent": "Coconut"}),
        P(VERDANT, "conditioner", "Curl Defining Conditioner",
          "Rich, sulfate-free conditioner with shea butter and flaxseed that detangles and defines curls with less frizz.",
          floz((12, 12.99)), sf, {"Hair type": "Curly, coily", "Sulfates": "Sulfate free", "Silicones": "Silicone free", "Scent": "Coconut"}),
        P(VERDANT, "shampoo", "Color Care Sulfate-Free Shampoo",
          "Gentle sulfate-free shampoo with sunflower extract that helps color-treated hair keep its shine and tone longer.",
          floz((12, 12.99)), sf, {"Hair type": "Color-treated", "Sulfates": "Sulfate free", "Scent": "Citrus blossom"}),
        P(VERDANT, "conditioner", "Color Care Conditioner",
          "Sulfate-free conditioner for color-treated hair with UV filters and argan oil.",
          floz((12, 12.99)), sf, {"Hair type": "Color-treated", "Sulfates": "Sulfate free", "Scent": "Citrus blossom"}),
        P(VERDANT, "shampoo", "Volumizing Sulfate-Free Shampoo for Fine Hair",
          "Lightweight sulfate-free shampoo with rice protein that adds body to fine, thin hair without weighing it down.",
          floz((12, 12.99)), sf, {"Hair type": "Fine, thin", "Sulfates": "Sulfate free", "Scent": "Green tea"}),
        P(VERDANT, "conditioner", "Volumizing Lightweight Conditioner for Fine Hair",
          "Weightless conditioner that detangles fine hair while keeping volume.",
          floz((12, 12.99)), sf, {"Hair type": "Fine, thin", "Sulfates": "Sulfate free", "Scent": "Green tea"}),
        P(CLEARWELL, "shampoo", "Fragrance-Free Gentle Shampoo",
          "Sulfate-free, fragrance-free shampoo for sensitive scalps with no dyes or essential oils. Dermatologist tested and hypoallergenic. Safe for all hair types.",
          floz((12, 10.99)), ["sulfate-free", "cruelty-free", *GENTLE], {"Hair type": "All, sensitive scalp", "Sulfates": "Sulfate free", "Scent": "Unscented"}),
        P(CLEARWELL, "conditioner", "Fragrance-Free Gentle Conditioner",
          "Fragrance-free conditioner for sensitive scalps with no dyes or essential oils. Hypoallergenic.",
          floz((12, 10.99)), ["sulfate-free", "cruelty-free", *GENTLE], {"Hair type": "All, sensitive scalp", "Sulfates": "Sulfate free", "Scent": "Unscented"}),
        P(OWN_BRAND, "shampoo", "Moisturizing Shampoo, Coconut",
          "Value moisturizing shampoo with a rich lather and coconut scent for normal to dry hair. Contains sulfates.",
          floz((28, 3.99)), [], {"Hair type": "Normal to dry", "Sulfates": "Contains sodium laureth sulfate", "Scent": "Coconut"}),
        P(OWN_BRAND, "conditioner", "Moisturizing Conditioner, Coconut",
          "Value moisturizing conditioner with a coconut scent for normal to dry hair.",
          floz((28, 3.99)), [], {"Hair type": "Normal to dry", "Scent": "Coconut"}),
        P(OWN_BRAND, "shampoo", "2-in-1 Shampoo & Conditioner, Classic Clean",
          "Value 2-in-1 shampoo and conditioner with a clean scent. Contains sulfates.",
          floz((25.4, 3.99)), [], {"Hair type": "All", "Sulfates": "Contains sodium lauryl sulfate", "Scent": "Classic Clean"}),
        P(OWN_BRAND, "shampoo", "Clarifying Shampoo",
          "Deep-cleaning clarifying shampoo that removes product buildup and hard water minerals. Use once a week; contains sulfates.",
          floz((12, 4.49)), [], {"Hair type": "All (weekly use)", "Sulfates": "Contains sodium lauryl sulfate", "Scent": "Lemon"}),
        P(OWN_BRAND, "dry-shampoo", "Dry Shampoo, Fresh Scent",
          "Aerosol dry shampoo that absorbs oil and refreshes hair between washes.",
          one(5.99, "5 oz can", "5OZ"), [], {"Hair type": "All", "Scent": "Fresh"}),
        P(OWN_BRAND, "shampoo", "Kids' Tear-Free 3-in-1 Shampoo, Conditioner & Body Wash, Berry",
          "Tear-free 3-in-1 for kids that shampoos, conditions, and washes in one step, with a berry scent.",
          floz((18, 4.99)), ["tear-free", "kids"], {"Hair type": "Kids, all", "Scent": "Berry"}),
        P(VERDANT, "hair-styling", "Curl Cream Leave-In Conditioner",
          "Leave-in curl cream with aloe and shea that defines curls, fights frizz, and adds moisture without crunch.",
          floz((8, 11.99)), ["sulfate-free", *CLEAN], {"Hair type": "Curly, coily", "Hold": "Soft"}),
        P(OWN_BRAND, "hair-styling", "Strong Hold Hair Gel",
          "Value alcohol-free strong-hold styling gel with no flaking.",
          one(2.99, "16 oz", "16OZ"), [], {"Hold": "Strong", "Alcohol": "Alcohol free"}),
        P(OWN_BRAND, "hair-styling", "Flexible Hold Hairspray",
          "Aerosol hairspray with a flexible, brushable hold and humidity resistance.",
          one(3.99, "11 oz", "11OZ"), [], {"Hold": "Flexible"}),
        P(SOLSTICE, "hair-dryer", "Ionic Hair Dryer, 1875W",
          "1875-watt ionic hair dryer with three heat and two speed settings, a cool shot, and a concentrator and diffuser.",
          one(29.99), [], {"Wattage": "1875 W", "Heat settings": "3", "Attachments": "Concentrator, diffuser"}),
        P(SOLSTICE, "flat-iron", "Ceramic Flat Iron, 1 in",
          "Ceramic flat iron with adjustable heat up to 450°F, dual voltage, and auto shutoff.",
          one(34.99), [], {"Plate": "1 in ceramic", "Max temperature": "450°F", "Auto shutoff": "60 minutes"}),
    ]


def body_and_face() -> list[ProductSeed]:
    return [
        P(VERDANT, "body-wash", "Eucalyptus Mint Body Wash",
          "Sulfate-free, plant-based body wash with eucalyptus and peppermint essential oils.",
          floz((16, 9.99)), ["sulfate-free", *CLEAN], {"Scent": "Eucalyptus Mint", "Sulfates": "Sulfate free"}),
        P(CLEARWELL, "body-wash", "Fragrance-Free Hydrating Body Wash",
          "Creamy, soap-free body wash with ceramides and glycerin for dry and sensitive skin. Fragrance free and hypoallergenic.",
          floz((20, 11.99)), ["sulfate-free", "cruelty-free", *GENTLE], {"Scent": "Unscented", "Sulfates": "Sulfate free", "Skin type": "Dry, sensitive"}),
        P(OWN_BRAND, "body-wash", "Ocean Breeze Body Wash",
          "Value moisturizing body wash with a fresh ocean breeze scent.",
          floz((22, 3.99)), [], {"Scent": "Ocean Breeze", "Sulfates": "Contains sulfates"}),
        P(OWN_BRAND, "body-wash", "Men's 3-in-1 Body Wash, Cedar",
          "Value 3-in-1 hair, face, and body wash for men with a cedar scent.",
          floz((18, 4.49)), [], {"Scent": "Cedar", "Sulfates": "Contains sulfates"}),
        P(OWN_BRAND, "body-wash", "Shea Butter Moisturizing Body Wash",
          "Value creamy body wash with shea butter for dry skin, lightly scented.",
          floz((22, 3.99)), [], {"Scent": "Shea butter", "Skin type": "Dry"}),
        P(VERDANT, "bar-soap", "Oatmeal & Honey Bar Soap",
          "Cold-process bar soap with colloidal oatmeal and honey for gentle exfoliation. Contains honey, so not vegan.",
          one(5.99, "5 oz bar", "5OZ"), ["cruelty-free", "sulfate-free"], {"Scent": "Oatmeal honey", "Vegan": "No (contains honey)"}),
        P(VERDANT, "bar-soap", "Activated Charcoal Bar Soap",
          "Vegan cold-process bar soap with activated charcoal and tea tree oil for oily skin.",
          one(5.99, "5 oz bar", "5OZ"), ["sulfate-free", *CLEAN], {"Scent": "Tea tree", "Skin type": "Oily"}),
        P(CLEARWELL, "bar-soap", "Unscented Sensitive Skin Beauty Bars, 4-Pack",
          "Mild, fragrance-free cleansing bars with one-quarter moisturizing cream that won't dry sensitive skin. Hypoallergenic.",
          one(6.99, "4 x 4 oz bars", "4PK"), ["cruelty-free", *GENTLE], {"Scent": "Unscented", "Skin type": "Sensitive"}),
        P(OWN_BRAND, "bar-soap", "Moisturizing Beauty Bars, 8-Pack, Original",
          "Value moisturizing beauty bars with a light classic scent.",
          one(5.99, "8 x 3.75 oz bars", "8PK"), [], {"Scent": "Original"}),
        P(CLEARWELL, "body-lotion", "Daily Moisturizing Lotion, Fragrance-Free",
          "Lightweight, non-greasy daily lotion with ceramides and hyaluronic acid for 24-hour hydration. Fragrance free, hypoallergenic, and non-comedogenic.",
          floz((16, 13.99)), ["cruelty-free", *GENTLE], {"Scent": "Unscented", "Skin type": "Normal to dry, sensitive", "Key ingredients": "Ceramides, hyaluronic acid"}),
        P(CLEARWELL, "body-lotion", "Moisturizing Cream for Very Dry Skin",
          "Rich, fragrance-free moisturizing cream in a tub for very dry, rough skin on face and body.",
          one(16.99, "16 oz tub", "16OZ"), ["cruelty-free", *GENTLE], {"Scent": "Unscented", "Skin type": "Very dry, sensitive", "Key ingredients": "Ceramides, petrolatum"}),
        P(OWN_BRAND, "body-lotion", "Cocoa Butter Body Lotion",
          "Value body lotion with cocoa butter and vitamin E and a warm cocoa scent.",
          floz((20, 4.99)), [], {"Scent": "Cocoa butter", "Skin type": "Dry"}),
        P(OWN_BRAND, "body-lotion", "Fragrance-Free Daily Body Lotion",
          "Value fragrance-free lotion for sensitive skin that absorbs quickly.",
          floz((20, 4.99)), ["fragrance-free", "sensitive-skin"], {"Scent": "Unscented", "Skin type": "All, sensitive"}),
        P(VERDANT, "body-lotion", "Whipped Shea Body Butter, Vanilla",
          "Whipped shea and cocoa butter body cream with a warm vanilla scent. Vegan.",
          one(14.99, "8 oz jar", "8OZ"), CLEAN, {"Scent": "Vanilla", "Skin type": "Dry"}),
        P(CLEARWELL, "face-wash", "Gentle Hydrating Facial Cleanser",
          "Non-foaming, fragrance-free cream cleanser with ceramides that cleans without disrupting the skin barrier. For normal to dry skin.",
          floz((16, 13.99)), ["cruelty-free", "sulfate-free", *GENTLE], {"Skin type": "Normal to dry", "Texture": "Cream, non-foaming", "Scent": "Unscented"}),
        P(CLEARWELL, "face-wash", "Foaming Facial Cleanser for Normal to Oily Skin",
          "Fragrance-free gel-to-foam cleanser with niacinamide that removes excess oil without over-drying.",
          floz((16, 13.99)), ["cruelty-free", *GENTLE], {"Skin type": "Normal to oily", "Texture": "Foaming gel", "Scent": "Unscented"}),
        P(VERDANT, "face-wash", "Vitamin C Brightening Gel Cleanser",
          "Vegan gel cleanser with vitamin C and orange peel extract for dull skin.",
          floz((6, 12.99)), ["sulfate-free", *CLEAN], {"Skin type": "All", "Texture": "Gel", "Scent": "Citrus"}),
        P(OWN_BRAND, "face-wash", "Micellar Cleansing Water",
          "No-rinse micellar water that removes makeup and cleanses in one step. Fragrance free.",
          floz((13.5, 5.99)), ["fragrance-free", "sensitive-skin"], {"Skin type": "All", "Rinse": "No rinse"}),
        P(OWN_BRAND, "makeup-remover", "Makeup Remover Wipes, 3-Pack",
          "Soft pre-moistened wipes that remove makeup, including waterproof mascara.",
          one(6.99, "3 packs of 25 (75 wipes)", "3PK"), [], {"Count": "75"}),
        P(CLEARWELL, "face-moisturizer", "Daily Facial Moisturizing Lotion, Oil-Free",
          "Oil-free, fragrance-free daily face lotion with niacinamide and ceramides. No SPF; pair with sunscreen during the day.",
          floz((3, 14.99)), ["cruelty-free", *GENTLE], {"SPF": "None", "Skin type": "All, sensitive", "Oil free": "Yes"}),
        P(CLEARWELL, "face-moisturizer", "Overnight Recovery Night Cream",
          "Rich, fragrance-free night cream with peptides and ceramides that restores moisture while you sleep.",
          one(16.99, "1.7 oz jar", "1_7OZ"), ["cruelty-free", *GENTLE], {"SPF": "None", "Skin type": "Normal to dry"}),
        P(OWN_BRAND, "face-moisturizer", "Oil-Free Face Moisturizer",
          "Value lightweight, oil-free face moisturizer for everyday use.",
          floz((4, 6.99)), [], {"SPF": "None", "Oil free": "Yes"}),
        P(VERDANT, "face-serum", "Hyaluronic Acid Hydrating Serum",
          "Fragrance-free serum with 2% hyaluronic acid and vitamin B5 for plump, hydrated skin. Vegan.",
          floz((1, 19.99)), ["fragrance-free", *CLEAN], {"Key ingredients": "Hyaluronic acid 2%, vitamin B5", "Skin type": "All"}),
        P(VERDANT, "face-serum", "Retinol Night Serum, 0.3%",
          "Gentle 0.3% encapsulated retinol serum with squalane for smoother skin. Use at night; vegan.",
          floz((1, 24.99)), CLEAN, {"Key ingredients": "Retinol 0.3%, squalane", "Use": "Night only"}),
        P(CLEARWELL, "eye-cream", "Hydrating Eye Cream",
          "Fragrance-free eye cream with caffeine and ceramides that hydrates and brightens under-eye skin.",
          one(15.99, "0.5 oz tube", "0_5OZ"), ["cruelty-free", *GENTLE], {"Key ingredients": "Caffeine, ceramides"}),
    ]


def sun_and_lip() -> list[ProductSeed]:
    zinc = "Mineral (zinc oxide)"
    chem = "Chemical"
    return [
        sunscreen(CLEARWELL, "Mineral Sunscreen Lotion SPF 50",
                  "Broad-spectrum SPF 50 mineral sunscreen with 21% zinc oxide, fragrance free and gentle on sensitive skin. Water resistant for 80 minutes.",
                  floz((3, 14.99)), ["cruelty-free", "water-resistant", *GENTLE], 50, zinc, "Zinc oxide 21%", "80 minutes", "Lotion"),
        sunscreen(CLEARWELL, "Kids' Mineral Sunscreen Lotion SPF 50",
                  "Tear-free, fragrance-free SPF 50 mineral sunscreen for kids with zinc oxide. Water resistant for 80 minutes.",
                  floz((3, 13.99)), ["kids", "tear-free", "cruelty-free", "water-resistant", *GENTLE], 50, zinc, "Zinc oxide 20%", "80 minutes", "Lotion"),
        sunscreen(CLEARWELL, "Tinted Mineral Face Sunscreen SPF 30",
                  "Sheer tinted SPF 30 mineral face sunscreen that blends into most skin tones with no white cast. Not water resistant.",
                  floz((1.7, 17.99)), ["cruelty-free", *GENTLE], 30, "Mineral (zinc oxide, titanium dioxide)", "Zinc oxide 11%, titanium dioxide 3%", "Not water resistant", "Tinted lotion"),
        sunscreen(VERDANT, "Mineral Sunscreen Lotion SPF 30",
                  "Vegan, reef-conscious SPF 30 mineral sunscreen made with non-nano zinc oxide. Water resistant for 80 minutes.",
                  floz((3, 15.99)), ["water-resistant", *CLEAN], 30, zinc, "Zinc oxide 20% (non-nano)", "80 minutes", "Lotion"),
        sunscreen(VERDANT, "Mineral Sunscreen Stick SPF 50, Unscented",
                  "Vegan, fragrance-free SPF 50 mineral sunscreen stick for face and body with non-nano zinc oxide. Water resistant for 80 minutes.",
                  one(12.99, "0.5 oz stick", "0_5OZ"), ["water-resistant", "fragrance-free", *CLEAN], 50, zinc, "Zinc oxide 22% (non-nano)", "80 minutes", "Stick"),
        sunscreen(OWN_BRAND, "Mineral Sunscreen Lotion SPF 50",
                  "Value SPF 50 mineral sunscreen with zinc oxide and titanium dioxide. Fragrance free; water resistant for 80 minutes.",
                  floz((6, 9.99)), ["fragrance-free", "water-resistant"], 50, "Mineral (zinc oxide, titanium dioxide)", "Zinc oxide 9%, titanium dioxide 6%", "80 minutes", "Lotion"),
        sunscreen(OWN_BRAND, "Sport Sunscreen Lotion SPF 50",
                  "Value broad-spectrum SPF 50 chemical sunscreen that stays on through sweat. Water resistant for 80 minutes.",
                  floz((8, 7.99)), ["water-resistant"], 50, chem, "Avobenzone 3%, homosalate 10%, octisalate 5%, octocrylene 10%", "80 minutes", "Lotion"),
        sunscreen(OWN_BRAND, "Sunscreen Spray SPF 30",
                  "Value lightweight continuous-spray SPF 30 chemical sunscreen. Water resistant for 80 minutes.",
                  one(8.99, "6 oz can", "6OZ"), ["water-resistant"], 30, chem, "Avobenzone 3%, homosalate 8%, octisalate 5%, octocrylene 6%", "80 minutes", "Spray"),
        sunscreen(OWN_BRAND, "Kids' Sunscreen Spray SPF 50",
                  "Value continuous-spray SPF 50 chemical sunscreen for kids. Water resistant for 80 minutes.",
                  one(8.99, "6 oz can", "6OZ"), ["kids", "water-resistant"], 50, chem, "Avobenzone 3%, homosalate 10%, octisalate 5%, octocrylene 7%", "80 minutes", "Spray"),
        P(OWN_BRAND, "after-sun", "After-Sun Aloe Vera Gel",
          "Cooling after-sun gel with aloe vera to soothe and moisturize skin after sun exposure.",
          floz((16, 4.99)), [], {"Key ingredients": "Aloe vera"}),
        P(VERDANT, "lip-balm", "Beeswax Lip Balm, 4-Pack",
          "Moisturizing lip balm made with beeswax and peppermint, vanilla, citrus, and coconut. Contains beeswax, so not vegan.",
          one(7.99, "4 tubes", "4PK"), ["cruelty-free"], {"Wax": "Beeswax", "SPF": "None"}),
        P(VERDANT, "lip-balm", "Vegan Lip Balm, Unscented",
          "Vegan lip balm made with candelilla wax and shea butter and no fragrance or flavor.",
          one(3.99, "1 tube", "1PK"), ["fragrance-free", *CLEAN], {"Wax": "Candelilla (plant based)", "SPF": "None"}),
        P(CLEARWELL, "lip-balm", "Lip Repair Balm, Fragrance-Free",
          "Fragrance-free healing lip balm with ceramides and petrolatum for severely dry, chapped lips.",
          one(6.99, "0.35 oz tube", "1PK"), ["cruelty-free", *GENTLE], {"SPF": "None"}),
        P(OWN_BRAND, "lip-balm", "SPF 15 Lip Balm, 3-Pack",
          "Value moisturizing lip balm with broad-spectrum SPF 15 in a mint flavor.",
          one(3.99, "3 tubes", "3PK"), [], {"SPF": "15"}),
    ]


def deodorant_and_oral() -> list[ProductSeed]:
    alfree = ["aluminum-free", *CLEAN]
    return [
        P(VERDANT, "deodorant", "Aluminum-Free Deodorant, Lavender",
          "Aluminum-free, baking-soda-free deodorant with arrowroot and coconut oil that neutralizes odor. Not an antiperspirant.",
          one(10.99, "2.65 oz stick", "STICK"), alfree, {"Type": "Deodorant (not antiperspirant)", "Aluminum": "Aluminum free", "Scent": "Lavender", "Baking soda": "None"}),
        P(VERDANT, "deodorant", "Aluminum-Free Deodorant, Unscented",
          "Aluminum-free, fragrance-free deodorant for sensitive underarms. Not an antiperspirant.",
          one(10.99, "2.65 oz stick", "STICK"), [*alfree, "fragrance-free", "sensitive-skin"], {"Type": "Deodorant (not antiperspirant)", "Aluminum": "Aluminum free", "Scent": "Unscented", "Baking soda": "None"}),
        P(VERDANT, "deodorant", "Aluminum-Free Deodorant, Cedar & Sage",
          "Aluminum-free deodorant with a woodsy cedar and sage scent. Not an antiperspirant.",
          one(10.99, "2.65 oz stick", "STICK"), alfree, {"Type": "Deodorant (not antiperspirant)", "Aluminum": "Aluminum free", "Scent": "Cedar & Sage"}),
        P(OWN_BRAND, "deodorant", "Antiperspirant Deodorant, Clean Scent",
          "Value 48-hour antiperspirant deodorant that reduces sweat with aluminum zirconium.",
          one(3.99, "2.6 oz stick", "STICK"), [], {"Type": "Antiperspirant", "Aluminum": "Contains aluminum zirconium", "Protection": "48 hours", "Scent": "Clean"}),
        P(OWN_BRAND, "deodorant", "Men's Antiperspirant Deodorant, Sport",
          "Value 48-hour antiperspirant deodorant for men with a sport scent.",
          one(3.99, "2.7 oz stick", "STICK"), [], {"Type": "Antiperspirant", "Aluminum": "Contains aluminum zirconium", "Protection": "48 hours", "Scent": "Sport"}),
        P(CLEARWELL, "deodorant", "Sensitive Skin Antiperspirant, Fragrance-Free",
          "Fragrance-free clinical-strength antiperspirant for sensitive skin. Contains aluminum to reduce sweat.",
          one(6.99, "2.6 oz stick", "STICK"), ["cruelty-free", *GENTLE], {"Type": "Antiperspirant", "Aluminum": "Contains aluminum zirconium", "Protection": "72 hours", "Scent": "Unscented"}),
        P(PEARLWELL, "toothpaste", "Cavity Protection Fluoride Toothpaste, Mint",
          "Everyday fluoride toothpaste that strengthens enamel and fights cavities.",
          one(2.99, "6 oz tube", "6OZ"), [], {"Fluoride": "Sodium fluoride 0.24%", "Benefit": "Cavity protection", "Flavor": "Mint"}),
        P(PEARLWELL, "toothpaste", "Advanced Whitening Fluoride Toothpaste",
          "Fluoride toothpaste with hydrated silica and hydrogen peroxide that removes surface stains for whiter teeth.",
          one(4.99, "4 oz tube", "4OZ"), [], {"Fluoride": "Sodium fluoride 0.24%", "Benefit": "Whitening", "Flavor": "Fresh mint"}),
        P(PEARLWELL, "toothpaste", "Sensitivity Relief Fluoride Toothpaste",
          "Fluoride toothpaste with 5% potassium nitrate that builds protection against hot and cold sensitivity with twice-daily brushing.",
          one(5.99, "4 oz tube", "4OZ"), [], {"Fluoride": "Sodium fluoride 0.24%", "Benefit": "Sensitive teeth", "Active": "Potassium nitrate 5%", "Flavor": "Mild mint"}),
        P(PEARLWELL, "toothpaste", "Kids' Fluoride Toothpaste, Bubble Fruit",
          "Kids' cavity-fighting fluoride toothpaste with a mild bubble fruit flavor, for ages 2 and up.",
          one(2.99, "4.2 oz tube", "4OZ"), ["kids"], {"Fluoride": "Sodium fluoride 0.24%", "Benefit": "Cavity protection", "Ages": "2+", "Flavor": "Bubble fruit"}),
        P(VERDANT, "toothpaste", "Fluoride-Free Toothpaste, Peppermint",
          "Fluoride-free toothpaste with xylitol and baking soda and a natural peppermint flavor. Vegan.",
          one(5.99, "4.7 oz tube", "4OZ"), CLEAN, {"Fluoride": "Fluoride free", "Benefit": "Fresh breath", "Flavor": "Peppermint"}),
        P(OWN_BRAND, "toothpaste", "Fluoride Toothpaste, Mint, 3-Pack",
          "Value three-pack of everyday cavity protection fluoride toothpaste.",
          one(4.99, "3 x 6 oz tubes", "3PK"), [], {"Fluoride": "Sodium fluoride 0.24%", "Benefit": "Cavity protection", "Flavor": "Mint"}),
        P(PEARLWELL, "mouthwash", "Alcohol-Free Fluoride Mouthwash, Mint",
          "Alcohol-free fluoride rinse that strengthens enamel and freshens breath without the burn.",
          floz((33.8, 5.99)), [], {"Alcohol": "Alcohol free", "Fluoride": "Yes", "Flavor": "Mint"}),
        P(PEARLWELL, "mouthwash", "Antiseptic Mouthwash, Original",
          "Antiseptic mouthwash that kills germs that cause bad breath and plaque. Contains alcohol.",
          floz((33.8, 5.49)), [], {"Alcohol": "Contains alcohol (21.6%)", "Fluoride": "No", "Flavor": "Original"}),
        P(OWN_BRAND, "mouthwash", "Alcohol-Free Mouthwash, Clean Mint",
          "Value alcohol-free mouthwash for fresh breath.",
          floz((33.8, 3.99)), [], {"Alcohol": "Alcohol free", "Fluoride": "No", "Flavor": "Clean mint"}),
        P(PEARLWELL, "toothbrush", "Soft Manual Toothbrushes, 4-Pack",
          "Soft-bristle manual toothbrushes with a tongue cleaner and non-slip grip.",
          one(4.99, "4 toothbrushes", "4PK"), [], {"Bristles": "Soft", "Type": "Manual"}),
        P(PEARLWELL, "toothbrush", "Kids' Soft Toothbrushes, 4-Pack",
          "Small-head, extra-soft toothbrushes with easy-grip handles for kids ages 2 and up.",
          one(3.99, "4 toothbrushes", "4PK"), ["kids"], {"Bristles": "Extra soft", "Type": "Manual", "Ages": "2+"}),
        P(VERDANT, "toothbrush", "Bamboo Toothbrushes, 4-Pack",
          "Toothbrushes with biodegradable bamboo handles and soft plant-based bristles.",
          one(7.99, "4 toothbrushes", "4PK"), ["biodegradable", *CLEAN], {"Bristles": "Soft", "Handle": "Bamboo (biodegradable)", "Type": "Manual"}),
        P(PEARLWELL, "electric-toothbrush", "Sonic Rechargeable Toothbrush Pro",
          "Rechargeable sonic toothbrush with pressure sensor, four modes, a 2-minute timer, 30-day battery, and travel case.",
          one(79.99), ["rechargeable", "usb-c"], {"Modes": "4", "Battery life": "30 days", "Pressure sensor": "Yes", "Charging": "USB-C"}),
        P(PEARLWELL, "toothbrush-heads", "Sonic Replacement Brush Heads, 4-Pack",
          "Replacement brush heads for Pearlwell sonic toothbrushes. Replace every 3 months.",
          one(19.99, "4 heads", "4PK"), [], {"Fits": "Pearlwell Sonic toothbrushes", "Bristles": "Soft"}),
        P(PEARLWELL, "dental-floss", "Mint Waxed Dental Floss, 2-Pack",
          "Shred-resistant waxed mint floss, 2 x 55 yards.",
          one(3.99, "2 x 55 yd", "2PK"), [], {"Length": "110 yd total", "Flavor": "Mint"}),
        P(PEARLWELL, "dental-floss", "Floss Picks, 150 Count",
          "Mint-flavored dental floss picks with a built-in toothpick end, for on-the-go flossing.",
          one(3.49, "150 picks", "150CT"), [], {"Count": "150", "Flavor": "Mint"}),
    ]


def shaving_makeup_nails() -> list[ProductSeed]:
    return [
        P(KEENEDGE, "razor", "Men's 5-Blade Razor with 2 Cartridges",
          "Five-blade razor with a pivoting head, a lubricating strip, and a precision trimmer on the back. Includes 2 cartridges.",
          one(10.99, "Handle + 2 cartridges", "KIT"), [], {"Blades": "5", "Cartridges included": "2"}),
        P(KEENEDGE, "razor-cartridges", "5-Blade Razor Refill Cartridges, 8 Count",
          "Refill cartridges that fit Keenedge 5-blade men's and women's razor handles.",
          one(19.99, "8 cartridges", "8CT"), [], {"Blades": "5", "Fits": "Keenedge 5-blade handles"}),
        P(KEENEDGE, "razor", "Women's 5-Blade Razor with 2 Cartridges",
          "Five-blade women's razor with a shea butter moisture bar and a curved handle. Includes 2 cartridges.",
          one(10.99, "Handle + 2 cartridges", "KIT"), [], {"Blades": "5", "Cartridges included": "2"}),
        P(OWN_BRAND, "razor", "Disposable Razors, 3-Blade, 12-Pack",
          "Value 3-blade disposable razors with a pivoting head and aloe strip.",
          one(7.99, "12 razors", "12PK"), [], {"Blades": "3", "Type": "Disposable"}),
        P(KEENEDGE, "razor", "Stainless Steel Safety Razor with 10 Blades",
          "Plastic-free double-edge safety razor in stainless steel with 10 replacement blades.",
          one(29.99, "Razor + 10 blades", "KIT"), [], {"Blades": "Single double-edge blade", "Material": "Stainless steel"}),
        P(KEENEDGE, "beard-trimmer", "Rechargeable Beard Trimmer",
          "Cordless rechargeable beard trimmer with 20 length settings, a washable head, and 90-minute runtime.",
          one(39.99), ["cordless", "rechargeable", "usb-c", "water-resistant"], {"Length settings": "20 (0.5-10 mm)", "Runtime": "90 minutes", "Charging": "USB-C"}),
        P(KEENEDGE, "shaving-cream", "Sensitive Shave Gel, Fragrance-Free",
          "Fragrance-free shave gel with aloe for smooth shaves on sensitive skin.",
          one(3.99, "7 oz can", "7OZ"), ["fragrance-free", "sensitive-skin"], {"Scent": "Unscented", "Form": "Gel"}),
        P(OWN_BRAND, "shaving-cream", "Classic Shaving Cream",
          "Value rich-lather shaving cream with a classic scent.",
          one(2.49, "11 oz can", "11OZ"), [], {"Scent": "Classic", "Form": "Foam"}),
        P(SOLSTICE, "mascara", "Lengthening Mascara, Black",
          "Buildable lengthening mascara with a flexible brush that separates lashes without clumps. Vegan and cruelty free.",
          one(8.99), CLEAN, {"Color": "Black", "Waterproof": "No"}),
        shades(SOLSTICE, "foundation", "Liquid Foundation, Medium Coverage",
               "Lightweight, fragrance-free liquid foundation with a natural satin finish and medium, buildable coverage. Vegan and cruelty free.",
               ["Fair", "Light", "Light Medium", "Medium", "Tan", "Deep"], 11.99, ["fragrance-free", *CLEAN],
               {"Coverage": "Medium", "Finish": "Satin", "SPF": "None"}),
        shades(SOLSTICE, "lip-color", "Moisturizing Satin Lipstick",
               "Creamy satin lipstick with shea butter for comfortable color. Vegan and cruelty free.",
               ["Nude Rose", "Berry", "Classic Red", "Mauve"], 7.99, CLEAN, {"Finish": "Satin"}),
        P(SOLSTICE, "makeup-brushes", "Makeup Brush Set, 10-Piece",
          "Ten synthetic-bristle makeup brushes for foundation, powder, and eyes, with a travel pouch. Vegan and cruelty free.",
          one(14.99, "10 brushes", "10PC"), CLEAN, {"Bristles": "Synthetic", "Pieces": "10"}),
        P(OWN_BRAND, "makeup-sponges", "Makeup Blending Sponges, 4-Pack",
          "Value latex-free makeup blending sponges for liquid and cream products.",
          one(5.99, "4 sponges", "4PK"), [], {"Latex": "Latex free"}),
        shades(SOLSTICE, "nail-polish", "Long-Wear Nail Polish",
               "Chip-resistant long-wear nail polish with a glossy finish that lasts up to 7 days. Vegan and cruelty free.",
               ["Ballet Pink", "Cherry Red", "Navy", "Sheer Nude", "Clear Top Coat"], 6.99, CLEAN, {"Wear": "Up to 7 days", "Finish": "Glossy"}),
        P(OWN_BRAND, "nail-polish-remover", "Acetone-Free Nail Polish Remover",
          "Value acetone-free nail polish remover with vitamin E that is gentle on nails.",
          floz((6, 2.99)), [], {"Acetone": "Acetone free"}),
        P(OWN_BRAND, "nail-care", "Nail Clipper Set, 3 Pieces",
          "Stainless steel fingernail clipper, toenail clipper, and nail file.",
          one(4.99, "3 pieces", "3PC"), [], {"Material": "Stainless steel", "Pieces": "3"}),
    ]
# fmt: on


def products() -> list[ProductSeed]:
    return [
        *hair(),
        *body_and_face(),
        *sun_and_lip(),
        *deodorant_and_oral(),
        *shaving_makeup_nails(),
    ]
