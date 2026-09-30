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
    r"inspect\w*|labels?|drop.?offs?|eligib\w*|window|price match|gift cards?)\b",
    re.IGNORECASE,
)


# "What does keto friendly mean?": label meanings are in the product labels policy.
LABEL_QUESTION = re.compile(
    r"\b(?:mean|means|meaning|difference between|same as|counts? as|definition of|defined)\b",
    re.IGNORECASE,
)


def wants_policy(text: str) -> bool:
    return bool(POLICY_WORDS.search(text) or LABEL_QUESTION.search(text))


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


def retrieval_query(text: str) -> str:
    """The customer's words as a search query: timing questions say "timing", refund-amount
    questions say what section 7 says, filler goes."""
    said = _AMOUNT.sub(" much back paid ", _TIMING.sub(" timing ", text.lower()))
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
