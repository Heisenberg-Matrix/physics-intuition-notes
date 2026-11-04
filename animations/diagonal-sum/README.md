# 对角线和 — 1 + 2 + … + n + … + 2 + 1 = n²

5×5 方阵沿平行斜线分组，每组依次有 1、2、3、4、5、4、3、2、1 个球。斜线数完，整个正方形正好是 25 个球——不用逐项相加，也能看见 `n²`。手绘铅笔质感、暖白纸面、低饱和配色，29 秒竖屏，中文解说 + 关键词字幕 + 极轻音效。

成片：[diagonal-sum.mp4](diagonal-sum.mp4)（1080×1920，60 fps，28.72 秒）

## 预览

直接用浏览器打开 [index.html](index.html)，或在仓库根目录启动静态服务器：

```bash
python -m http.server 8123
# http://localhost:8123/animations/diagonal-sum/
```

## 渲染

依赖：Python 3.9+、Manim CE（本仓库用 0.19.1 验证）、`manim-voiceover` 0.3.7、`edge-tts`，以及 `PATH` 中的 `ffmpeg`。本仓库的 `.venv/Scripts/ffmpeg.exe` 可直接加入 `PATH`。画面字体使用 Windows 自带的 `Segoe Print` 与 `KaiTi`。

```bash
cd animations/diagonal-sum

# manim-voiceover 用 --no-deps 安装，避免它把现有 manim / click / cloup 换掉
pip install --no-deps manim-voiceover==0.3.7
pip install mutagen "sox>=1.4.1,<2" python-slugify python-dotenv edge-tts

# 渲染画面 + 解说音轨；同时写出 media/timeline.json
python -m manim diagonal_sum.py DiagonalSum

# 合成三枚音效（首次或想改音色时）
python make_sfx.py

# 按时间轴混入音效，视频流直接复制，输出 diagonal-sum.mp4
python mix_audio.py
```

渲染日志会打印每句解说的起点与时长，例如 `[voice] count_up @ 9.20s, 3.89s`，便于核对音画同步。`manim-voiceover` 把语音缓存在 `media/voiceovers/`，改词后按新文本重新生成。

只检查最后一帧：

```bash
python -m manim diagonal_sum.py DiagonalSum -s
```

## 解说、字幕与时间轴

解说词、字幕、音色、音效与提示点都在 [narration.py](narration.py) 中独立管理；画面文件只读取它们。

| 阶段 | 开始 | 画面 | 解说 | 字幕 |
| --- | --- | --- | --- | --- |
| hook | 0.00 s | 长加法出现，问号轻跳 | 从一加到五，再加回一。 | 你会一个个加吗？ |
| turn | 2.76 s | 公式上移，方阵 1→2×2→3×3→4×4→5×5 展开 | 其实，换个方向看就行。 | 换个方向看？ |
| count_intro | 6.84 s | 九条平行斜虚线淡入 | 沿着斜线数一数。 | 沿着斜线数 |
| count_up | 9.02 s | 前五条斜线依次点亮，下方计数 1→5 | 一个、两个、三个、四个、五个…… | 1、2、3、4、5…… |
| count_down | 12.91 s | 后四条斜线点亮，计数 4→1 | 再四个、三个、两个、一个。 | 4、3、2、1 |
| epiphany | 16.84 s | 虚线淡出，小球恢复同一颜色，出现边长标注 | 等等，这不就是一个正方形吗？ | 原来是个正方形！ |
| answer1 | 19.89 s | 原加法重现，问号换成 5×5 = 25 | 所以，根本不用挨个加。 | 不用挨个加 |
| answer2 | 22.55 s | 过渡到通式 | 答案就是 n 的平方。 | 答案是 n 的平方 |
| outro | 24.95 s | 一个小球轻弹，画面淡出 | 有时候，换个角度，答案就出来了。 | 换个角度，就看见了。 |

- 音色：`zh-CN-XiaoxiaoNeural`，语速 `+0%`，自然口语，不用夸张营销腔；通过自定义 `EdgeTTSService` 接入 `manim-voiceover` 的计时体系。
- 字幕固定在画面下方安全区（`y = -6.25`），只保留关键词，每句一行，不与公式重叠。
- 每句解说对应一个 `with self.voiceover(...)` 块，字幕随块显隐；计数阶段把语音时长按个数均分，小球高亮与「一个、两个……」同拍推进。
- 多音字：`数一数` 的「数」应读 shǔ，Edge TTS 易读成 shù；合成前用同音字「属」引导（`PRONUNCIATION`），听感不变。

## 音效

[make_sfx.py](make_sfx.py) 用 numpy 现场合成三枚音效，无外部素材：

- `paper.wav`：纸张摩擦的沙沙声，用于公式上移与斜虚线淡出；
- `pencil.wav`：笔尖划纸的短促声，用于开场公式、斜线出现与答案出现；
- `ball.wav`：带轻微下滑音的小球弹跳声，用于方阵补齐与结尾弹跳。

[mix_audio.py](mix_audio.py) 读取渲染时写出的 `media/timeline.json`，按 [narration.py](narration.py) 的 `CUES` 在阶段内偏移处叠加，增益分别为 −20 / −22 / −18 dB，整体远低于人声；没有背景音乐。改时间点只需改 `CUES`，重新跑 `mix_audio.py`，不必重渲染画面。

## 涉及参数

| 参数 | 值 | 说明 |
| --- | --- | --- |
| `GRID.n` | `5` | 方阵边长；斜线长度自然为 1…n…1 |
| `GRID.cell` | `1.15` | 相邻小球中心距（场景单位） |
| `GRID.radius` | `0.42` | 小球半径，边缘略带手绘抖动 |
| `GRID.center_y` | `1.0` | 方阵中心高度 |
| 配色 | `#FAF6EF` / `#4B4740` / `#8AAFA6` / `#CE9A80` | 暖白纸面、石墨、低饱和青绿与陶土 |
| 字体 | `Segoe Print` / `KaiTi` | 数字与公式 / 中文字幕与标注 |
| 字幕位置 | `y = -6.25` | 竖屏下方安全区 |
| `SFX_GAIN_DB` | `-20` / `-22` / `-18` dB | 纸、笔、球三枚音效的混音增益 |
| `PAUSE` | `0.18 s` | 阶段之间的呼吸间隔 |

## 音画同步

`manim-voiceover` 以语音实际时长决定每个阶段的下限；动画只按原速播放，剩余时间自动停住等待，没有为了卡点加速。计数阶段用 `step = 语音时长 / 个数` 均分高亮起点，所以「一个、两个、三个……」与斜线点亮保持同一节拍。字幕和音效共用同一份阶段时间轴：

```text
hook 0.00s · turn 2.76s · count_intro 6.84s · count_up 9.02s
count_down 12.91s · epiphany 16.84s · answer1 19.89s
answer2 22.55s · outro 24.95s → 28.72s
```

## 验证情况

- 已用 Manim 0.19.1 + manim-voiceover 0.3.7 完整渲染：28.72 s，1080×1920，60 fps，AAC 48 kHz 立体声；视频流直接复制，未改分辨率、帧率或画质。
- 抽查关键帧：0.8 s 长加法、4.5 s 单球、6.5 s 5×5、9.3 s 前五条斜线、16.2 s 九组完成、17.9 s 方阵变同色与边长标注、22.0 s `5×5=25`、24.2 s 通式、25.6 s 余韵、28.4 s 淡出，均与解说对应。
- 混音后整体平均 −23.2 dB、峰值 −5.2 dB，无削波；音效在无人声的空隙处约 −25 dB，存在但不抢人声。
- 字幕固定在画面下方安全区，不压公式；`n²` 在楷体字幕里缺字，字幕改为「答案是 n 的平方」，公式中的 `n²` 仍由 Segoe Print 正常显示。
- Edge TTS 需要联网；音频缓存在 `media/voiceovers/`。`sox` 仅用于变速，未安装 SoX 二进制时只打印警告，不影响本片。
- 字体依赖 Windows 的 `Segoe Print` / `KaiTi`；其它系统会回退到可用字体，版面可能略有差异。
- 未在移动端真机验证 `index.html` 的播放样式。

## 文件

- `diagonal_sum.py` — 场景源码（方阵、斜线、计数、顿悟与公式）
- `narration.py` — 解说词、字幕、多音字表、音色与音效配置
- `make_sfx.py` — 合成纸张 / 铅笔 / 小球三枚音效
- `mix_audio.py` — 读取时间轴并混入音效，输出成片
- `diagonal-sum.mp4` — 成片（中文解说 + 字幕 + 音效）
- `poster.jpg` — 页面封面（通式帧）
- `index.html` — 视频预览页
- `media/` — 渲染产物、语音缓存与时间轴，已在 `.gitignore` 中忽略
