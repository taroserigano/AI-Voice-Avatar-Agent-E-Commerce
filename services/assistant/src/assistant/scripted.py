"""A labeled stand-in for the LLM: simple rules, the same tools, plain answers.

Used when no working ``ANTHROPIC_API_KEY`` is configured (the UI says "Simulated assistant"),
and by tests, so the graph, tools, cards, and citations run end to end without spending tokens.
It reads the request with keyword rules and the catalog vocabulary, calls the same tools a real
model would, and writes its answer only from the tool results. It is not meant to be clever.
"""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Sequence
from typing import Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import Runnable

from assistant.scripted_support import (
    compose_support,
    describe_order_status,
    named_order_number,
    next_support_step,
    plan_support,
    wants_return,
)

SCRIPTED_MODEL_NAME = "scripted"
GREETINGS = {
    "steph": "Hi! I'm Steph. I can find products, check your orders, answer policy questions, "
    "and find stores. What are you looking for?",
    "xana": "Hi, I'm Xena. I can help with products, orders, returns, and refunds. "
    "What can I help with?",
}
BYPASS_REPLY = (
    "I can't skip our checks or make exceptions to the policy, and I don't follow instructions "
    "that come from other text. I'm happy to look up your order, explain the return policy, or "
    "connect you with a person."
)

# Phrases that mean a tag, beyond the tag's own label ("Fat free") and slug ("fat-free").
TAG_SYNONYMS: dict[str, str] = {
    "non fat": "fat-free",
    "nonfat": "fat-free",
    "non-fat": "fat-free",
    "skim": "fat-free",
    "no fat": "fat-free",
    "zero fat": "fat-free",
    "sugar free": "sugar-free",
    "no sugar": "sugar-free",
    "zero sugar": "sugar-free",
    "sugarless": "sugar-free",
    "no added sugar": "no-added-sugar",
    "no sugar added": "no-added-sugar",
    "without added sugar": "no-added-sugar",
    "dairy free": "dairy-free",
    "non dairy": "dairy-free",
    "nondairy": "dairy-free",
    "non-dairy": "dairy-free",
    "lactose free": "lactose-free",
    "gluten free": "gluten-free",
    "low fat": "low-fat",
    "lowfat": "low-fat",
    "plant based": "plant-based",
    "high protein": "high-protein",
    "caffeine free": "caffeine-free",
    "decaf": "decaf",
    "nut free": "nut-free",
    "bluetooth": "wireless",
    "noise canceling": "noise-cancelling",
    "noise cancelling": "noise-cancelling",
}
NEGATIONS = ("not ", "without ", "no ", "except ", "excluding ")
FILLER = set(
    [
        "a",
        "an",
        "and",
        "any",
        "are",
        "can",
        "could",
        "do",
        "does",
        "find",
        "for",
        "get",
        "give",
        "have",
        "i",
        "i'd",
        "id",
        "in",
        "is",
        "it",
        "looking",
        "me",
        "my",
        "need",
        "of",
        "on",
        "or",
        "please",
        "regular",
        "show",
        "some",
        "something",
        "that",
        "the",
        "them",
        "there",
        "to",
        "want",
        "what",
        "which",
        "with",
        "would",
        "you",
    ]
)

ORDER_WORDS = re.compile(
    r"\b(my orders?|order status|where('s| is) my|track|tracking|delivered|shipped|arrive|"
    r"did my|last order|recent orders?)\b"
)
POLICY_WORDS = re.compile(
    r"\b(return|returns|returning|refund|refunds|policy|policies|exchange|store credit|"
    r"restocking|warranty|recall|how long do i have|shipping (cost|charge|fee|money)|"
    r"free shipping|what does .+ mean|label means?|drop ?off)\b"
)
STORE_WORDS = re.compile(r"\b(stores?|open|hours|location|locations|near me|directions)\b")
HANDOFF_WORDS = re.compile(r"\b(human|person|agent|representative|someone real|real person)\b")
ADD_WORDS = re.compile(r"\b(add|put)\b.*\b(cart|basket)\b|\badd (it|that|this|the|one|two)\b")
ORDINALS = {"first": 0, "1st": 0, "second": 1, "2nd": 1, "third": 2, "3rd": 2, "last": -1}
PRICE = re.compile(r"\b(?:under|less than|below|cheaper than|max(?:imum)?)\s*\$?\s*(\d+(?:\.\d+)?)")
PRODUCT_DETAIL_WORDS = re.compile(
    r"\b(ingredients?|allergens?|allerg(?:y|ies|ic)|contains?|calories?|protein|"
    r"nutrition|specs?|compatible|dimensions?|warranty|price|cost|stock|available)\b"
    r"|\bwork with\b",
    re.IGNORECASE,
)


def _norm(text: str) -> str:
    return " " + re.sub(r"[^a-z0-9$.\-' ]+", " ", text.lower()).replace("-", " ") + " "


def _plural_forms(word: str) -> list[str]:
    forms = [word, word + "s", word + "es"]
    if word.endswith("y"):
        forms.append(word[:-1] + "ies")
    return forms


def parse_product_request(text: str, vocabulary: dict[str, Any]) -> dict[str, Any]:
    """Turn a shopping request into search_products arguments, using the catalog vocabulary."""
    t = _norm(text)
    consumed = t
    tags: list[str] = []
    exclude: list[str] = []
    known_tags = {v["value"]: v["label"] for v in vocabulary.get("tags", [])}

    phrases: list[tuple[str, str]] = [(p, slug) for p, slug in TAG_SYNONYMS.items()]
    for slug, label in known_tags.items():
        phrases.append((label.lower().replace("-", " "), slug))
        phrases.append((slug.replace("-", " "), slug))
    # Longest phrases first, so "no added sugar" wins over "no sugar".
    for phrase, slug in sorted(set(phrases), key=lambda p: -len(p[0])):
        if slug not in known_tags:
            continue
        needle = f" {_norm(phrase).strip()} "
        idx = consumed.find(needle)
        if idx < 0:
            continue
        before = consumed[max(0, idx - 12) : idx + 1]
        negated = phrase not in TAG_SYNONYMS and any(before.endswith(n) for n in NEGATIONS)
        (exclude if negated else tags).append(slug)
        consumed = consumed.replace(needle, " ¦ ", 1)

    types: list[str] = []
    for value in sorted(
        (v["value"] for v in vocabulary.get("product_types", [])), key=len, reverse=True
    ):
        words = value.replace("-", " ")
        head, _, last = words.rpartition(" ")
        for form in _plural_forms(last):
            needle = f" {(head + ' ' if head else '')}{form} "
            if needle in consumed:
                types.append(value)
                consumed = consumed.replace(needle, " ¦ ", 1)
                break

    args: dict[str, Any] = {}
    if types:
        args["product_types"] = sorted(set(types))
    if tags:
        args["tags"] = sorted(set(tags))
    if exclude:
        args["exclude_tags"] = sorted(set(exclude) - set(tags))
    if m := PRICE.search(t):
        args["max_price_dollars"] = float(m.group(1))
    if re.search(r"\bcheapest\b|\blowest price\b", t):
        args["sort"] = "price_asc"
    if not types and not tags:
        rest = [w for w in re.findall(r"[a-z0-9']+", consumed) if w not in FILLER]
        args["query"] = " ".join(rest) or text.strip()
    return args


def read_payload(content: str) -> dict[str, Any]:
    m = re.search(r"<untrusted_data[^>]*>\s*(.*?)\s*</untrusted_data>", content, re.DOTALL)
    try:
        return dict(json.loads(m.group(1) if m else content))
    except (ValueError, TypeError):
        return {}


def _call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "args": args, "id": f"call_{uuid.uuid4().hex[:12]}", "type": "tool_call"}


def _last_product_cards(messages: Sequence[BaseMessage]) -> list[dict[str, Any]]:
    for m in reversed(messages):
        if isinstance(m, ToolMessage) and m.name in ("search_products", "get_product_details"):
            cards = [c for c in (m.artifact or []) if c.get("kind") == "product"]
            if cards:
                return cards
    return []


def plan(
    text: str,
    history: Sequence[BaseMessage],
    vocabulary: dict[str, Any],
    tools: set[str],
    signals: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    t = _norm(text)
    calls: list[dict[str, Any]] = []
    intent = (signals or {}).get("intent") or {}
    wants_person = intent.get("act") and intent.get("value") == "talk_to_person"
    if (wants_person or HANDOFF_WORDS.search(t)) and "handoff_to_person" in tools:
        return [_call("handoff_to_person", {"reason": text.strip()[:200]})]
    if ADD_WORDS.search(t) and "add_to_cart" in tools:
        cards = _last_product_cards(history)
        if cards:
            idx = next((i for w, i in ORDINALS.items() if f" {w} " in t), 0)
            card = cards[idx] if -len(cards) <= idx < len(cards) else cards[0]
            qty = 2 if " two " in t else 1
            if card.get("variant_id"):
                return [_call("add_to_cart", {"variant_id": card["variant_id"], "quantity": qty})]
    if (
        PRODUCT_DETAIL_WORDS.search(t)
        and not ORDER_WORDS.search(t)
        and not POLICY_WORDS.search(t)
        and "get_product_details" in tools
    ):
        cards = _last_product_cards(history)
        if cards:
            ordinal = next((i for w, i in ORDINALS.items() if f" {w} " in t), None)
            if len(cards) == 1 or ordinal is not None:
                card = cards[ordinal or 0]
                return [_call("get_product_details", {"product_id": card["id"]})]
    # "I want to return my earbuds" goes to Xena; "can I drop off a return at a store?" is a
    # policy question Steph answers herself.
    asks_question = bool(re.match(r"\s*(can|could|do|does|how|what|where|when|is|are|will)\b", t))
    if "suggest_xana" in tools and not asks_question and wants_return(text, signals or {}):
        return [_call("suggest_xana", {"about": text.strip()[:200]})]
    wants_store = bool(STORE_WORDS.search(t)) and not re.search(r"\bopen(ed)? (it|the|box)\b", t)
    wants_policy = bool(POLICY_WORDS.search(t))
    wants_orders = bool(ORDER_WORDS.search(t))
    if wants_policy and "search_policies" in tools:
        calls.append(_call("search_policies", {"question": text.strip()[:300]}))
    if wants_store and "list_stores" in tools:
        city = re.search(r"\b(?:in|at) (?:the )?([a-z]+(?: [a-z]+)?) store\b", t)
        calls.append(_call("list_stores", {"city": city.group(1)} if city else {}))
    number = named_order_number(text)
    if number and not wants_policy and "get_order_status" in tools:
        # A named order ("where's order E2EA6BC6?") is looked up by its number, not by listing.
        calls.append(_call("get_order_status", {"order_number": number}))
    elif wants_orders and "list_my_orders" in tools:
        item = re.search(r"\bwith (?:the|my) ([a-z ]+?)(?: in it)?\b", t)
        calls.append(_call("list_my_orders", {"contains": item.group(1).strip()} if item else {}))
    if calls:
        return calls
    if re.fullmatch(r"\s*(hi|hello|hey|thanks|thank you|ok|okay)[ !.]*", text.lower()):
        return []
    return (
        [_call("search_products", parse_product_request(text, vocabulary))]
        if "search_products" in tools
        else []
    )


def _describe_search(args: dict[str, Any], vocabulary: dict[str, Any]) -> str:
    labels = {v["value"]: v["label"].lower() for v in vocabulary.get("tags", [])}
    words = [labels.get(t, t) for t in args.get("tag", args.get("tags", []))]
    types = args.get("product_type", args.get("product_types", []))
    thing = " or ".join(t.replace("-", " ") for t in types) or args.get("q") or "products"
    return " ".join([*words, thing])


def _answer_product_detail(data: dict[str, Any], question: str) -> str:
    """The scripted fallback states only fields returned for this product."""
    title = str(data.get("title") or "This product")
    q = question.lower()
    if "ingredient" in q:
        ingredients = data.get("ingredients")
        return (
            f"{title} lists these ingredients: {ingredients}."
            if ingredients
            else f"The listing for {title} doesn't specify ingredients."
        )
    if re.search(r"\b(allerg|contain)\w*\b", q):
        allergens = data.get("allergens")
        if allergens is None:
            return f"The listing for {title} doesn't specify allergens. Check the package."
        listed = ", ".join(allergens) if allergens else "none"
        return (
            f"The listed major allergens for {title} are {listed}. "
            "The listing doesn't confirm whether cross-contact is possible; check the package "
            "or ask the manufacturer if you have an allergy."
        )
    if re.search(r"\b(nutrition|calori|protein)\w*\b", q):
        n = data.get("nutrition_per_serving")
        return (
            f"Per {n['serving_size']}, {title} has {n['calories']} calories, "
            f"{n['protein_g']:g} g protein, and {n['added_sugars_g']:g} g added sugar."
            if n
            else f"The listing for {title} doesn't provide nutrition facts."
        )
    if re.search(r"\b(price|cost|stock|available)\b", q):
        variants = data.get("variants") or []
        if len(variants) > 1:
            options = "; ".join(
                f"{v['name']}: {v['price']}" + (" in stock" if v["in_stock"] else " out of stock")
                for v in variants[:4]
            )
            return f"{title} has these options: {options}."
        return (
            f"{title} is {data.get('price')} and is "
            f"{'in stock' if data.get('in_stock') else 'out of stock'} right now."
        )
    specs = data.get("specs") or {}
    matched = [f"{k}: {v}" for k, v in specs.items() if k.lower() in q]
    if matched:
        return f"The listing for {title} says {'; '.join(matched[:3])}."
    return (
        f"The listing for {title} doesn't specify that. Check the product card for its "
        "published details."
    )


def compose(results: list[ToolMessage], vocabulary: dict[str, Any]) -> str:
    parts: list[str] = []
    for m in results:
        data = read_payload(str(m.content))
        if "error" in data:
            parts.append("Sorry, I couldn't get that information just now. Please try again.")
            continue
        if m.name == "search_products":
            if data.get("unsupported_filters"):
                parts.append(
                    "I can't verify that request with the catalog's available filters. "
                    "Please rephrase the product type or feature."
                )
                continue
            desc = _describe_search(data.get("filters_used", {}), vocabulary)
            items = data.get("results", [])
            if not items:
                parts.append(
                    f"I couldn't find an exact match for {desc}. Try fewer filters, or tell me "
                    "what matters most and I'll look again."
                )
            else:
                lines = "\n".join(
                    f"- {p['title']} ({p['brand']}), {p['price']}"
                    + ("" if p["in_stock"] else " (out of stock)")
                    for p in items[:3]
                )
                total = data.get("total_matches", len(items))
                parts.append(
                    f"I found {total} {'match' if total == 1 else 'matches'} for {desc}. "
                    f"Top picks:\n{lines}\nWant me to add one to your cart?"
                )
        elif m.name == "get_product_details":
            n = data.get("nutrition_per_serving")
            extra = (
                f" Per {n['serving_size']}: {n['calories']} calories, {n['protein_g']:g} g "
                f"protein, {n['added_sugars_g']:g} g added sugar."
                if n
                else ""
            )
            parts.append(
                f"{data.get('title')} by {data.get('brand')} is {data.get('price')}.{extra}"
            )
        elif m.name == "add_to_cart":
            parts.append(
                f"Added {data['added']} to your cart. It now has {data['cart_items']} items "
                f"({data['cart_subtotal']})."
            )
        elif m.name == "get_order_status" and "order_id" in data:
            parts.append(describe_order_status(data))
        elif m.name in ("list_my_orders", "get_order_status"):
            orders = data.get("orders") or ([data] if "order_id" in data else [])
            if not orders:
                parts.append("I couldn't find an order like that on your account.")
            for o in orders[:3]:
                items = ", ".join(f"{i['quantity']} × {i['title']}" for i in o["items"][:3])
                when = f", delivered {o['delivered_on']}" if o.get("delivered_on") else ""
                parts.append(
                    f"Order #{o['order_number']} ({o['status']}{when}), {o['total']}: {items}."
                )
        elif m.name == "list_stores":
            stores = data.get("stores", [])
            if len(stores) == 1 or len(stores) < 4:
                for s in stores[:2]:
                    state = "open now" if s["open_now"] else "closed right now"
                    drop = (
                        " It has a return drop-off." if "Return drop-off" in s["services"] else ""
                    )
                    parts.append(
                        f"{s['name']} at {s['address']} is {state} (today {s['today']}).{drop}"
                    )
            else:
                open_now = [s["name"] for s in stores if s["open_now"]]
                parts.append(
                    f"We have {len(stores)} stores around Dallas–Fort Worth; {len(open_now)} are "
                    "open now. The closest few are on the cards below."
                )
        elif m.name == "search_policies":
            sections = data.get("sections", [])
            if not sections:
                parts.append(
                    "I don't have an approved policy that answers that. "
                    "I can connect you with a person."
                )
                continue
            top = sections[0]
            text = re.sub(r"[*_`>#|]", "", top["text"])
            text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
            sentences = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
            parts.append(" ".join(sentences[:2]) + f" [[cite:{top['cite']}]]")
        elif m.name == "suggest_xana":
            parts.append(
                "I can't start returns myself, but Xena, our customer-support assistant, can: "
                "she'll find the order, show your exact refund, and start the return when you "
                "confirm."
            )
        elif m.name == "handoff_to_person":
            parts.append(
                "I can hand this to a person. Open Support to talk with Xena or ask for a member "
                "of our team; your conversation comes with you."
            )
    return "\n\n".join(parts) or "How can I help?"


class ScriptedChatModel(BaseChatModel):
    """Rules instead of a language model. Clearly labeled wherever it's used."""

    @property
    def _llm_type(self) -> str:
        return SCRIPTED_MODEL_NAME

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> Runnable[Any, Any]:
        names = [getattr(t, "name", str(t)) for t in tools]
        return self.bind(tool_names=names, **kwargs)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        vocabulary: dict[str, Any] = kwargs.get("vocabulary") or {}
        tools = set(kwargs.get("tool_names") or [])
        signals: dict[str, Any] = kwargs.get("signals") or {}
        agent = kwargs.get("agent") or "steph"
        last_human = max(
            (i for i, m in enumerate(messages) if isinstance(m, HumanMessage)), default=-1
        )
        results = [m for m in messages[last_human + 1 :] if isinstance(m, ToolMessage)]
        if results:
            text = str(messages[last_human].content) if last_human >= 0 else ""
            if agent == "xana":
                step = next_support_step(text, results, signals)
                if (
                    step is None
                    and results[-1].name == "search_products"
                    and PRODUCT_DETAIL_WORDS.search(text)
                ):
                    found = read_payload(str(results[-1].content)).get("results") or []
                    if len(found) == 1 and found[0].get("product_id"):
                        step = [
                            _call("get_product_details", {"product_id": found[0]["product_id"]})
                        ]
                if step and {c["name"] for c in step} <= tools:
                    return ChatResult(
                        generations=[ChatGeneration(message=AIMessage(content="", tool_calls=step))]
                    )
                answer = compose_support(results, text)
                latest = read_payload(str(results[-1].content))
                if (
                    answer is None
                    and results[-1].name == "get_product_details"
                    and "error" not in latest
                ):
                    answer = _answer_product_detail(latest, text)
                if (
                    answer is None
                    and results[-1].name == "search_products"
                    and PRODUCT_DETAIL_WORDS.search(text)
                    and len(latest.get("results") or []) > 1
                ):
                    answer = "I found several possible products. Which one do you mean?"
                message = AIMessage(
                    content=answer if answer is not None else compose(results, vocabulary)
                )
            else:
                message = AIMessage(content=compose(results, vocabulary))
        else:
            text = str(messages[last_human].content) if last_human >= 0 else ""
            if (signals.get("policy_bypass") or 0) >= 0.7:
                reply = AIMessage(content=BYPASS_REPLY)
                return ChatResult(generations=[ChatGeneration(message=reply)])
            cards = _last_product_cards(messages[:last_human])
            if (
                agent == "xana"
                and PRODUCT_DETAIL_WORDS.search(text)
                and len(cards) > 1
                and not any(f" {w} " in _norm(text) for w in ORDINALS)
                and not ORDER_WORDS.search(_norm(text))
                and not POLICY_WORDS.search(_norm(text))
            ):
                reply = AIMessage(
                    content="Which product do you mean? Please choose one of the cards."
                )
                return ChatResult(generations=[ChatGeneration(message=reply)])
            calls = (plan_support(text, signals) if agent == "xana" else None) or plan(
                text, messages[:last_human], vocabulary, tools, signals
            )
            message = (
                AIMessage(content="", tool_calls=calls)
                if calls
                else AIMessage(content=GREETINGS.get(agent, GREETINGS["steph"]))
            )
        return ChatResult(generations=[ChatGeneration(message=message)])
