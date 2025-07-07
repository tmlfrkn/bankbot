#!/usr/bin/env python3
"""
run_rag_retrieval.py
--------------------
Lightweight test to verify the RETRIEVE stage of the RAG pipeline without
invoking the Yi language model.

For every query in `gorevler/banking_queries_multilingual.md` it:
1. Generates the query embedding.
2. Retrieves the top-k document chunks from `document_chunks` table respecting
   the role-based access matrix (default ACCESS_LEVEL=L5).
3. Prints the query followed by the retrieved content blocks **with** citation
   strings so we can manually inspect whether the retrieval is relevant.

Useful when you want to debug the similarity search or access filtering without
waiting for LLM inference.
"""
from pathlib import Path
import sys
import os

from run_rag_queries import (
    TESTSET_PATH,
    TOP_K,
    DEFAULT_ACCESS_LEVEL,
    parse_testset,
    allowed_document_types,
    build_context,
    connect_db,
    vector_search,
    load_embedding_model,
)


def main() -> None:
    if not TESTSET_PATH.exists():
        print("Testset markdown not found.")
        sys.exit(1)

    pairs = parse_testset(TESTSET_PATH)
    print(f"Loaded {len(pairs)} queries. Running retrieval-only test...\n")

    embedder = load_embedding_model()
    conn = connect_db()

    level = DEFAULT_ACCESS_LEVEL
    allowed_docs = allowed_document_types(level)

    for idx, (query, _) in enumerate(pairs, 1):
        q_emb = embedder.encode(query)
        chunks = vector_search(conn, q_emb, allowed_docs, TOP_K)
        context = build_context(chunks, level)

        sep = "#" * 100
        print(sep)
        print(f"Query {idx}: {query}\n")
        print("Retrieved Context with Citations:\n")
        print(context if context else "<No context found>")
        print(sep + "\n")

    conn.close()


if __name__ == "__main__":
    main() 