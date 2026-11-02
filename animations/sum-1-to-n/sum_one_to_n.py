"""Visual proof: 1 + 2 + ... + n = n(n + 1) / 2.

The staircase is drawn in compressed form: rows 1, 2, 3 and n are visible,
while the rows in between are represented by a vertical ellipsis.  Two such
staircases still tile an n x (n + 1) rectangle: the hidden middle band stays
empty in both copies, and every visible row is completed by the other colour.

Rendered for a 1080 x 1920 portrait frame. No LaTeX: Text / MarkupText only.

Each stage is wrapped in a manim-voiceover block, so the spoken line sets the
pace: the animation never speeds up, and the scene waits for the voice to end.
Narration text and voice settings live in narration.py.

Run:
    python -m manim sum_one_to_n.py SumOneToN
    python make_bgm.py
    python mix_audio.py
"""

from dataclasses import dataclass

import numpy as np

from manim import (
    AnimationGroup,
    Circle,
    Create,
    DoubleArrow,
    DOWN,
    FadeIn,
    FadeOut,
    FadeTransform,
    GrowFromCenter,
    LaggedStart,
    LEFT,
    MarkupText,
    PI,
    Rectangle,
    RIGHT,
    Rotate,
    Text,
    UP,
    VGroup,
    config,
    logger,
    smooth,
)
from manim_voiceover import VoiceoverScene

from narration import NARRATION, PAUSE, EdgeTTSService

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

# ---------------------------------------------------------------- data
N = 5                       # last row of the staircase; change freely
TOP_ROWS = (1, 2, 3)        # concrete rows shown before the ellipsis
GRID_WIDTH = 6.0            # n + 1 columns always occupy this width
Y_CENTER = 1.4              # vertical centre of the square-ish block

assert N >= TOP_ROWS[-1] + 2, "need at least one hidden row for the ellipsis"

# One place to tune the timeline; every beat below uses one of these values.
# The narrated version is a little slower than the silent cut, never faster.
TIMING = {
    "lead_in": 0.5,
    "build_row": 0.75,
    "layout_shift": 1.4,
    "last_row": 1.2,
    "label_morph": 0.9,
    "read_stair": 0.6,
    "copy_fade": 0.6,
    "rotate": 1.6,
    "slide": 1.4,
    "settle": 1.0,
    "read_rect": 0.4,
    "rect_draw": 1.4,
    "dimensions": 1.3,
    "formula_in": 1.5,
    "final_hold": 2.0,
}


@dataclass(frozen=True)
class StaircaseLayout:
    """Math data and screen positions for the compressed staircase.

    ``display_rows`` are the rows that actually get drawn.  ``hidden_rows``
    are real mathematical rows folded into the single ellipsis band; they are
    never rendered as rows, but they still count in the proof.
    """

    n: int
    top_rows: tuple
    grid_width: float
    y_center: float

    # ---- derived geometry ------------------------------------------------
    @property
    def cell(self) -> float:
        return self.grid_width / (self.n + 1)

    @property
    def width(self) -> float:
        return self.grid_width

    @property
    def height(self) -> float:
        # three visible rows + one empty band + the n-th row
        return 5.0 * self.cell

    @property
    def left(self) -> float:
        return -self.width / 2

    @property
    def right(self) -> float:
        return self.width / 2

    @property
    def top(self) -> float:
        return self.y_center + 2.5 * self.cell

    @property
    def bottom(self) -> float:
        return self.y_center - 2.5 * self.cell

    @property
    def display_rows(self) -> tuple:
        return self.top_rows + (self.n,)

    @property
    def hidden_rows(self) -> tuple:
        return tuple(range(self.top_rows[-1] + 1, self.n))

    # ---- positions -------------------------------------------------------
    def row_y(self, row: int) -> float:
        if row == self.n:
            # symmetric with row 1 about row 3, so a 180-degree rotation of
            # the drawn block keeps row 3 in place and puts row 2 in the gap
            return self.y_center - 2.0 * self.cell
        return self.y_center + (3 - row) * self.cell

    @property
    def gap_y(self) -> float:
        return self.y_center - self.cell

    def col_x(self, col: int) -> float:
        return self.left + (col + 0.5) * self.cell

    def center(self, row: int, col: int) -> np.ndarray:
        return np.array([self.col_x(col), self.row_y(row), 0.0])

    def a_cols(self, row: int) -> range:
        """Left-aligned row in the original staircase: row balls."""
        return range(row)

    def b_cols(self, row: int) -> range:
        """Right-aligned complement row: n + 1 - row balls."""
        return range(row, self.n + 1)


def make_ball(fill: str, edge: str, radius: float) -> Circle:
    """A flat, matte ball: solid fill plus a faint darker rim."""
    return Circle(
        radius=radius,
        fill_color=fill,
        fill_opacity=1.0,
        stroke_color=edge,
        stroke_width=1.6,
        stroke_opacity=0.45,
    )


class SumOneToN(VoiceoverScene):
    def construct(self):
        self.camera.background_color = BG
        self.set_speech_service(EdgeTTSService(), create_subcaption=False)

        layout = StaircaseLayout(N, TOP_ROWS, GRID_WIDTH, Y_CENTER)
        cell = layout.cell
        radius = 0.40 * cell
        label_size = max(22, round(34 * cell))
        caption_size = max(20, round(30 * cell))
        label_right = layout.left - 0.25 * cell

        def make_row(row: int, cols: range, fill: str, edge: str) -> VGroup:
            return VGroup(
                *[
                    make_ball(fill, edge, radius).move_to(
                        layout.center(row, col)
                    )
                    for col in cols
                ]
            )

        def make_label(
            text: str, y: float, italic: bool = False
        ) -> Text | MarkupText:
            if italic:
                label = MarkupText(
                    f"<i>{text}</i>",
                    font=MATH_FONT,
                    font_size=label_size,
                    color=INK,
                )
            else:
                label = Text(
                    text,
                    font=MATH_FONT,
                    font_size=label_size,
                    color=INK,
                )
            label.set_x(label_right - label.width / 2)
            label.set_y(y)
            return label

        # ============================================== 1. visible staircase
        rows: dict[int, VGroup] = {}
        labels: dict[int, Text | MarkupText] = {}
        top_group = VGroup()
        drop = 0.35 * cell

        with self.voiceover(text=NARRATION["build"]) as tracker:
            logger.info(
                f"[voice] build @ {tracker.start_t:.2f}s, "
                f"{tracker.duration:.2f}s"
            )
            self.wait(TIMING["lead_in"])

            for row_index in TOP_ROWS:
                row = make_row(
                    row_index, layout.a_cols(row_index), TEAL, TEAL_EDGE
                )
                label = make_label(str(row_index), layout.row_y(row_index))

                # start a little lower; the layout opens up when the gap arrives
                row.shift(DOWN * drop)
                label.shift(DOWN * drop)

                rows[row_index] = row
                labels[row_index] = label
                top_group.add(row, label)

                self.play(
                    AnimationGroup(
                        LaggedStart(
                            *[GrowFromCenter(ball) for ball in row],
                            lag_ratio=0.18,
                        ),
                        FadeIn(label, shift=RIGHT * 0.10),
                        lag_ratio=0.15,
                    ),
                    run_time=TIMING["build_row"],
                    rate_func=smooth,
                )
        self.wait(PAUSE)

        # smooth layout transition: lift the shown rows, open the gap
        ellipsis = Text(
            "⋮",
            font=CN_FONT,
            font_size=label_size,
            color=MUTED,
        )
        ellipsis.set_x(label_right - ellipsis.width / 2)
        ellipsis.set_y(layout.gap_y)

        with self.voiceover(text=NARRATION["compress"]) as tracker:
            logger.info(
                f"[voice] compress @ {tracker.start_t:.2f}s, "
                f"{tracker.duration:.2f}s"
            )
            self.play(
                top_group.animate.shift(UP * drop),
                FadeIn(ellipsis, scale=0.9),
                run_time=TIMING["layout_shift"],
                rate_func=smooth,
            )
        self.wait(PAUSE)

        # last row: concrete count first, then the symbolic label
        row_n = make_row(N, layout.a_cols(N), TEAL, TEAL_EDGE)
        label_n_concrete = make_label(str(N), layout.row_y(N))

        with self.voiceover(text=NARRATION["last_row"]) as tracker:
            logger.info(
                f"[voice] last_row @ {tracker.start_t:.2f}s, "
                f"{tracker.duration:.2f}s"
            )
            self.play(
                AnimationGroup(
                    LaggedStart(
                        *[GrowFromCenter(ball) for ball in row_n],
                        lag_ratio=0.10,
                    ),
                    FadeIn(label_n_concrete, shift=UP * 0.15),
                    lag_ratio=0.15,
                ),
                run_time=TIMING["last_row"],
                rate_func=smooth,
            )

            label_n = make_label("n", layout.row_y(N), italic=True)
            self.play(
                FadeTransform(
                    label_n_concrete, label_n, run_time=TIMING["label_morph"]
                )
            )

            rows[N] = row_n
            self.wait(TIMING["read_stair"])
        self.wait(PAUSE)

        # ============================================== 2. copy + rotate
        stair_balls = VGroup(rows[1], rows[2], rows[3], rows[N])
        copy = stair_balls.copy()
        copy.set_fill(TERRA, opacity=1.0)
        copy.set_stroke(TERRA_EDGE, width=1.6, opacity=0.45)

        lift = 0.8 * cell
        copy.shift(UP * lift)

        with self.voiceover(text=NARRATION["copy"]) as tracker:
            logger.info(
                f"[voice] copy @ {tracker.start_t:.2f}s, "
                f"{tracker.duration:.2f}s"
            )
            self.play(FadeIn(copy, run_time=TIMING["copy_fade"]))
            self.wait(0.15)

            self.play(
                Rotate(copy, PI, about_point=copy.get_center()),
                run_time=TIMING["rotate"],
                rate_func=smooth,
            )
            self.wait(0.10)
        self.wait(PAUSE)

        with self.voiceover(text=NARRATION["complement"]) as tracker:
            logger.info(
                f"[voice] complement @ {tracker.start_t:.2f}s, "
                f"{tracker.duration:.2f}s"
            )
            # rotate about its own centre, then slide one column right and down
            self.play(
                copy.animate.shift(RIGHT * cell + DOWN * lift),
                run_time=TIMING["slide"],
                rate_func=smooth,
            )
            self.wait(0.15)

            # The rotated block already matches the complement at rows 1, 3
            # and n. Row 2 of the block has fallen into the ellipsis band;
            # fade it away. The complement of row 2 (and the left part of
            # row 3) is made of hidden rows, so those balls are revealed at
            # their final positions.
            new_row_2 = make_row(2, layout.b_cols(2), TERRA, TERRA_EDGE)
            extra_row_3_cols = range(3, layout.n - 2)
            new_row_3 = make_row(3, extra_row_3_cols, TERRA, TERRA_EDGE)

            revealed = [
                FadeIn(ball, scale=0.8) for ball in new_row_2
            ] + [
                FadeIn(ball, scale=0.8) for ball in new_row_3
            ]

            self.play(
                FadeOut(copy[1], scale=0.9),
                LaggedStart(*revealed, lag_ratio=0.08),
                run_time=TIMING["settle"],
                rate_func=smooth,
            )
            self.wait(TIMING["read_rect"])
        self.wait(PAUSE)

        # ============================================== 3. rectangle + labels
        rect = Rectangle(
            width=layout.width,
            height=layout.height,
            stroke_color=INK,
            stroke_width=3.0,
            stroke_opacity=0.8,
            fill_opacity=0.0,
        ).move_to(np.array([0.0, layout.y_center, 0.0]))

        with self.voiceover(text=NARRATION["rectangle"]) as tracker:
            logger.info(
                f"[voice] rectangle @ {tracker.start_t:.2f}s, "
                f"{tracker.duration:.2f}s"
            )
            self.play(
                Create(rect, run_time=TIMING["rect_draw"], rate_func=smooth)
            )
            self.wait(0.3)

            row_arrow_x = layout.right + 0.45 * cell
            row_arrow = DoubleArrow(
                start=np.array([row_arrow_x, layout.bottom, 0.0]),
                end=np.array([row_arrow_x, layout.top, 0.0]),
                buff=0.0,
                stroke_width=2.2,
                color=MUTED,
                tip_length=0.16,
            )
            col_arrow_y = layout.bottom - 0.45 * cell
            col_arrow = DoubleArrow(
                start=np.array([layout.left, col_arrow_y, 0.0]),
                end=np.array([layout.right, col_arrow_y, 0.0]),
                buff=0.0,
                stroke_width=2.2,
                color=MUTED,
                tip_length=0.16,
            )

            row_label = Text(
                "n 行", font=CN_FONT, font_size=caption_size, color=INK
            )
            row_label.rotate(PI / 2).next_to(
                row_arrow, RIGHT, buff=0.30 * cell
            )

            col_label = Text(
                "n + 1 列", font=CN_FONT, font_size=caption_size, color=INK
            )
            col_label.next_to(col_arrow, DOWN, buff=0.24 * cell)

            self.play(
                AnimationGroup(
                    Create(row_arrow),
                    Create(col_arrow),
                    FadeIn(row_label, shift=LEFT * 0.12),
                    FadeIn(col_label, shift=UP * 0.12),
                    lag_ratio=0.15,
                ),
                run_time=TIMING["dimensions"],
                rate_func=smooth,
            )
            self.wait(TIMING["read_rect"])
        self.wait(PAUSE)

        # ============================================== 4. formula
        formula = MarkupText(
            "1 + 2 + ··· + <i>n</i> = <i>n</i>(<i>n</i> + 1)/2",
            font=MATH_FONT,
            font_size=58,
            color=INK,
        )
        formula.move_to(np.array([0.0, -3.4, 0.0]))
        if formula.width > 7.1:
            formula.scale_to_fit_width(7.1)

        with self.voiceover(text=NARRATION["formula"]) as tracker:
            logger.info(
                f"[voice] formula @ {tracker.start_t:.2f}s, "
                f"{tracker.duration:.2f}s"
            )
            self.play(
                FadeIn(
                    formula,
                    shift=UP * 0.25,
                    run_time=TIMING["formula_in"],
                    rate_func=smooth,
                )
            )
        self.wait(TIMING["final_hold"])
