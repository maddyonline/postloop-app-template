#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE_FILE="$ROOT_DIR/.data/mongo-runtime-mode"
LOCAL_PID="$ROOT_DIR/.data/mongo-local/mongod.pid"

mode=""
if [[ -f "$MODE_FILE" ]]; then
  mode="$(cat "$MODE_FILE")"
fi

if [[ "$mode" == "docker" ]] && command -v docker >/dev/null 2>&1; then
  echo "[mongo] Stopping docker compose MongoDB..."
  (cd "$ROOT_DIR" && docker compose stop mongodb || true)
fi

if [[ "$mode" == "local" ]] && [[ -f "$LOCAL_PID" ]]; then
  pid="$(cat "$LOCAL_PID")"
  if ps -p "$pid" >/dev/null 2>&1; then
    echo "[mongo] Stopping local mongod process ($pid)..."
    kill "$pid" || true
  fi
fi

rm -f "$MODE_FILE"
echo "[mongo] Stop complete"
