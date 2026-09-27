from __future__ import annotations

import random

from ai_commerce_voice.fillers import BY_TOOL, GENERIC, FillerPicker, all_phrases
from ai_commerce_voice.speech_text import SpeechChunker, speakable, spell_order_numbers


def chunks_of(deltas: list[str]) -> list[str]:
    c = SpeechChunker()
    out: list[str] = []
    for d in deltas:
        out += c.feed(d)
    return out + c.flush()


def test_the_first_clause_is_spoken_before_the_sentence_ends() -> None:
    out = chunks_of(["Your order E2EA6BC6 shipped", " yesterday, and it", " arrives Friday."])
    assert out[0] == "Your order E 2 E A 6 B C 6 shipped yesterday,"
    assert out[1] == "and it arrives Friday."


def test_a_short_opening_isnt_cut_at_its_comma() -> None:
    # "Sure," alone would sound clipped; wait for a real clause.
    assert chunks_of(["Sure, I can", " help with that. What's", " the order?"]) == [
        "Sure, I can help with that.",
        "What's the order?",
    ]


def test_later_chunks_cut_at_sentence_ends_only() -> None:
    out = chunks_of(
        ["It's eligible for a refund. ", "You'll get it back, to your card, in five days."]
    )
    assert out == ["It's eligible for a refund.", "You'll get it back, to your card, in five days."]


def test_citation_markers_are_never_spoken_even_split_across_deltas() -> None:
    out = chunks_of(
        [
            "Returns are free within 30 days. [[ci",
            "te:returns-and-refunds#rr-2",
            "-1]] Anything else?",
        ]
    )
    assert out == ["Returns are free within 30 days.", "Anything else?"]
    assert all("cite" not in c and "[" not in c for c in out)


def test_markdown_isnt_read_aloud() -> None:
    assert speakable("**Refund:** $12.63") == "Refund: $12.63"


def test_order_numbers_are_spelled_but_words_and_money_are_not() -> None:
    assert spell_order_numbers("Order E2EA6BC6 for $12.63") == "Order E 2 E A 6 B C 6 for $12.63"
    assert spell_order_numbers("DELIVERED ABCDEFGH 12345678") == "DELIVERED ABCDEFGH 12345678"


def test_a_long_run_on_is_cut_at_a_space() -> None:
    out = chunks_of(["word " * 80])
    assert len(out) >= 2 and all(len(c) <= 220 for c in out)


def test_fillers_are_random_but_never_repeat_back_to_back() -> None:
    picker = FillerPicker(rng=random.Random(7))
    picks = [picker.pick() for _ in range(40)]
    assert all(a != b for a, b in zip(picks, picks[1:], strict=False))
    assert set(picks) <= set(GENERIC) and len(set(picks)) > 3


def test_tool_fillers_say_what_xana_is_doing() -> None:
    picker = FillerPicker(rng=random.Random(1))
    assert picker.pick("get_order_status") in BY_TOOL["get_order_status"]
    assert picker.pick("not_a_tool") in GENERIC
    assert len(all_phrases()) == len(set(all_phrases()))
