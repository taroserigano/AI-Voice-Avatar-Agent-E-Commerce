"""Assistant API: conversations with Steph (shopping) and Xana (support).

Every route but ``/healthz`` needs the customer's session: the browser reaches this service
through the web app's ``/api/assistant/*`` rewrite with its HttpOnly cookie, and each request
asks the commerce API who that is. Conversations belong to one customer; anyone else gets 404.
"""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Iterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from langgraph.checkpoint.postgres import PostgresSaver
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from sqlalchemy import select
from sqlalchemy.orm import Session

from assistant import voice
from assistant.commerce import CommerceClient, Customer, NotSignedIn, resolve_customer
from assistant.config import get_settings
from assistant.db import Conversation, get_sessionmaker, utcnow
from assistant.graph import build_graph
from assistant.jev.signals import decision_model
from assistant.models import choose_model
from assistant.prompts import PROMPT_VERSIONS
from assistant.schemas import (
    AgentName,
    AssistantStatus,
    ConfirmCheckIn,
    ConfirmCheckOut,
    ConversationDetail,
    ConversationOut,
    CreateConversation,
    ResumeTurn,
    SendMessage,
    SpeakIn,
    TranscriptOut,
    VoiceConfig,
)
from assistant.tools import ToolContext
from assistant.turns import history, pending_quote, run_turn, sse

log = logging.getLogger(__name__)
TYPED_YES = re.compile(r"^\s*(yes|yeah|yep|sure|ok|okay|confirm|do it|go ahead)\b")


def get_db() -> Iterator[Session]:
    with get_sessionmaker()() as session:
        yield session


def current_customer(request: Request) -> Customer:
    settings = get_settings()
    try:
        return resolve_customer(request.cookies.get(settings.session_cookie_name), settings)
    except NotSignedIn:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in required") from None


CustomerDep = Annotated[Customer, Depends(current_customer)]
DbDep = Annotated[Session, Depends(get_db)]


def _conversation_out(c: Conversation) -> ConversationOut:
    return ConversationOut(
        id=c.id,
        agent=c.agent,
        title=c.title,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


def _own(db: Session, conversation_id: uuid.UUID, customer: Customer) -> Conversation:
    conv = db.get(Conversation, conversation_id)
    if conv is None or conv.user_id != customer.id:
        # 404 either way: don't confirm that someone else's conversation exists.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return conv


def _decision_model_name() -> str:
    model = decision_model()
    if model is None:
        return "off"
    return "jev-simulator" if model.simulated else get_settings().jev_model


def create_app(checkpointer: Any | None = None) -> FastAPI:
    settings = get_settings()
    state: dict[str, Any] = {}

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
        pool = None
        saver = checkpointer
        if saver is None:
            pool = ConnectionPool(
                settings.psycopg_dsn,
                min_size=1,
                max_size=8,
                kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
            )
            saver = PostgresSaver(pool)  # type: ignore[arg-type]
        state["graph"] = build_graph(saver)
        yield
        if pool is not None:
            pool.close()

    app = FastAPI(
        title="AI Commerce Assistant API",
        version="0.1.0",
        docs_url="/docs" if settings.is_dev else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/assistant/status", response_model=AssistantStatus)
    def assistant_status(customer: CustomerDep) -> AssistantStatus:
        choice = choose_model()
        return AssistantStatus(
            model=choice.name,
            simulated=choice.simulated,
            reason=choice.reason,
            prompt_versions=PROMPT_VERSIONS,
            decision_model=_decision_model_name(),
            debug=settings.is_dev,
        )

    @app.post("/v1/assistant/conversations", response_model=ConversationOut, status_code=201)
    def create_conversation(
        body: CreateConversation, customer: CustomerDep, db: DbDep
    ) -> ConversationOut:
        conv = Conversation(id=uuid.uuid4(), user_id=customer.id, agent=body.agent)
        db.add(conv)
        db.commit()
        return _conversation_out(conv)

    @app.get("/v1/assistant/conversations", response_model=list[ConversationOut])
    def list_conversations(
        customer: CustomerDep,
        db: DbDep,
        agent: AgentName | None = None,
        limit: Annotated[int, Query(ge=1, le=50)] = 20,
    ) -> list[ConversationOut]:
        stmt = select(Conversation).where(Conversation.user_id == customer.id)
        if agent:
            stmt = stmt.where(Conversation.agent == agent)
        rows = db.scalars(stmt.order_by(Conversation.updated_at.desc()).limit(limit))
        return [_conversation_out(c) for c in rows]

    @app.get("/v1/assistant/conversations/{conversation_id}", response_model=ConversationDetail)
    def get_conversation(
        conversation_id: uuid.UUID, customer: CustomerDep, db: DbDep
    ) -> ConversationDetail:
        conv = _own(db, conversation_id, customer)
        snapshot = state["graph"].get_state({"configurable": {"thread_id": str(conv.id)}})
        messages = (snapshot.values or {}).get("messages", []) if snapshot else []
        return ConversationDetail(
            **_conversation_out(conv).model_dump(),
            messages=history(messages),
            pending_quote=pending_quote(state["graph"], str(conv.id)),
        )

    def _stream(
        conv: Conversation, customer: Customer, voice: bool, **turn: Any
    ) -> StreamingResponse:
        client = CommerceClient(customer.id, settings)
        ctx = ToolContext(
            client=client,
            agent=conv.agent,
            first_name=customer.name.split(" ")[0],
            voice=voice,
            conversation_id=str(conv.id),
        )

        def events() -> Iterator[str]:
            try:
                waiting = pending_quote(state["graph"], str(conv.id)) if turn.get("text") else None
                if waiting and TYPED_YES.match(str(turn["text"]).lower()):
                    # A typed "yes" isn't a confirmation: point to the button, keep the quote.
                    yield sse(
                        "text",
                        {
                            "delta": "To confirm, tap Confirm return on the quote. "
                            "(By voice, say yes after I read it back.)"
                        },
                    )
                    yield sse("quote", waiting)
                    yield sse("citations", {"valid": [], "invalid": []})
                    yield sse(
                        "done",
                        {
                            "model": choose_model().name,
                            "simulated": choose_model().simulated,
                            "prompt_version": PROMPT_VERSIONS[conv.agent],
                        },
                    )
                    return
                if waiting:
                    # The customer moved on while a quote was waiting: close it (nothing is
                    # returned) before handling what they said.
                    for _ in run_turn(
                        state["graph"],
                        conversation_id=str(conv.id),
                        agent=conv.agent,
                        ctx=ctx,
                        resume={"outcome": "superseded"},
                    ):
                        pass
                yield from run_turn(
                    state["graph"], conversation_id=str(conv.id), agent=conv.agent, ctx=ctx, **turn
                )
            finally:
                client.close()

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )

    @app.post("/v1/assistant/conversations/{conversation_id}/messages")
    def send_message(
        conversation_id: uuid.UUID, body: SendMessage, customer: CustomerDep, db: DbDep
    ) -> StreamingResponse:
        conv = _own(db, conversation_id, customer)
        text = body.text.strip()[: settings.max_input_chars]
        if conv.turn_count >= settings.max_turns_per_conversation:
            limit_hit = sse(
                "error",
                {"message": "This conversation is at its limit. Start a new one to keep going."},
            )
            return StreamingResponse(iter([limit_hit]), media_type="text/event-stream")
        if conv.turn_count == 0:
            conv.title = text[:80]
        conv.turn_count += 1
        conv.updated_at = utcnow()
        db.commit()
        return _stream(conv, customer, body.voice, text=text)

    # --- Voice (Xana) ------------------------------------------------------------------------

    @app.get("/v1/assistant/voice/config", response_model=VoiceConfig)
    def voice_config(customer: CustomerDep) -> VoiceConfig:
        return VoiceConfig(
            stt=voice.stt_provider(settings),
            tts=voice.tts_provider(settings),
            max_seconds=settings.voice_max_seconds,
            decision_model=_decision_model_name(),
            notice="Xana is an AI assistant. Your speech is sent to our speech providers to be "
            "turned into text and isn't stored; the text is saved with this conversation.",
        )

    @app.post("/v1/assistant/voice/transcribe", response_model=TranscriptOut)
    def transcribe_audio(
        customer: CustomerDep, audio: Annotated[UploadFile, File()]
    ) -> TranscriptOut:
        data = audio.file.read(settings.voice_max_audio_bytes + 1)
        if len(data) > settings.voice_max_audio_bytes:
            raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "That recording is too long.")
        if len(data) < 200:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, "No speech in that recording."
            )
        try:
            result = voice.transcribe(settings, data, audio.content_type or "audio/webm")
        except voice.VoiceError as exc:
            raise HTTPException(exc.status, str(exc)) from None
        return TranscriptOut(
            text=result.text, provider=result.provider, latency_ms=round(result.latency_ms, 1)
        )

    @app.post("/v1/assistant/voice/speak", response_class=Response)
    def speak_text(body: SpeakIn, customer: CustomerDep) -> Response:
        text = voice.speakable(body.text)[: settings.voice_max_speak_chars]
        if not text:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Nothing to say.")
        try:
            audio = voice.speak(settings, text, body.agent)
        except voice.VoiceError as exc:
            raise HTTPException(exc.status, str(exc)) from None
        return Response(
            content=audio, media_type="audio/mpeg", headers={"Cache-Control": "no-store"}
        )

    @app.post("/v1/assistant/voice/confirm-check", response_model=ConfirmCheckOut)
    def confirm_check(body: ConfirmCheckIn, customer: CustomerDep, db: DbDep) -> ConfirmCheckOut:
        """Did the customer clearly say yes to the read-back? The app decides, not the model;
        on "yes" the browser confirms with the store itself."""
        conv = _own(db, body.conversation_id, customer)
        waiting = pending_quote(state["graph"], str(conv.id))
        if waiting is None or waiting.get("quote_id") != str(body.quote_id):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "No quote is waiting in this conversation"
            )
        result = voice.confirm_decision(
            body.text,
            final=body.final,
            readback_complete=body.readback_complete,
            speech_ms=body.speech_ms,
        )
        say = {
            "yes": "Thanks, confirming your return now.",
            "no": "Okay, I won't return it. Nothing has changed.",
            "unclear": 'Sorry, I need a clear yes to confirm. Say "yes, confirm", or tap Confirm '
            "return on the screen.",
        }[result.decision]
        log.info("voice confirmation: %s (%s)", result.decision, result.reason)
        return ConfirmCheckOut(decision=result.decision, reason=result.reason, say=say)

    @app.post("/v1/assistant/conversations/{conversation_id}/resume")
    def resume_turn(
        conversation_id: uuid.UUID, body: ResumeTurn, customer: CustomerDep, db: DbDep
    ) -> StreamingResponse:
        """Continue after the customer confirmed or declined a quote in their browser. The
        proposal tool checks the outcome with the store; this message only wakes it up."""
        conv = _own(db, conversation_id, customer)
        waiting = pending_quote(state["graph"], str(conv.id))
        if waiting is None or waiting.get("quote_id") != str(body.quote_id):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "No quote is waiting in this conversation"
            )
        conv.updated_at = utcnow()
        db.commit()
        return _stream(conv, customer, body.voice, resume={"outcome": body.outcome})

    return app


def build_instrumented_app() -> FastAPI:
    from assistant.telemetry import init_telemetry

    init_telemetry("assistant-api")
    app = create_app()
    FastAPIInstrumentor.instrument_app(app, excluded_urls="healthz")
    return app
