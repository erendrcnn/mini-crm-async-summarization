from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.user import User, Role
from ..models.note import Note, NoteStatus
from ..schemas.note import NoteCreate, NoteOut

router = APIRouter()


@router.post("", response_model=NoteOut, status_code=201)
async def create_note(payload: NoteCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Create a new note and queue it for summarization"""
    if not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="Note text cannot be empty")
    
    note = Note(owner_id=user.id, raw_text=payload.raw_text, status=NoteStatus.queued)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return NoteOut.model_validate(note)


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(note_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Get a specific note by ID (role-based access)"""
    if note_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid note ID")
        
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if user.role != Role.ADMIN and note.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied: insufficient permissions")
    return NoteOut.model_validate(note)


@router.get("", response_model=list[NoteOut])
async def list_notes(
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None, pattern="^(queued|processing|done|failed)$"),
    q: str | None = Query(None, min_length=1, max_length=200),
):
    base = select(Note)
    count_stmt = select(func.count())
    if user.role != Role.ADMIN:
        base = base.where(Note.owner_id == user.id)
        count_stmt = count_stmt.select_from(Note).where(Note.owner_id == user.id)
    else:
        count_stmt = count_stmt.select_from(Note)

    if status:
        base = base.where(Note.status == status)
        count_stmt = count_stmt.where(Note.status == status)
    if q:
        like = f"%{q}%"
        base = base.where(Note.raw_text.ilike(like))
        count_stmt = count_stmt.where(Note.raw_text.ilike(like))

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = base.order_by(Note.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    notes = result.scalars().all()
    response.headers["X-Total-Count"] = str(total)
    return [NoteOut.model_validate(n) for n in notes]
