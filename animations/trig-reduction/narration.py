"""中文配音：用 edge-tts 逐句合成，按字幕时间铺进 54 秒音轨。

画面已经由 scene.py 渲染成无声 MP4；这里只负责声音：
1. 读取 scene.py 的 CUES（字幕文本 + 名义起始时间）；
2. 每句单独合成，缓存到 media/voice/；
3. 用实测的字幕淡入时刻把语音依次排好（不重叠，允许最多晚 0.4 秒）；
4. 输出 48 kHz 单声道 WAV，交给 run.sh 与视频合成为 AAC。

edge-tts 需要联网。改文案只需改 scene.py 的 CUES，然后重跑本脚本。
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import re
import subprocess
import sys
import wave
from pathlib import Path

import edge_tts
import numpy as np

from scene import CUES, TOTAL

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "+4%"
PITCH = "+0Hz"
VOLUME = "+0%"
SR = 48_000
FADE = 0.02          # 每句首尾 20 ms 淡入淡出，避免爆音
GAP = 0.10           # 相邻两句之间的最小空隙
MAX_LAG = 0.45       # 语音最多比字幕晚多少秒

# 字幕实际淡入完成的时刻（取自 scene.py 的渲染日志）。
# 画面是确定性渲染，重跑 scene.py 后这些值保持不变。
ONSETS = {
    "hook1": 0.40,
    "hook2": 3.97,
    "circle": 6.40,
    "circle_coords": 9.37,
    "half_q": 14.47,
    "half_a": 18.97,
    "neg_q": 26.63,
    "neg_a": 30.27,
    "combine1": 36.53,
    "combine2": 41.83,
    "reveal": 47.53,
}

# 中文课堂读法：cos → 扣赛因，sin → 赛因。
PRONOUNCE = [
    (re.compile(r"(?<![A-Za-z])cos(?![A-Za-z])"), "扣赛因"),
    (re.compile(r"(?<![A-Za-z])sin(?![A-Za-z])"), "赛因"),
]


def speakable(text: str) -> str:
    for pattern, spoken in PRONOUNCE:
        text = pattern.sub(spoken, text)
    return text


def find_ffmpeg() -> str:
    import shutil

    found = shutil.which("ffmpeg")
    if found:
        return found
    for candidate in (
        REPO / ".venv" / "Scripts" / "ffmpeg.exe",
        REPO / ".venv" / "bin" / "ffmpeg",
    ):
        if candidate.exists():
            return str(candidate)
    raise SystemExit("找不到 ffmpeg：请安装 FFmpeg 或放到 .venv/Scripts/ffmpeg.exe")


def cache_path(key: str, text: str) -> Path:
    digest = hashlib.sha1(f"{text}|{VOICE}|{RATE}|{PITCH}".encode("utf-8")).hexdigest()[:10]
    return ROOT / "media" / "voice" / f"{key}-{digest}.mp3"


async def synthesize(text: str, path: Path) -> None:
    """合成一句；网络抖动时最多重试 3 次。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    last: Exception | None = None
    for attempt in range(3):
        try:
            await edge_tts.Communicate(
                text, VOICE, rate=RATE, pitch=PITCH, volume=VOLUME
            ).save(str(path))
            return
        except Exception as exc:  # noqa: BLE001 - edge-tts 的网络异常类型不固定
            last = exc
            print(f"[voice] {path.stem} 第 {attempt + 1} 次失败：{exc!r}", flush=True)
            await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"合成失败：{path.stem}") from last


def decode(path: Path, ffmpeg: str) -> np.ndarray:
    """把 MP3 解成 48 kHz 单声道 float32，返回 [-1, 1]。"""
    raw = subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-i",
            str(path),
            "-f",
            "s16le",
            "-ac",
            "1",
            "-ar",
            str(SR),
            "-",
        ],
        capture_output=True,
        check=True,
    ).stdout
    pcm = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    return pcm


def build_voiceover(ffmpeg: str) -> tuple[np.ndarray, list[tuple[str, float, float]]]:
    lines = [(key, CUES[key][1]) for key in CUES]
    track = np.zeros(int(round(TOTAL * SR)), dtype=np.float32)
    placed: list[tuple[str, float, float]] = []
    cursor = 0.0

    for key, subtitle in lines:
        spoken = speakable(subtitle)
        path = cache_path(key, spoken)
        if not path.exists():
            print(f"[voice] synth {key}: {spoken}", flush=True)
            asyncio.run(synthesize(spoken, path))
        audio = decode(path, ffmpeg)

        start = max(ONSETS[key], cursor)
        lag = start - ONSETS[key]
        if lag > MAX_LAG:
            print(f"[voice] warning: {key} 比字幕晚 {lag:.2f}s", flush=True)
        end = start + len(audio) / SR
        if end > TOTAL:
            print(f"[voice] warning: {key} 超出片尾 {end - TOTAL:.2f}s", flush=True)

        # 首尾淡入淡出
        n = len(audio)
        fade = min(int(FADE * SR), n // 2)
        if fade > 0:
            audio = audio.copy()
            audio[:fade] *= np.linspace(0.0, 1.0, fade, dtype=np.float32)
            audio[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)

        i0 = int(round(start * SR))
        i1 = min(i0 + n, len(track))
        if i1 > i0:
            track[i0:i1] += audio[: i1 - i0]

        placed.append((key, start, end))
        cursor = end + GAP

    peak = float(np.max(np.abs(track)))
    if peak > 0.0:
        track *= min(1.0, 0.92 / peak)
    return track, placed


def write_wav(track: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(track, -1.0, 1.0)
    with wave.open(str(path), "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(SR)
        fh.writeframes((pcm * 32767.0).astype("<i2").tobytes())


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 trig-reduction 的中文配音 WAV")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "media" / "voice" / "voiceover.wav",
        help="输出 WAV 路径",
    )
    args = parser.parse_args()

    ffmpeg = find_ffmpeg()
    track, placed = build_voiceover(ffmpeg)
    write_wav(track, args.out)

    print(f"[voice] {VOICE} rate={RATE} -> {args.out}", flush=True)
    for key, start, end in placed:
        print(f"  {key:14s} {start:5.2f} → {end:5.2f}s  (+{start - ONSETS[key]:.2f}s)", flush=True)
    print(f"[voice] duration {len(track) / SR:.2f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
