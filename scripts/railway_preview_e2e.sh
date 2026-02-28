#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="${RAILWAY_PROJECT_NAME:-postloop-preview-$(date +%s)}"
WEB_SERVICE_NAME="${RAILWAY_WEB_SERVICE_NAME:-web}"
RUN_PLAYWRIGHT="${RUN_PLAYWRIGHT:-1}"

echo "[railway] using root: $ROOT_DIR"
cd "$ROOT_DIR"

if ! command -v railway >/dev/null 2>&1; then
  echo "[railway] railway CLI not found. Install: https://docs.railway.com/reference/cli-api"
  exit 1
fi

if ! railway whoami >/dev/null 2>&1; then
  echo "[railway] not logged in. Run: railway login"
  exit 1
fi

if ! railway status --json >/dev/null 2>&1; then
  echo "[railway] no linked project, creating one: $PROJECT_NAME"
  railway init -n "$PROJECT_NAME"
fi

echo "[railway] ensuring service exists: $WEB_SERVICE_NAME"
railway add --service "$WEB_SERVICE_NAME" >/dev/null 2>&1 || true

echo "[railway] deploying service: $WEB_SERVICE_NAME"
railway up -s "$WEB_SERVICE_NAME" -c

echo "[railway] resolving preview URL"
DOMAIN_OUTPUT="$(railway domain -s "$WEB_SERVICE_NAME" --json 2>&1 || railway domain -s "$WEB_SERVICE_NAME" 2>&1)"

PREVIEW_URL="$(
python3 - "$DOMAIN_OUTPUT" <<'PY'
import json
import re
import sys

raw = sys.argv[1].strip()

try:
    payload = json.loads(raw)
except json.JSONDecodeError:
    payload = None

if payload is not None:
    items = payload if isinstance(payload, list) else [payload]
    for item in items:
        domain = item.get("domain") or item.get("hostname")
        if domain:
            domain = domain.replace("https://", "").replace("http://", "")
            print(f"https://{domain}")
            raise SystemExit(0)

match = re.search(r"https?://[A-Za-z0-9.-]+", raw)
if match:
    print(match.group(0))
    raise SystemExit(0)

match = re.search(r"[A-Za-z0-9.-]+\.up\.railway\.app", raw)
if match:
    print(f"https://{match.group(0)}")
    raise SystemExit(0)

print("")
PY
)"

if [[ -z "$PREVIEW_URL" ]]; then
  echo "[railway] failed to resolve preview URL"
  exit 1
fi

echo "[railway] preview url: $PREVIEW_URL"

echo "[railway] waiting for app readiness"
for _ in {1..60}; do
  if curl -fsS "$PREVIEW_URL/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "[railway] health check response:"
curl -fsS "$PREVIEW_URL/healthz"
echo

if [[ "$RUN_PLAYWRIGHT" == "1" ]]; then
  echo "[railway] running Playwright e2e against preview"
  cd "$ROOT_DIR/frontend"
  npm ci
  npx playwright install --with-deps chromium
  PLAYWRIGHT_BASE_URL="$PREVIEW_URL" npm run test:e2e
fi

echo "[railway] done"
