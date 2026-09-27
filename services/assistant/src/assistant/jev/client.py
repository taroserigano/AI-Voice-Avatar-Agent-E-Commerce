"""The HTTP client for ``POST https://api.typesafe.ai/v1/systemone``.

Retries only 429 and 529 (rate limit, overloaded) with a short backoff, and gives up quickly:
the assistant keeps working without Jev, so a slow answer is worth less than no answer.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Protocol

import httpx
from opentelemetry import trace

from assistant.jev.types import JevResult, Question, Usage, parse_answers

log = logging.getLogger(__name__)
tracer = trace.get_tracer("assistant.jev")

RETRY_STATUSES = frozenset({429, 529})


class JevError(RuntimeError):
    pass


class DecisionModel(Protocol):
    """Jev or its local simulator."""

    simulated: bool

    def ask(self, state: Any, questions: dict[str, Question]) -> JevResult: ...


class JevClient:
    simulated = False

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "jev-latest",
        base_url: str = "https://api.typesafe.ai",
        timeout_s: float = 1.5,
        max_attempts: int = 2,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.model = model
        self.max_attempts = max_attempts
        self._http = httpx.Client(
            base_url=base_url,
            timeout=timeout_s,
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
        )

    def ask(self, state: Any, questions: dict[str, Question]) -> JevResult:
        body = {
            "state": state,
            "model": self.model,
            "questions": {k: q.model_dump(exclude_none=True) for k, q in questions.items()},
        }
        with tracer.start_as_current_span("jev.systemone") as span:
            span.set_attribute("jev.questions", len(questions))
            span.set_attribute("jev.model.requested", self.model)
            started = time.perf_counter()
            for attempt in range(1, self.max_attempts + 1):
                try:
                    resp = self._http.post("/v1/systemone", json=body)
                except httpx.HTTPError as exc:
                    raise JevError(f"Jev unreachable: {type(exc).__name__}") from exc
                if resp.status_code in RETRY_STATUSES and attempt < self.max_attempts:
                    wait = min(float(resp.headers.get("retry-after", "0.3") or 0.3), 1.0)
                    time.sleep(wait)
                    continue
                break
            latency = (time.perf_counter() - started) * 1000
            if resp.status_code != 200:
                span.set_attribute("jev.status", resp.status_code)
                raise JevError(f"Jev answered {resp.status_code}")
            data = resp.json()
            usage = Usage.model_validate(data.get("usage") or {})
            span.set_attribute("jev.model", data.get("model", ""))
            span.set_attribute("jev.input_tokens", usage.input_tokens)
            span.set_attribute("jev.latency_ms", round(latency, 1))
            return JevResult(
                model=data.get("model", self.model),
                answers=parse_answers(data.get("answers") or {}),
                usage=usage,
                latency_ms=latency,
            )
