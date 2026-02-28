from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from .models import NoteCreate, NoteRead
from .repository import InMemoryNoteRepository, MongoNoteRepository, NoteRepository


def _build_default_repo() -> tuple[NoteRepository, MongoClient | None]:
    mongo_url = os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017")
    db_name = os.getenv("MONGO_DB_NAME", "postloop_notes")

    try:
        client = MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        collection = client[db_name]["notes"]
        return MongoNoteRepository(collection), client
    except PyMongoError:
        # Keep local/unit-test startup resilient when Mongo is not available yet.
        return InMemoryNoteRepository(), None


def create_app(repo: NoteRepository | None = None) -> FastAPI:
    if repo is None:
        note_repo, mongo_client = _build_default_repo()
    else:
        note_repo = repo
        mongo_client = None

    @asynccontextmanager
    async def _lifespan(_: FastAPI):
        yield
        if mongo_client is not None:
            mongo_client.close()

    app = FastAPI(title="Postloop Notes API", version="0.1.0", lifespan=_lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/notes", response_model=list[NoteRead])
    def list_notes() -> list[NoteRead]:
        notes = note_repo.list_notes()
        return [
            NoteRead(id=n.id, title=n.title, done=n.done, created_at=n.created_at) for n in notes
        ]

    @app.post("/api/notes", response_model=NoteRead, status_code=201)
    def create_note(payload: NoteCreate) -> NoteRead:
        note = note_repo.create_note(payload.title.strip())
        return NoteRead(id=note.id, title=note.title, done=note.done, created_at=note.created_at)

    @app.patch("/api/notes/{note_id}/toggle", response_model=NoteRead)
    def toggle_note(note_id: str) -> NoteRead:
        note = note_repo.toggle_note(note_id)
        if note is None:
            raise HTTPException(status_code=404, detail="Note not found")
        return NoteRead(id=note.id, title=note.title, done=note.done, created_at=note.created_at)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
