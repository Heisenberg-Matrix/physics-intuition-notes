#!/usr/bin/env bash
# 一键渲染：./run.sh preview 出低清预览，./run.sh 出 1080×1920 成片；
# 两者都带中文配音和很轻的合成底噪音乐。
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

# 配音与音乐分别缓存；文案、语速不变时不会重新合成。
"$PY" narration.py
"$PY" music.py

mux() {
  # $1 无声视频，$2 输出文件
  "$FF" -y -v error -i "$1" -i media/voice/voiceover.wav -i media/music.wav \
    -filter_complex \
    "[1:a]volume=1.0[voice];[2:a]volume=0.45[music];[voice][music]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[a]" \
    -map 0:v:0 -map "[a]" -c:v copy \
    -c:a aac -b:a 128k -ar 48000 -ac 1 \
    -movflags +faststart -shortest "$2"
}

if [ "${1:-}" = "preview" ]; then
  PREVIEW=1 "$PY" -m manim -ql --disable_caching scene.py OrbitScene
  mux media/videos/scene/960p30/OrbitScene.mp4 media/preview.mp4
  echo "[preview] media/preview.mp4"
else
  "$PY" -m manim -qh --disable_caching scene.py OrbitScene
  mux media/videos/scene/1920p30/OrbitScene.mp4 orbit-speed-period.mp4
  echo "[video] orbit-speed-period.mp4"

  "$FF" -y -v error -ss 90.8 -i orbit-speed-period.mp4 -frames:v 1 -q:v 3 poster.jpg
  echo "[poster] poster.jpg"
fi
