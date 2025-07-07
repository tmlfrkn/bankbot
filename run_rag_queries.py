#!/usr/bin/env python3
"""
run_rag_queries.py
------------------
This script executes an end-to-end test of the RAG pipeline against the
`gorevler/banking_queries_multilingual.md` dataset.  For every query it:

1. Embeds the query with the same embedding model used during indexing.
2. Performs a vector similarity search on the `document_chunks` table (pgvector).
3. Applies the role-based access matrix from *Technical Proficiency Test – BankBot*
   to filter which document types are eligible for retrieval for a given access
   level (default: L5 – Executive).
4. Assembles a prompt that includes the top-k retrieved chunks as context and
   asks the Yi-1.5-9B-Chat model to answer the user's question.
5. Prints the generated answer alongside the expected answer for manual review.

Environment variables expected (same as in `rag_pipeline_fixed.py`):
    DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT
    YI_MODEL_PATH (optional, default path provided)

Dependencies: psycopg2, sentence-transformers, ctransformers, pgvector ext.
"""
from __future__ import annotations

import os
import re
import sys
import textwrap
from pathlib import Path
from typing import List, Tuple, Dict, Any

import psycopg2
from sentence_transformers import SentenceTransformer  # type: ignore
from ctransformers import AutoModelForCausalLM, AutoConfig  # type: ignore
import numpy as np

###############################################################################
# Configuration                                                               #
###############################################################################

TESTSET_PATH = Path("gorevler/banking_queries_multilingual.md")
TOP_K = int(os.getenv("TOP_K", "5"))
DEFAULT_ACCESS_LEVEL = int(os.getenv("ACCESS_LEVEL", "5"))  # 1-5

# Access matrix mapping (Level -> allowed visibility per document type)
ACCESS_MATRIX: Dict[str, Dict[int, str]] = {
    "Public Product Info":       {1: "Full", 2: "Full", 3: "Full", 4: "Full", 5: "Full"},
    "Internal Procedures":       {1: "None", 2: "Full", 3: "Full", 4: "Full", 5: "Full"},
    "Risk Models":               {1: "None", 2: "None", 3: "Full", 4: "Summary", 5: "Full"},
    "Regulatory Docs":           {1: "None", 2: "Summary", 3: "Relevant", 4: "Full", 5: "Full"},
    "Investigation Reports":     {1: "None", 2: "None", 3: "None", 4: "None", 5: "Full"},
    "Executive Reports":         {1: "None", 2: "None", 3: "None", 4: "Summary", 5: "Full"},
}

QUERY_HEADER_RE = re.compile(r"^\*\*[A-Za-zğşıöçĞŞİÖÇ ]+ Query [0-9]+:\*\*")
EXPECTED_HEADER_RE = re.compile(r"^\*\*Expected Response:\*\*")
CITATION_LINE_RE = re.compile(r"^\*Citation:|^\*Kaynak:")

###############################################################################
# Utility functions                                                           #
###############################################################################

def parse_testset(path: Path) -> List[Tuple[str, str]]:
    """Return list of (query, expected_response) pairs from the markdown file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    pairs: List[Tuple[str, str]] = []
    i = 0
    while i < len(lines):
        if QUERY_HEADER_RE.match(lines[i]):
            i += 1
            if i >= len(lines):
                break
            query = lines[i].strip().strip('"')
            # advance to expected header
            while i < len(lines) and not EXPECTED_HEADER_RE.match(lines[i]):
                i += 1
            if i >= len(lines):
                break
            i += 1  # move to first expected-response line
            expected_lines: List[str] = []
            while i < len(lines):
                if lines[i].strip() == "" or CITATION_LINE_RE.match(lines[i]):
                    break
                expected_lines.append(lines[i].rstrip())
                i += 1
            expected = "\n".join(expected_lines).strip()
            pairs.append((query, expected))
        i += 1
    return pairs


def allowed_document_types(level: int) -> List[str]:
    """Return doc types with visibility other than 'None' for the level."""
    allowed: List[str] = []
    for doc_type, matrix in ACCESS_MATRIX.items():
        if matrix.get(level, "None") != "None":
            allowed.append(doc_type)
    return allowed


def build_context(chunks: List[Dict[str, Any]], level: int) -> str:
    """Concatenate chunks into a context string with citation tags."""
    parts: List[str] = []
    for idx, ch in enumerate(chunks, 1):
        vis = ACCESS_MATRIX.get(ch["document_type"], {}).get(level, "None")
        if vis == "None":
            continue

        citation = f"{ch['entity']} – {ch['main_section_title']}"
        if ch.get("sub_section_title"):
            citation += f", {ch['sub_section_title']}"

        if vis == "Summary" and ch.get("summary"):
            content = ch["summary"]
        else:
            content = ch.get("text_content") or ch.get("summary") or ""

        parts.append(
            f"[[{idx}]] {content}\n*Citation: {citation}*"
        )
    return "\n\n".join(parts)

###############################################################################
# Database interaction                                                        #
###############################################################################

def connect_db():
    params = {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "bankbot"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD"),
        "port": os.getenv("DB_PORT", "5432"),
    }
    return psycopg2.connect(**params)


def vector_search(conn, embed: np.ndarray, allowed_doc_types: List[str], top_k: int) -> List[Dict[str, Any]]:
    """Return top-k document chunks as list of dicts."""
    cur = conn.cursor()
    # Convert numpy embedding to pgvector literal string: '[0.1,0.2,...]'
    vec_literal = '[' + ','.join(f'{x:.6f}' for x in embed.tolist()) + ']'

    placeholders = ','.join(['%s'] * len(allowed_doc_types)) if allowed_doc_types else "''"
    sql = (
        f"SELECT chunk_id, source_document, entity, language, document_type, "
        f"main_section_title, sub_section_title, text_content, summary, "
        f"embedding <-> %s::vector AS distance "
        f"FROM document_chunks "
        f"WHERE document_type IN ({placeholders}) "
        f"ORDER BY embedding <-> %s::vector LIMIT %s;"
    )
    params = [vec_literal] + allowed_doc_types + [vec_literal, top_k]
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
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
        "distance",
    ]
    return [dict(zip(cols, row)) for row in rows]

###############################################################################
# Model loading                                                               #
###############################################################################


def load_embedding_model():
    import torch  # local import to avoid startup penalty if torch missing
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return SentenceTransformer("intfloat/multilingual-e5-large", device=device)


def load_llm():
    model_path = os.getenv(
        "YI_MODEL_PATH", "./models/yi-1.5-9b-chat/Yi-1.5-9B-Chat-Q4_K_M.gguf")
    return AutoModelForCausalLM.from_pretrained(
        model_path,
        model_type="llama",
        gpu_layers=50,
        context_length=8192,
        max_new_tokens=512,
        temperature=0.3,
        threads=8,
    )

###############################################################################
# Main                                                                         #
###############################################################################

def generate_answer(llm, query: str, context: str) -> str:
    """Call LLM with RAG prompt to produce answer with citations."""
    prompt = textwrap.dedent(
        f"""
        [INST]
        You are BankBot, an enterprise banking assistant.
        TASK:
        1. Answer the user question as accurately and concisely as possible USING ONLY the information provided in the context below.
        2. Write the answer in the SAME LANGUAGE as the question.
        3. When you reference a specific fact from a source chunk, append the corresponding citation label in square brackets, e.g. [1] or [2].
        4. After the answer, add a new line that begins with "*Citation:" followed by the EXACT citation strings for each label you used (do NOT translate or modify them), separated by "; ". Citation strings are provided inside the context next to each chunk.
        5. If the required information is NOT present in the context, reply with exactly: "I don't have enough information in my current knowledge base to answer that."

        # Context
        {context}

        # Question
        {query}
        [/INST]
        """
    )
    return llm(prompt).strip()


def main() -> None:
    if not TESTSET_PATH.exists():
        print("Testset file not found.")
        sys.exit(1)

    pairs = parse_testset(TESTSET_PATH)
    print(f"Loaded {len(pairs)} queries from dataset.\n")

    # Load models once
    embedder = load_embedding_model()
    llm = load_llm()

    # Connect DB once
    conn = connect_db()

    level = DEFAULT_ACCESS_LEVEL
    allowed_docs = allowed_document_types(level)

    for idx, (query, expected) in enumerate(pairs, 1):
        q_embed = embedder.encode(query)
        chunks = vector_search(conn, q_embed, allowed_docs, TOP_K)
        context = build_context(chunks, level)
        answer = generate_answer(llm, query, context)

        sep = "=" * 100
        print(sep)
        print(f"Query {idx}: {query}\n")
        print("Generated Answer:\n" + answer + "\n")
        print("Expected Answer:\n" + expected + "\n")
        print(sep + "\n")

    conn.close()


if __name__ == "__main__":
    main() 