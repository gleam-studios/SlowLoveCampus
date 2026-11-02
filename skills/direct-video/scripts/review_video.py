#!/usr/bin/env python3
"""Create technical metadata and timestamped visual-review evidence, not a taste score."""
import argparse
from fractions import Fraction
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont


def run(args):
    return subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def frame(path, t, width):
    raw = run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.6f}",
        "-i", str(path), "-map", "0:v:0", "-frames:v", "1", "-vf", f"scale={width}:-1",
        "-f", "image2pipe", "-vcodec", "png", "pipe:1",
    ]).stdout
    return Image.open(io.BytesIO(raw)).convert("RGB")


def sheet(path, times, output, width, cols):
    frames = [(t, frame(path, t, width)) for t in times]
    height = max(im.height for _, im in frames)
    font = ImageFont.load_default(size=14)
    gap, label = 8, 24
    rows = math.ceil(len(frames) / cols)
    canvas = Image.new("RGB", (cols * (width + gap) + gap, rows * (height + label + gap) + gap), "#151719")
    draw = ImageDraw.Draw(canvas)
    for i, (t, im) in enumerate(frames):
        x = gap + (i % cols) * (width + gap)
        y = gap + (i // cols) * (height + label + gap)
        canvas.paste(im, (x, y))
        draw.text((x + 4, y + height + 4), f"{t:.3f}s", font=font, fill="white")
    canvas.save(output, quality=92)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--samples", type=int, default=12)
    ap.add_argument("--cuts", default="", help="Comma-separated cut/event seconds; sample ±5 frames")
    ap.add_argument("--width", type=int, default=360)
    args = ap.parse_args()
    if not args.video.is_file():
        ap.error("Input video does not exist")
    if not 2 <= args.samples <= 48 or not 160 <= args.width <= 1920:
        ap.error("samples must be 2–48 and width 160–1920")
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            ap.error(f"Missing dependency: {tool}")
    try:
        cuts = [float(x.strip()) for x in args.cuts.split(",") if x.strip()]
    except ValueError:
        ap.error("cuts must be comma-separated numbers")
    if len(cuts) > 12 or not all(math.isfinite(t) for t in cuts):
        ap.error("Use at most 12 finite event times")
    info = json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(args.video)]).stdout)
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
    if video is None:
        ap.error("No video stream")
    duration = float(video.get("duration") or info.get("format", {}).get("duration") or 0)
    if duration <= 0:
        ap.error("Cannot establish positive video duration")
    rate = video.get("avg_frame_rate", "0/0")
    try:
        fps = float(Fraction(rate))
    except (ZeroDivisionError, ValueError):
        fps = 0
    if fps <= 0:
        ap.error("Cannot establish frame rate; inspect input manually")
    if any(t < 0 or t >= duration for t in cuts):
        ap.error("Event times must lie within [0,duration)")
    args.out.mkdir(parents=True, exist_ok=True)
    last = max(0, duration - max(1 / fps, .04))
    times = [last * i / (args.samples - 1) for i in range(args.samples)]
    sheet(args.video, times, args.out / "contact-sheet.jpg", args.width, 4)
    event_records = []
    for i, t in enumerate(cuts):
        stamps = sorted(set(round(min(last, max(0, t + k / fps)), 6) for k in range(-5, 6)))
        name = f"event-{i+1:02d}-{t:.3f}s.jpg"
        sheet(args.video, stamps, args.out / name, min(args.width, 320), 4)
        event_records.append({"time": t, "sample_times": stamps, "sheet": name})
    decode = subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(args.video),
        "-map", "0:v:0", "-map", "0:a?", "-f", "null", "-",
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    errors = decode.stderr.decode(errors="replace").strip()
    input_ref = Path(os.path.relpath(args.video.resolve(), Path(__file__).resolve().parents[3])).as_posix()
    if isinstance(info.get("format"), dict):
        info["format"]["filename"] = input_ref
    report = {
        "path_base": "project", "input": input_ref, "duration_seconds": duration, "fps_average": fps,
        "size": [video.get("width"), video.get("height")], "pixel_format": video.get("pix_fmt"),
        "sample_aspect_ratio": video.get("sample_aspect_ratio"),
        "color_space": video.get("color_space"), "color_transfer": video.get("color_transfer"),
        "audio_stream_count": sum(s.get("codec_type") == "audio" for s in info.get("streams", [])),
        "decode_status": "PASS" if decode.returncode == 0 and not errors else "REPAIR",
        "decode_messages": errors, "sample_times": times, "events": event_records,
        "visual_review": "UNVERIFIED: inspect sheets and actual motion",
        "audio_review": "UNVERIFIED: stream presence is not listening or sync verification",
        "note": "For VFR, avg fps is only a sampling estimate; inspect actual timestamps for frame-accurate cuts.",
    }
    (args.out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (args.out / "probe.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"out": str(args.out.resolve()), "decode": report["decode_status"], "duration": duration, "size": report["size"], "audio_streams": report["audio_stream_count"]}))
    return 0 if report["decode_status"] == "PASS" else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as exc:
        print(exc.stderr.decode(errors="replace") if exc.stderr else str(exc), file=sys.stderr)
        sys.exit(2)
