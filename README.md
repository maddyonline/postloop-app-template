# postloop-app-template

Starter template for rapidly building app products with:

- `backend/`: Python FastAPI API
- `frontend/`: React + Vite web app
- MongoDB storage (Docker first, local daemon fallback)
- GitHub Actions CI for backend lint/unit tests and frontend Playwright E2E

## Prerequisites

- Python 3.9+
- Node.js 20+
- Docker (recommended) or local `mongod`

## Quick Start

1. Start MongoDB:

```bash
./scripts/ensure_mongodb.sh
```

2. Start backend (Terminal 1):

```bash
cd backend
python3 -m pip install -e '.[dev]'
python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

3. Start frontend (Terminal 2):

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

4. Open `http://127.0.0.1:5173` and use the notes app.

## Local Testing

Backend lint + tests:

```bash
cd backend
python3 -m pip install -e '.[dev]'
ruff check .
pytest
```

Frontend lint + E2E:

```bash
cd frontend
npm install
npm run lint
npx playwright install chromium
npm run test:e2e
```

Note: E2E expects backend at `http://127.0.0.1:8000` and frontend at `http://127.0.0.1:4173` (Playwright webServer mode starts frontend automatically).

## MongoDB Runtime Mode

`./scripts/ensure_mongodb.sh` behavior:

1. If Docker exists and daemon is running: starts `docker compose` MongoDB.
2. Else if `mongod` exists: starts local MongoDB daemon on `127.0.0.1:27017`.
3. Else: exits with instructions.

Stop services:

```bash
./scripts/stop_mongodb.sh
```

## Environment Variables

Backend reads:

- `MONGO_URL` (default `mongodb://127.0.0.1:27017`)
- `MONGO_DB_NAME` (default `postloop_notes`)

Frontend reads:

- `VITE_API_BASE_URL` (default `http://127.0.0.1:8000`)

## GitHub Actions

CI workflow (`.github/workflows/ci.yml`) runs on push/PR/manual dispatch and includes:

- `backend` job: Ruff lint + pytest unit tests
- `frontend-e2e` job: Playwright E2E against running backend + MongoDB service

## Modal Preview Deployments

This template includes `.github/workflows/preview-modal.yml` for per-push PR previews on Modal.

Behavior:

1. On PR `opened/synchronize/reopened`, workflow builds frontend and deploys `modal_app.py` to a commit-scoped app name:
   - `postloop-preview-pr-<number>-<shortsha>`
2. It resolves the preview URL and posts/updates a PR comment with the current URL and commit.
3. It runs Playwright E2E against the deployed preview (`PLAYWRIGHT_BASE_URL=<preview-url>`).
4. On PR `closed`, it stops all matching apps for that PR (`postloop-preview-pr-<number>-*`).

Required repository secrets:

- `MODAL_TOKEN_ID`
- `MODAL_TOKEN_SECRET`

Optional repository variable:

- `MODAL_ENVIRONMENT` (if you use a non-default Modal environment)

Notes:

- `modal_app.py` serves backend APIs and frontend static assets from one Modal endpoint.
- The Modal web function is configured with `min_containers=1` to keep previews warm.
- Frontend bundle must exist at `frontend/dist` before deploy; workflow handles this build step automatically.
- Modal plan endpoint limits apply (for example, free tier caps deployed web endpoints), so stale previews should be cleaned up.
- Preview URLs are unique per push because app names include the commit short SHA.
- UI includes a build badge (`Build: <shortsha> • run <run-id> • <app-name>`) so each push is visibly distinct.
- Remote E2E can also be run manually with:

```bash
cd frontend
PLAYWRIGHT_BASE_URL="https://<your-preview-url>" npm run test:e2e
```

## Manual Modal Cleanup

Run this locally when you want to proactively clean old preview apps:

```bash
# dry run: show what would be stopped
python3 scripts/cleanup_modal_previews.py --prefix postloop-preview-pr-

# stop everything for one PR except the newest app
python3 scripts/cleanup_modal_previews.py --pr-number 123 --keep-latest 1 --apply

# stop all preview apps older than 4 hours
python3 scripts/cleanup_modal_previews.py --prefix postloop-preview- --older-than-hours 4 --apply
```
