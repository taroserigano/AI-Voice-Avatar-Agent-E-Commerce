"""From the model's streamed text to speakable chunks, as early as it's safe to speak them.

Latency: the speech engine starts talking when it has the first chunk, so the first chunk is
cut as soon as it's a complete clause (a comma, colon, or dash after a few words), and every
chunk after that at a sentence end. The engine keeps prosody across chunks (one context per
answer), so early cuts don't sound choppy.

Accuracy: citation markers (``[[cite:...]]``) are shown on screen, never read aloud; markdown
isn't spoken; emoji are dropped (the prompt forbids them, but an upbeat model slips one in
now and then, and the speech engine would read it out); order numbers are spelled out
character by character so "E2EA6BC6" isn't read as a word.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Any marker, well formed or not: "[[cite:shipping#...]]" (s-011, 2026-10-10) is never said.
CITE = re.compile(r"\[\[cite:[^\]]*\]\]")
# A marker that may still be arriving: hold it back until it closes.
_OPEN_CITE = re.compile(r"\[(\[(c(i(t(e(:[^\]]*)?)?)?)?)?)?$")
_MARKDOWN = re.compile(r"(\*\*|__|`|^#+\s*|^\s*[-*]\s+)", re.MULTILINE)
_ORDER_NUMBER = re.compile(r"\b(?=[A-Z0-9]{8}\b)(?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{8}\b")
_SENTENCE_END = re.compile(r"[.!?…](?:[\"'’”)\]]*)\s")
_CLAUSE_END = re.compile(r"[,;:—–](?:\s)")
# Pictographs, symbols, flags, and the joiners and variation selectors that build emoji.
_EMOJI = re.compile("[🀀-🫿☀-➿⬀-⯿️‍]")

FIRST_CHUNK_MIN_WORDS = 4
MAX_CHUNK_CHARS = 220


def spell_order_numbers(text: str) -> str:
    """Read order numbers one character at a time: 'E2EA6BC6' → 'E 2 E A 6 B C 6'."""
    return _ORDER_NUMBER.sub(lambda m: " ".join(m.group(0)), text)


def speakable(text: str) -> str:
    text = CITE.sub("", text)
    text = re.sub(r"(\d)\s*×\s*", r"\1 ", text)  # "1 × Notebook" -> "1 Notebook"
    text = _MARKDOWN.sub("", text)
    text = _EMOJI.sub("", text)
    text = spell_order_numbers(text)
    return re.sub(r"[ \t]+", " ", text).replace(" .", ".").replace(" ,", ",")


@dataclass
class SpeechChunker:
    """Feed model text deltas in; get speakable chunks out."""

    first_min_words: int = FIRST_CHUNK_MIN_WORDS
    buffer: str = ""
    emitted: int = 0
    spoken: list[str] = field(default_factory=list)

    def feed(self, delta: str) -> list[str]:
        self.buffer += delta
        out: list[str] = []
        while True:
            cut = self._cut_point()
            if cut is None:
                break
            chunk, self.buffer = self.buffer[:cut], self.buffer[cut:]
            if (said := self._emit(chunk)) is not None:
                out.append(said)
        return out

    def flush(self) -> list[str]:
        chunk, self.buffer = self.buffer, ""
        said = self._emit(chunk)
        return [said] if said is not None else []

    def _emit(self, chunk: str) -> str | None:
        said = speakable(chunk).strip()
        if not said or not re.search(r"\w", said):
            return None
        self.emitted += 1
        self.spoken.append(said)
        return said

    def _cut_point(self) -> int | None:
        text = self.buffer
        # Never cut inside a citation marker that's still arriving.
        safe = len(text)
        if m := _OPEN_CITE.search(text):
            safe = m.start()
        head = text[:safe]
        if m := _SENTENCE_END.search(head):
            return m.end()
        if self.emitted == 0:
            # The first clause boundary with enough words before it ("Sure, I can check that,"
            # cuts at the second comma, not after "Sure,").
            for m in _CLAUSE_END.finditer(head):
                if len(head[: m.start()].split()) >= self.first_min_words:
                    return m.end()
        if len(head) > MAX_CHUNK_CHARS:
            space = head.rfind(" ", 0, MAX_CHUNK_CHARS)
            return space + 1 if space > 0 else MAX_CHUNK_CHARS
        return None
