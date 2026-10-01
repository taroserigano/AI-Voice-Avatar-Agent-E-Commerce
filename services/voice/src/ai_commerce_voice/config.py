"""Voice agent settings, read from the environment and the repo-root ``.env``."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]

# Cartesia's "Skylar - Friendly Guide": approachable American English, made for support.
SKYLAR = "db6b0ed5-d5d3-463d-ae85-518a07d3c2b4"
# Tavus stock face "Rose - Business" (Phoenix-4.5): Taro asked for a customer-support look
# (2026-09-30; it replaced "Anna - Casual", rc9cff32ceba).
ROSE = "rf1bd7e252de"


@dataclass(frozen=True)
class Look:
    """A face the customer can pick for Xana. Phoenix-4 faces, because Tavus's green screen
    (which lets the browser put a light background behind her) doesn't work on Phoenix-4.5."""

    key: str
    label: str
    face_id: str
    greenscreen: bool = True


# Taro (2026-09-30): pick the look and the background from tabs on the screen.
LOOKS: tuple[Look, ...] = (
    Look("rose", "Rose", "r6c7a6cb6d9b"),
    Look("margo", "Margo", "r78c9b897fbc"),
    Look("julia", "Julia", "rd27826c12a6"),
    Look("helen", "Helen", "r12d3eb75ec2"),
    Look("miranda", "Miranda", "r3cb75621574"),
)


class VoiceSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: Literal["dev", "test", "ci", "staging", "prod"] = "dev"
    voice_host: str = "127.0.0.1"
    voice_port: int = Field(default=8103, validation_alias=AliasChoices("VOICE_PORT"))
    # Browsers that may open the socket (cross-site WebSocket hijacking guard). The web app's
    # own origin in dev; set it explicitly elsewhere.
    voice_allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3100",
        "http://localhost:3200",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3100",
    ]

    # Who the customer is: the commerce API checks the session cookie.
    commerce_api_url: str = Field(
        default="http://127.0.0.1:8000", validation_alias="COMMERCE_API_URL"
    )
    session_cookie_name: str = "ac_session"

    # Speech out: Cartesia Sonic, streamed over one WebSocket per session.
    cartesia_api_key: str | None = Field(
        default=None, validation_alias=AliasChoices("CARTESIA_SONIC_API_KEY", "CARTESIA_API_KEY")
    )
    cartesia_model: str = "sonic-3.6-2026-08-27"
    cartesia_version: str = "2026-08-14"
    cartesia_voice_id: str = SKYLAR
    cartesia_voice_name: str = "Skylar"

    # Speech in and the model: OpenAI (decision 22).
    openai_api_key: str | None = Field(
        default=None, validation_alias=AliasChoices("OPEN_AI_API", "OPENAI_API_KEY")
    )
    voice_stt_model: str = "gpt-live-transcribe"
    voice_llm_model: str = "gpt-6-luna"
    # Low effort answers simple questions from the orders snapshot instead of calling a tool
    # (measured: effort "none" looked up an order it already had). Priority processing took
    # the first token from ~600-950 ms to ~450-590 ms (2026-09-26).
    voice_llm_reasoning: Literal["none", "low", "medium"] = "low"
    voice_llm_service_tier: Literal["default", "priority", "flex"] = "priority"
    # "auto": the real model when a key is set, the labeled scripted one otherwise.
    voice_llm_mode: Literal["auto", "openai", "scripted"] = "auto"
    # The stronger model for the turns code escalates (decision 26, ai_commerce_voice.escalation).
    # Empty: Luna answers every turn.
    voice_escalation_model: str = "gpt-6-sol"
    voice_escalation_reasoning: Literal["none", "low", "medium"] = "low"

    # Xana's face: a Tavus avatar in echo mode (docs/features/10-xana-avatar). Off unless
    # VOICE_AVATAR=tavus and a key and PAL are set; the customer still turns it on per call.
    voice_avatar: Literal["off", "tavus"] = "off"
    tavus_api_key: str | None = Field(
        default=None, validation_alias=AliasChoices("TAVUS_APIKEY", "TAVUS_API_KEY")
    )
    # The echo PAL made by `pnpm tavus:setup`.
    tavus_pal_id: str | None = None
    tavus_face_id: str = ROSE
    # Avatars at once across this process (the Tavus account's limits; each one bills).
    tavus_max_live: int = 2
    # The look a call starts with (a key of LOOKS); the customer can switch on screen.
    tavus_default_look: str = "rose"
    # Tavus doesn't join or bill test-mode conversations (tests only).
    tavus_test_mode: bool = False

    # Turn-taking. Silence that ends the customer's turn (server VAD), and how long Xana waits
    # for answer audio before saying a filler.
    voice_end_silence_ms: int = 450
    voice_filler_after_ms: int = 900
    voice_max_turn_s: float = 45.0
    voice_max_tool_calls: int = 6
    voice_max_session_s: int = 20 * 60

    @property
    def avatar_ready(self) -> bool:
        return self.voice_avatar == "tavus" and bool(self.tavus_api_key and self.tavus_pal_id)

    @property
    def is_dev(self) -> bool:
        return self.app_env in ("dev", "test", "ci")


@lru_cache
def get_settings() -> VoiceSettings:
    return VoiceSettings()
