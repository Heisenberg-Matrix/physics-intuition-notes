"""谁规定一圈必须是 360°？——弧度制，一次让角度拥有两种能力。

一条竖屏 9:16 的科普短片。它不从定义出发，而是先把“一圈记成几份”
这件事还原成人的选择：360 只是习惯，换成 4 份、1 份都不影响记录旋转。
随后出现新的需求——量一段弧有多长——逼着我们把“圈数”换算成长度，
换算式里自然冒出一个系数 2π/N。把 N 选成 2π，系数变成 1，
于是同一个数字 θ 既能记录转了多少，又能直接给出弧长 s = rθ。
π 在这里始终是周长与直径的比，不是角度；θ = s/r 是两个长度之比，
不是长度本身。

声音说明
--------
``CUES`` 给出每句字幕与配音的起始时间，``NARRATION`` 保留完整解说词；
``narration.py`` 逐句合成语音，再按实测字幕时刻对齐。

时间轴
------
00.0–17.4  一圈 = 360° 只是习惯；改成 4 份、1 份，照样记录旋转
17.4–34.9  新需求：这段弧有多长？把圆周拉直，得到 C = 2πr 与 π = C/d
34.9–57.6  弧长 = 整圈周长 × 转过的圈数；定义 N、θ，代出 s = (2π/N)·r·θ
57.6–64.9  令 2π/N = 1，N = 2π，系数消失，公式只剩 s = rθ
64.9–97.1  半径当软尺：弧长 = r 时 θ = 1；2r、3r 同理；连续变化；一石二鸟
97.1–107.3 为什么偏偏是 2π：整圈弧长 2πr，所以 θ = 2π；半圈 π，四分之一 π/2
107.3–115.0 360° = 2π 弧度；一个数字，两种用途

渲染
----
    python -m manim -qh --disable_caching scene.py RadianScene
    # 低清预览：PREVIEW=1 python -m manim -ql --disable_caching scene.py RadianScene
    # 只渲染前 N 段：STAGE=3 python -m manim -ql ...（用于逐段检查版面）

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
STAGE = int(os.environ.get("STAGE", "9"))

config.frame_width = 9
config.frame_height = 16
config.pixel_width = 540 if PREVIEW else 1080
config.pixel_height = 960 if PREVIEW else 1920
config.frame_rate = 30
config.background_color = "#F5F0E6"

BG = "#F5F0E6"
INK = "#30343B"
INK_SOFT = "#6F7075"
TEAL = "#299C8D"      # 角度 θ、旋转
ORANGE = "#D6A04D"    # 弧长 s、长度
BLUE = "#648BCB"      # 半径 r
ROSE = "#C67591"      # 系数、π、强调
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
CENTER = np.array([0.0, 1.90, 0.0])   # 圆心，全片不动
RADIUS = 1.95                          # 圆半径
SUB_Y = -6.55                          # 字幕基线
TAU = 2 * np.pi

# 每段的目标起止时间（秒）；hold_until 把画面锁在这些节拍上。
SEGMENTS = {
    "intro": (0.0, 17.4),
    "need": (17.4, 34.9),
    "formula": (34.9, 57.6),
    "choose": (57.6, 64.9),
    "ruler": (64.9, 97.1),
    "why": (97.1, 107.3),
    "close": (107.3, 115.0),
}
TOTAL = SEGMENTS["close"][1]

# 完整解说词：这是配音实际念的口语版本，``narration.py`` 直接读它。
# 字幕里用 π、θ、2πr 这些符号，念出来是“派”“西塔”“二派 r”，
# 两者分开写，眼睛看到的和耳朵听到的都自然。
NARRATION = {
    "hook1": "一圈，为什么是三百六十度？",
    "hook2": "谁规定，一圈必须是三百六？",
    "four": "如果我说，一圈就是四份呢？",
    "one": "干脆一点，把一圈记作一。",
    "record": "这么记，转了多少，一点不耽误。",
    "need": "可如果我问：这段弧有多长？",
    "unroll": "先别急着算，把圆周拉直看看。",
    "circum": "整圈的长度，是派乘直径。",
    "pi": "派是周长比直径，不是角度。",
    "formula": "回到弧长：周长乘转过的圈数。",
    "define": "把一圈分成 N 份，转过西塔份。",
    "example": "比如 N 等于四，转一份西塔是一。",
    "assemble": "于是 s 等于二派 r，乘西塔比 N。",
    "coef": "整理一下，系数是二派比 N。",
    "choose": "N 随我们定，干脆等于二派。",
    "rform": "系数变成一，只剩 s 等于 r 乘西塔。",
    "ruler": "半径就是一把软尺，贴着圆弧量。",
    "onerad": "弧长正好等于 r，这就是一弧度。",
    "twothree": "两倍 r 是两弧度，三倍是三弧度。",
    "chord": "注意，量的是弧段，不是直弦。",
    "live": "角度连续转，弧长就连续变。",
    "ratio": "西塔是 s 比 r，本身不是长度。",
    "split": "同一个西塔，既记旋转，又算弧长。",
    "birds": "一个数字，两种用途，一石二鸟。",
    "why": "为什么是二派？整圈弧长二派 r。",
    "half": "半圈是派，四分之一是二分之派。",
    "close": "角度没变长，只是换了个记法。",
    "name": "这就是弧度制。",
}

# 字幕与起始时间；字幕统一缩到安全宽度 7.2。
CUES: dict[str, tuple[float, str]] = {
    "hook1": (0.40, "一圈，为什么是 360°？"),
    "hook2": (3.70, "谁规定，一圈必须是 360°？"),
    "four": (7.00, "如果我说，一圈就是 4 份呢？"),
    "one": (10.40, "干脆一点，把一圈记作 1。"),
    "record": (13.80, "这么记，转了多少，一点不耽误。"),
    "need": (17.40, "可如果我问：这段弧有多长？"),
    "unroll": (21.60, "先别急着算，把圆周拉直看看。"),
    "circum": (26.40, "整圈的长度，是 π 乘直径。"),
    "pi": (30.40, "π 是周长比直径，不是角度。"),
    "formula": (34.90, "回到弧长：周长乘转过的圈数。"),
    "define": (40.00, "把一圈分成 N 份，转过 θ 份。"),
    "example": (44.60, "比如 N 等于 4，转一份 θ 是 1。"),
    "assemble": (49.60, "于是 s = 2πr × θ/N。"),
    "coef": (53.90, "整理一下，系数是 2π/N。"),
    "choose": (57.60, "N 随我们定，干脆等于 2π。"),
    "rform": (60.80, "系数变成 1，只剩 s = rθ。"),
    "ruler": (64.90, "半径就是一把软尺，贴着圆弧量。"),
    "onerad": (68.90, "弧长正好等于 r，这就是 1 弧度。"),
    "twothree": (73.10, "两倍 r 是 2 弧度，三倍是 3 弧度。"),
    "chord": (77.30, "注意，量的是弧段，不是直弦。"),
    "live": (81.00, "角度连续转，弧长就连续变。"),
    "ratio": (85.30, "θ 是 s 比 r，本身不是长度。"),
    "split": (89.30, "同一个 θ，既记旋转，又算弧长。"),
    "birds": (93.30, "一个数字，两种用途，一石二鸟。"),
    "why": (97.10, "为什么是 2π？整圈弧长 2πr。"),
    "half": (102.10, "半圈是 π，四分之一是 π/2。"),
    "close": (107.30, "角度没变长，只是换了个记法。"),
    "name": (110.90, "这就是弧度制。"),
}


# ---------------------------------------------------------------------------
# 小工具：字体、排版、安全宽度
# ---------------------------------------------------------------------------
def cn(text: str, size: float = 26, color: str = INK, weight: str = NORMAL,
       t2c: dict[str, str] | None = None) -> Text:
    return Text(text, font=CN_FONT, font_size=size, color=color,
                weight=weight, t2c=t2c)


def m(body: str, size: float = 36, color: str = INK) -> MarkupText:
    """Cambria Math 的数学排字；变量用斜体。"""
    return MarkupText(body, font=MATH_FONT, font_size=size, color=color)


def it(name: str) -> str:
    return f"<i>{name}</i>"


def span(body: str, color: str) -> str:
    return f'<span foreground="{color}">{body}</span>'


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


def dirv(angle: float) -> np.ndarray:
    return np.array([np.cos(angle), np.sin(angle), 0.0])


def point_at(angle: float, radius: float = RADIUS) -> np.ndarray:
    return CENTER + radius * dirv(angle)


def arc_at(angle: float, color: str, width: float = 5.0,
           radius: float = RADIUS, start: float = 0.0) -> Arc:
    return Arc(
        radius=radius,
        start_angle=start,
        angle=max(angle, 0.001),
        arc_center=CENTER,
        color=color,
        stroke_width=width,
    )


class LiveNumber(Text):
    """固定小数位的数字；值变化时原地重排，不跳位置。"""

    def __init__(self, value: float = 0.0, places: int = 2,
                 size: float = 40, color: str = INK):
        self.places = places
        self.size = size
        self._color = color
        self._value = value
        super().__init__(self._fmt(value), font=MATH_FONT,
                         font_size=size, color=color)

    def _fmt(self, value: float) -> str:
        return f"{value:.{self.places}f}"

    def set_value(self, value: float) -> None:
        self._value = value
        text = self._fmt(value)
        if text == self.text:
            return
        center = self.get_center()
        fresh = Text(text, font=MATH_FONT, font_size=self.size, color=self._color)
        fresh.move_to(center)
        self.become(fresh)


def readout(label: str, num: LiveNumber, suffix: str = "",
            size: float = 22, color: str = DIM) -> VGroup:
    parts = [cn(label, size, color), num]
    if suffix:
        parts.append(cn(suffix, size, color))
    return VGroup(*parts).arrange(RIGHT, buff=0.14)


# ---------------------------------------------------------------------------
# 场景
# ---------------------------------------------------------------------------
class RadianScene(Scene):
    """一个连续场景；圆固定，只有角度、弧长和公式在变。"""

    def construct(self) -> None:
        self.add(paper_dots())
        self.subtitle: Text | None = None
        self.theta = ValueTracker(0.0)

        if STAGE >= 1:
            self.phase_intro()
        if STAGE >= 2:
            self.phase_need()
        if STAGE >= 3:
            self.phase_formula()
        if STAGE >= 4:
            self.phase_choose()
        if STAGE >= 5:
            self.phase_ruler()
        if STAGE >= 6:
            self.phase_why()
        if STAGE >= 7:
            self.phase_close()

        stage_end = list(SEGMENTS.values())[min(STAGE, len(SEGMENTS)) - 1][1]
        self.hold_until(stage_end)
        print(f"[timeline] end at {self.renderer.time:.2f}s")

    # -------------------------------------------------------------- 时间控制
    def hold_until(self, target: float) -> None:
        now = self.renderer.time
        if target > now + 1e-3:
            self.wait(target - now)
        elif now > target + 0.05:
            print(f"[timing] overrun: {now:.2f}s > {target:.2f}s")

    def cue(self, key: str) -> None:
        at, text = CUES[key]
        self.hold_until(at)
        new = subtitle_text(text)
        if self.subtitle is not None:
            self.play(FadeOut(self.subtitle, run_time=0.15))
        self.play(FadeIn(new, shift=UP * 0.05), run_time=0.20)
        self.subtitle = new
        print(f"[cue] {key:10s} {self.renderer.time:6.2f}s")

    # ============================================================== 第一段
    def phase_intro(self) -> None:
        """一圈 = 360° 只是习惯；4、1 都一样能记录旋转。"""
        top = Arc(radius=RADIUS, start_angle=0, angle=PI,
                  arc_center=CENTER, color=INK, stroke_width=2.4)
        bot = Arc(radius=RADIUS, start_angle=PI, angle=PI,
                  arc_center=CENTER, color=INK, stroke_width=2.4)
        self.circle = VGroup(top, bot)
        self.top_arc, self.bot_arc = top, bot

        # 整圈不能用单条 2π 的 Arc：闭合处的贝塞尔控制点会错位，
        # 画出巨大的缺口弧。拆成四段四分之一圆弧，方向仍然连续。
        turn = VGroup(*[
            Arc(radius=RADIUS + 0.44,
                start_angle=-PI / 2 + k * PI / 2, angle=PI / 2,
                arc_center=CENTER, color=TEAL, stroke_width=2.2)
            for k in range(4)
        ])
        turn[-1].add_tip(tip_length=0.16)
        self.turn_arrow = turn

        num = VGroup(cn("360°", 58, INK), cn("一整圈", 21, DIM)
                     ).arrange(DOWN, buff=0.42).move_to(CENTER)

        self.cue("hook1")
        self.play(Create(turn), run_time=1.2)
        self.play(Create(top), Create(bot), run_time=0.9)
        self.play(FadeIn(num, scale=0.92), run_time=0.7)

        # 360 是谁定的？
        self.cue("hook2")
        box = SurroundingRectangle(num[0], color=ROSE, buff=0.18,
                                   stroke_width=3.0)
        q = cn("谁规定的？", 24, ROSE).move_to([0, 5.05, 0])
        self.play(Create(box), FadeIn(q, shift=DOWN * 0.08), run_time=0.7)
        self.play(num[0].animate.set_color(ROSE), run_time=0.35)
        self.hold_until(7.0)

        # 改成 4 份
        self.cue("four")
        four = VGroup(cn("4", 58, TEAL), cn("份", 21, DIM)
                      ).arrange(DOWN, buff=0.18).move_to(CENTER)
        ticks = VGroup(*[
            Line(point_at(a, RADIUS - 0.03), point_at(a, RADIUS + 0.30),
                 color=AXIS, stroke_width=2.0)
            for a in [0.0, PI / 2, PI, 3 * PI / 2]
        ])
        self.play(FadeOut(box), FadeOut(q), FadeOut(num),
                  FadeIn(four, scale=0.92), run_time=0.65)
        self.play(Create(ticks), run_time=0.7)
        self.hold_until(10.4)

        # 改成 1 份
        self.cue("one")
        one = VGroup(cn("1", 58, TEAL), cn("圈", 21, DIM)
                     ).arrange(DOWN, buff=0.18).move_to(CENTER)
        self.play(FadeOut(four), FadeIn(one, scale=0.92), run_time=0.55)
        self.play(FadeOut(ticks[1:]), run_time=0.55)
        self.hold_until(13.8)

        # 一圈记作 1，也能说清转了多少
        self.cue("record")
        self.theta.set_value(0.0)
        sector = always_redraw(lambda: Sector(
            radius=RADIUS, start_angle=0,
            angle=max(self.theta.get_value(), 0.001),
            arc_center=CENTER, fill_color=TEAL,
            fill_opacity=0.14, stroke_width=0,
        ))
        radius = always_redraw(lambda: Line(
            CENTER, point_at(self.theta.get_value()),
            color=TEAL, stroke_width=3.2,
        ))
        number = LiveNumber(0.0, 2, 40, TEAL)
        group = readout("转了", number, "圈", 22, DIM)
        group.move_to([0, -0.95, 0])
        number.add_updater(
            lambda mob: mob.set_value(self.theta.get_value() / TAU)
        )
        group.add_updater(
            lambda g: g.arrange(RIGHT, buff=0.14).move_to([0, -0.95, 0])
        )
        self.play(FadeOut(one), FadeOut(ticks), FadeOut(self.turn_arrow),
                  FadeIn(sector), FadeIn(radius), FadeIn(group),
                  run_time=0.6)
        self.play(self.theta.animate.set_value(0.40 * TAU),
                  run_time=1.8, rate_func=smooth)
        self.hold_until(17.4)

        # 留给下一段清理
        self.intro_leftovers = VGroup(sector, radius, group)

    # ============================================================== 第二段
    def phase_need(self) -> None:
        """新需求：量弧长。把圆周拉直，得到 C = 2πr 与 π = C/d。"""
        self.cue("need")
        self.play(FadeOut(self.intro_leftovers), run_time=0.5)

        theta_now = self.theta.get_value()
        highlight = arc_at(theta_now, ORANGE, 8.0)
        qmark = cn("？", 42, ORANGE).move_to(
            point_at(theta_now / 2, RADIUS + 0.62)
        )
        self.play(Create(highlight), run_time=0.8)
        self.play(FadeIn(qmark, scale=0.8), run_time=0.45)
        self.hold_until(21.6)

        # 圆周拉直：上下两个半圆各自变成一条直线
        self.cue("unroll")
        self.play(FadeOut(highlight), FadeOut(qmark),
                  FadeOut(self.turn_arrow), run_time=0.6)
        half_len = PI * RADIUS
        y_top, y_bot = 4.60, 5.60
        # 端点顺序要和圆弧一致：上半圆从右侧（0）走到左侧（π），
        # 下半圆从左（π）回到右（2π）。否则形变时会在空中打一个圈。
        line_top = Line([half_len / 2, y_top, 0], [-half_len / 2, y_top, 0],
                        color=INK, stroke_width=3.0)
        line_bot = Line([-half_len / 2, y_bot, 0], [half_len / 2, y_bot, 0],
                        color=INK, stroke_width=3.0)
        self.play(
            ReplacementTransform(self.top_arc, line_top),
            ReplacementTransform(self.bot_arc, line_bot),
            run_time=2.1,
        )
        lab_top = m(f"π{it('r')}", 28, ORANGE).next_to(line_top, RIGHT, buff=0.22)
        lab_bot = m(f"π{it('r')}", 28, ORANGE).next_to(line_bot, RIGHT, buff=0.22)
        note = cn("把圆周拉直", 22, DIM).move_to([0, 6.35, 0])
        self.play(FadeIn(lab_top), FadeIn(lab_bot), FadeIn(note), run_time=0.5)
        self.hold_until(26.4)

        # 整圈 = 2πr，并且 π 是比值
        self.cue("circum")
        c_eq = m(
            f'{span(it("C"), INK)} = 2π{span(it("r"), ORANGE)}',
            44,
        ).move_to([0, -1.35, 0])
        sum_eq = m(
            f'π{it("r")} + π{it("r")} = 2π{it("r")}',
            30, ORANGE,
        ).move_to([0, -2.15, 0])
        self.play(FadeIn(c_eq, shift=UP * 0.10), run_time=0.6)
        self.play(FadeIn(sum_eq), run_time=0.5)
        self.hold_until(30.4)

        self.cue("pi")
        pi_eq = m(
            f'{span("π", ROSE)} = {it("C")} / {it("d")}',
            40,
        ).move_to([0, -3.05, 0])
        d_eq = m(f'{it("d")} = 2{it("r")}', 28, DIM).move_to([0, -3.80, 0])
        pi_note = cn("π ≈ 3.14159… 是比值，不是角度", 22, ROSE).move_to(
            [0, -4.55, 0]
        )
        self.play(FadeIn(pi_eq, shift=UP * 0.08), run_time=0.65)
        self.play(FadeIn(d_eq), FadeIn(pi_note), run_time=0.65)
        self.hold_until(34.9)

        self.need_group = VGroup(
            line_top, line_bot, lab_top, lab_bot, note,
            c_eq, sum_eq, pi_eq, d_eq, pi_note,
        )

    # ============================================================== 第三段
    def phase_formula(self) -> None:
        """弧长 = 整圈周长 × 圈数；定义 N 与 θ，代出 s = (2π/N)·r·θ。"""
        self.cue("formula")

        # 两条直线折回圆周
        top = Arc(radius=RADIUS, start_angle=0, angle=PI,
                  arc_center=CENTER, color=INK, stroke_width=2.4)
        bot = Arc(radius=RADIUS, start_angle=PI, angle=PI,
                  arc_center=CENTER, color=INK, stroke_width=2.4)
        c_eq = self.need_group[5]
        # 两条直线和两个半圆共享端点，直接形变会让端点在空中交叉成
        # 一个“眼睛”。这里改用淡出/淡入，画面更干净。
        fade_out = VGroup(*self.need_group[:5], *self.need_group[6:])
        self.play(
            FadeOut(fade_out),
            FadeIn(VGroup(top, bot)),
            run_time=0.8,
        )
        self.top_arc, self.bot_arc = top, bot
        self.circle = VGroup(top, bot)
        c_eq.save_state()
        self.play(c_eq.animate.scale(0.78).move_to([0, -1.30, 0]), run_time=0.5)

        rel = cn("弧长 = 整圈周长 × 转过的圈数", 24, INK,
                 t2c={"弧长": ORANGE, "转过的圈数": TEAL})
        fit_width(rel, 7.2).move_to([0, -2.25, 0])
        self.play(FadeIn(rel, shift=UP * 0.08), run_time=0.6)

        # 中央角标记与动径
        self.theta.set_value(2.51)
        radius0 = DashedLine(CENTER, point_at(0.0), color=AXIS,
                             stroke_width=1.5, dash_length=0.10)
        radius_now = always_redraw(lambda: Line(
            CENTER, point_at(self.theta.get_value()),
            color=TEAL, stroke_width=3.0,
        ))
        angle_arc = always_redraw(lambda: arc_at(
            self.theta.get_value(), TEAL, 2.4, radius=0.82,
        ))
        theta_lab = m(f'{span(it("θ"), TEAL)}', 30).move_to(
            point_at(self.theta.get_value() / 2, 1.10)
        )
        theta_lab.add_updater(lambda mob: mob.move_to(
            point_at(self.theta.get_value() / 2, 1.10)
        ))
        self.play(FadeIn(radius0), FadeIn(radius_now),
                  FadeIn(angle_arc), FadeIn(theta_lab), run_time=0.6)
        self.hold_until(40.0)

        # 定义 N 与 θ
        self.cue("define")
        n_line = cn("N：一圈分成多少份", 24, INK, t2c={"N": ROSE})
        t_line = cn("θ：一共转过了多少份", 24, INK, t2c={"θ": TEAL})
        n_line.move_to([0, -3.20, 0])
        t_line.move_to([0, -3.85, 0])
        turns = cn("圈数 = θ / N", 27, INK, t2c={"θ": TEAL, "N": ROSE})
        turns.move_to([0, -4.55, 0])
        self.play(FadeIn(n_line, shift=UP * 0.06),
                  FadeIn(t_line, shift=UP * 0.06), run_time=0.65)
        self.play(FadeIn(turns), run_time=0.55)
        self.hold_until(44.6)

        # N = 4 的具体例子
        self.cue("example")
        ticks4 = VGroup(*[
            Line(point_at(a, RADIUS - 0.03), point_at(a, RADIUS + 0.30),
                 color=AXIS, stroke_width=2.0)
            for a in [0.0, PI / 2, PI, 3 * PI / 2]
        ])
        self.play(Create(ticks4), run_time=0.5)
        self.play(self.theta.animate.set_value(PI / 2),
                  run_time=1.2, rate_func=smooth)
        theta_one = m(f'{span(it("θ"), TEAL)} = 1', 30).move_to(
            point_at(PI / 4, RADIUS - 0.62)
        )
        quarter = cn("四分之一圈", 22, TEAL).move_to(
            point_at(PI / 4, RADIUS + 0.55)
        )
        ex = cn("N = 4 时，圈数 = θ / N = 1 / 4", 23, INK,
                t2c={"θ": TEAL, "N": ROSE})
        ex.move_to([0, -5.20, 0])
        # 动径上的 θ 与“θ = 1”在同一角度、只差 0.23 个半径，必须收掉一个，
        # 否则两个 θ 叠在一起，等号上会多出一道横线。
        self.play(FadeIn(theta_one), FadeIn(quarter), FadeOut(theta_lab),
                  run_time=0.55)
        self.play(FadeIn(ex), run_time=0.5)
        self.hold_until(49.6)

        # 代入：s = 2πr · θ/N
        self.cue("assemble")
        self.play(
            FadeOut(rel), FadeOut(n_line), FadeOut(t_line),
            FadeOut(turns), FadeOut(ex),
            FadeOut(theta_one), FadeOut(quarter), FadeOut(ticks4),
            run_time=0.6,
        )
        s_theta = m(
            f'{span(it("s"), ORANGE)} = 2π{span(it("r"), BLUE)} · '
            f'{span(it("θ"), TEAL)} / {span("N", ROSE)}',
            44,
        ).move_to([0, -3.30, 0])
        self.play(FadeIn(s_theta, shift=UP * 0.10), run_time=0.7)
        self.hold_until(53.9)

        # 整理出系数 2π/N
        self.cue("coef")
        prefix = m(f'{span(it("s"), ORANGE)} = ', 44)
        coef = m(f'({span("2π", ROSE)}/{span("N", ROSE)})', 44)
        suffix = m(
            f' · {span(it("r"), BLUE)} · {span(it("θ"), TEAL)}',
            44,
        )
        coef_formula = VGroup(prefix, coef, suffix).arrange(RIGHT, buff=0.05)
        coef_formula.move_to([0, -3.30, 0])
        coef_box = SurroundingRectangle(coef, color=ROSE, buff=0.10,
                                        stroke_width=2.4)
        coef_note = cn("转换系数", 20, ROSE).next_to(coef_box, DOWN, buff=0.18)
        self.play(ReplacementTransform(s_theta, coef_formula), run_time=0.7)
        self.play(Create(coef_box), FadeIn(coef_note), run_time=0.5)
        self.hold_until(57.6)

        self.formula_left = VGroup(c_eq, radius0, radius_now, angle_arc,
                                   theta_lab, coef_formula, coef_box,
                                   coef_note)

    # ============================================================== 第四段
    def phase_choose(self) -> None:
        """令 2π/N = 1，N = 2π，系数消失，s = rθ。"""
        self.cue("choose")
        eq1 = m(f'2π / N = 1', 30, ROSE).move_to([0, -5.00, 0])
        eq2 = m(f'N = 2π', 32, ROSE).move_to([0, -5.60, 0])
        self.play(FadeIn(eq1, shift=UP * 0.06), run_time=0.55)
        self.play(FadeIn(eq2, shift=UP * 0.06), run_time=0.55)
        self.hold_until(60.8)

        self.cue("rform")
        coef_formula = self.formula_left[5]
        coef_box = self.formula_left[6]
        coef_note = self.formula_left[7]
        step = m(
            f'{span(it("s"), ORANGE)} = 1 · {span(it("r"), BLUE)} · '
            f'{span(it("θ"), TEAL)}',
            44,
        ).move_to([0, -3.30, 0])
        self.play(FadeOut(coef_box), FadeOut(coef_note),
                  FadeOut(eq1), run_time=0.35)
        self.play(ReplacementTransform(coef_formula, step), run_time=0.6)
        final = m(
            f'{span(it("s"), ORANGE)} = {span(it("r"), BLUE)}'
            f'{span(it("θ"), TEAL)}',
            56,
        ).move_to([0, -3.30, 0])
        self.play(ReplacementTransform(step, final), run_time=0.6)
        one_turn = cn("一圈 = 2π 弧度", 26, ROSE).move_to(
            [0, -5.05, 0]
        )
        self.play(FadeOut(eq2), FadeIn(one_turn), run_time=0.45)
        self.hold_until(64.9)

        self.s_eq = final
        self.one_turn = one_turn

    # ============================================================== 第五段
    def phase_ruler(self) -> None:
        """半径当软尺：θ = 1 弧度 ⇔ 弧长 = r；连续变化；一石二鸟。"""
        self.cue("ruler")
        leftovers = self.formula_left[:5]
        self.play(
            FadeOut(leftovers),
            FadeOut(self.one_turn),
            self.s_eq.animate.scale(0.62).move_to([0, -1.25, 0]),
            run_time=0.6,
        )

        # 半径与“软尺”
        radius = Line(CENTER, point_at(0.0), color=BLUE, stroke_width=7)
        r_lab = m(f'{span(it("r"), BLUE)}', 34).move_to(
            point_at(0.0, RADIUS / 2) + UP * 0.30
        )
        self.play(Create(radius), run_time=0.6)
        self.play(FadeIn(r_lab), run_time=0.3)

        ruler = Line(CENTER, point_at(0.0), color=ORANGE, stroke_width=8)
        arc1 = arc_at(1.0, ORANGE, 8.0)
        self.play(FadeIn(ruler), run_time=0.25)
        self.play(ReplacementTransform(ruler, arc1), run_time=1.2)
        bend_note = cn("把 r 弯上去", 21, ORANGE).move_to([0, -2.05, 0])
        self.play(FadeIn(bend_note), run_time=0.3)
        self.hold_until(68.9)

        # 弧长 = r ⇒ 一弧度
        self.cue("onerad")
        arc_lab = cn("弧长 = r", 22, ORANGE).move_to([2.62, 2.55, 0])
        leader = Line(arc_lab.get_left(), point_at(0.5, RADIUS + 0.04),
                      color=ORANGE, stroke_width=1.2)
        rad_note = cn("θ = 1 弧度", 26, TEAL).move_to([0, -2.75, 0])
        self.play(FadeOut(bend_note), FadeIn(arc_lab), Create(leader),
                  FadeIn(rad_note), run_time=0.6)
        self.hold_until(73.1)

        # 2r、3r
        self.cue("twothree")
        arc3 = arc_at(3.0, ORANGE, 8.0)
        ticks = VGroup(*[
            Line(point_at(a, RADIUS - 0.10), point_at(a, RADIUS + 0.16),
                 color=INK, stroke_width=1.8)
            for a in [1.0, 2.0, 3.0]
        ])
        marks = VGroup(*[
            m(f'{"" if k == 1 else k}{it("r")}', 24, ORANGE).move_to(
                point_at(float(k), RADIUS + 0.46)
            )
            for k in [1, 2, 3]
        ])
        self.play(ReplacementTransform(arc1, arc3),
                  FadeOut(arc_lab), FadeOut(leader), FadeOut(rad_note),
                  run_time=1.4)
        self.play(Create(ticks), FadeIn(marks), run_time=0.6)
        self.hold_until(77.3)

        # 弧段不是弦
        self.cue("chord")
        chord = DashedLine(point_at(0.0), point_at(1.0), color=ROSE,
                           stroke_width=2.6, dash_length=0.12)
        chord_lab = cn("弦", 20, ROSE).move_to(
            point_at(0.5, RADIUS * 0.86) + LEFT * 0.10
        )
        chord_note = cn("量的是弧段，不是直弦", 22, ROSE).move_to(
            [0, -2.75, 0]
        )
        self.play(Create(chord), FadeIn(chord_lab), run_time=0.6)
        self.play(FadeIn(chord_note), run_time=0.35)
        self.hold_until(81.0)

        # 连续变化
        self.cue("live")
        self.play(FadeOut(chord), FadeOut(chord_lab), FadeOut(chord_note),
                  FadeOut(arc3), FadeOut(marks), FadeOut(ticks),
                  FadeOut(radius), FadeOut(r_lab), run_time=0.5)
        self.theta.set_value(0.0)
        live_arc = always_redraw(lambda: arc_at(
            self.theta.get_value(), ORANGE, 8.0,
        ))
        live_dot = always_redraw(lambda: Dot(
            point_at(self.theta.get_value()), radius=0.075, color=ORANGE,
        ))
        static_ticks = VGroup(*[
            Line(point_at(a, RADIUS - 0.10), point_at(a, RADIUS + 0.16),
                 color=AXIS, stroke_width=1.6)
            for a in [1.0, 2.0, 3.0]
        ])
        theta_num = LiveNumber(0.0, 2, 36, TEAL)
        s_num = LiveNumber(0.0, 2, 36, ORANGE)
        theta_ro = readout("θ =", theta_num, "", 22, TEAL)
        s_ro = readout("s =", s_num, "r", 22, ORANGE)
        theta_ro.move_to([0, -2.35, 0])
        s_ro.move_to([0, -3.05, 0])
        theta_num.add_updater(
            lambda mob: mob.set_value(self.theta.get_value())
        )
        s_num.add_updater(
            lambda mob: mob.set_value(self.theta.get_value())
        )
        theta_ro.add_updater(
            lambda g: g.arrange(RIGHT, buff=0.14).move_to([0, -2.35, 0])
        )
        s_ro.add_updater(
            lambda g: g.arrange(RIGHT, buff=0.14).move_to([0, -3.05, 0])
        )
        self.add(live_arc, live_dot, static_ticks, theta_ro, s_ro)
        self.play(FadeIn(static_ticks), FadeIn(theta_ro), FadeIn(s_ro),
                  run_time=0.5)
        self.play(self.theta.animate.set_value(3.0),
                  run_time=2.4, rate_func=linear)
        self.hold_until(85.3)

        # 分屏：记录旋转 vs 计算弧长
        self.cue("ratio")
        eq_ratio = VGroup(
            m(f'{span(it("θ"), TEAL)} = {span(it("s"), ORANGE)} / '
              f'{span(it("r"), BLUE)}', 40),
            cn("两个长度之比", 19, DIM),
        ).arrange(DOWN, buff=0.12).move_to([0, -1.50, 0])
        self.play(self.s_eq.animate.set_opacity(0.0),
                  FadeIn(eq_ratio, shift=UP * 0.05), run_time=0.5)
        self.hold_until(89.3)

        # 分屏：同一个 θ 的两份工作
        self.cue("split")
        self.play(FadeOut(eq_ratio), FadeOut(theta_ro), FadeOut(s_ro),
                  run_time=0.4)
        self.play(self.theta.animate.set_value(1.20), run_time=0.6)

        badge = VGroup(
            cn("θ", 40, TEAL),
        ).move_to(CENTER)
        badge_box = SurroundingRectangle(badge, color=TEAL, buff=0.16,
                                         stroke_width=2.2)
        badge_group = VGroup(badge, badge_box)
        self.play(FadeIn(badge_group, scale=0.9), run_time=0.35)

        panel_a = RoundedRectangle(width=3.35, height=2.0, corner_radius=0.16,
                                   color=TEAL, stroke_width=2.0,
                                   fill_color=TEAL, fill_opacity=0.05)
        panel_b = RoundedRectangle(width=3.35, height=2.0, corner_radius=0.16,
                                   color=ORANGE, stroke_width=2.0,
                                   fill_color=ORANGE, fill_opacity=0.05)
        panel_a.move_to([-1.78, -3.25, 0])
        panel_b.move_to([1.78, -3.25, 0])
        title_a = cn("记录旋转", 24, TEAL).next_to(panel_a.get_top(), DOWN, buff=0.20)
        title_b = cn("计算弧长", 24, ORANGE).next_to(panel_b.get_top(), DOWN, buff=0.20)
        val_a = m(f'{span(it("θ"), TEAL)} = 1.20', 30).move_to(
            panel_a.get_center() + DOWN * 0.10
        )
        val_b = VGroup(
            m(f'{span(it("s"), ORANGE)} = {it("r")}{it("θ")}', 30, ORANGE),
            m(f'= 1.20 {it("r")}', 26, ORANGE),
        ).arrange(DOWN, buff=0.12).move_to(panel_b.get_center() + DOWN * 0.10)
        note_a = cn("转了多少", 18, DIM).next_to(panel_a.get_bottom(), UP, buff=0.18)
        note_b = cn("弧有多长", 18, DIM).next_to(panel_b.get_bottom(), UP, buff=0.18)

        conn_a = DashedLine([0, 1.55, 0], [-1.78, -2.25, 0],
                            color=DIM, stroke_width=1.4, dash_length=0.10)
        conn_b = DashedLine([0, 1.55, 0], [1.78, -2.25, 0],
                            color=DIM, stroke_width=1.4, dash_length=0.10)
        self.play(FadeIn(panel_a), FadeIn(panel_b),
                  FadeIn(title_a), FadeIn(title_b), run_time=0.45)
        self.play(Create(conn_a), Create(conn_b), run_time=0.4)
        self.play(FadeIn(val_a), FadeIn(val_b),
                  FadeIn(note_a), FadeIn(note_b), run_time=0.45)
        self.hold_until(93.3)

        self.cue("birds")
        birds = cn("一石二鸟！", 38, ROSE, weight=BOLD).move_to([0, -5.05, 0])
        self.play(
            panel_a.animate.set_stroke(width=3.2, color=TEAL),
            panel_b.animate.set_stroke(width=3.2, color=ORANGE),
            run_time=0.4,
        )
        self.play(FadeIn(birds, scale=0.9), run_time=0.5)
        self.hold_until(97.1)

        self.split_left = VGroup(
            live_arc, live_dot, static_ticks, badge_group,
            panel_a, panel_b, title_a, title_b, val_a, val_b,
            note_a, note_b, conn_a, conn_b, birds,
        )

    # ============================================================== 第六段
    def phase_why(self) -> None:
        """整圈弧长 2πr，所以 θ = 2π；半圈 π，四分之一 π/2。"""
        self.cue("why")
        self.play(FadeOut(self.split_left), run_time=0.6)

        theta_eq = m(
            f'{span(it("θ"), TEAL)} = {span(it("s"), ORANGE)} / '
            f'{span(it("r"), BLUE)}', 42,
        ).move_to([0, -2.15, 0])
        s_num = LiveNumber(0.0, 2, 34, ORANGE)
        th_num = LiveNumber(0.0, 2, 34, TEAL)
        s_ro = readout("s =", s_num, "r", 22, ORANGE)
        th_ro = readout("θ =", th_num, "", 22, TEAL)
        s_ro.move_to([0, -3.05, 0])
        th_ro.move_to([0, -3.75, 0])
        s_num.add_updater(lambda mob: mob.set_value(self.theta.get_value()))
        th_num.add_updater(lambda mob: mob.set_value(self.theta.get_value()))
        s_ro.add_updater(
            lambda g: g.arrange(RIGHT, buff=0.14).move_to([0, -3.05, 0])
        )
        th_ro.add_updater(
            lambda g: g.arrange(RIGHT, buff=0.14).move_to([0, -3.75, 0])
        )
        sweep_arc = always_redraw(lambda: arc_at(
            self.theta.get_value(), ORANGE, 6.0,
        ))
        self.theta.set_value(0.0)
        self.add(sweep_arc)
        self.play(FadeIn(theta_eq), FadeIn(s_ro), FadeIn(th_ro), run_time=0.5)
        self.play(self.theta.animate.set_value(TAU), run_time=2.4,
                  rate_func=linear)

        exact_s = m(f'{span(it("s"), ORANGE)} = 2π{it("r")}', 32, ORANGE
                    ).move_to([0, -3.05, 0])
        exact_th = m(f'{span(it("θ"), TEAL)} = 2π', 32, TEAL
                     ).move_to([0, -3.75, 0])
        self.play(FadeOut(s_ro), FadeOut(th_ro), run_time=0.25)
        self.play(FadeIn(exact_s), FadeIn(exact_th), run_time=0.5)

        # 半圈与四分之一圈
        self.cue("half")
        half_arc = Arc(radius=RADIUS + 0.10, start_angle=0, angle=PI,
                       arc_center=CENTER, color=ORANGE, stroke_width=6.0)
        quarter_arc = Arc(radius=RADIUS + 0.20, start_angle=0, angle=PI / 2,
                          arc_center=CENTER, color=ROSE, stroke_width=6.0)
        pi_lab = m(f'{span("π", ROSE)}', 26).move_to(
            CENTER + LEFT * (RADIUS + 0.46)
        )
        half_lab = m(f'{span("π/2", ROSE)}', 24).move_to(
            CENTER + UP * (RADIUS + 0.46)
        )
        two_pi_lab = m(f'{span("2π", ROSE)}', 24).move_to(
            CENTER + RIGHT * (RADIUS + 0.48)
        )
        half_eq = cn("半圈：s = πr，θ = π", 26, ORANGE).move_to(
            [0, -2.70, 0]
        )
        quarter_eq = cn("四分之一圈：s = πr/2，θ = π/2", 26, ROSE).move_to(
            [0, -3.50, 0]
        )
        pi_note = cn("π 是两个长度之比，不是角度", 22, ROSE).move_to(
            [0, -4.30, 0]
        )
        self.play(FadeOut(exact_s), FadeOut(exact_th),
                  FadeOut(theta_eq), FadeOut(sweep_arc), run_time=0.4)
        self.play(Create(half_arc), run_time=0.6)
        self.play(Create(quarter_arc), run_time=0.5)
        self.play(FadeIn(pi_lab), FadeIn(half_lab), FadeIn(two_pi_lab),
                  run_time=0.4)
        self.play(FadeIn(half_eq), FadeIn(quarter_eq), run_time=0.5)
        self.play(FadeIn(pi_note), run_time=0.35)
        self.hold_until(107.3)

        self.why_left = VGroup(
            half_arc, quarter_arc, pi_lab, half_lab, two_pi_lab,
            half_eq, quarter_eq, pi_note,
        )

    # ============================================================== 第七段
    def phase_close(self) -> None:
        """360° = 2π 弧度；一个数字，两种用途。"""
        self.cue("close")
        self.play(FadeOut(self.why_left), run_time=0.6)

        deg_eq = cn("360° = 2π 弧度", 34, INK,
                    t2c={"2π": ROSE, "弧度": ROSE}).move_to([0, -1.95, 0])
        s_eq = m(
            f'{span(it("s"), ORANGE)} = {span(it("r"), BLUE)}'
            f'{span(it("θ"), TEAL)}', 54,
        ).move_to([0, -3.25, 0])
        one_two = cn("一个数字，两种用途。", 27, INK).move_to([0, -4.55, 0])
        name = cn("弧度制", 34, ROSE, weight=BOLD)
        name_box = SurroundingRectangle(name, color=ROSE, buff=0.24,
                                        stroke_width=2.2)
        name_badge = VGroup(name_box, name).move_to([0, -5.55, 0])
        self.play(FadeIn(deg_eq, shift=UP * 0.08), run_time=0.6)
        self.play(FadeIn(s_eq, scale=0.95), run_time=0.6)
        self.play(FadeIn(one_two), run_time=0.4)
        self.cue("name")
        self.play(FadeIn(name_badge, scale=0.92), run_time=0.45)
        self.hold_until(TOTAL)
