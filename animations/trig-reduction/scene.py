"""三角函数诱导公式：单位圆上的旋转与对称。

一条竖屏 9:16 的科普短片。全片只有一个连续场景：
点 P 沿单位圆运动，半径与坐标投影实时跟随，用旋转和镜像
解释 sin(kπ ± α)、cos(kπ ± α) 的符号，而不是让观众背公式。

声音说明
--------
当前版本不合成配音，只用画面字幕标记每句解说的位置；
``NARRATION`` 保留原始解说词，``CUES`` 给出每句的起始时间，
后续接 TTS 时可以直接按这些时间点对齐。

时间轴
------
00.0–06.0  钩子：四个诱导公式，然后提出“真的需要背吗”
06.0–14.0  建立单位圆，标出 cos α / sin α
14.0–25.0  逆时针转半圈：π + α，横纵坐标同时变号
25.0–36.0  顺时针转到 −α：横坐标不变，纵坐标变号
36.0–47.0  四个点同时在场，逐一比较三种对称关系
47.0–54.0  规则合并，推广到任意整数 k，停留 2 秒

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
SEGMENTS = {
    "hook": (0.0, 6.0),
    "circle": (6.0, 14.0),
    "half_turn": (14.0, 25.0),
    "negative": (25.0, 36.0),
    "combine": (36.0, 47.0),
    "reveal": (47.0, 54.0),
}
TOTAL = SEGMENTS["reveal"][1]

# 原始解说词：当前只作为注释/字幕使用，方便以后接 TTS。
NARRATION = {
    "hook1": "这些三角函数公式，你还记得几个？",
    "hook2": "有没有可能……根本不用背？",
    "circle": "其实，我们只需要一个圆。横坐标是 cos，纵坐标是 sin。",
    "half_q": "如果再转半圈呢？",
    "half_a": "转过半圈，横坐标和纵坐标，竟然都反了。",
    "neg_q": "那如果角度变成负数呢？",
    "neg_a": "这一次，横坐标不变，只有纵坐标反了。",
    "combine": "转半圈，再改变角度的正负方向……所有规律，都藏在这个圆里。",
    "reveal": "原来，诱导公式不用硬背。转一转，就看懂了。",
}

# 字幕与起始时间；长句在 subtitle_text 里自动缩到安全宽度。
CUES: dict[str, tuple[float, str]] = {
    "hook1": (0.20, "这些三角函数公式，你还记得几个？"),
    "hook2": (3.60, "有没有可能……根本不用背？"),
    "circle": (6.05, "其实，我们只需要一个圆。"),
    "circle_coords": (9.00, "横坐标是 cos，纵坐标是 sin。"),
    "half_q": (14.10, "如果再转半圈呢？"),
    "half_a": (18.50, "转过半圈，横坐标和纵坐标，竟然都反了。"),
    "neg_q": (26.30, "那如果角度变成负数呢？"),
    "neg_a": (29.80, "这一次，横坐标不变，只有纵坐标反了。"),
    "combine1": (36.20, "转半圈，再改变角度的正负方向……"),
    "combine2": (41.00, "所有规律，都藏在这个圆里。"),
    "reveal": (47.20, "原来，诱导公式不用硬背。转一转，就看懂了。"),
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
        self.circle_phase()
        self.half_turn_phase()
        self.negative_phase()
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
        """hue: 0 青绿 → 1 玫红（对径点），0 → −1 橙黄（负角点）。"""
        t = self.hue.get_value()
        if t >= 0:
            return mix(TEAL, ROSE, min(t, 1.0))
        return mix(TEAL, ORANGE, min(-t, 1.0))

    def point(self) -> np.ndarray:
        return point_on_circle(self.angle.get_value())

    def point_from(self, tracker: ValueTracker) -> np.ndarray:
        return point_on_circle(tracker.get_value())

    def build_live_objects(self) -> None:
        """半径、动点、坐标投影和坐标轴上的高亮段，全部绑定 tracker。"""
        c = CENTER

        def radius():
            return Line(c, self.point(), color=self.live_color(), stroke_width=4.0)

        def dot():
            return Dot(self.point(), radius=0.095, color=self.live_color())

        def proj_opacity() -> float:
            return 0.62 * self.proj_alpha.get_value()

        # 投影用细实线：always_redraw 每帧重建 DashedLine 时虚线数量会变化，
        # Manim 的 become/align_points 在子路径数不一致时会越界，因此用实线。
        def x_proj():
            p = self.point()
            return Line(
                p,
                [p[0], c[1], 0],
                color=self.live_color(),
                stroke_width=1.8,
                stroke_opacity=proj_opacity(),
            )

        def y_proj():
            p = self.point()
            return Line(
                p,
                [c[0], p[1], 0],
                color=self.live_color(),
                stroke_width=1.8,
                stroke_opacity=proj_opacity(),
            )

        def x_bar():
            p = self.point()
            return Line(
                c,
                [p[0], c[1], 0],
                color=self.live_color(),
                stroke_width=4.0,
                stroke_opacity=0.55 * self.proj_alpha.get_value(),
            )

        def y_bar():
            p = self.point()
            return Line(
                c,
                [c[0], p[1], 0],
                color=self.live_color(),
                stroke_width=4.0,
                stroke_opacity=0.55 * self.proj_alpha.get_value(),
            )

        def hl_x():
            p = self.point()
            return Line(
                c,
                [p[0], c[1], 0],
                color=self.live_color(),
                stroke_width=8.0,
                stroke_opacity=0.55 * self.hlx.get_value(),
            )

        def hl_y():
            p = self.point()
            return Line(
                c,
                [c[0], p[1], 0],
                color=self.live_color(),
                stroke_width=8.0,
                stroke_opacity=0.55 * self.hly.get_value(),
            )

        self.radius = always_redraw(radius)
        self.dot = always_redraw(dot)
        self.x_proj = always_redraw(x_proj)
        self.y_proj = always_redraw(y_proj)
        self.x_bar = always_redraw(x_bar)
        self.y_bar = always_redraw(y_bar)
        self.hl_x_line = always_redraw(hl_x)
        self.hl_y_line = always_redraw(hl_y)

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

    # -------------------------------------------------------------- 02 单位圆
    def circle_phase(self) -> None:
        """06–14 s：缓缓画出单位圆；半径从 0° 转到 α，再出现坐标投影。"""
        self.cue("circle")
        self.hold_until(6.35)

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

        self.play(Create(self.circle), Create(self.axes), run_time=1.20)

        self.angle = ValueTracker(0.0)
        self.hue = ValueTracker(0.0)
        self.proj_alpha = ValueTracker(0.0)
        self.hlx = ValueTracker(0.0)
        self.hly = ValueTracker(0.0)
        self.build_live_objects()
        self.add(self.radius, self.dot)

        # 半径从 0 扫到 α；这是连续旋转，不是换点。
        self.play(
            self.angle.animate.set_value(ALPHA),
            run_time=1.35,
            rate_func=smooth,
        )

        self.cue("circle_coords")
        self.add(
            self.x_proj,
            self.y_proj,
            self.x_bar,
            self.y_bar,
            self.hl_x_line,
            self.hl_y_line,
        )
        self.play(self.proj_alpha.animate.set_value(1.0), run_time=0.45)

        p = self.point()
        cos_label = math_text("<i>cos</i> α", r"\cos\alpha", 30, TEAL)
        cos_label.move_to([p[0], CENTER[1] - 0.46, 0])
        sin_label = math_text("<i>sin</i> α", r"\sin\alpha", 30, TEAL)
        sin_label.next_to([CENTER[0], p[1], 0], LEFT, buff=0.18)
        p_label = math_text("P", "P", 28, TEAL)
        p_label.next_to(p, UR, buff=0.10)

        self.play(FadeIn(cos_label, shift=DOWN * 0.05), run_time=0.25)
        self.play(FadeIn(sin_label, shift=LEFT * 0.05), run_time=0.25)
        self.play(FadeIn(p_label), run_time=0.20)
        self.hold_until(10.80)
        self.play(Indicate(cos_label, color=TEAL, scale_factor=1.10), run_time=0.55)
        self.hold_until(11.70)
        self.play(Indicate(sin_label, color=TEAL, scale_factor=1.10), run_time=0.55)

        self.labels_unit = VGroup(cos_label, sin_label, p_label)
        self.hold_until(13.55)
        self.play(FadeOut(self.labels_unit), run_time=0.35)

    # -------------------------------------------------------------- 03 转半圈
    def half_turn_phase(self) -> None:
        """14–25 s：从 α 连续逆时针转 π 到 π+α，两坐标同时变号。"""
        self.cue("half_q")
        self.hold_until(15.00)

        # 原位置留一个浅色对照点。
        self.ghost = Dot(
            self.point(), radius=0.075, color=TEAL, fill_opacity=0.35, stroke_width=0
        )
        self.ghost_label = math_text("α", r"\alpha", 30, TEAL).move_to(
            label_position(ALPHA)
        )
        self.ghost_label.set_opacity(0.55)
        self.play(FadeIn(self.ghost), FadeIn(self.ghost_label), run_time=0.28)

        arc = Arc(
            radius=RADIUS,
            start_angle=ALPHA,
            angle=PI,
            arc_center=CENTER,
            color=ROSE,
            stroke_width=2.2,
            stroke_opacity=0.45,
        ).add_tip(tip_length=0.10)
        self.play(
            Create(arc),
            self.angle.animate.set_value(ALPHA + PI),
            run_time=3.00,
            rate_func=smooth,
        )
        self.play(self.hue.animate.set_value(1.0), run_time=0.30)

        self.cue("half_a")

        # 先横坐标，再纵坐标，一次只强调一条。
        self.play(self.hlx.animate.set_value(1.0), run_time=0.35)
        cos_formula = math_text(
            "<i>cos</i>(π + α) = −<i>cos</i> α",
            r"\cos(\pi+\alpha)=-\cos\alpha",
            36,
            INK,
        ).move_to([0, -2.35, 0])
        self.play(FadeIn(cos_formula, shift=UP * 0.08), run_time=0.40)

        self.hold_until(20.10)
        self.play(self.hly.animate.set_value(1.0), run_time=0.35)
        sin_formula = math_text(
            "<i>sin</i>(π + α) = −<i>sin</i> α",
            r"\sin(\pi+\alpha)=-\sin\alpha",
            36,
            INK,
        ).move_to([0, -3.25, 0])
        self.play(FadeIn(sin_formula, shift=UP * 0.08), run_time=0.40)
        self.half_formulas = VGroup(cos_formula, sin_formula)

        self.hold_until(21.75)
        self.play(
            Indicate(cos_formula, color=ROSE, scale_factor=1.04), run_time=0.55
        )
        self.hold_until(22.65)
        self.play(
            Indicate(sin_formula, color=ROSE, scale_factor=1.04), run_time=0.55
        )

        self.hold_until(24.45)
        self.play(
            FadeOut(self.half_formulas),
            self.hlx.animate.set_value(0.0),
            self.hly.animate.set_value(0.0),
            FadeOut(arc),
            run_time=0.45,
        )

    # -------------------------------------------------------------- 04 负角
    def negative_phase(self) -> None:
        """25–36 s：顺时针转到 −α，强调关于 x 轴的镜像。"""
        self.hold_until(25.00)
        self.play(
            self.angle.animate.set_value(ALPHA),
            self.hue.animate.set_value(0.0),
            run_time=1.05,
            rate_func=smooth,
        )

        self.cue("neg_q")
        self.hold_until(27.00)

        arc = Arc(
            radius=RADIUS,
            start_angle=ALPHA,
            angle=-2 * ALPHA,
            arc_center=CENTER,
            color=ORANGE,
            stroke_width=2.2,
            stroke_opacity=0.5,
        ).add_tip(tip_length=0.10)
        self.play(
            Create(arc),
            self.angle.animate.set_value(-ALPHA),
            run_time=2.35,
            rate_func=smooth,
        )
        self.play(self.hue.animate.set_value(-1.0), run_time=0.30)

        neg_label = math_text("−α", r"-\alpha", 30, ORANGE).move_to(
            label_position(-ALPHA)
        )
        self.play(FadeIn(neg_label), run_time=0.25)

        self.cue("neg_a")

        # 同一个 x：两点由一条竖直虚线连起来。
        connector = DashedLine(
            self.point(),
            point_on_circle(ALPHA),
            dash_length=0.09,
            dashed_ratio=0.55,
            color=DIM,
            stroke_width=2.0,
            stroke_opacity=0.65,
        )
        self.play(FadeIn(connector), run_time=0.25)

        self.play(self.hlx.animate.set_value(1.0), run_time=0.35)
        cos_formula = math_text(
            "<i>cos</i>(−α) = <i>cos</i> α",
            r"\cos(-\alpha)=\cos\alpha",
            36,
            INK,
        ).move_to([0, -2.35, 0])
        self.play(FadeIn(cos_formula, shift=UP * 0.08), run_time=0.40)

        self.hold_until(31.40)
        self.play(self.hly.animate.set_value(1.0), run_time=0.35)
        sin_formula = math_text(
            "<i>sin</i>(−α) = −<i>sin</i> α",
            r"\sin(-\alpha)=-\sin\alpha",
            36,
            INK,
        ).move_to([0, -3.25, 0])
        self.play(FadeIn(sin_formula, shift=UP * 0.08), run_time=0.40)
        self.neg_formulas = VGroup(cos_formula, sin_formula)

        self.hold_until(33.10)
        self.play(
            Indicate(cos_formula, color=ORANGE, scale_factor=1.04), run_time=0.55
        )
        self.hold_until(34.00)
        self.play(
            Indicate(sin_formula, color=ORANGE, scale_factor=1.04), run_time=0.55
        )

        self.hold_until(35.25)
        self.play(
            FadeOut(self.neg_formulas),
            FadeOut(connector),
            FadeOut(neg_label),
            FadeOut(arc),
            self.hlx.animate.set_value(0.0),
            self.hly.animate.set_value(0.0),
            run_time=0.50,
        )

    # -------------------------------------------------------------- 05 合并
    def combine_phase(self) -> None:
        """36–47 s：四个点同时在圆上，逐一比较三种对称。"""
        self.cue("combine1")
        self.play(
            self.angle.animate.set_value(ALPHA),
            self.hue.animate.set_value(0.0),
            run_time=0.80,
            rate_func=smooth,
        )
        self.play(FadeOut(self.ghost), FadeOut(self.ghost_label), run_time=0.25)

        # 让 live 的投影退场，画面只留四条半径和四个点。
        self.play(self.proj_alpha.animate.set_value(0.0), run_time=0.30)

        self.static_group = VGroup()
        self.alpha_label = math_text("α", r"\alpha", 30, TEAL).move_to(
            label_position(ALPHA)
        )
        self.static_group.add(self.alpha_label)
        self.play(FadeIn(self.alpha_label), run_time=0.25)

        # 对径点 π+α：探针从 α 逆时针扫 π。
        self.sweep_to(
            ALPHA + PI,
            ROSE,
            "<i>π</i> + α",
            r"\pi+\alpha",
            run_time=1.30,
        )
        # 关于纵轴的镜像点 π−α：探针从 α 逆时针扫到 140°。
        self.sweep_to(
            PI - ALPHA,
            BLUE,
            "<i>π</i> − α",
            r"\pi-\alpha",
            run_time=1.10,
        )
        # 负角点 −α：前面已经完整走过，这里直接让点留场。
        neg_radius, neg_dot = self.make_static_point(-ALPHA, ORANGE)
        neg_label = math_text("−α", r"-\alpha", 30, ORANGE).move_to(
            label_position(-ALPHA)
        )
        self.static_group.add(neg_radius, neg_dot, neg_label)
        self.play(FadeIn(neg_radius), FadeIn(neg_dot), FadeIn(neg_label), run_time=0.30)

        self.cue("combine2")

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

        self.hold_until(46.20)
        self.fade_live([self.radius, self.dot], run_time=0.35)
        self.play(FadeOut(self.static_group), run_time=0.35)

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
            run_time=0.35,
        )
        self.hold_until(self.renderer.time + 0.95)
        self.play(
            FadeOut(connector),
            FadeOut(ring1),
            FadeOut(ring2),
            FadeOut(note),
            run_time=0.20,
        )

    # -------------------------------------------------------------- 06 揭晓
    def reveal_phase(self) -> None:
        """47–54 s：合并规律，推广到任意整数 k，最后停留 2 秒。"""
        self.cue("reveal")
        self.hold_until(47.80)

        rows = VGroup(
            self.rule_row("半圈数为偶数：坐标不变", TEAL),
            self.rule_row("半圈数为奇数：坐标都变号", ROSE),
            self.rule_row("角度取负：sin 变号，cos 不变", ORANGE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.38)
        rows.move_to([0, -2.55, 0])
        note = cn("k 为任意整数：每转半圈，再变一次号", 24, INK_SOFT)
        note.next_to(rows, DOWN, buff=0.42)
        rules = VGroup(rows, note)

        self.play(
            LaggedStart(*[FadeIn(r, shift=UP * 0.06) for r in rows], lag_ratio=0.25),
            FadeIn(note),
            run_time=0.90,
        )

        self.hold_until(50.20)
        self.play(FadeOut(rules), run_time=0.30)

        formulas = VGroup(
            math_text(
                "<i>sin</i>(<i>k</i>π + α) = (−1)ᵏ <i>sin</i> α",
                r"\sin(k\pi+\alpha)=(-1)^k\sin\alpha",
                36,
                INK,
            ),
            math_text(
                "<i>sin</i>(<i>k</i>π − α) = (−1)ᵏ⁺¹ <i>sin</i> α",
                r"\sin(k\pi-\alpha)=(-1)^{k+1}\sin\alpha",
                36,
                INK,
            ),
            math_text(
                "<i>cos</i>(<i>k</i>π ± α) = (−1)ᵏ <i>cos</i> α",
                r"\cos(k\pi\pm\alpha)=(-1)^k\cos\alpha",
                36,
                INK,
            ),
        ).arrange(DOWN, buff=0.32)
        formulas.move_to([0, -3.05, 0])
        final_note = cn("k 为任意整数", 24, INK_SOFT).next_to(formulas, DOWN, buff=0.38)

        for f in formulas:
            self.play(FadeIn(f, shift=UP * 0.06), run_time=0.34)
        self.play(FadeIn(final_note), run_time=0.25)

        self.unsay(52.10)
        self.hold_until(TOTAL)

    def rule_row(self, text: str, color: str) -> VGroup:
        marker = Dot(radius=0.060, color=color, stroke_width=0)
        label = cn(text, 28, INK)
        return VGroup(marker, label).arrange(RIGHT, buff=0.22)
