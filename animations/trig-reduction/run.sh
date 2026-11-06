#!/usr/bin/env bash
# 一键渲染：./run.sh preview 出低清预览，./run.sh 出 1080×1920 成片。
set -e
cd "$(dirname "$0")"

PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  if [ -x "../../.venv/Scripts/python.exe" ]; then
    PY="../../.venv/Scripts/python.exe"
  else
    PY="python"
  fi
fi

if [ "${1:-}" = "preview" ]; then
  PREVIEW=1 "$PY" -m manim -ql --disable_caching scene.py TrigReductionScene
  cp media/videos/scene/960p30/TrigReductionScene.mp4 media/preview.mp4
  echo "[preview] media/preview.mp4"
else
  "$PY" -m manim -qh --disable_caching scene.py TrigReductionScene
  cp media/videos/scene/1920p30/TrigReductionScene.mp4 trig-reduction.mp4
  echo "[video] trig-reduction.mp4"

  FF="$(command -v ffmpeg || true)"
  if [ -z "$FF" ] && [ -x "../../.venv/Scripts/ffmpeg.exe" ]; then
    FF="../../.venv/Scripts/ffmpeg.exe"
  fi
  if [ -n "$FF" ]; then
    "$FF" -y -ss 53 -i trig-reduction.mp4 -frames:v 1 -q:v 3 poster.jpg
    echo "[poster] poster.jpg"
  fi
fi
