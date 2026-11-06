# 三角函数诱导公式，真的需要背吗？

一条 54 秒的竖屏动画，配中文配音与字幕。它不从公式出发，而是把点 P 放到单位圆上：

- 逆时针转半圈，看点落到 π+α 时坐标怎么变；
- 顺时针转到 −α，看点如何关于 x 轴对称；
- 最后让 α、−α、π−α、π+α 四个点同时留在圆上，比较三种对称关系。

所有结论都来自同一个圆的旋转与镜像：

```text
sin(kπ + α) = (−1)^k sin α
sin(kπ − α) = (−1)^(k+1) sin α
cos(kπ ± α) = (−1)^k cos α        (k ∈ ℤ)
```

成片：[trig-reduction.mp4](trig-reduction.mp4)（1080×1920，30 fps，54 秒，AAC 48 kHz 单声道配音）。

## 预览

直接用浏览器打开 [index.html](index.html)，或在仓库根目录启动静态服务器：

```bash
python -m http.server 8123
# http://localhost:8123/animations/trig-reduction/
```

## 渲染

依赖：Python 3.10+、Manim CE 0.19.1、NumPy、edge-tts 7.3.1（配音，需联网）、FFmpeg（写 MP4 与混音）。本仓库已在 Manim 0.19.1 + Python 3.10.11 + edge-tts 7.3.1 下验证。

```bash
cd animations/trig-reduction
pip install -r requirements.txt

./run.sh preview     # 540×960 @30，输出 media/preview.mp4（含配音）
./run.sh             # 1080×1920 @30，输出 trig-reduction.mp4 与 poster.jpg（含配音）
```

等价的 Manim 命令：

```bash
# 低清预览（无声）
PREVIEW=1 python -m manim -ql --disable_caching scene.py TrigReductionScene

# 成片（Manim 按画面高度命名输出目录，竖屏 1080×1920 是 1920p30）
python -m manim -qh --disable_caching scene.py TrigReductionScene

# 配音：逐句合成，命中缓存后不再联网
python narration.py

# 把音轨混进视频
ffmpeg -i media/videos/scene/1920p30/TrigReductionScene.mp4 \
  -i media/voice/voiceover.wav -map 0:v:0 -map 1:a:0 -c:v copy \
  -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a aac -b:a 128k -ar 48000 -ac 1 \
  -movflags +faststart -shortest trig-reduction.mp4
```

`--disable_caching` 建议保留：本片大量使用 `always_redraw`，分段缓存不能完整记录 updater 状态，复用旧分段容易出现错帧。

## 配音

- **音色**：`zh-CN-XiaoxiaoNeural`，语速 `+4%`；逐句合成后用 20 ms 淡入淡出拼进 54 秒音轨。
- **文本来源**：直接读 `scene.py` 的 `CUES`，字幕和语音不会各写一份；课堂上 `cos`、`sin` 分别读作“扣赛因”“赛因”，在 `narration.py` 的 `PRONOUNCE` 里统一替换。
- **对齐**：`ONSETS` 记录画面中每句字幕实际淡入完成的秒数；语音从该时刻起播，若上一句还没说完就顺延，保证不重叠（本片最多把某句顺延 0.29 秒）。
- **响度**：混流时 `loudnorm=I=-16:TP=-1.5`，符合短视频平台常见的 −16 LUFS 目标。
- **缓存**：每句 MP3 按文本哈希缓存在 `media/voice/`，改一句只会重合成那一句；首次合成需联网。
- **无背景音乐**：只保留人声，避免和关键词字幕抢注意力。

## 分镜与时间轴

配音由 `narration.py` 按 `CUES` 逐句铺在字幕出现的时刻；`NARRATION` 保留完整解说词作备份。字幕固定在画面坐标 `y = −6.55`，避开平台底部按钮区。

| 时间 | 画面 | 解说 / 字幕 |
| --- | --- | --- |
| 0.0–6.0 s | 四个诱导公式交错出现，收缩淡出；出现“有没有可能……根本不用背？” | 这些三角函数公式，你还记得几个？ / 有没有可能……根本不用背？ |
| 6.0–14.0 s | 画出单位圆与坐标轴，半径从 0 转到 α=40°，投出 cos α、sin α | 其实，我们只需要一个圆。横坐标是 cos，纵坐标是 sin。 |
| 14.0–25.0 s | 原位置留浅色对照点，半径连续逆时针转 π 到 π+α；横、纵投影依次高亮 | 如果再转半圈呢？ / 转过半圈，横坐标和纵坐标，竟然都反了。 |
| 25.0–36.0 s | 恢复 α 后顺时针转到 −α，竖直虚线连接两点，强调关于 x 轴对称 | 那如果角度变成负数呢？ / 这一次，横坐标不变，只有纵坐标反了。 |
| 36.0–47.0 s | 四个点同时在圆上：π−α、π+α、−α 依次与 α 比较 | 转半圈，再改变角度的正负方向…… / 所有规律，都藏在这个圆里。 |
| 47.0–54.0 s | 三行规律合并，推广到任意整数 k，最后三条公式停留约 2 秒 | 原来，诱导公式不用硬背。转一转，就看懂了。 |

## 实现要点

- **连续旋转**：`ValueTracker` 保存弧度，半径、动点、两条投影线都用 `always_redraw` 跟随；转半圈是 `α → α+π` 的插值，不是换点。
- **方向可读**：逆时针转 π、顺时针转 −2α 时各画一段带箭头的圆弧，正负角一眼可辨。
- **一次只强调一个关系**：合并段用“虚线 + 两个圆环 + 一句说明”依次比较 π−α、π+α、−α；每次只停留一个关系。
- **颜色**：青绿 `#299C8D` 是原始角，橙黄 `#D6A04D` 是负角点，蓝 `#648BCB` 是关于纵轴的镜像点，玫红 `#C67591` 是对径点；与公式、字幕的颜色分工一致。
- **安全区**：所有公式与字幕限制在竖屏中央约 7.3 个画幅单位内（左右各留约 8% 空白）；单位圆圆心固定，全片不切镜头。
- **投影线用细实线**：`always_redraw` 每帧重建 `DashedLine` 时虚线数量会变化，Manim 的 `become/align_points` 在子路径数不一致时会抛出 `IndexError` 并卡住；改用同色细实线，规范允许实线或虚线，画面也更干净。
- **公式排版**：本机没有 LaTeX 时，`math_text` 自动退回 Cambria Math 的 `MarkupText`（`sin` 用斜体标记）；有 LaTeX 时优先用 `MathTex`，两条路径内容一致。

## 可调参数

| 参数 | 位置 | 值 / 说明 |
| --- | --- | --- |
| `PREVIEW` | 环境变量 | `1` → 540×960@30；否则 1080×1920@30 |
| `CENTER` / `RADIUS` | `scene.py` | 单位圆圆心 `(0, 1.35)`、半径 2.55；全片位置稳定 |
| `ALPHA` | `scene.py` | 演示角 40°；改角度会同步影响所有投影和标签 |
| `CUES` | `scene.py` | 每句字幕的文本与名义起始时间；配音也读这里 |
| `NARRATION` | `scene.py` | 完整解说词备份 |
| `VOICE` / `RATE` | `narration.py` | 音色与语速，默认晓晓 `+4%` |
| `ONSETS` | `narration.py` | 字幕实际淡入时刻；重跑渲染后按日志更新 |
| `TEAL` / `ORANGE` / `BLUE` / `ROSE` | `scene.py` | 四种点的语义色 |
| `SUB_Y` | `scene.py` | 字幕高度 −6.55 |
| 各段时长 | `SEGMENTS` | 0–6、6–14、14–25、25–36、36–47、47–54 秒 |

## 验证情况

- **渲染**：Manim 0.19.1 完整渲染 540×960@30 预览与 1080×1920@30 成片，单场景连续渲染，时长 54.00 秒；成片约 4.4 MB，视频 1080×1920@30，音轨 AAC 48 kHz 单声道。`./run.sh preview` 已从头跑通一次，确认配音生成与混流链路可用。
- **数学**：α=40°；π+α=220° 落在第三象限，π−α=140° 落在第二象限，−α=−40° 落在第四象限；三条最终公式均与 `k` 的奇偶一致。
- **逐帧抽查**：钩子公式可读；0→α 连续扫过；转 π 后横纵坐标同时为负，投影段依次加粗；−α 与 α 共用同一 x；四个点的连线分别为水平、过圆心、竖直；最终画面只剩单位圆、三条公式与“k 为任意整数”，停留约 2 秒。
- **安全边距**：540×960 下最左/最右内容均留有约 8% 画幅宽度；字幕与公式不重叠，最终停留约 2 秒。
- **配音**：11 句全部落在对应字幕窗口内，句首静音后起声与字幕相差 0.2–0.5 秒；成片实测 −15.9 LUFS、真峰值 −1.5 dBFS；首句约 0.59 秒起声，末句约 51.8 秒收尾，片尾留约 2 秒静默定格。
- **已知限制**：本机无 LaTeX，公式字形为 Cambria Math；Edge TTS 首次合成需要联网，没有背景音乐。

## 文件

- `scene.py` — 完整 Manim 场景、时间轴、公式与字幕
- `narration.py` — 逐句 TTS、时间对齐、输出 `media/voice/voiceover.wav`
- `run.sh` — 一键预览 / 成片渲染，并混入配音
- `requirements.txt` — Python 依赖
- `index.html` — 视频预览页
- `trig-reduction.mp4` — 成片
- `poster.jpg` — 网页封面
- `media/` — 渲染缓存、预览与配音缓存（忽略提交）
