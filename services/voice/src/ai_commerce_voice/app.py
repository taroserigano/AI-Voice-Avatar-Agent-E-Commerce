"""The voice agent service: one WebSocket per call at ``/v1/voice/xana``.

Security, same rules as the rest of the store:

- sign-in required: the session cookie is checked with the commerce API before anything else
  (close code 4401 otherwise), and the customer's identity is injected on the server;
- the socket only opens from the store's own pages (``Origin`` allowlist), so another site
  can't ride the customer's cookie (cross-site WebSocket hijacking);
- a conversation id from the browser is used only if that customer owns it;
- the model gets Xana's narrow support tools, never a confirm tool; a spoken yes is judged by
  the app's strict rule (plus Jev's veto when on), and the browser confirms with the store.

Speed: the speech-to-text and speech sockets are opened, the customer's recent orders are
read, and the model's HTTPS connection is warmed all at once while the call connects. Fillers
are rendered once per process (and cached on disk), so they cost nothing per call.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import logging
import uuid
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from langchain_core.language_models import BaseChatModel

from ai_commerce_voice.brain import (
    XanaBrain,
    build_voice_graph,
    make_context,
    orders_snapshot,
    system_prompt,
)
from ai_commerce_voice.config import VoiceSettings, get_settings
from ai_commerce_voice.ears_openai import OpenAILiveEars
from ai_commerce_voice.face_tavus import AvatarLink, TavusFace
from ai_commerce_voice.fillers import all_phrases
from ai_commerce_voice.mouth_cartesia import CartesiaMouth
from ai_commerce_voice.ports import AgentEvent, TurnEnded
from ai_commerce_voice.session import FillerClip, VoiceSession
from assistant import voice as assistant_voice
from assistant.commerce import (
    CommerceClient,
    CommerceError,
    Customer,
    NotSignedIn,
    catalog_vocabulary,
    resolve_customer,
)
from assistant.config import get_settings as assistant_settings
from assistant.db import Conversation, get_sessionmaker, utcnow
from assistant.tools import ToolContext, with_brands

log = logging.getLogger(__name__)

CACHE = Path(__file__).resolve().parents[2] / ".cache" / "fillers"
NOTICE = (
    "Xana is an AI assistant. Your voice is streamed to our speech providers to be turned into "
    "text and isn't stored; the transcript is saved with this conversation."
)
_pool = ThreadPoolExecutor(max_workers=16, thread_name_prefix="voice-io")
_background: set[asyncio.Task[None]] = set()


def confirm_rule(
    text: str, *, final: bool, readback_complete: bool, speech_ms: float
) -> Literal["yes", "no", "unclear"]:
    """The chat's own strict check of a spoken yes (plus Jev's veto when on). Never the model."""
    result = assistant_voice.confirm_decision(
        text, final=final, readback_complete=readback_complete, speech_ms=int(speech_ms)
    )
    log.info("voice confirmation: %s (%s)", result.decision, result.reason)
    decision: Literal["yes", "no", "unclear"] = result.decision
    return decision


# --- models ---------------------------------------------------------------------------------


@dataclass
class ModelPick:
    model: BaseChatModel
    name: str
    simulated: bool
    # The stronger model for escalated turns (decision 26), if configured.
    strong: BaseChatModel | None = None
    strong_name: str | None = None


def pick_model(settings: VoiceSettings, http: httpx.AsyncClient) -> ModelPick:
    if settings.voice_llm_mode == "scripted" or (
        settings.voice_llm_mode == "auto" and not settings.openai_api_key
    ):
        from assistant.scripted import SCRIPTED_MODEL_NAME, ScriptedChatModel

        return ModelPick(ScriptedChatModel(), SCRIPTED_MODEL_NAME, True)
    from langchain_openai import ChatOpenAI

    def chat_model(name: str, effort: str) -> BaseChatModel:
        return ChatOpenAI(
            model=name,
            api_key=settings.openai_api_key,
            use_responses_api=True,
            reasoning={"effort": effort},
            streaming=True,
            max_retries=1,
            timeout=20,
            max_tokens=400 if effort in ("none", "low") else 1200,
            http_async_client=http,
            model_kwargs={
                "prompt_cache_key": f"xana-voice-v1-{name}",
                "service_tier": settings.voice_llm_service_tier,
            },
        )

    strong_name = settings.voice_escalation_model or None
    return ModelPick(
        chat_model(settings.voice_llm_model, settings.voice_llm_reasoning),
        settings.voice_llm_model,
        False,
        strong=chat_model(strong_name, settings.voice_escalation_reasoning)
        if strong_name
        else None,
        strong_name=strong_name,
    )


# --- fillers ----------------------------------------------------------------------------------


def _cache_key(settings: VoiceSettings, text: str) -> str:
    raw = f"{settings.cartesia_model}|{settings.cartesia_voice_id}|24000|{text}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


async def load_fillers(settings: VoiceSettings, clips: dict[str, FillerClip]) -> None:
    """Every filler, from the disk cache or rendered with Skylar (two at a time: Cartesia's
    concurrency limit is per account). Fills ``clips`` in place, so calls that started before
    rendering finished get the fillers as soon as they exist."""
    missing: list[str] = []
    CACHE.mkdir(parents=True, exist_ok=True)
    for text in all_phrases():
        base = CACHE / _cache_key(settings, text)
        pcm, meta = base.with_suffix(".pcm"), base.with_suffix(".json")
        if pcm.exists() and meta.exists():
            clips[text] = FillerClip(text, pcm.read_bytes(), json.loads(meta.read_text("utf-8")))
        else:
            missing.append(text)
    if missing and settings.cartesia_api_key:
        mouth = CartesiaMouth(
            settings.cartesia_api_key,
            model=settings.cartesia_model,
            version=settings.cartesia_version,
            voice_id=settings.cartesia_voice_id,
        )
        await mouth.start()
        gate = asyncio.Semaphore(2)

        async def one(text: str) -> None:
            async with gate:
                try:
                    audio, words = await mouth.synthesize(text)
                except Exception as exc:  # noqa: BLE001 - a missing filler just isn't played
                    log.warning("filler %r not rendered: %s", text, exc)
                    return
            base = CACHE / _cache_key(settings, text)
            base.with_suffix(".pcm").write_bytes(audio)
            base.with_suffix(".json").write_text(json.dumps(words), "utf-8")
            clips[text] = FillerClip(text, audio, words)

        try:
            await asyncio.gather(*(one(t) for t in missing))
        finally:
            await mouth.close()
    log.info("voice fillers ready: %d of %d", len(clips), len(all_phrases()))


def make_face(settings: VoiceSettings, http: httpx.AsyncClient) -> TavusFace | None:
    """Xana's avatar, when it's turned on for this server and configured."""
    if not settings.avatar_ready:
        return None
    assert settings.tavus_api_key and settings.tavus_pal_id
    return TavusFace(
        settings.tavus_api_key,
        pal_id=settings.tavus_pal_id,
        face_id=settings.tavus_face_id,
        http=http,
        max_live=settings.tavus_max_live,
        max_call_s=settings.voice_max_session_s,
        test_mode=settings.tavus_test_mode,
    )


# --- per-call helpers -------------------------------------------------------------------------


def _own_or_new(customer: Customer, conversation_id: str | None) -> Conversation:
    with get_sessionmaker()() as db:
        if conversation_id:
            with contextlib.suppress(ValueError):
                found: Conversation | None = db.get(Conversation, uuid.UUID(conversation_id))
                if found is not None and found.user_id == customer.id and found.agent == "xana":
                    return found
        conv = Conversation(user_id=customer.id, agent="xana", title="Voice call with Xana")
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv


def _count_turn(conversation_id: uuid.UUID, text: str, limit: int) -> bool:
    """Count a customer turn; False when the conversation is at its limit."""
    with get_sessionmaker()() as db:
        conv = db.get(Conversation, conversation_id)
        if conv is None or conv.turn_count >= limit:
            return False
        if conv.turn_count == 0:
            conv.title = f"Voice: {text}"[:80]
        conv.turn_count += 1
        conv.updated_at = utcnow()
        db.commit()
        return True


def _warm_policy_search(client: CommerceClient) -> None:
    """One throwaway policy search while the call connects, so the first real question doesn't
    pay for a cold connection, embedding client, and vector index."""
    # RuntimeError: the call ended and its client closed before the warm-up finished.
    with contextlib.suppress(CommerceError, httpx.HTTPError, RuntimeError):
        client.get("/v1/policies/search", params={"q": "return policy", "limit": 1})


def _recent_orders(client: CommerceClient) -> list[dict[str, Any]] | None:
    try:
        summaries = client.get("/v1/orders")[:8]
        details = list(_pool.map(lambda o: client.get(f"/v1/orders/{o['id']}"), summaries))
        delivered = [d for d in details if d.get("status") == "delivered"]
        # Whether each item can be returned right now, from the returns engine: the model
        # must never work that out from the delivery date itself.
        for d, opts in zip(
            delivered,
            _pool.map(lambda d: client.get(f"/v1/orders/{d['id']}/return-options"), delivered),
            strict=True,
        ):
            d["return_options"] = opts
        return with_brands(client, details)
    except (CommerceError, httpx.HTTPError) as exc:
        log.warning("couldn't read recent orders for the call: %s", exc)
        return None


class CountingBrain:
    """Xana's brain with the conversation's turn limit applied."""

    def __init__(self, brain: XanaBrain, conversation_id: uuid.UUID, limit: int) -> None:
        self.inner = brain
        self.model = brain.model
        self.simulated = brain.simulated
        self._id = conversation_id
        self._limit = limit

    async def turn(self, text: str, message_id: str | None = None) -> AsyncIterator[AgentEvent]:
        ok = await asyncio.to_thread(_count_turn, self._id, text, self._limit)
        if not ok:
            yield TurnEnded(
                error="This conversation is at its limit. Start a new call to keep going."
            )
            return
        async for ev in self.inner.turn(text, message_id=message_id):
            yield ev

    def resume(
        self, outcome: Literal["confirmed", "declined", "superseded"]
    ) -> AsyncIterator[AgentEvent]:
        return self.inner.resume(outcome)

    async def pending_quote(self) -> dict[str, Any] | None:
        return await self.inner.pending_quote()


# --- the app ----------------------------------------------------------------------------------


def create_app(checkpointer: Any | None = None) -> FastAPI:
    settings = get_settings()
    state: dict[str, Any] = {"fillers": {}}

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        pool = None
        saver = checkpointer
        if saver is None:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            from psycopg.rows import dict_row
            from psycopg_pool import AsyncConnectionPool

            pool = AsyncConnectionPool(
                assistant_settings().psycopg_dsn,
                min_size=1,
                max_size=8,
                open=False,
                kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
            )
            await pool.open(wait=True, timeout=10)
            saver = AsyncPostgresSaver(pool)  # type: ignore[arg-type]
        state["graph"] = build_voice_graph(saver)
        state["http"] = httpx.AsyncClient(
            http2=False,
            timeout=httpx.Timeout(20, connect=5),
            limits=httpx.Limits(max_keepalive_connections=20),
        )
        state["fillers_task"] = asyncio.create_task(load_fillers(settings, state["fillers"]))
        state["face"] = make_face(settings, state["http"])
        yield
        await state["http"].aclose()
        if pool is not None:
            await pool.close()

    app = FastAPI(
        title="Xana voice agent", version="0.1.0", docs_url=None, redoc_url=None, lifespan=lifespan
    )

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        return {"ok": True, "fillers": len(state["fillers"]) or None}

    @app.websocket("/v1/voice/xana")
    async def voice_call(ws: WebSocket) -> None:
        origin = ws.headers.get("origin")
        if origin not in settings.voice_allowed_origins:
            await ws.close(code=4403)
            return
        a_settings = assistant_settings()
        try:
            customer = await asyncio.to_thread(
                resolve_customer, ws.cookies.get(a_settings.session_cookie_name), a_settings
            )
        except NotSignedIn:
            await ws.close(code=4401)
            return
        await ws.accept()
        if not settings.cartesia_api_key or not settings.openai_api_key:
            await ws.send_json(
                {
                    "type": "error",
                    "fatal": True,
                    "message": "Xana's voice isn't set up on this server.",
                }
            )
            await ws.close()
            return

        try:
            hello = json.loads(await asyncio.wait_for(ws.receive_text(), 10))
        except (TimeoutError, json.JSONDecodeError, WebSocketDisconnect):
            await ws.close(code=4400)
            return

        client = CommerceClient(customer.id, a_settings)
        first_name = (customer.name or "").split(" ")[0]
        mouth = CartesiaMouth(
            settings.cartesia_api_key,
            model=settings.cartesia_model,
            version=settings.cartesia_version,
            voice_id=settings.cartesia_voice_id,
            voice_name=settings.cartesia_voice_name,
        )
        session_ref: dict[str, VoiceSession] = {}
        ears = OpenAILiveEars(
            settings.openai_api_key,
            model=settings.voice_stt_model,
            talking=lambda: bool(session_ref) and session_ref["s"].state == "speaking",
        )
        pick = pick_model(settings, state["http"])

        async def warm_model() -> None:
            if not pick.simulated:
                with contextlib.suppress(httpx.HTTPError):
                    await state["http"].get(
                        "https://api.openai.com/v1/models/" + settings.voice_llm_model,
                        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    )

        try:
            # Not awaited: a cold policy search can take seconds, and the call shouldn't wait.
            warm = asyncio.create_task(asyncio.to_thread(_warm_policy_search, client))
            _background.add(warm)
            warm.add_done_callback(_background.discard)
            conv, orders, *_ = await asyncio.gather(
                asyncio.to_thread(_own_or_new, customer, hello.get("conversation_id")),
                asyncio.to_thread(_recent_orders, client),
                ears.start(),
                mouth.start(),
                warm_model(),
            )
        except Exception:
            log.exception("voice call setup failed")
            await ws.send_json(
                {
                    "type": "error",
                    "fatal": True,
                    "message": "Couldn't connect Xana's voice. Try again in a moment.",
                }
            )
            await ws.close()
            client.close()
            await ears.close()
            await mouth.close()
            return

        try:
            vocabulary = await asyncio.to_thread(catalog_vocabulary, client)
        except (CommerceError, httpx.HTTPError) as exc:
            log.warning("couldn't read catalog filters for the call: %s", type(exc).__name__)
            vocabulary = {}
        system = system_prompt(
            first_name,
            date.today(),
            orders_snapshot(orders) if orders is not None else None,
            vocabulary,
        )
        extra: dict[str, Any] = {}
        if pick.simulated:
            extra = {
                "vocabulary": vocabulary,
                "signals": {"source": "off"},
                "agent": "xana",
            }
        ctx = ToolContext(
            client=client,
            agent="xana",
            first_name=first_name,
            voice=True,
            conversation_id=str(conv.id),
        )
        brain = XanaBrain(
            state["graph"],
            conversation_id=str(conv.id),
            ctx=ctx,
            voice=make_context(
                pick.model,
                strong=pick.strong,
                strong_name=pick.strong_name,
                system=system,
                max_tool_calls=settings.voice_max_tool_calls,
                bind_extra=extra,
            ),
            model=pick.name,
            simulated=pick.simulated,
        )
        send_lock = asyncio.Lock()

        async def send_json(msg: dict[str, Any]) -> None:
            async with send_lock:
                await ws.send_text(json.dumps(msg, default=str, ensure_ascii=False))

        async def send_bytes(data: bytes) -> None:
            async with send_lock:
                await ws.send_bytes(data)

        session = VoiceSession(
            send_json=send_json,
            send_bytes=send_bytes,
            ears=ears,
            mouth=mouth,
            brain=CountingBrain(brain, conv.id, a_settings.max_turns_per_conversation),
            confirm=confirm_rule,
            fillers=state["fillers"],
            filler_after_ms=settings.voice_filler_after_ms,
            max_turn_s=settings.voice_max_turn_s,
        )
        session_ref["s"] = session
        avatar = AvatarLink(state.get("face"), str(conv.id), send_json)
        await send_json(
            {
                "type": "ready",
                "conversation_id": str(conv.id),
                "first_name": first_name,
                "voice": {"provider": "cartesia", "name": settings.cartesia_voice_name},
                "stt": {"provider": "openai", "model": settings.voice_stt_model},
                "llm": {"model": pick.name, "simulated": pick.simulated},
                "avatar": avatar.describe(),
                "notice": NOTICE,
            }
        )
        waiting = await brain.pending_quote()
        if waiting:
            session.quote = waiting
            await send_json({"type": "quote", "quote": waiting})
        await session.start()

        try:
            async with asyncio.timeout(settings.voice_max_session_s):
                while True:
                    msg = await ws.receive()
                    if msg["type"] == "websocket.disconnect":
                        break
                    if (data := msg.get("bytes")) is not None:
                        await session.on_audio(data)
                    elif (text := msg.get("text")) is not None:
                        with contextlib.suppress(json.JSONDecodeError):
                            parsed = json.loads(text)
                            if not isinstance(parsed, dict):
                                continue
                            if str(parsed.get("type", "")).startswith("avatar."):
                                await avatar.on_message(parsed)
                            else:
                                await session.on_message(parsed)
        except (WebSocketDisconnect, TimeoutError):
            pass
        finally:
            await avatar.close()
            await session.close()
            await ears.close()
            await mouth.close()
            client.close()
            with contextlib.suppress(Exception):
                await ws.close()

    return app


def main() -> None:
    import sys

    import uvicorn

    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    config = uvicorn.Config(
        "ai_commerce_voice.app:create_app",
        factory=True,
        host=settings.voice_host,
        port=settings.voice_port,
        ws_max_size=2**20,
        log_level="info",
    )
    server = uvicorn.Server(config)
    if sys.platform == "win32":
        # Async psycopg (the checkpoint pool) can't run on Windows' default Proactor loop.
        asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop)
    else:
        server.run()
