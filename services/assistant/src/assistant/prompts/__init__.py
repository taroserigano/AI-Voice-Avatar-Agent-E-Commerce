"""Versioned system prompts. The version is part of the file name and is recorded on each turn."""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

PROMPT_DIR = Path(__file__).resolve().parent
PROMPT_VERSIONS = {"steph": "steph.v1", "xana": "xana.v2"}
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
    return text + (VOICE_NOTE if voice else "")
