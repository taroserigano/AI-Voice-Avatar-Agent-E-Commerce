"""Approved policy documents (``content/policies/*.md``), split into citable sections.

Each document has YAML front matter (id, title, version, effective date, and optionally a
``section_prefix``). Numbered headings become sections with stable IDs: with prefix ``rr``,
``## 7. How much you get back`` is ``rr-7`` and ``### 7.2 Splitting discounts`` is ``rr-7-2``.
The web page uses the same IDs as anchors, and the assistant cites them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from commerce.config import REPO_ROOT

POLICY_DIR = REPO_ROOT / "content" / "policies"

_FRONT_MATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
_HEADING = re.compile(r"^(#{2,3})\s+(\d+)(?:\.(\d+))?\.?\s+(.+?)\s*$")


@dataclass(frozen=True)
class PolicySection:
    doc_id: str
    section_id: str  # "rr-7-2", or "" for an unnumbered document's single section
    number: str  # "7.2"
    title: str
    parent_title: str | None  # the "## 7." title for a "### 7.2" section
    body: str  # markdown, without the heading

    @property
    def anchor(self) -> str:
        return self.section_id


@dataclass(frozen=True)
class PolicyDocument:
    id: str
    title: str
    version: str
    effective_date: date
    status: str
    section_prefix: str | None
    summary: tuple[str, ...]
    rules: dict[str, Any]
    intro: str  # markdown before the first numbered heading
    sections: tuple[PolicySection, ...] = field(default=())

    def section(self, section_id: str) -> PolicySection:
        for s in self.sections:
            if s.section_id == section_id:
                return s
        raise KeyError(f"{self.id} has no section {section_id!r}")


def parse_policy(text: str) -> PolicyDocument:
    match = _FRONT_MATTER.match(text)
    if not match:
        raise ValueError("policy document has no front matter")
    meta: dict[str, Any] = yaml.safe_load(match.group(1)) or {}
    body = text[match.end() :]
    prefix = meta.get("section_prefix")

    intro_lines: list[str] = []
    sections: list[PolicySection] = []
    current: dict[str, Any] | None = None
    parent_title: str | None = None

    def close() -> None:
        if current is not None:
            sections.append(
                PolicySection(
                    doc_id=meta["id"],
                    section_id=current["id"],
                    number=current["number"],
                    title=current["title"],
                    parent_title=current["parent"],
                    body="\n".join(current["lines"]).strip(),
                )
            )

    for line in body.splitlines():
        heading = _HEADING.match(line) if prefix else None
        if heading:
            close()
            level, major, minor, title = heading.groups()
            if level == "##":
                parent_title = title
            number = f"{major}.{minor}" if minor else major
            section_id = f"{prefix}-{major}" + (f"-{minor}" if minor else "")
            current = {
                "id": section_id,
                "number": number,
                "title": title,
                "parent": parent_title if level == "###" else None,
                "lines": [],
            }
        elif current is None:
            intro_lines.append(line)
        else:
            current["lines"].append(line)
    close()

    if not prefix:
        # An unnumbered document is one citable section.
        intro = "\n".join(intro_lines).strip()
        sections = [PolicySection(meta["id"], "", "", meta["title"], None, _strip_h1(intro))]

    return PolicyDocument(
        id=meta["id"],
        title=meta["title"],
        version=str(meta["version"]),
        effective_date=meta["effective_date"],
        status=str(meta.get("status", "")),
        section_prefix=prefix,
        summary=tuple(meta.get("summary") or ()),
        rules=dict(meta.get("rules") or {}),
        intro=_strip_h1("\n".join(intro_lines).strip()),
        sections=tuple(sections),
    )


def _strip_h1(markdown: str) -> str:
    return re.sub(r"\A#\s+.*(?:\r?\n)+", "", markdown).strip()


@lru_cache
def load_policies(directory: Path = POLICY_DIR) -> dict[str, PolicyDocument]:
    docs = [parse_policy(p.read_text(encoding="utf-8")) for p in sorted(directory.glob("*.md"))]
    return {d.id: d for d in docs}


def load_policy(doc_id: str) -> PolicyDocument:
    return load_policies()[doc_id]
