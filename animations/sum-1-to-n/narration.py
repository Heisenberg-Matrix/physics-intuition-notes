"""中文解说词、语音与背景音乐配置。

把“说什么、用什么声音说、配什么音乐”集中在这里，场景文件只负责画面。
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts
from manim import logger
from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import SpeechService

# ---------------------------------------------------------------- 语音
VOICE = {
    "voice": "zh-CN-XiaoxiaoNeural",
    "rate": "+0%",
    "pitch": "+0Hz",
    "volume": "+0%",
}

# 每一句都对应画面中的一个明确阶段；改词后重新渲染即可，缓存按文本区分。
NARRATION = {
    "build": "一加到 n，可以先把它们摆成阶梯：第几行，就放几个球。",
    "compress": "中间的行用省略号收起来；它们只是被藏住，并没有少。",
    "last_row": "最下面一行，有 n 个球。",
    "copy": "复制一份，旋转半圈。",
    "complement": "第二份的每一行，正好补上第一份的空缺。",
    "rectangle": "于是每行都有 n 加一个球，一共 n 行。",
    "formula": "这个长方形由两份相同的阶梯拼成，所以一份正好是它的一半。",
}

# 每句之间的呼吸间隔（秒），避免上一句刚结束就进入下一个动作。
PAUSE = 0.20

# ---------------------------------------------------------------- 背景音乐
BGM = {
    "enabled": True,
    "file": "bgm.wav",     # 由 make_bgm.py 生成，路径相对本目录
    "gain_db": -20.0,      # 铺底比人声低约 20 dB，保持人声清晰
    "fade_in": 2.0,
    "fade_out": 3.0,
}


class EdgeTTSService(SpeechService):
    """用 Microsoft Edge 在线语音合成，接入 manim-voiceover 的计时体系。"""

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
        input_text = remove_bookmarks(text)
        input_data = {
            "input_text": input_text,
            "service": "edge-tts",
            "voice": self.voice,
            "rate": self.rate,
            "pitch": self.pitch,
            "volume": self.volume,
        }

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            return cached_result

        audio_path = path or (self.get_audio_basename(input_data) + ".mp3")
        output = cache_dir / audio_path

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
