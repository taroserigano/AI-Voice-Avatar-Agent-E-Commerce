"""Office & School: notebooks, pens and pencils, markers, paper, sticky notes, planners,
binders and filing, desk organization, staplers, scissors, calculators, backpacks, lunch
boxes, labels, and mailing supplies.
"""

from __future__ import annotations

from collections.abc import Iterable

from commerce.seed.data import ProductSeed
from commerce.seed.gen.common import Size, cents, item, options, slugify

CAT = "office"
QUILLMARK = "Quillmark"  # premium stationery
OWN_BRAND = "Serigan Mart Office"  # store brand, value
DESKWISE = "Deskwise"  # desk tools and calculators
BOOKBUG = "Bookbug"  # kids' backpacks and lunch boxes


def one(dollars: float, label: str = "Each", code: str = "EA") -> list[Size]:
    return [Size(code, label, cents(dollars))]


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
def paper_goods() -> list[ProductSeed]:
    return [
        P(OWN_BRAND, "notebook", "Spiral Notebooks, College Ruled, 70 Sheets, 5-Pack",
          "Five single-subject spiral notebooks with 70 college-ruled sheets each, perforated pages, and assorted color covers. 8 x 10.5 in.",
          one(4.99, "5 notebooks", "5PK"), [], {"Ruling": "College ruled", "Size": "8 x 10.5 in", "Sheets": "70 per notebook", "Binding": "Spiral"}),
        P(OWN_BRAND, "notebook", "Spiral Notebooks, Wide Ruled, 70 Sheets, 5-Pack",
          "Five single-subject spiral notebooks with 70 wide-ruled sheets each for younger students. 8 x 10.5 in.",
          one(4.99, "5 notebooks", "5PK"), [], {"Ruling": "Wide ruled", "Size": "8 x 10.5 in", "Sheets": "70 per notebook", "Binding": "Spiral"}),
        P(OWN_BRAND, "notebook", "Composition Notebooks, Wide Ruled, 4-Pack",
          "Four sewn-binding marble composition notebooks with 100 wide-ruled sheets each. 9.75 x 7.5 in.",
          one(5.99, "4 notebooks", "4PK"), [], {"Ruling": "Wide ruled", "Size": "9.75 x 7.5 in", "Sheets": "100 per notebook", "Binding": "Sewn"}),
        P(OWN_BRAND, "notebook", "Graph Ruled Composition Notebook, 4 x 4",
          "Composition notebook with 100 sheets of quad-ruled graph paper (4 squares per inch) for math and science.",
          one(2.49), [], {"Ruling": "Graph (4 squares per inch)", "Size": "9.75 x 7.5 in", "Sheets": "100", "Binding": "Sewn"}),
        colors(QUILLMARK, "notebook", "Ruled Hardcover Notebook, A5",
               "A5 hardcover notebook with 192 pages of lined, fountain-pen friendly 100 gsm paper, a ribbon marker, and an elastic closure.",
               ["Forest", "Navy", "Black"], 14.99, [], {"Ruling": "Lined (6 mm)", "Size": "A5 (5.8 x 8.3 in)", "Pages": "192", "Paper": "100 gsm"}),
        P(QUILLMARK, "notebook", "Graph Hardcover Notebook, A5",
          "A5 hardcover notebook with 192 pages of 5 mm graph paper, numbered pages, and an index.",
          one(14.99), [], {"Ruling": "Graph (5 mm)", "Size": "A5 (5.8 x 8.3 in)", "Pages": "192", "Paper": "100 gsm"}),
        P(QUILLMARK, "notebook", "Dotted Softcover Journals, B5, 2-Pack",
          "Two lay-flat softcover journals with 80 pages of dotted paper each, great for bullet journaling. B5 size.",
          one(16.99, "2 journals", "2PK"), [], {"Ruling": "Dotted (5 mm)", "Size": "B5 (6.9 x 9.8 in)", "Pages": "80 per journal", "Paper": "100 gsm"}),
        P(OWN_BRAND, "legal-pad", "Legal Pads, Yellow, 12-Pack",
          "Twelve perforated yellow legal pads with 50 wide-ruled sheets each. 8.5 x 11.75 in.",
          one(11.99, "12 pads", "12PK"), [], {"Ruling": "Wide ruled", "Size": "8.5 x 11.75 in", "Sheets": "50 per pad"}),
        P(OWN_BRAND, "copy-paper", "Multipurpose Copy Paper, 8.5 x 11 in, 20 lb",
          "Bright white 20 lb multipurpose paper for printers, copiers, and fax machines. 500 sheets per ream.",
          [Size("1RM", "1 ream (500 sheets)", cents(8.99)), Size("10RM", "Case of 10 reams (5,000 sheets)", cents(49.99))], [],
          {"Size": "8.5 x 11 in", "Weight": "20 lb", "Brightness": "92", "Sheets": "500 per ream"}),
        P(OWN_BRAND, "copy-paper", "30% Recycled Copy Paper, 8.5 x 11 in, 500 Sheets",
          "20 lb copy paper made with 30% post-consumer recycled content. 500 sheets.",
          one(9.49, "1 ream (500 sheets)", "1RM"), ["recycled-materials"], {"Size": "8.5 x 11 in", "Weight": "20 lb", "Recycled content": "30% post-consumer"}),
        P(QUILLMARK, "copy-paper", "Premium Bright White Paper, 24 lb, 500 Sheets",
          "Heavier 24 lb, 97-bright paper for crisp presentations and double-sided printing.",
          one(12.99, "1 ream (500 sheets)", "1RM"), [], {"Size": "8.5 x 11 in", "Weight": "24 lb", "Brightness": "97"}),
        P(OWN_BRAND, "sticky-notes", "Sticky Notes, 3 x 3 in, Pastel, 12 Pads",
          "Twelve pads of 3 x 3 in pastel sticky notes, 100 sheets per pad.",
          one(7.99, "12 pads", "12PK"), [], {"Size": "3 x 3 in", "Sheets": "100 per pad"}),
        P(QUILLMARK, "sticky-notes", "Super Sticky Lined Notes, 4 x 6 in, 5 Pads",
          "Extra-strong adhesive lined sticky notes that stay put on walls and monitors. 5 pads of 45 sheets.",
          one(9.99, "5 pads", "5PK"), [], {"Size": "4 x 6 in", "Ruling": "Lined", "Sheets": "45 per pad"}),
        P(QUILLMARK, "planner", "Undated Weekly Planner, A5",
          "Undated A5 weekly planner with 52 week-on-two-pages spreads, monthly calendars, goal pages, and a ribbon marker; start any time.",
          one(19.99), [], {"Layout": "Week on two pages", "Dated": "Undated", "Size": "A5"}),
        P(QUILLMARK, "planner", "Undated Daily Planner",
          "Undated daily planner with a full page per day, hourly schedule, to-do list, and habit tracker for 6 months.",
          one(24.99), [], {"Layout": "Day per page", "Dated": "Undated", "Size": "7 x 9 in", "Duration": "6 months"}),
    ]


def writing_and_desk() -> list[ProductSeed]:
    return [
        P(OWN_BRAND, "pens", "Ballpoint Pens, Medium Point, Black, 60-Pack",
          "Sixty smooth-writing 1.0 mm black ballpoint pens with capped barrels.",
          one(7.99, "60 pens", "60PK"), [], {"Ink": "Black ballpoint", "Point": "Medium (1.0 mm)", "Count": "60"}),
        P(QUILLMARK, "pens", "Fine Liner Pens, 0.4 mm, 10 Colors",
          "Ten fine-tip felt liner pens with water-based ink that won't bleed through most paper.",
          one(12.99, "10 pens", "10PK"), [], {"Ink": "Water-based felt tip", "Point": "0.4 mm", "Count": "10"}),
        P(QUILLMARK, "pens", "Retractable Gel Pens, 0.7 mm, Black, 12-Pack",
          "Twelve retractable black gel pens with a comfortable grip and smooth, bold lines.",
          one(11.99, "12 pens", "12PK"), [], {"Ink": "Black gel", "Point": "0.7 mm", "Count": "12"}),
        P(OWN_BRAND, "pencils", "#2 Pencils, Pre-Sharpened, 24-Pack",
          "Twenty-four pre-sharpened #2 HB wood pencils with latex-free erasers.",
          one(3.99, "24 pencils", "24PK"), [], {"Lead": "#2 HB", "Count": "24", "Eraser": "Latex free"}),
        P(OWN_BRAND, "pencils", "Mechanical Pencils, 0.7 mm, 10-Pack",
          "Ten refillable 0.7 mm mechanical pencils with erasers and extra lead.",
          one(5.99, "10 pencils", "10PK"), [], {"Lead": "0.7 mm HB", "Count": "10"}),
        P(DESKWISE, "pencil-sharpener", "Electric Pencil Sharpener",
          "Plug-in or battery-powered electric pencil sharpener with auto stop and a large shavings bin.",
          one(19.99), [], {"Power": "AC adapter or 4 AA batteries", "Fits": "Standard #2 and colored pencils"}),
        P(OWN_BRAND, "highlighters", "Highlighters, Chisel Tip, Assorted, 12-Pack",
          "Twelve chisel-tip highlighters in six bright colors with smear-resistant ink.",
          one(6.99, "12 highlighters", "12PK"), [], {"Tip": "Chisel", "Count": "12", "Colors": "6"}),
        P(OWN_BRAND, "markers", "Dry Erase Markers, Chisel Tip, Low Odor, 12-Pack",
          "Twelve low-odor dry erase markers that wipe clean from whiteboards.",
          one(9.99, "12 markers", "12PK"), [], {"Tip": "Chisel", "Count": "12", "Odor": "Low"}),
        P(OWN_BRAND, "markers", "Permanent Markers, Fine Point, Black, 12-Pack",
          "Twelve quick-drying, water-resistant black fine point permanent markers.",
          one(7.99, "12 markers", "12PK"), [], {"Tip": "Fine", "Count": "12", "Color": "Black"}),
        colors(OWN_BRAND, "binder", "1-Inch 3-Ring Binder",
               "Durable 1-inch round-ring binder with a clear view cover and two inside pockets; holds about 175 sheets.",
               ["Black", "Blue", "Red", "White"], 2.99, [], {"Ring size": "1 in", "Ring type": "Round", "Capacity": "175 sheets"}),
        P(OWN_BRAND, "binder", "2-Inch Heavy-Duty D-Ring Binder",
          "Heavy-duty 2-inch D-ring binder with a view cover; holds about 500 sheets.",
          one(7.99), [], {"Ring size": "2 in", "Ring type": "D-ring", "Capacity": "500 sheets"}),
        P(OWN_BRAND, "folders", "Two-Pocket Folders with Prongs, 12-Pack",
          "Twelve durable poly two-pocket folders with three-prong fasteners in assorted colors.",
          one(6.99, "12 folders", "12PK"), [], {"Material": "Polypropylene", "Count": "12"}),
        P(OWN_BRAND, "folders", "Hanging File Folders, Letter Size, 25-Pack",
          "Twenty-five letter-size hanging file folders with tabs and inserts.",
          one(12.99, "25 folders", "25PK"), [], {"Size": "Letter", "Count": "25"}),
        P(OWN_BRAND, "sheet-protectors", "Sheet Protectors, 100-Pack",
          "One hundred clear top-loading sheet protectors that fit 3-ring binders.",
          one(9.99, "100 protectors", "100PK"), [], {"Size": "8.5 x 11 in", "Count": "100"}),
        P(DESKWISE, "file-organizer", "13-Pocket Expanding File Organizer",
          "Portable accordion file with 13 labeled pockets and an elastic closure for receipts and documents.",
          one(14.99), [], {"Pockets": "13", "Size": "Letter"}),
        P(DESKWISE, "desk-organizer", "Mesh Desk Organizer with Drawer",
          "Black steel mesh desk organizer with upright file slots, a pen cup, and a sliding drawer.",
          one(19.99), [], {"Material": "Steel mesh", "Compartments": "5 plus drawer"}),
        P(DESKWISE, "desk-organizer", "Monitor Stand Riser with Drawer",
          "Wood-and-metal monitor riser that lifts screens to eye level, with a storage drawer underneath.",
          one(29.99), [], {"Size": "20 x 9 x 4 in", "Weight capacity": "44 lb"}),
        P(DESKWISE, "stapler", "Desktop Stapler with 1,000 Staples",
          "Full-strip desktop stapler that staples up to 20 sheets, with 1,000 standard staples included.",
          one(9.99), [], {"Capacity": "20 sheets", "Staples included": "1,000"}),
        P(OWN_BRAND, "staples", "Standard Staples, 5,000 Count",
          "Standard 1/4-inch staples for most desktop staplers.",
          one(3.49, "5,000 staples", "5000CT"), [], {"Size": "Standard 1/4 in", "Count": "5,000"}),
        P(DESKWISE, "scissors", "8-Inch Scissors, 3-Pack",
          "Three all-purpose stainless steel scissors with soft-grip handles.",
          one(9.99, "3 pairs", "3PK"), [], {"Blade": "Stainless steel, 8 in", "Count": "3"}),
        P(OWN_BRAND, "scissors", "Kids' Blunt-Tip Scissors, 2-Pack",
          "Two pairs of 5-inch blunt-tip safety scissors for kids ages 4 and up.",
          one(3.99, "2 pairs", "2PK"), ["kids"], {"Blade": "Stainless steel, 5 in, blunt tip", "Ages": "4+"}),
        P(DESKWISE, "calculator", "Basic Desktop Calculator, Solar and Battery",
          "Eight-digit desktop calculator with a large display, powered by solar with battery backup.",
          one(7.99), [], {"Type": "Basic", "Digits": "8", "Power": "Solar with battery backup"}),
        P(DESKWISE, "calculator", "Scientific Calculator",
          "Two-line scientific calculator with 240 functions for algebra, trigonometry, and statistics.",
          one(14.99), [], {"Type": "Scientific", "Functions": "240", "Power": "Solar with battery backup"}),
        P(DESKWISE, "calculator", "Graphing Calculator",
          "Color-screen graphing calculator with a rechargeable battery for high school and college math, allowed on most standardized tests.",
          one(99.99), ["rechargeable", "usb-c"], {"Type": "Graphing", "Display": "Color", "Power": "Rechargeable, USB-C"}),
    ]


def carry_and_mail() -> list[ProductSeed]:
    return [
        colors(BOOKBUG, "backpack", "Kids' School Backpack, 16 in",
               "Water-resistant kids' backpack with a padded back, a chest strap, a front organizer pocket, and two side bottle pockets. Ages 5-10.",
               ["Navy Dinosaurs", "Purple Stars", "Teal Rockets"], 24.99, ["kids", "water-resistant"], {"Height": "16 in", "Laptop sleeve": "No", "Ages": "5-10"}),
        colors(OWN_BRAND, "backpack", "Classic Backpack, 17 in",
               "Value everyday backpack with a padded laptop sleeve for up to 15 in laptops and two side pockets.",
               ["Black", "Gray", "Navy"], 19.99, [], {"Height": "17 in", "Laptop sleeve": "Up to 15 in"}),
        colors(BOOKBUG, "lunch-box", "Insulated Kids' Lunch Box",
               "Soft insulated lunch box with a BPA-free, leak-resistant lining and a name tag. Wipe clean.",
               ["Navy Dinosaurs", "Purple Stars"], 14.99, ["kids", "bpa-free"], {"Insulated": "Yes", "Lining": "BPA-free PEVA"}),
        P(BOOKBUG, "lunch-box", "Bento Lunch Box, 5 Compartments",
          "Leak-proof bento box with five compartments for kids' lunches. BPA free and top-rack dishwasher safe.",
          one(19.99), ["kids", "bpa-free", "dishwasher-safe"], {"Compartments": "5", "Material": "BPA-free plastic, silicone seal", "Leak proof": "Yes"}),
        P(OWN_BRAND, "lunch-box", "Insulated Lunch Bag, Adult",
          "Roomy insulated lunch bag for adults with a BPA-free lining, a front pocket, and a shoulder strap.",
          one(12.99), ["bpa-free"], {"Insulated": "Yes", "Lining": "BPA-free PEVA", "Capacity": "9 L"}),
        P(OWN_BRAND, "labels", "Address Labels, 1 x 2-5/8 in, 750 Labels",
          "White laser and inkjet address labels, 30 per sheet on 25 sheets.",
          one(9.99, "750 labels", "750CT"), [], {"Size": "1 x 2-5/8 in", "Per sheet": "30", "Printer": "Laser and inkjet"}),
        P(DESKWISE, "label-maker", "Handheld Label Maker with Tape",
          "Handheld label maker with a QWERTY keyboard, 6 fonts, and one roll of 12 mm tape. Uses 6 AAA batteries (not included).",
          one(29.99), [], {"Tape width": "12 mm", "Keyboard": "QWERTY", "Power": "6 AAA batteries"}),
        P(OWN_BRAND, "envelopes", "#10 Security Envelopes, Self-Seal, 100 Count",
          "One hundred #10 business envelopes with a security tint and a self-seal flap.",
          one(7.99, "100 envelopes", "100CT"), [], {"Size": "#10 (4-1/8 x 9-1/2 in)", "Closure": "Self seal", "Security tint": "Yes"}),
        P(OWN_BRAND, "envelopes", "Manila Catalog Envelopes, 9 x 12 in, 25 Count",
          "Twenty-five 9 x 12 in manila catalog envelopes with a gummed flap.",
          one(6.99, "25 envelopes", "25CT"), [], {"Size": "9 x 12 in", "Closure": "Gummed"}),
        P(OWN_BRAND, "mailers", "Bubble Mailers, 6 x 10 in, 25-Pack",
          "Twenty-five padded bubble mailers with a self-seal strip for shipping small items.",
          one(11.99, "25 mailers", "25PK"), [], {"Size": "6 x 10 in (#0)", "Closure": "Self seal"}),
    ]
# fmt: on


def products() -> list[ProductSeed]:
    return [*paper_goods(), *writing_and_desk(), *carry_and_mail()]
