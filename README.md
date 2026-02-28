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
