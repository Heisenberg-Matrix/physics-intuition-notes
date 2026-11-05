# 三个平方阶梯体，拼出平方和公式

四个平方数 `1²、2²、3²、4²` 各是一层方阵，叠起来就是一块四层阶梯积木。把这块阶梯复制三份，只做整体旋转与平移，像俄罗斯方块一样滑进空缺——三块恰好拼成「4×5×4 的长方体 + 顶部 1+2+3+4 的台阶」。于是

```text
3S = n(n+1)·n + n(n+1)/2 = n(n+1)(n+1/2)
```

两边除以三，就得到 `1² + 2² + ⋯ + n² = n(n+1)(2n+1)/6`。全片约 70 秒，竖屏 9:16，中文解说 + 关键词字幕。

成片：[square-sum-3d.mp4](square-sum-3d.mp4)（1080×1920，60 fps，69.97 秒）

## 预览

直接用浏览器打开 [index.html](index.html)，或在仓库根目录启动静态服务器：

```bash
python -m http.server 8123
# http://localhost:8123/animations/square-sum-3d/
```

## 渲染

依赖：Python 3.10+、Manim CE 0.19.1、`manim-voiceover` 0.3.7、`edge-tts`、NumPy、FFmpeg（Manim 混音需要）。Manim 的中文文字使用系统字体（Microsoft YaHei / 思源黑体 / SimHei / KaiTi 自动挑选），公式在无 LaTeX 时回退到 Cambria Math 排版。

```bash
cd animations/square-sum-3d

# manim-voiceover 用 --no-deps 安装，避免它替换已装好的 manim / click / cloup
pip install -r requirements.txt
pip install --no-deps manim-voiceover==0.3.7

# 一键：几何校验 → 合成配音 → 1080×1920@60 渲染 → 复制成片
./run.sh
```

等价于：

```bash
python assembly.py      # 先看离散校验，必须输出 ok: True
python narration.py     # 预合成每句配音，写出 media/voice_durations.json
python -m manim -qh --disable_caching scene.py SquareSumScene
cp media/videos/scene/1920p60/SquareSumScene.mp4 square-sum-3d.mp4
```

低清预览（540×960@30，约十几秒一帧的机器也可跑）：

```bash
./run.sh --preview      # 输出 media/preview.mp4
# 或手动：PREVIEW=1 python -m manim -ql --disable_caching scene.py SquareSumScene
```

**务必保留 `--disable_caching`。** Manim 把每段 `play` 缓存成 partial movie，缓存键不完整记录场景状态；改过镜头或文字后复用旧分段，会出现两个公式叠在同一帧的重影。`run.py` 在渲染前会删除 `media/videos/`，从干净状态开始。语音缓存 `media/voiceovers/` 不受影响。

只检查最后一帧：

```bash
python -m manim -s -ql scene.py SquareSumScene
```

## 几何：为什么三块一定拼得上

不是靠目测摆出来的。`assembly.py` 把每个小方块当成整数网格 `(x, y, z)` 上的一个单位立方体，用立方体的 24 个真旋转（带符号置换矩阵，行列式 +1）与整数平移枚举所有摆放，再求精确覆盖；动画里的滑入路径也在同一网格上用 BFS 求出，并逐格检查与已放置积木不重叠。

n = 4 时恰好有两组解（B、C 互换）：B、C 分别是 A 绕同一条体对角线轴 `(-1,-1,1)` 旋转 −120° 与 +120° 后的刚体（等价于绕 `(1,1,-1)` 反向旋转）。

| 校验项 | 结果 |
| --- | --- |
| A / B / C 格数 | 30 / 30 / 30 |
| 两两重叠 | A&B 0，A&C 0，B&C 0 |
| 三者并集 | 90 格，与目标区域完全相等（缺失 0，多余 0） |
| 刚体性 | 三块都等于原阶梯只做一次旋转 + 平移 |
| 目标分解 | 4×5×4 长方体 80 格 + 顶部阶梯 10 格 |
| 顶部各行 | 1、2、3、4（合计 10 = 1+2+3+4） |
| 等效高度 | 90 / (4×5) = 4.5 = n + ½ |
| 滑入路径 | B 15 步、C 9 步，逐格无重叠，终点等于求解位置 |

`python assembly.py` 会打印同样的报告；任何一项失败都会直接退出，不生成动画。

`n + ½` 是**等效高度**：90 个小方块铺满 4×5 的底面时，平均高度是 4.5 层，并不是真的有半个方块。

## 镜头与解说

配音为 `zh-CN-XiaoxiaoNeural`，语速 −4%，自然口语；每句单独合成，画面时长由真实音频驱动（`manim-voiceover` 的 tracker）。字幕固定在画面下方安全区 `y = -6.92`，一句一行，不与公式重叠。

| 镜头 | 开始 | 画面 | 解说 | 字幕 |
| --- | --- | --- | --- | --- |
| hook1 | 0.00 s | 标题 `1²+2²+⋯+n²=?`，四层方阵以爆炸高度依次出现 | 一的平方，加二的平方，一直加到 n 的平方。 | 从 1² 加到 n² |
| hook2 | 4.67 s | 问号轻跳两下 | 有没有一种办法，不用算，就能看出答案？ | 不用算，能看出来吗？ |
| build | 8.88 s | 3×3、2×2、1×1 逐层落位，右侧标出 4²、3²、2²、1² | 把每个平方，变成一层小方块。四层叠起来，就是一块阶梯积木。 | 一层 = 一个平方数 |
| copy | 15.67 s | 镜头拉开，左右出现 B、C 两块同形积木，`S+S+S=3S` 出现 | 现在，复制三份。三块积木，形状完全一样。 | 复制三份，形状一样 |
| fit_b | 21.10 s | B 整体转 −120°，从正前方绕过右侧，缓入空缺；A 压暗、接触边高亮 | 先固定一块。第二块转个方向，像俄罗斯方块一样，滑进空缺。 | 转个方向，滑进空缺 |
| fit_c | 29.80 s | C 从右侧画外直线滑入，停顿后坐实，成功轮廓亮起 | 再把第三块放进去。看，这些台阶，正在一点点互相补齐。 | 台阶互相补齐 |
| reveal | 36.35 s | 镜头转到 3/4 视角，标出 n、n+1、n，顶部台阶单独提亮 | 拼好之后，下面是一个长方体。上面，还多出一片三角形的台阶。 | 下面是长方体，上面是台阶 |
| top_count | 43.37 s | 顶部四行依次点亮，计数 1、2、3、4，写出 `1+2+⋯+n = n(n+1)/2` | 数一数：一、二、三、四，一共十块，正好是一加到 n。 | 10 块 = 1 + 2 + 3 + 4 |
| formula | 51.50 s | 长方体整体恢复饱和，分两行推出 `3S = n(n+1)·n + n(n+1)/2` 与 `3S = n(n+1)(n+½)` | 所以，三个积木的体积，就是长方体的体积，加上顶部这一片。 | 3S = 长方体 + 顶部台阶 |
| answer | 57.83 s | 积木缩小上移，公式 `S = …÷3` 过渡到最终平方和公式 | 两边除以三。平方和公式，就这样拼出来了。 | 平方和公式，拼出来了 |
| outro | 63.75 s | 其余元素淡出，只留公式停 2 秒，背景干净 | 原来，平方和公式，真的可以拼出来。 | 几何，让公式自己出现 |

（开始时间取自 `media/timeline.json`，以实际配音时长为准；成片 69.97 秒。）

## 可调参数

| 参数 | 位置 | 值 / 说明 |
| --- | --- | --- |
| `PREVIEW` | 环境变量 | `1` → 540×960@30；否则 1080×1920@60 |
| `CAMERA_SHOTS` | `scene.py` | 每个镜头的 `phi`、`theta`、`zoom`、`frame_center`；改镜头只改这里 |
| `OFFSET` | `scene.py` | `(-1.5, -2.0, -2.0)`，网格到世界坐标的平移 |
| `SIDE` | `scene.py` | 小方块棱长 0.98，留 0.02 的缝，避免共面闪烁 |
| `A_COL` / `B_COL` / `C_COL` | `scene.py` | 低饱和蓝 `#9DB9D4`、橙 `#E5B084`、绿 `#A8C6A6` |
| 压暗幅度 | `scene.py` | A 被遮挡时 0.45，顶部台阶对比时 0.72；用降饱和而非透明度，避免“幽灵方块” |
| `SUB_Y` | `scene.py` | 字幕高度 −6.92 |
| `VOICE` | `narration.py` | 音色、语速、音高、音量 |
| `LINES` / `SUBTITLES` | `narration.py` | 解说与字幕逐句独立，改词不影响几何 |
| `PRONUNCIATION` | `narration.py` | 多音字同音字引导（“数一数”→“属一属”，仍读 shǔ） |
| `PAUSE` | `narration.py` | 字幕条目之间的 0.18 s 呼吸 |
| `n` | `assembly.py` | 默认 4；求解与校验对一般 n 成立，但当前镜头按 n=4 编排 |

## 画面约束怎么落实

- **不穿模**：三块的最终位置来自精确覆盖；B、C 的滑入路径逐格校验，路径不是手摆的关键帧。
- **刚体**：B、C 只做一次整体旋转（绕各自的体对角线）和分段平移；内部方块从不单独移动。
- **遮挡关系正确**：Manim 的 `ThreeDCamera` 按深度排序；移动中的积木保持饱和，已放置的降饱和压暗，接触边短暂描边。
- **字幕与公式固定**：字幕、标题、体积公式都用 `add_fixed_in_frame_mobjects`，不随 3D 镜头旋转。
- **一个动作一个焦点**：镜头旋转与积木运动分时进行；B、C 的最终落位都放慢并留停顿，不加无意义的特效。
- **安全边距**：所有公式用 `fit_width` 限制在 7.6/9 个画幅单位内；竖屏左右至少约 6% 画面宽度的空白。
- **数量控制**：90 个方块各自是一个 `Cube` 组（6 面），总对象数约千级；没有逐帧重建几何。

## 验证情况

- 几何：`python assembly.py` 输出 `ok: True`，包括 90 格精确覆盖、三块刚体性、顶部 1+2+3+4、等效高度 4.5、B/C 滑入路径逐格无重叠。
- 渲染：以 Manim 0.19.1 + manim-voiceover 0.3.7 完整渲染 1080×1920@60；`--disable_caching` 并清空 `media/videos/` 后，公式过渡处只出现当前一行，没有重影。
- 镜头抽查：四层落位时 4²/3²/2²/1² 四个标签同时可见；复制镜头三块都在画框内；B 绕过正前方时不触边；C 从画外进入时的裁切发生在画面之外；最终画面只剩公式并停留 2 秒。
- 音画同步：每个 `voiceover` 块写出真实起止到 `media/timeline.json`，SRT 由同一份时间轴生成，字幕不重叠。
- 已知限制：本机无 LaTeX，公式用 Cambria Math 的 `MarkupText` 排版，字形与 LaTeX 略有差异；Edge TTS 需要联网（音频缓存在 `media/voiceovers/`）；字体缺失时 Manim 会回退，版面可能轻微变化。

## 文件

- `assembly.py` — 阶梯生成、精确覆盖求解、滑入路径 BFS、离散校验
- `scene.py` — 三维场景、镜头、拼装动画、公式与字幕
- `narration.py` — 解说词、字幕、多音字、Edge TTS 服务与 SRT 导出
- `run.py` / `run.sh` — 一键校验、配音、渲染、导出
- `requirements.txt` — Python 依赖
- `subtitles.srt` — 与成片同步的标准字幕
- `media/timeline.json`、`media/voice_durations.json` — 真实配音时间轴
- `media/voiceovers/` — 每句配音缓存（忽略提交）
- `square-sum-3d.mp4` — 成片
- `poster.jpg` — 网页封面
- `index.html` — 视频预览页
