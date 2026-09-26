"""Toys & Games: puzzles by piece count, board and card games, building sets, plush, dolls,
action figures, remote control, art supplies, STEM kits, outdoor toys, and baby toys.

Every toy states "Ages" in its specs; games also state players and play time.
"""

from __future__ import annotations

from collections.abc import Iterable

from commerce.seed.data import ProductSeed
from commerce.seed.gen.common import Size, cents, item

CAT = "toys"
PEBBLE = "Pebble & Pine"  # wooden toys, puzzles, games: premium, eco
STACKWISE = "Stackwise"  # building bricks
LARKSPUR = "Larkspur Play"  # store brand, value
DOODLEBUG = "Doodlebug Art Co."  # art supplies
CURIO = "Curio Labs"  # STEM
ZOOMTRAX = "Zoomtrax"  # RC and action figures

K = ["kids"]


def one(dollars: float, label: str = "Each", code: str = "EA") -> list[Size]:
    return [Size(code, label, cents(dollars))]


def T(
    brand: str,
    product_type: str,
    title: str,
    description: str,
    dollars: float,
    ages: str,
    tags: Iterable[str] = K,
    **specs: str,
) -> ProductSeed:
    """A single-variant toy; extra keyword specs become Title Case spec names."""
    return item(
        category=CAT, product_type=product_type, brand=brand, title=title,
        description=description, sizes=one(dollars), tags=tags,
        specs={"Ages": ages, **{k.replace("_", " ").capitalize(): v for k, v in specs.items()}},
    )  # fmt: skip


def puzzle(
    brand: str, title: str, pieces: int, ages: str, dollars: float, size: str, scene: str
) -> ProductSeed:
    board = "Thick recycled board" if brand == PEBBLE else "Sturdy cardboard"
    tags = ["recycled-materials"] if brand == PEBBLE else ["kids"]
    return T(brand, "puzzle", title,
             f"A {pieces:,}-piece jigsaw puzzle of {scene}. Finished size {size}; includes a reference poster.",
             dollars, ages, tags, pieces=str(pieces), finished_size=size, material=board)  # fmt: skip


# fmt: off
def puzzles_and_games() -> list[ProductSeed]:
    return [
        puzzle(LARKSPUR, "Farm Animals 24-Piece Floor Puzzle", 24, "3+", 9.99, "24 x 18 in", "farm animals with extra-large pieces for small hands"),
        puzzle(PEBBLE, "Ocean Friends 100-Piece Kids' Puzzle", 100, "5+", 9.99, "19 x 14 in", "whales, turtles, and fish in a coral reef"),
        puzzle(PEBBLE, "Garden Party 300-Piece Puzzle", 300, "8+", 14.99, "24 x 18 in", "a summer garden party, with large-format pieces"),
        puzzle(PEBBLE, "Mountain Lake 500-Piece Puzzle", 500, "10+", 16.99, "20 x 15 in", "a mountain lake at sunrise"),
        puzzle(PEBBLE, "Night Market 1000-Piece Puzzle", 1000, "12+", 19.99, "27 x 20 in", "a lantern-lit night market"),
        puzzle(PEBBLE, "Vintage Seed Packets 1000-Piece Puzzle", 1000, "12+", 21.99, "27 x 20 in", "a collage of illustrated vintage seed packets"),
        puzzle(PEBBLE, "Starry Canyon 2000-Piece Puzzle", 2000, "14+", 29.99, "38 x 27 in", "a desert canyon under the Milky Way"),
        T(PEBBLE, "board-game", "Treasure Isles Family Board Game",
          "Race around the islands collecting treasure and trading maps in this family board game for 2-6 players ages 8 and up.",
          24.99, "8+", K, players="2-6", play_time="30-45 minutes"),
        T(LARKSPUR, "board-game", "Hoot Hoot Owl Matching Game",
          "A cooperative first board game where preschoolers match colors to help the owls fly home. No reading required.",
          12.99, "3+", K, players="2-4", play_time="15 minutes"),
        T(PEBBLE, "board-game", "Fox & Hen Two-Player Strategy Game",
          "A quick, tactical two-player strategy game with a wooden board and pieces.",
          29.99, "10+", [], players="2", play_time="20 minutes"),
        T(LARKSPUR, "board-game", "Wooden Chess & Checkers Set",
          "Two-in-one folding wooden board with chess pieces and checkers, stored inside the board.",
          24.99, "6+", [], players="2", play_time="Varies"),
        T(PEBBLE, "party-game", "Quick Sketch Drawing Party Game",
          "Fast-paced drawing and guessing party game with 400 prompts and dry-erase boards for teams.",
          19.99, "12+", [], players="4-10", play_time="30 minutes"),
        T(LARKSPUR, "card-game", "Color Clash Card Game",
          "Classic match-the-color-or-number card game with wild cards, for 2-10 players.",
          7.99, "7+", K, players="2-10", play_time="15-30 minutes"),
        T(PEBBLE, "board-game", "Wordsmith Letter Tile Game",
          "Build crossword-style words from letter tiles in this word game for 2-4 players.",
          19.99, "8+", [], players="2-4", play_time="30 minutes"),
        T(LARKSPUR, "card-game", "Classic Playing Cards, 2 Decks",
          "Two standard 52-card decks with jokers, plastic-coated for smooth shuffling.",
          4.99, "6+", [], players="1+", play_time="Varies"),
    ]


def building_plush_dolls() -> list[ProductSeed]:
    return [
        T(STACKWISE, "building-blocks", "Classic Creative Brick Box, 500 Pieces",
          "500 building bricks in 30 colors with wheels, windows, and eyes, plus an idea booklet and a storage box.",
          29.99, "4+", K, pieces="500"),
        T(STACKWISE, "building-blocks", "City Fire Station Building Set, 780 Pieces",
          "Build a three-story fire station with a fire truck, ladder, and four minifigures.",
          69.99, "7+", K, pieces="780"),
        T(STACKWISE, "building-blocks", "Space Shuttle Explorer Building Set, 1,200 Pieces",
          "Detailed display model of a space shuttle with opening cargo bay doors and a satellite, for teens and adults.",
          99.99, "12+", [], pieces="1,200"),
        T(STACKWISE, "building-blocks", "Junior Big Bricks, 80 Pieces",
          "Large, easy-to-grip bricks sized for toddlers so they are not a choking hazard.",
          24.99, "18 months+", K, pieces="80"),
        T(CURIO, "building-blocks", "Magnetic Building Tiles, 60 Pieces",
          "Translucent magnetic tiles in squares and triangles for building 2D and 3D shapes.",
          39.99, "3+", K, pieces="60"),
        T(PEBBLE, "plush-toy", "Plush Brown Bear, 16 in",
          "Huggable 16-inch plush bear with embroidered eyes, safe from birth and surface washable.",
          19.99, "0+", K, size="16 in"),
        T(PEBBLE, "plush-toy", "Plush Unicorn, 14 in",
          "Soft 14-inch plush unicorn with a sparkly horn and rainbow mane.",
          16.99, "3+", K, size="14 in"),
        T(LARKSPUR, "plush-toy", "Jumbo Plush Golden Retriever, 36 in",
          "Giant 36-inch plush golden retriever for cuddling and lounging.",
          39.99, "3+", K, size="36 in"),
        T(LARKSPUR, "doll", "18-Inch Doll with Outfit and Hairbrush",
          "18-inch soft-body doll with long brushable hair, a removable outfit, shoes, and a hairbrush.",
          24.99, "3+", K, size="18 in"),
        T(LARKSPUR, "doll", "Baby Doll with Bottle and Blanket, 12 in",
          "Soft-bodied 12-inch baby doll with a pretend bottle and blanket.",
          14.99, "2+", K, size="12 in"),
        T(LARKSPUR, "doll", "Fashion Doll with Accessories, 11.5 in",
          "Poseable 11.5-inch fashion doll with two outfits and accessories.",
          9.99, "3+", K, size="11.5 in"),
        T(PEBBLE, "dollhouse", "Wooden Dollhouse with 16 Furniture Pieces",
          "Three-story wooden dollhouse with an open back, stairs, and 16 pieces of furniture. Fits dolls up to 5 inches.",
          89.99, "3+", K, pieces="16 furniture pieces", size="30 x 24 x 11 in"),
        T(ZOOMTRAX, "action-figure", "Starbound Heroes Captain Nova 6-Inch Action Figure",
          "Poseable 6-inch action figure with 20 points of articulation and a light-up blaster accessory.",
          12.99, "4+", K, size="6 in"),
        T(ZOOMTRAX, "action-figure", "Starbound Heroes Command Base Playset",
          "Two-level command base playset with a launcher, lights and sounds, and one figure included.",
          44.99, "4+", K),
        T(ZOOMTRAX, "action-figure", "Dinosaur Figure Set, 12 Pieces",
          "Twelve realistic dinosaur figures from 4 to 7 inches, including a T. rex, triceratops, and stegosaurus.",
          19.99, "3+", K, pieces="12"),
    ]


def rc_art_stem() -> list[ProductSeed]:
    return [
        T(ZOOMTRAX, "rc-car", "Stunt RC Car with 360° Flips",
          "Double-sided remote control stunt car that flips and spins 360°, with a rechargeable USB-C battery.",
          34.99, "6+", [*K, "rechargeable", "usb-c"], top_speed="8 mph", run_time="20 minutes"),
        T(ZOOMTRAX, "rc-car", "My First RC Car",
          "Chunky, easy two-button remote control car for toddlers with lights and sounds. Uses AA batteries (included).",
          24.99, "2+", K, top_speed="3 mph"),
        T(ZOOMTRAX, "drone", "Mini Camera Drone",
          "Beginner-friendly foldable drone under 250 g with a 1080p camera, altitude hold, and two rechargeable batteries.",
          59.99, "14+", ["rechargeable", "usb-c"], flight_time="2 x 12 minutes", weight="245 g"),
        T(DOODLEBUG, "crayons", "Washable Crayons, 24 Count",
          "Bright washable crayons that wash off skin, walls, and most clothing with soap and water. Non-toxic.",
          2.99, "3+", K, count="24", washable="Yes"),
        T(DOODLEBUG, "markers", "Washable Broad Line Markers, 10 Count",
          "Chunky washable markers in 10 classic colors with ink that washes off skin and most fabrics.",
          4.99, "3+", K, count="10", washable="Yes", tip="Broad (conical)"),
        T(DOODLEBUG, "markers", "Washable Fine Line Markers, 40 Count",
          "Forty washable fine-tip markers for detailed drawing and coloring books.",
          11.99, "4+", K, count="40", washable="Yes", tip="Fine"),
        T(DOODLEBUG, "colored-pencils", "Pre-Sharpened Colored Pencils, 24 Count",
          "Twenty-four pre-sharpened colored pencils with break-resistant cores.",
          4.99, "5+", K, count="24"),
        T(DOODLEBUG, "paint", "Washable Kids' Paint Set, 6 Colors",
          "Six 8 oz bottles of washable tempera paint that cleans up with soap and water. Non-toxic.",
          9.99, "3+", K, count="6 bottles", washable="Yes"),
        T(DOODLEBUG, "modeling-dough", "Modeling Dough, 10-Pack",
          "Ten 2 oz tubs of soft, non-toxic modeling dough in bright colors. Made with wheat flour; not for children with wheat allergy.",
          9.99, "2+", K, count="10 tubs", allergy_note="Contains wheat"),
        T(DOODLEBUG, "sidewalk-chalk", "Jumbo Sidewalk Chalk, 48 Pieces",
          "Forty-eight jumbo chalk sticks in 12 colors that wash away with water.",
          7.99, "3+", K, count="48"),
        T(CURIO, "stem-kit", "Crystal Growing Science Kit",
          "Grow seven colorful crystals and a display geode and learn how crystals form. Adult supervision required.",
          19.99, "10+", K, experiments="7 crystals"),
        T(CURIO, "stem-kit", "Erupting Volcano Science Kit",
          "Build and paint a volcano, then make it erupt again and again with baking soda reactions.",
          14.99, "6+", K, experiments="5"),
        T(CURIO, "stem-kit", "Snap-Together Circuits Kit, 100+ Projects",
          "Snap-together electronic parts that build over 100 working circuits like alarms, lights, and a fan. Uses AA batteries (not included).",
          39.99, "8+", K, projects="100+"),
        T(CURIO, "stem-kit", "Code & Roll Coding Robot",
          "Screen-free coding robot that kids program with arrow cards and a free app, with a rechargeable USB-C battery.",
          59.99, "8+", [*K, "rechargeable", "usb-c", "bluetooth"], battery="Rechargeable, 90 minutes"),
        T(CURIO, "telescope", "Kids' Beginner Telescope, 70 mm",
          "70 mm refractor telescope with a tabletop tripod, two eyepieces, and a moon map.",
          49.99, "8+", K, aperture="70 mm"),
        T(CURIO, "microscope", "Kids' Microscope Kit, 40x-1000x",
          "Beginner microscope with LED lighting, prepared slides, and tools for making your own.",
          34.99, "8+", K, magnification="40x-1000x"),
    ]


def outdoor_and_baby() -> list[ProductSeed]:
    return [
        T(LARKSPUR, "outdoor-toy", "Automatic Bubble Machine",
          "Battery-powered bubble machine that blows hundreds of bubbles a minute; includes 8 oz of bubble solution.",
          19.99, "3+", K, power="4 AA batteries (not included)"),
        T(LARKSPUR, "outdoor-toy", "Water Blasters, 4-Pack",
          "Four pump-action foam water blasters that shoot up to 25 feet.",
          14.99, "6+", K, range="Up to 25 ft"),
        T(ZOOMTRAX, "scooter", "3-Wheel Kick Scooter with Light-Up Wheels",
          "Lean-to-steer three-wheel scooter with light-up wheels and an adjustable handlebar. Holds up to 110 lb.",
          39.99, "3-5", K, weight_limit="110 lb"),
        T(LARKSPUR, "outdoor-toy", "Playground Balls, 8.5 in, 3-Pack",
          "Three bouncy 8.5-inch rubber playground balls with a hand pump.",
          12.99, "3+", K, size="8.5 in"),
        T(PEBBLE, "baby-toy", "Wooden Stacking Rings",
          "Classic stacking toy with smooth hardwood rings finished in water-based, child-safe paint.",
          14.99, "12 months+", K, material="Hardwood, water-based paint"),
        T(LARKSPUR, "baby-toy", "Soft Stacking Blocks, 12 Pieces",
          "Squishy fabric blocks with textures, crinkle, and a rattle that are safe to mouth.",
          14.99, "6 months+", K, pieces="12"),
        T(LARKSPUR, "baby-toy", "Musical Light-Up Baby Piano",
          "Kick-and-play piano mat with lights, songs, and animal sounds for tummy time and sitting babies.",
          19.99, "6 months+", K, power="3 AA batteries (included)"),
        T(PEBBLE, "baby-toy", "Wooden Activity Cube",
          "Five-sided wooden activity cube with a bead maze, shape sorter, gears, and sliders.",
          39.99, "12 months+", K, material="Hardwood, water-based paint"),
    ]
# fmt: on


def products() -> list[ProductSeed]:
    return [*puzzles_and_games(), *building_plush_dolls(), *rc_art_stem(), *outdoor_and_baby()]
