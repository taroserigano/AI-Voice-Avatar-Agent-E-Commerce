"""Xena's voice brain, driven with typed turns for the golden-set eval (``--channel voice``).

The same brain as a voice call (services/voice): the voice prompt with the call-start orders
snapshot, gpt-6-luna at the voice settings, the policy prefetch, and Xena's real tools against
the running commerce API for the signed-in customer. Only the ears and mouth are left out: the
customer's words go in as text and the answer comes out as text, so no speech is synthesized.
Conversations are checkpointed in memory, not saved.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import date
from typing import Any

import httpx
from langgraph.checkpoint.memory import InMemorySaver
from xana_eval import turn_contexts

from ai_commerce_voice.app import _recent_orders, pick_model
from ai_commerce_voice.brain import (
    XanaBrain,
    build_voice_graph,
    make_context,
    orders_snapshot,
    system_prompt,
)
from ai_commerce_voice.config import get_settings as voice_settings
from ai_commerce_voice.ports import CardOut, QuoteOut, TextDelta, ToolStarted, TurnEnded
from assistant.commerce import CommerceClient, catalog_vocabulary, resolve_customer
from assistant.config import get_settings as assistant_settings
from assistant.tools import ToolContext

_graph = build_voice_graph(InMemorySaver())


async def _run(user_web: httpx.Client, texts: list[str]) -> list[dict[str, Any]]:
    a = assistant_settings()
    v = voice_settings()
    customer = resolve_customer(user_web.cookies.get(a.session_cookie_name), a)
    client = CommerceClient(customer.id, a)
    first_name = customer.name.split(" ")[0]
    orders = _recent_orders(client)
    snapshot = orders_snapshot(orders) if orders is not None else None
    vocabulary = catalog_vocabulary(client)
    async with httpx.AsyncClient(timeout=30) as http:
        pick = pick_model(v, http)
        brain = XanaBrain(
            _graph,
            conversation_id=str(uuid.uuid4()),
            ctx=ToolContext(client=client, agent="xana", first_name=first_name, voice=True),
            voice=make_context(
                pick.model,
                system=system_prompt(first_name, date.today(), snapshot, vocabulary),
                max_tool_calls=v.voice_max_tool_calls,
                strong=pick.strong,
                strong_name=pick.strong_name,
            ),
            model=pick.name,
            simulated=pick.simulated,
        )
        out = []
        for text in texts:
            got: dict[str, Any] = {"text": "", "cards": [], "quotes": [], "tools": [],
                                   "citations": [], "invalid_citations": [], "errors": [],
                                   "done": {"model": pick.name}}  # fmt: skip
            # A new turn while a quote waits closes it first, as the call does.
            if await brain.pending_quote():
                async for _ in brain.resume("superseded"):
                    pass
            started = time.perf_counter()
            async for ev in brain.turn(text):
                if isinstance(ev, TextDelta):
                    if not got["text"]:
                        got["first_text_ms"] = round((time.perf_counter() - started) * 1000)
                    got["text"] += ev.text
                elif isinstance(ev, ToolStarted):
                    got["tools"].append(ev.name)
                elif isinstance(ev, CardOut):
                    got["cards"].append(ev.card)
                elif isinstance(ev, QuoteOut):
                    got["quotes"].append(ev.quote)
                elif isinstance(ev, TurnEnded):
                    got["citations"] = ev.citations or []
                    got["invalid_citations"] = list(ev.invalid_citations or [])
                    if ev.error:
                        got["errors"].append(ev.error)
            got["turn_ms"] = round((time.perf_counter() - started) * 1000)
            state = await brain.graph.aget_state(
                {"configurable": {"thread_id": brain.conversation_id}}
            )
            got["escalated"] = state.values.get("escalated")
            out.append(got)
        # What the model asked each tool and what came back, per turn; the call-start orders
        # snapshot in the system prompt is evidence for every turn.
        state = await brain.graph.aget_state({"configurable": {"thread_id": brain.conversation_id}})
        found = turn_contexts(state.values.get("messages", []), texts)
        for got, f in zip(out, found, strict=True):
            got["tool_calls"] = f["tool_calls"]
            got["contexts"] = f["contexts"] + (
                [{"tool": "orders_snapshot", "content": json.dumps(snapshot)}] if snapshot else []
            )
        client.close()
        return out


def voice_turns(user_web: httpx.Client, texts: list[str]) -> list[dict[str, Any]]:
    return asyncio.run(_run(user_web, texts))
