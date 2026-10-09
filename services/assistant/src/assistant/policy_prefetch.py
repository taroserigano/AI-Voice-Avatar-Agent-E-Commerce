"""Search the policies before the model, for a customer message about policy.

Most policy questions are answered from one ``search_policies`` call. Making it before the
model, with the customer's own words, saves a whole model round (~1-1.7 s for voice's model,
~2 s for chat's) and costs a ~300 ms search. The result is recorded in the conversation as a
real ``search_policies`` call with the tool's own output format, so citations are checked as
usual and the model can still search again when the sections don't cover the question.
"""

from __future__ import annotations

import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from langchain_core.messages import AIMessage, AnyMessage, ToolMessage

from assistant.commerce import CommerceClient
from assistant.tools import citation_card, policy_search, untrusted

PREFETCH_TIMEOUT_S = 1.2
PREFETCH_SECTIONS = 6
# Words that mean the answer likely rests on a policy (not "where's my order?").
POLICY_WORDS = re.compile(
    r"\b(polic(y|ies)|returns?|returned|returning|refunds?|refunded|exchanges?|warrant(y|ies)|"
    r"opened|damaged|broken|defective|restocking|final sale|cancel\w*|perishables?|spoiled|"
    r"inspect\w*|labels?|drop.?offs?|eligib\w*|window|price match|gift cards?|"
    r"(?:sales )?tax(?:es|ed)?|warrant\w*|free shipping|shipping (?:cost|fee|charge)s?|"
    r"send (?:it |them |this |that )?back|money back|take (?:it |them )?back|exchange|"
    r"doesn'?t work|stopped working|not working|reasons?|lost|stolen|late|delay\w*|approve\w*|"
    r"swap|wrong (?:item|size|color|one)|hasn'?t (?:arrived|moved|changed|updated|come)|"
    # How the site works (the help center) and shipping rules (customer-support probe,
    # 2026-10-08: "do you ship to Canada?", "how do I reset my password?" went unanswered).
    r"disputes?|chargebacks?|charged (?:twice|double|wrong\w*|more)|double.?charged|billing|"
    r"payment methods?|pay(?:pal| with| by)|apple pay|google pay|credit cards?|debit cards?|"
    r"check ?out|promo(?: codes?)?|coupons?|discount codes?|rewards?|loyalty|points|"
    r"passwords?|log ?in|sign(?:ed)? ?(?:in|up|out)|accounts?|e-?mail address|my e-?mail|"
    r"wish ?lists?|favorites|save for later|receipts?|invoices?|"
    r"(?:write|leave|post|edit|delete) (?:a |my )?reviews?|"
    r"(?:change|modify|edit|update) (?:my |the )?(?:order|address|delivery)|"
    r"internationa\w*|ship (?:to|outside)|deliver (?:to|outside)|countr(?:y|ies)|canada|mexico|"
    r"fulfilling|preparing|phone number|contact|customer service|"
    r"manuals?|cables|accessories|packaging|(?:original|the|without a) box|tags|different card|"
    r"pick ?up|in.?store|"
    r"never (?:came|arrived|got here|showed up)|didn'?t (?:come|arrive|get here)|missing|"
    r"call (?:you|someone|customer)|hours|place (?:an |the |my )?order|order (?:it|this) for me)\b",
    re.IGNORECASE,
)


# "What does keto friendly mean?": label meanings are in the product labels policy.
LABEL_QUESTION = re.compile(
    r"\b(?:mean|means|meaning|difference between|same as|counts? as|definition of|defined)\b",
    re.IGNORECASE,
)


def wants_policy(text: str) -> bool:
    return bool(
        POLICY_WORDS.search(text)
        or _ABROAD.search(text)
        or _FAIR_USE.search(text)
        or _DISPUTE.search(text)
        or LABEL_QUESTION.search(text)
        or (_FOOD.search(text) and _SPOILED.search(text))
    )


# Conversational words that match the wrong sections ("What's *your* return *policy*..." ranks
# "Your privacy" first) and dilute meaning search. Measured on the real policies: dropping them
# put "Standard items" and "Electronics" in the top six for opened headphones, and the three
# refund-timing sections in the top three for "how long do refunds take".
_FILLER = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "about",
        "any",
        "anything",
        "as",
        "at",
        "be",
        "been",
        "but",
        "by",
        "can",
        "could",
        "did",
        "do",
        "does",
        "doing",
        "for",
        "from",
        "get",
        "go",
        "going",
        "got",
        "had",
        "has",
        "have",
        "hey",
        "hi",
        "hello",
        "how",
        "i",
        "if",
        "in",
        "is",
        "it",
        "its",
        "it's",
        "just",
        "know",
        "let",
        "like",
        "me",
        "my",
        "of",
        "on",
        "or",
        "our",
        "please",
        "policy",
        "policies",
        "say",
        "should",
        "so",
        "tell",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "they",
        "this",
        "to",
        "us",
        "wanna",
        "want",
        "was",
        "we",
        "what",
        "what's",
        "whats",
        "when",
        "where",
        "which",
        "who",
        "why",
        "will",
        "with",
        "would",
        "xana",
        "you",
        "your",
        "you're",
        "yours",
        "ok",
        "okay",
        "um",
        "uh",
        "also",
        "again",
        "still",
        "really",
        "thanks",
        "thank",
    ]
)
_TIMING = re.compile(
    r"\b(how long|how soon|how many days|when will|when do|when does|when would)\b", re.I
)

# "How do you calculate my refund?" matched the regulations and missed "How much you get back"
# (section 7); these words rank all of section 7 first. Only refund-amount questions: "how
# much is shipping?" is about shipping.
_AMOUNT = re.compile(
    r"\b(calculat\w*|(?:refund|return) amount|how much (?:money )?(?:do|will|would|can) (?:i|we)"
    r" get(?: back)?|how much (?:is|will be|would be) (?:my|the) refund)\b",
    re.I,
)


# "It's defective and it's been two months": past the window, the answer is the manufacturer's
# warranty (section 12.2), which words like "defective" alone don't find.
_FAULT = re.compile(
    r"\b(?:defective|broken|broke|stopped working|doesn'?t work|won'?t (?:turn on|work|charge)|"
    r"faulty|died)\b",
    re.I,
)
_LONG_AGO = re.compile(r"\b(?:months?|years?|\d+ weeks|several weeks|a while)\b", re.I)
# Food that went bad: "the whole milk was bad" ranked discount splitting first and "my eggs were
# cracked" the label glossary; the perishable rule (section 2.2) wasn't retrieved and the voice
# answer cited it from memory (golden eval, 2026-10-03).
_FOOD = re.compile(
    r"\b(?:milk|cheese|cheddar|yogh?urt|eggs?|meat|chicken|beef|pork|fish|salmon|seafood|produce|"
    r"fruit|berries|vegetables?|lettuce|bread|bakery|frozen|ice cream|groceries|grocery|food|"
    r"pizzas?|waffles|dairy|deli|sushi|steaks?|shrimp|produce)\b",
    re.I,
)
_SPOILED = re.compile(
    r"\b(?:bad|went off|spoiled|spoilt|sour|soured|expired|moldy|mouldy|rotten|stale|cracked|"
    r"thawed|melted|leaking|leaked|smelled|smells|past (?:its|the) date)\b",
    re.I,
)


# Food they don't want any more: "I don't like the pizza, can I return it?" retrieved condition
# and label sections, and voice cited section 2.1 from memory (support set, round 9, 2026-10-08).
_CHANGED_MIND = re.compile(
    r"\b(?:don'?t (?:like|want|need)|didn'?t (?:like|want)|chang\w* (?:my |of )?mind|"
    r"not hungry|tastes? (?:bad|weird|gross)|ordered too much|too many)\b",
    re.IGNORECASE,
)


# Somewhere we don't ship: "I live in Japan, can I order?" retrieved checkout and answered
# "checkout is off", not "we ship to the US only" (support set, 2026-10-08).
_ABROAD = re.compile(
    r"\b(?:abroad|overseas|internationa\w*|"
    r"outside (?:the )?(?:US|U\.S\.|USA|United States|country)|"
    r"canada|mexico|uk|united kingdom|england|britain|ireland|france|germany|spain|italy|"
    r"netherlands|europe|australia|new zealand|japan|china|korea|india|philippines|brazil|"
    r"argentina|colombia|puerto rico|toronto|vancouver|london|paris|tokyo|sydney)\b",
    re.IGNORECASE,
)
# "Will I get banned for returning too much?" missed fair use (section 15).
_FAIR_USE = re.compile(
    r"\b(?:bann?ed|ban me|blacklist\w*|blocked|too many returns|"
    r"return(?:ing)? too (?:much|many|often)|"
    r"how many returns|limit on returns|abus\w*)\b",
    re.IGNORECASE,
)


# "What if you say my return was damaged by me?" retrieved the condition rules, not what happens
# when an item fails inspection or how to disagree (sections 11.3 and 16.2; support set,
# 2026-10-08).
_DISPUTE = re.compile(
    r"\b(?:disagree\w*|don'?t agree|not fair|unfair|appeal|"
    r"(?:say|says|said|claim\w*|decide\w*) (?:that )?(?:i|my \w+|it was|it's) "
    r"\w*\s?(?:damag\w*|broke\w*)|"
    r"damaged (?:it )?(?:by me|myself)|i damaged|fail(?:s|ed)? (?:the )?inspection)\b",
    re.IGNORECASE,
)


def retrieval_query(text: str) -> str:
    """The customer's words as a search query: timing questions say "timing", refund-amount
    questions say what section 7 says, an old fault asks about the warranty, filler goes."""
    said = _AMOUNT.sub(" much back paid ", _TIMING.sub(" timing ", text.lower()))
    if _FAULT.search(said) and _LONG_AGO.search(said):
        said += " warranty manufacturer after the return window"
    if _ABROAD.search(said):
        said += " where we ship addresses in the united states only international"
    if _FAIR_USE.search(said):
        said += " fair use decline returns that look like abuse high rate of returns"
    if _DISPUTE.search(said):
        said += " inspection outcomes failed not refunded ship it back review"
        said += " disagreeing with a decision"
    if _FOOD.search(said) and _SPOILED.search(said):
        said += " perishable fresh frozen food spoiled damaged within 7 days of delivery"
    elif _FOOD.search(said) and _CHANGED_MIND.search(said):
        said += " perishable change of mind fresh frozen food quality problem"
    words = re.findall(r"[a-z0-9]+(?:'[a-z]+)?", said)
    kept = [w for w in words if w not in _FILLER]
    return " ".join(dict.fromkeys(kept)) or text.strip()


def policy_tool_output(result: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    """``search_policies``' own content and citation cards, for a search made outside it."""
    payload = {
        "sections": [
            {
                "cite": r["cite"],
                "title": f"{r['doc_title']} §{r['number']} {r['title']}".strip(),
                "version": r["version"],
                "text": r["body"],
            }
            for r in result["results"]
        ]
    }
    cards = [citation_card(r).model_dump() for r in result["results"]]
    return untrusted("search_policies", payload), cards


def prefetched_messages(
    question: str, result: dict[str, Any], mid: str | None = None
) -> list[AnyMessage]:
    """A policy search made outside the tool, as the ``search_policies`` call and its result.
    Fixed ids from ``mid`` let a restarted turn replace its draft messages."""
    mid = mid or str(uuid.uuid4())
    content, cards = policy_tool_output(result)
    call = {
        "name": "search_policies",
        "args": {"question": question},
        "id": f"prefetch-{mid}",
        "type": "tool_call",
    }
    return [
        AIMessage(content="", tool_calls=[call], id=f"{mid}-policy-call"),
        ToolMessage(
            content=content,
            artifact=cards,
            name="search_policies",
            tool_call_id=call["id"],
            id=f"{mid}-policies",
        ),
    ]


_POOL = ThreadPoolExecutor(max_workers=8, thread_name_prefix="policy-prefetch")


def start_policy_search(client: CommerceClient, text: str) -> tuple[str, Any] | None:
    """Start the search for a policy question in the background: (query, future), or None
    when the message isn't about policy."""
    if not wants_policy(text):
        return None
    question = retrieval_query(text)[:300]
    return question, _POOL.submit(policy_search, client, question, PREFETCH_SECTIONS)
