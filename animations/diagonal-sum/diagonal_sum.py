"""Visual proof: 1 + 2 + ... + n + ... + 2 + 1 = n².

A 5×5 grid is counted along parallel diagonals.  The diagonals hold
1, 2, 3, 4, 5, 4, 3, 2, 1 balls, so the whole square has 25 balls:
the same sum, seen without adding term by term.

Rendered for a 1080 × 1920 portrait frame.  Pencil-style text, warm paper,
low-saturation colours.  Each spoken line is a manim-voiceover block, and
narration / subtitles / sound cues live in narration.py.

Run:
    python -m manim diagonal_sum.py DiagonalSum
    python make_sfx.py
    python mix_audio.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from manim import (
    AnimationGroup,
    Circle,
    Create,
    DashedLine,
    DoubleArrow,
    DOWN,
    FadeIn,
    FadeOut,
    GrowFromCenter,
    ImageMobject,
    LaggedStart,
    LEFT,
    MarkupText,
    ORIGIN,
    PI,
    Rectangle,
    RIGHT,
    Text,
    UP,
    VGroup,
    config,
    logger,
    smooth,
    there_and_back,
)
from manim_voiceover import VoiceoverScene
from PIL import Image

from narration import (
    CUES,
    NARRATION,
    PAUSE,
    SUBTITLES,
    EdgeTTSService,
)

# ---------------------------------------------------------------- palette
BG = "#FAF6EF"           # warm paper
INK = "#4B4740"          # graphite
MUTED = "#8C857A"
TEAL = "#8AAFA6"         # low-saturation teal
TEAL_DARK = "#6F978E"
TEAL_SOLID = "#7FA79E"   # final uniform square
TERRA = "#CE9A80"        # low-saturation terracotta
TERRA_DARK = "#B57F66"
BALL_BASE = "#F4EDE1"    # unlit paper ball

MATH_FONT = "Segoe Print"
CN_FONT = "KaiTi"

# ---------------------------------------------------------------- frame
config.frame_width = 9.0
config.frame_height = 16.0
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_rate = 60
config.background_color = BG


@dataclass(frozen=True)
class SquareGrid:
    """5×5 ball grid; row 0 is the top row, column 0 the left column."""

    n: int = 5
    cell: float = 1.15
    radius: float = 0.42
    center_y: float = 1.0

    @property
    def half(self) -> float:
        return (self.n - 1) / 2 * self.cell

    @property
    def extent(self) -> float:
        return self.half + self.radius

    def pos(self, row: int, col: int) -> np.ndarray:
        return np.array(
            [
                (col - (self.n - 1) / 2) * self.cell,
                self.center_y + ((self.n - 1) / 2 - row) * self.cell,
                0.0,
            ]
        )

    def cells(self):
        return [(row, col) for row in range(self.n) for col in range(self.n)]

    def diagonal(self, key: int):
        return [(row, col) for row, col in self.cells() if row + col == key]


GRID = SquareGrid()


def paper_texture() -> ImageMobject | None:
    """一张很淡的纸纹，生成一次后缓存在 media/ 中。"""
    path = Path(__file__).resolve().parent / "media" / "paper.png"
    try:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            width, height = 540, 960
            rng = np.random.default_rng(11)
            base = np.array([250.0, 246.0, 239.0])
            noise = rng.normal(0, 1.25, (height, width))
            yy, xx = np.mgrid[0:height, 0:width]
            vignette = 1 - 0.018 * (
                ((xx - width / 2) / (width / 2)) ** 2
                + ((yy - height / 2) / (height / 2)) ** 2
            )
            pixels = base[None, None, :] + noise[..., None]
            pixels = pixels * vignette[..., None]
            Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8)).save(path)
        texture = ImageMobject(str(path)).scale_to_fit_height(config.frame_height)
        return texture.move_to(ORIGIN).set_z_index(-100)
    except Exception as exc:  # 纹理只是装饰，失败时退回纯色纸面
        logger.warning(f"paper texture skipped: {exc}")
        return None


def make_ball(center: np.ndarray, row: int, col: int) -> Circle:
    """A lightly wobbled circle, so the grid does not look machine-perfect."""
    ball = Circle(
        radius=GRID.radius,
        fill_color=BALL_BASE,
        fill_opacity=1.0,
        stroke_color=INK,
        stroke_width=1.7,
        stroke_opacity=0.55,
    )
    phase = 0.7 * row + 1.3 * col

    def wobble(point: np.ndarray) -> np.ndarray:
        x, y = point[0], point[1]
        r = np.hypot(x, y)
        if r < 1e-9:
            return point
        angle = np.arctan2(y, x)
        scale = 1 + 0.013 * np.sin(3 * angle + phase)
        scale += 0.008 * np.sin(5 * angle + 2 * phase)
        return np.array([x * scale, y * scale, point[2]])

    ball.apply_function(wobble)
    ball.move_to(center)
    return ball


class DiagonalSum(VoiceoverScene):
    def construct(self):
        self.camera.background_color = BG
        self.set_speech_service(EdgeTTSService(), create_subcaption=False)

        texture = paper_texture()
        if texture is not None:
            self.add(texture)

        self.timeline: dict[str, dict[str, float]] = {}
        self.balls: dict[tuple[int, int], Circle] = {}
        self.diag_lines: list = []
        self.count_labels: list = []
        self.subtitle = None
        self.hook_formula = None
        self.answer = None
        self.border = None
        self.dimensions = None

        self.hook()
        self.turn()
        self.count_intro()
        self.count_up()
        self.count_down()
        self.epiphany()
        self.answer_part_one()
        self.answer_part_two()
        self.outro()

        timeline_path = Path(__file__).resolve().parent / "media" / "timeline.json"
        timeline_path.parent.mkdir(parents=True, exist_ok=True)
        timeline_path.write_text(
            json.dumps(self.timeline, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"[timeline] wrote {timeline_path}")

    # ------------------------------------------------------------ helpers
    def mark(self, key: str, tracker) -> None:
        self.timeline[key] = {
            "start": round(tracker.start_t, 3),
            "duration": round(tracker.duration, 3),
        }
        logger.info(
            f"[voice] {key} @ {tracker.start_t:.2f}s, {tracker.duration:.2f}s"
        )

    def show_subtitle(self, key: str) -> None:
        text = SUBTITLES.get(key)
        if not text:
            return
        new = Text(text, font=CN_FONT, font_size=31, color=INK)
        if new.width > 7.6:
            new.scale_to_fit_width(7.6)
        new.move_to(np.array([0.0, -6.25, 0.0]))

        if self.subtitle is None:
            self.play(FadeIn(new, shift=UP * 0.08), run_time=0.25)
        else:
            self.play(
                FadeOut(self.subtitle, shift=DOWN * 0.06, run_time=0.18),
                FadeIn(new, shift=UP * 0.06, run_time=0.25),
            )
        self.subtitle = new

    def make_diagonal(self, key: int) -> DashedLine:
        cells = sorted(GRID.diagonal(key), key=lambda pair: pair[1])
        start = GRID.pos(*cells[0]) + np.array([-0.55 * GRID.cell, -0.55 * GRID.cell, 0])
        end = GRID.pos(*cells[-1]) + np.array([0.55 * GRID.cell, 0.55 * GRID.cell, 0])
        return DashedLine(
            start,
            end,
            dash_length=0.12,
            dashed_ratio=0.55,
            stroke_color=INK,
            stroke_width=1.8,
            stroke_opacity=0.50,
        )

    def highlight_group(self, key: int, color: str, dark: str):
        cells = sorted(GRID.diagonal(key), key=lambda pair: pair[1])
        balls = [self.balls[cell].animate.set_fill(color, opacity=1.0) for cell in cells]
        count = len(cells)
        label = Text(
            str(count),
            font=MATH_FONT,
            font_size=34,
            color=dark,
        )
        label.move_to(np.array([(key - 4) * 0.78, -2.58, 0.0]))
        self.count_labels.append(label)
        return AnimationGroup(
            LaggedStart(*balls, lag_ratio=0.12),
            self.diag_lines[key].animate.set_stroke(width=2.4, opacity=0.9),
            FadeIn(label, scale=1.25),
            lag_ratio=0.10,
        )

    def make_square_frame(self):
        size = 2 * GRID.extent
        border = Rectangle(
            width=size,
            height=size,
            stroke_color=INK,
            stroke_width=2.2,
            stroke_opacity=0.55,
            fill_opacity=0.0,
        ).move_to(np.array([0.0, GRID.center_y, 0.0]))
        echo = border.copy().set_stroke(width=1.0, opacity=0.22)
        echo.shift(np.array([0.014, -0.012, 0.0]))

        top_y = GRID.center_y + GRID.extent + 0.22
        top_arrow = DoubleArrow(
            start=np.array([-GRID.extent, top_y, 0.0]),
            end=np.array([GRID.extent, top_y, 0.0]),
            buff=0.0,
            stroke_width=1.8,
            color=INK,
            tip_length=0.13,
            stroke_opacity=0.55,
        )
        top_label = Text("5", font=MATH_FONT, font_size=34, color=INK)
        top_label.next_to(top_arrow, UP, buff=0.10)

        left_x = -GRID.extent - 0.24
        left_arrow = DoubleArrow(
            start=np.array([left_x, GRID.center_y - GRID.extent, 0.0]),
            end=np.array([left_x, GRID.center_y + GRID.extent, 0.0]),
            buff=0.0,
            stroke_width=1.8,
            color=INK,
            tip_length=0.13,
            stroke_opacity=0.55,
        )
        left_label = Text("5", font=MATH_FONT, font_size=34, color=INK)
        left_label.rotate(PI / 2).next_to(left_arrow, LEFT, buff=0.10)

        return VGroup(border, echo), VGroup(top_arrow, top_label, left_arrow, left_label)

    # ------------------------------------------------------------ stages
    def hook(self) -> None:
        with self.voiceover(text=NARRATION["hook"]) as tracker:
            self.mark("hook", tracker)
            self.show_subtitle("hook")

            left = Text(
                "1 + 2 + 3 + 4 + 5 + 4 + 3 + 2 + 1 =",
                font=MATH_FONT,
                font_size=38,
                color=INK,
            )
            question = Text("?", font=MATH_FONT, font_size=46, color=TERRA_DARK)
            formula = VGroup(left, question).arrange(RIGHT, buff=0.16)
            if formula.width > 8.1:
                formula.scale_to_fit_width(8.1)
            formula.move_to(np.array([0.0, 2.30, 0.0]))

            self.play(
                FadeIn(left, shift=UP * 0.12),
                FadeIn(question, scale=0.8),
                run_time=0.55,
                rate_func=smooth,
            )
            for _ in range(2):
                self.play(
                    question.animate.scale(1.12, about_point=question.get_center()),
                    run_time=0.16,
                    rate_func=smooth,
                )
                self.play(
                    question.animate.scale(
                        1 / 1.12, about_point=question.get_center()
                    ),
                    run_time=0.16,
                    rate_func=smooth,
                )
            self.hook_formula = formula

    def turn(self) -> None:
        with self.voiceover(text=NARRATION["turn"]) as tracker:
            self.mark("turn", tracker)
            self.show_subtitle("turn")

            target = self.hook_formula.copy()
            target.scale(0.66).move_to(np.array([0.0, 6.25, 0.0]))
            self.play(
                FadeOut(self.hook_formula, shift=UP * 0.15),
                FadeIn(target, shift=UP * 0.15),
                run_time=0.65,
                rate_func=smooth,
            )
            self.hook_formula = target
            self.play(
                self.hook_formula.animate.set_opacity(0.50),
                run_time=0.25,
                rate_func=smooth,
            )

            # 1×1 → 2×2 → 3×3 → 4×4 → 5×5, each step centred on the grid
            for step in range(1, GRID.n + 1):
                start = (GRID.n - step) // 2
                fresh = []
                for row in range(start, start + step):
                    for col in range(start, start + step):
                        if (row, col) in self.balls:
                            continue
                        ball = make_ball(GRID.pos(row, col), row, col)
                        self.balls[(row, col)] = ball
                        fresh.append(ball)
                self.play(
                    LaggedStart(
                        *[GrowFromCenter(ball) for ball in fresh],
                        lag_ratio=0.12,
                    ),
                    run_time=0.55 if step == 1 else 0.45,
                    rate_func=smooth,
                )
                if step == 1:
                    first = fresh[0]
                    self.play(first.animate.scale(1.12), run_time=0.14)
                    self.play(first.animate.scale(1 / 1.12), run_time=0.14)
                    self.wait(0.05)
            self.wait(0.25)

    def count_intro(self) -> None:
        with self.voiceover(text=NARRATION["count_intro"]) as tracker:
            self.mark("count_intro", tracker)
            self.show_subtitle("count_intro")

            self.diag_lines = [
                self.make_diagonal(key).set_z_index(-1)
                for key in range(2 * GRID.n - 1)
            ]
            self.play(
                LaggedStart(
                    *[FadeIn(line, shift=UP * 0.02) for line in self.diag_lines],
                    lag_ratio=0.08,
                ),
                run_time=0.7,
                rate_func=smooth,
            )

    def count_up(self) -> None:
        with self.voiceover(text=NARRATION["count_up"]) as tracker:
            self.mark("count_up", tracker)
            self.show_subtitle("count_up")

            step = tracker.duration / 5
            for index, key in enumerate(range(5)):
                accent, dark = (TEAL, TEAL_DARK) if key % 2 == 0 else (TERRA, TERRA_DARK)
                self.play(
                    self.highlight_group(key, accent, dark),
                    run_time=0.42,
                    rate_func=smooth,
                )
                if index < 4:
                    self.wait(max(0.0, step - 0.42))

    def count_down(self) -> None:
        with self.voiceover(text=NARRATION["count_down"]) as tracker:
            self.mark("count_down", tracker)
            self.show_subtitle("count_down")

            step = tracker.duration / 4
            for index, key in enumerate(range(5, 9)):
                accent, dark = (TEAL, TEAL_DARK) if key % 2 == 0 else (TERRA, TERRA_DARK)
                self.play(
                    self.highlight_group(key, accent, dark),
                    run_time=0.36,
                    rate_func=smooth,
                )
                if index < 3:
                    self.wait(max(0.0, step - 0.36))
            self.wait(0.15)
        self.wait(PAUSE)

    def epiphany(self) -> None:
        self.wait(0.3)  # 「等等」前留半拍
        with self.voiceover(text=NARRATION["epiphany"]) as tracker:
            self.mark("epiphany", tracker)
            # 先让「等等」落地，等方阵变成同一种颜色后再出字幕
            if self.subtitle is not None:
                self.remove(self.subtitle)
                self.subtitle = None

            self.play(
                FadeOut(VGroup(*self.diag_lines)),
                run_time=0.55,
                rate_func=smooth,
            )
            self.play(
                AnimationGroup(
                    *[
                        ball.animate.set_fill(TEAL_SOLID, opacity=1.0)
                        for ball in self.balls.values()
                    ]
                ),
                run_time=0.60,
                rate_func=smooth,
            )
            self.show_subtitle("epiphany")

            self.border, self.dimensions = self.make_square_frame()
            self.play(
                Create(self.border),
                FadeIn(self.dimensions, shift=UP * 0.08),
                run_time=0.75,
                rate_func=smooth,
            )

            stage = VGroup(
                *self.balls.values(),
                self.border,
                self.dimensions,
                *self.count_labels,
                self.hook_formula,
            )
            self.play(
                stage.animate.scale(
                    0.96, about_point=np.array([0.0, GRID.center_y, 0.0])
                ),
                run_time=0.9,
                rate_func=smooth,
            )

    def answer_part_one(self) -> None:
        with self.voiceover(text=NARRATION["answer1"]) as tracker:
            self.mark("answer1", tracker)
            self.show_subtitle("answer1")

            self.play(
                FadeOut(VGroup(*self.count_labels), shift=DOWN * 0.08),
                FadeOut(self.hook_formula),
                run_time=0.50,
                rate_func=smooth,
            )

            line1 = MarkupText(
                "1 + 2 + 3 + 4 + 5 + 4 + 3 + 2 + 1 = ?",
                font=MATH_FONT,
                font_size=36,
                color=INK,
            )
            line1.scale_to_fit_width(8.0)
            line1.move_to(np.array([0.0, -2.85, 0.0]))
            self.play(FadeIn(line1, shift=UP * 0.12), run_time=0.55)

            line2 = MarkupText(
                "1 + 2 + 3 + 4 + 5 + 4 + 3 + 2 + 1 = 5 × 5 = 25",
                font=MATH_FONT,
                font_size=36,
                color=INK,
            )
            line2.scale_to_fit_width(8.2)
            line2.move_to(np.array([0.0, -2.85, 0.0]))
            self.play(
                FadeOut(line1, shift=DOWN * 0.06),
                run_time=0.35,
                rate_func=smooth,
            )
            self.play(
                FadeIn(line2, shift=UP * 0.08),
                run_time=0.45,
                rate_func=smooth,
            )
            self.answer = line2

    def answer_part_two(self) -> None:
        with self.voiceover(text=NARRATION["answer2"]) as tracker:
            self.mark("answer2", tracker)
            self.show_subtitle("answer2")

            general = MarkupText(
                "1 + 2 + … + <i>n</i> + … + 2 + 1 = <i>n</i>²",
                font=MATH_FONT,
                font_size=46,
                color=INK,
            )
            general.scale_to_fit_width(7.8)
            general.move_to(np.array([0.0, -2.85, 0.0]))
            self.play(
                FadeOut(self.answer, shift=DOWN * 0.06),
                run_time=0.35,
                rate_func=smooth,
            )
            self.play(
                FadeIn(general, shift=UP * 0.08),
                run_time=0.50,
                rate_func=smooth,
            )
            self.answer = general

    def outro(self) -> None:
        with self.voiceover(text=NARRATION["outro"]) as tracker:
            self.mark("outro", tracker)
            self.show_subtitle("outro")

            ball = self.balls[(GRID.n - 1, GRID.n - 1)]
            self.play(
                ball.animate(run_time=0.50, rate_func=there_and_back)
                .scale(1.16)
                .shift(UP * 0.18),
                run_time=0.50,
            )
            self.wait(0.20)

            fade_length = 0.8
            # 字幕淡入 0.25 s + 弹跳 0.5 s + 停顿 0.2 s
            remaining = tracker.duration - 0.95 - fade_length
            if remaining > 0:
                self.wait(remaining)

            cast = VGroup(
                *self.balls.values(),
                self.border,
                self.dimensions,
                self.answer,
                self.subtitle,
            )
            self.play(FadeOut(cast), run_time=fade_length, rate_func=smooth)
            self.subtitle = None
        self.wait(0.2)
