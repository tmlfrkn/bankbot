from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import QueryHistory


async def log_history(
    db: AsyncSession,
    *,
    user_id: UUID,
    session_id: Optional[UUID],
    route: str,
    query_text: str,
    response_text: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> QueryHistory:
    """Insert a new QueryHistory row and return it.

    If *session_id* is None, a new UUID4 session id will be generated automatically
    so that callers can simply omit it for a fresh conversation thread.
    """
    if session_id is None:
        session_id = uuid4()

    history = QueryHistory(
        user_id=user_id,
        session_id=session_id,
        route=route,
        query_text=query_text,
        response_text=response_text,
        ip_address=ip_address,
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)
    return history


async def list_sessions(db: AsyncSession, *, user_id: UUID) -> List[UUID]:
    """Return distinct session ids for the given user ordered by recency."""
    stmt = select(QueryHistory.session_id).where(QueryHistory.user_id == user_id).distinct().order_by(QueryHistory.created_at.desc())
    result = await db.execute(stmt)
    return [row[0] for row in result.fetchall()]


async def session_messages(db: AsyncSession, *, user_id: UUID, session_id: UUID) -> List[QueryHistory]:
    """Fetch all history entries for a session, newest first."""
    stmt = (
        select(QueryHistory)
        .where(
            QueryHistory.user_id == user_id,
            QueryHistory.session_id == session_id,
        )
        .order_by(QueryHistory.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def delete_session(db: AsyncSession, *, user_id: UUID, session_id: UUID) -> None:
    """Delete all history entries for a session."""
    stmt = delete(QueryHistory).where(
        QueryHistory.user_id == user_id,
        QueryHistory.session_id == session_id,
    )
    await db.execute(stmt)
    await db.commit() 