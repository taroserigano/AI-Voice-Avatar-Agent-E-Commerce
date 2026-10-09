"""Build Xena's customer-support coverage sets: what a support representative is asked, beyond the
2,000 golden questions.

  uv run --directory services/assistant python ../../evals/xana/build_support.py

Taro (2026-10-08): Xena should answer every general question about products, the return and
refund policy, and the customer's order history and ordered items, the way a customer-support
representative would. These sets cover what the golden 2,000 barely touched: how the site works
(account, checkout, payment, promo codes, receipts, reviews, contacting us; the help center),
shipping rules, every return-policy section, catalog-wide product questions (brands, counts,
price ranges, things we don't sell), order amounts (subtotal, discount, tax, shipping), a third
customer (Dana) with different orders, multi-part and long messages, other languages, and
escalation.

Every case is written once and goes to one of two files by a fixed hash of its id:

- ``evals/xana/support/support.jsonl``: the development half. Run it, read the failures, fix.
- ``evals/xana/locked/holdout.jsonl``: the locked half. Don't read its failures or tune on it;
  run it once at the end of a round (``--file``) and report it separately.

As in the other builders, every expected fact comes from the seed data (catalog, orders,
stores) or the policy files, and the builder refuses a case the data doesn't support.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SUPPORT = ROOT / "evals" / "xana" / "support"
LOCKED = ROOT / "evals" / "xana" / "locked"

_spec = importlib.util.spec_from_file_location("build_batches", ROOT / "evals/xana/build_batches.py")
assert _spec and _spec.loader
B = importlib.util.module_from_spec(_spec)
sys.modules["build_batches"] = B
_spec.loader.exec_module(B)
G = B.G

PRODUCTS, CATALOG, ORDERS = G.PRODUCTS, G.CATALOG, G.ORDERS
ALICE, BOB, DANA = G.ALICE, G.BOB, "dana@example.com"
price, num, name, min_price = G.price, G.num, G.name, G.min_price
problems: list[str] = G.problems
rng = random.Random(11)

HC = "help-center#hc-"
SD = "shipping-and-delivery#sd-"
R = "returns-and-refunds#rr-"
SHIP = "shipping-and-delivery"
HELP = "help-center"

# What answers say.
NO = (r"\b(?:no|not|don't|doesn't|do not|does not|isn't|aren't|can't|cannot|won't|unfortunately|"
      r"there's no|there isn't|we only)\b")  # fmt: skip
NOT_YES = r"^\W*(?:yes|yep|yeah|absolutely|sure|of course)\b"
PERSON = r"person|support case|human|agent|someone|team member|our team|support team"
CANT_SELF = (r"(?:can't|cannot|can not|isn't|is not|no|not (?:yet )?(?:able|possible|available)|"
             r"doesn't|there's no|there isn't)")  # fmt: skip
WE_DONT_SELL = (
    r"(?:don't|do not|doesn't|does not|didn't|did not|can't|cannot|couldn't|could not) (?:\w+ ){0,3}"
    r"(?:sell|carry|have|stock|find|see|offer|fill|list)|not (?:\w+ ){0,3}(?:sell|carry|"
    r"available|listed|in (?:our|the) catalog|something we)|isn't (?:something|in|part|available)|"
    r"aren't (?:in|part|something|available)|only (?:carry|sell|have)"
)
ON_THE_WAY, DELIVERED = B.ON_THE_WAY, B.DELIVERED
NOT_SHIPPED = (r"(?:hasn't|has not|haven't|have not|not|isn't|is not|aren't|are not)(?: \w+){0,2} "
               r"(?:shipped|been shipped|left|sent|out)|preparing|getting (?:it |them |your order )?ready|"
               r"being prepared|not yet shipped|no tracking|ships? (?:soon|within|in)")  # fmt: skip
CANCELED = r"cancel+ed"
PAST_30 = G.PAST_30
NOT_DELIVERED = G.NOT_DELIVERED
FINAL = G.FINAL


class Pool:
    def __init__(self) -> None:
        self.cases: list[dict[str, Any]] = []
        self.texts: set[str] = set()

    def add(self, category: str, turns: list[dict[str, Any]], user: str = ALICE, **extra: Any) -> None:
        key = " / ".join(t["user"] for t in turns)
        if key in self.texts:
            problems.append(f"duplicate question: {key}")
            return
        self.texts.add(key)
        case = {"id": "", "category": category, "user": user, "turns": turns}
        case.update({k: v for k, v in extra.items() if v is not None})
        self.cases.append(case)


pool = Pool()


def one(category: str, text: str, expect: dict[str, Any], user: str = ALICE, **extra: Any) -> None:
    pool.add(category, [{"user": text, "expect": expect}], user, **extra)


def answer(**kw: Any) -> dict[str, Any]:
    return {"action": "answer", **{k: v for k, v in kw.items() if v is not None}}


def site(category: str, texts: list[str], cite_any: list[str], mentions_re: list[str] | None = None,
         user: str = ALICE, **kw: Any) -> None:  # fmt: skip
    """How the site works or a policy rule: answered from an approved section, with its citation."""
    for t in texts:
        one(category, t, answer(cite_any=cite_any, mentions_re=mentions_re, **kw), user)


# --- 1. How the site works (help center) --------------------------------------------------------

# A made-up self-service flow is the failure to catch here.
FAKE_RESET = [r"forgot (?:your )?password\W{0,3} (?:link|page|button|option)", r"reset link",
              r"check your (?:email|inbox)", r"(?:Settings|Profile) (?:>|page|tab)"]  # fmt: skip
site("account", ["how do I reset my password?", "I forgot my password, what do I do?",
                 "can I change my password?", "where do I update my password"],
     [HC + "1-2"], [PERSON], must_not_mention_re=FAKE_RESET)  # fmt: skip
site("account", ["how do I change the email on my account?", "can I update my email address?",
                 "I need to change my name on the account"],
     [HC + "1-2"], [CANT_SELF], must_not_mention_re=FAKE_RESET)  # fmt: skip
site("account", ["how do I delete my account?", "I want to close my Serigan Mart account",
                 "can you remove my account?"], [HC + "1-3"], [PERSON], must_not_mention_re=FAKE_RESET)
site("account", ["how do I sign out?", "where's the log out button?"], [HC + "1-1"],
     [r"account menu|Hi,|top right|Sign out"])  # fmt: skip
site("account", ["how long do I stay logged in?", "why do I keep getting signed out?"], [HC + "1-1"],
     [r"12 hours|twelve hours"])  # fmt: skip
site("account", ["can I shop without an account?", "do you have guest checkout?"],
     [HC + "1-1", HC + "2-1"], [r"sign(?:ed)?.?in|account|guest"])  # fmt: skip
site("account", ["can I save my address for next time?", "where do I manage my saved addresses?"],
     [HC + "1-4"], [r"address book|no saved|isn't|not|order'?s? page|each order"])  # fmt: skip
site("account", ["where can I see what I've searched for and looked at?"], [HC + "1-5"],
     [r"Activity"], cite_ok_if=["get_my_account_activity"])  # fmt: skip

site("checkout", ["how do I check out?", "why can't I place my order?", "the checkout button isn't working"],
     [HC + "2-1"], [r"turned off|off in (?:this|the) demo|can't place|cannot place|not open|isn't open|"
                    r"no (?:orders|checkout)|demo store|not (?:available|possible)"])  # fmt: skip
one("checkout", "can I buy what's in my cart?", answer(
    cite_any=[HC + "2-1"], cite_ok_if=["get_my_cart"],
    mentions_re=[r"turned off|off in (?:this|the) demo|can't|cannot|not (?:open|available|possible)|demo store"]))
site("checkout", ["can you place an order for me?", "just order it for me"], [HC + "2-1"],
     [r"can't|cannot|not able|unable|turned off"], not_uses=["propose_return"])  # fmt: skip
site("payment", ["what payment methods do you accept?", "how can I pay?"], [HC + "2-2"], [r"\bcards?\b"])
for t in ["do you take PayPal?", "can I pay with Apple Pay?", "do you accept Google Pay?",
          "can I pay cash on delivery?"]:  # fmt: skip
    one("payment", t, answer(cite_any=[HC + "2-2"], mentions_re=[NO], must_not_mention_re=[NOT_YES]))
site("payment", ["do you store my card number?", "is it safe to pay on your site?"],
     [HC + "2-2", HC + "8", "returns-regulations#rg-9-2"],
     [r"never (?:see|store)|don't (?:see|store|keep)|last four|Stripe|not stored|aren't stored"])  # fmt: skip
for t in ["do you have any promo codes?", "where do I enter a coupon?", "is there a discount code for first orders?",
          "do you have a rewards program?", "do I earn points on purchases?", "do you offer subscriptions?"]:  # fmt: skip
    one("promotions", t, answer(cite_any=[HC + "2-3"], mentions_re=[NO], must_not_mention_re=[NOT_YES]))
for t in ["do you price match?", "will you match a lower price I found at another store?"]:
    one("promotions", t, answer(cite_any=[HC + "2-3", R + "10-2"], mentions_re=[NO],
                                must_not_mention_re=[NOT_YES]))  # fmt: skip
site("gift_cards", ["how do gift cards work?", "are your gift cards physical or digital?"],
     [HC + "2-4"], [r"e-?mail|digital"])  # fmt: skip
site("gift_cards", ["what amounts do gift cards come in?"], [HC + "2-4"], [r"\$15", r"\$200"],
     cite_ok_if=["search_products"])  # fmt: skip
site("gift_cards", ["how do I check my gift card balance?", "can I use a gift card at checkout?"],
     [HC + "2-4"], [r"can't|cannot|not (?:yet|able|possible)|isn't|turned off|off"])  # fmt: skip
site("cart", ["how do I change the quantity in my cart?", "how do I take something out of my cart?"],
     [HC + "2-5"], [r"[Cc]art page|[Cc]art"])  # fmt: skip
site("cart", ["is there a limit on how many I can add to my cart?"], [HC + "2-5"], [r"\b10\b|\bten\b"])
for t in ["can I make a wishlist?", "is there a save for later button?"]:
    one("cart", t, answer(cite_any=[HC + "2-5"], mentions_re=[NO], must_not_mention_re=[NOT_YES]))
site("tax", ["how is sales tax figured?", "why was I charged tax?"], [HC + "2-6", SD + "6"],
     [r"address"])  # fmt: skip
site("tax", ["do you charge tax on groceries?", "is food taxed?"], [HC + "2-6", SD + "6", R + "7-5"],
     [r"(?:aren't|are not|isn't|is not|not|no|without) (?:\w+ )?tax|tax.?(?:free|exempt)|exempt|untaxed"])  # fmt: skip

site("order_page", ["how do I get a receipt for an order?", "can I print an invoice?",
                    "I need a receipt for my headphones order"],
     [HC + "3-4"], [r"Receipt"])  # fmt: skip
site("order_page", ["how do I reorder something?", "is there a quick way to buy the same thing again?"],
     [HC + "3-5", HC + "2-5"], [r"Buy again"])  # fmt: skip
site("order_page", ["where can I see all my past orders?"], [HC + "3-1"], [r"Orders (?:&|and) returns"],
     cite_ok_if=["list_my_orders"])  # fmt: skip
site("order_change", ["can I change the shipping address on an order I already placed?",
                      "I typed the wrong address, can you fix it?",
                      "can I add something to an order I already placed?",
                      "can I cancel an order?"],
     [HC + "3-6", R + "8-1"], [CANT_SELF], must_not_mention_re=[r"(?:I've|I have) (?:changed|updated|canceled|cancelled)"])  # fmt: skip
site("payment", ["what does Payment failed mean on my order?", "my order says partially refunded, why?"],
     [HC + "3-7", R + "11-5"], [r"refund|payment|charge|person"],
     cite_ok_if=["get_refund_status"])  # answered from their own return  # fmt: skip

site("reviews", ["how do I write a review?", "where can I leave a review for something I bought?"],
     [HC + "4-1"], [r"Write a review"])  # fmt: skip
site("reviews", ["how many stars can I give in a review?"], [HC + "4-1"], [r"1 (?:to|-|–) 5|one to five|five stars|5 stars"])
site("reviews", ["do I have to buy something to review it?", "can I edit my review?"], [HC + "4-1"],
     [r"[Vv]erified purchase|(?:don't|do not|doesn't) (?:have|need)|no purchase|anyone|[Ee]dit|yes"])  # fmt: skip
site("stores", ["how many stores do you have?"], [HC + "5-1"], [r"\b10\b|\bten\b"], cite_ok_if=["list_stores"])
site("stores", ["can I check if a store has something in stock?", "does the Plano store have the Arc headphones on the shelf?"],
     [HC + "5-2"], [r"call|can't (?:see|tell|check)|online stock|not able|don't (?:see|know)"])  # fmt: skip
for t in ["can I pick up my order at a store?", "do you do curbside pickup?"]:
    one("stores", t, answer(cite_any=[HC + "5-2", SD + "5"], mentions_re=[NO], must_not_mention_re=[NOT_YES]))
site("contact", ["what's your customer service number?", "can I call someone?"], [HC + "6-1"], [r"555.?0100"])
site("contact", ["what's your support email?"], [HC + "6-1"], [r"help@serigan-mart\.example"])
site("contact", ["what are your customer service hours?"], [HC + "6-1"], [r"7\s?(?:AM|a\.m\.|am)", r"10\s?(?:PM|p\.m\.|pm)"])
site("contact", ["how long until someone gets back to me on a support case?", "when will a person reply?"],
     [HC + "6-2", R + "16-1"], [r"1 business day|one business day"])  # fmt: skip
site("contact", ["where do I see my support requests?"], [HC + "6-2"], [r"Your requests|Support page"],
     cite_ok_if=["list_my_support_cases"])  # fmt: skip
site("contact", ["what's the difference between you and Steph?"], [HC + "6-1"], [r"Steph"])
site("privacy", ["should I give you my card number to get my refund?"], [HC + "8", R + "11-2"],
     [r"(?:don't|do not|never|no need)"], no_refund_claim=True)  # fmt: skip

# --- 2. Shipping and delivery ---------------------------------------------------------------------

site("shipping", ["how much is shipping?", "what do you charge for delivery?", "is shipping free?",
                  "how much do I need to spend for free shipping?"],
     [SD + "1", R + "7-3"], [r"\$35|35 dollars|thirty.five"])  # fmt: skip
site("shipping", ["do you have express shipping?", "can I get overnight delivery?", "is there 2-day shipping?"],
     [SD + "1", SD + "3"], [r"standard|only one|don't offer|no (?:express|expedited|overnight|faster)|2.?(?:–|-|to)\s?5"])  # fmt: skip
for country in ["Canada", "Mexico", "the UK", "Germany", "Australia", "Japan"]:
    one("shipping", rng.choice(["do you ship to {c}?", "can you deliver to {c}?", "I live in {c}, can I order?"]).format(c=country),
        answer(cite_any=[SD + "2"], mentions_re=[r"United States|U\.S\.|\bUS\b|USA|America"],
               must_not_mention_re=[NOT_YES]))  # fmt: skip
site("shipping", ["do you ship internationally?"], [SD + "2"], [r"United States|U\.S\.|\bUS\b|USA"])
site("shipping", ["how long does delivery take?", "how fast do orders arrive?", "when will my order arrive if I order today?"],
     [SD + "3"], [r"2.?(?:–|-|to)\s?5|two to five"])  # fmt: skip
site("shipping", ["how soon do you ship after I order?"], [SD + "3", R + "8-1"], [r"1 business day|one business day"])
site("shipping", ["what does Preparing mean on my order?"], [SD + "4", HC + "3-2"],
     [r"payment|paid|haven't shipped|not (?:yet )?shipped|hasn't shipped|getting (?:it )?ready|being prepared|ship"])  # fmt: skip
site("shipping", ["what does In progress mean?"], [SD + "4"], [r"pack|on (?:the|its) way|shipping|being"])

# --- 3. Return and refund policy, section by section ----------------------------------------------

site("policy", ["the store sent me the wrong color, what do I do?", "I got someone else's item in my box"],
     [R + "4-3"], [r"return|wrong"])  # fmt: skip
site("policy", ["what if the item I got is defective?", "it arrived damaged, do I pay for the return?"],
     [R + "4-3", R + "6-1", R + "7-4"], [r"free|no (?:cost|charge|fee)|return"])  # fmt: skip
site("policy", ["my order is late, can I cancel it?", "what happens if you can't ship my order on time?"],
     [R + "8-1", HC + "3-6"], [r"cancel|new date|refund"])  # fmt: skip
site("policy", ["tracking hasn't updated in a week", "it says delivered but there's nothing at my door"],
     [R + "8-2"], [PERSON, r"replacement|refund|carrier"])  # fmt: skip
site("policy", ["if an order gets canceled do I get my money back?"], [R + "8-3"], [r"refund|full|original"])
site("policy", ["someone gave me a gift from your store, how do I return it?", "can I return a gift without the giver knowing?"],
     [R + "9"], [r"(?:person|account|someone) (?:who|that) (?:sent|gave|placed|bought|ordered)|giver|sender|"
                 r"place[ds]? the order|purchaser|whoever (?:bought|ordered|sent)|ask (?:them|the)"])  # fmt: skip
site("policy", ["can I swap my shoes for a bigger size?", "can I exchange this for another color?"],
     [R + "10-1"], [r"(?:don't|do not|no) (?:\w+ ){0,3}exchanges?|return (?:it )?for a refund|new order"])  # fmt: skip
site("policy", ["it went on sale the day after I bought it, can I get the difference back?"],
     [R + "10-2"], [NO], must_not_mention_re=[NOT_YES])  # fmt: skip
site("policy", ["what happens if my returned tablet fails inspection?", "what if you say my return was damaged by me?"],
     [R + "11-3", R + "16-2", R + "4-2", R + "15"],
     [r"not (?:be )?refunded|won't be refunded|ship (?:it|the item) back|review|person"])  # fmt: skip
site("policy", ["the refund was issued but I don't see it on my card", "how long until the refund shows on my statement?"],
     [R + "11-4"], [r"3.?(?:–|-|to)\s?10|three to ten"])  # fmt: skip
site("policy", ["what do I do if something I bought gets recalled?"], [R + "12-1"], [r"recall"])
site("policy", ["my air fryer broke after two months, what can I do?", "does Serigan Mart handle warranty claims?"],
     [R + "12-2"], [r"manufacturer|warranty"])  # fmt: skip
site("policy", ["if I file a chargeback will I still get my return refund?"], [R + "13"], [r"pause|paused|hold|dispute"])
site("policy", ["will I get banned for returning too much?"], [R + "15"], [r"abuse|decline|review|never count"])
site("policy", ["can I talk to someone about a return you declined?"], [R + "16-2", R + "16-1"], [PERSON + r"|review"],
     cite_ok_if=["handoff_to_person", "handoff"])  # fmt: skip
site("policy", ["how long is a return quote good for?"], [R + "1-3"], [r"15 minutes|fifteen minutes"])
site("policy", ["what reasons can I give for a return?"], [R + "5-2", R + "4-3"], [r"damaged|wrong item|no longer needed|defective|doesn't work"])
site("policy", ["can I return something with Steph instead of you?"], [R + "5-1"], [r"Steph|Orders (?:&|and) returns|same"])
site("policy", ["can I return something at the store if I bought it online?", "where can I drop off a return?"],
     [R + "6-2"], [r"drop.?off|store"], cite_ok_if=["list_stores"])  # fmt: skip
site("policy", ["do I need a box to send a return?", "can I put returns from two orders in one package?"],
     [R + "6-3", R + "4-1"], [r"one package|own package|separate|each return|package"])  # fmt: skip
site("policy", ["if I return everything do I get the shipping back?"], [R + "7-3"], [r"every (?:unit|item)|whole order|all (?:of )?the items|yes"])
site("policy", ["do gift cards get tax refunded?"], [R + "7-5", R + "3-1"], [r"final sale|no tax|not taxed|can't be returned"])
site("policy", ["what's the refund timing for cheap items?"], [R + "11-1"], [r"instant|scan"])
site("policy", ["will my refund go to my bank account or card?"], [R + "11-2"],
     [r"original(?:ly)? (?:payment|paid)|card you (?:originally )?paid|paid with|same card"])
site("policy", ["my old card was closed, where does my refund go?"], [R + "11-2"], [r"bank|new card|person"])

# --- 4. The catalog: questions about all of it ------------------------------------------------------

by_type: dict[str, list[Any]] = defaultdict(list)
for p in PRODUCTS:
    by_type[p.product_type].append(p)
TYPE_WORD = {**B.TYPE_WORDS}


def tword(t: str) -> str:
    return TYPE_WORD.get(t) or t.replace("-", " ") + ("" if t.endswith("s") else "s")


# Brands: every brand of a kind of product.
brand_types = sorted(t for t, ps in by_type.items() if 3 <= len(ps) <= 30 and 2 <= len({p.brand for p in ps}) <= 4)
for t in rng.sample(brand_types, 24):
    brands = sorted({p.brand for p in by_type[t]})
    one("brands", rng.choice(["what brands of {w} do you carry?", "which {w} brands do you have?",
                              "who makes the {w} you sell?", "what brands do you have for {w}?"]).format(w=tword(t)),
        answer(uses=["search_products"], mentions_re=[re.escape(b) for b in brands]),
        note=f"{t}: {', '.join(brands)}")  # fmt: skip

# Counts: how many of a kind.
count_types = sorted(t for t, ps in by_type.items() if 4 <= len(ps) <= 40)
for t in rng.sample(count_types, 20):
    n = len(by_type[t])
    one("count", rng.choice(["how many {w} do you have?", "how many kinds of {w} do you sell?",
                             "how many different {w} are there?"]).format(w=tword(t)),
        answer(mentions_re=[num(n)]), note=f"{t}: {n} products")  # fmt: skip

# Cheapest and priciest of a kind.
def max_price(p: Any) -> int:
    return max((v.price_cents or p.price_cents) for v in p.variants)


for t in rng.sample(sorted(t for t, ps in by_type.items() if len(ps) >= 3), 30):
    most = rng.random() < 0.5
    key = max_price if most else min_price
    ps = sorted(by_type[t], key=key)
    pick, other = (ps[-1], ps[-2]) if most else (ps[0], ps[1])
    if key(pick) == key(other):
        continue
    text = rng.choice(["what's your most expensive {w}?", "which {w} costs the most?"] if most
                      else ["what's the cheapest {w} you have?", "which {w} is the least expensive?",
                            "lowest priced {w}?"]).format(w=tword(t).removesuffix("s") if rng.random() < 0.3 else tword(t))  # fmt: skip
    one("price_extreme", text, {"action": "search", "search": {"product_type": [t]}, "winner": pick.slug,
                                "winner_title": pick.title, "mentions_re": [price(key(pick))]},
        note=f"{pick.title} {price(key(pick))}")  # fmt: skip

# Price ranges and floors.
range_types = sorted(t for t, ps in by_type.items() if len(ps) >= 5)
for t in rng.sample(range_types, 24):
    prices = sorted(min_price(p) for p in by_type[t])
    lo = prices[len(prices) // 3] // 500 * 500
    hi = prices[2 * len(prices) // 3] // 500 * 500 + 500
    if lo == 0 or hi <= lo:
        continue
    if rng.random() < 0.5:
        search = {"product_type": [t], "min_price_minor": lo}
        text = rng.choice(["show me {w} over ${a}", "{w} that cost more than ${a}", "any {w} above ${a}?"])
    else:
        search = {"product_type": [t], "min_price_minor": lo, "max_price_minor": hi}
        text = rng.choice(["{w} between ${a} and ${b}", "I want {w} in the ${a} to ${b} range",
                           "show me {w} from ${a} to ${b}"])  # fmt: skip
    if not G.hits(search):
        continue
    one("price_range", text.format(w=tword(t), a=lo // 100, b=hi // 100),
        {"action": "search", "search": search, "all_results_match": True})

# Things we don't sell.
# question: (product type that must not exist, how the answer names the thing)
NOT_SOLD = {
    "do you sell laptops?": ("laptop", r"laptops?|computers?"), "do you have any beer?": ("beer", r"beer|alcohol"),
    "can I buy wine here?": ("wine", r"wine|alcohol"), "do you carry cigarettes?": ("cigarette", r"cigarettes?|tobacco"),
    "do you sell couches?": ("sofa", r"couch(?:es)?|sofas?|furniture"),
    "do you have refrigerators?": ("refrigerator", r"refrigerators?|fridges?|appliances?"),
    "do you sell washing machines?": ("washer", r"washing machines?|washers?|appliances?"),
    "do you have car tires?": ("tire", r"tires?|auto"), "can I fill a prescription here?": ("prescription", r"prescriptions?|pharmacy"),
    "do you sell cell phones?": ("smartphone", r"phones?"), "do you carry video games?": ("video-game", r"(?:video )?games?"),
    "do you sell books?": ("book", r"books?"), "do you have fresh flowers?": ("flower", r"flowers?"),
    "do you sell pianos?": ("piano", r"pianos?|instruments?"), "do you carry jewelry?": ("jewelry", r"jewelry"),
    "do you sell guitars?": ("guitar", r"guitars?|instruments?"), "do you have baby formula?": ("formula", r"formula"),
    "do you sell lawn mowers?": ("mower", r"(?:lawn )?mowers?"),
}  # fmt: skip
types = set(by_type)
for text, (word, thing) in NOT_SOLD.items():
    clash = [t for t in types if t == word or t.startswith(word + "-") or t.endswith("-" + word) or t == word + "s"]
    if clash:
        problems.append(f"{text}: the catalog has {clash}")
        continue
    one("not_sold", text, answer(mentions_re=[WE_DONT_SELL, thing], must_not_mention_re=[NOT_YES]))

# Do you sell X (yes), new kinds.
for t in rng.sample(sorted(t for t, ps in by_type.items() if len(ps) >= 2 and (tuple([t]), ()) not in B.USED_SEARCHES), 24):
    text = rng.choice(["do you carry {w}?", "do y'all have {w}?", "I'm looking for {w}", "got any {w}?",
                       "do you sell {w}?"]).format(w=tword(t))  # fmt: skip
    expect = G.search_expect(types=[t], label=text)
    if expect:
        one("do_you_sell", text, expect)

# One named product: colors, sizes, warranty, rating, reviews.
NAMED = [p for p in PRODUCTS if G.unique_name(p) and p.slug not in B.USED_SLUGS]
def variant_re(v: str) -> str:
    pounds = re.match(r"(\d+(?:\.\d+)?) lb\b", v)
    if pounds:  # "15 lb bag" is also "15-pound", and "15-, 30-, and 40-pound bags"
        n = re.escape(pounds.group(1))
        return rf"(?<![\d.]){n}(?:\s?-?\s?(?:lb|lbs|pounds?)\b|-,|-\s+(?:and|or)\b)"
    m = re.match(r"(\d+) x ", v)
    if not m:
        return G.spec_pattern(v)
    n = int(m.group(1))
    count = f"(?:{n}|{G.WORDS[n]})" if n <= 12 else str(n)
    # "4 x 5.3 oz cups" is also "a 4-pack" or "four 5.3 oz cups"
    return (
        rf"(?<![\d.]){count}\s?[- ]?(?:x\b|pack|count|ct\b)|pack of {count}|"
        rf"\b{count}\s+\d[\d.]*\s?-?\s?[a-z]|{G.spec_pattern(v)}"
    )


SIZES = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"]


def variants_re(names: list[str]) -> list[str]:
    """Every variant named, or for a run of letter sizes also the range ("XS through XXL")."""
    each = [variant_re(v) for v in names]
    upper = [v.upper() for v in names]
    if len(names) >= 3 and all(u in SIZES for u in upper):
        at = [SIZES.index(u) for u in upper]
        if at == list(range(at[0], at[0] + len(at))):
            ahead = "".join(f"(?=.*(?:{e}))" for e in each)
            span = rf"\b{upper[0]}\s*(?:through|thru|to|-|\u2013|\u2014)\s*{upper[-1]}\b"
            return [rf"(?s)^{ahead}|{span}"]
    return each


multi_variant = [p for p in NAMED if 3 <= len(p.variants) <= 6 and len({v.name for v in p.variants}) == len(p.variants)]
for p in rng.sample(multi_variant, 20):
    names = [v.name for v in p.variants]
    one("variants", rng.choice(["what options does the {n} come in?", "what are the choices for the {n}?",
                                "which sizes or colors does the {n} have?"]).format(n=name(p)),
        answer(product_title=p.title, mentions_re=variants_re(names)),
        note=", ".join(names))  # fmt: skip
with_warranty = [p for p in NAMED if p.specs.get("Warranty")]
for p in rng.sample(with_warranty, 16):
    one("warranty", rng.choice(["what's the warranty on the {n}?", "how long is the {n} covered?",
                                "does the {n} come with a warranty?"]).format(n=name(p)),
        answer(product_title=p.title, mentions_re=[G.spec_pattern(p.specs["Warranty"])]),
        note=f"Warranty: {p.specs['Warranty']}")  # fmt: skip
for p in rng.sample([p for p in NAMED if p.category in ("electronics", "home-kitchen", "outdoor", "toys", "sports")], 14):
    one("reviews", rng.choice(["what do people say about the {n}?", "is the {n} any good?",
                               "what's the rating on the {n}?", "any complaints about the {n}?"]).format(n=name(p)),
        answer(product_title=p.title, uses_any=["get_product_reviews", "search_products", "get_product_details"],
               mentions_re=[r"stars?|out of 5|/5|rating|review"]))  # fmt: skip

# Gift and budget picks: anything, within the budget.
for text, cap in [("a gift for a coffee lover under $40", 4000), ("something for a 10 year old under $25", 2500),
                  ("birthday gift ideas under $20", 2000), ("a housewarming gift under $50", 5000),
                  ("stocking stuffers under $10", 1000), ("a gift for someone who runs, under $60", 6000)]:  # fmt: skip
    one("gift", text, {"action": "search", "search": {"max_price_minor": cap}, "all_results_match": True})

# --- 5. Orders and ordered items (Dana, Bob, and Alice) -----------------------------------------------

oid, onum = B.oid, B.onum


def facts(key: str, *fields: str) -> list[dict[str, str]]:
    return [{"order_id": oid(key), "field": f} for f in fields]


def order_q(category: str, texts: list[str], user: str, key: str | None = None, fields: tuple[str, ...] = (),
            mentions_re: list[str] | None = None, **kw: Any) -> None:  # fmt: skip
    for t in texts:
        exp = answer(not_uses=["quote_return", "propose_return"], mentions_re=mentions_re, **kw)
        if key and fields:
            exp["order_facts"] = facts(key, *fields)
        one(category, t, exp, user, order=key)


def money(m: int) -> str:
    """An amount as the answer may write it: "$5.00" or "$5" for whole dollars."""
    if m % 100 == 0:
        return rf"\${m // 100:,}(?:\.00)?(?![\d.])"
    return price(m)


def line(key: str, slug: str) -> Any:
    return next(ln for ln in ORDERS[key].lines if ln.product.slug == slug)


SPEAKER, BARS = "lumen-labs-beam-go-waterproof-bluetooth-speaker", "ironpeak-nutrition-chocolate-chip-cookie-dough-protein-bar"
SHOES, LEGGINGS = "stridewell-men-s-cushioned-running-shoes-black", "tempo-athletics-women-s-high-waisted-leggings-25-in-navy"
TV, FRYER, BOARD = "novaview-55-inch-4k-uhd-smart-tv", "crispwell-digital-air-fryer-6-qt", "serigan-mart-home-bamboo-cutting-board-15-x-10-in"
PIZZA, ICE_CREAM = "brickyard-pizza-co-bbq-chicken-pizza", "moonlit-creamery-coffee-ice-cream"
DOG_FOOD, BIG_BOARD = "meadowbrook-pet-puppy-dry-dog-food-chicken-and-brown-rice", "kettleworth-end-grain-acacia-cutting-board-18-x-12-in"
dana_keys = [k for k in ORDERS if k.startswith("dana-")]
if len(dana_keys) != 7:
    problems.append(f"Dana has {len(dana_keys)} seeded orders, expected 7")

# History and counts.
order_q("history", ["show me my orders", "what have I ordered from you?", "list my order history"], DANA,
        mentions_re=[r"speaker|protein", r"TV|television"], uses=["list_my_orders"])  # fmt: skip
order_q("history", ["how many orders have I placed?", "how many orders do I have with you?"], DANA,
        mentions_re=[num(7)])  # fmt: skip
order_q("history", ["how many orders have I made?"], BOB, mentions_re=[num(3)])
alice_total = sum(o.total_minor for k, o in ORDERS.items() if k.startswith("alice-"))
order_q("history", ["how much have I spent with you in total?", "what's my total spending on all my orders?"], ALICE,
        mentions_re=[money(alice_total)])  # fmt: skip
order_q("history", ["what was my last order?", "what's in my newest order?"], DANA, key="dana-preparing",
        mentions_re=[r"speaker|Beam", r"protein bars?|Ironpeak"])  # fmt: skip
order_q("history", ["what did I order about two weeks ago?"], DANA, key="dana-tv", mentions_re=[r"TV|television|Novaview"])
order_q("history", ["have I ever bought ice cream from you?"], DANA, mentions_re=[r"Moonlit|Coffee Ice Cream"])
order_q("history", ["did I order any frozen pizza?"], DANA, mentions_re=[r"Brickyard|BBQ Chicken"])
NEVER = (r"(?:don't|do not|didn't|did not|haven't|have not|can't|cannot) (?:\w+ ){0,3}(?:see|find|order|ordered|"
         r"bought|buy|purchased?)|no (?:\w+ ){0,3}(?:in your|on your|orders?|purchases?|history)|not (?:in|on) (?:your|any)|in them|in any of|"
         r"none (?:of (?:them|your orders) )?(?:include|includes|have|has|contain|contains|had|were)|"
         r"(?:shows?|has|have|see|found|includes?) no\b")  # fmt: skip
for t in ["have I ever ordered headphones?", "did I buy a coffee maker from you?"]:
    one("history", t, answer(mentions_re=[NEVER], uses=["list_my_orders"], must_not_mention_re=[NOT_YES]), DANA)

# The order not shipped yet (Preparing).
order_q("status", ["has my speaker shipped yet?", "where's my protein bar order?", "is my latest order on its way?",
                   "can I get tracking for my speaker?"], DANA, key="dana-preparing",
        mentions_re=[NOT_SHIPPED], must_not_mention_re=[r"(?:was|has been) delivered|out for delivery|in transit"])  # fmt: skip
order_q("status", ["what's the status of my TV order?", "did my Novaview TV arrive?"], DANA, key="dana-tv",
        fields=("delivered_on",), mentions_re=[DELIVERED])  # fmt: skip
order_q("status", ["what happened to my acacia cutting board order?", "why didn't my end-grain cutting board ever come?"],
        DANA, key="dana-canceled", mentions_re=[CANCELED])  # fmt: skip
order_q("status", [f"what's the status of order {onum('dana-pet')}?", f"can you look up order {onum('dana-frozen')}?"],
        DANA, mentions_re=[DELIVERED])  # fmt: skip
order_q("status", ["which carrier delivered my TV?"], DANA, key="dana-tv", fields=("carrier",))
order_q("status", ["what's the tracking number for my dog food?"], DANA, key="dana-pet", fields=("tracking_number",))
order_q("status", ["when did my running shoes arrive?", "what day was the dog food delivered?"], DANA,
        key=None, mentions_re=[DELIVERED])  # fmt: skip
order_q("status", ["when did I order the air fryer?"], DANA, key="dana-kitchen-old", fields=("placed_on",))

# What was in an order, and what it cost.
order_q("items", ["what size shoes did I order?", "what size were the Stridewell shoes I bought?"], DANA,
        key="dana-running", mentions_re=[r"\b9\b|nine"], must_not_mention_re=[r"9\.5|nine and a half"])  # fmt: skip
order_q("items", ["what color speaker did I get?"], DANA, key="dana-preparing", mentions_re=[r"[Tt]eal"])
order_q("items", ["how many leggings did I buy?", "what size leggings did I order?"], DANA, key="dana-running",
        mentions_re=[r"\b2\b|two|\bM\b|medium"])  # fmt: skip
order_q("items", ["what size bag of dog food did I get?"], DANA, key="dana-pet", mentions_re=[r"15.?(?:lb|pound)"])
order_q("items", ["how many protein bars are in my order?"], DANA, key="dana-preparing", mentions_re=[r"\b12\b|twelve"])
TV_PAID = f"{money(line('dana-tv', TV).unit_price_minor)}|{money(ORDERS['dana-tv'].total_minor)}"
order_q("amounts", ["how much did I pay for the TV?", "what did the Novaview TV cost me?"], DANA, key="dana-tv",
        mentions_re=[TV_PAID])  # fmt: skip
order_q("amounts", ["how much were the running shoes?"], DANA, key="dana-running",
        mentions_re=[money(line("dana-running", SHOES).unit_price_minor)])  # fmt: skip
order_q("amounts", ["did I get a discount on the leggings?", "was there a discount on my leggings order?"], DANA,
        key="dana-running", mentions_re=[money(line("dana-running", LEGGINGS).discount_minor)])  # fmt: skip
order_q("amounts", ["how much tax did I pay on the TV?"], DANA, key="dana-tv", mentions_re=[money(ORDERS["dana-tv"].tax_minor)])
order_q("amounts", ["was I charged shipping on the pizza order?", "why did I pay shipping on my frozen food order?"],
        DANA, key="dana-frozen", mentions_re=[money(ORDERS["dana-frozen"].shipping_minor)])  # fmt: skip
order_q("amounts", ["did I pay shipping on my shoes order?"], DANA, key="dana-running",
        mentions_re=[r"free|no shipping|\$0(?:\.00)?|didn't pay|did not pay|wasn't charged|no charge"])  # fmt: skip
order_q("amounts", ["what's the subtotal on my running order?"], DANA, key="dana-running",
        mentions_re=[money(ORDERS["dana-running"].subtotal_minor)])  # fmt: skip
order_q("amounts", ["what was the total for my dog food order?"], DANA, key="dana-pet", fields=("total",))
order_q("amounts", ["did they charge tax on my ice cream and pizza?"], DANA, key="dana-frozen",
        mentions_re=[r"(?:no|not|wasn't|weren't|without|\$0(?:\.00)?) (?:\w+ )?tax|tax.?(?:free|exempt)|untaxed|no sales tax|\$0\.00"])  # fmt: skip
order_q("order_page", ["what card did I use for the TV?"], DANA, key="dana-tv", mentions_re=[r"order'?s? page|Orders (?:&|and) returns"],
        must_not_mention_re=[r"[Aa]mex|American Express|0005|Visa|Mastercard"])  # fmt: skip
order_q("order_page", ["what address did my TV go to?"], DANA, key="dana-tv", mentions_re=[r"order'?s? page|Orders (?:&|and) returns"],
        must_not_mention_re=[r"Greenville"])  # fmt: skip
order_q("order_page", ["can I get a receipt for my TV?"], DANA, key="dana-tv", mentions_re=[r"Receipt"])
order_q("order_page", ["can you cancel my speaker order?", "I want to change the address on my speaker order"], DANA,
        key="dana-preparing", cite_any=[HC + "3-6", R + "8-1"], cite_ok_if=["handoff", "person"],
        must_not_mention_re=[r"(?:I've|I have) (?:changed|updated|canceled|cancelled)"])  # fmt: skip
order_q("items", ["what did I order with my tablet?"], BOB, key="bob-tablet", mentions_re=[r"only|just|tablet"])
order_q("items", ["how much was my french press?"], BOB, key="bob-canceled",
        mentions_re=[money(line("bob-canceled", "kettleworth-french-press").unit_price_minor) + "|" + CANCELED])  # fmt: skip

# --- 6. Returns with Dana's orders ----------------------------------------------------------------------


def quote(texts: list[str], key: str, slugs: list[str], qty: int = 1, user: str = DANA, **extra: Any) -> None:
    q, outcome = G.quote_expect(user, key, slugs, qty)
    for t in texts:
        action = "quote_or_offer" if re.search(r"\bcan i\b.*\?$", t, re.I) else "quote"
        one("return_quote", t, {"action": action, "quote": q, **extra}, user, order=key, outcome=outcome)


def refuse(texts: list[str], key: str, reason: str, slugs: list[str], mentions_re: list[str], user: str = DANA,
           **extra: Any) -> None:  # fmt: skip
    out = G.expected_outcome(user, ORDERS[key], slugs, 1)
    if out.get("reason") != reason:
        problems.append(f"{texts[0]}: expected {reason}, the reference says {out.get('reason')}")
    for t in texts:
        one("not_eligible", t, {"action": "refuse", "mentions_re": mentions_re, **extra}, user, order=key,
            outcome={"lines": slugs, "eligible": False, "reason": reason, "refund_minor": 0,
                     "confirmation_required": False})  # fmt: skip


quote(["I want to return my running shoes", "send back the Stridewell shoes, they're too small"], "dana-running", [SHOES])
quote(["return one pair of the leggings", "I only want to send back one of the leggings"], "dana-running", [LEGGINGS], 1)
quote(["return both pairs of leggings"], "dana-running", [LEGGINGS], 2)
quote(["I want to return the TV", "the Novaview TV has a dead pixel, I want to send it back"], "dana-tv", [TV])
quote(["my ice cream arrived melted, I want a refund", "the coffee ice cream was all melted when it got here"],
      "dana-frozen", [ICE_CREAM])  # fmt: skip
quote(["both pizzas were thawed when they came, refund them please"], "dana-frozen", [PIZZA], 2)
quote(["return the dog food, my puppy won't eat it"], "dana-pet", [DOG_FOOD])
# A change of mind about fresh food: the engine would price it (it's within 7 days), so the rule
# Xena applies is the quality-problem one (section 3.2), not a reason code.
for t in ["I don't like the pizza, can I return it?", "can I send back the ice cream? I changed my mind"]:
    one("not_eligible", t, {"action": "refuse", "mentions_re": [r"change of mind|changed (?:your )?mind|don't like|quality|"
                                                               r"spoiled|damaged|thawed|melted|can't|cannot|isn't|not"]},
        DANA, order="dana-frozen")  # fmt: skip
refuse(["I want to return my air fryer", "can I still return the bamboo cutting board?"], "dana-kitchen-old",
       "outside_window", [FRYER], [PAST_30])  # fmt: skip
refuse(["return my speaker", "can I return the protein bars?"], "dana-preparing", "not_delivered", [SPEAKER],
       [NOT_DELIVERED + "|" + NOT_SHIPPED])  # fmt: skip
refuse(["I want to return the acacia cutting board"], "dana-canceled", "canceled", [BIG_BOARD], [CANCELED])
order_q("returns", ["which of my orders can I still return?"], DANA,
        mentions_re=[r"shoes|leggings|running", r"TV|television", r"dog food|puppy food|Meadowbrook"])  # fmt: skip
order_q("returns", ["how many days do I have left to return the running shoes?"], DANA, key="dana-running",
        mentions_re=[r"\b[56]\b|five|six|(?:through|until|by|ends?(?: on)?) (?:\w+, )?\w+ \d"],
        must_not_mention_re=[r"too late|past (?:the|its|your) (?:30.day )?(?:return )?window"])  # fmt: skip
order_q("returns", ["is it too late to return my leggings?"], DANA, key="dana-running",
        mentions_re=[r"(?:not|isn't) too late|still (?:return|eligible|time|within|be returned|can)|can (?:still )?(?:return|send)|"
                     r"(?:are|is) (?:still )?eligible|eligible for (?:a )?return"],
        must_not_mention_re=[r"(?<!not )(?<!n't )too late|past (?:the|its|your) (?:30.day )?(?:return )?window"])  # fmt: skip
order_q("returns", ["do I have any returns going?", "where's my refund?"], DANA,
        mentions_re=[r"(?:don't|do not|haven't|have not|can't|cannot) (?:\w+ ){0,3}(?:have|see|find|started|any)|"
                     r"no (?:\w+ )?(?:returns?|refunds?)|not (?:started|any|see)|nothing"],
        uses_any=["get_refund_status", "list_my_orders"], must_not_mention_re=[NOT_YES])  # fmt: skip

# --- 7. Multi-part, long, and other-language messages -------------------------------------------------

one("multi", "has my speaker shipped yet, and can I still return my running shoes?",
    answer(mentions_re=[NOT_SHIPPED, r"\byes\b|can still|eligible|can return|still return|until|returnable"]), DANA,
    order="dana-preparing")
one("multi", "what's your return window and do you ship to Canada?",
    answer(cite=["returns-and-refunds", SHIP], mentions_re=[r"30|thirty", r"United States|U\.S\.|\bUS\b|USA"]))
one("multi", "where's my yoga mat, and do you sell vegan cheese?",
    answer(order_facts=facts("alice-in-transit", "arriving_by"), uses=["search_products"]), order="alice-in-transit")
one("multi", "how much did I pay for my TV, and how long do refunds take for electronics?",
    answer(mentions_re=[TV_PAID, r"inspect"]), DANA, order="dana-tv")
one("multi", "do you take PayPal and is there a promo code I can use?",
    answer(cite_any=[HC + "2-2", HC + "2-3"], mentions_re=[r"PayPal", r"promo|code|coupon"]))
one("multi", "two things: what's your phone number, and how do I reset my password?",
    answer(cite_any=[HC + "6-1", HC + "1-2"], mentions_re=[r"555.?0100", r"password"]))
one("multi", "can I return the gift card, and when does my yoga mat arrive?",
    answer(mentions_re=[FINAL], order_facts=facts("alice-in-transit", "arriving_by")), order="alice-in-transit")
one("multi", "what size shoes did I get and what's the warranty on the TV I bought?",
    answer(mentions_re=[r"\b9\b|nine", G.spec_pattern(CATALOG[TV].specs.get("Warranty", "1-year"))]), DANA)
LONG = [
    ("Hi there. So I ordered a TV from you guys a couple of weeks ago for my living room, and it's been great, "
     "but my brother-in-law just told me he's giving me his old one, so honestly I don't really need it anymore. "
     "It's still in perfect shape and I kept all the cables. What would I get back if I return it?",
     {"action": "quote_or_offer", "quote": G.quote_expect(DANA, "dana-tv", [TV], 1)[0]}, DANA, "dana-tv"),
    ("OK this is kind of a long story but my sister came to visit, we ordered pizza and ice cream from you for movie "
     "night, and the delivery got left on the porch in the sun for hours. The ice cream was soup by the time we found "
     "it. The pizzas were fine actually. Can I get my money back for the ice cream?",
     {"action": "quote", "quote": G.quote_expect(DANA, "dana-frozen", [ICE_CREAM], 1)[0]}, DANA, "dana-frozen"),
    ("Hello, I'm trying to figure out my budget for the month and I need to know two things about my orders: "
     "how much did the dog food cost, and did I pay shipping on it? Thanks so much.",
     answer(mentions_re=[f"{money(line('dana-pet', DOG_FOOD).unit_price_minor)}|{money(ORDERS['dana-pet'].total_minor)}",
                         money(ORDERS["dana-pet"].shipping_minor)]), DANA, "dana-pet"),
    ("I've been shopping with you for a while and I really like the store, but I have a question I couldn't find "
     "an answer to anywhere on the site. If I buy something and then the price drops the next week, which happened "
     "to me at another store, do you give the difference back?",
     answer(cite_any=[R + "10-2"], mentions_re=[NO], must_not_mention_re=[NOT_YES]), ALICE, None),
    ("So my grandmother wants to order from you but she lives in Toronto. I told her I'd ask. She'd want to buy "
     "some of the kitchen stuff and maybe a gift card for my cousin. Can you ship there?",
     answer(cite_any=[SD + "2"], mentions_re=[r"United States|U\.S\.|\bUS\b|USA"], must_not_mention_re=[NOT_YES]), ALICE, None),
    ("I bought running shoes for my son for track season, size 9 I think, but he grew again (of course) and now "
     "they pinch his toes. He's only worn them around the house. Can I swap them for a 9.5?",
     answer(cite_any=[R + "10-1"], mentions_re=[r"(?:don't|do not|no) (?:\w+ )?exchanges?|return (?:them |it )?for a refund|new order|place a new"]),
     DANA, "dana-running"),
]  # fmt: skip
for text, expect, user, key in LONG:
    one("long", text, expect, user, order=key)

OTHER_LANG = [
    ("¿Cuál es el número de seguimiento de mi esterilla de yoga?", answer(order_facts=facts("alice-in-transit", "tracking_number")), ALICE, "alice-in-transit"),
    ("¿Cuánto pagué por mi pedido de audífonos?", answer(order_facts=facts("alice-headphones", "total")), ALICE, "alice-headphones"),
    ("¿Hacen envíos a Canadá?", answer(cite_any=[SD + "2"]), ALICE, None),
    ("¿Cuánto cuesta el envío?", answer(cite_any=[SD + "1"], mentions_re=[r"5[.,]99"]), ALICE, None),
    ("Quiero devolver mis audífonos Pulse", {"action": "quote", "quote": G.quote_expect(ALICE, "alice-headphones", ["sonora-pulse-wireless-earbuds"], 1)[0]}, ALICE, "alice-headphones"),
    ("Mi helado llegó derretido, quiero un reembolso", {"action": "quote", "quote": G.quote_expect(DANA, "dana-frozen", [ICE_CREAM], 1)[0]}, DANA, "dana-frozen"),
    ("¿Tienen leche sin lactosa?", G.search_expect(types=["milk"], tags=["lactose-free"], label="leche sin lactosa"), ALICE, None),
    ("Combien de temps ai-je pour retourner un article ?", answer(cite_any=[R + "2-1", R + "1-4"], mentions_re=[r"30"]), ALICE, None),
    ("Est-ce que je peux retourner une carte cadeau ?", answer(cite_any=[R + "3-1", R + "1-4"]), ALICE, None),
    ("Vocês entregam no Brasil?", answer(cite_any=[SD + "2"]), ALICE, None),
    ("Wie lange dauert der Versand normalerweise?", answer(cite_any=[SD + "3"], mentions_re=[r"2.?(?:–|-|bis|to)\s?5"]), ALICE, None),
    ("¿Cuántos pedidos he hecho?", answer(mentions_re=[num(7)]), DANA, None),
]  # fmt: skip
for text, expect, user, key in OTHER_LANG:
    one("other_language", text, expect, user, order=key)

# --- 8. A person, and upset customers -------------------------------------------------------------------

for t in ["I want to talk to a human", "get me a manager", "can I speak to a real person please",
          "transfer me to an agent", "I need a supervisor right now"]:  # fmt: skip
    one("person", t, {"action": "handoff", "uses": ["handoff_to_person"]})
site("upset", ["this is the third time I'm asking, my package never came and tracking says delivered",
               "I'm really frustrated, my order says delivered but I never got it"],
     [R + "8-2"], [PERSON])  # fmt: skip
site("upset", ["I think you charged me twice and I'm not happy about it"], [HC + "3-7", R + "13"], [PERSON], user=DANA)
site("upset", ["your inspection rejected my return and that's not fair"], [R + "16-2", R + "11-3"], [PERSON + r"|review"])

# --- Write ------------------------------------------------------------------------------------------------


def locked(case: dict[str, Any]) -> bool:
    """Half of the cases, by a fixed hash of what's asked: the same question always lands on the
    same side, whatever else is added."""
    key = " / ".join(t["user"] for t in case["turns"])
    return int(hashlib.sha256(key.encode()).hexdigest(), 16) % 2 == 0


def main() -> None:
    if problems:
        print("The support sets don't match the seed data:", *problems, sep="\n  ")
        sys.exit(1)
    dev = [c for c in pool.cases if not locked(c)]
    held = [c for c in pool.cases if locked(c)]
    for i, c in enumerate(dev, 1):
        c["id"] = f"s-{i:03d}"
    for i, c in enumerate(held, 1):
        c["id"] = f"h-{i:03d}"
    for folder, fname, cases in ((SUPPORT, "support.jsonl", dev), (LOCKED, "holdout.jsonl", held)):
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / fname
        path.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases), encoding="utf-8",
                        newline="\n")  # fmt: skip
        cats = Counter(c["category"] for c in cases)
        print(f"{path.relative_to(ROOT)}: {len(cases)} cases {dict(sorted(cats.items()))}")


if __name__ == "__main__":
    main()
