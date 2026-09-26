"""Pet supplies: dog and cat food and treats, cat litter, toys, beds, leashes and collars, poop
bags, bowls, and pads.

Pet food is not human food, so it has no nutrition panel: every food and treat carries
"Life stage", "Protein source", and a "Guaranteed analysis" in its specs instead.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from commerce.seed.data import ProductSeed
from commerce.seed.gen.common import Size, cents, item, options, slugify

CAT = "pet"
MEADOWBROOK = "Meadowbrook Pet"  # mainstream dog and cat food
TRAILHOUND = "Trailhound"  # premium, grain-free and limited ingredient
WHISKERWELL = "Whiskerwell"  # cat food and litter
LARKSPUR = "Larkspur Pet"  # store brand, value
WAGWORKS = "Wagworks"  # toys, beds, leashes, bags


def ga(protein: float, fat: float, fiber: float, moisture: float) -> str:
    """A guaranteed analysis as printed on pet food labels."""
    return (
        f"Crude protein {protein:g}% min, crude fat {fat:g}% min, "
        f"crude fiber {fiber:g}% max, moisture {moisture:g}% max"
    )


def sz(*rows: tuple[str, str, float]) -> list[Size]:
    return [Size(code, label, cents(price)) for code, label, price in rows]


def bags(*rows: tuple[float, float]) -> list[Size]:
    """Bag sizes from (pounds, dollars) rows."""
    return [Size(f"{lb:g}LB".replace(".", "_"), f"{lb:g} lb bag", cents(p)) for lb, p in rows]


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


def with_options(
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


@dataclass(frozen=True)
class Food:
    """One pet food or treat listing."""

    brand: str
    product_type: str  # dog-food, cat-food, dog-treats, cat-treats
    title: str
    life_stage: str
    protein: str
    analysis: str
    sizes: list[Size]
    note: str  # the sentence that sets this recipe apart
    breed: str | None = None
    form: str = "Dry kibble"
    grain_free: bool = False
    limited: bool = False
    kcal: str | None = None


def build(f: Food) -> ProductSeed:
    animal = "dog" if f.product_type.startswith("dog") else "cat"
    tags = (["grain-free"] if f.grain_free else []) + (["limited-ingredient"] if f.limited else [])
    specs = {
        "Life stage": f.life_stage,
        "Protein source": f.protein,
        "Form": f.form,
        "Grain": "Grain free" if f.grain_free else "Contains grains",
        "Guaranteed analysis": f.analysis,
    }
    if f.breed:
        specs["Breed size"] = f.breed
    if f.kcal:
        specs["Calories"] = f.kcal
    if f.limited:
        specs["Recipe"] = "Limited ingredient (single animal protein)"
    grain = "Grain free. " if f.grain_free else ""
    description = (
        f"{f.form} for {animal}s; life stage: {f.life_stage.lower()}. {f.note} "
        f"{grain}Protein source: {f.protein.lower()}."
    )
    return P(f.brand, f.product_type, f.title, description, f.sizes, tags, specs)


# fmt: off
def dog_food() -> list[ProductSeed]:
    kibble_mb = bags((5, 12.99), (15, 29.99), (30, 49.99))
    kibble_th = bags((4, 19.99), (12, 44.99), (24, 74.99))
    rows = [
        # Meadowbrook: mainstream, with grains
        Food(MEADOWBROOK, "dog-food", "Adult Dry Dog Food, Chicken & Brown Rice", "Adult", "Chicken", ga(26, 15, 4, 10), kibble_mb,
             "Real chicken is the first ingredient, with brown rice and omega-6 for a shiny coat.", "All breed sizes", kcal="370 kcal/cup"),
        Food(MEADOWBROOK, "dog-food", "Puppy Dry Dog Food, Chicken & Brown Rice", "Puppy", "Chicken", ga(28, 17, 4, 10), bags((5, 13.99), (15, 32.99), (30, 54.99)),
             "Made with DHA for brain and eye development and small, easy-to-chew kibble.", "All breed sizes", kcal="390 kcal/cup"),
        Food(MEADOWBROOK, "dog-food", "Senior 7+ Dry Dog Food, Chicken & Barley", "Senior (7+ years)", "Chicken", ga(24, 11, 5, 10), kibble_mb,
             "Fewer calories plus glucosamine and chondroitin for aging joints.", "All breed sizes", kcal="340 kcal/cup"),
        Food(MEADOWBROOK, "dog-food", "Small Breed Adult Dry Dog Food, Chicken & Rice", "Adult", "Chicken", ga(27, 16, 4, 10), bags((4, 10.99), (12, 24.99)),
             "Small kibble sized for little mouths, for dogs up to 25 lb.", "Small breed (up to 25 lb)", kcal="400 kcal/cup"),
        Food(MEADOWBROOK, "dog-food", "Small Breed Senior Dry Dog Food, Chicken & Rice", "Senior (7+ years)", "Chicken", ga(25, 12, 5, 10), bags((4, 11.49), (12, 25.99)),
             "Small kibble with glucosamine for small dogs 7 years and older.", "Small breed (up to 25 lb)", kcal="360 kcal/cup"),
        Food(MEADOWBROOK, "dog-food", "Large Breed Adult Dry Dog Food, Chicken & Rice", "Adult", "Chicken", ga(24, 13, 4, 10), bags((15, 29.99), (30, 49.99), (40, 59.99)),
             "Large kibble with glucosamine for dogs over 50 lb.", "Large breed (50+ lb)", kcal="350 kcal/cup"),
        Food(MEADOWBROOK, "dog-food", "Large Breed Puppy Dry Dog Food, Chicken & Rice", "Puppy", "Chicken", ga(27, 13, 4, 10), bags((15, 32.99), (30, 54.99)),
             "Controlled calcium for steady bone growth in puppies that will grow over 50 lb.", "Large breed (50+ lb)", kcal="360 kcal/cup"),
        Food(MEADOWBROOK, "dog-food", "Healthy Weight Adult Dry Dog Food, Chicken & Rice", "Adult", "Chicken", ga(24, 8, 10, 10), kibble_mb,
             "20% fewer calories than our adult recipe, with fiber to help dogs feel full.", "All breed sizes", kcal="300 kcal/cup"),
        Food(MEADOWBROOK, "dog-food", "Adult Dry Dog Food, Lamb & Rice", "Adult", "Lamb", ga(24, 14, 4, 10), kibble_mb,
             "Real lamb is the first ingredient, for dogs who prefer a change from chicken.", "All breed sizes", kcal="360 kcal/cup"),
        # Trailhound: premium, grain free and limited ingredient
        Food(TRAILHOUND, "dog-food", "Grain-Free Adult Dry Dog Food, Salmon & Sweet Potato", "Adult", "Salmon", ga(26, 16, 5, 10), kibble_th,
             "Salmon is the first ingredient, with sweet potato and peas in place of grains.", "All breed sizes", grain_free=True, kcal="380 kcal/cup"),
        Food(TRAILHOUND, "dog-food", "Grain-Free Puppy Dry Dog Food, Salmon & Sweet Potato", "Puppy", "Salmon", ga(30, 18, 5, 10), kibble_th,
             "Salmon and DHA for growing puppies, with no corn, wheat, or other grains.", "All breed sizes", grain_free=True, kcal="400 kcal/cup"),
        Food(TRAILHOUND, "dog-food", "Grain-Free Senior Dry Dog Food, Chicken & Sweet Potato", "Senior (7+ years)", "Chicken", ga(25, 12, 6, 10), kibble_th,
             "Deboned chicken with glucosamine and chondroitin for joints and fewer calories for less active seniors.", "All breed sizes", grain_free=True, kcal="345 kcal/cup"),
        Food(TRAILHOUND, "dog-food", "Grain-Free Adult Dry Dog Food, Beef & Sweet Potato", "Adult", "Beef", ga(26, 15, 5, 10), kibble_th,
             "Real beef is the first ingredient, with sweet potato and no grains.", "All breed sizes", grain_free=True, kcal="375 kcal/cup"),
        Food(TRAILHOUND, "dog-food", "Limited Ingredient Grain-Free Dry Dog Food, Lamb & Pea", "Adult", "Lamb", ga(22, 12, 5, 10), bags((4, 21.99), (12, 47.99), (22, 79.99)),
             "One animal protein (lamb) and a short ingredient list for dogs with food sensitivities.", "All breed sizes", grain_free=True, limited=True, kcal="355 kcal/cup"),
        Food(TRAILHOUND, "dog-food", "Limited Ingredient Grain-Free Dry Dog Food, Salmon & Potato", "Adult", "Salmon", ga(22, 12, 5, 10), bags((4, 21.99), (12, 47.99), (22, 79.99)),
             "One animal protein (salmon) and a short ingredient list for sensitive stomachs and skin.", "All breed sizes", grain_free=True, limited=True, kcal="360 kcal/cup"),
        Food(TRAILHOUND, "dog-food", "Small Breed Grain-Free Adult Dry Dog Food, Chicken & Pea", "Adult", "Chicken", ga(28, 17, 5, 10), bags((4, 19.99), (10, 39.99)),
             "Small, nutrient-dense kibble for small dogs, with no grains.", "Small breed (up to 25 lb)", grain_free=True, kcal="410 kcal/cup"),
        Food(TRAILHOUND, "dog-food", "Wholesome Grains Adult Dry Dog Food, Beef & Brown Rice", "Adult", "Beef", ga(25, 15, 4, 10), kibble_th,
             "Real beef with brown rice, oats, and barley for dogs who do well on grains.", "All breed sizes", kcal="370 kcal/cup"),
        # Larkspur Pet: value
        Food(LARKSPUR, "dog-food", "Complete Nutrition Adult Dry Dog Food, Beef Flavor", "Adult", "Beef and chicken by-product meal", ga(21, 10, 4.5, 12), bags((18, 15.99), (40, 28.99)),
             "Value adult dog food made with whole grain corn and 23 vitamins and minerals.", "All breed sizes", kcal="335 kcal/cup"),
        Food(LARKSPUR, "dog-food", "Complete Nutrition Puppy Dry Dog Food, Chicken Flavor", "Puppy", "Chicken by-product meal", ga(27, 12, 4, 12), bags((16, 16.99)),
             "Value puppy food with DHA and calcium for growing puppies.", "All breed sizes", kcal="350 kcal/cup"),
        Food(LARKSPUR, "dog-food", "Complete Nutrition Senior Dry Dog Food, Chicken Flavor", "Senior (7+ years)", "Chicken by-product meal", ga(22, 8, 5, 12), bags((16, 16.99)),
             "Value senior dog food with fewer calories and added glucosamine.", "All breed sizes", kcal="310 kcal/cup"),
        # Wet dog food
        Food(MEADOWBROOK, "dog-food", "Chunks in Gravy Wet Dog Food Variety Pack, 12 x 13 oz", "Adult", "Chicken, beef, and lamb", ga(8, 5, 1.5, 78),
             sz(("12PK", "12 cans x 13 oz", 19.99)), "Hearty chunks in gravy in three flavors: chicken, beef, and lamb.", form="Wet (canned)"),
        Food(MEADOWBROOK, "dog-food", "Puppy Pâté Wet Dog Food, Chicken, 12 x 13 oz", "Puppy", "Chicken", ga(9, 6, 1.5, 78),
             sz(("12PK", "12 cans x 13 oz", 21.99)), "Smooth chicken pâté with DHA for puppies, easy to mix with kibble.", form="Wet (canned)"),
        Food(MEADOWBROOK, "dog-food", "Senior Tender Stew Wet Dog Food, Chicken & Vegetables, 12 x 12.5 oz", "Senior (7+ years)", "Chicken", ga(7, 4, 1.5, 80),
             sz(("12PK", "12 cans x 12.5 oz", 21.99)), "Soft chicken stew with carrots and peas that is easy for older dogs to chew.", form="Wet (canned)"),
        Food(TRAILHOUND, "dog-food", "Grain-Free Beef Stew Wet Dog Food, 12 x 12.5 oz", "Adult", "Beef", ga(8, 4, 1.5, 80),
             sz(("12PK", "12 cans x 12.5 oz", 34.99)), "Chunky beef stew with sweet potatoes and carrots.", form="Wet (canned)", grain_free=True),
        Food(TRAILHOUND, "dog-food", "Limited Ingredient Lamb Pâté Wet Dog Food, 6 x 13 oz", "Adult", "Lamb", ga(8, 5, 1.5, 78),
             sz(("6PK", "6 cans x 13 oz", 21.99)), "Lamb and pumpkin pâté with one animal protein for sensitive dogs.", form="Wet (canned)", grain_free=True, limited=True),
        Food(TRAILHOUND, "dog-food", "Small Breed Grain-Free Wet Dog Food Trays, Chicken, 12 x 3.5 oz", "Adult", "Chicken", ga(9, 5, 1, 82),
             sz(("12PK", "12 trays x 3.5 oz", 17.99)), "Single-serve trays of chicken in broth sized for small dogs.", breed="Small breed (up to 25 lb)", form="Wet (trays)", grain_free=True),
        Food(LARKSPUR, "dog-food", "Classic Loaf Wet Dog Food, Beef", "Adult", "Beef and meat by-products", ga(8, 5, 1.5, 78),
             sz(("1CAN", "1 can (13.2 oz)", 1.29), ("12PK", "12 cans x 13.2 oz", 14.49)), "Value beef loaf in a pull-top can.", form="Wet (canned)"),
        # Dog treats
        Food(MEADOWBROOK, "dog-treats", "Dental Chews for Dogs", "Adult (9+ months)", "Chicken flavor (rice and potato based)", ga(8, 3, 3, 16),
             sz(("SM", "Small (5-20 lb), 36 chews", 19.99), ("MD", "Medium (20-40 lb), 24 chews", 19.99), ("LG", "Large (40+ lb), 17 chews", 19.99)),
             "Textured daily dental chews that help reduce tartar build-up. Choose the size for your dog's weight.", form="Chew"),
        Food(TRAILHOUND, "dog-treats", "Grain-Free Chicken Jerky Dog Treats", "All life stages", "Chicken", ga(60, 5, 1, 25),
             sz(("12OZ", "12 oz bag", 14.99), ("24OZ", "24 oz bag", 24.99)), "Single-ingredient chicken breast jerky, slow roasted in the USA.", form="Jerky", grain_free=True, limited=True),
        Food(MEADOWBROOK, "dog-treats", "Soft & Chewy Training Treats, Chicken", "All life stages", "Chicken", ga(18, 8, 2, 28),
             sz(("4OZ", "4 oz pouch (about 150 treats)", 5.99)), "Tiny soft training treats with only 3 calories each, ideal for repetition.", form="Soft treat", kcal="3 kcal/treat"),
        Food(LARKSPUR, "dog-treats", "Peanut Butter Dog Biscuits", "Adult", "Peanut butter (wheat based)", ga(14, 6, 5, 12),
             sz(("4LB", "4 lb box", 8.99)), "Crunchy oven-baked biscuits made with wheat flour and peanut butter.", form="Biscuit"),
        Food(TRAILHOUND, "dog-treats", "Beef Rawhide-Free Chew Rolls, 10 Count", "Adult", "Beef", ga(40, 6, 3, 18),
             sz(("10CT", "10 rolls", 16.99)), "Long-lasting rawhide-free chews wrapped in real beef for strong chewers.", form="Chew", grain_free=True),
    ]  # fmt: skip
    return [build(f) for f in rows]


def cat_food() -> list[ProductSeed]:
    kibble = bags((3.5, 12.99), (7, 21.99), (14, 36.99))
    rows = [
        Food(WHISKERWELL, "cat-food", "Indoor Adult Dry Cat Food, Chicken", "Adult (1-7 years)", "Chicken", ga(32, 13, 7, 10), kibble,
             "Made for indoor cats, with fiber for hairball control and fewer calories to help maintain a healthy weight.", kcal="360 kcal/cup"),
        Food(WHISKERWELL, "cat-food", "Kitten Dry Cat Food, Chicken", "Kitten (up to 1 year)", "Chicken", ga(36, 18, 4, 10), bags((3.5, 13.99), (7, 23.99)),
             "Small kibble with DHA and extra protein for growing kittens.", kcal="420 kcal/cup"),
        Food(WHISKERWELL, "cat-food", "Senior 11+ Dry Cat Food, Chicken & Rice", "Senior (11+ years)", "Chicken", ga(30, 14, 5, 10), kibble,
             "Easy-to-digest recipe with antioxidants and controlled minerals for older cats.", kcal="380 kcal/cup"),
        Food(WHISKERWELL, "cat-food", "Hairball Control Adult Dry Cat Food, Salmon", "Adult (1-7 years)", "Salmon", ga(31, 13, 8.5, 10), kibble,
             "Natural fiber blend that helps hairballs pass, with salmon as the first ingredient.", kcal="365 kcal/cup"),
        Food(WHISKERWELL, "cat-food", "Grain-Free Indoor Dry Cat Food, Salmon", "Adult (1-7 years)", "Salmon", ga(34, 14, 6, 10), kibble,
             "Indoor formula with salmon and peas and no corn, wheat, or soy.", grain_free=True, kcal="375 kcal/cup"),
        Food(WHISKERWELL, "cat-food", "Limited Ingredient Grain-Free Dry Cat Food, Turkey", "Adult (1-7 years)", "Turkey", ga(32, 14, 5, 10), bags((4, 17.99), (10, 36.99)),
             "One animal protein and a short ingredient list for cats with sensitive stomachs.", grain_free=True, limited=True, kcal="380 kcal/cup"),
        Food(MEADOWBROOK, "cat-food", "Adult Dry Cat Food, Chicken & Rice", "Adult (1-7 years)", "Chicken", ga(30, 12, 4, 12), bags((3.5, 9.99), (16, 29.99)),
             "Real chicken is the first ingredient, with taurine for heart and eye health.", kcal="370 kcal/cup"),
        Food(LARKSPUR, "cat-food", "Complete Adult Dry Cat Food, Ocean Fish Flavor", "Adult (1-7 years)", "Fish meal and chicken by-product meal", ga(30, 11, 4, 12), bags((16, 15.99)),
             "Value adult cat food with taurine and 25 vitamins and minerals.", kcal="350 kcal/cup"),
        Food(LARKSPUR, "cat-food", "Indoor Adult Dry Cat Food, Chicken", "Adult (1-7 years)", "Chicken by-product meal", ga(30, 10, 6, 12), bags((6.3, 7.99), (16, 16.99)),
             "Value indoor cat food with fiber for hairball control.", kcal="345 kcal/cup"),
        # Wet
        Food(WHISKERWELL, "cat-food", "Pâté Wet Cat Food Variety Pack", "Adult (1-7 years)", "Chicken, salmon, and turkey", ga(10, 5, 1.5, 78),
             sz(("12PK", "12 cans x 3 oz", 11.99), ("24PK", "24 cans x 3 oz", 21.99)), "Smooth pâté in chicken, salmon, and turkey flavors.", form="Wet (canned)"),
        Food(WHISKERWELL, "cat-food", "Kitten Pâté Wet Cat Food, Chicken, 12 x 3 oz", "Kitten (up to 1 year)", "Chicken", ga(11, 6, 1, 78),
             sz(("12PK", "12 cans x 3 oz", 12.99)), "Extra-smooth chicken pâté with DHA for kittens.", form="Wet (canned)"),
        Food(WHISKERWELL, "cat-food", "Senior 11+ Minced Wet Cat Food, Salmon, 12 x 3 oz", "Senior (11+ years)", "Salmon", ga(10, 4, 1.5, 80),
             sz(("12PK", "12 cans x 3 oz", 12.99)), "Finely minced salmon in gravy that is easy for older cats to eat.", form="Wet (canned)"),
        Food(WHISKERWELL, "cat-food", "Grain-Free Flaked Tuna Wet Cat Food, 24 x 3 oz", "Adult (1-7 years)", "Tuna", ga(12, 2, 1, 82),
             sz(("24PK", "24 cans x 3 oz", 22.99)), "Flaked skipjack tuna in broth with no grains.", form="Wet (canned)", grain_free=True),
        Food(WHISKERWELL, "cat-food", "Hairball Control Wet Cat Food, Chicken, 12 x 3 oz", "Adult (1-7 years)", "Chicken", ga(10, 4, 2.5, 78),
             sz(("12PK", "12 cans x 3 oz", 12.99)), "Chicken pâté with added fiber to help reduce hairballs.", form="Wet (canned)"),
        Food(LARKSPUR, "cat-food", "Classic Pâté Wet Cat Food Variety Pack, 24 x 5.5 oz", "Adult (1-7 years)", "Chicken, fish, and beef", ga(9, 5, 1.5, 78),
             sz(("24PK", "24 cans x 5.5 oz", 19.99)), "Value pâté in chicken, ocean fish, and beef flavors.", form="Wet (canned)"),
        # Treats
        Food(WHISKERWELL, "cat-treats", "Crunchy Cat Treats, Salmon", "Adult (1+ years)", "Salmon", ga(30, 17, 4, 12),
             sz(("3OZ", "3 oz pouch", 2.49), ("30OZ", "30 oz tub", 12.99)), "Crunchy outside, soft inside, under 2 calories per treat.", form="Crunchy treat", kcal="1.8 kcal/treat"),
        Food(WHISKERWELL, "cat-treats", "Lickable Puree Cat Treats, Tuna, 20 Tubes", "All life stages", "Tuna", ga(8, 0.5, 0.5, 91),
             sz(("20CT", "20 tubes x 0.5 oz", 8.99)), "Squeezable tuna puree to hand-feed or pour over food.", form="Puree", grain_free=True, kcal="6 kcal/tube"),
    ]  # fmt: skip
    return [build(f) for f in rows]


def litter() -> list[ProductSeed]:
    clay = {"Material": "Bentonite clay"}
    return [
        P(WHISKERWELL, "cat-litter", "Unscented Clumping Clay Cat Litter",
          "Hard-clumping bentonite clay litter with no added fragrance and 99% dust free. Traps odor with activated charcoal.",
          sz(("20LB", "20 lb box", 11.99), ("40LB", "40 lb box", 19.99)), ["fragrance-free"],
          {**clay, "Clumping": "Yes", "Scent": "Unscented", "Lightweight": "No", "Dust": "99% dust free"}),
        P(WHISKERWELL, "cat-litter", "Lightweight Unscented Clumping Cat Litter",
          "Lightweight clumping litter that is half the weight of regular clay litter with the same number of scoops. Unscented and 99% dust free.",
          sz(("8_5LB", "8.5 lb (as much litter as 20 lb of clay)", 12.99), ("17LB", "17 lb (as much litter as 40 lb of clay)", 21.99)), ["fragrance-free"],
          {**clay, "Clumping": "Yes", "Scent": "Unscented", "Lightweight": "Yes, about half the weight of clay", "Dust": "99% dust free"}),
        P(WHISKERWELL, "cat-litter", "Multi-Cat Clumping Cat Litter, Fresh Scent",
          "Extra-strength clumping clay litter for homes with several cats, with a fresh scent that releases when cats dig.",
          sz(("20LB", "20 lb box", 12.99), ("40LB", "40 lb box", 21.99)), [],
          {**clay, "Clumping": "Yes", "Scent": "Fresh", "Lightweight": "No", "Cats": "Multi-cat"}),
        P(WHISKERWELL, "cat-litter", "Natural Corn & Grass Clumping Cat Litter, Unscented",
          "Plant-based clumping litter made from corn and grass seed that is lightweight, flushable where permitted, and biodegradable. No added fragrance.",
          sz(("10LB", "10 lb bag", 16.99), ("20LB", "20 lb bag", 29.99)), ["plant-based", "biodegradable", "fragrance-free"],
          {"Material": "Corn and grass seed", "Clumping": "Yes", "Scent": "Unscented", "Lightweight": "Yes"}),
        P(LARKSPUR, "cat-litter", "Clumping Cat Litter, Unscented",
          "Value clumping clay litter with no added fragrance.",
          sz(("35LB", "35 lb jug", 12.99)), ["fragrance-free"],
          {**clay, "Clumping": "Yes", "Scent": "Unscented", "Lightweight": "No"}),
        P(LARKSPUR, "cat-litter", "Non-Clumping Clay Cat Litter, Unscented",
          "Budget non-clumping clay litter that absorbs moisture. Change fully every week.",
          sz(("25LB", "25 lb bag", 6.99)), ["fragrance-free"],
          {"Material": "Clay", "Clumping": "No", "Scent": "Unscented", "Lightweight": "No"}),
        P(LARKSPUR, "cat-litter", "Pine Pellet Cat Litter",
          "Non-clumping pellets of reclaimed pine that absorb and break down into sawdust. Biodegradable, with a natural pine smell and no added fragrance.",
          sz(("20LB", "20 lb bag", 9.99)), ["biodegradable", "recycled-materials"],
          {"Material": "Reclaimed pine", "Clumping": "No", "Scent": "Natural pine (no added fragrance)", "Lightweight": "Yes"}),
        P(WAGWORKS, "litter-box", "High-Sided Litter Box with Scoop",
          "Extra-large litter box with high sides to reduce scatter and a low entry, plus a matching scoop.",
          sz(("EA", "Each", 19.99)), [], {"Size": "24 x 18 x 10 in", "Covered": "No"}),
    ]


def toys_beds_gear() -> list[ProductSeed]:
    return [
        P(WAGWORKS, "dog-toy", "Durable Rubber Chew Toy for Dogs",
          "Tough natural rubber chew toy with a hollow center to stuff with treats. Top-rack dishwasher safe.",
          sz(("SM", "Small (up to 20 lb)", 8.99), ("MD", "Medium (20-45 lb)", 12.99), ("LG", "Large (45-75 lb)", 15.99)),
          ["dishwasher-safe"], {"For": "Dogs", "Material": "Natural rubber", "Chew strength": "Heavy chewers"}),
        P(WAGWORKS, "dog-toy", "Squeaky Plush Fox Dog Toy",
          "Soft plush fox with two squeakers and crinkle paper for gentle players. Not for heavy chewers.",
          sz(("EA", "Each", 7.99)), ["machine-washable"], {"For": "Dogs", "Material": "Plush polyester", "Chew strength": "Light chewers"}),
        P(WAGWORKS, "dog-toy", "Cotton Rope Tug Toy for Dogs",
          "Braided cotton rope toy for tug and fetch that also helps clean teeth. Machine washable.",
          sz(("EA", "Each", 9.99)), ["machine-washable"], {"For": "Dogs", "Material": "Cotton rope", "Length": "18 in"}),
        P(WAGWORKS, "dog-toy", "Dog Tennis Balls, 6-Pack",
          "Bouncy, felt-covered tennis balls made for dogs, with a non-abrasive felt that is gentle on teeth.",
          sz(("6PK", "6 balls", 7.99)), [], {"For": "Dogs", "Diameter": "2.5 in"}),
        P(WAGWORKS, "cat-toy", "Feather Wand Cat Toy with 3 Refills",
          "Interactive wand toy with a flexible rod and three feather and bell refills.",
          sz(("EA", "Each", 6.99)), [], {"For": "Cats"}),
        P(WAGWORKS, "cat-toy", "Catnip Mice Cat Toys, 6-Pack",
          "Six plush mice filled with organic catnip.",
          sz(("6PK", "6 mice", 4.99)), [], {"For": "Cats", "Filling": "Organic catnip"}),
        P(WAGWORKS, "cat-scratcher", "Sisal Cat Scratching Post, 32 in",
          "Tall, sturdy sisal rope scratching post with a heavy base and a dangling toy.",
          sz(("EA", "Each", 29.99)), [], {"For": "Cats", "Height": "32 in", "Material": "Sisal rope"}),
        P(WAGWORKS, "pet-bed", "Orthopedic Memory Foam Dog Bed",
          "Supportive memory foam dog bed for older dogs and achy joints, with a waterproof liner and a removable, machine-washable cover.",
          sz(("MD", "Medium, 30 x 20 in (up to 40 lb)", 49.99), ("LG", "Large, 36 x 27 in (up to 70 lb)", 69.99), ("XL", "XL, 44 x 32 in (up to 100 lb)", 89.99)),
          ["machine-washable", "waterproof"], {"For": "Dogs", "Fill": "Memory foam", "Cover": "Removable, machine washable"}),
        P(WAGWORKS, "pet-bed", "Calming Donut Pet Bed",
          "Round faux-fur donut bed with a raised rim for dogs and cats who like to curl up. Machine washable.",
          sz(("SM", "Small, 20 in (up to 15 lb)", 24.99), ("MD", "Medium, 30 in (up to 35 lb)", 34.99), ("LG", "Large, 36 in (up to 60 lb)", 44.99)),
          ["machine-washable"], {"For": "Dogs and cats", "Fill": "Polyester fiber"}),
        P(WAGWORKS, "pet-bed", "Felt Cat Cave Bed",
          "Cozy hooded cave bed made of wool-blend felt for cats who like to hide.",
          sz(("EA", "Each", 29.99)), [], {"For": "Cats", "Material": "Wool-blend felt", "Size": "16 in"}),
        P(LARKSPUR, "pet-bed", "Bolster Dog Bed",
          "Value rectangular dog bed with plush bolster sides and a machine-washable cover.",
          sz(("MD", "Medium, 28 x 22 in", 19.99), ("LG", "Large, 36 x 27 in", 29.99)),
          ["machine-washable"], {"For": "Dogs", "Fill": "Polyester fiber"}),
        with_options(WAGWORKS, "dog-leash", "Reflective Nylon Dog Leash, 6 ft",
                     "Strong 6-foot nylon leash with reflective stitching for night walks and a padded handle.",
                     ["Black", "Red", "Blue"], 12.99, "color", [], {"Length": "6 ft", "Width": "1 in", "Reflective": "Yes"}),
        P(WAGWORKS, "dog-leash", "Retractable Dog Leash, 16 ft",
          "Retractable tape leash that extends to 16 feet, with one-button brake and lock.",
          sz(("SM", "Small (dogs up to 26 lb)", 17.99), ("MD", "Medium (dogs up to 44 lb)", 19.99), ("LG", "Large (dogs up to 110 lb)", 24.99)),
          [], {"Length": "16 ft", "Type": "Tape"}),
        with_options(WAGWORKS, "dog-collar", "Adjustable Nylon Dog Collar",
                     "Adjustable nylon collar with a quick-release buckle and a metal D-ring for ID tags.",
                     ["Small (10-14 in)", "Medium (14-20 in)", "Large (18-26 in)"], 8.99, "size", [], {"Material": "Nylon", "Buckle": "Quick release"}),
        with_options(WAGWORKS, "dog-harness", "No-Pull Dog Harness",
                     "Padded no-pull harness with front and back leash clips and reflective trim. Machine washable.",
                     ["XS", "S", "M", "L", "XL"], 24.99, "size", ["machine-washable"], {"Leash clips": "Front and back", "Reflective": "Yes"}),
        P(WAGWORKS, "cat-collar", "Breakaway Cat Collars with Bell, 2-Pack",
          "Safety breakaway cat collars that release under pressure, with bells. Fit necks 8-12 in.",
          sz(("2PK", "2 collars", 6.99)), [], {"Fits": "8-12 in necks", "Buckle": "Breakaway"}),
        P(WAGWORKS, "poop-bags", "Compostable Dog Poop Bags, Unscented, 120 Count",
          "Plant-based compostable poop bags certified for home composting, leak proof and unscented. 8 rolls of 15.",
          sz(("120CT", "120 bags (8 rolls)", 11.99)), ["plant-based", "biodegradable", "fragrance-free"],
          {"Count": "120", "Material": "Plant-based compostable film", "Scent": "Unscented"}),
        P(WAGWORKS, "poop-bags", "Extra Thick Poop Bags, Unscented, 270 Count",
          "Extra-thick, leak-proof poop bags on 18 rolls that fit most dispensers. Unscented.",
          sz(("270CT", "270 bags (18 rolls)", 12.99)), ["fragrance-free"],
          {"Count": "270", "Material": "Polyethylene", "Scent": "Unscented"}),
        P(LARKSPUR, "poop-bags", "Dog Waste Bags with Dispenser, Lavender Scented, 300 Count",
          "Value lavender-scented waste bags on 20 rolls with a leash-clip dispenser.",
          sz(("300CT", "300 bags (20 rolls)", 8.99)), [],
          {"Count": "300", "Material": "Polyethylene", "Scent": "Lavender"}),
        P(WAGWORKS, "pet-bowl", "Stainless Steel Pet Bowls, 2-Pack",
          "Rust-resistant stainless steel bowls with non-skid rubber bases. Dishwasher safe.",
          sz(("SM", "Small, 2 cups each", 12.99), ("LG", "Large, 6 cups each", 17.99)),
          ["dishwasher-safe"], {"Material": "Stainless steel"}),
        P(LARKSPUR, "puppy-pads", "Puppy Training Pads",
          "Five-layer leak-proof training pads with a quick-dry top and a built-in attractant. 22 x 22 in.",
          sz(("50CT", "50 pads", 14.99), ("100CT", "100 pads", 24.99)), [],
          {"Size": "22 x 22 in", "Layers": "5"}),
    ]
# fmt: on


def products() -> list[ProductSeed]:
    return [*dog_food(), *cat_food(), *litter(), *toys_beds_gear()]
