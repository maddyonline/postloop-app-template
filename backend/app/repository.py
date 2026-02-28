from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from pymongo.collection import Collection


@dataclass
class NoteRecord:
    id: str
    title: str
    done: bool
    created_at: datetime


class NoteRepository(Protocol):
    def list_notes(self) -> list[NoteRecord]: ...

    def create_note(self, title: str) -> NoteRecord: ...

    def toggle_note(self, note_id: str) -> NoteRecord | None: ...


class InMemoryNoteRepository(NoteRepository):
    def __init__(self) -> None:
        self._notes: dict[str, NoteRecord] = {}

    def list_notes(self) -> list[NoteRecord]:
        return sorted(self._notes.values(), key=lambda note: note.created_at, reverse=True)

    def create_note(self, title: str) -> NoteRecord:
        record = NoteRecord(
            id=str(uuid4()),
            title=title,
            done=False,
            created_at=datetime.now(timezone.utc),
        )
        self._notes[record.id] = record
        return record

    def toggle_note(self, note_id: str) -> NoteRecord | None:
        record = self._notes.get(note_id)
        if record is None:
            return None
        updated = NoteRecord(
            id=record.id,
            title=record.title,
            done=not record.done,
            created_at=record.created_at,
        )
        self._notes[note_id] = updated
        return updated


class MongoNoteRepository(NoteRepository):
    def __init__(self, collection: Collection) -> None:
        self.collection = collection
        self.collection.create_index([("created_at", -1)])

    def list_notes(self) -> list[NoteRecord]:
        notes: list[NoteRecord] = []
        for doc in self.collection.find().sort("created_at", -1):
            notes.append(
                NoteRecord(
                    id=doc["_id"],
                    title=doc["title"],
                    done=bool(doc.get("done", False)),
                    created_at=doc["created_at"],
                )
            )
        return notes

    def create_note(self, title: str) -> NoteRecord:
        note_id = str(uuid4())
        created_at = datetime.now(timezone.utc)
        self.collection.insert_one(
            {
                "_id": note_id,
                "title": title,
                "done": False,
                "created_at": created_at,
            }
        )
        return NoteRecord(id=note_id, title=title, done=False, created_at=created_at)

    def toggle_note(self, note_id: str) -> NoteRecord | None:
        doc = self.collection.find_one({"_id": note_id})
        if doc is None:
            return None

        updated_done = not bool(doc.get("done", False))
        self.collection.update_one({"_id": note_id}, {"$set": {"done": updated_done}})

        updated = self.collection.find_one({"_id": note_id})
        assert updated is not None
        return NoteRecord(
            id=updated["_id"],
            title=updated["title"],
            done=bool(updated.get("done", False)),
            created_at=updated["created_at"],
        )
