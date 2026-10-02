"""``pnpm tavus:setup``: make (or find) Xena's echo PAL on Tavus and print its id.

Nothing creates Tavus resources at runtime; this is the one explicit step. The PAL is echo
mode (Tavus renders the face; our pipeline supplies every word), with the microphone off
(the spike showed microphone echo doesn't speak, and the customer's voice never goes to
Tavus). Put the printed ``TAVUS_PAL_ID`` in ``.env`` with ``VOICE_AVATAR=tavus``.
"""

from __future__ import annotations

import sys
from typing import Any

import httpx

from ai_commerce_voice.config import get_settings
from ai_commerce_voice.face_tavus import TAVUS_API

# Tavus keeps only letters, digits and spaces in PAL names.
PAL_NAME = "Xana ai commerce echo"


def same_name(a: str | None, b: str) -> bool:
    def norm(t: str) -> str:
        return " ".join("".join(c if c.isalnum() else " " for c in t.lower()).split())

    return a is not None and norm(a) == norm(b)


def pal_request(face_id: str) -> dict[str, Any]:
    return {
        "pal_name": PAL_NAME,
        "pipeline_mode": "echo",
        "default_face_id": face_id,
        "layers": {"transport": {"input_settings": {"microphone": "disabled"}}},
    }


def main() -> int:
    s = get_settings()
    if not s.tavus_api_key:
        print("TAVUS_APIKEY isn't set in .env.", file=sys.stderr)
        return 1
    headers = {"x-api-key": s.tavus_api_key}
    with httpx.Client(base_url=TAVUS_API, headers=headers, timeout=20) as http:
        pals = http.get("/v2/pals", params={"limit": 100}).raise_for_status().json()
        for pal in pals.get("data", []):
            if (
                same_name(pal.get("pal_name"), PAL_NAME)
                and pal.get("default_face_id") == s.tavus_face_id
                and pal.get("pipeline_mode") == "echo"
            ):
                pal_id = pal["pal_id"]
                print(f"Found Xena's PAL for face {s.tavus_face_id}.")
                break
        else:
            made = http.post("/v2/pals", json=pal_request(s.tavus_face_id)).raise_for_status()
            pal_id = made.json()["pal_id"]
            print(f"Created Xena's PAL for face {s.tavus_face_id}.")
    print(f"TAVUS_PAL_ID={pal_id}")
    if s.tavus_pal_id != pal_id or s.voice_avatar != "tavus":
        print("Add these to .env:\n  VOICE_AVATAR=tavus\n  TAVUS_PAL_ID=" + pal_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
