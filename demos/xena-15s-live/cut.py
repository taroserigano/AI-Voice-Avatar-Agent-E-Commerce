"""Mux a take and cut it around the conversation: python cut.py <out dir> [seconds, default 15]"""

import json
import re
import subprocess
import sys
from pathlib import Path

name = sys.argv[1]
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 15.0
mode = "avatar" if name.startswith("avatar") else "voice"
d = Path(__file__).parent / "out" / name
m = json.loads((d / "marks.json").read_text())
rec = m["recAt"]
rel = {k: (v - rec) / 1000 for k, v in m.items() if isinstance(v, (int, float)) and k != "questionSeconds"}
full = d / "full.mp4"
subprocess.run(
    ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", "frames.txt",
     "-i", "audio.webm", "-vf", "fps=30,scale=1920:1080:flags=lanczos,format=yuv420p", "-c:v", "libx264",
     "-preset", "medium", "-crf", "17", "-c:a", "aac", "-b:a", "192k", full.name],
    cwd=d, check=True,
)
probe = subprocess.run(
    ["ffmpeg", "-hide_banner", "-i", full.name, "-af", "silencedetect=n=-45dB:d=0.35", "-f", "null", "-"],
    cwd=d, capture_output=True, text=True,
).stderr
ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", probe)]
starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", probe)]
speech_from = next(e for e in ends if e > rel["question"] - 0.5)  # the question begins
speech_to = max(s for s in starts if s < rel["end"])  # Xena's last word
span = speech_to - speech_from
lead = max(0.6, (DUR - span) * 0.6)
# Voice: start on the orb before the call so the Start tap is in shot, if it fits.
if mode == "voice" and speech_to - (rel["start"] - 0.6) <= DUR - 0.4:
    lead = speech_from - (rel["start"] - 0.6)
t0 = max(0.0, speech_from - lead)
if t0 + DUR < speech_to + 0.3:
    print(f"warning: speech runs {speech_to - t0 - DUR:.2f}s past the cut")
print(f"{mode}: question {speech_from:.2f}s, last word {speech_to:.2f}s, span {span:.2f}s, cut {t0:.2f}-{t0 + DUR:.2f}")
out = d / f"xena-{mode}-{int(DUR)}s.mp4"
subprocess.run(
    ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t0:.3f}", "-i", full.name, "-t", f"{DUR:g}",
     "-vf", f"fade=t=in:st=0:d=0.35,fade=t=out:st={DUR - 0.5:g}:d=0.5",
     "-af", f"afade=t=in:st=0:d=0.2,afade=t=out:st={DUR - 0.5:g}:d=0.5",
     "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
     "-movflags", "+faststart", out.name],
    cwd=d, check=True,
)
for s in [round(DUR * f, 1) for f in (0.05, 0.25, 0.45, 0.65, 0.85, 0.97)]:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(s), "-i", out.name,
                    "-frames:v", "1", "-vf", "scale=960:-1", f"p_{s}.png"], cwd=d, check=True)
print(out)
