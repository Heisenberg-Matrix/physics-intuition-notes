"""高轨低速大周期，为什么根本不用背？——卫星圆轨道的一条推导链。

一条约 92 秒的竖屏短片。它不要求观众记住口诀，而是把口诀拆成
三个可以直接看见的物理事实：

1. 同一位置，引力加速度与卫星质量无关：a = GM/r²；
2. 轨道越高，r 越大，加速度越小；
3. 圆周运动还要求 a = v²/r。两个 a 是同一个东西，于是
   GM/r² = v²/r，解得 v = √(GM/r)。

最后让两颗卫星按真实的比例同时起跑：低轨跑完一圈时，高轨只走了
约 35%。高轨路程更长、速度更慢，周期自然更大。

所有速度、加速度、周期都在中心天体的惯性系里描述；轨道半径从
天体中心量起。若取 r₂ = 2r₁，则 v₂/v₁ = 1/√2，T₂/T₁ = 2√2，
画面中的角速度严格按这个比例设置。

声音说明
--------
``CUES`` 给出每句字幕与配音的起始时间，``NARRATION`` 保留完整解说词；
``narration.py`` 逐句合成语音，再按实测字幕时刻对齐。

渲染
----
    python -m manim -qh --disable_caching scene.py OrbitScene
    # 低清预览：PREVIEW=1 python -m manim -ql --disable_caching scene.py OrbitScene
    # 只渲染前 N 段：STAGE=3 python -m manim -ql ...（用于逐段检查版面）

本机没有 LaTeX 时，数学文字自动退回 Cambria Math 的 MarkupText。
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
STAGE = int(os.environ.get("STAGE", "8"))

config.frame_width = 9
config.frame_height = 16
config.pixel_width = 540 if PREVIEW else 1080
config.pixel_height = 960 if PREVIEW else 1920
config.frame_rate = 30
config.background_color = "#F5F0E6"

BG = "#F5F0E6"
INK = "#30343B"
INK_SOFT = "#6F7075"
LOW = "#5E8FC7"       # 低轨：柔和蓝
HIGH = "#D9924E"      # 高轨：暖橙
ACC = "#2F9E8F"       # 加速度：青绿
VEL = "#C2647F"       # 速度：玫红
ROSE = "#C67591"      # 关键结论
AXIS = "#A9A296"
DIM = "#8F8A80"
PAPER_DOT = "#D9D0BF"
EARTH_FILL = "#C7D0BE"
EARTH_LINE = "#8FA08C"

CN_FONT = "Microsoft YaHei"
MATH_FONT = "Cambria Math"


def pick_font(candidates: list[str], fallback: str) -> str:
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

# ---------------------------------------------------------------------------
# 版面常量
# ---------------------------------------------------------------------------
CENTER = np.array([0.0, 1.85, 0.0])
R_EARTH = 0.55
R1 = 1.55
R2 = 2.0 * R1
SUB_Y = -6.55
TAU = 2 * np.pi

# 每段的目标起止时间（秒）；各段终点就是下一段第一句字幕的名义时刻。
SEGMENTS = {
    "intro": (0.0, 9.5),
    "promise": (9.5, 15.0),
    "mass": (15.0, 27.5),
    "accel": (27.5, 41.0),
    "velocity": (41.0, 51.5),
    "derive": (51.5, 66.5),
    "period": (66.5, 81.5),
    "close": (81.5, 92.0),
}
TOTAL = SEGMENTS["close"][1]

# 完整解说词：配音实际念的口语版本，narration.py 直接读它。
# 字幕里保留公式与符号，口播里换成“二派 r”“根号”等自然读法。
NARRATION = {
    "q1": "高考物理有句口诀：高轨低速大周期……还是高轨高速小周期？",
    "q2": "你还记得，哪个才是对的吗？",
    "promise": "其实，这个口诀根本不用背。搞懂加速度就够了。",
    "mass1": "卫星可以很轻，也可以很重。",
    "mass2": "但在同一位置，引力加速度一样，跟质量无关。",
    "mass3": "公式里，根本没有卫星的质量。",
    "far": "那离地球更远呢？看，加速度跟距离的平方成反比。",
    "ratio": "轨道半径翻倍，加速度就只剩四分之一。",
    "q3": "但加速度小，速度就一定小吗？",
    "not": "当然不能这么说！因为做圆周运动，半径也很重要。",
    "merge": "卫星做匀速圆周运动，这两个加速度就是同一个东西。",
    "solve": "把它们放在一起，速度就出来了！",
    "lower": "轨道越高，速度越低。原来是这么来的！",
    "period": "那周期呢？你看，高轨道一圈的路更长，卫星跑得还更慢，转一圈的时间当然更长！",
    "tform": "一圈的周长，除以速度，就是周期。",
    "recap": "高轨低速大周期。你看，两个加速度关系，整个口诀就自己推出来了。",
}

# 字幕与名义起始时间；字幕统一缩到安全宽度 7.2。
CUES: dict[str, tuple[float, str]] = {
    "q1": (0.60, "高轨低速大周期？还是高轨高速小周期？"),
    "q2": (6.60, "你还记得哪个是对的吗？"),
    "promise": (9.50, "其实，只要理解加速度。"),
    "mass1": (15.00, "卫星可以很轻，也可以很重。"),
    "mass2": (18.10, "同一位置，引力加速度一样。"),
    "mass3": (22.60, "公式里，根本没有卫星的质量。"),
    "far": (27.50, "轨道越高，引力加速度越小。"),
    "ratio": (33.10, "半径翻倍，加速度只剩四分之一。"),
    "q3": (41.00, "加速度小，速度就一定小吗？"),
    "not": (45.20, "圆周运动里，半径也很重要。"),
    "merge": (51.50, "两个加速度，其实是同一个东西。"),
    "solve": (56.80, "合在一起，速度就出来了。"),
    "lower": (59.90, "轨道越高，速度越低。"),
    "period": (66.50, "路程更长、速度更慢，周期更大。"),
    "tform": (75.60, "周期 = 一圈的周长 ÷ 速度。"),
    "recap": (81.50, "高轨低速大周期，自己就推出来了。"),
}


# ---------------------------------------------------------------------------
# 小工具：字体、排版、安全宽度
# ---------------------------------------------------------------------------
def cn(text: str, size: float = 26, color: str = INK, weight: str = NORMAL,
       t2c: dict[str, str] | None = None) -> Text:
    return Text(text, font=CN_FONT, font_size=size, color=color,
                weight=weight, t2c=t2c)


def m(body: str, size: float = 38, color: str = INK) -> MarkupText:
    """Cambria Math 的数学排字；变量用斜体。"""
    return MarkupText(body, font=MATH_FONT, font_size=size, color=color)


def it(name: str) -> str:
    return f"<i>{name}</i>"


def span(body: str, color: str) -> str:
    return f'<span foreground="{color}">{body}</span>'


def fit_width(mob, max_width: float = 7.2):
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


def tangent(angle: float) -> np.ndarray:
    """逆时针运动在角度 angle 处的单位切向。"""
    return np.array([-np.sin(angle), np.cos(angle), 0.0])


def point_on(radius: float, angle: float) -> np.ndarray:
    return CENTER + radius * dirv(angle)


def orbit_circle(radius: float, color: str, width: float = 2.0,
                 opacity: float = 0.75) -> Circle:
    return Circle(radius=radius, color=color, stroke_width=width,
                  stroke_opacity=opacity).move_to(CENTER)


def satellite(color: str, radius: float = 0.10) -> VGroup:
    """一个简单圆形天体：实心点 + 细环，不用写实贴图。"""
    return VGroup(
        Dot(radius=radius, color=color, fill_opacity=0.95, stroke_width=0),
        Circle(radius=radius + 0.055, color=color, stroke_width=1.1,
               stroke_opacity=0.55),
    )


def earth() -> VGroup:
    body = Circle(radius=R_EARTH, color=EARTH_LINE, stroke_width=2.0).move_to(CENTER)
    body.set_fill(EARTH_FILL, opacity=0.95)
    # 一条很淡的高光弧，让圆球有体积感，但不做写实大陆。
    shine = Arc(
        radius=R_EARTH * 0.82,
        start_angle=PI * 0.62,
        angle=PI * 0.72,
        arc_center=CENTER,
        color="#E4E9DB",
        stroke_width=3.0,
        stroke_opacity=0.75,
    )
    return VGroup(body, shine)


def arrow_between(start: np.ndarray, end: np.ndarray, color: str,
                  width: float = 4.0, opacity: float = 1.0) -> Arrow:
    return Arrow(
        start, end, buff=0, color=color, stroke_width=width,
        stroke_opacity=opacity, max_tip_length_to_length_ratio=0.16,
        max_stroke_width_to_length_ratio=6,
    )


class OrbitScene(Scene):
    """一个连续场景；中心天体与两条轨道固定，卫星和公式在变。"""

    def construct(self) -> None:
        self.add(paper_dots())
        self.subtitle: Text | None = None
        self.ang_low = ValueTracker(0.0)
        self.ang_high = ValueTracker(0.0)

        if STAGE >= 1:
            self.phase_intro()
        if STAGE >= 2:
            self.phase_promise()
        if STAGE >= 3:
            self.phase_mass()
        if STAGE >= 4:
            self.phase_accel()
        if STAGE >= 5:
            self.phase_velocity()
        if STAGE >= 6:
            self.phase_derive()
        if STAGE >= 7:
            self.phase_period()
        if STAGE >= 8:
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

    # ============================================================== 镜头 01
    def phase_intro(self) -> None:
        """开场只抛选择题，不提前公布答案。"""
        self.cue("q1")
        a_badge = cn("A", 30, DIM)
        b_badge = cn("B", 30, DIM)
        opt_a = cn("高轨低速大周期？", 40, INK)
        opt_b = cn("高轨高速小周期？", 40, INK)
        group_a = VGroup(a_badge, opt_a).arrange(RIGHT, buff=0.35)
        group_b = VGroup(b_badge, opt_b).arrange(RIGHT, buff=0.35)
        group_a.move_to([0, 2.15, 0])
        group_b.move_to([0, 0.95, 0])
        ask = cn("你还记得，哪个是对的吗？", 24, DIM).move_to([0, -0.85, 0])

        self.play(FadeIn(group_a, shift=UP * 0.10), run_time=0.55)
        self.hold_until(4.25)
        self.play(FadeIn(group_b, shift=UP * 0.10), run_time=0.55)
        # 第二个选项出现后刻意停一拍，让观众先猜。
        self.hold_until(6.35)
        self.cue("q2")
        self.play(FadeIn(ask, shift=UP * 0.08), run_time=0.45)
        self.hold_until(9.5)

        self.options = VGroup(group_a, group_b, ask)

    # ============================================================== 镜头 02
    def phase_promise(self) -> None:
        """口诀先放下，只承诺一件事：搞懂加速度。"""
        self.cue("promise")
        self.play(
            self.options.animate.scale(0.82).set_opacity(0.0),
            run_time=0.75,
        )
        self.remove(self.options)

        body = earth()
        orbit_low = orbit_circle(R1, LOW)
        orbit_high = orbit_circle(R2, HIGH)
        self.earth = body
        self.orbit_low = orbit_low
        self.orbit_high = orbit_high
        self.play(
            FadeIn(body),
            Create(orbit_low),
            Create(orbit_high),
            run_time=1.0,
        )

        low = satellite(LOW).move_to(point_on(R1, 0.55))
        high = satellite(HIGH).move_to(point_on(R2, 2.35))
        self.static_low = low
        self.static_high = high
        self.play(FadeIn(low), FadeIn(high), run_time=0.5)

        text = cn("其实，只要理解加速度。", 28, INK,
                  t2c={"加速度": ACC}).move_to([0, -2.55, 0])
        self.promise_text = text
        self.play(FadeIn(text, shift=UP * 0.08), run_time=0.55)
        self.hold_until(14.55)
        self.play(FadeOut(text), run_time=0.45)

    # ============================================================== 镜头 03
    def phase_mass(self) -> None:
        """同一半径，两颗不同质量的卫星，加速度箭头一样长。"""
        self.cue("mass1")
        angle = 0.52
        s1 = satellite(LOW).move_to(point_on(R1, angle - 0.055))
        s2 = satellite(LOW).move_to(point_on(R1, angle + 0.055))
        m1 = cn("m", 28, INK).next_to(s1, UR, buff=0.10)
        m2 = cn("2m", 28, INK).next_to(s2, UL, buff=0.10)
        self.play(
            FadeOut(self.static_high),
            FadeOut(self.static_low),
            FadeIn(s1), FadeIn(s2),
            FadeIn(m1), FadeIn(m2),
            run_time=0.55,
        )

        # 两条等长的加速度箭头，方向都指向地心。
        def acc_arrow(sat, color=ACC, length=0.95):
            p = sat.get_center()
            u = (CENTER - p) / np.linalg.norm(CENTER - p)
            return arrow_between(p, p + length * u, color, width=3.6)

        arr1 = acc_arrow(s1)
        arr2 = acc_arrow(s2)
        self.play(GrowArrow(arr1), GrowArrow(arr2), run_time=0.65)
        self.hold_until(18.1)

        self.cue("mass2")
        formula = m(
            f'{it("a")} = {span(it("GM"), ACC)}/{span(it("r") + "²", LOW)}',
            42,
        ).move_to([0, -3.05, 0])
        self.play(FadeIn(formula, shift=UP * 0.08), run_time=0.55)
        self.hold_until(22.6)

        self.cue("mass3")
        # 质量标签先消失，两条箭头合并成一条，把注意力交给 r。
        self.play(FadeOut(m1), FadeOut(m2), run_time=0.35)
        mid = (s1.get_center() + s2.get_center()) / 2
        u = (CENTER - mid) / np.linalg.norm(CENTER - mid)
        arr = arrow_between(mid, mid + 0.95 * u, ACC, width=4.0)
        a_lab = m(it("a"), 30, ACC).next_to(arr.get_center(), LEFT, buff=0.12)
        self.play(
            FadeOut(arr1), FadeOut(arr2),
            GrowArrow(arr), FadeIn(a_lab),
            run_time=0.55,
        )
        no_m = cn("公式里没有 m", 22, ROSE).move_to([0, -4.05, 0])
        self.play(FadeIn(no_m, shift=UP * 0.06), run_time=0.45)
        self.mass_group = VGroup(s1, s2, arr, a_lab, formula, no_m)
        self.hold_until(26.95)
        self.play(FadeOut(self.mass_group), run_time=0.55)

    # ============================================================== 镜头 04
    def phase_accel(self) -> None:
        """半径从 r 拉到 2r，箭头按平方关系缩到四分之一。

        高轨卫星先从低轨半径处沿同一条径向线外移；这是“只改变半径”的
        对照，不是变轨过程：画面用虚线半径和连续缩短的箭头表示 r 变大，
        不画推进、弧线转移或速度方向。
        """
        self.cue("far")
        angle_low = 0.43
        angle_high = 0.82
        low = satellite(LOW).move_to(point_on(R1, angle_low))
        high = satellite(HIGH).move_to(point_on(R1, angle_high))
        self.play(FadeIn(low), FadeIn(high), run_time=0.45)

        # 高轨卫星的半径由 tracker 驱动；位置、虚线半径和加速度箭头
        # 都从同一个半径读数来，保证 r 翻倍时箭头严格缩到 1/4。
        self.high_radius = ValueTracker(R1)
        high.add_updater(lambda mob: mob.move_to(
            point_on(self.high_radius.get_value(), angle_high)
        ))

        r_low = DashedLine(CENTER, point_on(R1, angle_low), color=LOW,
                           stroke_width=1.3, dash_length=0.08,
                           stroke_opacity=0.55)
        r_high = DashedLine(CENTER, point_on(R1, angle_high), color=HIGH,
                            stroke_width=1.3, dash_length=0.08,
                            stroke_opacity=0.55)
        r_high.add_updater(lambda mob: mob.put_start_and_end_on(
            CENTER, point_on(self.high_radius.get_value(), angle_high)
        ))
        t_low = tangent(angle_low)
        t_high = tangent(angle_high)
        r1_lab = m(it("r"), 26, LOW).move_to(
            point_on(1.28, angle_low) - 0.34 * t_low
        )
        r2_lab_start = m(it("r"), 26, HIGH).move_to(
            point_on(1.28, angle_high) + 0.34 * t_high
        )
        self.play(Create(r_low), Create(r_high), FadeIn(r1_lab),
                  FadeIn(r2_lab_start), run_time=0.45)

        def acc_arrow_from(p, length):
            u = (CENTER - p) / np.linalg.norm(CENTER - p)
            return arrow_between(p, p + length * u, ACC, width=3.6)

        def high_accel_length() -> float:
            return (R1 / self.high_radius.get_value()) ** 2

        arr_low = acc_arrow_from(low.get_center(), 1.0)
        arr_high = always_redraw(lambda: acc_arrow_from(
            high.get_center(), high_accel_length()
        ))
        self.play(GrowArrow(arr_low), FadeIn(arr_high), run_time=0.55)
        a_lab = m(it("a"), 28, ACC).move_to(
            point_on(0.84, angle_low) + 0.30 * t_low
        )
        self.play(FadeIn(a_lab), run_time=0.25)

        # 只把半径从 r 拉到 2r：虚线跟着伸长，箭头同步缩短。
        radius_note = cn("只变半径（示意）", 20, INK_SOFT).move_to([0, -2.2, 0])
        self.play(
            FadeOut(r2_lab_start),
            FadeIn(radius_note),
            self.high_radius.animate.set_value(R2),
            run_time=1.55,
            rate_func=smooth,
        )
        r2_lab = m("2" + it("r"), 26, HIGH).move_to(
            point_on(2.32, angle_high) + 0.40 * t_high
        )
        self.play(FadeOut(radius_note), FadeIn(r2_lab), run_time=0.30)

        formula = m(
            f'{it("a")} = {span(it("GM"), ACC)}/{span(it("r") + "²", HIGH)}',
            42,
        ).move_to([0, -3.05, 0])
        self.play(FadeIn(formula, shift=UP * 0.08), run_time=0.50)
        self.hold_until(33.1)

        self.cue("ratio")
        note = cn("r 翻倍 → a 变 1/4", 22, HIGH).move_to([0, -4.05, 0])
        a4_lab = m(it("a") + "/4", 26, ACC).move_to(
            point_on(3.0, angle_high) + 0.32 * t_high
        )
        self.play(
            FadeIn(note, shift=UP * 0.06),
            Indicate(formula, color=ROSE, scale_factor=1.02),
            run_time=0.75,
        )
        self.play(FadeIn(a4_lab), run_time=0.30)
        self.accel_group = VGroup(
            low, high, r_low, r_high, r1_lab, r2_lab,
            arr_low, arr_high, a_lab, a4_lab, formula, note,
        )
        self.hold_until(41.0)

    # ============================================================== 镜头 05
    def phase_velocity(self) -> None:
        """加速度小不等于速度小；圆周运动还有 a = v²/r。"""
        self.cue("q3")
        # 公式让位给问句，但两颗卫星和箭头先留着。
        self.play(FadeOut(self.accel_group[10]), FadeOut(self.accel_group[11]),
                  run_time=0.35)
        question = cn("加速度小，速度就一定小吗？", 28, INK,
                      t2c={"速度": VEL}).move_to([0, -2.55, 0])
        big_q = m("?", 90, ROSE).move_to([0, -4.05, 0])
        self.play(FadeIn(question, shift=UP * 0.06), FadeIn(big_q), run_time=0.5)
        self.play(Indicate(big_q, scale_factor=1.12, color=ROSE), run_time=0.8)
        self.hold_until(45.2)

        self.cue("not")
        self.play(FadeOut(question), FadeOut(big_q), run_time=0.4)
        # 只保留低轨，把镜头交给一颗卫星。
        keep = VGroup(
            self.accel_group[0], self.accel_group[2],
        )
        drop = VGroup(
            self.accel_group[1], self.accel_group[3], self.accel_group[4],
            self.accel_group[5], self.accel_group[6], self.accel_group[7],
            self.accel_group[8], self.accel_group[9], self.accel_group[10],
        )
        self.play(FadeOut(drop), run_time=0.55)

        self.low_now = self.accel_group[0]
        self.low_angle = 0.43
        p = point_on(R1, self.low_angle)
        u = (CENTER - p) / np.linalg.norm(CENTER - p)
        t = tangent(self.low_angle)
        v_arrow = arrow_between(p, p + 0.95 * t, VEL, width=3.6)
        a_arrow = arrow_between(p, p + 0.72 * u, ACC, width=3.6)
        v_lab = m(it("v"), 28, VEL).next_to(v_arrow.get_end(), UP, buff=0.08)
        a_lab = m(it("a"), 28, ACC).move_to(
            point_on(1.05, self.low_angle) + 0.32 * tangent(self.low_angle)
        )
        self.play(GrowArrow(v_arrow), GrowArrow(a_arrow),
                  FadeIn(v_lab), FadeIn(a_lab), run_time=0.65)

        formula = m(
            f'{it("a")} = {span(it("v") + "²", VEL)}/{span(it("r"), LOW)}',
            42,
        ).move_to([0, -3.0, 0])
        note = cn("同一个 a，半径越大，速度反而越小", 21, DIM).move_to(
            [0, -4.05, 0]
        )
        self.play(FadeIn(formula, shift=UP * 0.08), run_time=0.55)
        self.play(FadeIn(note), run_time=0.4)
        self.velocity_group = VGroup(
            keep, v_arrow, a_arrow, v_lab, a_lab, formula, note,
        )
        self.hold_until(50.95)
        self.play(FadeOut(self.velocity_group), run_time=0.55)

    # ============================================================== 镜头 06
    def phase_derive(self) -> None:
        """两个加速度合成一个等式，解出 v = √(GM/r)。"""
        self.cue("merge")
        left_head = cn("引力加速度", 21, DIM)
        right_head = cn("圆周运动加速度", 21, DIM)
        left_eq = m(
            f'{span(it("GM"), ACC)}/{span(it("r") + "²", LOW)}', 40
        )
        right_eq = m(
            f'{span(it("v") + "²", VEL)}/{span(it("r"), LOW)}', 40
        )
        left = VGroup(left_head, left_eq).arrange(DOWN, buff=0.22)
        right = VGroup(right_head, right_eq).arrange(DOWN, buff=0.22)
        left.move_to([-2.1, -2.45, 0])
        right.move_to([2.1, -2.45, 0])
        self.play(FadeIn(left, shift=UP * 0.08), FadeIn(right, shift=UP * 0.08),
                  run_time=0.7)
        self.hold_until(54.6)

        # 两张卡片向中间靠拢；标题退场，只留下两条加速度。
        self.play(FadeOut(left_head), FadeOut(right_head), run_time=0.35)
        self.play(
            left_eq.animate.move_to([-0.85, -2.95, 0]),
            right_eq.animate.move_to([0.85, -2.95, 0]),
            run_time=0.65,
        )
        eq_sign = m("=", 42, INK).move_to([0, -2.95, 0])
        self.play(FadeIn(eq_sign), run_time=0.3)
        self.hold_until(56.8)

        self.cue("solve")
        eq1 = VGroup(left_eq, eq_sign, right_eq)
        mult = cn("两边乘 r", 20, DIM).move_to([0, -3.95, 0])
        self.play(
            Indicate(eq1, color=ROSE, scale_factor=1.02),
            FadeIn(mult),
            run_time=0.55,
        )
        self.wait(0.15)
        eq2 = m(
            f'{span(it("GM"), ACC)}/{span(it("r"), LOW)} = '
            f'{span(it("v") + "²", VEL)}', 42
        ).move_to([0, -2.95, 0])
        # 不用形状匹配去硬变形：Cambria Math 的上下标会被拆成碎片。
        # 先给出“两边乘 r”的中间式，再干净地换成开方结果。
        self.play(FadeOut(eq1, shift=UP * 0.08), run_time=0.2)
        self.play(FadeIn(eq2, shift=UP * 0.08), run_time=0.2)
        self.play(FadeOut(mult), run_time=0.15)
        eq3 = m(
            f'{it("v")} = √({span(it("GM"), ACC)}/{span(it("r"), LOW)})',
            44,
        ).move_to([0, -2.95, 0])
        self.play(FadeOut(eq2, shift=UP * 0.08), run_time=0.2)
        self.play(FadeIn(eq3, shift=UP * 0.08), run_time=0.2)
        box = SurroundingRectangle(eq3, color=ROSE, buff=0.18, stroke_width=2.4)
        self.play(Create(box), run_time=0.4)
        self.hold_until(59.9)

        self.cue("lower")
        # 公式缩到左上角；两颗卫星开始按真实速度比例运行。
        self.play(
            FadeOut(box),
            eq3.animate.scale(0.62).move_to([-2.55, 5.55, 0]),
            run_time=0.7,
        )
        self.corner_formula = eq3

        self.start_running(66.3)
        self.hold_until(66.5)

    def start_running(self, end: float) -> None:
        """让两颗卫星按 v ∝ 1/√r 的角速度运行；不为了画面随意改比例。"""
        # 圆轨道：ω = √(GM/r³)。取 ω₁ 对应 4 秒一圈，
        # 则 ω₂/ω₁ = 1/(2√2)，与 v₂/v₁ = 1/√2 一致。
        omega1 = TAU / 4.0
        omega2 = omega1 / (2 * np.sqrt(2))
        a0 = self.ang_low.get_value()
        b0 = self.ang_high.get_value()
        run_time = max(0.2, end - self.renderer.time)
        low = always_redraw(lambda: satellite(LOW).move_to(
            point_on(R1, self.ang_low.get_value())
        ))
        high = always_redraw(lambda: satellite(HIGH).move_to(
            point_on(R2, self.ang_high.get_value())
        ))
        self.running_low = low
        self.running_high = high
        self.add(low, high)
        self.play(
            self.ang_low.animate.set_value(a0 + omega1 * run_time),
            self.ang_high.animate.set_value(b0 + omega2 * run_time),
            run_time=run_time,
            rate_func=linear,
        )

    # ============================================================== 镜头 07
    def phase_period(self) -> None:
        """同一径向起点、同时起跑；低轨一圈，高轨只走了约 35%。"""
        self.cue("period")
        # 清掉上一段的轨迹和卫星，回到同一起点。
        self.play(
            FadeOut(self.corner_formula),
            FadeOut(self.running_low),
            FadeOut(self.running_high),
            run_time=0.45,
        )
        self.ang_low.set_value(0.0)
        self.ang_high.set_value(0.0)

        start_line = DashedLine(CENTER, point_on(R2, 0.0), color=AXIS,
                                stroke_width=1.2, dash_length=0.10,
                                stroke_opacity=0.55)
        start_dot = Dot(point_on(R1, 0.0), radius=0.06, color=AXIS)
        start_lab = cn("同一起点", 18, DIM).move_to(
            [2.2, CENTER[1] + 0.72, 0]
        )
        self.play(Create(start_line), FadeIn(start_dot), FadeIn(start_lab),
                  run_time=0.55)

        low = always_redraw(lambda: satellite(LOW).move_to(
            point_on(R1, self.ang_low.get_value())
        ))
        high = always_redraw(lambda: satellite(HIGH).move_to(
            point_on(R2, self.ang_high.get_value())
        ))
        trail_low = TracedPath(
            lambda: point_on(R1, self.ang_low.get_value()),
            stroke_color=LOW, stroke_width=3.5, stroke_opacity=0.75,
        )
        trail_high = TracedPath(
            lambda: point_on(R2, self.ang_high.get_value()),
            stroke_color=HIGH, stroke_width=3.5, stroke_opacity=0.75,
        )
        self.add(trail_low, trail_high, low, high)
        self.low_run = low
        self.high_run = high
        self.trail_low = trail_low
        self.trail_high = trail_high

        # 低轨 4.0 秒一圈；高轨的角速度严格是 1/(2√2)。
        self.play(
            self.ang_low.animate.set_value(TAU),
            self.ang_high.animate.set_value(TAU / (2 * np.sqrt(2))),
            run_time=4.0,
            rate_func=linear,
        )
        lap_note = cn("低轨：跑完一圈", 21, LOW).move_to([-2.35, -0.55, 0])
        part_note = cn("高轨：还没跑完", 21, HIGH).move_to([2.25, 4.75, 0])
        self.play(FadeIn(lap_note), FadeIn(part_note), run_time=0.45)
        self.hold_until(75.6)

        self.cue("tform")
        t_eq = m(
            f'{it("T")} = 2π{span(it("r"), LOW)}/{span(it("v"), VEL)}',
            42,
        ).move_to([0, -2.45, 0])
        ratio_note = m(
            f'{it("T")}₂/{it("T")}₁ = 2√2', 24, HIGH
        ).move_to([0, -3.35, 0])
        ratio_v = m(
            f'{it("v")}₂/{it("v")}₁ = 1/√2', 22, DIM
        ).move_to([0, -4.1, 0])
        self.play(FadeIn(t_eq, shift=UP * 0.08), run_time=0.55)
        self.play(FadeIn(ratio_note), FadeIn(ratio_v), run_time=0.45)

        # 高轨的路更长：把整条高轨轻轻描亮。
        self.play(self.orbit_high.animate.set_stroke(width=4.5), run_time=0.4)
        self.play(self.orbit_high.animate.set_stroke(width=2.0), run_time=0.4)
        self.period_group = VGroup(
            start_line, start_dot, start_lab, lap_note, part_note,
            t_eq, ratio_note, ratio_v, trail_low, trail_high,
            self.low_run, self.high_run,
        )
        self.hold_until(81.5)

    # ============================================================== 镜头 08
    def phase_close(self) -> None:
        """回到开场选择题，再把三条理解关系收回口诀。"""
        self.cue("recap")
        self.play(
            FadeOut(self.period_group),
            FadeOut(self.orbit_low),
            FadeOut(self.orbit_high),
            FadeOut(self.earth),
            run_time=0.65,
        )

        # 重新摆出开场的选择题。
        a_badge = cn("A", 28, DIM)
        b_badge = cn("B", 28, DIM)
        opt_a_text = cn("高轨低速大周期", 37, INK)
        opt_b_text = cn("高轨高速小周期", 37, DIM)
        group_a = VGroup(a_badge, opt_a_text).arrange(RIGHT, buff=0.32)
        group_b = VGroup(b_badge, opt_b_text).arrange(RIGHT, buff=0.32)
        group_a.move_to([0, 3.35, 0])
        group_b.move_to([0, 2.05, 0])
        self.play(FadeIn(group_a, shift=UP * 0.08), FadeIn(group_b),
                  run_time=0.55)

        correct_box = SurroundingRectangle(opt_a_text, color=ACC, buff=0.16,
                                           stroke_width=2.4)
        self.play(Create(correct_box), run_time=0.5)
        self.play(Indicate(group_a, color=ACC, scale_factor=1.03), run_time=0.7)
        self.play(opt_b_text.animate.set_opacity(0.25),
                  b_badge.animate.set_opacity(0.25), run_time=0.5)

        rel1 = fit_width(cn(
            "轨道越高 → 加速度越小", 26, INK, t2c={"加速度越小": ACC}
        ), 7.0).move_to([0, 0.35, 0])
        rel2 = fit_width(cn(
            "结合圆周运动 → 速度越小", 26, INK, t2c={"速度越小": VEL}
        ), 7.0).move_to([0, -1.05, 0])
        rel3 = fit_width(cn(
            "路程更长、速度更慢 → 周期越大", 26, INK, t2c={"周期越大": HIGH}
        ), 7.0).move_to([0, -2.45, 0])
        self.play(FadeIn(rel1, shift=UP * 0.08), run_time=0.45)
        self.hold_until(85.9)
        self.play(FadeIn(rel2, shift=UP * 0.08), run_time=0.45)
        self.hold_until(87.4)
        self.play(FadeIn(rel3, shift=UP * 0.08), run_time=0.45)
        self.hold_until(89.2)

        # 片尾清空，只留一句。
        self.play(
            FadeOut(group_a), FadeOut(group_b), FadeOut(correct_box),
            FadeOut(rel1), FadeOut(rel2), FadeOut(rel3),
            run_time=0.6,
        )
        if self.subtitle is not None:
            self.play(FadeOut(self.subtitle), run_time=0.25)
            self.subtitle = None
        final = cn("理解了，就不用背了。", 42, INK,
                   t2c={"不用背": ROSE}).move_to([0, 0.4, 0])
        underline = Line(final.get_left() + DOWN * 0.32,
                         final.get_right() + DOWN * 0.32,
                         color=ROSE, stroke_width=2.2, stroke_opacity=0.7)
        self.play(FadeIn(final, shift=UP * 0.10), Create(underline),
                  run_time=0.7)
        self.hold_until(TOTAL)
