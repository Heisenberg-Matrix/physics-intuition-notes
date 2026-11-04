"""把轻微音效混到 manim-voiceover 的成片上，视频流直接复制。

    python make_sfx.py      # 首次或想改音效时
    python mix_audio.py

音效时间点来自渲染时写出的 media/timeline.json，再按 narration.py 的 CUES
加上阶段内偏移。没有背景音乐，只在关键变化处点缀。
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from narration import CUES, SFX_GAIN_DB

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "media" / "videos" / "diagonal_sum" / "1920p60" / "DiagonalSum.mp4"
TIMELINE = ROOT / "media" / "timeline.json"
SFX_DIR = ROOT / "media" / "sfx"
OUT = ROOT / "diagonal-sum.mp4"


def find_ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    # 本仓库把 imageio-ffmpeg 的二进制放在了虚拟环境的 Scripts 下
    candidate = Path(sys.executable).with_name("ffmpeg.exe")
    if candidate.exists():
        return str(candidate)
    raise SystemExit("ffmpeg not found; put it on PATH or in .venv/Scripts")


def video_duration(path: Path) -> float:
    probe = subprocess.run(
        [find_ffmpeg(), "-hide_banner", "-i", str(path)],
        capture_output=True,
        text=True,
    )
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", probe.stderr)
    if not match:
        raise SystemExit("could not read video duration")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def cue_times(duration: float) -> list[tuple[float, str]]:
    if not TIMELINE.exists():
        raise SystemExit(f"missing {TIMELINE}; render the scene first")
    timeline = json.loads(TIMELINE.read_text(encoding="utf-8"))
    cues = []
    for stage, offset, sound in CUES:
        if stage not in timeline:
            print(f"skip cue {stage}/{sound}: stage not in timeline")
            continue
        if not (SFX_DIR / f"{sound}.wav").exists():
            print(f"skip cue {stage}/{sound}: missing {sound}.wav")
            continue
        moment = timeline[stage]["start"] + offset
        if 0 <= moment < duration:
            cues.append((moment, sound))
    return cues


def main() -> None:
    duration = video_duration(RAW)
    cues = cue_times(duration)

    if not cues:
        shutil.copyfile(RAW, OUT)
        print(f"no sound cues; copied voice-only video to {OUT}")
        return

    inputs = [find_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error"]
    inputs += ["-i", str(RAW)]
    filters = [f"[0:a]apad=whole_dur={duration:.3f}[vo]"]
    labels = ["[vo]"]

    for index, (moment, sound) in enumerate(cues, start=1):
        inputs += ["-i", str(SFX_DIR / f"{sound}.wav")]
        delay_ms = round(moment * 1000)
        gain = SFX_GAIN_DB[sound]
        filters.append(
            f"[{index}:a]volume={gain}dB,"
            f"adelay={delay_ms}:all=1,"
            f"apad=whole_dur={duration:.3f}[sfx{index}]"
        )
        labels.append(f"[sfx{index}]")

    mix = "".join(labels) + (
        f"amix=inputs={len(labels)}:duration=first:normalize=0,"
        "alimiter=limit=0.95[a]"
    )
    filters.append(mix)

    command = inputs + [
        "-filter_complex",
        ";".join(filters),
        "-map",
        "0:v",
        "-map",
        "[a]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(OUT),
    ]
    subprocess.run(command, check=True)

    print(f"wrote {OUT} ({duration:.2f}s, {len(cues)} sound cues)")
    for moment, sound in cues:
        print(f"  {moment:6.2f}s  {sound}")


if __name__ == "__main__":
    main()
