import { FormEvent, useEffect, useMemo, useState } from 'react'

type Note = {
  id: string
  title: string
  done: boolean
  created_at: string
}

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://127.0.0.1:8000'
const PREVIEW_COMMIT = ((import.meta.env.VITE_PREVIEW_COMMIT as string | undefined) ?? '').trim()
const PREVIEW_RUN_ID = ((import.meta.env.VITE_PREVIEW_RUN_ID as string | undefined) ?? '').trim()
const PREVIEW_APP = ((import.meta.env.VITE_PREVIEW_APP as string | undefined) ?? '').trim()

export default function App() {
  const [notes, setNotes] = useState<Note[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function fetchNotes() {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE}/api/notes`)
      if (!response.ok) {
        throw new Error(`Failed to load notes: ${response.status}`)
      }
      const data = (await response.json()) as Note[]
      setNotes(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchNotes()
  }, [])

  async function createNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const title = input.trim()
    if (!title) {
      return
    }

    const response = await fetch(`${API_BASE}/api/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })

    if (!response.ok) {
      setError(`Failed to create note: ${response.status}`)
      return
    }

    setInput('')
    await fetchNotes()
  }

  async function toggleNote(noteId: string) {
    const response = await fetch(`${API_BASE}/api/notes/${noteId}/toggle`, {
      method: 'PATCH',
    })

    if (!response.ok) {
      setError(`Failed to toggle note: ${response.status}`)
      return
    }

    await fetchNotes()
  }

  const openCount = useMemo(() => notes.filter((note) => !note.done).length, [notes])
  const previewCommitShort = PREVIEW_COMMIT ? PREVIEW_COMMIT.slice(0, 7) : 'local'

  return (
    <main className="container" data-testid="app-root">
      <h1>Starter Notes App</h1>
      <p className="preview-meta" data-testid="preview-meta">
        <strong>Build:</strong> {previewCommitShort}
        {PREVIEW_RUN_ID ? ` • run ${PREVIEW_RUN_ID}` : ''}
        {PREVIEW_APP ? ` • ${PREVIEW_APP}` : ''}
      </p>
      <p>Open notes: {openCount}</p>

      <form onSubmit={createNote}>
        <input
          data-testid="note-input"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Add a note"
          maxLength={200}
        />
        <button data-testid="add-note-button" type="submit">
          Add
        </button>
      </form>

      {error && (
        <p role="alert" data-testid="error-banner">
          {error}
        </p>
      )}

      {loading && <p>Loading...</p>}

      <ul className="notes" data-testid="notes-list">
        {notes.map((note) => (
          <li
            key={note.id}
            className={`note ${note.done ? 'done' : ''}`}
            data-testid="note-item"
            data-note-id={note.id}
            data-done={note.done ? 'true' : 'false'}
          >
            <span>{note.title}</span>
            <button
              className="secondary"
              type="button"
              data-testid={`toggle-${note.id}`}
              onClick={() => toggleNote(note.id)}
            >
              {note.done ? 'Mark open' : 'Mark done'}
            </button>
          </li>
        ))}
      </ul>
    </main>
  )
}
