"""Visual proof: 1 + 2 + ... + n = n(n + 1) / 2.

Two staircases of n rows, rotated and interlocked, tile an n x (n + 1) rectangle.
Rendered for a 1080 x 1920 portrait frame. No LaTeX: Text / MarkupText only.

Run:
    python -m manim -qh sum_one_to_n.py SumOneToN
"""

import numpy as np

from manim import (
    AnimationGroup,
    Circle,
    Create,
    DoubleArrow,
    DOWN,
    FadeIn,
    GrowFromCenter,
    LaggedStart,
    LEFT,
    MarkupText,
    PI,
    Rectangle,
    RIGHT,
    Rotate,
    Scene,
    Text,
    UP,
    VGroup,
    config,
    smooth,
)

# ---------------------------------------------------------------- palette
BG = "#FAF6EF"          # warm white
TEAL = "#6FA79D"        # muted teal
TEAL_EDGE = "#598C83"
TERRA = "#C98A6E"       # muted terracotta
TERRA_EDGE = "#AC7057"
INK = "#3B3A36"
MUTED = "#9A9388"

CN_FONT = "Microsoft YaHei"
MATH_FONT = "Georgia"

# ---------------------------------------------------------------- frame
config.frame_width = 9.0
config.frame_height = 16.0
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_rate = 60
config.background_color = BG

# geometry (scene units)
N = 5
S = 1.0                 # cell edge
BALL_R = 0.40           # ball radius, leaves a small matte gap
RECT_CENTER = np.array([0.0, 1.2, 0.0])


def make_ball(fill: str, edge: str) -> Circle:
    """A flat, matte ball: solid fill plus a faint darker rim."""
    return Circle(
        radius=BALL_R,
        fill_color=fill,
        fill_opacity=1.0,
        stroke_color=edge,
        stroke_width=1.6,
        stroke_opacity=0.45,
    )


class SumOneToN(Scene):
    def construct(self):
        self.camera.background_color = BG

        width = (N + 1) * S
        height = N * S
        bottom_left = (
            RECT_CENTER + LEFT * (width / 2) + DOWN * (height / 2)
        )

        def cell(row: int, col: int) -> np.ndarray:
            """Center of the cell at (row from bottom, column from left)."""
            return (
                bottom_left
                + RIGHT * ((col + 0.5) * S)
                + UP * ((row + 0.5) * S)
            )

        # ------------------------------------------------ staircase (teal)
        rows = VGroup()
        for r in range(N):
            row = VGroup(*[make_ball(TEAL, TEAL_EDGE) for _ in range(r + 1)])
            for c, ball in enumerate(row):
                ball.move_to(cell(r, c))
            rows.add(row)
        stair = VGroup(rows)

        self.wait(0.6)
        for r, row in enumerate(rows):
            self.play(
                LaggedStart(
                    *[GrowFromCenter(ball) for ball in row],
                    lag_ratio=0.18,
                ),
                run_time=0.50 + 0.08 * r,
                rate_func=smooth,
            )
            self.wait(0.06)
        self.wait(0.8)

        # ------------------------------------------------ rotated copy
        copy = stair.copy()
        copy.set_fill(TERRA, opacity=1.0)
        copy.set_stroke(TERRA_EDGE, width=1.6, opacity=0.45)

        lift = 0.7
        copy.shift(UP * lift)
        self.play(FadeIn(copy, run_time=0.55))
        self.wait(0.2)

        self.play(
            Rotate(copy, PI, about_point=copy.get_center()),
            run_time=1.25,
            rate_func=smooth,
        )
        self.wait(0.15)

        # rotate about its own centre, then slide one cell right and back down
        self.play(
            copy.animate.shift(RIGHT * S + DOWN * lift),
            run_time=1.1,
            rate_func=smooth,
        )
        self.wait(0.5)

        # ------------------------------------------------ rectangle
        rect = Rectangle(
            width=width,
            height=height,
            stroke_color=INK,
            stroke_width=3.0,
            stroke_opacity=0.8,
            fill_opacity=0.0,
        ).move_to(RECT_CENTER)

        self.play(Create(rect, run_time=1.1, rate_func=smooth))
        self.wait(0.3)

        # ------------------------------------------------ dimensions
        row_arrow = DoubleArrow(
            start=bottom_left + LEFT * 0.45,
            end=bottom_left + LEFT * 0.45 + UP * height,
            buff=0.0,
            stroke_width=2.2,
            color=MUTED,
            tip_length=0.16,
        )
        col_arrow = DoubleArrow(
            start=bottom_left + DOWN * 0.5,
            end=bottom_left + DOWN * 0.5 + RIGHT * width,
            buff=0.0,
            stroke_width=2.2,
            color=MUTED,
            tip_length=0.16,
        )

        row_label = Text("n 行", font=CN_FONT, font_size=34, color=INK)
        row_label.rotate(PI / 2).next_to(row_arrow, LEFT, buff=0.28)

        col_label = Text("n + 1 列", font=CN_FONT, font_size=34, color=INK)
        col_label.next_to(col_arrow, DOWN, buff=0.26)

        self.play(
            AnimationGroup(
                Create(row_arrow),
                Create(col_arrow),
                FadeIn(row_label, shift=RIGHT * 0.12),
                FadeIn(col_label, shift=UP * 0.12),
                lag_ratio=0.15,
            ),
            run_time=0.9,
            rate_func=smooth,
        )
        self.wait(0.5)

        # ------------------------------------------------ formula
        formula = MarkupText(
            "1 + 2 + ··· + <i>n</i> = <i>n</i>(<i>n</i> + 1)/2",
            font=MATH_FONT,
            font_size=58,
            color=INK,
        )
        formula.move_to(np.array([0.0, -3.55, 0.0]))
        if formula.width > 7.1:
            formula.scale_to_fit_width(7.1)

        self.play(
            FadeIn(formula, shift=UP * 0.25, run_time=1.3, rate_func=smooth)
        )
        self.wait(3.2)
