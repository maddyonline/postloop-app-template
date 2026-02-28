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
python3 -m pip install -e .[dev]
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
python3 -m pip install -e .[dev]
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

## Railway Preview (No Agents)

Use this when you want to validate preview deployments end-to-end manually first.

1. Install Railway CLI and log in:

```bash
railway login
```

2. Run preview deploy + checks:

```bash
./scripts/railway_preview_e2e.sh
```

What this script does:

- Creates a Railway project if the repo is not linked yet.
- Deploys the `web` service from this repo using the root `Dockerfile`.
- Creates or resolves a Railway-provided domain.
- Verifies `/healthz`.
- Runs Playwright E2E against the deployed URL (`RUN_PLAYWRIGHT=1` by default).

Useful overrides:

- `RUN_PLAYWRIGHT=0 ./scripts/railway_preview_e2e.sh` to skip remote E2E.
- `RAILWAY_PROJECT_NAME=your-name ./scripts/railway_preview_e2e.sh` to control project name on first run.
- `RAILWAY_WEB_SERVICE_NAME=web ./scripts/railway_preview_e2e.sh` to target a specific service name.

Optional: wire a Railway Mongo service into the preview app:

```bash
# Add a Mongo service in the linked project (once)
railway add -d mongo

# If your service name is not "MongoDB", replace it in the reference below
railway variables -s web \
  --set 'MONGO_URL=${{MongoDB.MONGO_URL}}' \
  --set 'MONGO_DB_NAME=postloop_notes'
```

## Railway Preview Deployments

This template includes two Railway preview workflows:

- `.github/workflows/preview-railway.yml`
- `.github/workflows/preview-railway-sweeper.yml`

Behavior:

1. On PR `opened/synchronize/reopened`, preview workflow ensures environment `preview-pr-<number>` exists, deploys the app, resolves preview URL, runs Playwright smoke test, and updates a sticky PR comment.
2. On PR `closed`, preview workflow deletes the matching Railway environment.
3. Sweeper workflow runs every 30 minutes and deletes preview environments whose latest deployment is older than `PREVIEW_TTL_HOURS` (default `4`).

Required repository secret:

- `RAILWAY_API_TOKEN`
  - Must be a Railway API token from dashboard token settings (not CLI login/session state).

Required repository variables:

- `RAILWAY_PROJECT_ID`
- `RAILWAY_WEB_SERVICE`

Optional repository variables:

- `RAILWAY_MONGO_SERVICE` (reserved for explicit DB cleanup automation)
- `PREVIEW_TTL_HOURS` (default `4`)

Remote E2E can also be run manually with:

```bash
cd frontend
PLAYWRIGHT_BASE_URL="https://<your-preview-url>" npm run test:e2e
```
