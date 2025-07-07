from __future__ import annotations

from functools import lru_cache
from typing import List, Dict, Any

import numpy as np
from sentence_transformers import SentenceTransformer  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from asyncio import to_thread

from app.models import ACCESS_MATRIX, AccessType, DocumentChunk  # add DocumentChunk

TOP_K_DEFAULT = 3


@lru_cache(maxsize=1)
def load_embedder():
    import torch  # local import
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return SentenceTransformer("intfloat/multilingual-e5-large", device=device)


def embed_text(text: str) -> np.ndarray:
    model = load_embedder()
    return model.encode(text)


async def embed_text_async(text: str) -> np.ndarray:
    """Non-blocking embed call using default thread pool."""
    return await to_thread(embed_text, text)


def allowed_doc_types(level: int) -> List[str]:
    return [dt for dt, mapping in ACCESS_MATRIX.items() if mapping.get(level, AccessType.NONE) != AccessType.NONE]


async def vector_search(db: AsyncSession, embed: np.ndarray, allowed_types: List[str], top_k: int = TOP_K_DEFAULT) -> List[Dict[str, Any]]:
    """Return list of chunk dicts ordered by distance using ORM expressions."""
    embed_list = embed.tolist()

    distance_expr = DocumentChunk.embedding.l2_distance(embed_list).label("distance")

    stmt = (
        select(
            DocumentChunk.chunk_id,
            DocumentChunk.source_document,
            DocumentChunk.entity,
            DocumentChunk.language,
            DocumentChunk.document_type,
            DocumentChunk.main_section_title,
            DocumentChunk.sub_section_title,
            DocumentChunk.text_content,
            DocumentChunk.summary,
            DocumentChunk.generated_labels,
            distance_expr,
        )
        .where(DocumentChunk.document_type.in_(allowed_types))
        .order_by(distance_expr)
        .limit(top_k)
    )

    print("[DEBUG] vector_search allowed_types:", allowed_types)
    result = await db.execute(stmt)
    rows = result.fetchall()
    print(f"[DEBUG] vector_search fetched rows: {len(rows)}")

    cols = [
        "chunk_id",
        "source_document",
        "entity",
        "language",
        "document_type",
        "main_section_title",
        "sub_section_title",
        "text_content",
        "summary",
        "generated_labels",
        "distance",
    ]
    return [dict(zip(cols, row)) for row in rows]


def choose_content(chunk: Dict[str, Any], level: int) -> str | None:
    """Return appropriate content string for the user level based on ACCESS_MATRIX.

    Priority:
    1. FULL      -> raw full text (text_content)
    2. SUMMARY   -> summary field
    3. RELEVANT  -> relevant snippet (if missing, fallback to summary)
    4. NONE      -> None (filtered out later)
    """
    vis = ACCESS_MATRIX.get(chunk["document_type"], {}).get(level, AccessType.NONE)
    if vis == AccessType.NONE:
        return None

    if vis == AccessType.SUMMARY:
        return chunk.get("summary")

    if vis == AccessType.RELEVANT:
        # Use generated_labels first; else summary; else first 400 chars
        labels = chunk.get("generated_labels")
        if labels:
            # Ensure string format (comma-separated)
            return ", ".join(labels)

        # Fallbacks
        if chunk.get("summary"):
            return chunk["summary"]
        raw = chunk.get("text_content") or ""
        return raw[:400] + ("…" if len(raw) > 400 else "")

    # AccessType.FULL – return full raw text
    return chunk.get("text_content")


def build_context(chunks: List[Dict[str, Any]], level: int) -> str:
    parts = []
    for idx, ch in enumerate(chunks, 1):
        content = choose_content(ch, level)
        if not content:
            continue
        citation = f"{ch['entity']} – {ch['main_section_title']}"
        if ch.get("sub_section_title"):
            citation += f", {ch['sub_section_title']}"
        parts.append(f"[[{idx}]] {content}\n*Citation: {citation}*")
    return "\n\n".join(parts) 