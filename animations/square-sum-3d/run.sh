#!/usr/bin/env bash
# 一键渲染：几何校验 → 配音 → 1080×1920 成片。
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

exec "$PY" run.py "$@"
