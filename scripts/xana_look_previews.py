"""Make the look picker's previews: a short looping portrait clip and a poster per look.

Run from the repo root (needs TAVUS_APIKEY in .env and ffmpeg on PATH):
  uv run --directory services/voice python ../../scripts/xana_look_previews.py

For each face in ``ai_commerce_voice.config.LOOKS`` it reads the face's own preview video from
Tavus, cuts 3 seconds of it, crops a 4:5 portrait around her, and writes
``apps/web/public/xana/looks/<key>.mp4`` (silent, ~100 KB, loops like a GIF but far smaller)
and ``<key>.jpg`` (the first frame, for reduced motion and while the clip loads).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import httpx

from ai_commerce_voice.config import LOOKS, get_settings

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "apps/web/public/xana/looks"
# 4:5 portrait from the middle of the frame, 320x400, a little sharpened after scaling.
CROP = "crop=ih*4/5:ih,scale=320:400:flags=lanczos,unsharp=3:3:0.4"


def main() -> None:
    key = get_settings().tavus_api_key
    if not key:
        sys.exit("TAVUS_APIKEY isn't set.")
    OUT.mkdir(parents=True, exist_ok=True)
    with httpx.Client(
        base_url="https://tavusapi.com", headers={"x-api-key": key}, timeout=60
    ) as api:
        for look in LOOKS:
            face = api.get(f"/v2/faces/{look.face_id}").raise_for_status().json()
            url = face.get("thumbnail_video_url")
            if not url:
                print(f"{look.key}: no preview video, skipped")
                continue
            with tempfile.TemporaryDirectory() as tmp:
                src = Path(tmp) / "src.mp4"
                with httpx.stream("GET", url, timeout=120, follow_redirects=True) as r:
                    r.raise_for_status()
                    with src.open("wb") as f:
                        for chunk in r.iter_bytes():
                            f.write(chunk)
                clip, poster = OUT / f"{look.key}.mp4", OUT / f"{look.key}.jpg"
                ffmpeg("-ss", "1", "-t", "3", "-i", str(src), "-an", "-vf", f"{CROP},fps=24",
                       "-c:v", "libx264", "-preset", "slow", "-crf", "30", "-pix_fmt", "yuv420p",
                       "-movflags", "+faststart", str(clip))  # fmt: skip
                ffmpeg("-ss", "1", "-i", str(src), "-frames:v", "1", "-vf", CROP, "-q:v", "4",
                       str(poster))  # fmt: skip
            kb = clip.stat().st_size // 1024, poster.stat().st_size // 1024
            print(f"{look.key}: {kb[0]} KB clip, {kb[1]} KB poster")


def ffmpeg(*args: str) -> None:
    # Our own fixed arguments and file paths; ffmpeg from PATH (a local dev tool).
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)  # noqa: S603, S607


if __name__ == "__main__":
    main()
