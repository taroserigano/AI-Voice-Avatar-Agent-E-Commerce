import pytest

from ai_commerce_voice.config import VoiceSettings


@pytest.mark.parametrize(
    "name", ["LIVEAVATAR_API_KEY", "HEYGEN_LIVE_APIKEY", "HEYGEN_LIVE_API_KEY"]
)
def test_liveavatar_key_names_enable_the_configured_provider(name: str) -> None:
    settings = VoiceSettings(_env_file=None, voice_avatar="both", **{name: "fixture-key"})
    assert settings.liveavatar_api_key == "fixture-key"
    assert settings.heygen_ready
