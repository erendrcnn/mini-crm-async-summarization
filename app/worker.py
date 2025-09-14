import asyncio
import sys
import time
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from .core.database import SessionLocal
from .core.config import settings
from .models.note import Note, NoteStatus
from .services.summarizer import summarize


async def process_note(session: AsyncSession, note: Note):
    # Idempotency check - skip if already processed
    if note.status in [NoteStatus.processing, NoteStatus.done]:
        return

    # Mark as processing with timestamp
    await session.execute(
        update(Note)
        .where(Note.id == note.id)
        .values(status=NoteStatus.processing, attempts=note.attempts + 1)
    )
    await session.commit()

    try:
        # Simulate processing time for demo
        await asyncio.sleep(1)
        result = summarize(note.raw_text)
        
        # Update with result
        await session.execute(
            update(Note)
            .where(Note.id == note.id)
            .values(status=NoteStatus.done, summary=result)
        )
        await session.commit()
        print(f"✅ Successfully processed note {note.id}")
        
    except Exception as e:
        attempts = note.attempts + 1
        new_status = NoteStatus.failed if attempts >= settings.MAX_RETRIES else NoteStatus.queued
        
        # Exponential backoff for retries
        retry_delay = min(60, 2 ** attempts)
        
        await session.execute(
            update(Note)
            .where(Note.id == note.id)
            .values(status=new_status, attempts=attempts)
        )
        await session.commit()
        
        if new_status == NoteStatus.queued:
            print(f"Note {note.id} failed (attempt {attempts}), retrying in {retry_delay}s")
            await asyncio.sleep(retry_delay)
        else:
            print(f"Note {note.id} failed permanently after {attempts} attempts: {e}")


async def worker_loop():
    while True:
        try:
            async with SessionLocal() as session:
                result = await session.execute(
                    select(Note)
                    .where(Note.status == NoteStatus.queued)
                    .order_by(Note.created_at.asc())
                    .limit(5)
                )
                notes = result.scalars().all()
                for note in notes:
                    await process_note(session, note)
            await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
        except Exception as e:
            # Keep the worker alive on transient errors (e.g., tables not yet created)
            print(f"Worker loop error: {e}. Retrying shortly...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    # Use a compatible event loop on Windows for psycopg async
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    print("Worker started. Polling for queued notes...")
    asyncio.run(worker_loop())
