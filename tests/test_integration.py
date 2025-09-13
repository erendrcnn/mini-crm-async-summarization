import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import engine, Base, SessionLocal
from app.worker import process_note
from app.models.note import Note, NoteStatus
from sqlalchemy import select


@pytest.mark.anyio
async def test_signup_login_create_note_and_worker_process():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "Secret123!"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/auth/signup", json={"email": email, "password": password, "role": "AGENT"})
        assert r.status_code == 200
        token = r.json()["access_token"]

        r2 = await ac.post("/notes", headers={"Authorization": f"Bearer {token}"}, json={"raw_text": "Hello world. This is a long note for summary."})
        assert r2.status_code == 201
        note_id = r2.json()["id"]

        # Ensure queued
        r3 = await ac.get(f"/notes/{note_id}", headers={"Authorization": f"Bearer {token}"})
        assert r3.status_code == 200
        assert r3.json()["status"] == "queued"

    # Run worker on the specific note
    async with SessionLocal() as session:
        res = await session.execute(select(Note).where(Note.id == note_id))
        note = res.scalars().first()
        assert note is not None
        await process_note(session, note)

        res2 = await session.execute(select(Note).where(Note.id == note_id))
        note2 = res2.scalars().first()
        assert note2 is not None
        assert note2.status == NoteStatus.done
        assert note2.summary and len(note2.summary) > 0
