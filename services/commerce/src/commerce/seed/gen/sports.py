"""Sports & Fitness: yoga, strength (dumbbells, kettlebells, bands), cardio, fitness trackers,
water bottles, bikes and helmets, balls, racquets, and swim.

Weights, ball sizes, and bottle capacities are variants so "a 20 lb kettlebell" or "a size
4 soccer ball" resolves to one purchasable option.
"""

from __future__ import annotations

from collections.abc import Iterable

from commerce.seed.data import ProductSeed
from commerce.seed.gen.common import Size, cents, item, options, slugify

CAT = "sports"
TEMPO = "Tempo Athletics"  # fitness, premium
OWN_BRAND = "Serigan Mart Sport"  # store brand, value
COURTLINE = "Courtline"  # balls and racquets
SPOKEHAVEN = "Spokehaven"  # bikes


def one(dollars: float, label: str = "Each", code: str = "EA") -> list[Size]:
    return [Size(code, label, cents(dollars))]


def weights(unit: str, *rows: tuple[int, float]) -> list[Size]:
    """Weight variants from (pounds, dollars) rows, e.g. weights("pair", (5, 16.99))."""
    return [Size(f"{lb}LB", f"{lb} lb {unit}".strip(), cents(p)) for lb, p in rows]


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


def opts(
    brand: str,
    product_type: str,
    title: str,
    description: str,
    names: list[str],
    dollars: float,
    attribute: str,
    tags: Iterable[str] = (),
    specs: dict[str, str] | None = None,
) -> ProductSeed:
    slug = slugify(brand, title)
    return item(
        category=CAT, product_type=product_type, brand=brand, title=title,
        description=description, variants_=options(CAT, slug, names, cents(dollars), attribute),
        tags=tags, specs=specs, slug=slug,
    )  # fmt: skip


# fmt: off
def fitness() -> list[ProductSeed]:
    return [
        P(TEMPO, "yoga-mat", "Extra Thick Yoga Mat, 10 mm",
          "Extra-thick 10 mm foam mat that cushions knees and joints for yoga, Pilates, and floor exercises. Includes a carry strap.",
          one(29.99), [], {"Thickness": "10 mm", "Size": "72 x 24 in", "Material": "NBR foam", "Latex": "Latex free"}),
        P(OWN_BRAND, "yoga-mat", "Yoga Mat, 4 mm",
          "Lightweight 4 mm non-slip yoga mat for beginners and travel.",
          one(12.99), [], {"Thickness": "4 mm", "Size": "68 x 24 in", "Material": "PVC-free TPE"}),
        P(TEMPO, "yoga-mat", "Natural Rubber Pro Yoga Mat, 5 mm",
          "Professional 5 mm mat with a natural tree rubber base and a polyurethane top that grips even when sweaty. Contains natural rubber latex.",
          one(79.99), [], {"Thickness": "5 mm", "Size": "71 x 26 in", "Material": "Natural rubber, polyurethane top", "Latex": "Contains natural rubber latex"}),
        P(TEMPO, "yoga-block", "Cork Yoga Blocks, 2-Pack",
          "Two firm, sustainable cork yoga blocks for support and alignment in standing and seated poses.",
          one(24.99, "2 blocks", "2PK"), [], {"Material": "Cork", "Size": "9 x 6 x 4 in"}),
        P(OWN_BRAND, "yoga-block", "Foam Yoga Blocks, 2-Pack",
          "Lightweight high-density foam yoga blocks.",
          one(9.99, "2 blocks", "2PK"), [], {"Material": "EVA foam", "Size": "9 x 6 x 4 in"}),
        P(TEMPO, "yoga-strap", "Cotton Yoga Strap, 8 ft",
          "Durable cotton yoga strap with a metal D-ring buckle for stretching and flexibility.",
          one(8.99), ["machine-washable"], {"Length": "8 ft", "Material": "Cotton"}),
        P(OWN_BRAND, "dumbbells", "Neoprene Dumbbells, Pair",
          "Pair of neoprene-coated dumbbells with a comfortable grip and hexagon ends that won't roll. Choose your weight.",
          weights("pair", (3, 12.99), (5, 16.99), (8, 22.99), (10, 27.99), (12, 32.99), (15, 39.99)), [],
          {"Material": "Cast iron, neoprene coating", "Sold as": "Pair"}),
        P(TEMPO, "dumbbells", "Rubber Hex Dumbbell, Single",
          "Rubber-encased hex dumbbell with a knurled chrome handle for home gyms. Sold individually; choose your weight.",
          weights("", (10, 19.99), (15, 27.99), (20, 34.99), (25, 42.99), (30, 49.99), (40, 64.99), (50, 79.99)), [],
          {"Material": "Cast iron, rubber coating", "Sold as": "Single dumbbell"}),
        P(TEMPO, "kettlebell", "Cast Iron Kettlebell",
          "Solid cast iron kettlebell with a wide, smooth handle and a flat base, color coded by weight.",
          weights("", (10, 24.99), (15, 32.99), (20, 39.99), (25, 47.99), (35, 59.99), (50, 84.99)), [],
          {"Material": "Solid cast iron, powder coat"}),
        P(TEMPO, "resistance-bands", "Resistance Tube Set with Handles, 11-Piece",
          "Five stackable resistance tubes (10-50 lb) with handles, ankle straps, and a door anchor for full-body workouts.",
          one(29.99, "11 pieces", "11PC"), [], {"Resistance": "10-50 lb each, stackable to 150 lb", "Pieces": "11"}),
        P(OWN_BRAND, "resistance-bands", "Fabric Booty Bands, 3-Pack",
          "Three non-slip fabric loop bands in light, medium, and heavy that won't roll up during glute workouts. Latex free.",
          one(12.99, "3 bands", "3PK"), ["machine-washable"], {"Resistance": "Light, medium, heavy", "Material": "Fabric (latex free)"}),
        P(TEMPO, "resistance-bands", "Pull-Up Assist Bands, Set of 4",
          "Four long latex power bands from 15 to 125 lb for assisted pull-ups, mobility, and strength work.",
          one(34.99, "4 bands", "4PK"), [], {"Resistance": "15-125 lb", "Length": "41 in", "Material": "Natural latex"}),
        P(TEMPO, "exercise-ball", "Anti-Burst Exercise Ball with Pump",
          "Anti-burst stability ball for core work and desk sitting, with a hand pump. Choose the size for your height.",
          [Size("55CM", "55 cm (height 5'0\"-5'5\")", cents(19.99)), Size("65CM", "65 cm (height 5'6\"-6'0\")", cents(22.99)), Size("75CM", "75 cm (height 6'1\"+)", cents(24.99))],
          [], {"Weight capacity": "2,000 lb static", "Pump included": "Yes"}),
        P(TEMPO, "medicine-ball", "Soft Medicine Ball",
          "Soft-shell medicine ball for slams, wall balls, and core throws.",
          weights("", (6, 24.99), (10, 32.99), (14, 39.99)), [], {"Diameter": "14 in", "Shell": "Soft vinyl"}),
        P(OWN_BRAND, "jump-rope", "Basic PVC Jump Rope",
          "Adjustable 9 ft PVC jump rope with foam handles.",
          one(6.99), [], {"Length": "9 ft adjustable", "Handles": "Foam"}),
        P(TEMPO, "jump-rope", "Weighted Jump Rope, 1 lb",
          "Weighted 1 lb jump rope that builds upper-body strength while you do cardio.",
          one(24.99), [], {"Rope weight": "1 lb", "Length": "9 ft adjustable"}),
        P(TEMPO, "fitness-tracker", "Tempo Fit Band Fitness Tracker",
          "Slim fitness band that tracks steps, heart rate, sleep, and 20 workout modes, with a 10-day battery and 5 ATM water resistance for swimming.",
          one(49.99), ["wireless", "bluetooth", "rechargeable", "water-resistant"],
          {"Battery life": "Up to 10 days", "Water resistance": "5 ATM (swim-proof)", "GPS": "Connected (uses phone)", "Display": "1.1 in color AMOLED"}),
        P(TEMPO, "fitness-tracker", "Tempo Pace GPS Running Smartwatch",
          "GPS running watch with built-in GPS, wrist heart rate, training plans, and music controls. 5 ATM water resistant.",
          one(149.99), ["wireless", "bluetooth", "rechargeable", "water-resistant"],
          {"Battery life": "Up to 14 days (20 hours GPS)", "Water resistance": "5 ATM (swim-proof)", "GPS": "Built-in", "Display": "1.3 in always-on"}),
        P(TEMPO, "fitness-tracker", "Tempo Kids' Activity Tracker",
          "Kid-friendly activity tracker for ages 6 and up with step goals, sleep tracking, and chore reminders. Swim-proof.",
          one(34.99), ["kids", "wireless", "bluetooth", "rechargeable", "water-resistant"],
          {"Battery life": "Up to 5 days", "Water resistance": "5 ATM (swim-proof)", "Ages": "6+"}),
        P(TEMPO, "water-bottle", "Insulated Water Bottle with Straw Lid",
          "Vacuum-insulated stainless bottle with a leak-proof straw lid that keeps drinks cold 24 hours. BPA free; lid is dishwasher safe.",
          [Size("20OZ", "20 oz", cents(19.99)), Size("32OZ", "32 oz", cents(24.99)), Size("40OZ", "40 oz", cents(29.99))],
          ["bpa-free"], {"Material": "18/8 stainless steel", "Keeps cold": "24 hours", "Keeps hot": "12 hours", "Lid": "Straw lid, leak proof"}),
        P(OWN_BRAND, "water-bottle", "Squeeze Sports Bottles, 24 oz, 2-Pack",
          "BPA-free squeezable sports bottles with a push-pull cap. Dishwasher safe.",
          one(9.99, "2 bottles", "2PK"), ["bpa-free", "dishwasher-safe"], {"Material": "BPA-free LDPE plastic", "Capacity": "24 oz", "Insulated": "No"}),
        P(TEMPO, "water-bottle", "Glass Water Bottle with Silicone Sleeve, 20 oz",
          "Borosilicate glass bottle with a protective silicone sleeve and a bamboo lid. BPA free.",
          one(17.99), ["bpa-free", "dishwasher-safe"], {"Material": "Borosilicate glass", "Capacity": "20 oz", "Insulated": "No"}),
        P(OWN_BRAND, "water-bottle", "Kids' Insulated Water Bottle, 14 oz",
          "Leak-proof insulated kids' bottle with a flip-up straw that keeps water cold for 12 hours. BPA free.",
          one(12.99), ["bpa-free", "kids"], {"Material": "Stainless steel", "Capacity": "14 oz", "Keeps cold": "12 hours"}),
        P(TEMPO, "water-bottle", "Half-Gallon Water Bottle with Time Markers, 64 oz",
          "BPA-free 64 oz bottle with hourly time markers and a carry strap to help you hit daily water goals.",
          one(19.99), ["bpa-free"], {"Material": "BPA-free Tritan plastic", "Capacity": "64 oz", "Insulated": "No"}),
    ]


def bikes_balls_racquets() -> list[ProductSeed]:
    return [
        P(SPOKEHAVEN, "bike", "26-Inch Mountain Bike, 21-Speed",
          "Hardtail mountain bike with a steel frame, front suspension fork, 21-speed twist shifters, and front and rear disc brakes. Fits riders 5'4\"-6'0\".",
          one(299.99), [], {"Wheel size": "26 in", "Speeds": "21", "Brakes": "Mechanical disc", "Rider height": "5'4\"-6'0\""}),
        P(SPOKEHAVEN, "bike", "700c Hybrid Commuter Bike, 7-Speed",
          "Lightweight aluminum hybrid bike with an upright position, 7 speeds, and rack mounts for commuting and paths.",
          one(349.99), [], {"Wheel size": "700c", "Speeds": "7", "Brakes": "Linear pull", "Rider height": "5'5\"-6'1\""}),
        P(SPOKEHAVEN, "bike", "Kids' 16-Inch Bike with Training Wheels",
          "Kids' bike with removable training wheels, a coaster brake plus hand brake, and a chain guard. Ages 4-6.",
          one(119.99), ["kids"], {"Wheel size": "16 in", "Speeds": "1", "Ages": "4-6", "Rider height": "3'7\"-4'0\""}),
        P(SPOKEHAVEN, "bike", "Kids' 20-Inch Bike, 6-Speed",
          "Kids' 20-inch bike with 6 speeds, hand brakes, and knobby tires. Ages 7-10.",
          one(169.99), ["kids"], {"Wheel size": "20 in", "Speeds": "6", "Ages": "7-10", "Rider height": "4'0\"-4'8\""}),
        P(SPOKEHAVEN, "balance-bike", "12-Inch Balance Bike",
          "Pedal-free balance bike that teaches toddlers to steer and balance, with an adjustable seat. Ages 18 months to 4 years.",
          one(69.99), ["kids"], {"Wheel size": "12 in", "Ages": "18 months-4 years", "Weight": "6.6 lb"}),
        P(SPOKEHAVEN, "bike-helmet", "Adult Bike Helmet",
          "Lightweight in-mold bike helmet with 18 vents, a dial-fit system, and a rear LED light. Meets CPSC bike helmet standards.",
          [Size("SM", "S/M (54-58 cm)", cents(34.99)), Size("LXL", "L/XL (58-62 cm)", cents(34.99))], [],
          {"Certification": "CPSC", "Vents": "18", "Light": "Rear LED"}),
        P(SPOKEHAVEN, "bike-helmet", "Kids' Bike Helmet",
          "Kids' multi-sport helmet with a dial-fit system and a fun print. Meets CPSC bike helmet standards.",
          [Size("TOD", "Toddler (48-52 cm), ages 1-3", cents(24.99)), Size("YTH", "Youth (52-56 cm), ages 5-8", cents(24.99))], ["kids"],
          {"Certification": "CPSC"}),
        P(SPOKEHAVEN, "bike-lock", "U-Lock with 4 ft Cable",
          "Hardened steel U-lock with a 4 ft braided cable and a mounting bracket.",
          one(29.99), [], {"Shackle": "16 mm hardened steel", "Cable": "4 ft braided steel"}),
        P(SPOKEHAVEN, "bike-light", "Rechargeable Bike Light Set",
          "USB-C rechargeable front and rear bike lights with 5 modes; the front light puts out 400 lumens.",
          one(19.99), ["rechargeable", "usb-c", "water-resistant"], {"Front": "400 lumens", "Rear": "30 lumens", "Water resistance": "IPX5"}),
        P(COURTLINE, "basketball", "Official Size 7 Indoor/Outdoor Basketball",
          "Composite leather basketball with deep channels for grip on indoor courts and outdoor blacktop. Official men's size.",
          one(29.99, "Size 7 (29.5 in)", "SIZE7"), [], {"Size": "7 (29.5 in), official men's", "Cover": "Composite leather", "Use": "Indoor/outdoor"}),
        opts(COURTLINE, "basketball", "Rubber Outdoor Basketball",
             "Durable rubber basketball built for outdoor courts. Choose your size.",
             ["Size 5 (27.5 in, ages 9-11)", "Size 6 (28.5 in, women's and ages 12+)", "Size 7 (29.5 in, men's official)"], 14.99, "size",
             [], {"Cover": "Rubber", "Use": "Outdoor"}),
        opts(COURTLINE, "soccer-ball", "Machine-Stitched Soccer Ball",
             "Durable machine-stitched soccer ball for practice and games. Size 3 for under 8, size 4 for ages 8-12, size 5 for 13 and up.",
             ["Size 3 (under 8)", "Size 4 (ages 8-12)", "Size 5 (ages 13+)"], 19.99, "size",
             [], {"Cover": "Synthetic leather", "Construction": "Machine stitched"}),
        opts(COURTLINE, "football", "Composite Football",
             "Composite leather football with a grippy pebbled surface and raised laces.",
             ["Official (ages 14+)", "Junior (ages 9-13)", "Pee Wee (ages 6-9)"], 24.99, "size",
             [], {"Cover": "Composite leather"}),
        P(COURTLINE, "volleyball", "Indoor/Outdoor Volleyball",
          "Soft-touch official-size volleyball for gym and beach play.",
          one(19.99), [], {"Size": "Official (size 5)", "Cover": "Soft synthetic leather"}),
        P(COURTLINE, "tennis-balls", "Extra Duty Tennis Balls",
          "Pressurized extra-duty felt tennis balls for hard courts.",
          [Size("1CAN", "1 can (3 balls)", cents(4.99)), Size("4CAN", "4 cans (12 balls)", cents(17.99))], [], {"Felt": "Extra duty", "Court": "Hard court"}),
        P(COURTLINE, "tennis-racquet", "Adult Tennis Racquet, 27 in",
          "Pre-strung aluminum tennis racquet with an oversized head for recreational players. Includes a cover.",
          one(49.99), [], {"Length": "27 in", "Head size": "110 sq in", "Strung": "Yes"}),
        opts(COURTLINE, "tennis-racquet", "Junior Tennis Racquet",
             "Lightweight pre-strung junior racquet. Choose the length for your child's height.",
             ["21 in (ages 5-6)", "23 in (ages 7-8)", "25 in (ages 9-10)"], 24.99, "length",
             ["kids"], {"Strung": "Yes"}),
        P(COURTLINE, "pickleball-paddle", "Pickleball Paddle Set, 2 Paddles and 4 Balls",
          "Two fiberglass-face pickleball paddles with polymer honeycomb cores, four balls, and a carry bag.",
          one(39.99, "Set", "SET"), [], {"Paddles": "2", "Balls": "4 (2 indoor, 2 outdoor)", "Face": "Fiberglass"}),
        P(COURTLINE, "badminton-set", "Badminton Set for 4 Players",
          "Backyard badminton set with four racquets, three shuttlecocks, a net, and poles.",
          one(34.99, "Set", "SET"), [], {"Players": "4", "Includes": "4 racquets, 3 shuttlecocks, net, poles"}),
        P(TEMPO, "swim-goggles", "Anti-Fog Swim Goggles, Adult",
          "Leak-proof swim goggles with anti-fog, UV-protected lenses and an adjustable split strap.",
          one(14.99), ["waterproof"], {"Lens": "Clear anti-fog, UV protection", "Fit": "Adult"}),
        P(TEMPO, "swim-goggles", "Mirrored Competition Swim Goggles",
          "Low-profile racing goggles with mirrored anti-fog lenses and four nose-bridge sizes.",
          one(24.99), ["waterproof"], {"Lens": "Mirrored anti-fog, UV protection", "Fit": "Adult"}),
        P(OWN_BRAND, "swim-goggles", "Kids' Swim Goggles, 2-Pack",
          "Two pairs of comfortable anti-fog kids' goggles with soft silicone seals. Ages 3-12.",
          one(12.99, "2 pairs", "2PK"), ["kids", "waterproof"], {"Lens": "Anti-fog", "Ages": "3-12"}),
        P(TEMPO, "swim-cap", "Silicone Swim Cap",
          "Durable, stretchy silicone swim cap that keeps hair out of the way. Fits most adults.",
          one(9.99), ["waterproof"], {"Material": "Silicone", "Fit": "Adult"}),
    ]
# fmt: on


def products() -> list[ProductSeed]:
    return [*fitness(), *bikes_balls_racquets()]
