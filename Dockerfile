# syntax=docker/dockerfile:1.7

FROM node:20-bookworm-slim AS frontend_builder
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FRONTEND_DIST_DIR=/app/frontend_dist

WORKDIR /app
COPY backend/ /app/backend/
RUN pip install --no-cache-dir -e /app/backend
COPY --from=frontend_builder /app/frontend/dist /app/frontend_dist

EXPOSE 8080
CMD ["sh", "-lc", "uvicorn app.preview:app --app-dir /app/backend --host 0.0.0.0 --port ${PORT:-8080}"]
