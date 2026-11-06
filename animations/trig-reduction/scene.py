"""三角函数诱导公式：单位圆上的旋转与对称。

一条竖屏 9:16 的科普短片。全片只有一个连续场景：
点 P 沿单位圆运动，半径与坐标投影实时跟随，用旋转和镜像
解释 sin(kπ ± α)、cos(kπ ± α) 的符号，而不是让观众背公式。

声音说明
--------
``CUES`` 给出每句字幕与配音的起始时间，``NARRATION`` 保留完整解说词；
``narration.py`` 逐句合成语音，再按实测字幕时刻对齐。

时间轴
------
00.0–06.0  钩子：四个诱导公式，然后提出“真的需要背吗”
06.0–20.0  正弦入门 → 逆时针转 π：π+α，纵坐标变号
20.0–27.2  正弦负角：回到 α，顺时针转到 −α，纵坐标变号
27.2–34.0  正弦 π−α：关于纵轴对称，纵坐标不变
34.0–43.7  正弦全部讲完，再看余弦：+cos α，转到 π+α 变号
43.7–49.6  余弦负角：−α 与 α 共用横坐标
49.6–54.7  余弦 π−α：关于纵轴对称，横坐标变号
54.7–61.4  四个点同时在场，逐一比较三种对称关系
61.4–69.0  先列正弦公式，再快速补余弦；推广到任意整数 k

渲染
----
    python -m manim -qh --disable_caching scene.py TrigReductionScene
    # 低清预览：PREVIEW=1 python -m manim -ql --disable_caching scene.py TrigReductionScene

本机没有 LaTeX 时，数学文字自动退回 Cambria Math 的 MarkupText；
有 LaTeX 时优先使用 MathTex。两种路径的内容完全一致。
"""

from __future__ import annotations

import os
import shutil

import numpy as np
from manim import *

# ---------------------------------------------------------------------------
# 画幅与配色
# ---------------------------------------------------------------------------
PREVIEW = os.environ.get("PREVIEW") == "1"

config.frame_width = 9
config.frame_height = 16
config.pixel_width = 540 if PREVIEW else 1080
config.pixel_height = 960 if PREVIEW else 1920
config.frame_rate = 30
config.background_color = "#F5F0E6"

BG = "#F5F0E6"
INK = "#30343B"
INK_SOFT = "#6F7075"
TEAL = "#299C8D"      # 原始角与点
ORANGE = "#D6A04D"    # 负角对应点
BLUE = "#648BCB"      # 关于纵轴的镜像点
ROSE = "#C67591"      # 对径点
AXIS = "#A9A296"
DIM = "#8F8A80"
PAPER_DOT = "#D9D0BF"

CN_FONT = "Microsoft YaHei"
MATH_FONT = "Cambria Math"


def pick_font(candidates: list[str], fallback: str) -> str:
    """从系统已安装字体中挑第一个可用项，避免中文乱码。"""
    try:
        import manimpango

        installed = set(manimpango.list_fonts())
    except Exception:
        installed = set()
    for name in candidates:
        if name in installed:
            return name
    return fallback


CN_FONT = pick_font(
    ["Microsoft YaHei", "Noto Sans SC", "Source Han Sans SC", "SimHei", "KaiTi"],
    CN_FONT,
)
MATH_FONT = pick_font(["Cambria Math", "Segoe UI", "Arial"], MATH_FONT)

HAS_LATEX = shutil.which("latex") is not None

# ---------------------------------------------------------------------------
# 版面常量
# ---------------------------------------------------------------------------
CENTER = np.array([0.0, 1.35, 0.0])   # 单位圆圆心，全片不动
RADIUS = 2.55                          # 单位圆半径（1 个单位）
ALPHA = np.deg2rad(40)                 # 演示角，40° 让投影比例清晰
SUB_Y = -6.55                          # 字幕基线，留出平台底部安全区
LABEL_RADIUS = RADIUS + 0.62

# 每段的目标起止时间（秒）；用 hold_until 把画面锁在这些节拍上。
# 正弦的入门、π+α、−α、π−α 全部讲完，再按同样顺序讲余弦，
# 不穿插，公式和“符号从哪来”一一对应。
SEGMENTS = {
    "hook": (0.0, 6.0),
    "sin_intro": (6.0, 12.3),
    "sin_half": (12.3, 20.0),
    "sin_neg": (20.0, 27.2),
    "sin_mirror": (27.2, 34.0),
    "cos_intro": (34.0, 37.6),
    "cos_half": (37.6, 43.7),
    "cos_neg": (43.7, 49.6),
    "cos_mirror": (49.6, 54.7),
    "combine": (54.7, 61.4),
    "reveal": (61.4, 69.0),
}
TOTAL = SEGMENTS["reveal"][1]

# 原始解说词：与 CUES 保持一致，配音直接读 CUES。
NARRATION = {
    "hook1": "这些诱导公式，你还记得几个？",
    "hook2": "有没有可能……根本不用背？",
    "sin1": "先把点放在单位圆上。",
    "sin2": "点的纵坐标，就是正弦。",
    "half_q": "先看看转半圈。",
    "half_sin": "纵坐标由正变负。",
    "neg_q": "那角度变成负数呢？",
    "neg_sin": "纵坐标变号，正弦也变号。",
    "mirror_q": "再看 π 减 α。",
    "sin_mirror": "关于纵轴对称，纵坐标不变。",
    "cos_intro": "正弦讲完了，再来看余弦。",
    "cos_half": "转半圈，横坐标也变号。",
    "cos_neg": "角度取负，横坐标不变。",
    "cos_mirror": "关于纵轴对称，横坐标变号。",
    "combine1": "四个点，其实只差一个符号。",
    "reveal1": "所以，诱导公式不用背。",
    "reveal2": "转一转，就看懂了。",
}

# 字幕与起始时间；长句在 subtitle_text 里自动缩到安全宽度。
CUES: dict[str, tuple[float, str]] = {
    "hook1": (0.20, "这些诱导公式，你还记得几个？"),
    "hook2": (3.70, "有没有可能……根本不用背？"),
    "sin1": (6.20, "先把点放在单位圆上。"),
    "sin2": (8.90, "点的纵坐标，就是正弦。"),
    "half_q": (12.20, "先看看转半圈。"),
    "half_sin": (15.90, "纵坐标由正变负。"),
    "neg_q": (20.00, "那角度变成负数呢？"),
    "neg_sin": (23.70, "纵坐标变号，正弦也变号。"),
    "mirror_q": (27.40, "再看 π 减 α。"),
    "sin_mirror": (30.80, "关于纵轴对称，纵坐标不变。"),
    "cos_intro": (34.20, "正弦讲完了，再来看余弦。"),
    "cos_half": (37.70, "转半圈，横坐标也变号。"),
    "cos_neg": (43.80, "角度取负，横坐标不变。"),
    "cos_mirror": (49.60, "关于纵轴对称，横坐标变号。"),
    "combine1": (54.70, "四个点，其实只差一个符号。"),
    "reveal1": (61.50, "所以，诱导公式不用背。"),
    "reveal2": (65.60, "转一转，就看懂了。"),
}


# ---------------------------------------------------------------------------
# 小工具：字体、排版、安全宽度
# ---------------------------------------------------------------------------
def cn(text: str, size: float = 28, color: str = INK, weight: str = NORMAL) -> Text:
    return Text(text, font=CN_FONT, font_size=size, color=color, weight=weight)


def math_text(body: str, tex: str | None = None, size: float = 36, color: str = INK):
    """有 LaTeX 用 MathTex，否则用 Cambria Math 的 MarkupText。"""
    if HAS_LATEX and tex is not None:
        return MathTex(tex, font_size=size * 0.92, color=color)
    return MarkupText(body, font=MATH_FONT, font_size=size, color=color)


def fit_width(mob, max_width: float = 7.3):
    if mob.width > max_width:
        mob.scale_to_fit_width(max_width)
    return mob


def subtitle_text(text: str) -> Text:
    return fit_width(cn(text, 27, INK), 7.2).move_to([0, SUB_Y, 0])


def paper_dots() -> VGroup:
    """很淡的点阵，给浅黄背景一点草稿纸质感，不抢主体。"""
    dots = VGroup()
    for x in np.arange(-4.0, 4.01, 0.58):
        for y in np.arange(-7.4, 7.41, 0.58):
            dots.add(
                Dot(
                    [x, y, 0],
                    radius=0.012,
                    color=PAPER_DOT,
                    fill_opacity=0.55,
                    stroke_width=0,
                )
            )
    return dots


def label_position(angle_rad: float) -> np.ndarray:
    return CENTER + LABEL_RADIUS * np.array(
        [np.cos(angle_rad), np.sin(angle_rad), 0.0]
    )


def point_on_circle(angle_rad: float) -> np.ndarray:
    return CENTER + RADIUS * np.array(
        [np.cos(angle_rad), np.sin(angle_rad), 0.0]
    )


def mix(c1: str, c2: str, t: float):
    return interpolate_color(ManimColor(c1), ManimColor(c2), float(t))


# ---------------------------------------------------------------------------
# 场景
# ---------------------------------------------------------------------------
class TrigReductionScene(Scene):
    """一个连续场景；所有镜头参数固定，只有角度和颜色在变。"""

    # -------------------------------------------------------------- 生命周期
    def construct(self) -> None:
        self.add(paper_dots())
        self.subtitle: Text | None = None

        self.hook_phase()
        self.sin_intro_phase()
        self.sin_half_phase()
        self.sin_neg_phase()
        self.sin_mirror_phase()
        self.cos_intro_phase()
        self.cos_half_phase()
        self.cos_neg_phase()
        self.cos_mirror_phase()
        self.combine_phase()
        self.reveal_phase()

        self.hold_until(TOTAL)
        print(f"[timeline] end at {self.renderer.time:.2f}s")

    # -------------------------------------------------------------- 时间控制
    def hold_until(self, target: float) -> None:
        """等待到时间轴的 target 秒；动画若已超时则只记录，不倒退。"""
        now = self.renderer.time
        if target > now + 1e-3:
            self.wait(target - now)
        elif now > target + 0.05:
            print(f"[timing] overrun: {now:.2f}s > {target:.2f}s")

    def cue(self, key: str) -> None:
        """在预定时间切换字幕；旧字幕淡出，新字幕淡入。"""
        at, text = CUES[key]
        self.hold_until(at)
        new = subtitle_text(text)
        if self.subtitle is not None:
            self.play(FadeOut(self.subtitle, run_time=0.15))
        self.play(FadeIn(new, shift=UP * 0.05), run_time=0.20)
        self.subtitle = new
        print(f"[cue] {key:13s} {self.renderer.time:6.2f}s")

    def unsay(self, at: float | None = None) -> None:
        if at is not None:
            self.hold_until(at)
        if self.subtitle is not None:
            self.play(FadeOut(self.subtitle, run_time=0.25))
            self.subtitle = None

    # -------------------------------------------------------------- 运动基础
    def live_color(self):
        """hue: 0 青绿 → 1 玫红（对径点），0 → −1 橙黄（负角点）。

        mirror: 再叠加一层 0→1 的蓝色，用于关于纵轴的镜像点 π−α。
        """
        t = self.hue.get_value()
        if t >= 0:
            base = mix(TEAL, ROSE, min(t, 1.0))
        else:
            base = mix(TEAL, ORANGE, min(-t, 1.0))
        m = self.mirror.get_value()
        if m > 0:
            return interpolate_color(base, ManimColor(BLUE), min(m, 1.0))
        return base

    def point(self) -> np.ndarray:
        return point_on_circle(self.angle.get_value())

    def point_from(self, tracker: ValueTracker) -> np.ndarray:
        return point_on_circle(tracker.get_value())

    def build_live_objects(self) -> None:
        """半径、动点、正弦/余弦两层投影，全部绑定 tracker。

        两层各自有透明度：`sin_a` 管纵坐标投影，`cos_a` 管横坐标投影，
        这样同一时刻只突出一个三角函数，不把两条线堆在一张图里。
        """
        c = CENTER

        def radius():
            return Line(c, self.point(), color=self.live_color(), stroke_width=4.0)

        def dot():
            return Dot(self.point(), radius=0.095, color=self.live_color())

        # 投影用细实线：always_redraw 每帧重建 DashedLine 时虚线数量会变化，
        # Manim 的 become/align_points 在子路径数不一致时会越界，因此用实线。
        def sin_conn():
            p = self.point()
            return Line(
                p,
                [c[0], p[1], 0],
                color=self.live_color(),
                stroke_width=1.8,
                stroke_opacity=0.62 * self.sin_a.get_value(),
            )

        def sin_bar():
            p = self.point()
            return Line(
                c,
                [c[0], p[1], 0],
                color=self.live_color(),
                stroke_width=4.0,
                stroke_opacity=0.55 * self.sin_a.get_value(),
            )

        def sin_hl():
            p = self.point()
            return Line(
                c,
                [c[0], p[1], 0],
                color=self.live_color(),
                stroke_width=8.0,
                stroke_opacity=0.55 * self.hl_sin.get_value(),
            )

        def cos_conn():
            p = self.point()
            return Line(
                p,
                [p[0], c[1], 0],
                color=self.live_color(),
                stroke_width=1.8,
                stroke_opacity=0.62 * self.cos_a.get_value(),
            )

        def cos_bar():
            p = self.point()
            return Line(
                c,
                [p[0], c[1], 0],
                color=self.live_color(),
                stroke_width=4.0,
                stroke_opacity=0.55 * self.cos_a.get_value(),
            )

        def cos_hl():
            p = self.point()
            return Line(
                c,
                [p[0], c[1], 0],
                color=self.live_color(),
                stroke_width=8.0,
                stroke_opacity=0.55 * self.hl_cos.get_value(),
            )

        self.radius = always_redraw(radius)
        self.dot = always_redraw(dot)
        self.sin_conn_live = always_redraw(sin_conn)
        self.sin_bar_live = always_redraw(sin_bar)
        self.sin_hl_live = always_redraw(sin_hl)
        self.cos_conn_live = always_redraw(cos_conn)
        self.cos_bar_live = always_redraw(cos_bar)
        self.cos_hl_live = always_redraw(cos_hl)

    # -------------------------------------------------------------- 坐标工具
    def axis_foot(self, kind: str, p: np.ndarray) -> np.ndarray:
        if kind == "sin":
            return np.array([CENTER[0], p[1], 0.0])
        return np.array([p[0], CENTER[1], 0.0])

    def coord_label_pos(self, kind: str, p: np.ndarray) -> np.ndarray:
        """把 +sin α / −cos α 这类标签放在对应坐标条旁边。"""
        if kind == "sin":
            # 标签放在半径的另一侧，避免和斜着的半径重叠。
            side = 1.0 if p[0] < CENTER[0] else -1.0
            return np.array(
                [CENTER[0] + side * 0.88, (CENTER[1] + p[1]) / 2, 0.0]
            )
        # 余弦同理：点在下半圆时把标签放到横轴上方，免得被半径穿过。
        y = CENTER[1] - 0.46 if p[1] >= CENTER[1] else CENTER[1] + 0.46
        return np.array([(CENTER[0] + p[0]) / 2, y, 0.0])

    def coord_label(self, kind: str, text: str, color: str, angle: float):
        p = point_on_circle(angle)
        return math_text(text, None, 30, color).move_to(self.coord_label_pos(kind, p))

    def ghost_projection(self, kind: str, angle: float, color: str, text: str):
        """保留原角度的浅色投影 + 带正负号的标签，用来和新位置对照。"""
        p = point_on_circle(angle)
        foot = self.axis_foot(kind, p)
        conn = Line(
            p,
            foot,
            color=color,
            stroke_width=1.8,
            stroke_opacity=0.40,
        )
        bar = Line(
            CENTER,
            foot,
            color=color,
            stroke_width=3.2,
            stroke_opacity=0.28,
        )
        label = self.coord_label(kind, text, color, angle).set_opacity(0.72)
        return VGroup(conn, bar, label)

    def fade_live(self, mobjects, run_time: float = 0.4) -> None:
        """always_redraw 对象先停掉 updater，再淡出，否则透明度会被刷新。"""
        for mob in mobjects:
            mob.clear_updaters()
        self.play(FadeOut(VGroup(*mobjects)), run_time=run_time)

    # -------------------------------------------------------------- 01 钩子
    def hook_phase(self) -> None:
        """00–06 s：先让四个公式压过来，再提出疑问；不揭示答案。"""
        self.cue("hook1")

        specs = [
            ("<i>sin</i>(π − α)", r"\sin(\pi-\alpha)", -1.62, 4.10, -1.6),
            ("<i>cos</i>(π + α)", r"\cos(\pi+\alpha)", 1.62, 3.25, 1.2),
            ("<i>sin</i>(−α)", r"\sin(-\alpha)", -1.48, 2.35, -1.0),
            ("<i>cos</i>(2π − α)", r"\cos(2\pi-\alpha)", 1.62, 1.50, 1.6),
        ]
        hook = VGroup()
        for body, tex, x, y, tilt in specs:
            f = math_text(body, tex, 52, INK)
            f.move_to([x, y, 0]).rotate(tilt * DEGREES)
            hook.add(f)

        self.play(
            LaggedStart(
                *[FadeIn(f, shift=UP * 0.10) for f in hook],
                lag_ratio=0.24,
            ),
            run_time=2.15,
        )
        self.hold_until(3.00)

        # 向中央收缩、淡出：制造“记不住”的压迫感。
        self.play(
            *[
                f.animate.move_to([0, 2.45, 0]).scale(0.32).set_opacity(0.0)
                for f in hook
            ],
            run_time=0.55,
        )
        self.remove(hook)

        self.cue("hook2")
        question = cn("有没有可能……根本不用背？", 40, INK).move_to([0, 1.65, 0])
        self.play(FadeIn(question, shift=UP * 0.10), run_time=0.55)
        self.hold_until(5.55)
        self.play(FadeOut(question, run_time=0.35))

    # -------------------------------------------------------------- 02 正弦入门
    def sin_intro_phase(self) -> None:
        """06–12 s：只讲正弦——点的纵坐标。"""
        self.cue("sin1")

        self.circle = Circle(radius=RADIUS, color=INK, stroke_width=2.2)
        self.circle.move_to(CENTER)
        x_axis = Arrow(
            CENTER + [-3.35, 0, 0],
            CENTER + [3.35, 0, 0],
            buff=0,
            color=AXIS,
            stroke_width=1.2,
            max_tip_length_to_length_ratio=0.035,
        )
        y_axis = Arrow(
            CENTER + [0, -3.05, 0],
            CENTER + [0, 3.35, 0],
            buff=0,
            color=AXIS,
            stroke_width=1.2,
            max_tip_length_to_length_ratio=0.035,
        )
        self.axes = VGroup(x_axis, y_axis)

        self.play(Create(self.circle), Create(self.axes), run_time=1.10)

        self.angle = ValueTracker(0.0)
        self.hue = ValueTracker(0.0)
        self.mirror = ValueTracker(0.0)
        self.sin_a = ValueTracker(0.0)
        self.cos_a = ValueTracker(0.0)
        self.hl_sin = ValueTracker(0.0)
        self.hl_cos = ValueTracker(0.0)
        self.build_live_objects()
        self.add(
            self.radius,
            self.dot,
            self.sin_conn_live,
            self.sin_bar_live,
            self.sin_hl_live,
            self.cos_conn_live,
            self.cos_bar_live,
            self.cos_hl_live,
        )

        # 半径从 0 扫到 α；这是连续旋转，不是换点。
        self.play(
            self.angle.animate.set_value(ALPHA),
            run_time=1.35,
            rate_func=smooth,
        )

        self.cue("sin2")
        self.play(self.sin_a.animate.set_value(1.0), run_time=0.45)

        p = self.point()
        self.sin_intro_label = self.coord_label(
            "sin", "+<i>sin</i> α", TEAL, ALPHA
        )
        self.p_label = math_text("P", "P", 28, TEAL).next_to(p, UL, buff=0.10)
        self.alpha_label = math_text("α", r"\alpha", 30, TEAL).move_to(
            label_position(ALPHA)
        )
        self.play(FadeIn(self.sin_intro_label, shift=LEFT * 0.05), run_time=0.25)
        self.play(FadeIn(self.p_label), FadeIn(self.alpha_label), run_time=0.25)

        self.hold_until(10.70)
        self.play(
            Indicate(self.sin_intro_label, color=TEAL, scale_factor=1.10),
            run_time=0.55,
        )
        self.hold_until(11.95)

    # -------------------------------------------------------------- 03 转半圈 · 正弦
    def sin_half_phase(self) -> None:
        """12–20 s：只跟纵坐标，连续逆时针转 π，正变负。"""
        self.cue("half_q")
        self.play(FadeOut(self.sin_intro_label), run_time=0.20)

        # 原角度保留：对照点 + α + 浅色投影 + “+sin α”。
        self.ghost = Dot(
            self.point(), radius=0.075, color=TEAL, fill_opacity=0.35, stroke_width=0
        )
        self.ghost_sin = self.ghost_projection("sin", ALPHA, TEAL, "+<i>sin</i> α")
        self.alpha_label.set_opacity(0.75)
        self.play(FadeIn(self.ghost), FadeIn(self.ghost_sin), run_time=0.30)

        arc = self.make_arc(ALPHA, PI, ROSE)
        self.play(
            Create(arc),
            self.angle.animate.set_value(ALPHA + PI),
            run_time=2.60,
            rate_func=smooth,
        )
        self.cue("half_sin")
        self.play(self.hue.animate.set_value(1.0), run_time=0.30)
        self.play(self.hl_sin.animate.set_value(1.0), run_time=0.25)

        self.neg_sin_label = self.coord_label(
            "sin", "−<i>sin</i> α", ROSE, ALPHA + PI
        )
        self.live_angle_label = math_text(
            "<i>π</i> + α", r"\pi+\alpha", 30, ROSE
        ).move_to(label_position(ALPHA + PI))
        self.play(
            FadeIn(self.neg_sin_label),
            FadeIn(self.live_angle_label),
            run_time=0.30,
        )

        self.sin_formula = math_text(
            "<i>sin</i>(π + α) = −<i>sin</i> α",
            r"\sin(\pi+\alpha)=-\sin\alpha",
            36,
            INK,
        ).move_to([0, -2.45, 0])
        self.play(FadeIn(self.sin_formula, shift=UP * 0.08), run_time=0.40)

        self.hold_until(17.60)
        self.play(
            Indicate(self.sin_formula, color=ROSE, scale_factor=1.04),
            run_time=0.55,
        )
        self.hold_until(19.40)
        self.play(FadeOut(arc), run_time=0.20)

    # -------------------------------------------------------------- 04 负角 · 正弦
    def sin_neg_phase(self) -> None:
        """20–27 s：回到 α，再顺时针转到 −α，只跟纵坐标。"""
        self.cue("neg_q")

        # 回到原始角度，把上一段的结论收走。
        self.play(
            FadeOut(self.neg_sin_label),
            FadeOut(self.sin_formula),
            FadeOut(self.ghost_sin),
            FadeOut(self.live_angle_label),
            self.angle.animate.set_value(ALPHA),
            self.hue.animate.set_value(0.0),
            run_time=0.85,
            rate_func=smooth,
        )

        self.ghost_sin = self.ghost_projection("sin", ALPHA, TEAL, "+<i>sin</i> α")
        self.play(FadeIn(self.ghost_sin), run_time=0.30)

        arc = self.make_arc(ALPHA, -2 * ALPHA, ORANGE)
        self.play(
            Create(arc),
            self.angle.animate.set_value(-ALPHA),
            run_time=2.10,
            rate_func=smooth,
        )
        self.cue("neg_sin")
        self.play(self.hue.animate.set_value(-1.0), run_time=0.30)

        self.neg_sin_label = self.coord_label(
            "sin", "−<i>sin</i> α", ORANGE, -ALPHA
        )
        self.live_angle_label = math_text("−α", r"-\alpha", 30, ORANGE).move_to(
            label_position(-ALPHA)
        )
        self.connector = DashedLine(
            point_on_circle(-ALPHA),
            point_on_circle(ALPHA),
            dash_length=0.09,
            dashed_ratio=0.55,
            color=DIM,
            stroke_width=2.0,
            stroke_opacity=0.65,
        )
        self.play(
            FadeIn(self.neg_sin_label),
            FadeIn(self.live_angle_label),
            FadeIn(self.connector),
            run_time=0.30,
        )

        self.sin_formula = math_text(
            "<i>sin</i>(−α) = −<i>sin</i> α",
            r"\sin(-\alpha)=-\sin\alpha",
            36,
            INK,
        ).move_to([0, -2.45, 0])
        self.play(FadeIn(self.sin_formula, shift=UP * 0.08), run_time=0.40)

        self.hold_until(25.20)
        self.play(
            Indicate(self.sin_formula, color=ORANGE, scale_factor=1.04),
            run_time=0.55,
        )
        self.hold_until(26.80)
        self.play(FadeOut(arc), run_time=0.20)

    # -------------------------------------------------------------- 05 π − α · 正弦
    def sin_mirror_phase(self) -> None:
        """27–34 s：回到 α，再逆时针转到 π−α，纵坐标不变。"""
        self.cue("mirror_q")

        self.play(
            FadeOut(self.neg_sin_label),
            FadeOut(self.sin_formula),
            FadeOut(self.connector),
            FadeOut(self.live_angle_label),
            FadeOut(self.ghost_sin),
            self.angle.animate.set_value(ALPHA),
            self.hue.animate.set_value(0.0),
            run_time=0.80,
            rate_func=smooth,
        )

        self.ghost_sin = self.ghost_projection("sin", ALPHA, TEAL, "+<i>sin</i> α")
        self.play(FadeIn(self.ghost_sin), run_time=0.30)

        # 关于纵轴对称：x 变号，y 不变。
        arc = self.make_arc(ALPHA, PI - 2 * ALPHA, BLUE)
        self.play(
            Create(arc),
            self.angle.animate.set_value(PI - ALPHA),
            self.mirror.animate.set_value(1.0),
            run_time=1.90,
            rate_func=smooth,
        )
        self.cue("sin_mirror")

        self.sin_mirror_label = self.coord_label(
            "sin", "+<i>sin</i> α", BLUE, PI - ALPHA
        )
        self.live_angle_label = math_text(
            "<i>π</i> − α", r"\pi-\alpha", 30, BLUE
        ).move_to(label_position(PI - ALPHA))
        self.connector = DashedLine(
            point_on_circle(PI - ALPHA),
            point_on_circle(ALPHA),
            dash_length=0.10,
            dashed_ratio=0.55,
            color=BLUE,
            stroke_width=2.2,
            stroke_opacity=0.70,
        )
        self.play(
            FadeIn(self.sin_mirror_label),
            FadeIn(self.live_angle_label),
            FadeIn(self.connector),
            run_time=0.30,
        )

        self.sin_formula = math_text(
            "<i>sin</i>(π − α) = <i>sin</i> α",
            r"\sin(\pi-\alpha)=\sin\alpha",
            36,
            INK,
        ).move_to([0, -2.45, 0])
        self.play(FadeIn(self.sin_formula, shift=UP * 0.08), run_time=0.40)

        self.hold_until(32.00)
        self.play(
            Indicate(self.sin_formula, color=BLUE, scale_factor=1.04),
            run_time=0.55,
        )
        self.hold_until(33.60)
        self.play(FadeOut(arc), run_time=0.20)

    # -------------------------------------------------------------- 06 余弦入门
    def cos_intro_phase(self) -> None:
        """34–37.5 s：正弦全部讲完，再把画面收回 α，单独看横坐标。"""
        self.cue("cos_intro")

        # 把正弦段整套收走：标签、公式、虚线、投影、颜色。
        self.play(
            FadeOut(self.sin_mirror_label),
            FadeOut(self.sin_formula),
            FadeOut(self.connector),
            FadeOut(self.ghost_sin),
            FadeOut(self.live_angle_label),
            FadeOut(self.p_label),
            self.angle.animate.set_value(ALPHA),
            self.hue.animate.set_value(0.0),
            self.mirror.animate.set_value(0.0),
            self.sin_a.animate.set_value(0.0),
            self.hl_sin.animate.set_value(0.0),
            run_time=0.85,
            rate_func=smooth,
        )

        self.play(self.cos_a.animate.set_value(1.0), run_time=0.40)
        self.cos_intro_label = self.coord_label(
            "cos", "+<i>cos</i> α", TEAL, ALPHA
        )
        self.play(FadeIn(self.cos_intro_label, shift=DOWN * 0.05), run_time=0.25)

        self.hold_until(36.45)
        self.play(
            Indicate(self.cos_intro_label, color=TEAL, scale_factor=1.10),
            run_time=0.55,
        )
        self.hold_until(37.50)

    # -------------------------------------------------------------- 07 转半圈 · 余弦
    def cos_half_phase(self) -> None:
        """37.5–43.7 s：余弦同理，横坐标由正变负。"""
        self.cue("cos_half")
        self.ghost_cos = self.ghost_projection("cos", ALPHA, TEAL, "+<i>cos</i> α")
        self.play(
            FadeOut(self.cos_intro_label),
            FadeIn(self.ghost_cos),
            run_time=0.30,
        )

        arc = self.make_arc(ALPHA, PI, ROSE)
        self.play(
            Create(arc),
            self.angle.animate.set_value(ALPHA + PI),
            run_time=2.30,
            rate_func=smooth,
        )
        self.play(self.hue.animate.set_value(1.0), run_time=0.30)
        self.play(self.hl_cos.animate.set_value(1.0), run_time=0.25)

        self.neg_cos_label = self.coord_label(
            "cos", "−<i>cos</i> α", ROSE, ALPHA + PI
        )
        self.live_angle_label = math_text(
            "<i>π</i> + α", r"\pi+\alpha", 30, ROSE
        ).move_to(label_position(ALPHA + PI))
        self.play(
            FadeIn(self.neg_cos_label),
            FadeIn(self.live_angle_label),
            run_time=0.30,
        )

        self.cos_formula = math_text(
            "<i>cos</i>(π + α) = −<i>cos</i> α",
            r"\cos(\pi+\alpha)=-\cos\alpha",
            36,
            INK,
        ).move_to([0, -2.45, 0])
        self.play(FadeIn(self.cos_formula, shift=UP * 0.08), run_time=0.40)

        self.hold_until(42.00)
        self.play(
            Indicate(self.cos_formula, color=ROSE, scale_factor=1.04),
            run_time=0.55,
        )
        self.hold_until(43.40)
        self.play(FadeOut(arc), run_time=0.20)

    # -------------------------------------------------------------- 08 负角 · 余弦
    def cos_neg_phase(self) -> None:
        """43.7–49.6 s：回到 α，再转到 −α，横坐标不变。"""
        self.cue("cos_neg")

        self.play(
            FadeOut(self.neg_cos_label),
            FadeOut(self.cos_formula),
            FadeOut(self.ghost_cos),
            FadeOut(self.live_angle_label),
            self.angle.animate.set_value(ALPHA),
            self.hue.animate.set_value(0.0),
            run_time=0.80,
            rate_func=smooth,
        )
        self.play(self.hl_cos.animate.set_value(0.0), run_time=0.15)

        self.ghost_cos = self.ghost_projection("cos", ALPHA, TEAL, "+<i>cos</i> α")
        self.ghost_cos[2].move_to(
            [CENTER[0] + 0.98, CENTER[1] + 0.46, 0.0]
        )
        self.play(FadeIn(self.ghost_cos), run_time=0.30)

        self.cos_neg_arc = self.make_arc(ALPHA, -2 * ALPHA, ORANGE)
        self.play(
            Create(self.cos_neg_arc),
            self.angle.animate.set_value(-ALPHA),
            run_time=1.50,
            rate_func=smooth,
        )
        self.play(self.hue.animate.set_value(-1.0), run_time=0.25)
        self.play(self.hl_cos.animate.set_value(1.0), run_time=0.20)

        self.pos_cos_label = self.coord_label(
            "cos", "+<i>cos</i> α", ORANGE, -ALPHA
        )
        # 两个 +cos α 都在横轴上方，上下错开，避免彼此重叠或压到斜半径。
        self.pos_cos_label.move_to(
            [CENTER[0] + 0.98, CENTER[1] + 1.02, 0.0]
        )
        self.live_angle_label = math_text("−α", r"-\alpha", 30, ORANGE).move_to(
            label_position(-ALPHA)
        )
        self.connector = DashedLine(
            point_on_circle(-ALPHA),
            point_on_circle(ALPHA),
            dash_length=0.09,
            dashed_ratio=0.55,
            color=DIM,
            stroke_width=2.0,
            stroke_opacity=0.65,
        )
        self.play(
            FadeIn(self.pos_cos_label),
            FadeIn(self.live_angle_label),
            FadeIn(self.connector),
            run_time=0.30,
        )

        self.cos_formula = math_text(
            "<i>cos</i>(−α) = <i>cos</i> α",
            r"\cos(-\alpha)=\cos\alpha",
            36,
            INK,
        ).move_to([0, -2.45, 0])
        self.play(FadeIn(self.cos_formula, shift=UP * 0.08), run_time=0.35)

        self.hold_until(48.10)
        self.play(
            Indicate(self.cos_formula, color=ORANGE, scale_factor=1.04),
            run_time=0.55,
        )
        self.hold_until(49.50)

    # -------------------------------------------------------------- 09 π − α · 余弦
    def cos_mirror_phase(self) -> None:
        """49.6–54.7 s：回到 α，再转到 π−α，横坐标变号。"""
        self.cue("cos_mirror")

        self.play(
            FadeOut(self.pos_cos_label),
            FadeOut(self.cos_formula),
            FadeOut(self.ghost_cos),
            FadeOut(self.connector),
            FadeOut(self.live_angle_label),
            FadeOut(self.cos_neg_arc),
            self.angle.animate.set_value(ALPHA),
            self.hue.animate.set_value(0.0),
            self.mirror.animate.set_value(0.0),
            run_time=0.80,
            rate_func=smooth,
        )

        self.ghost_cos = self.ghost_projection("cos", ALPHA, TEAL, "+<i>cos</i> α")
        self.play(FadeIn(self.ghost_cos), run_time=0.30)

        self.cos_mirror_arc = self.make_arc(ALPHA, PI - 2 * ALPHA, BLUE)
        self.play(
            Create(self.cos_mirror_arc),
            self.angle.animate.set_value(PI - ALPHA),
            self.mirror.animate.set_value(1.0),
            run_time=1.60,
            rate_func=smooth,
        )
        self.play(self.hl_cos.animate.set_value(1.0), run_time=0.20)

        self.cos_mirror_label = self.coord_label(
            "cos", "−<i>cos</i> α", BLUE, PI - ALPHA
        )
        self.live_angle_label = math_text(
            "<i>π</i> − α", r"\pi-\alpha", 30, BLUE
        ).move_to(label_position(PI - ALPHA))
        self.connector = DashedLine(
            point_on_circle(PI - ALPHA),
            point_on_circle(ALPHA),
            dash_length=0.10,
            dashed_ratio=0.55,
            color=BLUE,
            stroke_width=2.2,
            stroke_opacity=0.70,
        )
        self.play(
            FadeIn(self.cos_mirror_label),
            FadeIn(self.live_angle_label),
            FadeIn(self.connector),
            run_time=0.30,
        )

        self.cos_formula = math_text(
            "<i>cos</i>(π − α) = −<i>cos</i> α",
            r"\cos(\pi-\alpha)=-\cos\alpha",
            36,
            INK,
        ).move_to([0, -2.45, 0])
        self.play(FadeIn(self.cos_formula, shift=UP * 0.08), run_time=0.35)

        self.hold_until(53.60)
        self.play(
            Indicate(self.cos_formula, color=BLUE, scale_factor=1.04),
            run_time=0.50,
        )
        self.hold_until(54.50)

    def make_arc(self, start: float, delta: float, color: str, opacity: float = 0.60) -> Arc:
        """带箭头的角度弧：逆时针 delta>0，顺时针 delta<0。

        半径比单位圆略大，画在圆外侧；若正好落在圆周上，会被同宽的
        黑色圆线整条盖住，只剩箭头看得见。
        """
        return Arc(
            radius=RADIUS + 0.16,
            start_angle=start,
            angle=delta,
            arc_center=CENTER,
            color=color,
            stroke_width=2.4,
            stroke_opacity=opacity,
        ).add_tip(tip_length=0.12)

    # -------------------------------------------------------------- 10 合并
    def combine_phase(self) -> None:
        """54.7–61.4 s：四个点同时在圆上，逐一比较三种对称。"""
        self.cue("combine1")
        self.play(
            FadeOut(self.cos_mirror_label),
            FadeOut(self.cos_formula),
            FadeOut(self.connector),
            FadeOut(self.ghost_cos),
            FadeOut(self.live_angle_label),
            FadeOut(self.cos_mirror_arc),
            self.angle.animate.set_value(ALPHA),
            self.hue.animate.set_value(0.0),
            self.mirror.animate.set_value(0.0),
            self.cos_a.animate.set_value(0.0),
            self.hl_cos.animate.set_value(0.0),
            run_time=0.70,
            rate_func=smooth,
        )
        self.play(FadeOut(self.ghost), run_time=0.15)

        # 让 live 的投影退场，画面只留四条半径和四个点。
        self.play(
            self.sin_a.animate.set_value(0.0),
            self.hl_sin.animate.set_value(0.0),
            run_time=0.15,
        )

        self.alpha_label.set_opacity(1.0)
        self.static_group = VGroup(self.alpha_label)

        # 对径点 π+α：探针从 α 逆时针扫 π。
        self.sweep_to(
            ALPHA + PI,
            ROSE,
            "<i>π</i> + α",
            r"\pi+\alpha",
            run_time=0.95,
        )
        # 关于纵轴的镜像点 π−α：探针从 α 逆时针扫到 140°。
        self.sweep_to(
            PI - ALPHA,
            BLUE,
            "<i>π</i> − α",
            r"\pi-\alpha",
            run_time=0.80,
        )
        # 负角点 −α：前面已经完整走过，这里直接让点留场。
        neg_radius, neg_dot = self.make_static_point(-ALPHA, ORANGE)
        neg_label = math_text("−α", r"-\alpha", 30, ORANGE).move_to(
            label_position(-ALPHA)
        )
        self.static_group.add(neg_radius, neg_dot, neg_label)
        self.play(FadeIn(neg_radius), FadeIn(neg_dot), FadeIn(neg_label), run_time=0.25)

        # 关系一：π−α 与 α——纵坐标相同，横坐标相反。
        self.show_relation(
            point_on_circle(PI - ALPHA),
            self.point(),
            BLUE,
            "π−α 与 α：纵坐标相同，横坐标相反",
        )

        # 关系二：π+α 与 α——对径点，横纵坐标都反号。
        self.show_relation(
            point_on_circle(ALPHA + PI),
            self.point(),
            ROSE,
            "π+α 与 α：横坐标、纵坐标都变号",
        )

        # 关系三：−α 与 α——横坐标相同，纵坐标相反。
        self.show_relation(
            point_on_circle(-ALPHA),
            self.point(),
            ORANGE,
            "−α 与 α：横坐标相同，纵坐标变号",
        )

        self.hold_until(61.35)
        self.fade_live([self.radius, self.dot], run_time=0.20)
        self.play(FadeOut(self.static_group), run_time=0.20)

    def sweep_to(
        self,
        end_angle: float,
        color: str,
        label_body: str,
        label_tex: str,
        run_time: float,
    ) -> None:
        """让一根半透明的彩色半径从 α 扫到目标角，再留下静态点和标签。"""
        sweep = ValueTracker(ALPHA)
        ghost_radius = always_redraw(
            lambda: Line(
                CENTER,
                self.point_from(sweep),
                color=color,
                stroke_width=2.4,
                stroke_opacity=0.55,
            )
        )
        ghost_dot = always_redraw(
            lambda: Dot(
                self.point_from(sweep),
                radius=0.070,
                color=color,
                fill_opacity=0.80,
                stroke_width=0,
            )
        )
        self.add(ghost_radius, ghost_dot)
        self.play(
            sweep.animate.set_value(end_angle),
            run_time=run_time,
            rate_func=smooth,
        )
        ghost_radius.clear_updaters()
        ghost_dot.clear_updaters()

        radius, dot = self.make_static_point(end_angle, color)
        label = math_text(label_body, label_tex, 30, color).move_to(
            label_position(end_angle)
        )
        self.static_group.add(radius, dot, label)
        self.play(
            FadeOut(ghost_radius),
            FadeOut(ghost_dot),
            FadeIn(radius),
            FadeIn(dot),
            FadeIn(label),
            run_time=0.30,
        )

    def make_static_point(self, angle_rad: float, color: str):
        p = point_on_circle(angle_rad)
        radius = Line(
            CENTER, p, color=color, stroke_width=2.3, stroke_opacity=0.85
        )
        dot = Dot(p, radius=0.075, color=color)
        return radius, dot

    def show_relation(
        self,
        p1: np.ndarray,
        p2: np.ndarray,
        color: str,
        caption: str,
    ) -> None:
        """用一条虚线 + 两个圆环 + 一句说明，强调一对点的坐标关系。"""
        connector = DashedLine(
            p1,
            p2,
            dash_length=0.10,
            dashed_ratio=0.55,
            color=color,
            stroke_width=2.4,
            stroke_opacity=0.80,
        )
        ring1 = Circle(radius=0.16, color=color, stroke_width=2.4).move_to(p1)
        ring2 = Circle(radius=0.16, color=color, stroke_width=2.4).move_to(p2)
        note = fit_width(cn(caption, 26, INK), 7.3).move_to([0, -2.40, 0])

        self.play(
            FadeIn(connector),
            FadeIn(ring1),
            FadeIn(ring2),
            FadeIn(note, shift=UP * 0.06),
            run_time=0.30,
        )
        self.hold_until(self.renderer.time + 0.45)
        self.play(
            FadeOut(connector),
            FadeOut(ring1),
            FadeOut(ring2),
            FadeOut(note),
            run_time=0.15,
        )

    # -------------------------------------------------------------- 11 揭晓
    def reveal_phase(self) -> None:
        """61.4–69 s：先合并三种操作，再列正弦、补余弦，推广到整数 k。"""
        self.cue("reveal1")

        rows = VGroup(
            self.rule_row("转半圈：坐标都变号", ROSE),
            self.rule_row("关于纵轴：正弦不变，余弦变号", BLUE),
            self.rule_row("角度取负：正弦变号，余弦不变", ORANGE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.34)
        rows.move_to([0, -2.75, 0])
        note = cn("k 为任意整数：每多转半圈，再变一次号", 24, INK_SOFT)
        note.next_to(rows, DOWN, buff=0.34)
        rules = VGroup(rows, note)

        self.play(
            LaggedStart(*[FadeIn(r, shift=UP * 0.06) for r in rows], lag_ratio=0.25),
            FadeIn(note),
            run_time=0.85,
        )

        self.hold_until(64.30)
        self.play(FadeOut(rules), run_time=0.30)

        # 先完整给出两条正弦公式。
        sin_row_1 = math_text(
            "<i>sin</i>(<i>k</i>π + α) = (−1)ᵏ <i>sin</i> α",
            r"\sin(k\pi+\alpha)=(-1)^k\sin\alpha",
            36,
            INK,
        ).move_to([0, -2.55, 0])
        sin_row_2 = math_text(
            "<i>sin</i>(<i>k</i>π − α) = (−1)ᵏ⁺¹ <i>sin</i> α",
            r"\sin(k\pi-\alpha)=(-1)^{k+1}\sin\alpha",
            36,
            INK,
        ).move_to([0, -3.30, 0])
        self.play(FadeIn(sin_row_1, shift=UP * 0.06), run_time=0.34)
        self.play(FadeIn(sin_row_2, shift=UP * 0.06), run_time=0.34)

        # 余弦只快速补一条，标出“同理”。
        cos_row = math_text(
            "<i>cos</i>(<i>k</i>π ± α) = (−1)ᵏ <i>cos</i> α",
            r"\cos(k\pi\pm\alpha)=(-1)^k\cos\alpha",
            36,
            INK,
        ).move_to([0, -4.05, 0])
        tail_note = cn("余弦同理 · k 为任意整数", 24, INK_SOFT)
        tail_note.next_to(cos_row, DOWN, buff=0.26)
        self.play(
            FadeIn(cos_row, shift=UP * 0.06),
            FadeIn(tail_note),
            run_time=0.40,
        )

        self.cue("reveal2")
        self.unsay(68.20)
        self.hold_until(TOTAL)

    def rule_row(self, text: str, color: str) -> VGroup:
        marker = Dot(radius=0.060, color=color, stroke_width=0)
        label = cn(text, 28, INK)
        return VGroup(marker, label).arrange(RIGHT, buff=0.22)
