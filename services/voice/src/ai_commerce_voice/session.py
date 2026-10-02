"""One live voice conversation: hearing, thinking, and speaking at the same time.

Everything is streamed and overlapped, which is where the speed comes from:

- the microphone streams to speech-to-text the whole time, and the server's voice activity
  detection hears the end of the customer's turn (no clip upload, no browser-side guessing);
- the model's answer streams into the speech engine clause by clause, and the audio streams
  to the browser as it's generated, so Xena starts talking while she's still "writing";
- if no answer audio is ready ``filler_after_ms`` after the customer stops, or a tool call
  starts before Xena has said anything, she says a short pre-recorded filler ("Let me
  check that order.") so there's never dead air;
- if the customer talks over her, she stops at once (the browser drops queued audio) and
  listens.

Captions: each spoken segment's text and word timings go to the browser, which shows words as
the audio reaches them (see apps/web/lib/voice-captions.ts).

Returns: when the agent proposes a quote, the read-back (built by code from the quote, never
the model) is spoken as its own segment. A spoken reply is judged by ``confirm`` (the app's
strict rule, with the read-back required to have played in full); only a clear yes lets the
browser confirm with the store. The model can't confirm anything.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import re
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from ai_commerce_voice.fillers import FillerPicker
from ai_commerce_voice.ports import (
    AgentEvent,
    Audio,
    Brain,
    CardOut,
    ConfirmRule,
    Draft,
    Ears,
    Final,
    Mouth,
    Partial,
    QuoteOut,
    SpeechDone,
    SpeechFailed,
    SpeechStarted,
    SpeechStopped,
    SttFailed,
    TextDelta,
    ToolStarted,
    TurnEnded,
    Utterance,
    Words,
)
from ai_commerce_voice.speech_text import SpeechChunker, speakable

log = logging.getLogger(__name__)

SendJson = Callable[[dict[str, Any]], Awaitable[None]]
SendBytes = Callable[[bytes], Awaitable[None]]

FRAME_BYTES = 4800  # 100 ms of PCM16 at 24 kHz per WebSocket frame for pre-rendered audio
BARGE_IN_MS = 250  # speech this long while Xena talks stops her; shorter is a cough or a blip
MIN_WORDS_TO_MOVE_ON = 5  # an "unclear" reply this long to a quote is a new request instead

CONFIRM_SAY = {
    "yes": "Thanks, confirming your return now.",
    "no": "Okay, I won't return it. Nothing has changed.",
    "unclear": "Sorry, I need a clear yes to confirm. Say yes, confirm, or tap Confirm return.",
}

_NOISE = re.compile(r"^\W*(uh+|um+|hmm+|mm+|ah+|oh+)?\W*$", re.IGNORECASE)


def same_words(a: str, b: str) -> bool:
    def norm(t: str) -> str:
        return " ".join(re.sub(r"[^\w\s]", " ", t.lower()).split())

    return norm(a) == norm(b)


@dataclass
class FillerClip:
    text: str
    pcm16: bytes
    words: list[dict[str, Any]]


@dataclass
class Segment:
    number: int
    kind: Literal["filler", "answer", "confirm"]
    text: str = ""
    sent_audio: bool = False
    complete: bool = False
    heard_complete: bool = False
    dropped: bool = False
    generation: int = 0
    synthesized: bool = False


@dataclass
class TurnClock:
    stopped_at: float | None = None
    final_at: float | None = None
    first_token_ms: float | None = None
    first_audio_at: float | None = None
    filler: bool = False

    def metrics(self) -> dict[str, Any]:
        base = self.stopped_at or self.final_at
        out: dict[str, Any] = {"filler": self.filler}
        if base is not None and self.final_at is not None and self.stopped_at is not None:
            out["stt_ms"] = round((self.final_at - self.stopped_at) * 1000, 1)
        if base is not None and self.first_audio_at is not None:
            out["first_audio_ms"] = round((self.first_audio_at - base) * 1000, 1)
        if self.first_token_ms is not None:
            out["llm_first_token_ms"] = round(self.first_token_ms, 1)
        return out


@dataclass
class VoiceSession:
    send_json: SendJson
    send_bytes: SendBytes
    ears: Ears
    mouth: Mouth
    brain: Brain
    confirm: ConfirmRule
    fillers: dict[str, FillerClip]
    filler_after_ms: int = 900
    max_turn_s: float = 45.0
    picker: FillerPicker = field(default_factory=FillerPicker)
    clock: Callable[[], float] = time.monotonic

    state: str = "connecting"
    quote: dict[str, Any] | None = None
    segments: dict[int, Segment] = field(default_factory=dict)
    _next_segment: int = 0
    _turn: asyncio.Task[None] | None = None
    _audio_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _speech_started_at: float | None = None
    _stopped_at: float | None = None
    _barge_timer: asyncio.Task[None] | None = None
    _readback_segment: int | None = None
    _answer_audio_started: bool = False
    _filler_played: bool = False
    _hearing_task: asyncio.Task[None] | None = None
    # The turn started early on the live transcript: (item_id, text).
    _draft: tuple[str, str] | None = None
    # The running turn only says a fixed line ("Thanks, confirming your return now.").
    _turn_is_say: bool = False
    muted: bool = False
    output_generation: int = 0
    spoken_confirmation: bool = True
    output_switching: bool = False

    # --- lifecycle -----------------------------------------------------------------------

    async def start(self) -> None:
        self._hearing_task = asyncio.create_task(self._hear())
        await self._set_state("listening")

    async def close(self) -> None:
        for task in (self._turn, self._barge_timer, self._hearing_task):
            if task and not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await task

    # --- from the browser ----------------------------------------------------------------

    async def on_audio(self, pcm16: bytes) -> None:
        if not self.muted and not self.output_switching:
            await self.ears.send_audio(pcm16)

    async def on_message(self, msg: dict[str, Any]) -> None:
        kind = msg.get("type")
        if kind == "played":
            seg = self.segments.get(int(msg.get("segment", -1)))
            if (
                seg
                and not seg.dropped
                and seg.synthesized
                and msg.get("complete")
                and seg.generation == self.output_generation
                and msg.get("generation", 0) == seg.generation
            ):
                seg.complete = True
                seg.heard_complete = self.spoken_confirmation
                await self._maybe_idle()
        elif kind == "interrupt":
            await self._barge_in()
        elif kind == "mute":
            self.muted = bool(msg.get("muted"))
            if self.muted:
                # Close any speech the detector thinks is still going on.
                await self.ears.send_audio(b"\x00\x00" * 24_000)
        elif kind == "text":
            text = str(msg.get("text") or "").strip()[:500]
            if text:
                now = self.clock()
                await self._on_final(Final(text=text, at=now, speech_ms=1000.0), typed=True)
        elif kind == "quote.outcome":
            outcome = msg.get("outcome")
            if self.quote and msg.get("quote_id") == self.quote.get("quote_id"):
                self.quote = None
                self._readback_segment = None
                await self._start_turn(resume="confirmed" if outcome == "confirmed" else "declined")

    # --- hearing -------------------------------------------------------------------------

    async def switch_output(self, provider: str, generation: int) -> None:
        self.output_switching = True
        await self._barge_in()
        self.output_generation = generation
        self.output_switching = provider != "local"
        # LiveAvatar playout timing needs a connected acceptance test. Its return flow
        # deliberately uses the existing explicit confirmation button in the meantime.
        self.spoken_confirmation = provider != "heygen"
        self._readback_segment = None
        self._draft = None

    async def output_ready(self, generation: int) -> None:
        if generation == self.output_generation:
            self.output_switching = False
            await self._maybe_idle()

    async def _hear(self) -> None:
        async for ev in self.ears.events():
            if isinstance(ev, SpeechStarted):
                self._speech_started_at = ev.at
                if self._talking():
                    self._barge_timer = asyncio.create_task(self._barge_after(BARGE_IN_MS))
                elif self.state != "thinking":
                    await self._set_state("hearing")
            elif isinstance(ev, SpeechStopped):
                self._stopped_at = ev.at
                if self._barge_timer and not self._barge_timer.done():
                    self._barge_timer.cancel()  # a blip, not a barge-in
                if self.state == "hearing":
                    await self._set_state("thinking")
            elif isinstance(ev, Partial):
                if ev.text.strip():
                    await self.send_json({"type": "user.partial", "text": ev.text})
            elif isinstance(ev, Draft):
                await self._on_draft(ev)
            elif isinstance(ev, Final):
                await self._on_final(ev)
            elif isinstance(ev, SttFailed):
                await self.send_json(
                    {"type": "error", "message": "I lost your audio for a moment."}
                )

    async def _barge_after(self, ms: int) -> None:
        await asyncio.sleep(ms / 1000)
        await self._barge_in()

    async def _barge_in(self) -> None:
        live = [s.number for s in self.segments.values() if not s.complete]
        if self._turn and not self._turn.done():
            self._turn.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._turn
        if live:
            for n in live:
                self.segments[n].complete = True
                self.segments[n].dropped = True
                self.segments[n].heard_complete = False
            await self.send_json({"type": "drop", "segments": live})
        await self._set_state("hearing")

    async def _on_draft(self, ev: Draft) -> None:
        """Start thinking on the live transcript while the final one is on its way. A reply
        to a quote waits for the final transcript: a confirmation is judged on final words."""
        if self.output_switching:
            return
        text = ev.text.strip()
        if self.quote is not None or not text or _NOISE.match(text):
            return
        self._draft = (ev.item_id, text)
        await self.send_json({"type": "user.final", "text": text})
        # When the words were ready (not when speech stopped): stt_ms is the transcriber's lag.
        clock = TurnClock(stopped_at=self._stopped_at, final_at=self.clock())
        await self._start_turn(text=text, message_id=ev.item_id, clock=clock)

    async def _on_final(self, ev: Final, *, typed: bool = False) -> None:
        if self.output_switching:
            return
        text = ev.text.strip()
        draft, self._draft = self._draft, None
        if draft is not None and ev.item_id == draft[0]:
            if same_words(draft[1], text) or not text:
                if text and text != draft[1]:
                    await self.send_json({"type": "user.final", "text": text})
                return
            if self._answer_audio_started:
                log.info("final transcript differs after audio started; keeping the answer")
                return
            # The words changed: think again on what was actually said (same message id, so
            # the draft is replaced in the conversation, not added to it).
            await self.send_json({"type": "user.final", "text": text})
            clock = TurnClock(stopped_at=self._stopped_at, final_at=ev.at)
            await self._start_turn(text=text, message_id=draft[0], clock=clock)
            return
        if not text or _NOISE.match(text):
            if self.state in ("hearing", "thinking") and not self._busy():
                await self._set_state("listening")
            return
        await self.send_json({"type": "user.final", "text": text})
        clock = TurnClock(stopped_at=None if typed else self._stopped_at, final_at=ev.at)
        speech_ms = ev.speech_ms or (
            (self._stopped_at - self._speech_started_at) * 1000
            if self._stopped_at and self._speech_started_at
            else 0.0
        )

        if self.quote is not None:
            generation = self.output_generation
            quote_id = self.quote["quote_id"]
            readback_done = (
                self._readback_segment is not None
                and self.spoken_confirmation
                and self.segments.get(self._readback_segment, Segment(0, "confirm")).heard_complete
            )
            # The app's rule (and Jev's veto, a network call) off the event loop.
            decision = await asyncio.to_thread(
                self.confirm, text, final=True, readback_complete=readback_done, speech_ms=speech_ms
            )
            if (
                generation != self.output_generation
                or self.quote is None
                or self.quote["quote_id"] != quote_id
            ):
                return
            if decision == "unclear" and len(text.split()) >= MIN_WORDS_TO_MOVE_ON:
                # They've moved on: close the quote quietly, then answer the new request.
                self.quote = None
                self._readback_segment = None
                await self._start_turn(resume="superseded", then=text, clock=clock)
                return
            await self.send_json(
                {
                    "type": "confirm.result",
                    "decision": decision,
                    "quote_id": self.quote["quote_id"],
                    **({"generation": generation} if generation else {}),
                }
            )
            line = CONFIRM_SAY[decision]
            if decision == "unclear" and not readback_done:
                line = "Please review the return details on screen and tap Confirm return."
            await self._start_turn(say=line, clock=clock)
            return

        await self._start_turn(text=text, clock=clock)

    # --- a turn ----------------------------------------------------------------------------

    async def _start_turn(
        self,
        *,
        text: str | None = None,
        resume: Literal["confirmed", "declined", "superseded"] | None = None,
        then: str | None = None,
        say: str | None = None,
        clock: TurnClock | None = None,
        message_id: str | None = None,
    ) -> None:
        if self._turn and not self._turn.done():
            if self._turn_is_say and resume is not None:
                # The store answered while Xena is saying "confirming your return now": let her
                # finish the sentence, then carry on (only talking over her cuts her off).
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await self._turn
            else:
                self._turn.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await self._turn
        self._turn_is_say = say is not None
        self._turn = asyncio.create_task(
            self._run_turn(
                text=text,
                resume=resume,
                then=then,
                say=say,
                clock=clock or TurnClock(),
                message_id=message_id,
            )
        )

    async def _run_turn(
        self,
        *,
        text: str | None,
        resume: Literal["confirmed", "declined", "superseded"] | None,
        then: str | None,
        say: str | None,
        clock: TurnClock,
        message_id: str | None = None,
    ) -> None:
        await self._set_state("thinking")
        self._answer_audio_started = False
        self._filler_played = False
        utterance: Utterance | None = None
        forward: asyncio.Task[None] | None = None
        answer: Segment | None = None
        chunker = SpeechChunker()
        # No filler for a fixed line, or right after "confirming your return now" (the outcome
        # follows it; "let me think" there would sound unsure about a done deal).
        quiet = say is not None or resume in ("confirmed", "declined")
        if quiet:
            self._filler_played = True
        filler_timer = (
            None if quiet else asyncio.create_task(self._filler_after(self.filler_after_ms, clock))
        )

        async def speak(chunk: str) -> None:
            nonlocal utterance, forward, answer
            if utterance is None:
                answer = await self._new_segment("answer")
                utterance = self.mouth.utterance()
                forward = asyncio.create_task(self._forward(utterance, answer, clock))
            assert answer is not None
            answer.text = f"{answer.text} {chunk}".strip()
            await self.send_json({"type": "segment.text", "segment": answer.number, "text": chunk})
            await utterance.push(chunk)

        async def finish() -> None:
            for chunk in chunker.flush():
                await speak(chunk)
            if utterance is not None:
                await utterance.finish()
            if forward is not None:
                await forward

        try:
            async with asyncio.timeout(self.max_turn_s):
                if say is not None:
                    await speak(say)
                    await finish()
                    return
                events = self._events(text=text, resume=resume, then=then, message_id=message_id)
                async for ev in events:
                    if isinstance(ev, TextDelta):
                        for chunk in chunker.feed(ev.text):
                            await speak(chunk)
                    elif isinstance(ev, ToolStarted):
                        await self.send_json({"type": "tool", "name": ev.name, "label": ev.label})
                        if utterance is None:
                            await self._play_filler(clock, tool=ev.name)
                    elif isinstance(ev, CardOut):
                        await self.send_json({"type": "card", "card": ev.card})
                    elif isinstance(ev, QuoteOut):
                        await finish()
                        utterance = forward = None
                        chunker = SpeechChunker()
                        self.quote = ev.quote
                        await self.send_json({"type": "quote", "quote": ev.quote})
                        readback = str(ev.quote.get("readback") or "")
                        if readback:
                            seg = await self._speak_whole(readback, "confirm", clock)
                            self._readback_segment = seg.number
                    elif isinstance(ev, TurnEnded):
                        clock.first_token_ms = ev.first_token_ms
                        await finish()
                        if ev.citations:
                            await self.send_json({"type": "citations", "citations": ev.citations})
                        if ev.error:
                            await self.send_json({"type": "error", "message": ev.error})
        except TimeoutError:
            log.warning("voice turn timed out")
            await self.send_json(
                {"type": "error", "message": "That took too long. Please ask me again."}
            )
        except asyncio.CancelledError:
            if utterance is not None:
                with contextlib.suppress(Exception):
                    await utterance.cancel()
            raise
        finally:
            if filler_timer and not filler_timer.done():
                filler_timer.cancel()
            if forward is not None and not forward.done():
                forward.cancel()
        await self.send_json({"type": "turn.done", "metrics": clock.metrics()})
        await self._maybe_idle()

    async def _events(
        self,
        *,
        text: str | None,
        resume: Literal["confirmed", "declined", "superseded"] | None,
        then: str | None,
        message_id: str | None = None,
    ) -> AsyncIterator[AgentEvent]:
        if resume is not None:
            async for ev in self.brain.resume(resume):
                yield ev
        follow = then if resume is not None else text
        if follow:
            async for ev in self.brain.turn(follow, message_id=message_id):
                yield ev

    # --- speaking ----------------------------------------------------------------------------

    async def _new_segment(self, kind: Literal["filler", "answer", "confirm"]) -> Segment:
        self._next_segment += 1
        seg = Segment(self._next_segment, kind, generation=self.output_generation)
        self.segments[seg.number] = seg
        if kind != "filler":
            # Real speech is on its way: a filler now would jump in front of it.
            self._answer_audio_started = True
        # Forget old, finished segments.
        for n in [n for n, s in self.segments.items() if s.complete and n < seg.number - 20]:
            del self.segments[n]
        await self.send_json(
            {
                "type": "segment.start",
                "segment": seg.number,
                "kind": kind,
                "text": "",
                "generation": seg.generation,
            }
        )
        return seg

    async def _send_audio(self, seg: Segment, pcm16: bytes, clock: TurnClock) -> None:
        if seg.complete:
            return
        header = seg.number.to_bytes(4, "little")
        if not seg.sent_audio:
            seg.sent_audio = True
            if clock.first_audio_at is None:
                clock.first_audio_at = self.clock()
            if self.state != "speaking":
                await self._set_state("speaking")
        await self.send_bytes(header + pcm16)

    async def _forward(self, utterance: Utterance, seg: Segment, clock: TurnClock) -> None:
        async for ev in utterance.events():
            if isinstance(ev, Audio):
                async with self._audio_lock:
                    self._answer_audio_started = True
                    await self._send_audio(seg, ev.pcm16, clock)
            elif isinstance(ev, Words):
                await self.send_json(
                    {"type": "segment.words", "segment": seg.number, "words": ev.words}
                )
            elif isinstance(ev, SpeechDone):
                seg.synthesized = True
                break
            elif isinstance(ev, SpeechFailed):
                seg.complete = True
                seg.dropped = True
                log.warning("speech failed: %s", ev.message)
                await self.send_json({"type": "drop", "segments": [seg.number]})
                await self.send_json(
                    {"type": "error", "message": "My voice cut out. The answer is on screen."}
                )
                break
        await self.send_json({"type": "segment.end", "segment": seg.number})

    async def _speak_whole(
        self, text: str, kind: Literal["filler", "answer", "confirm"], clock: TurnClock
    ) -> Segment:
        seg = await self._new_segment(kind)
        seg.text = text
        await self.send_json({"type": "segment.text", "segment": seg.number, "text": text})
        utterance = self.mouth.utterance()
        forward = asyncio.create_task(self._forward(utterance, seg, clock))
        # The caption keeps the exact words (a read-back is what gets confirmed); the voice
        # reads them the way a person would ("1 × Notebook" is "1 Notebook").
        try:
            await utterance.push(speakable(text))
            await utterance.finish()
            await forward
        finally:
            if not forward.done():
                forward.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await forward
            if not seg.synthesized:
                with contextlib.suppress(Exception):
                    await utterance.cancel()
        return seg

    async def _filler_after(self, ms: int, clock: TurnClock) -> None:
        await asyncio.sleep(ms / 1000)
        await self._play_filler(clock)

    async def _play_filler(self, clock: TurnClock, tool: str | None = None) -> None:
        if self._answer_audio_started or self._filler_played:
            return
        clip = self.fillers.get(self.picker.pick(tool))
        if clip is None:
            return
        self._filler_played = True
        clock.filler = True
        async with self._audio_lock:
            if self._answer_audio_started:
                return
            seg = await self._new_segment("filler")
            seg.text = clip.text
            await self.send_json({"type": "segment.text", "segment": seg.number, "text": clip.text})
            await self.send_json(
                {"type": "segment.words", "segment": seg.number, "words": clip.words}
            )
            for i in range(0, len(clip.pcm16), FRAME_BYTES):
                await self._send_audio(seg, clip.pcm16[i : i + FRAME_BYTES], clock)
            seg.synthesized = True
            await self.send_json({"type": "segment.end", "segment": seg.number})

    # --- state -------------------------------------------------------------------------------

    def _talking(self) -> bool:
        return any(s.sent_audio and not s.complete for s in self.segments.values())

    def _busy(self) -> bool:
        return (self._turn is not None and not self._turn.done()) or self._talking()

    async def _maybe_idle(self) -> None:
        if not self._busy() and self.state not in ("listening", "hearing"):
            await self._set_state("listening")

    async def _set_state(self, state: str) -> None:
        if state != self.state:
            self.state = state
            await self.send_json({"type": "state", "state": state})


async def render_fillers(mouth: Mouth, phrases: list[str]) -> dict[str, FillerClip]:
    """Synthesize every filler once, concurrently, at startup."""

    async def one(text: str) -> FillerClip | None:
        try:
            pcm, words = await mouth.synthesize(text)
            return FillerClip(text, pcm, words)
        except Exception as exc:  # noqa: BLE001 - a missing filler just isn't played
            log.warning("filler %r not rendered: %s", text, exc)
            return None

    clips = await asyncio.gather(*(one(p) for p in phrases))
    return {c.text: c for c in clips if c is not None}
