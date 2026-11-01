"""The customer's spoken question for the demo, from Cartesia (a different voice from Xena's).

  python tts.py list               -> a few English voices
  python tts.py say VOICE_ID "text" out.wav [lead_s] [tail_s]
"""

import io
import sys
import wave
from pathlib import Path

import httpx

ENV = Path(r"C:\Users\taro\Documents\TEMP\Walmart App\ai-commerce\.env")
KEY = next(
    line.split("=", 1)[1].strip()
    for line in ENV.read_text(encoding="utf-8").splitlines()
    if line.startswith(__import__("os").environ.get("CARTESIA_KEY_NAME", "CARTESIA_SONIC_API_KEY") + "=")
)
H = {"X-API-Key": KEY, "Cartesia-Version": "2026-08-14"}
RATE = 48_000

if sys.argv[1] == "list":
    r = httpx.get("https://api.cartesia.ai/voices", headers=H, params={"limit": 100}, timeout=30)
    r.raise_for_status()
    body = r.json()
    voices = body.get("data", body) if isinstance(body, dict) else body
    for v in voices:
        if v.get("language", "en") == "en":
            print(v["id"], "|", v.get("name"), "|", (v.get("description") or "")[:90])
    sys.exit()

_, _, voice, text, out, *pad = sys.argv
lead, tail = (float(pad[0]) if pad else 0.8), (float(pad[1]) if len(pad) > 1 else 60.0)
r = httpx.post(
    "https://api.cartesia.ai/tts/bytes",
    headers=H,
    json={
        "model_id": "sonic-3.6-2026-08-27",
        "transcript": text,
        "voice": {"mode": "id", "id": voice},
        "output_format": {"container": "raw", "encoding": "pcm_s16le", "sample_rate": RATE},
        "language": "en",
        **({"generation_config": {"speed": float(__import__("os").environ["SPEED"])}} if __import__("os").environ.get("SPEED") else {}),
    },
    timeout=60,
)
r.raise_for_status()
pcm = r.content
silence = lambda s: b"\x00\x00" * int(RATE * s)  # noqa: E731
with wave.open(out, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(RATE)
    w.writeframes(silence(lead) + pcm + silence(tail))
print(f"{out}: speech {len(pcm) / 2 / RATE:.2f}s, lead {lead}s")
