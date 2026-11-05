"""中文解说、字幕与 SRT 导出。

画面只读取这里的文案；改词不会影响几何或动画代码。
配音用 edge-tts 的 zh-CN-XiaoxiaoNeural，语速略慢，自然口语。
每个 key 对应一个 voiceover 块，块的时长由真实音频决定。
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import edge_tts
from manim import logger
from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import SpeechService

VOICE = {
    "voice": "zh-CN-XiaoxiaoNeural",
    "rate": "-4%",
    "pitch": "+0Hz",
    "volume": "+0%",
}

# 顺序即时间轴；每个 key 的语音结束前，画面动作应已完成。
LINES: dict[str, str] = {
    "hook1": "一的平方，加二的平方，一直加到 n 的平方。",
    "hook2": "有没有一种办法，不用算，就能看出答案？",
    "build": "把每个平方，变成一层小方块。四层叠起来，就是一块阶梯积木。",
    "copy": "现在，复制三份。三块积木，形状完全一样。",
    "fit_b": "先固定一块。第二块转个方向，像俄罗斯方块一样，滑进空缺。",
    "fit_c": "再把第三块放进去。看，这些台阶，正在一点点互相补齐。",
    "reveal": "拼好之后，下面是一个长方体。上面，还多出一片三角形的台阶。",
    "top_count": "数一数：一、二、三、四，一共十块，正好是一加到 n。",
    "formula": "所以，三个积木的体积，就是长方体的体积，加上顶部这一片。",
    "answer": "两边除以三。平方和公式，就这样拼出来了。",
    "outro": "原来，平方和公式，真的可以拼出来。",
}

SUBTITLES: dict[str, str] = {
    "hook1": "从 1² 加到 n²",
    "hook2": "不用算，能看出来吗？",
    "build": "一层 = 一个平方数",
    "copy": "复制三份，形状一样",
    "fit_b": "转个方向，滑进空缺",
    "fit_c": "台阶互相补齐",
    "reveal": "下面是长方体，上面是台阶",
    "top_count": "10 块 = 1 + 2 + 3 + 4",
    "formula": "3S = 长方体 + 顶部台阶",
    "answer": "平方和公式，拼出来了",
    "outro": "几何，让公式自己出现",
}

# “数一数”的“数”读 shǔ；Edge TTS 容易读成 shù，合成前用同音字引导。
PRONUNCIATION = {
    "数一数": "属一属",
}

PAUSE = 0.18


def speakable(text: str) -> str:
    for written, spoken in PRONUNCIATION.items():
        text = text.replace(written, spoken)
    return text


class EdgeTTSService(SpeechService):
    """Microsoft Edge 在线语音，接入 manim-voiceover 的计时体系。"""

    def __init__(
        self,
        voice: str = VOICE["voice"],
        rate: str = VOICE["rate"],
        pitch: str = VOICE["pitch"],
        volume: str = VOICE["volume"],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.volume = volume

    def generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None, **kwargs
    ) -> dict:
        cache_dir = Path(cache_dir) if cache_dir is not None else Path(self.cache_dir)
        input_text = speakable(remove_bookmarks(text))
        input_data = {
            "input_text": input_text,
            "service": "edge-tts",
            "voice": self.voice,
            "rate": self.rate,
            "pitch": self.pitch,
            "volume": self.volume,
        }
        cached = self.get_cached_result(input_data, cache_dir)
        if cached is not None:
            return cached
        audio_path = path or (self.get_audio_basename(input_data) + ".mp3")
        output = cache_dir / audio_path
        output.parent.mkdir(parents=True, exist_ok=True)

        async def _synthesize() -> None:
            communicate = edge_tts.Communicate(
                input_text,
                self.voice,
                rate=self.rate,
                pitch=self.pitch,
                volume=self.volume,
            )
            await communicate.save(str(output))

        asyncio.run(_synthesize())
        logger.info(f"[voice] {audio_path}")
        return {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }


def generate_voiceover(cache_dir: str = "media/voiceovers") -> dict[str, dict]:
    """预先合成每句配音并记录时长，供低画质预览与 SRT 使用。"""
    service = EdgeTTSService(cache_dir=cache_dir)
    durations: dict[str, dict] = {}
    for key, text in LINES.items():
        result = service._wrap_generate_from_text(text)
        audio = Path(cache_dir) / result["final_audio"]
        durations[key] = {
            "text": text,
            "audio": str(audio),
            "duration": _mp3_duration(audio),
        }
        print(f"[voice] {key:10s} {durations[key]['duration']:.2f}s  {text}")
    out = Path(cache_dir).parent / "voice_durations.json"
    out.write_text(json.dumps(durations, ensure_ascii=False, indent=2), encoding="utf-8")
    return durations


def _mp3_duration(path: Path) -> float:
    from mutagen.mp3 import MP3

    return float(MP3(str(path)).info.length)


def synchronize_subtitles(
    timeline: dict[str, dict], pause: float = PAUSE
) -> list[dict]:
    """由场景写出的 voiceover 时间轴生成字幕条目。"""
    cues = []
    for key in LINES:
        if key not in timeline:
            continue
        item = timeline[key]
        cues.append(
            {
                "key": key,
                "start": float(item["start"]),
                "end": float(item["start"] + item["duration"] + pause),
                "text": SUBTITLES[key],
            }
        )
    # 一条字幕结束前留 0.1 s 空隙，避免 SRT 条目互相重叠。
    for current, nxt in zip(cues, cues[1:]):
        current["end"] = min(current["end"], nxt["start"] - 0.1)
    return cues


def _srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def export_srt(cues: list[dict], path: str = "subtitles.srt") -> Path:
    lines = []
    for i, cue in enumerate(cues, 1):
        lines += [str(i), f"{_srt_time(cue['start'])} --> {_srt_time(cue['end'])}", cue["text"], ""]
    out = Path(path)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    generate_voiceover()
