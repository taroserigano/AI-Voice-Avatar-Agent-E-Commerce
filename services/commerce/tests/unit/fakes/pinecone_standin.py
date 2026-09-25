"""A stand-in for the Pinecone index client, for pure unit tests ONLY.

Decision (2026-09-25): only unit tests may stub Pinecone, at the adapter boundary. This file
lives under ``tests/unit/`` so no app code can import it, and ``test_no_standin_in_app.py``
fails CI if anything under ``src/`` tries. It does not embed anything: "search" returns
records in a fixed order with scripted scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any


@dataclass
class PineconeIndexStandIn:
    scripted_hits: list[tuple[str, float]] = field(default_factory=list)
    upsert_calls: list[tuple[str, list[dict[str, Any]]]] = field(default_factory=list)
    delete_calls: list[dict[str, Any]] = field(default_factory=list)
    search_calls: list[dict[str, Any]] = field(default_factory=list)

    def upsert_records(self, *, records: list[dict[str, Any]], namespace: str) -> None:
        if len(records) > 96:
            raise ValueError("Pinecone rejects more than 96 records per integrated upsert")
        self.upsert_calls.append((namespace, records))

    def search(self, *, namespace: str, top_k: int, inputs: dict[str, Any], **kw: Any) -> Any:
        self.search_calls.append({"namespace": namespace, "top_k": top_k, "inputs": inputs, **kw})
        hits = [SimpleNamespace(id=i, score=s, fields={}) for i, s in self.scripted_hits[:top_k]]
        return SimpleNamespace(result=SimpleNamespace(hits=hits))

    def delete(
        self, *, ids: list[str] | None = None, delete_all: bool = False, namespace: str = ""
    ) -> None:
        self.delete_calls.append({"ids": ids, "delete_all": delete_all, "namespace": namespace})
