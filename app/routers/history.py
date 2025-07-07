from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_token_payload
from ..services import history_service as history_srv

router = APIRouter(prefix="/history", tags=["history"])


class SessionSummary(BaseModel):
    session_id: UUID
    last_query: str
    last_created_at: str  # ISO timestamp


class HistoryEntrySchema(BaseModel):
    id: UUID
    session_id: UUID
    route: str
    query_text: str
    response_text: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: str  # ISO format

    class Config:
        orm_mode = True


@router.get("/sessions", response_model=List[SessionSummary])
async def list_user_sessions(
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_token_payload),
):
    """Return list of session ids for the current user with last query snippet."""
    user_id = payload.get("sub")
    session_ids = await history_srv.list_sessions(db, user_id=UUID(user_id))
    summaries: List[SessionSummary] = []
    for sid in session_ids:
        messages = await history_srv.session_messages(db, user_id=UUID(user_id), session_id=sid)
        if not messages:
            continue
        last_msg = messages[0]  # newest first due to ordering
        summaries.append(
            SessionSummary(
                session_id=sid,
                last_query=last_msg.query_text[:120],
                last_created_at=last_msg.created_at.isoformat(),
            )
        )
    return summaries


@router.get("/sessions/{session_id}", response_model=List[HistoryEntrySchema])
async def get_session_messages(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_token_payload),
):
    user_id = UUID(payload.get("sub"))
    messages = await history_srv.session_messages(db, user_id=user_id, session_id=session_id)
    if not messages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or empty")
    return messages


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_token_payload),
):
    user_id = UUID(payload.get("sub"))
    await history_srv.delete_session(db, user_id=user_id, session_id=session_id)
    return None 