"""生成一段很轻的底噪音乐，避免短片只有干声。

不是采样素材，全部用正弦波叠加合成：
- 4 小节循环的暖色和弦垫（A 小调 → F → C → G），每小节 8 秒；
- 每 4 秒一次很轻的高音拨弦，给“轻快”一点脉冲；
- 在解出公式、给出周期公式两个位置各加一声轻铃。

音量刻意压得很低，混音时再衰减一次，保证人声永远在前景。
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 48_000
DURATION = 92.0
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "media" / "music.wav"


def note(freq: float, t: np.ndarray, amp: float) -> np.ndarray:
    """带一点点二次谐波的软正弦，比纯正弦更暖。"""
    return amp * (
        np.sin(2 * np.pi * freq * t)
        + 0.22 * np.sin(2 * np.pi * 2 * freq * t)
        + 0.08 * np.sin(2 * np.pi * 3 * freq * t)
    )


def chord(freqs: list[float], start: float, length: float) -> np.ndarray:
    n = int(length * SR)
    t = np.arange(n) / SR
    env = np.minimum(1.0, t / 1.2) * np.minimum(1.0, (length - t) / 1.6)
    env = np.clip(env, 0.0, 1.0)
    out = np.zeros(n, dtype=np.float32)
    for f in freqs:
        out += note(f, t, 0.018)
    return (out * env).astype(np.float32)


def pluck(freq: float, start: float, length: float = 1.1) -> np.ndarray:
    n = int(length * SR)
    t = np.arange(n) / SR
    env = np.exp(-4.2 * t)
    tone = np.sin(2 * np.pi * freq * t) + 0.18 * np.sin(2 * np.pi * 2 * freq * t)
    return (0.012 * tone * env).astype(np.float32)


def bell(freq: float, start: float, length: float = 1.6) -> np.ndarray:
    n = int(length * SR)
    t = np.arange(n) / SR
    env = np.exp(-3.0 * t)
    tone = (
        np.sin(2 * np.pi * freq * t)
        + 0.5 * np.sin(2 * np.pi * 1.5 * freq * t)
        + 0.25 * np.sin(2 * np.pi * 2.02 * freq * t)
    )
    return (0.016 * tone * env).astype(np.float32)


def add(track: np.ndarray, clip: np.ndarray, at: float) -> None:
    i = int(at * SR)
    j = min(i + len(clip), len(track))
    if j > i:
        track[i:j] += clip[: j - i]


def main() -> None:
    track = np.zeros(int(DURATION * SR), dtype=np.float32)

    # 每个和弦 8 秒，循环铺满全片。
    progression = [
        [110.00, 261.63, 329.63],  # A minor
        [87.31, 220.00, 261.63],   # F major
        [130.81, 164.81, 196.00],  # C major
        [98.00, 246.94, 293.66],   # G major
    ]
    at = 0.0
    while at < DURATION:
        for freqs in progression:
            if at >= DURATION:
                break
            add(track, chord(freqs, at, min(8.0, DURATION - at)), at)
            at += 8.0

    # 很轻的拨弦，每 4 秒一次，音高随和弦走。
    melody = [523.25, 440.00, 523.25, 392.00]
    for k, mf in enumerate(melody):
        at = k * 4.0
        while at < DURATION:
            add(track, pluck(mf, at), at)
            at += 16.0

    # 关键推导处的两声轻铃。
    add(track, bell(880.0, 59.6), 59.6)
    add(track, bell(1046.5, 74.8), 74.8)

    peak = float(np.max(np.abs(track)))
    if peak > 0:
        track *= 0.12 / peak

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT), "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(SR)
        fh.writeframes((np.clip(track, -1.0, 1.0) * 32767).astype("<i2").tobytes())
    print(f"[music] {OUT}  {DURATION:.1f}s")


if __name__ == "__main__":
    main()
