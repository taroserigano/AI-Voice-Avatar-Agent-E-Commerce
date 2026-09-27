"""The System One API's request and answer shapes (``POST /v1/systemone``)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Noul(BaseModel):
    type: Literal["noul"] = "noul"
    instructions: str | dict[str, Any]
    criteria: dict[str, str] | None = None  # {"true": ..., "false": ...}


class Choice(BaseModel):
    type: Literal["choice"] = "choice"
    instructions: str | dict[str, Any]
    criteria: dict[str, str | None]  # option -> description (max 255 options)


class Score(BaseModel):
    type: Literal["score"] = "score"
    instructions: str | dict[str, Any]
    criteria: list[str]  # ordered levels, 2-10


Question = Noul | Choice | Score


class NoulAnswer(BaseModel):
    type: Literal["noul"] = "noul"
    noul: float = Field(ge=0, le=1)


class ChoiceAnswer(BaseModel):
    type: Literal["choice"] = "choice"
    choice: str
    probabilities: dict[str, float]
    confidence: float = Field(ge=0, le=1)


class ScoreAnswer(BaseModel):
    type: Literal["score"] = "score"
    score: float
    probabilities: dict[str, float] = Field(default_factory=dict)
    confidence: float = Field(ge=0, le=1)


Answer = NoulAnswer | ChoiceAnswer | ScoreAnswer


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class JevResult(BaseModel):
    model: str
    answers: dict[str, Answer]
    usage: Usage = Field(default_factory=Usage)
    latency_ms: float = 0.0
    simulated: bool = False


def parse_answers(raw: dict[str, Any]) -> dict[str, Answer]:
    out: dict[str, Answer] = {}
    for key, value in raw.items():
        kind = value.get("type")
        if kind == "noul":
            out[key] = NoulAnswer.model_validate(value)
        elif kind == "choice":
            out[key] = ChoiceAnswer.model_validate(value)
        elif kind == "score":
            out[key] = ScoreAnswer.model_validate(value)
    return out
