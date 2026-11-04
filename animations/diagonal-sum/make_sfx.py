"""合成三枚极轻的音效：纸张、铅笔、小球。

    python make_sfx.py

输出到 media/sfx/，不依赖任何外部素材。音量在 mix_audio.py 里统一压低。
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

RATE = 44100
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "media" / "sfx"

rng = np.random.default_rng(20261104)


def envelope(n: int, attack: float, decay: float) -> np.ndarray:
    t = np.linspace(0.0, 1.0, n)
    return np.minimum(t / max(attack, 1e-6), 1.0) * np.exp(-t / max(decay, 1e-6))


def save(name: str, data: np.ndarray) -> None:
    peak = np.max(np.abs(data))
    if peak > 0:
        data = data / peak * 0.6
    with wave.open(str(OUT / name), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes((data * 32767).astype("<i2").tobytes())
    print(f"wrote {OUT / name}")


def paper() -> np.ndarray:
    n = int(0.55 * RATE)
    noise = rng.normal(0, 1, n)
    # 两级滑动平均：去掉刺耳高频，留下纸张摩擦的沙沙声
    kernel = np.ones(24) / 24
    smooth = np.convolve(noise, kernel, mode="same")
    smooth = np.convolve(smooth, kernel, mode="same")
    env = envelope(n, attack=0.08, decay=0.24)
    return smooth * env


def pencil() -> np.ndarray:
    n = int(0.22 * RATE)
    noise = rng.normal(0, 1, n)
    # 一阶差分做轻微高通，像笔尖划过纸面
    scratch = np.diff(noise, prepend=0.0)
    env = envelope(n, attack=0.015, decay=0.07)
    return scratch * env


def ball() -> np.ndarray:
    n = int(0.20 * RATE)
    t = np.linspace(0, 0.20, n, endpoint=False)
    freq = 720 - 380 * (t / 0.20)
    phase = 2 * np.pi * np.cumsum(freq) / RATE
    tone = np.sin(phase) * np.exp(-t / 0.055)
    click = rng.normal(0, 0.15, n) * np.exp(-t / 0.006)
    return tone + click


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    save("paper.wav", paper())
    save("pencil.wav", pencil())
    save("ball.wav", ball())


if __name__ == "__main__":
    main()
