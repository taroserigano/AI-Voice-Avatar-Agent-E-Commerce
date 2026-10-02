"""Voice for Xena without LiveKit (yet): speech-to-text, text-to-speech, and the app-controlled
spoken confirmation.

Turn-based: the browser detects the end of the customer's speech, uploads that clip, and plays
the answer. Providers are chosen by which keys are set and each is labeled in ``/voice/config``:

- speech-to-text: Deepgram (``DEEPGRAM_API_KEY``) → Groq Whisper (``GROQ_API_KEY``) → the
  browser's own speech recognition (the page says so);
- text-to-speech: Cartesia ``sonic-3.6-2026-08-27`` (``CARTESIA_API_KEY``) → the browser's voice.

Audio is sent to the provider to be converted and is never stored; the transcript is saved with
the conversation (returns regulations §5.1).

A spoken "yes" confirms a return only if :func:`confirm_decision` says so: the read-back played
in full, the transcript is final and long enough, it's a clear unconditional yes by rule, and
(when Jev is on) Jev agrees. Jev can only block a confirmation, never make one.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Literal

import httpx

from assistant.config import Settings
from assistant.jev.client import JevError
from assistant.jev.decisions import voice_yes_passes
from assistant.jev.questions import voice_yes_question
from assistant.jev.signals import decision_model

log = logging.getLogger(__name__)

SttProvider = Literal["deepgram", "groq", "browser"]
TtsProvider = Literal["cartesia", "browser"]


class VoiceError(RuntimeError):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def stt_provider(settings: Settings) -> SttProvider:
    if settings.deepgram_api_key:
        return "deepgram"
    if settings.groq_api_key:
        return "groq"
    return "browser"


def tts_provider(settings: Settings) -> TtsProvider:
    return "cartesia" if settings.cartesia_api_key else "browser"


@dataclass(frozen=True)
class Transcript:
    text: str
    provider: SttProvider
    latency_ms: float


def transcribe(settings: Settings, audio: bytes, content_type: str) -> Transcript:
    provider = stt_provider(settings)
    started = time.perf_counter()
    if provider == "deepgram":
        resp = httpx.post(
            "https://api.deepgram.com/v1/listen",
            params={"model": "nova-3", "smart_format": "true", "language": "en"},
            headers={
                "Authorization": f"Token {settings.deepgram_api_key}",
                "Content-Type": content_type,
            },
            content=audio,
            timeout=20,
        )
        if resp.status_code != 200:
            raise VoiceError(502, f"speech-to-text answered {resp.status_code}")
        alt = resp.json()["results"]["channels"][0]["alternatives"][0]
        text = str(alt.get("transcript", ""))
    elif provider == "groq":
        ext = (
            "webm"
            if "webm" in content_type
            else "ogg"
            if "ogg" in content_type
            else "wav"
            if "wav" in content_type
            else "mp4"
        )
        resp = httpx.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            files={"file": (f"speech.{ext}", audio, content_type)},
            data={
                "model": settings.groq_stt_model,
                "response_format": "json",
                "language": "en",
                # Store vocabulary helps with product and brand names.
                "prompt": (
                    "Serigan Mart store support: returns, refunds, orders, headphones, earbuds."
                ),
            },
            timeout=20,
        )
        if resp.status_code != 200:
            raise VoiceError(502, f"speech-to-text answered {resp.status_code}")
        text = str(resp.json().get("text", ""))
    else:
        raise VoiceError(503, "No speech-to-text provider is configured; use the browser's.")
    return Transcript(
        text=text.strip(), provider=provider, latency_ms=(time.perf_counter() - started) * 1000
    )


def speak(settings: Settings, text: str, agent: str) -> bytes:
    if tts_provider(settings) != "cartesia":
        raise VoiceError(503, "No text-to-speech provider is configured; use the browser's.")
    voice_id = settings.xana_voice_id if agent == "xana" else settings.steph_voice_id
    resp = httpx.post(
        "https://api.cartesia.ai/tts/bytes",
        headers={"X-API-Key": settings.cartesia_api_key or "", "Cartesia-Version": "2025-04-16"},
        json={
            "model_id": settings.cartesia_model,
            "transcript": text,
            "voice": {"mode": "id", "id": voice_id},
            "output_format": {"container": "mp3", "sample_rate": 44100, "bit_rate": 128000},
            "language": "en",
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise VoiceError(502, f"text-to-speech answered {resp.status_code}")
    return resp.content


def speakable(text: str) -> str:
    """Answer text as it should be spoken: no citation markers, markdown, or list dashes."""
    text = re.sub(r"\[\[cite:[^\]]*\]\]", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`#>|]", "", text)
    text = re.sub(r"^\s*[-•]\s+", "", text, flags=re.MULTILINE)
    return re.sub(r"\s+", " ", text).strip()


# --- Spoken confirmation ------------------------------------------------------------------------

_YES = re.compile(
    r"^(yes|yeah|yep|yup|sure|correct|confirm|confirmed|do it|go ahead|please do|that's right)"
    r"([ ,.!]+(please|confirm( it| the return| my return)?|go ahead|do it|thanks|thank you|yes))*"
    r"[ .!]*$"
)
_NO = re.compile(r"^(no|nope|nah|cancel|don't|do not|stop|never mind|not now)\b")
_HEDGE = re.compile(
    r"\b(but|maybe|i guess|not sure|wait|hold on|um+|uh+|hmm+|mm+-?hmm|uh-huh|if)\b|\?"
)
MIN_SPEECH_MS = 250

Decision = Literal["yes", "no", "unclear"]


@dataclass(frozen=True)
class ConfirmDecision:
    decision: Decision
    reason: str
    rule_yes: bool
    jev_yes: float | None


def rule_decision(text: str) -> Decision:
    t = re.sub(r"\s+", " ", text.lower().strip())
    if not t or _HEDGE.search(t):
        return "unclear"
    if _NO.match(t):
        return "no"
    return "yes" if _YES.match(t) else "unclear"


def confirm_decision(
    text: str, *, final: bool, readback_complete: bool, speech_ms: int, use_jev: bool = True
) -> ConfirmDecision:
    """Whether a spoken answer to a read-back confirms, declines, or needs asking again."""
    if not readback_complete:
        return ConfirmDecision("unclear", "The read-back didn't finish playing.", False, None)
    if not final:
        return ConfirmDecision("unclear", "The transcript wasn't final.", False, None)
    if speech_ms < MIN_SPEECH_MS:
        return ConfirmDecision("unclear", "Too short to be sure.", False, None)
    by_rule = rule_decision(text)
    if by_rule != "yes":
        return ConfirmDecision(
            by_rule, "Not a clear yes." if by_rule == "unclear" else "Declined.", False, None
        )
    model = decision_model() if use_jev else None
    if model is None:
        return ConfirmDecision("yes", "Clear yes.", True, None)
    try:
        result = model.ask({"answer": text}, voice_yes_question())
    except JevError as exc:
        # No second vote available: fail closed and ask for the button instead.
        log.warning("Jev unavailable for a voice confirmation: %s", exc)
        return ConfirmDecision("unclear", "Couldn't double-check the answer.", True, None)
    answer = result.answers.get("voice_yes")
    p = getattr(answer, "noul", None)
    if not voice_yes_passes(result):
        return ConfirmDecision(
            "unclear", "The decision model wasn't sure it was a clear yes.", True, p
        )
    return ConfirmDecision("yes", "Clear yes.", True, p)
