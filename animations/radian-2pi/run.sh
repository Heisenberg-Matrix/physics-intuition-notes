#!/usr/bin/env bash
# 一键渲染：./run.sh preview 出低清预览，./run.sh 出 1080×1920 成片；两者都带中文配音。
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

FF="$(command -v ffmpeg || true)"
if [ -z "$FF" ] && [ -x "../../.venv/Scripts/ffmpeg.exe" ]; then
  FF="../../.venv/Scripts/ffmpeg.exe"
fi
if [ -z "$FF" ]; then
  echo "找不到 ffmpeg：请安装 FFmpeg 或放到 .venv/Scripts/ffmpeg.exe" >&2
  exit 1
fi

# 配音单独缓存；文案或语速不变时不会重新联网合成。
"$PY" narration.py

mux() {
  # $1 无声视频，$2 输出文件
  "$FF" -y -v error -i "$1" -i media/voice/voiceover.wav \
    -map 0:v:0 -map 1:a:0 -c:v copy \
    -af loudnorm=I=-16:TP=-1.5:LRA=11 \
    -c:a aac -b:a 128k -ar 48000 -ac 1 \
    -movflags +faststart -shortest "$2"
}

if [ "${1:-}" = "preview" ]; then
  PREVIEW=1 "$PY" -m manim -ql --disable_caching scene.py RadianScene
  mux media/videos/scene/960p30/RadianScene.mp4 media/preview.mp4
  echo "[preview] media/preview.mp4"
else
  "$PY" -m manim -qh --disable_caching scene.py RadianScene
  mux media/videos/scene/1920p30/RadianScene.mp4 radian-2pi.mp4
  echo "[video] radian-2pi.mp4"

  "$FF" -y -v error -ss 112.0 -i radian-2pi.mp4 -frames:v 1 -q:v 3 poster.jpg
  echo "[poster] poster.jpg"
fi
