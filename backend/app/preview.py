from __future__ import annotations

import os
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .main import create_app

app = create_app()
dist_dir = Path(os.getenv("FRONTEND_DIST_DIR", "/app/frontend_dist"))
assets_dir = dist_dir / "assets"

if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    if not dist_dir.exists():
        raise HTTPException(
            status_code=500,
            detail="Missing frontend/dist bundle. Build frontend before serving preview app.",
        )
    return FileResponse(dist_dir / "index.html")


@app.get("/{path_name:path}", include_in_schema=False)
def spa(path_name: str):
    if path_name.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")

    candidate = dist_dir / path_name
    if candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(dist_dir / "index.html")
