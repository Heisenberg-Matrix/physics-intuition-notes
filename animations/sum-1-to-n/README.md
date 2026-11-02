# Sum 1→n — 中文解说视觉证明

用 Manim Community Edition 制作的竖屏证明：阶梯只画出前几行（1、2、3）与第 `n` 行，中间被省略的行用 `⋮` 表示；把这份阶梯复制、旋转 180° 并平移，两块恰好拼成 `n × (n + 1)` 的长方形，于是总和是 `n(n + 1) / 2`。这一版加入与画面严格对应的中文解说和低音量背景铺底。

成片：[sum-1-to-n.mp4](sum-1-to-n.mp4)（1080×1920，60 fps，约 34.3 秒，中文解说 + BGM）

## 预览

直接用浏览器打开 [index.html](index.html)，或在仓库根目录启动静态服务器：

```bash
python -m http.server 8123
# http://localhost:8123/animations/sum-1-to-n/
```

## 渲染

依赖：Python 3.9+、Manim CE（本仓库用 0.19.1 验证）、`manim-voiceover` 0.3.7、`edge-tts`，以及 `PATH` 中的 `ffmpeg`（Manim 混音和最终合成都会用到）。本仓库的 `.venv/Scripts/ffmpeg.exe` 可直接加入 `PATH`。

```bash
cd animations/sum-1-to-n

# manim-voiceover 用 --no-deps 安装，避免它把现有 manim / click / cloup 换掉
pip install --no-deps manim-voiceover==0.3.7
pip install mutagen "sox>=1.4.1,<2" python-slugify python-dotenv edge-tts

# 渲染画面 + 解说音轨
python -m manim sum_one_to_n.py SumOneToN

# 生成背景铺底（首次或想换 BGM 时）
python make_bgm.py

# 混合人声与 BGM，视频流直接复制，输出 sum-1-to-n.mp4
python mix_audio.py
```

渲染时会打印每句解说的开始时间与时长，例如 `[voice] compress @ 5.85s, 5.64s`，便于核对音画同步。`manim-voiceover` 会把语音缓存在 `media/voiceovers/`，改词后按新文本重新生成。

只检查最后一帧：

```bash
python -m manim sum_one_to_n.py SumOneToN -s
```

## 解说与配音

解说词、音色、停顿和 BGM 参数都在 [narration.py](narration.py) 中独立管理，场景文件只负责画面。

| 阶段 | 开始 | 画面 | 解说 |
| --- | --- | --- | --- |
| build | 0.00 s | 第 1、2、3 行小球依次长出 | 一加到 n，可以先把它们摆成阶梯：第几行，就放几个球。 |
| compress | 5.85 s | 整体上移，省略号 `⋮` 淡入 | 中间的行用省略号收起来；它们只是被藏住，并没有少。 |
| last_row | 11.68 s | 第 n 行出现，数字 `5` 变为 `n` | 最下面一行，有 n 个球。 |
| copy | 14.62 s | 复制整座阶梯并旋转 180° | 复制一份，旋转半圈。 |
| complement | 17.52 s | 平移到补集位置，缺口被逐行补满 | 第二份的每一行，正好补上第一份的空缺。 |
| rectangle | 21.62 s | 画出长方形，标注 n 行、n+1 列 | 于是每行都有 n 加一个球，一共 n 行。 |
| formula | 26.05 s | 公式淡入并停留 | 这个长方形由两份相同的阶梯拼成，所以一份正好是它的一半。 |

- 音色：`zh-CN-XiaoxiaoNeural`，语速 `+0%`，由 Edge TTS 合成；通过自定义 `EdgeTTSService` 接入 `manim-voiceover` 的计时体系。
- 每句之间留 `PAUSE = 0.20 s`，最后公式停 `2.0 s` 再结束。
- 解说只解释画面中不易直接看出的关系（省略号不代表少算、复制件逐行补缺、两份合起来才是长方形），不逐字朗读公式。

## 涉及参数

| 参数 | 值 | 说明 |
| --- | --- | --- |
| `N` | `5` | 最后一行的行号；实际数学行长为 1…`N` |
| `TOP_ROWS` | `(1, 2, 3)` | 省略号之前实际绘制的行 |
| `GRID_WIDTH` | `6.0` | `n + 1` 列的总宽（场景单位），`cell = GRID_WIDTH / (n + 1)` |
| `Y_CENTER` | `1.4` | 可见块的竖直中心，与第 3 行重合 |
| `TIMING` | 见源码 | 每个动作的 `run_time`；旁白版整体比无声版更慢，绝不会加速 |
| `VOICE` / `NARRATION` | 见 [narration.py](narration.py) | 音色配置与七段解说词 |
| `BGM` | `-20 dB` | 背景铺底增益、淡入 2 s / 淡出 3 s、开关 |
| 背景 / 青绿 / 陶土 | `#FAF6EF` / `#6FA79D` / `#C98A6E` | 暖白与低饱和双色，边缘加深色描边 |
| 字体 | `Microsoft YaHei` / `Georgia` | 中文标注 / 数字与公式；变量 `n` 用 `<i>` 斜体 |

`N` 由数据层传入 `StaircaseLayout`（`@dataclass(frozen=True)`），所有坐标、行与列都由它推导，渲染代码不硬编码行数。脚本要求 `N ≥ TOP_ROWS[-1] + 2`，即省略号至少代表一行。

## 几何与动画说明

- 数学上有 `N` 行；屏幕上只绘制 `1、2、3、N` 四行，中间 `N - 4` 行折叠进一条省略号带（高度 1 个 `cell`），所以最终长方形是「3 个可见行 + 1 个空带 + 第 `n` 行」共 `5 · cell` 高；
- 第 3 行取在块中心，第 `n` 行满足 `y_n = 2·y_3 − y_1`。复制品绕自身中心旋转 180° 后：第 3 行原地不动，第 2 行恰好落进省略号带，第 1 行与第 `n` 行互换；再向右平移一个 `cell`，补集行就右对齐到第 `row … n` 列；
- 落进省略号带的复制行淡出，保持空带为空；由隐藏行补出的球（第 2 行的全部、第 3 行的中段）在最终位置淡入。最终每一可见行都是 `n + 1` 个球：左侧青绿为原阶梯，右侧陶土为补集；
- 开始时逐行长出 1、2、3 行，随后整体上移 `0.35 · cell` 的间距让出省略号带并淡入 `⋮`，最后一行以具体数字 `N` 出现、标签再 `FadeTransform` 成斜体 `n`。

## 音画同步

每个阶段都包在 `with self.voiceover(text=...)` 中；该句语音的实际时长决定这一阶段的长度，动画按原速（或更慢）播放，剩余时间自动停住等待，不会为了配合配音而加速原有动作。渲染日志中的阶段起点：

```text
build 0.00s · compress 5.85s · last_row 11.68s · copy 14.62s
complement 17.52s · rectangle 21.62s · formula 26.05s → 34.25s
```

## 背景音乐

原无声版没有 BGM，仓库里也没有音频素材；这里的铺底由 [make_bgm.py](make_bgm.py) 现场合成（C 大调四个七和弦、44 秒、无外部版权素材），输出到 `media/bgm.wav`，不纳入版本库。`mix_audio.py` 会把它压到人声之下约 20 dB，并做 2 秒淡入、3 秒淡出，再与解说轨混合；视频流直接复制，不改分辨率、帧率和画质。

想换音乐：把文件放到 `media/bgm.wav`（或改 [narration.py](narration.py) 中的 `BGM["file"]`），重跑 `python mix_audio.py`。想关掉音乐：把 `BGM["enabled"]` 设为 `False`，脚本会直接输出纯解说版。

## 验证情况

- 已在本机用 Manim 0.19.1 + manim-voiceover 0.3.7 完整渲染：34.25 s，1080×1920，60 fps，AAC 48 kHz 立体声，无音轨缺失；混音后峰值 −6.8 dB，无削波。
- 已按阶段起点抽查画面：1.2 s 第 1 行、4.5 s 三行成形、7.5 s 省略号带、12.0 s 第 n 行、14.9–16.4 s 复制旋转、18.2–20.6 s 补集拼合、22.2–24.2 s 长方形与标注、27.0 s 公式、33.0 s 终帧，均与解说对应。
- 波形检查：七段人声连续、句间有短停顿，片尾 2 秒仅有衰减中的 BGM。
- Edge TTS 需要联网；音频缓存在 `media/voiceovers/`。`sox` 仅用于变速，未安装 SoX 二进制时只打印警告，不影响本片。
- 未在移动端真机验证 `index.html` 的播放样式。

## 文件

- `sum_one_to_n.py` — 场景源码（`StaircaseLayout` 数学数据 + `SumOneToN` 渲染与时间线）
- `narration.py` — 解说词、语音与 BGM 配置、Edge TTS 服务
- `make_bgm.py` — 生成背景铺底 `media/bgm.wav`
- `mix_audio.py` — 合成人声 + BGM，输出成片
- `sum-1-to-n.mp4` — 成片（含中文解说与 BGM）
- `poster.jpg` — 页面封面（最终帧）
- `index.html` — 视频预览页
- `media/` — 本地渲染产物与语音缓存，已在 `.gitignore` 中忽略
