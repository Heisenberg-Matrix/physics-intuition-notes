"""把背景音乐混到 manim-voiceover 的成片上，视频流直接复制。

    python mix_audio.py

人声已在 manim 渲染时写入 `media/.../SumOneToN.mp4`；这里只补一层
`media/bgm.wav`，并保证输出与视频等长、首尾有淡入淡出。
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from narration import BGM

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "media" / "videos" / "sum_one_to_n" / "1920p60" / "SumOneToN.mp4"
OUT = ROOT / "sum-1-to-n.mp4"
BGM_FILE = ROOT / "media" / BGM["file"]


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
    """按视频流时长计算（manim 的音频轨只到最后一句话，可能更短）。"""
    probe = subprocess.run(
        [find_ffmpeg(), "-hide_banner", "-i", str(path)],
        capture_output=True,
        text=True,
    )
    match = re.search(
        r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", probe.stderr
    )
    if not match:
        raise SystemExit("could not read video duration")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def main() -> None:
    duration = video_duration(RAW)

    if not BGM["enabled"] or not BGM_FILE.exists():
        shutil.copyfile(RAW, OUT)
        print(f"BGM disabled or missing; copied voice-only video to {OUT}")
        return

    fade_out_start = max(duration - BGM["fade_out"], 0.0)
    filter_complex = (
        f"[0:a]apad=whole_dur={duration:.3f}[vo];"
        f"[1:a]volume={BGM['gain_db']}dB,"
        f"afade=t=in:st=0:d={BGM['fade_in']},"
        f"afade=t=out:st={fade_out_start:.3f}:d={BGM['fade_out']}[bg];"
        "[vo][bg]amix=inputs=2:duration=first:normalize=0,"
        "alimiter=limit=0.95[a]"
    )
    command = [
        find_ffmpeg(),
        "-y",
        "-hide_banner",
        "-loglevel", "error",
        "-i", str(RAW),
        "-i", str(BGM_FILE),
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        str(OUT),
    ]
    subprocess.run(command, check=True)
    print(f"wrote {OUT} ({duration:.2f}s, BGM {BGM['gain_db']} dB)")


if __name__ == "__main__":
    main()
