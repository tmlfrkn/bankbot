from typing import List, Dict, Any, Optional
from uuid import uuid4, UUID
import json

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_token_payload
from ..services import rag_service as rag
from ..services.llm_service import load_llm, generate_answer, generate_answer_async

router = APIRouter(prefix="/rag", tags=["rag"])


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[UUID] = None  # Optional client-provided session id


class ChunkResponse(BaseModel):
    chunk_id: str
    document_type: str
    citation: str
    content: str
    distance: float


class RetrieveResponse(BaseModel):
    query: str
    chunks: List[ChunkResponse]


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_top_chunks(req: QueryRequest, request: Request, db: AsyncSession = Depends(get_db), payload: Dict[str, Any] = Depends(get_current_token_payload)):
    """Return top 3 chunks for query based on user's access level."""
    print("[DEBUG] /rag/retrieve called by", payload.get("username"))
    print("[DEBUG] Query:", req.query)

    access_level: int = int(payload.get("access_level", 1))
    embed = await rag.embed_text_async(req.query)
    allowed_types = rag.allowed_doc_types(access_level)
    print("[DEBUG] Allowed doc types:", allowed_types)
    if not allowed_types:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access the relevant information.")

    chunks = await rag.vector_search(db, embed, allowed_types, top_k=3)
    print(f"[DEBUG] Retrieved {len(chunks)} raw chunks")

    resp_chunks: List[ChunkResponse] = []
    for idx, ch in enumerate(chunks, 1):
        citation = f"{ch['entity']} – {ch['main_section_title']}"
        if ch.get("sub_section_title"):
            citation += f", {ch['sub_section_title']}"
        content = rag.choose_content(ch, access_level) or ""
        resp_chunks.append(
            ChunkResponse(
                chunk_id=str(ch["chunk_id"]),
                document_type=ch["document_type"],
                citation=citation,
                content=content,
                distance=float(ch["distance"]),
            )
        )

    if not resp_chunks:
        # There were chunks but none accessible due to finer-grained restrictions
        if chunks:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access the relevant information.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No relevant documents found.")

    print(f"[DEBUG] Returning {len(resp_chunks)} accessible chunks\n")
    resp = RetrieveResponse(query=req.query, chunks=resp_chunks)

    # -------------------------------------------------------------
    # Persist history
    # -------------------------------------------------------------
    from ..services import history_service as history_srv

    session_id = req.session_id or uuid4()
    ip_addr = request.client.host if request.client else None
    await history_srv.log_history(
        db,
        user_id=UUID(payload.get("sub")),
        session_id=session_id,
        route="retrieve",
        query_text=req.query,
        response_text=json.dumps([c.dict() for c in resp_chunks], ensure_ascii=False),
        ip_address=ip_addr,
    )

    return resp


class AnswerResponse(BaseModel):
    query: str
    answer: str


@router.post("/answer", response_model=AnswerResponse)
async def answer_query(req: QueryRequest, request: Request, db: AsyncSession = Depends(get_db), payload: Dict[str, Any] = Depends(get_current_token_payload)):
    """Generate LLM answer using RAG context respecting access level."""
    print("[DEBUG] /rag/answer called by", payload.get("username"))
    print("[DEBUG] Query:", req.query)

    access_level: int = int(payload.get("access_level", 1))
    embed = await rag.embed_text_async(req.query)
    allowed_types = rag.allowed_doc_types(access_level)
    print("[DEBUG] Allowed doc types:", allowed_types)
    if not allowed_types:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access the relevant information.")

    chunks = await rag.vector_search(db, embed, allowed_types, top_k=3)
    print(f"[DEBUG] Retrieved {len(chunks)} raw chunks for answer")

    # Determine access visibility for chunks
    vis_list = [rag.ACCESS_MATRIX.get(c["document_type"], {}).get(access_level, rag.AccessType.NONE) for c in chunks]
    print("[DEBUG] Visibility list:", vis_list)

    only_limited = chunks and all(v in (rag.AccessType.SUMMARY, rag.AccessType.RELEVANT) for v in vis_list)
    print("[DEBUG] Only limited access chunks:", only_limited)
    if only_limited:
        # Build simple answer: each allowed chunk content with citation (no LLM)
        direct_answer = rag.build_context(chunks, access_level)
        print("[DEBUG] Direct answer built (Summary/Relevant only)")

        # History logging for direct answer branch
        from ..services import history_service as history_srv
        session_id = req.session_id or uuid4()
        ip_addr = request.client.host if request.client else None
        await history_srv.log_history(
            db,
            user_id=UUID(payload.get("sub")),
            session_id=session_id,
            route="answer",
            query_text=req.query,
            response_text=json.dumps([{"query": req.query, "answer": direct_answer}], ensure_ascii=False),
            ip_address=ip_addr,
        )

        return AnswerResponse(query=req.query, answer=direct_answer)

    context = rag.build_context(chunks, access_level)
    print("[DEBUG] Context length:", len(context))

    if not context:
        if chunks:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access the relevant information.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No relevant context found.")

    llm = load_llm()
    answer_text = await generate_answer_async(llm, req.query, context)
    print("[DEBUG] LLM answer generated, length:", len(answer_text))

    # determine session id
    session_id = req.session_id or uuid4()

    # after generating answer_text or direct_answer; place history logging accordingly.

    # We'll adjust accordingly below

    ip_addr = request.client.host if request.client else None

    # -------------------------------------------------------------
    # Persist history
    # -------------------------------------------------------------
    from ..services import history_service as history_srv

    await history_srv.log_history(
        db,
        user_id=UUID(payload.get("sub")),
        session_id=session_id,
        route="answer",
        query_text=req.query,
        response_text=json.dumps([{"query": req.query, "answer": answer_text}], ensure_ascii=False),
        ip_address=ip_addr,
    )

    return AnswerResponse(query=req.query, answer=answer_text) 