"""A Starlette/FastAPI response for a turn's SSE text."""

from __future__ import annotations

from collections.abc import Iterator

from starlette.responses import StreamingResponse

from ai_commerce_stream.sse import HEADERS


def sse_response(stream: Iterator[str], status_code: int = 200) -> StreamingResponse:
    """Sync iterators run in Starlette's threadpool, which suits the sync turn runner."""
    return StreamingResponse(
        stream, status_code=status_code, media_type="text/event-stream", headers=HEADERS
    )
