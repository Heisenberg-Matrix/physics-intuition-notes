"""生成解说视频的背景音乐铺底（不依赖任何外部音频素材）。

    python make_bgm.py

输出 `media/bgm.wav`：44 秒、44.1 kHz、立体声。四个七和弦缓慢交叠，
音量压得很低；最终混音时还会再降约 26 dB，只留一层暖色底噪。
"""

from pathlib import Path

import numpy as np

SR = 44100
SECONDS = 44.0
OUT = Path(__file__).resolve().parent / "media" / "bgm.wav"

# (低音 MIDI, 和弦 MIDI 音高)：C 大调上的四个七和弦，安静、无强终止感。
CHORDS = [
    (36, [60, 64, 67, 71]),   # Cmaj7
    (33, [57, 60, 64, 67]),   # Am7
    (29, [53, 57, 60, 64]),   # Fmaj7
    (31, [55, 59, 62, 64]),   # G6
]
CHORD_STARTS = [0.0, 10.5, 21.0, 31.5]
CHORD_LENGTH = 13.0


def midi_to_hz(note: int) -> float:
    return 440.0 * 2 ** ((note - 69) / 12)


def soft_note(freq: float, t: np.ndarray, detune_cents: float) -> np.ndarray:
    f = freq * 2 ** (detune_cents / 1200.0)
    phase = 2 * np.pi * f * t
    # 基音 + 两个弱泛音：比纯正弦更暖，又不会像铜管那样抢耳。
    return (
        np.sin(phase)
        + 0.30 * np.sin(2 * phase)
        + 0.10 * np.sin(3 * phase)
    ) / 1.40


def envelope(n: int, attack: float = 2.5, release: float = 3.0) -> np.ndarray:
    env = np.ones(n)
    a = min(int(attack * SR), n // 2)
    r = min(int(release * SR), n // 2)
    env[:a] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))
    env[n - r:] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, r))
    return env


def main() -> None:
    total = int(SECONDS * SR)
    left = np.zeros(total)
    right = np.zeros(total)

    for (bass, notes), start in zip(CHORDS, CHORD_STARTS):
        n = int(CHORD_LENGTH * SR)
        i0 = int(start * SR)
        i1 = min(i0 + n, total)
        n = i1 - i0
        t = np.arange(n) / SR

        chord_l = np.zeros(n)
        chord_r = np.zeros(n)

        for note in notes:
            freq = midi_to_hz(note)
            # 左右各偏几个音分，得到很宽的立体声像。
            chord_l += soft_note(freq, t, 3.5)
            chord_r += soft_note(freq, t, -3.5)

        bass_hz = midi_to_hz(bass)
        chord_l += 0.55 * soft_note(bass_hz, t, 0.0)
        chord_r += 0.55 * soft_note(bass_hz, t, 0.0)

        # 每个和弦有自己的缓慢呼吸，避免四小节循环太机械。
        lfo = 1.0 + 0.06 * np.sin(2 * np.pi * 0.055 * t + start)
        chord_l *= envelope(n) * lfo / (len(notes) + 0.55)
        chord_r *= envelope(n) * lfo / (len(notes) + 0.55)

        left[i0:i1] += chord_l
        right[i0:i1] += chord_r

    # 整体淡入淡出，循环结尾不会突然断掉。
    fade_in = int(2.0 * SR)
    fade_out = int(3.5 * SR)
    ramp_in = np.linspace(0, 1, fade_in) ** 2
    ramp_out = np.linspace(1, 0, fade_out) ** 2
    left[:fade_in] *= ramp_in
    right[:fade_in] *= ramp_in
    left[-fade_out:] *= ramp_out
    right[-fade_out:] *= ramp_out

    peak = max(np.abs(left).max(), np.abs(right).max())
    gain = 0.22 / peak
    stereo = np.stack([left * gain, right * gain], axis=1)
    pcm = (stereo * 32767).astype("<i2")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    import wave

    with wave.open(str(OUT), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())

    print(f"wrote {OUT} ({SECONDS:.0f}s, peak {0.22:.2f})")


if __name__ == "__main__":
    main()
