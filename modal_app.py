from __future__ import annotations

import sys
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parent
LOCAL_BACKEND_DIR = ROOT / "backend"
LOCAL_FRONTEND_DIST_DIR = ROOT / "frontend" / "dist"
CONTAINER_BACKEND_DIR = Path("/root/app/backend")
CONTAINER_FRONTEND_DIST_DIR = Path("/root/app/frontend_dist")

# Modal imports user code again inside the remote container. In that context the
# project root is not available at /root/<repo>, but the copied dirs exist under
# /root/app. Resolve source dirs from whichever location exists.
BACKEND_DIR = (
    LOCAL_BACKEND_DIR if LOCAL_BACKEND_DIR.exists() else CONTAINER_BACKEND_DIR
)
FRONTEND_DIST_DIR = (
    LOCAL_FRONTEND_DIST_DIR
    if LOCAL_FRONTEND_DIST_DIR.exists()
    else CONTAINER_FRONTEND_DIST_DIR
)

if not FRONTEND_DIST_DIR.exists():
    raise RuntimeError(
        "Missing frontend/dist. Build it before deploy: "
        "`cd frontend && npm ci && VITE_API_BASE_URL= npm run build`"
    )
if not BACKEND_DIR.exists():
    raise RuntimeError("Missing backend directory for Modal app packaging.")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("fastapi>=0.115.0", "pydantic>=2.10.0", "pymongo>=4.11.0")
    .add_local_dir(str(BACKEND_DIR), remote_path="/root/app/backend")
    .add_local_dir(str(FRONTEND_DIST_DIR), remote_path="/root/app/frontend_dist")
)

app = modal.App("postloop-notes-preview")


@app.function(image=image, timeout=900)
@modal.asgi_app()
def web():
    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    sys.path.insert(0, "/root/app/backend")
    from app.main import create_app  # pylint: disable=import-error

    app = create_app()
    dist_dir = Path("/root/app/frontend_dist")
    assets_dir = dist_dir / "assets"

    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(dist_dir / "index.html")

    @app.get("/{path_name:path}", include_in_schema=False)
    def spa(path_name: str):
        if path_name.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")

        candidate = dist_dir / path_name
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(dist_dir / "index.html")

    return app
