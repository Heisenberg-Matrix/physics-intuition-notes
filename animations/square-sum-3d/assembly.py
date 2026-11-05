"""三个平方阶梯体的刚体拼装：建模、求解与离散校验。

几何约定
--------
* 单位立方体占据整数网格 ``(x, y, z)``，``z`` 向上。
* n = 4 时，阶梯体 S 自下而上四层分别有 4x4、3x3、2x2、1x1 个小方块，
  共 30 块；层与层在一个角上对齐（不是居中）。
* 三个副本只允许整体旋转（立方体的 24 个真旋转）与平移，不允许拆散内部方块。
* 目标区域 T 是 4x5x4 的长方体（80 块）加上顶部 1+2+3+4=10 块阶梯。

求解思路
--------
枚举所有能把 S 放进 T 的 (旋转, 平移)，再固定 A，穷举 B，检查补集是否
也是某个合法摆放。这样得到的解是精确覆盖，不是近似或视觉拼接。
在 n=4 时恰好有两组（B、C 互换）解：B 与 C 分别是 A 绕体对角线
(1, 1, -1) 旋转 +120° 与 -120° 后的刚体。

随后用 BFS 在整数平移网格上寻找从场外滑入的路径，并对每一步做
“与已放置积木无重叠”的校验，保证动画里的滑入过程本身也不穿模。
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import product
from typing import Iterable

Cube = tuple[int, int, int]
Matrix = tuple[tuple[int, int, int], ...]


# --------------------------------------------------------------------------
# 1. 几何生成
# --------------------------------------------------------------------------
def generate_staircase(n: int = 4) -> frozenset[Cube]:
    """生成 n 层平方阶梯体：底层 n×n，向上依次 (n-1)×(n-1) … 1×1。"""
    return frozenset(
        (x, y, z)
        for z in range(n)
        for x in range(n - z)
        for y in range(n - z)
    )


def target_region(n: int = 4) -> frozenset[Cube]:
    """目标区域：n×(n+1)×n 长方体 + 顶部 1+2+…+n 的阶梯。"""
    base = {
        (x, y, z)
        for x in range(n)
        for y in range(n + 1)
        for z in range(n)
    }
    top = {(x, y, n) for x in range(n) for y in range(x + 1)}
    return frozenset(base | top)


def base_box(n: int = 4) -> frozenset[Cube]:
    return frozenset(
        (x, y, z) for x in range(n) for y in range(n + 1) for z in range(n)
    )


def top_region(n: int = 4) -> frozenset[Cube]:
    return frozenset((x, y, n) for x in range(n) for y in range(x + 1))


# --------------------------------------------------------------------------
# 2. 旋转与摆放
# --------------------------------------------------------------------------
def cube_rotations() -> list[Matrix]:
    """立方体的 24 个真旋转（行列式为 +1 的带符号置换矩阵）。"""
    rotations: list[Matrix] = []
    for perm in ((0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)):
        for signs in product((1, -1), repeat=3):
            m = [[0, 0, 0] for _ in range(3)]
            for i, p in enumerate(perm):
                m[i][p] = signs[i]
            det = (
                m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
                - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
            )
            if det == 1:
                rotations.append(tuple(tuple(row) for row in m))
    return rotations


def apply_matrix(m: Iterable[Iterable[int]], p: Cube) -> Cube:
    rows = tuple(tuple(row) for row in m)
    return tuple(sum(rows[i][j] * p[j] for j in range(3)) for i in range(3))


def transform(
    cells: Iterable[Cube], rotation: Matrix, translation: Cube
) -> frozenset[Cube]:
    tx, ty, tz = translation
    return frozenset(
        (x + tx, y + ty, z + tz)
        for x, y, z in (apply_matrix(rotation, p) for p in cells)
    )


@dataclass(frozen=True)
class Placement:
    name: str
    cells: frozenset[Cube]
    rotation: Matrix
    translation: Cube

    def __len__(self) -> int:
        return len(self.cells)


def _bounds(cells: Iterable[Cube]) -> tuple[range, range, range]:
    cells = tuple(cells)
    return (
        range(min(p[0] for p in cells), max(p[0] for p in cells) + 1),
        range(min(p[1] for p in cells), max(p[1] for p in cells) + 1),
        range(min(p[2] for p in cells), max(p[2] for p in cells) + 1),
    )


def placement_candidates(
    shape: frozenset[Cube], target: frozenset[Cube]
) -> dict[frozenset[Cube], tuple[Matrix, Cube]]:
    """所有把 shape 放进 target 的刚体摆放。"""
    candidates: dict[frozenset[Cube], tuple[Matrix, Cube]] = {}
    for rotation in cube_rotations():
        rotated = tuple(apply_matrix(rotation, p) for p in shape)
        xs, ys, zs = _bounds(rotated)
        xr, yr, zr = _bounds(target)
        for tx in range(xr.start - xs.start, xr.stop - xs.stop + 1):
            for ty in range(yr.start - ys.start, yr.stop - ys.stop + 1):
                for tz in range(zr.start - zs.start, zr.stop - zs.stop + 1):
                    cells = frozenset(
                        (x + tx, y + ty, z + tz) for x, y, z in rotated
                    )
                    if cells <= target:
                        candidates[cells] = (rotation, (tx, ty, tz))
    return candidates


def solve_assembly(n: int = 4) -> dict[str, Placement]:
    """精确覆盖求解；返回 A、B、C 三个刚体的旋转与平移。"""
    stair = generate_staircase(n)
    target = target_region(n)
    candidates = placement_candidates(stair, target)
    if stair not in candidates:
        raise RuntimeError("阶梯体无法放入目标区域")

    for b_cells, (b_rot, b_t) in candidates.items():
        if b_cells & stair:
            continue
        c_cells = target - stair - b_cells
        if c_cells in candidates:
            c_rot, c_t = candidates[c_cells]
            return {
                "A": Placement("A", stair, _identity(), (0, 0, 0)),
                "B": Placement("B", b_cells, b_rot, b_t),
                "C": Placement("C", c_cells, c_rot, c_t),
            }
    raise RuntimeError("没有找到三块阶梯体的精确刚体拼装")


def _identity() -> Matrix:
    return ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def rotation_axis_angle(rotation: Matrix) -> tuple[tuple[float, float, float], float]:
    """由真旋转矩阵求旋转轴与带符号角度（弧度）；用于把 120° 旋转做成动画。

    ``R - R^T = 2 sinθ [a]_×``，用反对称部分的符号确定 θ 的正负，
    避免 SVD 给出的轴方向不唯一。
    """
    import numpy as np

    r = np.array(rotation, dtype=float)
    trace = float(np.trace(r))
    angle = math_acos_clamped((trace - 1) / 2)
    skew = np.array(
        [r[2, 1] - r[1, 2], r[0, 2] - r[2, 0], r[1, 0] - r[0, 1]]
    )
    _, _, vh = np.linalg.svd(r - np.eye(3))
    axis = vh[-1]
    axis = axis / np.linalg.norm(axis)
    if float(np.dot(skew, axis)) < 0:
        angle = -angle
    return tuple(float(a) for a in axis), float(angle)


def math_acos_clamped(value: float) -> float:
    import math

    return math.acos(max(-1.0, min(1.0, value)))


# --------------------------------------------------------------------------
# 3. 滑入路径
# --------------------------------------------------------------------------
def _inflate(cells: Iterable[Cube]) -> frozenset[Cube]:
    return frozenset(cells)


def insertion_path(
    shape: frozenset[Cube],
    rotation: Matrix,
    target_t: Cube,
    obstacle: frozenset[Cube],
    start_t: Cube,
    bounds: tuple[range, range, range] | None = None,
) -> list[Cube]:
    """在整数平移网格上 BFS，找一条不与 obstacle 重叠的滑入路径。"""
    rotated = frozenset(apply_matrix(rotation, p) for p in shape)
    obstacles = _inflate(obstacle)
    if bounds is None:
        bounds = (range(-12, 13), range(-16, 13), range(-6, 9))
    start_t = tuple(start_t)  # type: ignore[assignment]
    target_t = tuple(target_t)  # type: ignore[assignment]

    def hits(t: Cube) -> bool:
        return bool(transform(rotated, _identity(), t) & obstacles)

    if hits(start_t) or hits(target_t):
        raise RuntimeError(f"起止位置与已放置积木重叠: {start_t} -> {target_t}")

    queue: deque[Cube] = deque([start_t])
    parent: dict[Cube, Cube | None] = {start_t: None}
    while queue:
        current = queue.popleft()
        if current == target_t:
            path: list[Cube] = []
            node: Cube | None = current
            while node is not None:
                path.append(node)
                node = parent[node]
            return path[::-1]
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            nxt = (current[0] + dx, current[1] + dy, current[2] + dz)
            if nxt in parent:
                continue
            if nxt[0] not in bounds[0] or nxt[1] not in bounds[1] or nxt[2] not in bounds[2]:
                continue
            if hits(nxt):
                continue
            parent[nxt] = current
            queue.append(nxt)
    raise RuntimeError(f"找不到滑入路径: {start_t} -> {target_t}")


def solve_insertion_paths(pieces: dict[str, Placement]) -> dict[str, list[Cube]]:
    """B 从正前方绕右侧滑入；C 随后从右侧远处直线滑入（起点在画外）。"""
    b = pieces["B"]
    c = pieces["C"]
    b_start = (b.translation[0], b.translation[1] - 7, b.translation[2])
    c_start = (c.translation[0] + 9, c.translation[1], c.translation[2])
    path_b = insertion_path(
        generate_staircase(), b.rotation, b.translation, pieces["A"].cells, b_start
    )
    path_c = insertion_path(
        generate_staircase(),
        c.rotation,
        c.translation,
        pieces["A"].cells | pieces["B"].cells,
        c_start,
    )
    return {"B": path_b, "C": path_c}


# --------------------------------------------------------------------------
# 4. 校验
# --------------------------------------------------------------------------
def validate_assembly(
    pieces: dict[str, Placement], paths: dict[str, list[Cube]] | None = None, n: int = 4
) -> dict[str, object]:
    stair = generate_staircase(n)
    target = target_region(n)
    names = ("A", "B", "C")
    overlaps = {
        f"{a}&{b}": len(pieces[a].cells & pieces[b].cells)
        for i, a in enumerate(names)
        for b in names[i + 1 :]
    }
    union = frozenset().union(*(pieces[name].cells for name in names))
    missing = target - union
    extra = union - target
    rigid = {
        name: transform(stair, pieces[name].rotation, pieces[name].translation)
        == pieces[name].cells
        for name in names
    }
    top = top_region(n)
    base = base_box(n)
    row_counts = [
        sum(1 for x, y, z in top if x == row) for row in range(n)
    ]

    path_checks: dict[str, bool] = {}
    if paths:
        rotated = {
            name: frozenset(apply_matrix(pieces[name].rotation, p) for p in stair)
            for name in ("B", "C")
        }
        for name, path in paths.items():
            obstacle = pieces["A"].cells
            if name == "C":
                obstacle = obstacle | pieces["B"].cells
            ok = True
            for t in path:
                shifted = {
                    (x + t[0], y + t[1], z + t[2]) for x, y, z in rotated[name]
                }
                if shifted & obstacle:
                    ok = False
                    break
            path_checks[name] = ok and path[-1] == pieces[name].translation

    report: dict[str, object] = {
        "n": n,
        "piece_sizes": {name: len(pieces[name].cells) for name in names},
        "overlap_sizes": overlaps,
        "union_size": len(union),
        "target_size": len(target),
        "missing": len(missing),
        "extra": len(extra),
        "rigid_copy": rigid,
        "union_equals_target": union == target,
        "base_box_size": len(base),
        "top_region_size": len(top),
        "top_row_counts": row_counts,
        "decomposes": union == base | top and not (base & top),
        "equivalent_height": len(union) / (n * (n + 1)),
        "path_checks": path_checks,
    }
    report["ok"] = bool(
        all(v == 30 for v in report["piece_sizes"].values())
        and all(v == 0 for v in overlaps.values())
        and len(union) == 90
        and union == target
        and all(rigid.values())
        and report["decomposes"]
        and all(path_checks.values())
    )
    return report


def main() -> None:
    pieces = solve_assembly()
    paths = solve_insertion_paths(pieces)
    report = validate_assembly(pieces, paths)
    print("== 刚体拼装校验 ==")
    for name, placement in pieces.items():
        print(f"{name}: |cells|={len(placement.cells)}, rotation={placement.rotation}, t={placement.translation}")
        axis, angle = rotation_axis_angle(placement.rotation)
        print(f"   axis={tuple(round(a, 3) for a in axis)}, angle={angle * 180 / 3.141592653589793:.1f}°")
    print(f"B path: {len(paths['B']) - 1} 步, C path: {len(paths['C']) - 1} 步")
    for key, value in report.items():
        print(f"{key}: {value}")
    if not report["ok"]:
        raise SystemExit("几何校验失败：拒绝输出拼装动画")


if __name__ == "__main__":
    main()
