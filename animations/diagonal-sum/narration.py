"""中文解说、字幕、音效与配音配置。

画面文件只读取这里的文案与时间轴；改词、换音色、调字幕都不必碰动画代码。
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

# 每个 key 对应画面中的一个阶段；语音的实际时长决定该阶段的长度。
NARRATION = {
    "hook": "这一长串数字，你会怎么算？",
    "turn": "其实，换个方向看就行。",
    "count_intro": "沿着斜线数一数。",
    "count_up": "一个、两个、三个、四个、五个……",
    "count_down": "再四个、三个、两个、一个。",
    "epiphany": "等等，这不就是一个正方形吗？",
    "answer1": "所以，根本不用挨个加。",
    "answer2": "答案就是 n 的平方。",
    "outro": "有时候，换个角度，答案就出来了。",
}

# 字幕只保留关键词，不逐字转写；每句都控制在一行内。
SUBTITLES = {
    "hook": "你会一个个加吗？",
    "turn": "换个方向看？",
    "count_intro": "沿着斜线数",
    "count_up": "1、2、3、4、5……",
    "count_down": "4、3、2、1",
    "epiphany": "原来是个正方形！",
    "answer1": "不用挨个加",
    "answer2": "答案是 n 的平方",
    "outro": "换个角度，就看见了。",
}

# “数一数”的“数”读 shǔ；Edge TTS 容易读成 shù，合成前换成同音字引导。
# 只做短语级替换，避免误伤其它词；新增文案若含多音字，在这里补一条。
PRONUNCIATION = {
    "数一数": "属一属",
}


def speakable(text: str) -> str:
    """把稿面文字换成 TTS 能读对的同音写法。"""
    for written, spoken in PRONUNCIATION.items():
        text = text.replace(written, spoken)
    return text


# 每句之间的呼吸间隔（秒）；count_up / count_down 内部另按语音时长均分。
PAUSE = 0.18

# ---------------------------------------------------------------- 音效
# 由 make_sfx.py 生成，全部是程序合成的轻微纸张 / 铅笔 / 小球声。
SFX_GAIN_DB = {
    "paper": -20.0,
    "pencil": -22.0,
    "ball": -18.0,
}

# (阶段, 相对阶段起点的秒数, 音效名)；mix_audio.py 读取渲染时写出的时间轴。
CUES = [
    ("hook", 0.10, "pencil"),
    ("turn", 0.10, "paper"),
    ("turn", 3.65, "ball"),        # 5×5 方阵补齐
    ("count_intro", 0.30, "pencil"),
    ("epiphany", 0.45, "paper"),   # 斜虚线淡出
    ("answer1", 0.10, "pencil"),
    ("outro", 0.20, "ball"),       # 小球轻弹
]


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
        input_text = speakable(remove_bookmarks(text))
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
