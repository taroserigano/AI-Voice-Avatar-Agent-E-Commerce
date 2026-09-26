"""Outdoor & Garden: camping (tents, sleeping bags, pads, coolers, lanterns, stoves), grills and
grilling tools, patio furniture, garden tools, watering, planters, seeds, soil and mulch,
and bird feeding.

Specs carry capacity (people, quarts), temperature ratings, R-values, and coverage.
"""

from __future__ import annotations

from collections.abc import Iterable

from commerce.seed.data import ProductSeed
from commerce.seed.gen.common import Size, cents, item, options, slugify

CAT = "outdoor"
SUMMIT = "Summit Forge"  # camping, premium
LARKSPUR = "Larkspur Outdoor"  # store brand, value
EMBERLINE = "Emberline Grills"  # grills and accessories
VERDANT = "Verdant Grounds"  # garden


def one(dollars: float, label: str = "Each", code: str = "EA") -> list[Size]:
    return [Size(code, label, cents(dollars))]


def sz(*rows: tuple[str, str, float]) -> list[Size]:
    return [Size(code, label, cents(price)) for code, label, price in rows]


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


# fmt: off
def camping() -> list[ProductSeed]:
    return [
        P(SUMMIT, "tent", "Solo 1-Person Ultralight Backpacking Tent",
          "Ultralight one-person tent that packs to the size of a water bottle, with a full rain fly, one door, and aluminum poles.",
          one(149.99), ["waterproof"], {"Capacity": "1 person", "Weight": "2 lb 8 oz", "Seasons": "3-season", "Floor area": "20 sq ft", "Setup": "Freestanding"}),
        P(SUMMIT, "tent", "Ridgeline 4-Person Dome Tent",
          "Roomy four-person dome tent with a full-coverage rain fly, two doors, two vestibules, and taped seams for car camping.",
          one(129.99), ["waterproof"], {"Capacity": "4 people", "Weight": "10 lb 4 oz", "Seasons": "3-season", "Floor area": "64 sq ft", "Peak height": "60 in"}),
        P(SUMMIT, "tent", "6-Person Instant Cabin Tent",
          "Cabin tent with pre-attached poles that sets up in about a minute, near-vertical walls, and room for two queen air mattresses.",
          one(219.99), ["water-resistant"], {"Capacity": "6 people", "Weight": "24 lb", "Seasons": "3-season", "Floor area": "100 sq ft", "Peak height": "78 in", "Setup": "Instant (pre-attached poles)"}),
        P(LARKSPUR, "tent", "2-Person Dome Tent",
          "Value two-person dome tent with a rain fly and a mesh roof for stargazing. Good for backyard camping and fair weather.",
          one(44.99), ["water-resistant"], {"Capacity": "2 people", "Weight": "5 lb 12 oz", "Seasons": "3-season (fair weather)", "Floor area": "35 sq ft"}),
        P(SUMMIT, "sleeping-bag", "Polar 0°F Mummy Sleeping Bag",
          "Cold-weather synthetic mummy bag rated to 0°F with a draft collar, insulated hood, and full-length zipper.",
          one(149.99), [], {"Temperature rating": "0°F", "Shape": "Mummy", "Fill": "Synthetic", "Weight": "4 lb 6 oz", "Fits up to": "6 ft 2 in"}),
        P(SUMMIT, "sleeping-bag", "Alpine 20°F Down Sleeping Bag",
          "Lightweight 650-fill water-resistant down mummy bag rated to 20°F that compresses small for backpacking.",
          one(199.99), ["water-resistant"], {"Temperature rating": "20°F", "Shape": "Mummy", "Fill": "650-fill water-resistant down", "Weight": "2 lb 4 oz", "Fits up to": "6 ft"}),
        P(LARKSPUR, "sleeping-bag", "40°F Rectangular Sleeping Bag",
          "Value rectangular sleeping bag rated to 40°F for summer camping and sleepovers. Machine washable.",
          one(29.99), ["machine-washable"], {"Temperature rating": "40°F", "Shape": "Rectangular", "Fill": "Synthetic", "Weight": "3 lb 8 oz", "Fits up to": "5 ft 11 in"}),
        P(LARKSPUR, "sleeping-bag", "Kids' 50°F Sleeping Bag",
          "Kid-size sleeping bag rated to 50°F with a fun print and a carry bag, for sleepovers and summer camp. Machine washable.",
          one(24.99), ["kids", "machine-washable"], {"Temperature rating": "50°F", "Shape": "Rectangular", "Fill": "Synthetic", "Fits up to": "5 ft"}),
        P(SUMMIT, "sleeping-pad", "Self-Inflating Camp Pad, R-Value 4.2",
          "Thick self-inflating foam pad for car camping and cold nights, with a non-slip bottom.",
          one(69.99), [], {"R-value": "4.2", "Thickness": "2 in", "Size": "72 x 22 in", "Weight": "3 lb 2 oz"}),
        P(SUMMIT, "sleeping-pad", "Ultralight Inflatable Sleeping Pad, R-Value 3.1",
          "Packable inflatable pad for backpacking with a built-in pump sack.",
          one(59.99), [], {"R-value": "3.1", "Thickness": "3 in", "Size": "72 x 21 in", "Weight": "15 oz"}),
        P(LARKSPUR, "sleeping-pad", "Closed-Cell Foam Sleeping Pad",
          "Durable closed-cell foam pad that can't puncture; use alone or under an inflatable pad.",
          one(24.99), [], {"R-value": "2.0", "Thickness": "0.75 in", "Size": "72 x 20 in", "Weight": "14 oz"}),
        P(LARKSPUR, "air-mattress", "Queen Air Mattress with Built-In Pump",
          "Raised 18-inch queen air mattress with a built-in electric pump that inflates in about 4 minutes.",
          one(59.99), [], {"Size": "Queen (80 x 60 in)", "Height": "18 in", "Pump": "Built-in electric (AC)"}),
        P(SUMMIT, "cooler", "Rotomolded Hard Cooler, 45 qt",
          "Rotomolded cooler with thick insulation that keeps ice up to 7 days, bear-resistant latches, and a drain plug.",
          one(249.99), [], {"Capacity": "45 qt", "Ice retention": "Up to 7 days", "Cans": "About 28 cans with ice", "Construction": "Rotomolded"}),
        P(SUMMIT, "cooler", "Rotomolded Hard Cooler, 25 qt",
          "Compact rotomolded cooler that keeps ice up to 5 days, with a carry handle and non-slip feet.",
          one(179.99), [], {"Capacity": "25 qt", "Ice retention": "Up to 5 days", "Cans": "About 16 cans with ice", "Construction": "Rotomolded"}),
        P(LARKSPUR, "cooler", "Wheeled Cooler, 60 qt",
          "Value wheeled cooler with a telescoping handle, cup holders in the lid, and 4-day ice retention.",
          one(54.99), [], {"Capacity": "60 qt", "Ice retention": "Up to 4 days", "Cans": "About 90 cans with ice", "Wheels": "Yes"}),
        P(SUMMIT, "cooler", "Soft-Sided Cooler Bag, 24 Can",
          "Leak-proof, waterproof soft cooler bag that holds 24 cans plus ice and keeps them cold for 2 days.",
          one(39.99), ["waterproof"], {"Capacity": "24 cans (about 20 qt)", "Ice retention": "Up to 2 days", "Construction": "Soft-sided"}),
        P(SUMMIT, "lantern", "Rechargeable LED Camp Lantern, 1000 Lumens",
          "Bright 1000-lumen LED lantern with four modes, a USB-C rechargeable battery that runs up to 100 hours on low, and a phone-charging port.",
          one(34.99), ["rechargeable", "usb-c", "water-resistant"], {"Brightness": "1000 lumens", "Runtime": "Up to 100 hours (low)", "Power": "Rechargeable, USB-C", "Water resistance": "IPX4"}),
        P(LARKSPUR, "lantern", "Battery-Powered LED Lantern, 300 Lumens",
          "Collapsible 300-lumen LED lantern powered by 3 AA batteries (included).",
          one(12.99), [], {"Brightness": "300 lumens", "Runtime": "Up to 12 hours", "Power": "3 AA batteries (included)"}),
        P(SUMMIT, "camp-stove", "2-Burner Propane Camp Stove",
          "Two-burner propane camping stove with 20,000 BTUs total, wind guards, and push-button ignition. Uses 1 lb propane cylinders.",
          one(69.99), [], {"Burners": "2", "Output": "20,000 BTU total", "Fuel": "1 lb propane cylinder (not included)"}),
    ]


def grilling_and_patio() -> list[ProductSeed]:
    return [
        P(EMBERLINE, "grill", "3-Burner Propane Gas Grill",
          "Three-burner propane grill with 450 sq in of porcelain-coated cast iron grates, a side burner, and a built-in thermometer.",
          one(349.99), [], {"Fuel": "Propane (tank not included)", "Burners": "3 + side burner", "Cooking area": "450 sq in", "Output": "36,000 BTU"}),
        P(EMBERLINE, "grill", "22-Inch Charcoal Kettle Grill",
          "Classic 22-inch charcoal kettle grill with a porcelain-enameled bowl, adjustable vents, and an ash catcher.",
          one(129.99), [], {"Fuel": "Charcoal", "Cooking area": "363 sq in", "Grate diameter": "22 in"}),
        P(EMBERLINE, "grill", "Portable Tabletop Propane Grill",
          "Compact tabletop propane grill for tailgating and camping, with folding legs and push-button ignition.",
          one(149.99), [], {"Fuel": "1 lb propane cylinder", "Burners": "1", "Cooking area": "200 sq in", "Output": "12,000 BTU"}),
        P(EMBERLINE, "grill-accessory", "5-Piece Stainless Steel Grill Tool Set",
          "Stainless spatula, tongs, fork, basting brush, and cleaning brush with a storage case. Dishwasher safe.",
          one(29.99), ["dishwasher-safe"], {"Pieces": "5", "Material": "Stainless steel"}),
        P(EMBERLINE, "grill-accessory", "Heavy-Duty Waterproof Grill Cover, 58 in",
          "Waterproof, UV-resistant grill cover with vents and hook-and-loop straps; fits most 3-4 burner grills.",
          one(29.99), ["waterproof"], {"Fits": "Grills up to 58 in wide", "Material": "600D polyester"}),
        P(EMBERLINE, "grill-accessory", "Bristle-Free Grill Brush",
          "Coil-style grill brush with no bristles that can break off into food, and a scraper.",
          one(14.99), [], {"Material": "Stainless steel coils"}),
        P(EMBERLINE, "grill-accessory", "Instant-Read Digital Meat Thermometer",
          "Fast 3-second digital meat thermometer with a folding probe, backlight, and magnet.",
          one(19.99), ["water-resistant"], {"Reading time": "3 seconds", "Range": "-58°F to 572°F", "Water resistance": "IP65"}),
        P(LARKSPUR, "patio-chair", "Resin Adirondack Chair",
          "Weather-resistant poly resin Adirondack chair that won't rot, splinter, or need painting.",
          one(49.99), ["recycled-materials"], {"Material": "Recycled poly resin", "Weight capacity": "300 lb"}),
        P(LARKSPUR, "patio-set", "4-Piece Wicker Patio Conversation Set",
          "All-weather wicker loveseat, two armchairs, and a glass-top table with washable cushions.",
          one(399.99), [], {"Pieces": "4", "Seats": "4", "Material": "Steel frame, PE wicker", "Cushions": "Removable, washable covers"}),
        P(LARKSPUR, "patio-set", "3-Piece Folding Bistro Set",
          "Folding steel bistro table and two chairs for balconies and small patios.",
          one(129.99), [], {"Pieces": "3", "Seats": "2", "Material": "Powder-coated steel"}),
        P(LARKSPUR, "patio-umbrella", "9 ft Market Patio Umbrella with Tilt",
          "9-foot market umbrella with UV-resistant fabric, crank open, and push-button tilt. Base sold separately.",
          one(59.99), ["water-resistant"], {"Diameter": "9 ft", "Fabric": "UPF 50 polyester", "Base": "Not included"}),
    ]


def garden() -> list[ProductSeed]:
    slug = slugify(VERDANT, "Garden Gloves, Nitrile Coated")
    return [
        P(VERDANT, "garden-tools", "Hand Trowel, Transplanter & Cultivator Set",
          "Three cast-aluminum hand tools with comfortable grips for planting, transplanting, and weeding.",
          one(19.99, "3 tools", "3PC"), [], {"Pieces": "3", "Material": "Cast aluminum"}),
        P(VERDANT, "garden-tools", "Bypass Pruning Shears",
          "Sharp bypass pruners with a non-stick coated blade for clean cuts on branches up to 3/4 inch.",
          one(17.99), [], {"Cutting capacity": "3/4 in", "Blade": "Coated carbon steel"}),
        P(VERDANT, "garden-tools", "Round-Point Digging Shovel",
          "Heavy-duty round-point shovel with a fiberglass handle and a cushioned grip.",
          one(29.99), [], {"Length": "48 in", "Handle": "Fiberglass"}),
        P(VERDANT, "garden-tools", "Adjustable Steel Leaf Rake",
          "Leaf rake that adjusts from 7 to 22 inches wide to reach under shrubs or clear wide lawns.",
          one(24.99), [], {"Width": "7-22 in adjustable", "Handle": "Steel, 63 in"}),
        item(category=CAT, product_type="garden-gloves", brand=VERDANT, title="Garden Gloves, Nitrile Coated",
             description="Breathable knit garden gloves with a nitrile-coated palm for grip and puncture resistance. 3 pairs.",
             variants_=options(CAT, slug, ["Small", "Medium", "Large"], cents(9.99), "size"),
             tags=["machine-washable"], specs={"Pairs": "3", "Palm": "Nitrile coated"}, slug=slug),
        P(VERDANT, "garden-hose", "Expandable Garden Hose, 100 ft",
          "Lightweight expandable hose that stretches to 100 feet with water pressure and shrinks back for storage. Includes a 10-pattern nozzle.",
          one(44.99), [], {"Length": "100 ft (expanded)", "Fittings": "Solid brass", "Nozzle included": "Yes"}),
        P(VERDANT, "hose-nozzle", "10-Pattern Hose Spray Nozzle",
          "Metal hose nozzle with 10 spray patterns and a thumb-control flow valve.",
          one(12.99), [], {"Patterns": "10", "Material": "Zinc alloy"}),
        P(VERDANT, "sprinkler", "Oscillating Lawn Sprinkler",
          "Adjustable oscillating sprinkler that covers up to 3,600 sq ft with range and width control.",
          one(19.99), [], {"Coverage": "Up to 3,600 sq ft"}),
        P(VERDANT, "planter", "Self-Watering Planters, 12 in, 2-Pack",
          "Two 12-inch planters with a built-in water reservoir and indicator for less frequent watering.",
          one(29.99, "2 planters", "2PK"), ["recycled-materials"], {"Diameter": "12 in", "Material": "Recycled plastic", "Drainage": "Reservoir with overflow"}),
        P(LARKSPUR, "planter", "Terracotta Pots with Saucers, 6 in, 3-Pack",
          "Classic unglazed terracotta pots with drainage holes and matching saucers.",
          one(14.99, "3 pots", "3PK"), [], {"Diameter": "6 in", "Material": "Terracotta", "Drainage": "Hole with saucer"}),
        P(VERDANT, "seeds", "Organic Heirloom Tomato Seeds, Brandywine",
          "Certified organic, non-GMO heirloom Brandywine tomato seeds; large pink beefsteak fruit in about 85 days.",
          one(3.49, "1 packet (about 30 seeds)", "PKT"), ["organic", "non-gmo"], {"Days to maturity": "85", "Sun": "Full sun", "Seeds": "About 30"}),
        P(VERDANT, "seeds", "Vegetable Garden Seed Collection, 10 Varieties",
          "Ten packets of non-GMO heirloom vegetable seeds: tomato, lettuce, carrot, bean, cucumber, zucchini, pepper, radish, spinach, and beet.",
          one(19.99, "10 packets", "10PK"), ["non-gmo"], {"Varieties": "10", "Sun": "Full sun"}),
        P(VERDANT, "seeds", "Pollinator Wildflower Seed Mix",
          "Blend of 20 native annual and perennial wildflowers that attract bees and butterflies; covers about 250 sq ft.",
          one(9.99, "4 oz bag", "4OZ"), ["non-gmo"], {"Coverage": "About 250 sq ft", "Varieties": "20"}),
        P(VERDANT, "soil", "Organic Raised Bed Soil, 1.5 cu ft",
          "OMRI-listed organic soil blend for raised beds and in-ground vegetables, with compost and aged bark.",
          one(12.99, "1.5 cu ft bag", "1_5CF"), ["organic"], {"Volume": "1.5 cu ft", "Use": "Raised beds, in-ground"}),
        P(VERDANT, "soil", "Organic Potting Mix",
          "OMRI-listed organic potting mix for containers and houseplants with perlite for drainage.",
          sz(("8QT", "8 qt bag", 6.99), ("1CF", "1 cu ft bag", 11.99)), ["organic"], {"Use": "Containers and houseplants"}),
        P(LARKSPUR, "mulch", "Shredded Cedar Mulch, 2 cu ft",
          "Natural shredded cedar mulch that holds moisture and suppresses weeds, with a fresh cedar aroma.",
          one(5.99, "2 cu ft bag", "2CF"), [], {"Volume": "2 cu ft", "Color": "Natural cedar"}),
        P(VERDANT, "bird-feeder", "Metal Tube Bird Feeder, 6 Ports",
          "Squirrel-resistant metal tube feeder with six perches that holds 2 lb of mixed seed.",
          one(19.99), [], {"Capacity": "2 lb seed", "Ports": "6"}),
        P(VERDANT, "bird-feeder", "Glass Hummingbird Feeder, 16 oz",
          "Glass hummingbird feeder with five flower ports and a built-in ant moat.",
          one(14.99), [], {"Capacity": "16 oz nectar", "Ports": "5"}),
        P(LARKSPUR, "bird-seed", "Wild Bird Seed Mix, 20 lb",
          "Value wild bird seed with millet, sunflower, and milo for a variety of backyard birds.",
          one(17.99, "20 lb bag", "20LB"), [], {"Weight": "20 lb", "Contains": "Millet, black oil sunflower, milo, cracked corn"}),
    ]
# fmt: on


def products() -> list[ProductSeed]:
    return [*camping(), *grilling_and_patio(), *garden()]
