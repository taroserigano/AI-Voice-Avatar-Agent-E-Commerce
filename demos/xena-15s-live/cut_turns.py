"""Cut a multi-question take to an exact length: python cut_turns.py <out dir> [seconds=30]

Only the customer's pause before each next question is shortened (to GAP seconds). Xena's
response time after every question is kept exactly as recorded.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

GAP = 0.3
name = sys.argv[1]
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
mode = "avatar" if name.startswith("avatar") else "voice"
d = Path(__file__).parent / "out" / name
m = json.loads((d / "marks.json").read_text())
rec = m["recAt"]
qs = [(t["question"] - rec) / 1000 for t in m["turns"]]
end = (m["end"] - rec) / 1000
if not (d / "full.mp4").exists():
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", "frames.txt",
         "-i", "audio.webm", "-vf", "fps=30,scale=1920:1080:flags=lanczos,format=yuv420p", "-c:v", "libx264",
         "-preset", "medium", "-crf", "17", "-c:a", "aac", "-b:a", "192k", "full.mp4"],
        cwd=d, check=True,
    )
probe = subprocess.run(
    ["ffmpeg", "-hide_banner", "-i", "full.mp4", "-af", "silencedetect=n=-45dB:d=0.25", "-f", "null", "-"],
    cwd=d, capture_output=True, text=True,
).stderr
sil = list(zip([float(x) for x in re.findall(r"silence_start: ([0-9.]+)", probe)],
               [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", probe)] + [end]))
# Each question's first sound, and the silence just before it (the customer's pause).
starts = []
for q in qs:
    s = next(e for _, e in sil if e > q - 0.3)
    starts.append(s)
segments = []
lead = 0.35
cur = starts[0] - lead
for s in starts[1:]:
    pause = next((a, b) for a, b in sil if a < s <= b + 0.01)
    cut_at = min(pause[0] + GAP / 2, s)
    segments.append((cur, cut_at))
    cur = max(cut_at, s - GAP / 2)
last_word = max(a for a, _ in sil if a < end)
segments.append((cur, end))
total = sum(b - a for a, b in segments)
# Fit to DUR: end the last segment so the whole is exactly DUR.
over = total - DUR
segments[-1] = (segments[-1][0], segments[-1][1] - over)
tail = segments[-1][1] - last_word
print(f"{name}: segments {[(round(a, 2), round(b, 2)) for a, b in segments]}; after the last word {tail:.2f}s")
if tail < 0.25:
    print("warning: the last word is cut")
parts, labels = [], []
for i, (a, b) in enumerate(segments):
    parts.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}];"
                 f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{i}];")
    labels.append(f"[v{i}][a{i}]")
graph = "".join(parts) + "".join(labels) + f"concat=n={len(segments)}:v=1:a=1[vc][ac];" \
    f"[vc]fade=t=in:st=0:d=0.3,fade=t=out:st={DUR - 0.4:g}:d=0.4[v];" \
    f"[ac]afade=t=in:st=0:d=0.15,afade=t=out:st={DUR - 0.3:g}:d=0.3[a]"
out = d / f"xena-{mode}-{int(DUR)}s.mp4"
subprocess.run(
    ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", "full.mp4", "-filter_complex", graph,
     "-map", "[v]", "-map", "[a]", "-t", f"{DUR:g}", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
     "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out.name],
    cwd=d, check=True,
)
for s in [round(DUR * f, 1) for f in (0.03, 0.22, 0.4, 0.58, 0.76, 0.97)]:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(s), "-i", out.name,
                    "-frames:v", "1", "-vf", "scale=960:-1", f"p_{s}.png"], cwd=d, check=True)
dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out.name],
                     cwd=d, capture_output=True, text=True).stdout.strip()
print(out, dur)
