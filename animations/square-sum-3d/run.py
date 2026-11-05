"""一键流程：几何校验 → 配音 → 渲染 → 导出成片。

用法：
    python run.py             # 1080×1920 @60，输出 square-sum-3d.mp4
    python run.py --preview   # 540×960 @30，输出 media/preview.mp4
    python run.py --skip-voice  # 不预先合成配音（渲染时仍会按需合成）

渲染前会清掉 media/videos/：Manim 的分段缓存不记录完整场景状态，
旧版本留下的 partial movie 可能与新画面拼接，造成公式重影。
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent  # 仓库根目录
SCENE = "SquareSumScene"


def run_validation() -> None:
    """数学先于画面：校验不通过就不渲染。"""
    sys.path.insert(0, str(HERE))
    from assembly import solve_assembly, solve_insertion_paths, validate_assembly

    pieces = solve_assembly()
    paths = solve_insertion_paths(pieces)
    report = validate_assembly(pieces, paths)
    print("== 刚体拼装校验 ==")
    for key in (
        "piece_sizes",
        "overlap_sizes",
        "union_size",
        "target_size",
        "missing",
        "extra",
        "rigid_copy",
        "decomposes",
        "equivalent_height",
        "dissection",
        "path_checks",
    ):
        print(f"{key}: {report[key]}")
    if not report["ok"]:
        raise SystemExit("几何校验失败：拒绝渲染")
    print("ok: True")


def render(preview: bool) -> Path:
    env = dict(os.environ)
    if preview:
        env["PREVIEW"] = "1"

    # 清掉可能污染拼接的旧分段缓存。
    shutil.rmtree(HERE / "media" / "videos", ignore_errors=True)

    quality = "-ql" if preview else "-qh"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "manim",
            quality,
            "--disable_caching",
            "scene.py",
            SCENE,
        ],
        cwd=HERE,
        env=env,
        check=True,
    )
    # Manim 按画面高度命名目录：9×16 的竖屏是 960p30 / 1920p60。
    if preview:
        return HERE / "media" / "videos" / "scene" / "960p30" / f"{SCENE}.mp4"
    return HERE / "media" / "videos" / "scene" / "1920p60" / f"{SCENE}.mp4"


def export_final_video(preview: bool = False) -> Path:
    """渲染并把成片复制到稳定路径，返回文件。"""
    rendered = render(preview)
    if not rendered.exists():
        raise SystemExit(f"未找到渲染结果: {rendered}")
    target = HERE / "media" / "preview.mp4" if preview else HERE / "square-sum-3d.mp4"
    shutil.copyfile(rendered, target)
    print(f"[export] {target}")
    return target


def make_poster(video: Path, at: float = 57.0) -> None:
    """取 3S 体积公式完整呈现的 3/4 视角做网页封面，没有 ffmpeg 时跳过。"""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        candidate = ROOT / ".venv" / "Scripts" / "ffmpeg.exe"
        ffmpeg = str(candidate) if candidate.exists() else None
    if ffmpeg is None:
        print("[poster] 未找到 ffmpeg，跳过")
        return
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-ss",
            str(at),
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-q:v",
            "3",
            str(HERE / "poster.jpg"),
        ],
        check=True,
    )
    print("[poster] poster.jpg")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true", help="低清预览")
    parser.add_argument("--skip-voice", action="store_true", help="跳过预合成配音")
    args = parser.parse_args()

    run_validation()
    if not args.skip_voice:
        from narration import generate_voiceover

        generate_voiceover()
    video = export_final_video(preview=args.preview)
    if not args.preview:
        make_poster(video)


if __name__ == "__main__":
    main()
