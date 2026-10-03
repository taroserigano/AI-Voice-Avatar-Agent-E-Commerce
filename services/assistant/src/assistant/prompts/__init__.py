"""Versioned system prompts. The version is part of the file name and is recorded on each turn."""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

PROMPT_DIR = Path(__file__).resolve().parent
PROMPT_VERSIONS = {"steph": "steph.v1", "xana": "xana.v4"}
VOICE_NOTE = (
    "\n\n## This turn is spoken\n"
    "The customer is talking to you by voice. Answer in one or two short sentences with no "
    "lists, links, or symbols; the screen shows the details."
)


@lru_cache
def _template(version: str) -> str:
    return (PROMPT_DIR / f"{version}.md").read_text(encoding="utf-8")


def prompt_version(agent: str) -> str:
    return PROMPT_VERSIONS[agent]


def catalog_size(vocabulary: dict[str, Any]) -> str:
    """How big the catalog is, from the vocabulary's live counts, so "how many products do you
    have?" gets a real number instead of "I don't know". Empty when the counts are missing."""
    types = [t for t in vocabulary.get("product_types", []) if t.get("count")]
    if not types:
        return ""
    total = sum(int(t["count"]) for t in types)
    per_type = ", ".join(f"{t['value']} {t['count']}" for t in types)
    return (
        "\n\n## Catalog size\n"
        f"The store lists {total} products right now, across {len(types)} product types. "
        "A product can come in several sizes or colors, and listed doesn't mean in stock. "
        "When the customer asks how many products the store has, or how many of a kind, answer "
        "with these numbers. "
        f"Products per type: {per_type}."
    )


def render_prompt(
    agent: str, *, first_name: str, vocabulary: dict[str, Any], today: date, voice: bool = False
) -> str:
    types = ", ".join(t["value"] for t in vocabulary.get("product_types", []))
    tags = "\n".join(f"- {t['value']}: {t['label']}" for t in vocabulary.get("tags", []))
    text = (
        _template(prompt_version(agent))
        .replace("{first_name}", first_name or "the customer")
        .replace("{today}", today.strftime("%A, %B %d, %Y"))
        .replace("{product_types}", types)
        .replace("{tags}", tags)
    )
    return text + catalog_size(vocabulary) + (VOICE_NOTE if voice else "")
