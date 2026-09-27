"""Spec rows for generated products whose description states a fact their row didn't record.

Each value restates the product's own description ("with a matching scoop" -> "Includes:
Matching scoop"), so it can't disagree with the listing. ``commerce.seed.specs`` merges these
in as the product's own rows; the test suite checks every slug here exists.
"""

from __future__ import annotations

DESCRIPTION_SPECS: dict[str, dict[str, str]] = {
    # Household and baby
    "freshfield-oxi-laundry-stain-remover-spray": {"Removes": "Food, grass, and grease stains"},
    "freshfield-dishwasher-rinse-aid": {"Benefits": "Faster drying; no spots or film on glassware"},
    "freshfield-foaming-bathroom-cleaner": {"Removes": "Soap scum and hard water stains"},
    "pillowmere-facial-tissues-with-lotion-4-boxes": {"Box style": "Cube"},
    "snugglebee-little-splashers-swim-diapers": {"Sides": "Tear-away, for easy changes"},
    "snugglebee-nighttime-youth-pants": {"Fit": "Discreet under pajamas"},
    "freshfield-non-scratch-scrub-sponges-6-pack": {
        "Sides": "Dual-sided", "Safe on": "Nonstick cookware",
    },
    "larkspur-kitchen-heavy-duty-scrub-sponges-9-pack": {
        "Best for": "Baked-on food on pots, pans, and grills", "Nonstick safe": "No",
    },
    "larkspur-baby-bottle-brush-set-with-nipple-cleaner": {
        "Includes": "Built-in nipple cleaner and drying stand",
    },
    # Pet
    "wagworks-high-sided-litter-box-with-scoop": {"Entry": "Low", "Includes": "Matching scoop"},
    "wagworks-dog-tennis-balls-6-pack": {"Felt": "Non-abrasive, gentle on teeth"},
    "wagworks-feather-wand-cat-toy-with-3-refills": {
        "Style": "Interactive wand", "Rod": "Flexible",
        "Includes": "3 feather and bell refills",
    },
    "wagworks-catnip-mice-cat-toys-6-pack": {"Material": "Plush"},
    "wagworks-sisal-cat-scratching-post-32-in": {"Base": "Heavy", "Extras": "Dangling toy"},
    "wagworks-felt-cat-cave-bed": {"Style": "Hooded cave"},
    # Home and kitchen
    "kettleworth-7-inch-santoku-knife": {"Edge": "Hollow edge, so slices don't stick"},
    "kettleworth-3-5-inch-paring-knife": {"Use": "Peeling and detail work"},
    "kettleworth-9-inch-serrated-bread-knife": {"Use": "Crusty bread and tomatoes"},
    "kettleworth-two-stage-knife-sharpener": {"Type": "Manual", "Slots": "2 (coarse and fine)"},
    "harbor-home-woven-seagrass-storage-baskets-set-of-3": {
        "Handles": "Yes", "Sizes": "Three nesting sizes", "Made": "Handwoven",
    },
    "larkspur-home-smooth-edge-can-opener": {
        "Cut": "Below the rim, for smooth edges", "Grips": "Soft", "Use": "Opening cans",
    },
    "larkspur-home-peva-shower-curtain-liner-clear": {
        "Extras": "Magnets and rust-proof grommets",
    },
    "airloft-replacement-true-hepa-filter-for-small-room-air-purifier": {
        "Filter type": "True HEPA plus carbon",
    },
    # Outdoor and garden
    "emberline-grills-bristle-free-grill-brush": {
        "Bristles": "None (coil style)", "Extras": "Scraper",
    },
    "verdant-grounds-bypass-pruning-shears": {"Type": "Bypass"},
    "verdant-grounds-hand-trowel-transplanter-and-cultivator-set": {
        "Includes": "Trowel, transplanter, and cultivator", "Grips": "Comfort grips",
    },
    "verdant-grounds-round-point-digging-shovel": {"Blade": "Round point", "Grip": "Cushioned"},
    "verdant-grounds-adjustable-steel-leaf-rake": {"Head": "Adjustable steel tines"},
    "verdant-grounds-expandable-garden-hose-100-ft": {
        "Nozzle patterns": "10", "Storage": "Shrinks back when the water is off",
    },
    "verdant-grounds-10-pattern-hose-spray-nozzle": {"Flow control": "Thumb valve"},
    "verdant-grounds-oscillating-lawn-sprinkler": {
        "Type": "Oscillating", "Adjustments": "Range and width",
    },
    "verdant-grounds-organic-potting-mix": {
        "Certification": "OMRI-listed organic", "Drainage": "Perlite",
    },
    "verdant-grounds-metal-tube-bird-feeder-6-ports": {
        "Material": "Metal", "Squirrel resistant": "Yes",
    },
    "verdant-grounds-glass-hummingbird-feeder-16-oz": {"Material": "Glass", "Ant moat": "Built-in"},
    # Sports
    "tempo-athletics-rubber-hex-dumbbell-single": {"Shape": "Hex", "Handle": "Knurled chrome"},
    "tempo-athletics-cast-iron-kettlebell": {
        "Handle": "Wide, smooth", "Base": "Flat", "Color coded": "By weight",
    },
    "larkspur-sport-basic-pvc-jump-rope": {"Material": "PVC"},
    "tempo-athletics-resistance-tube-set-with-handles-11-piece": {
        "Includes": "5 stackable tubes, handles, ankle straps, and a door anchor",
    },
    "tempo-athletics-weighted-jump-rope-1-lb": {"Benefit": "Builds upper-body strength"},
    "spokehaven-kids-bike-helmet": {"Fit": "Dial-fit system"},
    "spokehaven-u-lock-with-4-ft-cable": {"Includes": "Mounting bracket"},
    "courtline-official-size-7-indoor-outdoor-basketball": {"Grip": "Deep channels"},
    "courtline-rubber-outdoor-basketball": {"Durability": "Built for outdoor courts"},
    "courtline-composite-football": {"Surface": "Pebbled, grippy", "Laces": "Raised"},
    "courtline-indoor-outdoor-volleyball": {"Feel": "Soft-touch"},
    "courtline-junior-tennis-racquet": {"Weight": "Lightweight"},
    # Toys
    "stackwise-classic-creative-brick-box-500-pieces": {
        "Colors": "30", "Includes": "Wheels, windows, eyes, an idea booklet, and a storage box",
    },
    "stackwise-city-fire-station-building-set-780-pieces": {
        "Includes": "Fire truck, ladder, and 4 minifigures",
    },
    "stackwise-space-shuttle-explorer-building-set-1-200-pieces": {
        "Features": "Opening cargo bay doors and a satellite", "Use": "Display model",
    },
    "stackwise-junior-big-bricks-80-pieces": {
        "Brick size": "Large and easy to grip, too big to be a choking hazard",
    },
    "curio-labs-magnetic-building-tiles-60-pieces": {
        "Shapes": "Squares and triangles", "Material": "Translucent magnetic tiles",
    },
    "larkspur-play-18-inch-doll-with-outfit-and-hairbrush": {
        "Body": "Soft", "Includes": "Removable outfit, shoes, and hairbrush",
    },
    "larkspur-play-baby-doll-with-bottle-and-blanket-12-in": {
        "Body": "Soft", "Includes": "Pretend bottle and blanket",
    },
    "larkspur-play-fashion-doll-with-accessories-11-5-in": {
        "Poseable": "Yes", "Includes": "Two outfits and accessories",
    },
    "zoomtrax-starbound-heroes-captain-nova-6-inch-action-figure": {
        "Articulation": "20 points", "Accessory": "Light-up blaster",
    },
    "zoomtrax-starbound-heroes-command-base-playset": {
        "Levels": "2", "Features": "Lights and sounds", "Includes": "Launcher and one figure",
    },
    "zoomtrax-dinosaur-figure-set-12-pieces": {"Figure size": "4 to 7 in"},
    "doodlebug-art-co-pre-sharpened-colored-pencils-24-count": {"Cores": "Break-resistant"},
    "doodlebug-art-co-jumbo-sidewalk-chalk-48-pieces": {"Colors": "12", "Stick size": "Jumbo"},
    "curio-labs-crystal-growing-science-kit": {
        "Includes": "Display geode", "Supervision": "Adult supervision required",
    },
    "curio-labs-erupting-volcano-science-kit": {
        "Reaction": "Baking soda", "Reusable": "Erupts again and again",
    },
    "curio-labs-snap-together-circuits-kit-100-projects": {
        "Power": "AA batteries (not included)",
    },
    "larkspur-play-automatic-bubble-machine": {"Includes": "8 oz bubble solution"},
    "zoomtrax-3-wheel-kick-scooter-with-light-up-wheels": {
        "Steering": "Lean-to-steer", "Wheels": "3, light-up", "Handlebar": "Adjustable",
    },
    "pebble-and-pine-wooden-stacking-rings": {"Batteries": "None required"},
    "larkspur-play-soft-stacking-blocks-12-pieces": {
        "Material": "Fabric", "Features": "Textures, crinkle, and a rattle",
    },
    "larkspur-play-musical-light-up-baby-piano": {"Features": "Lights, songs, and animal sounds"},
    "pebble-and-pine-wooden-activity-cube": {
        "Sides": "5", "Activities": "Bead maze, shape sorter, gears, and sliders",
    },
    # Beauty and personal care
    "larkspur-basics-flexible-hold-hairspray": {
        "Form": "Aerosol spray", "Humidity resistant": "Yes",
    },
    "larkspur-basics-shea-butter-moisturizing-body-wash": {"Form": "Creamy liquid"},
    "larkspur-basics-cocoa-butter-body-lotion": {
        "Form": "Lotion", "Key ingredients": "Cocoa butter, vitamin E",
    },
    "larkspur-basics-makeup-remover-wipes-3-pack": {
        "Removes": "Makeup, including waterproof mascara",
    },
    "larkspur-basics-spf-15-lip-balm-3-pack": {"Flavor": "Mint", "Broad spectrum": "Yes"},
    "larkspur-basics-moisturizing-beauty-bars-8-pack-original": {"Benefit": "Moisturizing"},
    "pearlwell-soft-manual-toothbrushes-4-pack": {
        "Extras": "Tongue cleaner", "Grip": "Non-slip",
    },
    "pearlwell-floss-picks-150-count": {
        "Form": "Floss picks with a toothpick end", "Use": "On-the-go flossing",
    },
    "larkspur-basics-disposable-razors-3-blade-12-pack": {
        "Head": "Pivoting", "Extras": "Aloe strip",
    },
    "larkspur-basics-nail-clipper-set-3-pieces": {
        "Includes": "Fingernail clipper, toenail clipper, and nail file",
    },
    "keenedge-men-s-5-blade-razor-with-2-cartridges": {
        "Head": "Pivoting", "Extras": "Lubricating strip and precision trimmer",
    },
    "keenedge-women-s-5-blade-razor-with-2-cartridges": {
        "Handle": "Curved", "Extras": "Shea butter moisture bar",
    },
    "keenedge-stainless-steel-safety-razor-with-10-blades": {"Plastic-free": "Yes"},
    "larkspur-basics-acetone-free-nail-polish-remover": {"Key ingredients": "Vitamin E"},
    # Office
    "larkspur-office-sticky-notes-3-x-3-in-pastel-12-pads": {
        "Count": "12 pads", "Colors": "Pastel",
    },
    "quillmark-undated-weekly-planner-a5": {
        "Pages": "52 weekly spreads, monthly calendars, and goal pages",
        "Extras": "Ribbon marker",
    },
    "larkspur-office-mechanical-pencils-0-7-mm-10-pack": {
        "Refillable": "Yes", "Includes": "Erasers and extra lead",
    },
    "larkspur-office-two-pocket-folders-with-prongs-12-pack": {
        "Fasteners": "Three-prong", "Colors": "Assorted",
    },
    "deskwise-8-inch-scissors-3-pack": {"Handles": "Soft-grip"},
    "deskwise-electric-pencil-sharpener": {"Auto stop": "Yes", "Shavings bin": "Large"},
    "larkspur-office-hanging-file-folders-letter-size-25-pack": {
        "Includes": "Tabs and inserts",
    },
    "larkspur-office-sheet-protectors-100-pack": {"Loading": "Top-loading", "Finish": "Clear"},
    "deskwise-13-pocket-expanding-file-organizer": {
        "Style": "Portable accordion file", "Closure": "Elastic",
    },
    "deskwise-mesh-desk-organizer-with-drawer": {"Color": "Black"},
    "deskwise-monitor-stand-riser-with-drawer": {"Material": "Wood and metal"},
    "deskwise-desktop-stapler-with-1-000-staples": {"Type": "Full-strip"},
    "larkspur-office-standard-staples-5-000-count": {"Type": "Standard"},
    "larkspur-office-manila-catalog-envelopes-9-x-12-in-25-count": {
        "Count": "25", "Color": "Manila",
    },
}  # fmt: skip
