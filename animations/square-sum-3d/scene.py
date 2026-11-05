"""平方和公式的三维刚体拼装动画。

画面：Manim ThreeDScene；声音：manim-voiceover + edge-tts；
字幕：画面内固定文字（ThreeDScene.add_fixed_in_frame_mobjects）。
几何拼装与滑入路径全部来自 assembly.py 的离散校验结果。
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import numpy as np
from manim import *

from manim_voiceover import VoiceoverScene

from assembly import (
    Placement,
    apply_matrix,
    generate_staircase,
    rotation_axis_angle,
    solve_assembly,
    solve_insertion_paths,
    top_region,
)
from narration import (
    LINES,
    PAUSE,
    SUBTITLES,
    EdgeTTSService,
    export_srt,
    synchronize_subtitles,
)

# ---------------------------------------------------------------- 画面规格
PREVIEW = os.environ.get("PREVIEW") == "1"
config.frame_width = 9
config.frame_height = 16
config.pixel_width = 540 if PREVIEW else 1080
config.pixel_height = 960 if PREVIEW else 1920
config.frame_rate = 30 if PREVIEW else 60
config.background_color = "#FAF6EF"

# ---------------------------------------------------------------- 配色与字体
BG = "#FAF6EF"
INK = "#45423C"
INK_SOFT = "#6C675E"
A_COL = "#9DB9D4"
B_COL = "#E5B084"
C_COL = "#A8C6A6"
ACCENT = "#C4765A"
DIM_OPACITY = 0.14

CN_FONT = "Microsoft YaHei"
MATH_FONT = "Cambria Math"

SIDE = 0.98
OFFSET = np.array([-1.5, -2.0, -2.0])
SUB_Y = -6.92

# 每个镜头只有一组相机参数；角度变化都在这里改，画面代码不重复数字。
CAMERA_SHOTS = {
    "intro": {"phi": 64, "theta": -52, "zoom": 1.02, "frame_center": [0, -0.6, 0]},
    "copy": {"phi": 66, "theta": -72, "zoom": 0.50, "frame_center": [0.05, -0.15, 0]},
    # B 从正前方绕过时最靠画框边缘，0.60 是仍不裁切的最近距离。
    "fit_b": {"zoom": 0.60, "frame_center": [0, -0.9, 0]},
    "reveal": {"phi": 57, "theta": -110, "zoom": 1.06, "frame_center": [0, 0, 0.35]},
}


def camera_direction(shot: str) -> dict:
    """返回镜头 shot 的相机参数；角度单位为度，直接交给 Manim。"""
    spec = {key: value for key, value in CAMERA_SHOTS[shot].items()}
    for key in ("phi", "theta"):
        if key in spec:
            spec[key] = spec[key] * DEGREES
    return spec


def pick_font(candidates: list[str], fallback: str) -> str:
    """从已安装字体中挑第一个可用项，避免中文乱码。"""
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

# MathTex 需要本机 LaTeX；没有时退回 Cambria Math 排版的 MarkupText，
# 数学内容不变，只在 README 中说明。
HAS_LATEX = shutil.which("latex") is not None


def math_text(
    source: str, size: float = 40, color: str = INK, tex: str | None = None
):
    if HAS_LATEX and tex is not None:
        return MathTex(tex, font_size=size * 0.9, color=color)
    return MarkupText(source, font=MATH_FONT, font_size=size, color=color)


# ---------------------------------------------------------------- 几何与动画
def grid_to_world(cell) -> np.ndarray:
    return np.array([cell[0], cell[1], cell[2]], dtype=float) + OFFSET


def shade(color, amount: float) -> ManimColor:
    base = ManimColor(color)
    target = ManimColor("#FFFFFF") if amount > 0 else ManimColor("#000000")
    return interpolate_color(base, target, abs(amount))


def make_cube(cell, color):
    cube = Cube(
        side_length=SIDE,
        fill_color=color,
        fill_opacity=1.0,
        stroke_color=INK,
        stroke_width=1.05,
        stroke_opacity=0.9,
    )
    cube.move_to(grid_to_world(cell))
    cube.face_fills = []
    for face in cube:
        normal = face.get_center() - cube.get_center()
        amount = 0.0
        if normal[2] > 0.4:
            amount = 0.10
        elif normal[2] < -0.4:
            amount = -0.20
        elif normal[0] > 0.4:
            amount = -0.07
        elif normal[0] < -0.4:
            amount = -0.10
        elif normal[1] > 0.4:
            amount = -0.04
        face.set_fill(shade(color, amount), opacity=1.0)
        cube.face_fills.append(face.get_fill_color())
    return cube


def build_piece(cells, color, center_world=None):
    """按格子集合建一个 VGroup；可选地把质心平移到 center_world。"""
    cells = tuple(cells)
    centroid = np.mean(np.array(cells, dtype=float), axis=0)
    target = grid_to_world(centroid) if center_world is None else np.array(center_world)
    delta = target - grid_to_world(centroid)
    group = VGroup()
    for cell in sorted(cells):
        cube = make_cube(cell, color)
        cube.shift(delta)
        group.add(cube)
    group.center_world = target
    return group


class RigidRotation(Animation):
    """绕任意三维轴、绕自身中心做刚体旋转（旋转时所有顶点一起动）。"""

    def __init__(self, mobject, angle, axis, about_point=None, **kwargs):
        super().__init__(mobject, **kwargs)
        self.angle = float(angle)
        self.axis = np.array(axis, dtype=float)
        self.axis /= np.linalg.norm(self.axis)
        self.about = (
            np.array(about_point, dtype=float)
            if about_point is not None
            else np.array(mobject.get_center(), dtype=float)
        )
        self.members = [
            (member, member.points.copy())
            for member in mobject.family_members_with_points()
        ]

    def interpolate_mobject(self, alpha):
        angle = self.angle * self.rate_func(alpha)
        matrix = rotation_matrix(angle, self.axis)
        for member, points in self.members:
            member.set_points((points - self.about) @ matrix.T + self.about)


def ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3


class SquareSumScene(ThreeDScene, VoiceoverScene):
    # ------------------------------------------------------------ 初始化
    def construct(self):
        self.set_speech_service(EdgeTTSService(create_subcaption=False))
        self.timeline: dict[str, dict] = {}

        self.set_camera_orientation(**camera_direction("intro"))

        self.pieces = solve_assembly()
        self.paths = solve_insertion_paths(self.pieces)
        self.stair = generate_staircase()
        self.layer_groups: dict[int, VGroup] = {}

        self.subtitle = None
        self.title = None
        self.question = None
        self.copies_formula = None
        self.top_formula = None
        self.top_counts = None

        self.build_geometry()
        self.animate_sequence()

    # ------------------------------------------------------------ 文字
    def show_subtitle(self, key: str):
        text = SUBTITLES.get(key)
        if not text:
            return
        new = Text(text, font=CN_FONT, font_size=31, color=INK)
        if new.width > 7.6:
            new.scale_to_fit_width(7.6)
        new.move_to([0, SUB_Y, 0])
        self.add_fixed_in_frame_mobjects(new)
        if self.subtitle is None:
            self.play(FadeIn(new, shift=UP * 0.06), run_time=0.22)
        else:
            old = self.subtitle
            self.play(
                FadeOut(old, shift=DOWN * 0.05, run_time=0.16),
                FadeIn(new, shift=UP * 0.05, run_time=0.22),
            )
            self.remove(old)
        self.subtitle = new
        return new

    def mark(self, key: str, tracker) -> None:
        self.timeline[key] = {
            "start": round(float(tracker.start_t), 3),
            "duration": round(float(tracker.duration), 3),
        }
        print(f"[voice] {key:10s} @ {tracker.start_t:6.2f}s  {tracker.duration:5.2f}s")

    def make_title(self):
        left = math_text("1² + 2² + ⋯ + n² =", 42, INK)
        question = Text("?", font=MATH_FONT, font_size=54, color=ACCENT)
        group = VGroup(left, question).arrange(RIGHT, buff=0.18)
        group.move_to([0, 6.35, 0])
        self.add_fixed_in_frame_mobjects(group)
        self.title = group
        self.question = question

    # ------------------------------------------------------------ 几何
    def build_geometry(self):
        """搭出 A 的四层（爆炸高度），随后在 build 镜头里合拢。"""
        self.layer_zs = {0: 0.0, 1: 1.9, 2: 3.4, 3: 4.4}
        self.layer_labels = {}
        for z in range(4):
            cells = {(x, y, z) for x in range(4 - z) for y in range(4 - z)}
            group = VGroup()
            for cell in sorted(cells):
                group.add(make_cube(cell, A_COL))
            group.shift(OUT * self.layer_zs[z])
            self.layer_groups[z] = group

        # A 完成后就是这三层 VGroup 的并集（collapse 后 z 归位）。
        self.a_piece = VGroup(*[self.layer_groups[z] for z in range(4)])

    def collapse_shift(self, z: int) -> np.ndarray:
        """把第 z 层从爆炸高度移回它自己的网格高度。"""
        return OUT * (-self.layer_zs[z])

    def make_layer_label(self, z: int):
        """层数标签：按落位后的层高投影到屏幕，排在右侧，避免被方块挡住。"""
        anchor = np.array([(3 - z) / 2 - 1.5, (3 - z) / 2 - 2.0, z - 1.5])
        screen = self.camera.project_point(anchor)
        label = math_text(f"{4 - z}²", 36, INK_SOFT)
        label.move_to([3.15, screen[1] + 0.08, 0])
        self.add_fixed_in_frame_mobjects(label)
        return label

    # ------------------------------------------------------------ 主流程
    def animate_sequence(self):
        self.make_title()

        with self.voiceover(text=LINES["hook1"]) as tracker:
            self.mark("hook1", tracker)
            self.show_subtitle("hook1")
            self.play(FadeIn(self.title, shift=DOWN * 0.12), run_time=0.6)
            # 四个平方层依次出现（爆炸视图，尚未合拢）
            order = (0, 1, 2, 3)
            for z in order:
                self.play(
                    FadeIn(self.layer_groups[z], shift=OUT * 0.15),
                    run_time=0.55,
                )
                self.wait(0.12)

        with self.voiceover(text=LINES["hook2"]) as tracker:
            self.mark("hook2", tracker)
            self.show_subtitle("hook2")
            self.play(
                self.question.animate(rate_func=there_and_back).scale(1.18),
                run_time=0.55,
            )
            self.play(
                self.question.animate(rate_func=there_and_back).scale(1.18),
                run_time=0.55,
            )
            self.wait(0.5)

        with self.voiceover(text=LINES["build"]) as tracker:
            self.mark("build", tracker)
            self.show_subtitle("build")
            # 底层标签先出现；四层都落位后一起停留，直到复制镜头再退场，
            # 让 1²、2²、3²、4² 都有足够时间被读到。
            label0 = self.make_layer_label(0)
            self.layer_labels[0] = label0
            self.play(FadeIn(label0), run_time=0.3)
            # 逐层落位：3×3 落到 4×4 上，2×2、1×1 依次跟上
            for z in (1, 2, 3):
                label = self.make_layer_label(z)
                self.layer_labels[z] = label
                self.play(
                    self.layer_groups[z].animate(rate_func=smooth).shift(
                        self.collapse_shift(z)
                    ),
                    FadeIn(label),
                    run_time=0.95,
                )
                self.wait(0.12)
            self.wait(0.6)

        with self.voiceover(text=LINES["copy"]) as tracker:
            self.mark("copy", tracker)
            self.show_subtitle("copy")
            self.play(
                *[FadeOut(lab) for lab in self.layer_labels.values()],
                run_time=0.4,
            )
            self.move_camera(**camera_direction("copy"), run_time=1.1)
            self.b_piece = build_piece(self.stair, B_COL, center_world=[-5.0, -0.4, -0.4])
            self.c_piece = build_piece(self.stair, C_COL, center_world=[5.0, -0.4, -0.4])
            self.play(
                FadeIn(self.b_piece, shift=LEFT * 0.3),
                FadeIn(self.c_piece, shift=RIGHT * 0.3),
                run_time=0.9,
            )
            self.copies_formula = math_text("S + S + S = 3S", 38, INK)
            self.copies_formula.move_to([0, 5.0, 0])
            self.add_fixed_in_frame_mobjects(self.copies_formula)
            self.play(FadeIn(self.copies_formula, shift=DOWN * 0.1), run_time=0.5)
            self.wait(0.4)

        with self.voiceover(text=LINES["fit_b"]) as tracker:
            self.mark("fit_b", tracker)
            self.show_subtitle("fit_b")
            self.animate_assembly("B", tracker)

        with self.voiceover(text=LINES["fit_c"]) as tracker:
            self.mark("fit_c", tracker)
            self.show_subtitle("fit_c")
            self.animate_assembly("C", tracker)

        with self.voiceover(text=LINES["reveal"]) as tracker:
            self.mark("reveal", tracker)
            self.show_subtitle("reveal")
            self.play(FadeOut(self.copies_formula), run_time=0.3)
            self.move_camera(**camera_direction("reveal"), run_time=3.0)
            self.top_cubes = [
                cube
                for piece in (self.a_piece, self.b_piece, self.c_piece)
                for cube in piece.get_family()
                if hasattr(cube, "face_fills")
                and abs(cube.get_center()[2] - 2.0) < 0.15
            ]
            self.box_cubes = [
                cube
                for piece in (self.a_piece, self.b_piece, self.c_piece)
                for cube in piece.get_family()
                if hasattr(cube, "face_fills") and cube not in self.top_cubes
            ]
            self.play(
                *[a for cube in self.top_cubes for a in self.state_anims(cube, 0.72)],
                run_time=0.6,
            )
            self.show_box_dimensions()
            self.wait(0.4)

        with self.voiceover(text=LINES["top_count"]) as tracker:
            self.mark("top_count", tracker)
            self.show_subtitle("top_count")
            self.play(
                *[a for cube in self.top_cubes for a in self.state_anims(cube, 0.0)],
                *[a for cube in self.box_cubes for a in self.state_anims(cube, 0.72)],
                run_time=0.5,
            )
            self.highlight_top_rows(tracker)
            self.wait(0.2)

        with self.voiceover(text=LINES["formula"]) as tracker:
            self.mark("formula", tracker)
            self.show_subtitle("formula")
            self.play(
                *[a for cube in self.box_cubes for a in self.state_anims(cube, 0.0)],
                run_time=0.5,
            )
            self.show_volume_formula(tracker)

        with self.voiceover(text=LINES["answer"]) as tracker:
            self.mark("answer", tracker)
            self.show_subtitle("answer")
            self.show_final_formula(tracker)

        with self.voiceover(text=LINES["outro"]) as tracker:
            self.mark("outro", tracker)
            self.show_subtitle("outro")
            self.wait(max(0.2, tracker.duration - 1.0))
            self.play(
                FadeOut(Group(*self.mobjects_excluding_formula())),
                run_time=1.0,
            )
            # 只留公式，干净地停 2 秒。
            self.wait(2.0)

        self.write_timeline()

    @staticmethod
    def rotate_now(piece, angle, axis):
        """不给观众看的一次性刚体旋转，用于已在画外的积木。"""
        about = np.array(piece.get_center(), dtype=float)
        direction = np.array(axis, dtype=float)
        direction = direction / np.linalg.norm(direction)
        matrix = rotation_matrix(float(angle), direction)
        for member in piece.family_members_with_points():
            member.set_points((member.points - about) @ matrix.T + about)

    # ------------------------------------------------------------ 拼装
    def animate_assembly(self, stage: str, tracker):
        """拼装总入口：A 不动，B、C 各自只做整体旋转与平移。"""
        if stage == "B":
            self.assemble_piece_b(tracker)
        elif stage == "C":
            self.assemble_piece_c(tracker)
        else:
            raise ValueError(f"未知拼装阶段: {stage}")

    def assemble_piece_b(self, tracker):
        b = self.pieces["B"]
        axis, angle = rotation_axis_angle(b.rotation)
        self.play(
            RigidRotation(
                self.b_piece,
                angle=angle,
                axis=axis,
                run_time=1.25,
                rate_func=smooth,
            )
        )
        self.wait(0.15)

        entry = self.path_center(self.b_piece, b, self.paths["B"][0])
        delta = entry - np.array(self.b_piece.get_center())
        self.play(
            self.b_piece.animate.set_opacity(1.0).shift(delta),
            run_time=0.7,
            rate_func=smooth,
        )
        # 镜头推近时先把第三块收走，避免它在画框边缘被裁切。
        self.play(FadeOut(self.c_piece), run_time=0.4)
        self.move_camera(**camera_direction("fit_b"), run_time=0.7)

        legs = self.split_legs(self.paths["B"])
        for i, (start_t, end_t) in enumerate(legs):
            target = self.path_center(self.b_piece, b, end_t)
            d = target - np.array(self.b_piece.get_center())
            if i == len(legs) - 1:
                self.visual_emphasis(self.a_piece, 0.45, 0.4)
                self.play(
                    self.b_piece.animate.shift(d),
                    run_time=1.5,
                    rate_func=ease_out,
                )
            elif i == 0:
                self.play(
                    self.b_piece.animate.shift(d),
                    run_time=0.75,
                    rate_func=smooth,
                )
            else:
                self.play(
                    self.b_piece.animate.shift(d),
                    run_time=1.35,
                    rate_func=smooth,
                )
        self.visual_emphasis(self.a_piece, 0.0, 0.4)
        self.flash_contact(self.b_piece)
        self.wait(0.6)

    # ------------------------------------------------------------ 拼装 C
    def assemble_piece_c(self, tracker):
        c = self.pieces["C"]
        axis, angle = rotation_axis_angle(c.rotation)
        # C 已在画外收走；先把旋转直接摆好，再从右侧画外滑入，避免看到瞬间变形。
        self.rotate_now(self.c_piece, angle, axis)
        entry = self.path_center(self.c_piece, c, self.paths["C"][0])
        self.c_piece.shift(entry - np.array(self.c_piece.get_center()))
        self.c_piece.set_opacity(1.0)
        self.add(self.c_piece)
        self.play(
            *[a for piece in (self.a_piece, self.b_piece) for cube in piece.get_family()
              if hasattr(cube, "face_fills") for a in self.state_anims(cube, 0.45)],
            run_time=0.35,
        )
        path = self.paths["C"]
        pause_at = path[-2]
        approach = self.path_center(self.c_piece, c, pause_at)
        self.play(
            self.c_piece.animate.shift(approach - np.array(self.c_piece.get_center())),
            run_time=1.45,
            rate_func=smooth,
        )
        self.wait(0.45)
        final = self.path_center(self.c_piece, c, path[-1])
        self.play(
            self.c_piece.animate.shift(final - np.array(self.c_piece.get_center())),
            run_time=0.85,
            rate_func=ease_out,
        )
        self.play(
            *[a for piece in (self.a_piece, self.b_piece) for cube in piece.get_family()
              if hasattr(cube, "face_fills") for a in self.state_anims(cube, 0.0)],
            run_time=0.4,
        )
        self.flash_contact(self.c_piece)
        self.wait(0.7)

    def path_center(self, piece, placement: Placement, translation) -> np.ndarray:
        """目标位置取包围盒中心，和 Mobject.get_center() 的口径一致。

        用格子质心会让不规则的阶梯体对不齐（曾整体偏 1/3 格），
        所以这里统一用 min/max 的中点。
        """
        rotated = np.array(
            [apply_matrix(placement.rotation, cell) for cell in self.stair],
            dtype=float,
        ) + np.array(translation, dtype=float)
        lo, hi = rotated.min(axis=0), rotated.max(axis=0)
        return grid_to_world((lo + hi) / 2)

    @staticmethod
    def split_legs(path):
        """把整数平移路径切成方向不变的连续段。"""
        legs = []
        start = path[0]
        current = path[1]
        direction = np.subtract(current, start)
        for prev, nxt in zip(path[1:], path[2:]):
            d = np.subtract(nxt, prev)
            if tuple(d) != tuple(direction):
                legs.append((start, prev))
                start = prev
                direction = d
        legs.append((start, path[-1]))
        return legs

    def flash_contact(self, piece):
        for face in piece.family_members_with_points():
            if hasattr(face, "set_stroke"):
                face.set_stroke(color=ACCENT, width=2.2, opacity=0.95)
        self.wait(0.28)
        for face in piece.family_members_with_points():
            if hasattr(face, "set_stroke"):
                face.set_stroke(color=INK, width=1.05, opacity=0.9)

    # ------------------------------------------------------------ 尺寸与公式
    def show_box_dimensions(self):
        """在长方体可见轮廓外侧标出 n（宽）、n+1（深）、n（高）。

        标注是屏幕固定文字：镜头在这个镜头里不再旋转，所以箭头与边框始终贴合；
        放在轮廓外侧，既不会穿过方块，也不会盖住顶部台阶。
        """
        corners = {
            "near": (-1.5, -2.0, -2.0),
            "right": (2.5, -2.0, -2.0),
            "back": (-1.5, 3.0, -2.0),
            "back_top": (-1.5, 3.0, 1.49),
        }
        p = {
            key: np.array(self.camera.project_point(np.array(value, dtype=float)))[:2]
            for key, value in corners.items()
        }

        def unit(a, b):
            d = p[b] - p[a]
            return d / np.linalg.norm(d)

        def outward(a, b, sign):
            d = unit(a, b)
            return np.array([-d[1], d[0]]) * sign

        specs = [
            ("near", "right", -1.0, 0.55, "n"),      # 宽 4
            ("near", "back", 1.0, 0.55, "n+1"),      # 深 5
            ("back", "back_top", 1.0, 0.55, "n"),    # 高 4
        ]
        arrows = VGroup()
        labels = VGroup()
        for a, b, sign, gap, text in specs:
            n = outward(a, b, sign)
            start = np.append(p[a] + n * gap, 0.0)
            end = np.append(p[b] + n * gap, 0.0)
            arrows.add(
                Arrow(
                    start,
                    end,
                    buff=0.02,
                    color=ACCENT,
                    stroke_width=3.2,
                    max_tip_length_to_length_ratio=0.09,
                )
            )
            label = math_text(text, 38, ACCENT)
            label.move_to(np.append((p[a] + p[b]) / 2 + n * (gap + 0.52), 0.0))
            labels.add(label)

        self.add_fixed_in_frame_mobjects(arrows, labels)
        self.play(
            *[Create(arrow) for arrow in arrows],
            FadeIn(labels, shift=UP * 0.08),
            run_time=0.9,
        )
        self.dim_group = VGroup(arrows, labels)

    def highlight_top_rows(self, tracker):
        rows = []
        for x in range(4):
            cells = [(x, y, 4) for y in range(x + 1)]
            cubes = [c for c in self.top_cubes if round(c.get_center()[0] + 1.5) == x]
            rows.append(cubes)
        step = max(0.7, tracker.duration / 4)
        counts = VGroup()
        for x, cubes in enumerate(rows):
            label = math_text(str(x + 1), 34, ACCENT)
            pos = grid_to_world((x, x + 0.85, 4.7))
            label.move_to(pos)
            self.add_fixed_orientation_mobjects(label)
            tint_anims = []
            for cube in cubes:
                tint_anims += self.tint_anims(cube, ACCENT, 0.55)
            self.play(
                *tint_anims,
                FadeIn(label, scale=0.8),
                run_time=0.36,
            )
            counts.add(label)
            self.wait(max(0.15, step - 0.36))
        self.top_counts = counts
        formula = VGroup(
            math_text("1 + 2 + ⋯ + n =", 36, INK),
            self.fraction("n(n+1)", "2", 32, INK),
        ).arrange(RIGHT, buff=0.16)
        self.fit_width(formula)
        formula.move_to([0, -5.35, 0])
        self.add_fixed_in_frame_mobjects(formula)
        self.play(FadeIn(formula, shift=UP * 0.08), run_time=0.5)
        self.top_formula = formula
        self.wait(0.3)

    def tint_anims(self, cube, color, amount=0.5):
        anims = []
        for face, original in zip(cube, getattr(cube, "face_fills", [])):
            target = interpolate_color(original, ManimColor(color), amount)
            anims.append(face.animate.set_fill(target, opacity=1.0))
        return anims

    def state_anims(self, cube, amount: float):
        """用降低饱和度（而非透明度）表达“已放好”，避免方块变成幽灵。

        amount=0 恢复原色，amount=1 完全退到纸色。
        """
        return self.tint_anims(cube, BG, amount)

    def visual_emphasis(self, piece, amount: float, run_time: float = 0.35):
        """统一的“放置状态”视觉：0 保持饱和，越大越向纸色退去。

        正在移动的积木始终饱和，已放置的被压暗；接触边另由 flash_contact 高亮。
        """
        cubes = [m for m in piece.get_family() if hasattr(m, "face_fills")]
        self.play(
            *[a for cube in cubes for a in self.state_anims(cube, amount)],
            run_time=run_time,
        )

    def show_volume_formula(self, tracker):
        # 顶部台阶的计数公式先退场，避免与体积公式叠在同一行。
        if self.top_formula is not None:
            self.play(FadeOut(self.top_formula, shift=DOWN * 0.06), run_time=0.3)
            self.top_formula = None
        left = math_text("3S = n(n+1)·n +", 40, INK)
        frac = self.fraction("n(n+1)", "2", 32, INK)
        line1 = VGroup(left, frac).arrange(RIGHT, buff=0.16)
        self.fit_width(line1)
        line1.move_to([0, -5.35, 0])
        self.add_fixed_in_frame_mobjects(line1)
        self.play(FadeIn(line1, shift=UP * 0.1), run_time=0.6)
        self.wait(0.5)

        line2 = math_text("3S = n(n+1)(n + ½)", 42, INK)
        self.fit_width(line2)
        line2.move_to([0, -5.35, 0])
        self.add_fixed_in_frame_mobjects(line2)
        self.play(FadeOut(line1, shift=DOWN * 0.06), run_time=0.4)
        self.play(FadeIn(line2, shift=UP * 0.06), run_time=0.55)
        self.wait(0.6)
        self.volume_line = line2

    def show_final_formula(self, tracker):
        # 积木缩小上移，公式居中
        self.assembly = VGroup(self.a_piece, self.b_piece, self.c_piece)
        still_there = [m for m in (self.top_formula, self.top_counts) if m is not None]
        self.play(
            self.assembly.animate.scale(0.46).move_to([0, 0.5, 3.2]),
            FadeOut(self.volume_line),
            FadeOut(self.dim_group),
            *[FadeOut(m) for m in still_there],
            FadeOut(self.title),
            run_time=1.2,
        )
        self.play(
            *[a for cube in self.top_cubes for a in self.state_anims(cube, 0.0)],
            run_time=0.4,
        )
        self.top_formula = None
        step1 = VGroup(
            math_text("S = n(n+1)(n + ½) ÷ 3", 40, INK),
        )
        self.fit_width(step1)
        step1.move_to([0, -2.6, 0])
        step1.set_z_index(200)
        self.add_fixed_in_frame_mobjects(step1)
        self.play(FadeIn(step1, shift=UP * 0.08), run_time=0.6)
        self.wait(0.4)

        final = VGroup(
            math_text("1² + 2² + ⋯ + n² =", 42, INK),
            self.fraction("n(n+1)(2n+1)", "6", 36, ACCENT),
        ).arrange(RIGHT, buff=0.2)
        self.fit_width(final, 7.4)
        final.move_to([0, -2.6, 0])
        final.set_z_index(200)
        self.add_fixed_in_frame_mobjects(final)
        self.play(FadeOut(step1, shift=DOWN * 0.06), run_time=0.4)
        self.play(FadeIn(final, shift=UP * 0.08), run_time=0.8)
        self.final_formula = final
        self.wait(max(0.5, tracker.duration - 3.2))

    @staticmethod
    def fit_width(group, width: float = 7.6):
        """竖屏安全边距：公式最宽 7.6/9 个画幅单位。"""
        if group.width > width:
            group.scale_to_fit_width(width)
        return group

    def fraction(self, numerator: str, denominator: str, size: float, color: str):
        n = math_text(numerator, size, color)
        d = math_text(denominator, size, color)
        line = Line(LEFT, RIGHT, color=color, stroke_width=2.0)
        width = max(n.width, d.width) + 0.12
        line.set_width(width)
        n.next_to(line, UP, buff=0.05)
        d.next_to(line, DOWN, buff=0.05)
        return VGroup(n, line, d)

    # ------------------------------------------------------------ 收尾
    def mobjects_excluding_formula(self):
        return [m for m in self.mobjects if m is not self.final_formula]

    def write_timeline(self):
        out = Path("media") / "timeline.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(
            json.dumps(self.timeline, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        cues = synchronize_subtitles(self.timeline, pause=PAUSE)
        export_srt(cues, "subtitles.srt")
        print("[timeline]", {k: (v["start"], v["duration"]) for k, v in self.timeline.items()})
