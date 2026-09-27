"""A local stand-in for Jev, used when ``TYPESAFE_API_KEY`` isn't set. Clearly labeled.

Keyword rules that answer the same questions in the same shape, with made-up but honest
confidences: high only when a rule matches clearly. It's the baseline Jev is compared against
(``evals/jev_eval.py``), not a substitute for it.
"""

from __future__ import annotations

import re
from typing import Any

from assistant.jev.questions import FRUSTRATION_LEVELS, INTENTS, RETURN_REASONS, UNCLEAR
from assistant.jev.types import (
    Answer,
    Choice,
    ChoiceAnswer,
    JevResult,
    Noul,
    NoulAnswer,
    Question,
    Score,
    ScoreAnswer,
    Usage,
)

INTENT_RULES: list[tuple[str, str]] = [
    (
        "talk_to_person",
        r"\b(human|real person|a person|agent|representative|manager|someone real)\b",
    ),
    (
        "refund_status",
        r"\b(where('s| is) my refund|refund status|(haven't|have not|didn't) (got|gotten|received|get) (my|the|a) refund|did .* refund)\b",
    ),
    (
        "policy_question",
        r"\b(policy|policies|how long do i have|do i get .* back|shipping (cost|fee|charge|money)|free shipping|store credit|exchange|what does .* mean|restocking|drop ?off (my |a )?returns?|returns? at (a|the|any) .*store)\b",
    ),
    (
        "start_return",
        r"\b(return (my|the|it|this|these|those|them)|want to return|wanna return|need to return|send (it|this|them|the .+?) back|send back|refund|went bad|gone bad|spoiled|sour|broken|cracked|smashed|damaged|defective|(doesn't|don't|does not|do not) work|stopped working|wrong (item|size|color)|moldy|expired)\b",
    ),
    (
        "order_status",
        r"\b(my orders?|where('s| is) my|track|tracking|arrive|shipped|delivered|package)\b",
    ),
    ("store_info", r"\b(stores?|open now|hours|location|near me|directions)\b"),
    (
        "product_question",
        r"^\s*(is|does|do|are|can|how much|how many) (the|this|that|it|these|those)\b|\b(ingredients|allergens?|calories|contain)\b",
    ),
    (
        "product_search",
        r"\b(find|looking for|show me|need|want|buy|search|recommend)\b|\b(milk|yogurt|headphones|shoes|coffee|bread|cheese|snack)s?\b",
    ),
    ("other", r"^\s*(hi|hello|hey|thanks|thank you|ok|okay|bye)\b"),
]

REASON_RULES: list[tuple[str, str]] = [
    (
        "spoiled_or_expired",
        r"\b(spoiled|went bad|gone bad|moldy|mouldy|expired|sour|rotten|past (its|the) date|thawed|stale)\b",
    ),
    ("damaged", r"\b(broken|cracked|crushed|damaged|dented|shattered|leak(ed|ing)?|smashed)\b"),
    (
        "defective",
        r"\b((doesn't|don't|does not|do not) work|stopped working|won't (turn on|charge|pair)|defective|faulty|dead)\b",
    ),
    (
        "wrong_item",
        r"\b(wrong (item|size|color|colour|one|flavor)|not what i ordered|sent me the wrong|different item)\b",
    ),
    ("missing_parts", r"\b(missing|incomplete|not included)\b"),
    (
        "not_as_described",
        r"\b(not as described|doesn't match|different from the (picture|photo|listing))\b",
    ),
    ("better_price", r"\b(cheaper|better price|price (dropped|drop)|lower price)\b"),
    ("arrived_late", r"\b(too late|arrived late|came late|after the (party|event))\b"),
    (
        "no_longer_needed",
        r"\b(changed my mind|don't need|do not need|no longer need|don't want|didn't like|don't like|doesn't fit|too (small|big|large))\b",
    ),
]

PERSON = re.compile(
    r"\b(human|real person|talk to (a )?person|agent|representative|manager|someone real)\b"
)
BYPASS = re.compile(
    r"(ignore (all |your |the |previous |prior )*(rules|instructions|policy)|override|without (asking|confirm)|"
    r"just (refund|approve)|system:|you are now|pretend (you|to be)|skip the (check|confirmation))"
)
ANGRY = re.compile(
    r"\b(ridiculous|terrible|awful|angry|furious|unacceptable|worst|again|still|scam|!!)\b"
)
YES = re.compile(
    r"^\s*(yes|yeah|yep|yup|sure|correct|confirm|confirmed|do it|go ahead|please do|that's right)"
    r"([ ,.!]+(please|confirm( it| the return)?|go ahead|do it|thanks|thank you))*[ .!]*$"
)
HEDGE = re.compile(r"\b(but|maybe|i guess|not sure|wait|hold on|um+|uh+|mm+-?hmm|uh-huh|\?)\b|\?")


def _latest(state: Any) -> str:
    if isinstance(state, dict):
        if "answer" in state:
            return str(state["answer"])
        turns = state.get("conversation") or []
        for t in reversed(turns):
            if t.get("role") == "customer":
                return str(t.get("text", ""))
    return str(state)


def _choice(options: list[str], winner: str, confidence: float) -> ChoiceAnswer:
    rest = (1 - confidence) / max(len(options) - 1, 1)
    probs = {o: (confidence if o == winner else rest) for o in options}
    return ChoiceAnswer(choice=winner, probabilities=probs, confidence=confidence)


def _first_match(rules: list[tuple[str, str]], text: str) -> tuple[str | None, int]:
    hits = [label for label, pattern in rules if re.search(pattern, text)]
    return (hits[0] if hits else None), len(hits)


def _stem(word: str) -> str:
    return word[:-1] if word.endswith("s") and len(word) > 3 else word


def _target_line(text: str, options: dict[str, str | None]) -> ChoiceAnswer:
    words = {_stem(w) for w in re.findall(r"[a-z]{3,}", text)} - {
        "the",
        "and",
        "return",
        "want",
        "order",
        "item",
    }
    scores: dict[str, int] = {}
    for line_id, desc in options.items():
        if line_id == UNCLEAR or not desc:
            continue
        title = desc.lower().split(" in order ")[0]
        scores[line_id] = len(words & {_stem(w) for w in re.findall(r"[a-z]{3,}", title)})
    ids = list(options)
    best = max(scores.values(), default=0)
    winners = [k for k, v in scores.items() if v == best and v > 0]
    if len(winners) == 1:
        return _choice(ids, winners[0], 0.9 if best >= 2 else 0.82)
    return _choice(ids, UNCLEAR, 0.7)


class JevSimulator:
    simulated = True
    model = "jev-simulator"

    def ask(self, state: Any, questions: dict[str, Question]) -> JevResult:
        text = _latest(state).lower()
        answers: dict[str, Answer] = {}
        for key, q in questions.items():
            if key == "intent" and isinstance(q, Choice):
                label, n = _first_match(INTENT_RULES, text)
                answers[key] = _choice(
                    list(INTENTS),
                    label or "other",
                    0.9 if label and n == 1 else 0.72 if label else 0.4,
                )
            elif key == "return_reason" and isinstance(q, Choice):
                label, _ = _first_match(REASON_RULES, text)
                answers[key] = _choice(
                    list(RETURN_REASONS), label or "other", 0.85 if label else 0.5
                )
            elif key == "target_line" and isinstance(q, Choice):
                answers[key] = _target_line(text, q.criteria)
            elif key == "wants_person" and isinstance(q, Noul):
                answers[key] = NoulAnswer(noul=0.95 if PERSON.search(text) else 0.03)
            elif key == "policy_bypass" and isinstance(q, Noul):
                answers[key] = NoulAnswer(noul=0.92 if BYPASS.search(text) else 0.02)
            elif key == "frustration" and isinstance(q, Score):
                level = min(
                    len(ANGRY.findall(text)) + text.count("!") // 2, len(FRUSTRATION_LEVELS) - 1
                )
                answers[key] = ScoreAnswer(score=float(level), confidence=0.6)
            elif key == "voice_yes" and isinstance(q, Noul):
                clear = bool(YES.match(text)) and not HEDGE.search(text)
                answers[key] = NoulAnswer(noul=0.97 if clear else 0.04)
        return JevResult(model=self.model, answers=answers, usage=Usage(), simulated=True)
