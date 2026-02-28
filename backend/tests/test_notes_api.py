from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.repository import InMemoryNoteRepository


def _client() -> TestClient:
    app = create_app(repo=InMemoryNoteRepository())
    return TestClient(app)


def test_create_list_and_toggle_note() -> None:
    client = _client()

    create_resp = client.post("/api/notes", json={"title": "Book grooming slot"})
    assert create_resp.status_code == 201
    note = create_resp.json()
    assert note["title"] == "Book grooming slot"
    assert note["done"] is False

    list_resp = client.get("/api/notes")
    assert list_resp.status_code == 200
    listed = list_resp.json()
    assert len(listed) == 1
    assert listed[0]["id"] == note["id"]

    toggle_resp = client.patch(f"/api/notes/{note['id']}/toggle")
    assert toggle_resp.status_code == 200
    toggled = toggle_resp.json()
    assert toggled["done"] is True


def test_toggle_unknown_note_returns_404() -> None:
    client = _client()

    toggle_resp = client.patch("/api/notes/does-not-exist/toggle")
    assert toggle_resp.status_code == 404
