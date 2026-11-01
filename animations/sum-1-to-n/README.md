# Sum 1→n — 视觉证明动画

用 Manim Community Edition 制作的竖屏无字证明：把 `1 + 2 + ⋯ + n` 的阶梯复制一份、旋转 180° 并平移，两块阶梯恰好拼成 `n × (n + 1)` 的长方形，于是总和是 `n(n + 1) / 2`。

成片：[sum-1-to-n.mp4](sum-1-to-n.mp4)（1080×1920，60 fps，约 16 秒，无音轨）

## 预览

直接用浏览器打开 [index.html](index.html)，或在本仓库根目录启动静态服务器：

```bash
python -m http.server 8123
# http://localhost:8123/animations/sum-1-to-n/
```

视频可用浏览器原生播放，页面无外部依赖。

## 渲染

依赖：Python 3.9+、Manim CE（本仓库使用 0.19.1 验证）、`ffmpeg` 在 `PATH` 中。

```bash
cd animations/sum-1-to-n
python -m manim sum_one_to_n.py SumOneToN
```

输出在 `media/videos/sum_one_to_n/1920p60/SumOneToN.mp4`。分辨率、帧率、画幅已在脚本顶部通过 `config` 固定为 1080×1920 / 60 fps / 9×16 场景单位，无需额外命令行参数。

只检查最后一帧：

```bash
python -m manim sum_one_to_n.py SumOneToN -s
```

## 涉及参数

| 参数 | 值 | 说明 |
| --- | --- | --- |
| `N` | `5` | 演示用的行数；行长为 1…5 |
| `S` | `1.0` | 单元格边长（场景单位），同时决定整体尺寸 |
| `BALL_R` | `0.40` | 小球半径，留出 0.10 的哑光间隙 |
| `RECT_CENTER` | `(0, 1.2)` | 长方形中心 |
| 背景 | `#FAF6EF` | 暖白 |
| 青绿 / 陶土 | `#6FA79D` / `#C98A6E` | 低饱和双色，边缘加同色深调描边 |
| 字体 | `Microsoft YaHei` / `Georgia` | 中文标注 / 公式；变量 `n` 用 `<i>` 斜体 |

改 `N` 后阶梯会自动按新行数生成；`S` 控制整体缩放，若明显超出 9×16 画幅，需要同步调整 `RECT_CENTER` 与公式位置。

## 几何与动画说明

- 阶梯 A 第 `r` 行（自下而上，`r = 0…n-1`）有 `r + 1` 个小球，左对齐，占据 5 列；
- 复制品绕自身包围盒中心旋转 180°，再向右平移一个格、向下回到基准位置，正好填满 6×5 长方形的补集；
- 两组合计 `n(n + 1)` 个小球，因此 `1 + 2 + ⋯ + n = n(n + 1) / 2`；
- 时间线：逐行生成阶梯约 3.3 s → 复制、旋转、平移约 3.7 s → 画长方形并标注约 2.5 s → 公式淡入并停留约 4.5 s。

动画不使用 LaTeX（无 `Tex` / `MathTex`），公式由 `MarkupText` + Pango 斜体标签排版，可直接渲染。

## 验证情况

- 已在本机用 Manim 0.19.1（Python 3.10，Windows）完整渲染成 MP4，时长 16.03 s，分辨率 1080×1920，60 fps，无音轨。
- 已逐帧抽查阶梯生成、复制旋转、长方形标注和公式四个阶段；`⋯` 使用 Georgia 可直接显示的 `···`（U+00B7）以避开缺字回退问题。
- 未在移动端真机验证 `index.html` 的播放样式。

## 文件

- `sum_one_to_n.py` — 场景源码
- `sum-1-to-n.mp4` — 成片
- `poster.jpg` — 页面封面
- `index.html` — 视频预览页
- `media/` — 本地渲染产物，已在 `.gitignore` 中忽略
