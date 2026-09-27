"""Text pools for the seeded sample reviews: openers, closers, titles, department pools, and
lines keyed to product facts. The product-family pools live in ``review_text_families``.

Line syntax, parsed by ``commerce.seed.reviews``:

* An optional ``[conditions]`` prefix, ``;``-separated and all required. ``#topic`` is not a
  condition: at most one line per topic goes into a review, so "Dates are always well out"
  never sits next to "The date was closer than I'd like". Each condition is
  ``tag:a|b`` (has any of these tags), ``type:...``, ``dept:...``, ``title:...`` (the lowercase
  title contains any of these), ``spec:Key`` (has the spec) or ``spec:Key=a|b`` (the lowercase
  spec value contains any of these). A leading ``!`` negates a condition.
* Placeholders. A line is only used when the product has a value for every placeholder in it:
  ``{this}``/``{This}`` ("this milk", "these headphones"), ``{it}``/``{It}`` and ``{obj}``
  (subject and object pronoun), ``{it_is}`` ("it's"/"they're"), ``{is}``/``{was}``/``{has}``/
  ``{does}`` and ``{s}``/``{es}`` (verb agreement: "Last{s}", "Wash{es}"), ``{noun}``, ``{brand}``, ``{flavor}``, ``{scent}``, ``{roast}``, ``{cheese}``,
  ``{material}``, ``{battery}``, ``{color}``, ``{size}``, ``{pet}``/``{Pet}`` ("my dog").

Nothing here may claim a fact the product doesn't have: a line that mentions a tag's claim
("no added sugar", "gluten-free", "USB-C") carries that tag as a condition. Tests enforce it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pool:
    """Detail sentences and titles for one department or product family.

    ``pos`` suits 4-5 star reviews, ``meh`` is a mild nitpick (3-4 stars), ``neg`` is a real
    complaint (1-2 stars), ``tpos`` are titles for 4-5 star reviews. ``kind`` (families only)
    picks the opener and closer register: "food", "consumable", "durable", or "gift".
    """

    pos: tuple[str, ...] = ()
    meh: tuple[str, ...] = ()
    neg: tuple[str, ...] = ()
    tpos: tuple[str, ...] = ()
    kind: str = "durable"


# --- Openers and closers, by register -------------------------------------------------------
# "all" suits anything but gift cards; "repeat" suits things bought again and again.

OPEN_POS: dict[str, tuple[str, ...]] = {
    "all": (
        "Bought {this} on a whim and I'm glad I did.",
        "First time trying {brand}, and I'm impressed.",
        "Went with {this} after reading a few reviews.",
        "I was skeptical at first, but {this} won me over.",
        "[#price] Honestly didn't expect much at this price.",
        "My sister recommended {this}.",
        "Took a chance on {this} and it paid off.",
        "I compared a few options before choosing {this}.",
        "A friend swears by {brand}, so I gave {obj} a try.",
        "Wanted something reliable without spending a lot.",
        "Ordered {this} last month.",
        "Quick review for anyone on the fence.",
    ),
    "repeat": (
        "I've bought {this} a few times now.",
        "Switched to {brand} a few months ago.",
        "[!dept:produce] Tried {this} when my usual brand was out of stock.",
        "This is at least my fifth time ordering {this}.",
        "Been buying {this} for about a year.",
        "Restocked {this} again this month.",
    ),
    "food": (
        "{This} {is} a regular on our grocery list.",
        "Added {this} to my weekly grocery order.",
        "Grabbed {this} to try something new.",
        "I buy {this} almost every week.",
        "Our family goes through {this} fast.",
        "Picked up {this} with the rest of our groceries.",
    ),
    "consumable": (
        "[dept:household] Keep {this} stocked in the closet at all times.",
        "Picked up {this} to replace a pricier brand.",
        "Ordered {this} along with our usual household stuff.",
    ),
    "durable": (
        "Been using {this} for a few weeks now.",
        "Bought {this} to replace an older one that finally gave out.",
        "Ordered {this} as a gift and ended up getting one for myself too.",
        "[#arrival] {This} arrived quickly and well packed.",
        "I've had {this} for about two months now.",
        "After a month of regular use, here's my take.",
        "Did a fair amount of research before buying {this}.",
        "Upgraded to {this} this spring.",
    ),
    "gift": (
        "Bought {this} for a coworker's birthday.",
        "Sent {this} to my niece for graduation.",
        "Picked up {this} as a last-minute teacher gift.",
        "Got {this} for my dad, who is impossible to shop for.",
    ),
}

OPEN_MIXED: dict[str, tuple[str, ...]] = {
    "all": (
        "Mixed feelings on {this}.",
        "{This} {is} fine, but not amazing.",
        "I wanted to love {this}.",
        "Decent, with a few caveats.",
        "It's okay overall.",
        "Not bad, not great.",
        "I'm on the fence about {this}.",
        "Middle of the road for me.",
        "{This} {does} the job, mostly.",
    ),
    "repeat": ("[!dept:produce] I usually buy a different brand and wanted to compare.",),
    "food": ("Tried {this} for a change of pace.",),
    "consumable": ("Gave {this} a shot to save a few dollars.",),
    "durable": ("I've used {this} for a few weeks, so here's an honest take.",),
    "gift": ("Bought {this} for a friend's birthday.",),
}

OPEN_NEG: dict[str, tuple[str, ...]] = {
    "all": (
        "Really wanted to like {this}.",
        "Unfortunately {this} didn't work out for me.",
        "Disappointed with {this}.",
        "Not what I expected.",
        "I rarely leave bad reviews, but here we are.",
        "This one was a letdown.",
        "Expected better from {brand}.",
        "{This} missed the mark for me.",
    ),
    "repeat": ("I've bought {this} before, but this time was different.",),
    "food": ("Tried {this} once and that was enough.",),
    "consumable": ("Switched to {this} to save money and regretted it.",),
    "durable": ("Had high hopes for {this}.",),
    "gift": ("Bought {this} as a gift.",),
}

CLOSE_POS: dict[str, tuple[str, ...]] = {
    "all": (
        "Would buy again.",
        "Highly recommend.",
        "No complaints here.",
        "Definitely recommend.",
        "Happy with this purchase.",
        "I'd recommend {obj} to anyone.",
        "[#price] Worth every penny.",
        "Glad I gave {obj} a try.",
        "Exactly what I was looking for.",
        "[#price] Can't go wrong at this price.",
        "Very pleased overall.",
    ),
    "repeat": (
        "Already reordered.",
        "I'll keep buying {obj}.",
        "My go-to from now on.",
    ),
    "food": (
        "It's on our regular list now.",
        "Already added {obj} to my next order.",
        "Will be a regular in my cart.",
    ),
    "consumable": (
        "Stocking up next time it's on sale.",
        "Not going back to the pricier stuff.",
    ),
    "durable": (
        "Would recommend to a friend.",
        "Holding up well so far.",
        "Very happy with {obj} so far.",
        "Already told a couple of friends about {obj}.",
        "Solid purchase.",
    ),
    "gift": (
        "Will buy again for birthdays.",
        "An easy gift that always goes over well.",
    ),
}

CLOSE_MIXED: dict[str, tuple[str, ...]] = {
    "all": (
        "[#price] Fine for the price.",
        "Probably won't go out of my way to rebuy.",
        "[#price] Worth it on sale.",
        "Okay if you're not too picky.",
        "Not sure I'd buy {obj} again.",
        "Three stars feels fair.",
        "Might try something else next time.",
    ),
    "repeat": ("[!dept:produce] I'll probably go back to my usual brand.",),
    "food": ("We'll finish {obj}, but I'll try something else next time.",),
    "consumable": ("It'll do until I find something better.",),
    "durable": ("It does the job, just don't expect too much.",),
    "gift": ("Fine for a quick gift.",),
}

CLOSE_NEG: dict[str, tuple[str, ...]] = {
    "all": (
        "Won't be buying {obj} again.",
        "Can't recommend {obj}.",
        "[#price] Save your money.",
        "Pretty disappointing overall.",
        "I'll look elsewhere next time.",
        "Hopefully this was a one-off, but I'm not risking it again.",
    ),
    "repeat": ("Going back to what I used before.",),
    "food": ("[!dept:produce] Back to our old brand.",),
    "consumable": ("Back to the brand I trust.",),
    "durable": ("Not worth the hassle.",),
    "gift": ("I'll pick a different gift next time.",),
}

# A small upside inside a 2-star review.
SOFT: dict[str, tuple[str, ...]] = {
    "all": (
        "[#price] The price was fair, at least.",
        "Delivery was quick, to be fair.",
        "Packaging was fine, at least.",
    ),
    "food": ("[#price] To be fair, the price was good.",),
    "consumable": ("It was cheap, at least.",),
    "durable": ("It looks nice, I'll give it that.",),
    "gift": (),
}

# --- Titles by star rating --------------------------------------------------------------------

TITLES: dict[int, tuple[str, ...]] = {
    5: (
        "Exactly what I hoped for",
        "Love {obj}",
        "Excellent",
        "Better than expected",
        "A new favorite",
        "Highly recommend",
        "Great buy",
        "Five stars",
        "So glad I tried {obj}",
        "Perfect",
        "Worth every penny",
        "Fantastic",
        "My new go-to",
        "Couldn't be happier",
        "Impressed",
        "Top notch",
        "Great quality",
        "Will buy again",
        "Just right",
        "A keeper",
        "Really impressed",
        "Spot on",
        "Very happy",
        "Best I've tried",
        "No regrets",
    ),
    4: (
        "Really good",
        "Very good overall",
        "Solid choice",
        "Great value",
        "Happy with this",
        "Pretty great",
        "Good buy",
        "Nice surprise",
        "Does the job well",
        "Would buy again",
        "Recommended",
        "Solid",
        "Glad I bought {obj}",
        "Four stars",
        "Good overall",
    ),
    3: (
        "It's okay",
        "Mixed feelings",
        "Decent",
        "Average",
        "Fine for the price",
        "Not bad",
        "Middle of the road",
        "Could be better",
        "Just okay",
        "Meh",
        "Does the job",
        "Some pros, some cons",
        "Nothing special",
    ),
    2: (
        "Not for me",
        "Disappointing",
        "Expected more",
        "Wouldn't buy again",
        "Not great",
        "Missed the mark",
        "Letdown",
        "Needs work",
    ),
    1: (
        "Very disappointed",
        "Would not recommend",
        "Not worth it",
        "Don't bother",
        "Poor quality",
        "Big letdown",
        "Save your money",
        "Frustrating",
    ),
}

# For a 4-star review whose body includes a nitpick.
TITLES_NITPICK: tuple[str, ...] = (
    "Almost perfect", "Good, not perfect", "Minor nitpicks", "Close to five stars",
    "One small gripe", "Really good, with one catch",
)  # fmt: skip

# --- Register-wide detail pools (lowest weight) -----------------------------------------------

KIND_POOLS: dict[str, Pool] = {
    "food": Pool(
        pos=(
            "[#price] Good price compared to other stores.",
            "[#consistent] Consistent quality every time I order.",
            "[#arrival] Packaging arrived intact.",
            "[#price] The price is hard to beat.",
            "Taste{s} better than the name brand I used to buy.",
            "I usually get the {size}, which is the better deal.",
            "Everyone in the house is happy with it.",
            "Great quality for an everyday staple.",
            "[#price] Better quality than I expected for the price.",
            "[#consistent] Never had a bad batch.",
            "One of the better options out there.",
            "It's become part of our routine.",
        ),
        meh=(
            "[#price] The price has crept up lately.",
            "Sometimes it's out of stock when I need it.",
            "Wish it came in a bigger size.",
        ),
        neg=(
            "[#price] The price went up and the quality didn't.",
            "Quality has really slipped compared to what I used to get.",
            "The package was damaged when it arrived.",
        ),
    ),
    "consumable": Pool(
        pos=(
            "[#price] Good value for how long it lasts.",
            "Work{s} as well as the name brand.",
            "[#price] Fair price for what you get.",
            "I buy the {size}; it lasts ages.",
            "[#described] Do{es} exactly what {it} should.",
            "[#price] Better quality than I expected for the price.",
            "It's become part of my routine.",
            "Last{s} longer than the brand I used before.",
            "Nothing fancy, just reliable.",
        ),
        meh=(
            "[#price] The price has gone up a bit.",
            "Packaging is bulkier than it needs to be.",
        ),
        neg=(
            "Doesn't work nearly as well as the brand I used before.",
            "The package arrived damaged.",
            "Quality seems to have gone downhill.",
        ),
    ),
    "durable": Pool(
        pos=(
            "[#build] Feel{s} well made for the price.",
            "[#looks] Look{s} just like the photos.",
            "Held up well so far.",
            "[#looks] Nicer in person than I expected.",
            "[#looks] I went with {color}, and it looks just like the photos.",
            "[#looks] The {color} is even nicer in person.",
            "[#described] Exactly as described.",
            "[#price] Better quality than I expected for the price.",
            "[#price] Great value for the money.",
            "[#build] The quality surprised me.",
        ),
        meh=(
            "The packaging was a bit excessive.",
            "[#price] A little pricier than I'd like.",
        ),
        neg=(
            "Quality isn't what it used to be.",
            "Felt cheaper in person than it looked online.",
            "Arrived with a scuff on it.",
        ),
    ),
    "gift": Pool(),
}

# --- Department pools (middle weight) ---------------------------------------------------------

DEPARTMENTS: dict[str, Pool] = {
    "dairy-eggs": Pool(
        pos=(
            "[#date] Always fresh, with plenty of time before the date.",
            "[#price] Well priced compared to the name brands.",
            "Never had a damaged package.",
            "[#date] Dates are always well out.",
        ),
        meh=(
            "[#date] The date was a little closer than I'd like on my last order.",
            "[#price] Price has gone up a bit recently.",
        ),
        neg=(
            "[#date] Arrived just two days before the date.",
            "[#date] Went off well before the date.",
            "The container was cracked and had leaked in the bag.",
        ),
        tpos=("Fresh every time", "Fridge staple"),
    ),
    "produce": Pool(
        pos=(
            "Looked hand-picked.",
            "Better than what I find at most grocery stores.",
            "[#price] Fairly priced for the quality.",
            "Picked well; everything was usable.",
        ),
        meh=(
            "Quality varies a bit from order to order.",
            "Smaller than I expected.",
        ),
        neg=(
            "Half of it was bruised or mushy when it arrived.",
            "Went bad within two days.",
            "Looked old and tired when it arrived.",
        ),
        tpos=("Fresh and tasty", "Great quality produce"),
    ),
    "meat-seafood": Pool(
        pos=(
            "Well packaged with no leaks.",
            "[#date] Good date on it, with plenty of time to cook or freeze.",
            "Freeze{s} well, so I stock up.",
            "Quality is as good as the butcher counter.",
        ),
        meh=(
            "[#price] Price per pound has gone up.",
            "A bit more liquid in the package than I'd like.",
        ),
        neg=(
            "The package leaked in my bag.",
            "Had a sour smell when I opened it.",
            "[#date] Arrived with a date of the next day.",
        ),
        tpos=("Restaurant quality at home", "Dinner winner"),
    ),
    "bakery": Pool(
        pos=(
            "Taste{s} like {it} came from a real bakery.",
            "[#stale] Soft and fresh when it arrived.",
            "[#stale] Stayed fresh for several days.",
        ),
        meh=(
            "[#stale] Went stale a bit faster than I'd like.",
            "Got a little squished in the bag.",
        ),
        neg=(
            "Was already stale when it arrived.",
            "Mold showed up two days after I got it.",
        ),
        tpos=("Bakery fresh",),
    ),
    "frozen": Pool(
        pos=(
            "Arrived frozen solid.",
            "Great to keep on hand for busy nights.",
            "Freezer staple at our house.",
        ),
        meh=(
            "The box takes up a lot of freezer space.",
            "A bit of frost inside the package.",
        ),
        neg=(
            "Arrived partially thawed.",
            "Covered in freezer burn.",
        ),
        tpos=("Freezer staple",),
    ),
    "pantry": Pool(
        pos=(
            "Great pantry staple.",
            "Keep{s} for ages, so I stock up.",
            "Always keep extra in the pantry.",
        ),
        meh=(
            "[#price] Price has crept up.",
            "The packaging is hard to reseal.",
        ),
        neg=(
            "[#date] Best-by date was only a few weeks out.",
            "Arrived with the package torn open.",
        ),
        tpos=("Pantry staple",),
    ),
    "snacks": Pool(
        pos=(
            "Perfect afternoon snack.",
            "Great for lunchboxes.",
            "Hard to stop at one serving.",
        ),
        meh=(
            "Bag is half air.",
            "[#price] A bit pricey for what you get.",
        ),
        neg=(
            "Stale when I opened it.",
            "Crushed to crumbs in shipping.",
        ),
        tpos=("Great snack", "Snack drawer favorite"),
    ),
    "beverages": Pool(
        pos=(
            "Great to have on hand.",
            "[#arrival] Arrived well packed with nothing leaking.",
        ),
        meh=("[#price] Price went up recently.",),
        neg=("The packaging was damaged when it arrived.",),
    ),
    "household": Pool(
        pos=(
            "[#price] Great value for the size.",
            "Last{s} a long time.",
            "Always keep a spare in the closet.",
        ),
        meh=("[#price] Price has gone up.",),
        neg=("The container leaked in the box.",),
    ),
    "health-wellness": Pool(
        pos=(
            "[#price] Good price for the count.",
            "[#arrival] Arrived sealed and well packed.",
        ),
        meh=("[#price] Price is a bit high compared to the pharmacy.",),
        neg=("Seal was broken when it arrived.",),
    ),
    "baby": Pool(
        pos=(
            "[#price] Good value for baby stuff.",
            "[#arrival] Arrived quickly, which matters when you're running low.",
        ),
        meh=("[#price] A bit pricier than I'd like.",),
        neg=("Not up to the quality I expect for a baby product.",),
    ),
    "pet": Pool(
        pos=(
            "[#price] Good value compared to the pet store.",
            "[#arrival] Arrived quickly and well packed.",
        ),
        meh=("[#price] Price has crept up.",),
        neg=("Poor quality for the price.",),
    ),
    "electronics": Pool(
        pos=(
            "[#build] Feel{s} well built for the price.",
            "[#described] Work{s} exactly as described.",
            "No issues after a few weeks of daily use.",
            "Everything was included in the box.",
        ),
        meh=(
            "Instructions were pretty bare-bones.",
            "[#price] A little pricey compared to similar options.",
        ),
        neg=(
            "Stopped working after a few weeks.",
            "Arrived with a scratch on it.",
            "Customer support took days to respond.",
        ),
    ),
    "home-kitchen": Pool(
        pos=(
            "Look{s} great in our home.",
            "[#price] Good quality for the price.",
            "[#arrival] Arrived well packed with no damage.",
        ),
        meh=("A bit bulky to store.",),
        neg=(
            "Arrived damaged.",
            "Quality feels cheap.",
        ),
    ),
    "clothing-shoes": Pool(
        pos=(
            "[#fit] Fit{s} true to size.",
            "[#price] Great quality for the price.",
            "Comfortable right away.",
        ),
        meh=(
            "[#fit] Runs slightly small; consider sizing up.",
            "Color is a shade darker than pictured.",
        ),
        neg=(
            "[#fit] Runs way small.",
            "Started falling apart after a few wears.",
        ),
        tpos=("Great fit", "Comfy and cute"),
    ),
    "outdoor": Pool(
        pos=(
            "[#price] Good quality for the price.",
            "[#arrival] Arrived quickly and well packed.",
        ),
        meh=("[#price] A little pricier than I expected.",),
        neg=("[#price] Not worth the money.",),
    ),
    "sports": Pool(
        pos=(
            "Well made.",
            "[#price] Good quality for the price.",
        ),
        meh=("[#price] A bit pricey.",),
        neg=("Fell apart quickly.",),
    ),
    "toys": Pool(
        pos=(
            "The kids love {obj}.",
            "Great gift idea.",
            "Keeps the kids busy for hours.",
        ),
        meh=("[#price] Pricier than I'd expect.",),
        neg=("Broke within a week.",),
        tpos=("Kids love {obj}", "Great gift"),
    ),
    "beauty": Pool(
        pos=(
            "A little goes a long way.",
            "[#price] Nice quality for the price.",
        ),
        meh=("Packaging could be better.",),
        neg=("[#price] Not worth the price.",),
    ),
    "office": Pool(
        pos=(
            "[#price] Good quality for the price.",
            "Handy for the home office.",
        ),
        meh=("[#price] A bit pricey for what it is.",),
        neg=("Cheaply made.",),
    ),
    "gift-cards": Pool(),
}

# --- Lines keyed to tags (the "fact" slot of a 4-5 star review) -------------------------------

_GROCERY = "dept:dairy-eggs|produce|meat-seafood|bakery|frozen|pantry|snacks|beverages"

FACT_LINES: tuple[str, ...] = (
    "[tag:organic] Nice to find an organic option that doesn't cost a fortune.",
    "[tag:organic] I try to buy organic when I can, and this one is worth it.",
    "[tag:gluten-free;dept:bakery|pantry|snacks|frozen] Being gluten-free, I'm picky, and this is one of the better ones I've found.",
    "[tag:gluten-free;dept:bakery|pantry|snacks|frozen] Great that {it_is} gluten-free; the whole family eats {obj} without noticing.",
    "[tag:vegan;dept:dairy-eggs|meat-seafood|bakery|frozen|snacks] Love that {it_is} vegan, so everyone at the table can have some.",
    "[tag:vegan;tag:cruelty-free] Vegan and cruelty-free, which matters to me.",
    "[tag:cruelty-free;!tag:vegan] Happy {it_is} cruelty-free.",
    "[tag:dairy-free;type:plant-milk|cheese|ice-cream|frozen-novelty|frozen-yogurt|creamer|cookies|chocolate|candy] My son can't have dairy, and he loves {obj}.",
    "[tag:lactose-free;dept:dairy-eggs|beverages|frozen] I'm lactose intolerant and {this} {does}n't bother my stomach at all.",
    "[tag:no-added-sugar;type:yogurt|kefir|cereal|granola|oatmeal|juice|applesauce|canned-fruit|nut-butter|peanut-butter|pasta-sauce|dried-fruit|frozen-fruit|baby-food|baby-snacks|jam|fruit-nut-bar|plant-milk|protein-shake|frozen-novelty;#sweet] No added sugar, which was the main reason I picked {obj}.",
    "[tag:no-added-sugar;type:yogurt|kefir|cereal|granola|oatmeal|juice|applesauce|canned-fruit|nut-butter|peanut-butter|pasta-sauce|dried-fruit|frozen-fruit|baby-food|baby-snacks|jam|fruit-nut-bar|plant-milk|protein-shake|frozen-novelty;#sweet] Nice that there's no added sugar and {it} still taste{s} good.",
    "[tag:sugar-free;type:cookies|candy|chocolate|protein-bar|frozen-novelty|ice-cream|sweetener|syrup|jam|soda|energy-drink|electrolyte-mix|fiber-supplement;#sweet] Hard to believe {it_is} sugar-free.",
    "[tag:low-sugar;type:cereal|granola|yogurt|protein-bar|granola-bar|protein-shake|ice-cream;#sweet] I appreciate that {it_is} lower in sugar than most.",
    "[tag:high-protein;type:yogurt|kefir|protein-bar|protein-shake|cereal|granola|frozen-meal|burritos|breakfast-sandwich|jerky|plant-based-meat|tofu|bagels|oatmeal|pasta|protein-powder] The extra protein keeps me full for hours.",
    "[tag:high-protein;type:yogurt|kefir|protein-bar|protein-shake|jerky|protein-powder|cheese] A tasty way to hit my protein goals.",
    "[tag:keto;type:cheese|nuts|pork-rinds|seaweed-snacks|protein-bar|sweetener|cookies|ice-cream|creamer|bread|tortillas|jerky|candy|chocolate] Works well with my low-carb eating.",
    "[tag:low-sodium|no-salt-added;type:canned-beans|canned-tomatoes|canned-vegetables|soup|broth|chili|chips|crackers|nuts|pretzels|spices|soy-sauce|deli-meat|frozen-vegetables|tortilla-chips|popcorn;#salt] I'm watching my sodium, and this still has plenty of flavor.",
    "[tag:whole-grain] Nice to have a whole grain option that tastes this good.",
    "[tag:high-fiber;type:cereal|bread|protein-bar|canned-beans|granola|oatmeal|crackers|pasta|burritos|chili|tortillas] The fiber keeps me full through the morning.",
    "[tag:decaf] Decaf that actually tastes like the real thing.",
    "[tag:caffeine-free;type:tea|soda|iced-tea|sparkling-water] No caffeine, so I can have {obj} in the evening.",
    "[tag:fair-trade] Glad to see {it_is} fair trade.",
    "[tag:grass-fed] Worth paying a bit more for grass-fed.",
    "[tag:pasture-raised|free-range|cage-free] Happy to support better farming practices.",
    "[tag:antibiotic-free] Good to know {it_is} raised without antibiotics.",
    "[tag:wild-caught] Wild-caught, and you can taste the difference.",
    "[tag:local] Love buying local when I can.",
    "[tag:non-gmo;" + _GROCERY + "] Non-GMO is a nice bonus.",
    "[tag:unsweetened;type:plant-milk|tea|cold-brew|iced-tea|applesauce|oatmeal|nut-butter|dried-fruit|frozen-fruit|fruit-nut-bar] Unsweetened, so I can control how sweet it is.",
    "[tag:zero-calorie;type:sparkling-water|soda|energy-drink] Zero calories, which makes it an easy everyday drink.",
    "[tag:plant-based;type:plant-based-meat|tofu|plant-milk] Easy way to eat more plant-based meals.",
    "[tag:machine-washable;#wash] Hold{s} up well in the washing machine.",
    "[tag:dishwasher-safe] Goes right in the dishwasher, which I love.",
    "[tag:bpa-free] BPA-free, which matters to me.",
    "[tag:rechargeable;tag:usb-c] Love that {it} charge{s} over USB-C like everything else I own.",
    "[tag:rechargeable;!tag:usb-c] Nice not having to buy batteries.",
    "[tag:fragrance-free] No perfume smell, which I really appreciate.",
    "[tag:sensitive-skin|hypoallergenic;dept:beauty|baby|health-wellness] My sensitive skin had no reaction at all.",
    "[tag:hypoallergenic;dept:home-kitchen] My allergies haven't flared up since switching.",
    "[tag:sulfate-free;dept:beauty] Sulfate-free and still lathers decently.",
    "[tag:recycled-materials] Nice that {it_is} made with recycled materials.",
    "[tag:energy-efficient] Uses very little power, which is a nice bonus.",
    "[tag:kids;dept:toys|office] My kids use {obj} constantly.",
    "[tag:oven-safe;type:skillet|dutch-oven|saucepan|stockpot|cookware-set|griddle] Goes from stovetop to oven with no problem.",
    "[tag:cordless] Being cordless makes {obj} so much easier to use.",
    "[tag:tear-free] Truly tear-free; no crying at bath time.",
    "[tag:he-compatible] Works great in our HE washer.",
    "[tag:biodegradable] Glad {it_is} biodegradable.",
    "[tag:aluminum-free] One of the few aluminum-free options that actually works for me.",
    "[tag:moisture-wicking] Wicks sweat really well on hot days.",
    "[tag:dye-free] Dye-free, which is easier on our skin.",
    "[tag:grain-free;dept:pet] Grain-free, which works well for {pet}'s sensitive stomach.",
    "[tag:grain-free;!dept:pet] Grain-free and still taste{s} like a treat.",
    "[tag:limited-ingredient] Short ingredient list, which helps with {pet}'s allergies.",
)

# --- How reviewers refer to the product -------------------------------------------------------

# product_type -> noun, when the type slug doesn't read naturally ("usb-c-charger").
NOUNS: dict[str, str] = {
    "plant-milk": "plant milk", "sour-cream": "sour cream", "kiwi": "kiwis",
    "stone-fruit": "peaches", "melons": "melon", "lettuce": "lettuce", "leafy-greens": "greens",
    "salad-greens": "greens", "salad-kit": "salad kit", "fresh-herbs": "herbs",
    "cut-fruit": "fruit", "vegetable-tray": "veggie tray", "cut-vegetables": "veggies",
    "ground-chicken": "ground chicken", "ground-beef": "ground beef", "beef-roast": "roast",
    "ground-turkey": "ground turkey", "deli-meat": "deli meat", "hot-dogs": "hot dogs",
    "plant-based-meat": "plant-based meat", "english-muffins": "English muffins",
    "ice-cream": "ice cream", "frozen-yogurt": "frozen yogurt", "frozen-novelty": "treats",
    "frozen-vegetables": "veggies", "frozen-fruit": "fruit", "frozen-meal": "meal",
    "breakfast-sandwich": "breakfast sandwiches", "fish-sticks": "fish sticks",
    "frozen-shrimp": "shrimp", "chicken-nuggets": "nuggets", "frozen-chicken": "chicken strips",
    "frozen-potatoes": "potatoes", "oatmeal": "oats", "mac-and-cheese": "mac and cheese",
    "grains": "grain", "canned-beans": "beans", "canned-tomatoes": "tomatoes",
    "canned-vegetables": "veggies", "canned-fruit": "fruit", "peanut-butter": "peanut butter",
    "nut-butter": "nut butter", "cooking-oil": "oil", "pasta-sauce": "sauce",
    "mayonnaise": "mayo", "salad-dressing": "dressing", "bbq-sauce": "BBQ sauce",
    "soy-sauce": "soy sauce", "hot-sauce": "hot sauce", "baking-mix": "mix",
    "pancake-mix": "pancake mix", "baking-chips": "baking chips", "spices": "seasoning",
    "canned-fish": "fish", "cheese-puffs": "cheese puffs", "corn-chips": "corn chips",
    "pork-rinds": "pork rinds", "tortilla-chips": "tortilla chips", "bean-dip": "bean dip",
    "trail-mix": "trail mix", "protein-bar": "protein bars", "fruit-nut-bar": "bars",
    "granola-bar": "granola bars", "fruit-snacks": "fruit snacks", "dried-fruit": "dried fruit",
    "rice-cakes": "rice cakes", "seaweed-snacks": "seaweed snacks", "cold-brew": "cold brew",
    "iced-tea": "tea", "sparkling-water": "sparkling water", "sports-drink": "sports drink",
    "electrolyte-drink": "electrolyte drink", "protein-shake": "protein shakes",
    "energy-drink": "energy drink", "laundry-detergent": "detergent",
    "fabric-softener": "fabric softener", "dryer-sheets": "dryer sheets",
    "dryer-balls": "dryer balls", "stain-remover": "stain remover", "dish-soap": "dish soap",
    "dishwasher-detergent": "detergent", "rinse-aid": "rinse aid",
    "all-purpose-cleaner": "cleaner", "glass-cleaner": "glass cleaner",
    "bathroom-cleaner": "cleaner", "toilet-bowl-cleaner": "cleaner",
    "disinfecting-wipes": "wipes", "cleaning-wipes": "wipes", "paper-towels": "paper towels",
    "toilet-paper": "toilet paper", "facial-tissues": "tissues", "trash-bags": "trash bags",
    "food-storage-bags": "bags", "aluminum-foil": "foil", "parchment-paper": "parchment",
    "plastic-wrap": "plastic wrap", "light-bulbs": "bulbs", "battery-charger": "charger",
    "vitamin-d": "vitamin D", "vitamin-c": "vitamin C", "vitamin-b12": "B12",
    "fish-oil": "fish oil", "fiber-supplement": "fiber supplement",
    "protein-powder": "protein powder", "electrolyte-mix": "electrolyte mix",
    "gauze": "gauze pads", "medical-tape": "tape", "elastic-bandage": "wrap",
    "first-aid-kit": "kit", "ice-pack": "ice packs", "heating-pad": "heating pad",
    "pill-organizer": "pill organizer", "swim-diapers": "swim diapers",
    "training-pants": "training pants", "baby-wipes": "wipes", "baby-wash": "baby wash",
    "baby-lotion": "lotion", "baby-oil": "baby oil", "diaper-cream": "cream",
    "baby-bottles": "bottles", "bottle-brush": "brush set", "pacifier": "pacifiers",
    "sippy-cup": "sippy cups", "swaddle": "swaddles", "baby-towel": "towels",
    "baby-food": "baby food", "baby-snacks": "puffs", "dog-food": "dog food",
    "dog-treats": "treats", "cat-food": "cat food", "cat-treats": "treats",
    "cat-litter": "litter", "litter-box": "litter box", "dog-toy": "toy", "cat-toy": "toy",
    "cat-scratcher": "scratcher", "pet-bed": "bed", "dog-leash": "leash",
    "dog-collar": "collar", "dog-harness": "harness", "cat-collar": "collars",
    "poop-bags": "bags", "pet-bowl": "bowls", "puppy-pads": "pads",
    "bluetooth-speaker": "speaker", "smart-bulb": "bulbs", "power-bank": "power bank",
    "tv": "TV", "streaming-device": "streaming stick", "usb-c-charger": "charger",
    "car-charger": "car charger", "wireless-charger": "charging pad", "usb-c-cable": "cable",
    "hdmi-cable": "HDMI cable", "surge-protector": "surge protector", "phone-case": "case",
    "screen-protector": "screen protectors", "smart-plug": "smart plugs",
    "smart-light-strip": "light strip", "security-camera": "camera",
    "video-doorbell": "doorbell", "smart-thermostat": "thermostat", "usb-hub": "hub",
    "ssd": "SSD", "memory-card": "card", "flash-drive": "flash drive",
    "game-controller": "controller", "printer-ink": "ink", "electric-kettle": "kettle",
    "kitchen-knife": "knife", "sheet-set": "sheets", "throw-blanket": "throw",
    "food-storage": "containers", "coffee-maker": "coffee maker", "mixing-bowls": "bowls",
    "dutch-oven": "Dutch oven", "cookware-set": "cookware", "bakeware": "pans",
    "knife-set": "knife set", "knife-sharpener": "sharpener", "cutting-board": "cutting board",
    "kitchen-utensils": "utensils", "measuring-cups": "measuring cups",
    "air-fryer": "air fryer", "espresso-machine": "espresso machine",
    "slow-cooker": "slow cooker", "pressure-cooker": "pressure cooker",
    "rice-cooker": "rice cooker", "stand-mixer": "mixer", "hand-mixer": "mixer",
    "food-processor": "food processor", "dinnerware-set": "dishes",
    "drinking-glasses": "glasses", "duvet-cover": "duvet cover", "pillow": "pillows",
    "mattress-protector": "mattress protector", "weighted-blanket": "blanket",
    "bath-towels": "towels", "bath-mat": "bath mat", "shower-curtain": "shower curtain",
    "storage-bins": "bins", "robot-vacuum": "robot vacuum", "air-purifier": "purifier",
    "air-purifier-filter": "filter", "running-shoes": "shoes", "rain-jacket": "jacket",
    "t-shirt": "tee", "puffer-jacket": "jacket", "fleece-jacket": "fleece",
    "sports-bra": "sports bra", "tank-top": "tank", "sleeping-bag": "sleeping bag",
    "water-bottle": "bottle", "garden-bed": "garden bed", "garden-hose": "hose",
    "camp-chair": "chair", "sleeping-pad": "pad", "air-mattress": "air mattress",
    "camp-stove": "stove", "grill-accessory": "grill tools", "patio-chair": "chair",
    "patio-set": "patio set", "patio-umbrella": "umbrella", "garden-tools": "tools",
    "garden-gloves": "gloves", "hose-nozzle": "nozzle", "planter": "planters",
    "bird-feeder": "feeder", "bird-seed": "seed", "yoga-mat": "mat", "jump-rope": "jump rope",
    "resistance-bands": "bands", "foam-roller": "foam roller", "yoga-block": "blocks",
    "yoga-strap": "strap", "exercise-ball": "ball", "medicine-ball": "ball",
    "fitness-tracker": "tracker", "balance-bike": "bike", "bike-helmet": "helmet",
    "bike-lock": "lock", "bike-light": "lights", "soccer-ball": "ball",
    "tennis-balls": "balls", "tennis-racquet": "racquet", "pickleball-paddle": "paddles",
    "badminton-set": "set", "swim-goggles": "goggles", "swim-cap": "cap",
    "building-blocks": "blocks", "board-game": "game", "plush-toy": "stuffed animal",
    "rc-car": "RC car", "party-game": "game", "card-game": "game", "action-figure": "figure",
    "colored-pencils": "pencils", "paint": "paints", "modeling-dough": "dough",
    "sidewalk-chalk": "chalk", "stem-kit": "kit", "outdoor-toy": "toy", "baby-toy": "toy",
    "face-moisturizer": "moisturizer", "electric-toothbrush": "toothbrush",
    "hand-cream": "hand cream", "dry-shampoo": "dry shampoo", "hair-styling": "styler",
    "hair-dryer": "hair dryer", "flat-iron": "flat iron", "body-wash": "body wash",
    "bar-soap": "soap", "body-lotion": "lotion", "face-wash": "cleanser",
    "makeup-remover": "remover", "face-serum": "serum", "eye-cream": "eye cream",
    "after-sun": "gel", "lip-balm": "lip balm", "toothbrush": "toothbrushes",
    "toothbrush-heads": "brush heads", "dental-floss": "floss", "razor-cartridges": "cartridges",
    "beard-trimmer": "trimmer", "shaving-cream": "shave cream", "lip-color": "lipstick",
    "makeup-brushes": "brushes", "makeup-sponges": "sponges", "nail-polish": "polish",
    "nail-polish-remover": "remover", "nail-care": "clippers", "desk-lamp": "lamp",
    "legal-pad": "legal pads", "copy-paper": "paper", "sticky-notes": "sticky notes",
    "pencil-sharpener": "sharpener", "sheet-protectors": "sheet protectors",
    "file-organizer": "organizer", "desk-organizer": "organizer", "lunch-box": "lunch box",
    "label-maker": "label maker", "gift-card": "gift card",
}  # fmt: skip

# For vague types, a more specific noun when the title contains a keyword (first match wins).
TITLE_NOUNS: dict[str, tuple[tuple[str, str], ...]] = {
    "plant-milk": (("almond", "almond milk"), ("oat", "oat milk"), ("soy", "soy milk"),
                   ("coconut", "coconut milk"), ("cashew", "cashew milk")),
    "cheese": (("cottage", "cottage cheese"), ("cream cheese", "cream cheese"),
               ("string", "string cheese"), ("shreds", "shreds")),
    "cream": (("half & half", "half-and-half"), ("whipped", "whipped topping")),
    "citrus": (("orange", "oranges"), ("clementine", "clementines"), ("lemon", "lemons"),
               ("lime", "limes"), ("grapefruit", "grapefruit")),
    "stone-fruit": (("nectarine", "nectarines"), ("plum", "plums")),
    "melons": (("watermelon", "watermelon"), ("cantaloupe", "cantaloupe"),
               ("honeydew", "honeydew")),
    "lettuce": (("romaine", "romaine"),),
    "leafy-greens": (("kale", "kale"), ("chard", "chard"), ("collard", "collards")),
    "salad-greens": (("spinach", "spinach"), ("spring mix", "spring mix"),
                     ("arugula", "arugula"), ("kale", "kale"), ("coleslaw", "coleslaw mix"),
                     ("romaine", "romaine"), ("iceberg", "salad"), ("blend", "salad blend")),
    "fresh-herbs": (("cilantro", "cilantro"), ("parsley", "parsley"), ("basil", "basil"),
                    ("mint", "mint"), ("rosemary", "rosemary"), ("thyme", "thyme")),
    "squash": (("zucchini", "zucchini"),),
    "peppers": (("jalapeno", "jalapeños"),),
    "cut-vegetables": (("squash", "squash cubes"), ("cauliflower", "riced cauliflower")),
    "pork": (("chop", "pork chops"), ("tenderloin", "tenderloin"), ("rib", "ribs")),
    "deli-meat": (("turkey", "turkey"), ("roast beef", "roast beef"), ("ham", "ham"),
                  ("salami", "salami"), ("pepperoni", "pepperoni")),
    "fish": (("snapper", "snapper"), ("tilapia", "tilapia"), ("cod", "cod"),
             ("tuna", "tuna steaks")),
    "pastries": (("cinnamon roll", "cinnamon rolls"),),
    "frozen-novelty": (("sandwich", "ice cream sandwiches"), ("pops", "ice pops"),
                       ("bars", "bars")),
    "frozen-potatoes": (("fries", "fries"), ("tots", "tots"), ("hash brown", "hash browns"),
                        ("wedges", "wedges")),
    "grains": (("quinoa", "quinoa"), ("couscous", "couscous"), ("barley", "barley"),
               ("farro", "farro")),
    "nut-butter": (("almond", "almond butter"), ("cashew", "cashew butter"),
                   ("sunflower", "sunflower butter")),
    "jam": (("preserves", "preserves"), ("jelly", "jelly"), ("marmalade", "marmalade")),
    "spices": (("black pepper", "pepper"), ("garlic powder", "garlic powder"),
               ("onion powder", "onion powder"), ("chili powder", "chili powder"),
               ("cinnamon", "cinnamon"), ("cumin", "cumin"), ("paprika", "paprika"),
               ("turmeric", "turmeric"), ("rub", "rub")),
    "canned-fish": (("tuna", "tuna"), ("salmon", "salmon"), ("sardine", "sardines")),
    "nuts": (("peanuts", "peanuts"), ("cashews", "cashews"), ("almonds", "almonds"),
             ("pistachios", "pistachios"), ("walnut", "walnuts"), ("pecan", "pecans"),
             ("sunflower", "sunflower seeds"), ("pepitas", "pepitas")),
    "candy": (("gummy", "gummies"), ("peanut butter cups", "peanut butter cups"),
              ("licorice", "licorice"), ("hard candies", "hard candies")),
    "baking-chips": (("chocolate chips", "chocolate chips"),),
    "coffee-maker": (("french press", "French press"), ("pour-over", "pour-over")),
    "dishwasher-detergent": (("pods", "pods"),),
    "hair-styling": (("gel", "gel"), ("cream", "cream"), ("spray", "hairspray"),
                     ("pomade", "pomade"), ("mousse", "mousse")),
}  # fmt: skip

# Nouns ending in "s" that are singular.
SINGULAR_NOUNS = frozenset({"asparagus", "citrus", "couscous", "hummus", "floss", "molasses"})

# --- How many reviews a product gets ----------------------------------------------------------

POPULAR_TYPES = frozenset({
    "milk", "eggs", "bananas", "bread", "cheese", "butter", "apples", "berries", "avocados",
    "salad-greens", "chicken", "ground-beef", "bacon", "chips", "coffee", "soda", "water",
    "sparkling-water", "ice-cream", "pizza", "cereal", "peanut-butter", "protein-bar",
    "paper-towels", "toilet-paper", "laundry-detergent", "trash-bags", "batteries", "diapers",
    "baby-wipes", "dog-food", "cat-food", "cat-litter", "headphones", "earbuds", "tv",
    "power-bank", "usb-c-cable", "t-shirt", "jeans", "running-shoes", "sneakers", "sheet-set",
    "air-fryer", "pillow", "bath-towels", "shampoo", "toothpaste", "deodorant", "sunscreen",
    "multivitamin", "protein-powder", "yoga-mat", "water-bottle", "building-blocks", "puzzle",
    "board-game", "notebook", "pens", "backpack",
})  # fmt: skip

NICHE_TYPES = frozenset({
    "hdmi-cable", "staples", "rinse-aid", "sheet-protectors", "labels", "mulch", "bird-seed",
    "razor-cartridges", "printer-ink", "air-purifier-filter", "toothbrush-heads", "gauze",
    "medical-tape", "parchment-paper", "plastic-wrap", "swim-cap", "pencil-sharpener",
    "envelopes", "mailers", "file-organizer", "nail-care", "makeup-sponges", "bottle-brush",
    "baby-oil", "cat-collar", "grill-accessory", "hose-nozzle", "garden-gloves", "legal-pad",
    "highlighters", "binder", "folders", "salt", "vinegar", "gift-card", "memory-card",
    "screen-protector", "elastic-bandage", "pill-organizer", "nail-polish-remover",
})  # fmt: skip

# --- Sample reviewer accounts -----------------------------------------------------------------
# The first eight keep the addresses earlier seeds used, so existing rows stay attached.

REVIEWERS: tuple[tuple[str, str], ...] = (
    ("maya.sample@example.com", "Maya Okafor"),
    ("jordan.sample@example.com", "Jordan Lee"),
    ("priya.sample@example.com", "Priya Nair"),
    ("diego.sample@example.com", "Diego Alvarez"),
    ("hannah.sample@example.com", "Hannah Schmidt"),
    ("marcus.sample@example.com", "Marcus Bell"),
    ("sofia.sample@example.com", "Sofia Rossi"),
    ("kenji.sample@example.com", "Kenji Watanabe"),
    *(
        (f"{name.lower().replace(' ', '.').replace(chr(39), '')}.sample@example.com", name)
        for name in (
            "Aaliyah Brooks",
            "Ben Carter",
            "Carmen Diaz",
            "Daniel Kim",
            "Elena Petrova",
            "Fatima Hassan",
            "Grace Liu",
            "Hector Ramirez",
            "Isabel Moreno",
            "Jamal Washington",
            "Kate O'Brien",
            "Liam Murphy",
            "Mei Chen",
            "Noah Patel",
            "Olivia Nguyen",
            "Pedro Santos",
            "Quinn Harper",
            "Rachel Goldberg",
            "Sam Whitaker",
            "Tanya Ivanova",
            "Umar Siddiqui",
            "Vanessa Cruz",
            "Wei Zhang",
            "Xavier Thompson",
            "Yuki Tanaka",
            "Zoe Martin",
            "Andre Johnson",
            "Bianca Ferreira",
            "Chris Novak",
            "Dana Mitchell",
            "Emeka Obi",
            "Fiona Walsh",
            "Gabriel Silva",
            "Heather Collins",
            "Ian Fraser",
            "Jasmine Reed",
            "Kevin Tran",
            "Lauren Price",
            "Miguel Torres",
            "Nina Kowalski",
            "Oscar Lindqvist",
            "Paige Sullivan",
            "Rosa Delgado",
            "Sean Gallagher",
            "Tara Singh",
            "Victor Huang",
            "Whitney Cole",
            "Aisha Bello",
            "Brian Foster",
            "Chloe Bennett",
            "Derek Russo",
            "Erin Hayes",
            "Farah Aziz",
            "Hana Yamamoto",
            "Jorge Castillo",
            "Leah Stein",
        )
    ),
)
