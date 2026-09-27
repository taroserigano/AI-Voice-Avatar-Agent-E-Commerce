"""Hearing when the customer starts and stops talking, on the server, frame by frame.

An energy detector with an adaptive noise floor: fast and deterministic, and the browser has
already removed echo and steady noise (echoCancellation / noiseSuppression). Speech starts
after ``start_ms`` of frames above the floor; it ends after a stretch of quiet whose length
depends on what was said so far. A turn that ends in "?" or a full stop ends sooner
(``quick_end_ms``) than one trailing off mid-sentence ("my order from, um…"), which waits for
``end_ms``. That's cheap semantic endpointing: fast on complete questions, patient otherwise.

While Xana is talking the start threshold rises (``talking=True``): what's left of her own
voice after echo cancellation shouldn't count as the customer.
"""

from __future__ import annotations

import math
import re
from array import array
from dataclasses import dataclass, field
from typing import Literal

FRAME_MS = 20
_COMPLETE = re.compile(r"[.?!]\s*$")

VadEvent = Literal["start", "end"] | None


def rms(pcm16: bytes) -> float:
    samples = array("h")
    samples.frombytes(pcm16[: len(pcm16) - len(pcm16) % 2])
    if not samples:
        return 0.0
    return math.sqrt(sum(s * s for s in samples) / len(samples)) / 32768.0


@dataclass
class Vad:
    start_ms: int = 100
    end_ms: int = 650
    quick_end_ms: int = 360
    min_speech_ms: int = 160
    floor: float = 0.004
    ratio: float = 3.2  # speech is this many times the noise floor
    min_level: float = 0.012
    talking_level: float = 0.03
    pre_roll_ms: int = 300

    speaking: bool = False
    loud_ms: int = 0
    quiet_ms: int = 0
    speech_ms: int = 0
    pre_roll: list[bytes] = field(default_factory=list)

    def threshold(self, talking: bool) -> float:
        base = max(self.min_level, self.floor * self.ratio)
        return max(base, self.talking_level) if talking else base

    def feed(self, frame: bytes, *, transcript: str = "", talking: bool = False) -> VadEvent:
        level = rms(frame)
        loud = level >= self.threshold(talking)
        if not self.speaking:
            # Track the room's noise floor only while nobody is talking.
            if not loud:
                self.floor = 0.95 * self.floor + 0.05 * max(level, 0.0005)
            self.pre_roll.append(frame)
            if len(self.pre_roll) > self.pre_roll_ms // FRAME_MS:
                self.pre_roll.pop(0)
            self.loud_ms = self.loud_ms + FRAME_MS if loud else 0
            if self.loud_ms >= self.start_ms:
                self.speaking = True
                self.quiet_ms = 0
                self.speech_ms = self.loud_ms
                return "start"
            return None

        self.speech_ms += FRAME_MS
        self.quiet_ms = 0 if loud else self.quiet_ms + FRAME_MS
        wait = self.quick_end_ms if _COMPLETE.search(transcript) else self.end_ms
        if self.quiet_ms >= wait:
            self.speaking = False
            self.loud_ms = 0
            self.pre_roll.clear()
            return "end"
        return None

    def take_pre_roll(self) -> bytes:
        audio = b"".join(self.pre_roll)
        self.pre_roll.clear()
        return audio

    @property
    def spoken_ms(self) -> int:
        """Speech in the turn that just ended, without its trailing quiet."""
        return max(0, self.speech_ms - self.quiet_ms)
