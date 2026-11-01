"""Trim a take to the conversation, keeping every pause as recorded: python cut_full.py <out dir> <output name> [lead=1.5] [tail=1.5]

Nothing inside the conversation is shortened; only the setup before the first question and
the idle time after the last answer are cut.
"""

import json
import subprocess
import sys
from pathlib import Path

name, output = sys.argv[1], sys.argv[2]
LEAD = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5
TAIL = float(sys.argv[4]) if len(sys.argv) > 4 else 1.5
d = Path(__file__).parent / "out" / name
m = json.loads((d / "marks.json").read_text())
rec = m["recAt"]
first_q = (m["turns"][0]["question"] - rec) / 1000
end = (m["end"] - rec) / 1000
if not (d / "full.mp4").exists():
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", "frames.txt",
         "-i", "audio.webm", "-vf", "fps=30,scale=1920:1080:flags=lanczos,format=yuv420p", "-c:v", "libx264",
         "-preset", "medium", "-crf", "17", "-c:a", "aac", "-b:a", "192k", "full.mp4"],
        cwd=d, check=True,
    )
t0 = max(0.0, first_q - LEAD)
dur = end - t0 - (1.5 - TAIL)
subprocess.run(
    ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t0:.3f}", "-i", "full.mp4", "-t", f"{dur:.3f}",
     "-vf", f"fade=t=in:st=0:d=0.35,fade=t=out:st={dur - 0.5:.3f}:d=0.5",
     "-af", f"afade=t=in:st=0:d=0.2,afade=t=out:st={dur - 0.5:.3f}:d=0.5",
     "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
     "-movflags", "+faststart", output],
    cwd=d, check=True,
)
print(d / output, round(dur, 2), "s")
