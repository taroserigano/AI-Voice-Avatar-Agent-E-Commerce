"""Server-sent event encoding: v2 (with ``id:``), the heartbeat, and the v1 translator.

v1 is what Steph's web client parses today (``services/assistant/turns.py``):
``event: <name>`` / ``data: <json>`` with no ``id:``. :func:`encode_v1` reproduces those
bytes exactly, so old clients keep working until the web moves to v2 (decision v2-6).
"""

from __future__ import annotations

import json
from typing import Any

from ai_commerce_stream.events import (
    Card,
    Citations,
    Done,
    Error,
    Quote,
    Signals,
    StreamEvent,
    TextDelta,
    ToolStart,
)

HEARTBEAT = ": ping\n\n"  # a comment line: keeps proxies from closing an idle stream
HEADERS = {
    "Cache-Control": "no-store",
    "X-Accel-Buffering": "no",  # don't let a proxy buffer the stream
    "Connection": "keep-alive",
}
V2_HEADER = "x-assistant-stream"


def _json(data: Any) -> str:
    return json.dumps(data, default=str, ensure_ascii=False)


def encode(seq: int, event: StreamEvent) -> str:
    payload = event.model_dump(mode="json")
    return f"id: {seq}\nevent: {payload['type']}\ndata: {_json(payload)}\n\n"


def encode_v1(name: str, data: Any) -> str:
    return f"event: {name}\ndata: {_json(data)}\n\n"


def to_v1(event: StreamEvent) -> tuple[str, Any] | None:
    """The v1 event for a v2 one, or None where v1 has no equivalent (plans, handoffs...)."""
    match event:
        case Signals():
            return "signals", event.signals
        case ToolStart():
            return "status", {"tool": event.tool, "label": event.label}
        case TextDelta():
            return "text", {"delta": event.delta}
        case Card():
            return "card", event.card
        case Quote():
            return "quote", event.quote
        case Citations():
            return "citations", {"valid": event.valid, "invalid": event.invalid}
        case Done():
            return "done", {
                "model": event.model,
                "simulated": event.simulated,
                "prompt_version": event.prompt_version,
            }
        case Error():
            return "error", {"message": event.message}
    return None


def wants_v2(headers: Any) -> bool:
    return str(headers.get(V2_HEADER, "")).strip() == "2"


def parse_stream(text: str) -> list[dict[str, Any]]:
    """Split SSE text into events: ``{"id": str|None, "event": str, "data": Any}``.
    Comments (heartbeats) are skipped. For tests and server-side consumers."""
    out: list[dict[str, Any]] = []
    for block in text.replace("\r\n", "\n").split("\n\n"):
        fields: dict[str, str] = {}
        for line in block.split("\n"):
            if not line or line.startswith(":"):
                continue
            key, _, value = line.partition(":")
            fields[key] = fields.get(key, "") + value.removeprefix(" ")
        if "event" in fields or "data" in fields:
            out.append(
                {
                    "id": fields.get("id"),
                    "event": fields.get("event", "message"),
                    "data": json.loads(fields["data"]) if "data" in fields else None,
                }
            )
    return out
