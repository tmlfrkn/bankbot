from __future__ import annotations

from functools import lru_cache
from typing import List, Dict, Any

import numpy as np
from sentence_transformers import SentenceTransformer  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from asyncio import to_thread

from app.models import ACCESS_MATRIX, AccessType  # use central definitions

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
    """Return list of chunk dicts ordered by distance."""
    vec_literal = '[' + ','.join(f'{x:.6f}' for x in embed.tolist()) + ']'

    sql = text(
        """
        SELECT chunk_id, source_document, entity, language, document_type,
               main_section_title, sub_section_title, text_content, summary,
               embedding <-> (:vec)::vector AS distance
        FROM document_chunks
        WHERE document_type = ANY(:types)
        ORDER BY embedding <-> (:vec)::vector
        LIMIT :k;
        """
    )
    params = {"vec": vec_literal, "types": allowed_types, "k": top_k}

    print("[DEBUG] vector_search allowed_types:", allowed_types)
    result = await db.execute(sql, params)
    rows = result.fetchall()
    print(f"[DEBUG] vector_search fetched rows: {len(rows)}")
    cols = [
        "chunk_id","source_document","entity","language","document_type",
        "main_section_title","sub_section_title","text_content","summary","distance"
    ]
    return [dict(zip(cols, row)) for row in rows]


def choose_content(chunk: Dict[str, Any], level: int) -> str | None:
    vis = ACCESS_MATRIX.get(chunk["document_type"], {}).get(level, AccessType.NONE)
    if vis == AccessType.NONE:
        return None
    if vis == AccessType.SUMMARY and chunk.get("summary"):
        return chunk["summary"]
    if vis == AccessType.RELEVANT and chunk.get("summary"):
        return chunk["summary"]
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