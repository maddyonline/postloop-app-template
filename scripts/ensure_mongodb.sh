#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE_FILE="$ROOT_DIR/.data/mongo-runtime-mode"
LOCAL_DATA_DIR="$ROOT_DIR/.data/mongo-local"

mkdir -p "$ROOT_DIR/.data"

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  echo "[mongo] Docker detected; starting MongoDB container..."
  (cd "$ROOT_DIR" && docker compose up -d mongodb)
  echo "docker" > "$MODE_FILE"
  echo "[mongo] MongoDB is running via docker compose"
  exit 0
fi

if command -v mongod >/dev/null 2>&1; then
  if lsof -iTCP:27017 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "[mongo] MongoDB already listening on port 27017"
    echo "local" > "$MODE_FILE"
    exit 0
  fi

  mkdir -p "$LOCAL_DATA_DIR"
  LOG_PATH="$LOCAL_DATA_DIR/mongod.log"
  PID_PATH="$LOCAL_DATA_DIR/mongod.pid"

  echo "[mongo] Docker unavailable; starting local mongod daemon..."
  mongod \
    --dbpath "$LOCAL_DATA_DIR" \
    --bind_ip 127.0.0.1 \
    --port 27017 \
    --fork \
    --logpath "$LOG_PATH" \
    --pidfilepath "$PID_PATH"

  echo "local" > "$MODE_FILE"
  echo "[mongo] MongoDB started locally (pid file: $PID_PATH)"
  exit 0
fi

echo "[mongo] Could not start MongoDB."
echo "[mongo] Install Docker (with running daemon) or install mongod locally."
exit 1
